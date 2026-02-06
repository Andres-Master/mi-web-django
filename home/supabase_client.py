from supabase import create_client, Client
import os
from django.contrib.auth.hashers import make_password, check_password
from cryptography.fernet import Fernet
from django.conf import settings

# Detectar si estamos en desarrollo o producción
# Usar Supabase si estamos en producción (Render o PythonAnywhere)
USE_SUPABASE = (
    os.environ.get('USE_SUPABASE', '').lower() == 'true' or
    '/opt/render/' in str(settings.BASE_DIR) or  # Render
    '/home/' in str(settings.BASE_DIR)  # PythonAnywhere
)

# Inicializar cliente de Supabase
SUPABASE_URL = "https://db.nmggrmtioxrmwcxznjnf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRiLm5tZ2dybXRpb3hyY213Y3puam5mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzgyNTA4MzYsImV4cCI6MjA1MzgyNDgzNn0.YZhfXnAXE3bljGrL5sQ4zZqMVJn0YL8-IFaFDOJ5MJ0"

if USE_SUPABASE:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        supabase = None
else:
    supabase = None

# Usar Django ORM como fallback
from .models import Usuario as UsuarioModel, Conversacion as ConversacionModel, Mensaje as MensajeModel

class UsuarioService:
    @staticmethod
    def crear_usuario(username: str, email: str, contraseña: str):
        """Crear nuevo usuario"""
        if USE_SUPABASE and supabase:
            try:
                contraseña_hash = make_password(contraseña)
                response = supabase.table("home_usuario").insert({
                    "username": username,
                    "email": email,
                    "contraseña": contraseña_hash,
                    "fecha_creacion": "now()"
                }).execute()
                return response.data[0] if response.data else None
            except:
                pass
        
        # Fallback a SQLite/Django ORM
        usuario = UsuarioModel(username=username, email=email)
        usuario.set_password(contraseña)
        usuario.save()
        return {
            'id_usuario': usuario.id_usuario,
            'username': usuario.username,
            'email': usuario.email
        }

    @staticmethod
    def usuario_existe(username: str) -> bool:
        """Verificar si usuario existe"""
        if USE_SUPABASE and supabase:
            try:
                response = supabase.table("home_usuario").select("id_usuario").eq("username", username).execute()
                return len(response.data) > 0
            except:
                pass
        
        # Fallback a Django ORM
        return UsuarioModel.objects.filter(username=username).exists()

    @staticmethod
    def obtener_usuario(username: str):
        """Obtener usuario por username"""
        if USE_SUPABASE and supabase:
            try:
                response = supabase.table("home_usuario").select("*").eq("username", username).execute()
                return response.data[0] if response.data else None
            except:
                pass
        
        # Fallback a Django ORM
        usuario = UsuarioModel.objects.filter(username=username).first()
        if usuario:
            return {
                'id_usuario': usuario.id_usuario,
                'username': usuario.username,
                'email': usuario.email,
                'contraseña': usuario.contraseña
            }
        return None

    @staticmethod
    def verificar_contraseña(username: str, contraseña: str) -> bool:
        """Verificar contraseña de usuario"""
        usuario = UsuarioService.obtener_usuario(username)
        if not usuario:
            return False
        return check_password(contraseña, usuario["contraseña"])


class ConversacionService:
    @staticmethod
    def crear_conversacion(tipo: str, nombre: str = None, id_usuario_1: int = None, id_usuario_2: int = None):
        """Crear nueva conversación"""
        token = Fernet.generate_key().decode()
        
        if USE_SUPABASE and supabase:
            try:
                response = supabase.table("home_conversacion").insert({
                    "tipo": tipo,
                    "nombre": nombre,
                    "id_usuario_1": id_usuario_1,
                    "id_usuario_2": id_usuario_2,
                    "token": token,
                    "fecha_creacion": "now()"
                }).execute()
                return response.data[0] if response.data else None
            except:
                pass
        
        # Fallback a Django ORM
        conversacion = ConversacionModel(
            tipo=tipo,
            nombre=nombre,
            id_usuario_1_id=id_usuario_1,
            id_usuario_2_id=id_usuario_2,
            token=token
        )
        conversacion.save()
        return {
            'id_conversacion': conversacion.id_conversacion,
            'tipo': conversacion.tipo,
            'nombre': conversacion.nombre,
            'token': conversacion.token
        }

    @staticmethod
    def obtener_conversacion(id_conversacion: int):
        """Obtener conversación por ID"""
        if USE_SUPABASE and supabase:
            try:
                response = supabase.table("home_conversacion").select("*").eq("id_conversacion", id_conversacion).execute()
                return response.data[0] if response.data else None
            except:
                pass
        
        # Fallback a Django ORM
        conversacion = ConversacionModel.objects.filter(id_conversacion=id_conversacion).first()
        if conversacion:
            return {
                'id_conversacion': conversacion.id_conversacion,
                'tipo': conversacion.tipo,
                'nombre': conversacion.nombre,
                'token': conversacion.token
            }
        return None

    @staticmethod
    def obtener_conversaciones_publicas():
        """Obtener todas las conversaciones públicas"""
        if USE_SUPABASE and supabase:
            try:
                response = supabase.table("home_conversacion").select("*").eq("tipo", "publico").order("fecha_creacion", desc=True).execute()
                return response.data
            except:
                pass
        
        # Fallback a Django ORM
        conversaciones = ConversacionModel.objects.filter(tipo='publico').order_by('-fecha_creacion')
        return [{'id_conversacion': c.id_conversacion, 'tipo': c.tipo, 'nombre': c.nombre} for c in conversaciones]

    @staticmethod
    def obtener_conversaciones_usuario(id_usuario: int):
        """Obtener conversaciones de un usuario"""
        if USE_SUPABASE and supabase:
            try:
                publicas = supabase.table("home_conversacion").select("*").eq("tipo", "publico").order("fecha_creacion", desc=True).execute()
                privadas = supabase.table("home_conversacion").select("*").eq("tipo", "privado").filter(
                    "id_usuario_1", "eq", id_usuario
                ).or_(f"id_usuario_2.eq.{id_usuario}").order("fecha_creacion", desc=True).execute()
                return {'publicas': publicas.data, 'privadas': privadas.data}
            except:
                pass
        
        # Fallback a Django ORM
        from django.db.models import Q
        publicas = ConversacionModel.objects.filter(tipo='publico').order_by('-fecha_creacion')
        privadas = ConversacionModel.objects.filter(tipo='privado').filter(
            Q(id_usuario_1_id=id_usuario) | Q(id_usuario_2_id=id_usuario)
        ).order_by('-fecha_creacion')
        
        return {
            'publicas': [{'id_conversacion': c.id_conversacion, 'tipo': c.tipo, 'nombre': c.nombre} for c in publicas],
            'privadas': [{'id_conversacion': c.id_conversacion, 'tipo': c.tipo, 'nombre': c.nombre} for c in privadas]
        }

    @staticmethod
    def conversacion_privada_existe(id_usuario_1: int, id_usuario_2: int) -> bool:
        """Verificar si una conversación privada ya existe"""
        if USE_SUPABASE and supabase:
            try:
                response = supabase.table("home_conversacion").select("id_conversacion").eq("tipo", "privado").filter(
                    "id_usuario_1", "eq", id_usuario_1
                ).filter("id_usuario_2", "eq", id_usuario_2).execute()
                if response.data:
                    return True
                response = supabase.table("home_conversacion").select("id_conversacion").eq("tipo", "privado").filter(
                    "id_usuario_1", "eq", id_usuario_2
                ).filter("id_usuario_2", "eq", id_usuario_1).execute()
                return len(response.data) > 0
            except:
                pass
        
        # Fallback a Django ORM
        from django.db.models import Q
        existe = ConversacionModel.objects.filter(tipo='privado').filter(
            Q(id_usuario_1_id=id_usuario_1, id_usuario_2_id=id_usuario_2) |
            Q(id_usuario_1_id=id_usuario_2, id_usuario_2_id=id_usuario_1)
        ).exists()
        return existe


class MensajeService:
    @staticmethod
    def crear_mensaje(id_conversacion: int, id_usuario: int, texto_plano: str):
        """Crear nuevo mensaje (cifrado)"""
        conversacion = ConversacionService.obtener_conversacion(id_conversacion)
        if not conversacion:
            return None
        
        token = conversacion["token"]
        f = Fernet(token.encode() if isinstance(token, str) else token)
        mensaje_cifrado = f.encrypt(texto_plano.encode()).decode()
        
        if USE_SUPABASE and supabase:
            try:
                response = supabase.table("home_mensaje").insert({
                    "id_conversacion": id_conversacion,
                    "id_usuario": id_usuario,
                    "mensaje": mensaje_cifrado,
                    "fecha_envio": "now()"
                }).execute()
                return response.data[0] if response.data else None
            except:
                pass
        
        # Fallback a Django ORM
        mensaje = MensajeModel(
            id_conversacion_id=id_conversacion,
            id_usuario_id=id_usuario,
            mensaje=mensaje_cifrado
        )
        mensaje.save()
        return {'id_mensaje': mensaje.id_mensaje}

    @staticmethod
    def obtener_mensajes(id_conversacion: int):
        """Obtener todos los mensajes de una conversación"""
        if USE_SUPABASE and supabase:
            try:
                response = supabase.table("home_mensaje").select("*").eq("id_conversacion", id_conversacion).order("fecha_envio", desc=False).execute()
                return response.data
            except:
                pass
        
        # Fallback a Django ORM
        mensajes = MensajeModel.objects.filter(id_conversacion_id=id_conversacion).order_by('fecha_envio')
        return [{
            'id_mensaje': m.id_mensaje,
            'id_conversacion': m.id_conversacion_id,
            'id_usuario': m.id_usuario_id,
            'mensaje': m.mensaje,
            'fecha_envio': m.fecha_envio.isoformat()
        } for m in mensajes]

    @staticmethod
    def descifrar_mensaje(mensaje_cifrado: str, token: str) -> str:
        """Descifrar un mensaje"""
        try:
            f = Fernet(token.encode() if isinstance(token, str) else token)
            texto_descifrado = f.decrypt(mensaje_cifrado.encode()).decode()
            return texto_descifrado
        except Exception as e:
            print(f"Error al descifrar: {e}")
            return mensaje_cifrado

