from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .supabase_client import UsuarioService, ConversacionService, MensajeService
import json

# ==================== AUTENTICACIÓN ====================

def registro(request):
    """Vista para registrar un nuevo usuario"""
    if request.method == 'POST':
        username = request.POST.get('username')
        contraseña = request.POST.get('contraseña')
        email = request.POST.get('email')
        
        # Validar que el usuario no exista
        if UsuarioService.usuario_existe(username):
            return render(request, 'registro.html', {'error': 'El usuario ya existe'})
        
        # Crear usuario
        try:
            usuario = UsuarioService.crear_usuario(username, email, contraseña)
            
            # Guardar en sesión
            request.session['usuario_id'] = usuario['id_usuario']
            request.session['username'] = usuario['username']
            
            return redirect('conversaciones')
        except Exception as e:
            return render(request, 'registro.html', {'error': f'Error al registrar: {str(e)}'})
    
    return render(request, 'registro.html')


def login(request):
    """Vista para login de usuario"""
    if request.method == 'POST':
        username = request.POST.get('username')
        contraseña = request.POST.get('contraseña')
        
        try:
            # Verificar contraseña
            if UsuarioService.verificar_contraseña(username, contraseña):
                usuario = UsuarioService.obtener_usuario(username)
                
                # Login exitoso
                request.session['usuario_id'] = usuario['id_usuario']
                request.session['username'] = usuario['username']
                return redirect('conversaciones')
            else:
                return render(request, 'login.html', {'error': 'Contraseña incorrecta'})
        except Exception as e:
            return render(request, 'login.html', {'error': 'Usuario no encontrado'})
    
    return render(request, 'login.html')



def logout(request):
    """Cerrar sesión"""
    request.session.flush()
    return redirect('login')


# ==================== CONVERSACIONES ====================

def es_autenticado(request):
    """Verificar si el usuario está autenticado"""
    return 'usuario_id' in request.session


def conversaciones(request):
    """Listar todas las conversaciones disponibles"""
    if not es_autenticado(request):
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    username = request.session.get('username')
    
    try:
        # Obtener conversaciones
        conversaciones_publicas = ConversacionService.obtener_conversaciones_publicas()
        conversaciones_usuario = ConversacionService.obtener_conversaciones_usuario(usuario_id)
        
        contexto = {
            'username': username,
            'conversaciones_publicas': conversaciones_publicas,
            'conversaciones_privadas': conversaciones_usuario['privadas'],
        }
        
        return render(request, 'conversaciones.html', contexto)
    except Exception as e:
        return render(request, 'conversaciones.html', {'error': f'Error: {str(e)}'})


def crear_conversacion_publica(request):
    """Crear una nueva conversación pública"""
    if not es_autenticado(request):
        return redirect('login')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        
        if nombre:
            try:
                conversacion = ConversacionService.crear_conversacion(
                    tipo='publico',
                    nombre=nombre
                )
                
                return redirect('chat', id_conversacion=conversacion['id_conversacion'])
            except Exception as e:
                return render(request, 'crear_conversacion.html', {'error': str(e)})
    
    return render(request, 'crear_conversacion.html')


def crear_conversacion_privada(request):
    """Crear una conversación privada"""
    if not es_autenticado(request):
        return redirect('login')
    
    if request.method == 'POST':
        username_destino = request.POST.get('username')
        usuario_actual_id = request.session.get('usuario_id')
        
        try:
            usuario_destino = UsuarioService.obtener_usuario(username_destino)
            
            if not usuario_destino:
                return render(request, 'crear_privado.html', 
                            {'error': 'Usuario no encontrado'})
            
            # Verificar que no sea a sí mismo
            if usuario_actual_id == usuario_destino['id_usuario']:
                return render(request, 'crear_privado.html', 
                            {'error': 'No puedes crear una conversación contigo mismo'})
            
            # Verificar si ya existe
            if ConversacionService.conversacion_privada_existe(usuario_actual_id, usuario_destino['id_usuario']):
                # Buscar la conversación existente
                conversaciones_usuario = ConversacionService.obtener_conversaciones_usuario(usuario_actual_id)
                for conv in conversaciones_usuario['privadas']:
                    if (conv['id_usuario_1'] == usuario_destino['id_usuario'] or 
                        conv['id_usuario_2'] == usuario_destino['id_usuario']):
                        return redirect('chat', id_conversacion=conv['id_conversacion'])
            
            # Crear nueva conversación privada
            conversacion = ConversacionService.crear_conversacion(
                tipo='privado',
                id_usuario_1=usuario_actual_id,
                id_usuario_2=usuario_destino['id_usuario']
            )
            
            return redirect('chat', id_conversacion=conversacion['id_conversacion'])
        
        except Exception as e:
            return render(request, 'crear_privado.html', 
                        {'error': f'Error: {str(e)}'})
    
    return render(request, 'crear_privado.html')


# ==================== CHAT ====================

def chat(request, id_conversacion):
    """Vista de chat para una conversación"""
    if not es_autenticado(request):
        return redirect('login')
    
    usuario_actual_id = request.session.get('usuario_id')
    username = request.session.get('username')
    
    try:
        conversacion = ConversacionService.obtener_conversacion(id_conversacion)
        
        if not conversacion:
            return redirect('conversaciones')
        
        # Obtener mensajes y descifrarlos
        mensajes_raw = MensajeService.obtener_mensajes(id_conversacion)
        
        mensajes_descifrados = []
        for msg in mensajes_raw:
            try:
                texto_descifrado = MensajeService.descifrar_mensaje(msg['mensaje'], conversacion['token'])
                mensajes_descifrados.append({
                    'id_usuario': msg['id_usuario'],
                    'usuario': msg.get('usuario_username', 'Usuario'),  # Si la join funciona
                    'contenido': texto_descifrado,
                    'fecha': msg['fecha_envio'],
                    'es_tuyo': msg['id_usuario'] == usuario_actual_id
                })
            except:
                # Si falla el descifrado
                mensajes_descifrados.append({
                    'id_usuario': msg['id_usuario'],
                    'usuario': msg.get('usuario_username', 'Usuario'),
                    'contenido': '[Mensaje cifrado]',
                    'fecha': msg['fecha_envio'],
                    'es_tuyo': msg['id_usuario'] == usuario_actual_id
                })
        
        if request.method == 'POST':
            contenido = request.POST.get('mensaje')
            
            if contenido:
                try:
                    # Crear mensaje cifrado
                    MensajeService.crear_mensaje(id_conversacion, usuario_actual_id, contenido)
                    return redirect('chat', id_conversacion=id_conversacion)
                except Exception as e:
                    contexto = {
                        'username': username,
                        'conversacion': conversacion,
                        'mensajes': mensajes_descifrados,
                        'error': f'Error al enviar: {str(e)}'
                    }
                    return render(request, 'chat.html', contexto)
        
        contexto = {
            'username': username,
            'conversacion': conversacion,
            'mensajes': mensajes_descifrados,
        }
        
        return render(request, 'chat.html', contexto)
    except Exception as e:
        return render(request, 'chat.html', {'error': f'Error: {str(e)}'})


def index(request):
    """Redirigir a conversaciones si está autenticado, sino a login"""
    if es_autenticado(request):
        return redirect('conversaciones')
    return redirect('login')

