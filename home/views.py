from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Usuario, Conversacion, Mensaje
from cryptography.fernet import Fernet
import json

# ==================== AUTENTICACIÓN ====================

def registro(request):
    """Vista para registrar un nuevo usuario"""
    if request.method == 'POST':
        username = request.POST.get('username')
        contraseña = request.POST.get('contraseña')
        email = request.POST.get('email')
        
        # Validar que el usuario no exista
        if Usuario.objects.filter(username=username).exists():
            return render(request, 'registro.html', {'error': 'El usuario ya existe'})
        
        # Crear usuario
        usuario = Usuario(username=username, email=email)
        usuario.set_password(contraseña)
        usuario.save()
        
        # Guardar en sesión
        request.session['usuario_id'] = usuario.id_usuario
        request.session['username'] = usuario.username
        
        return redirect('conversaciones')
    
    return render(request, 'registro.html')


def login(request):
    """Vista para login de usuario"""
    if request.method == 'POST':
        username = request.POST.get('username')
        contraseña = request.POST.get('contraseña')
        
        try:
            usuario = Usuario.objects.get(username=username)
            
            if usuario.check_password(contraseña):
                # Login exitoso
                request.session['usuario_id'] = usuario.id_usuario
                request.session['username'] = usuario.username
                return redirect('conversaciones')
            else:
                return render(request, 'login.html', {'error': 'Contraseña incorrecta'})
        except Usuario.DoesNotExist:
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
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    
    # Conversaciones públicas
    conversaciones_publicas = Conversacion.objects.filter(tipo='publico')
    
    # Conversaciones privadas del usuario
    conversaciones_privadas = Conversacion.objects.filter(
        tipo='privado'
    ).filter(
        Q(id_usuario_1=usuario) | Q(id_usuario_2=usuario)
    )
    
    contexto = {
        'usuario': usuario,
        'conversaciones_publicas': conversaciones_publicas,
        'conversaciones_privadas': conversaciones_privadas,
    }
    
    return render(request, 'conversaciones.html', contexto)


def crear_conversacion_publica(request):
    """Crear una nueva conversación pública"""
    if not es_autenticado(request):
        return redirect('login')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        
        if nombre:
            # Generar token
            conversacion = Conversacion(
                tipo='publico',
                nombre=nombre
            )
            conversacion.generar_token()
            conversacion.save()
            
            return redirect('chat', id_conversacion=conversacion.id_conversacion)
    
    return render(request, 'crear_conversacion.html')


def crear_conversacion_privada(request):
    """Crear una conversación privada"""
    if not es_autenticado(request):
        return redirect('login')
    
    if request.method == 'POST':
        username_destino = request.POST.get('username')
        usuario_actual = Usuario.objects.get(id_usuario=request.session.get('usuario_id'))
        
        try:
            usuario_destino = Usuario.objects.get(username=username_destino)
            
            # Verificar que no sea a sí mismo
            if usuario_actual.id_usuario == usuario_destino.id_usuario:
                return render(request, 'crear_privado.html', 
                            {'error': 'No puedes crear una conversación contigo mismo'})
            
            # Verificar si ya existe
            existente = Conversacion.objects.filter(
                tipo='privado'
            ).filter(
                Q(id_usuario_1=usuario_actual, id_usuario_2=usuario_destino) |
                Q(id_usuario_1=usuario_destino, id_usuario_2=usuario_actual)
            ).first()
            
            if existente:
                return redirect('chat', id_conversacion=existente.id_conversacion)
            
            # Crear nueva conversación privada
            conversacion = Conversacion(
                tipo='privado',
                id_usuario_1=usuario_actual,
                id_usuario_2=usuario_destino
            )
            conversacion.generar_token()
            conversacion.save()
            
            return redirect('chat', id_conversacion=conversacion.id_conversacion)
        
        except Usuario.DoesNotExist:
            return render(request, 'crear_privado.html', 
                        {'error': 'Usuario no encontrado'})
    
    return render(request, 'crear_privado.html')


# ==================== CHAT ====================

def chat(request, id_conversacion):
    """Vista de chat para una conversación"""
    if not es_autenticado(request):
        return redirect('login')
    
    usuario_actual = Usuario.objects.get(id_usuario=request.session.get('usuario_id'))
    conversacion = get_object_or_404(Conversacion, id_conversacion=id_conversacion)
    
    # Obtener mensajes y descifrarlos
    mensajes = Mensaje.objects.filter(id_conversacion=conversacion).select_related('id_usuario')
    
    mensajes_descifrados = []
    for msg in mensajes:
        try:
            texto_descifrado = msg.descifrar_mensaje(conversacion.token)
            mensajes_descifrados.append({
                'usuario': msg.id_usuario.username,
                'contenido': texto_descifrado,
                'fecha': msg.fecha_envio,
                'es_tuyo': msg.id_usuario.id_usuario == usuario_actual.id_usuario
            })
        except:
            # Si falla el descifrado
            mensajes_descifrados.append({
                'usuario': msg.id_usuario.username,
                'contenido': '[Mensaje cifrado]',
                'fecha': msg.fecha_envio,
                'es_tuyo': msg.id_usuario.id_usuario == usuario_actual.id_usuario
            })
    
    if request.method == 'POST':
        contenido = request.POST.get('mensaje')
        
        if contenido:
            # Crear mensaje cifrado
            mensaje = Mensaje(
                id_conversacion=conversacion,
                id_usuario=usuario_actual,
                mensaje=''
            )
            mensaje.cifrar_mensaje(contenido, conversacion.token)
            mensaje.save()
            
            return redirect('chat', id_conversacion=id_conversacion)
    
    contexto = {
        'usuario': usuario_actual,
        'conversacion': conversacion,
        'mensajes': mensajes_descifrados,
    }
    
    return render(request, 'chat.html', contexto)


def index(request):
    """Redirigir a conversaciones si está autenticado, sino a login"""
    if es_autenticado(request):
        return redirect('conversaciones')
    return redirect('login')
