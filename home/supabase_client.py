from supabase import create_client, Client
import os
from django.contrib.auth.hashers import make_password, check_password
from cryptography.fernet import Fernet

# Inicializar cliente de Supabase (único backend)
SUPABASE_URL = "https://nmggrmtioxrmwcxznjnf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5tZ2dybXRpb3hybXdjeHpuam5mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzOTYwNzQsImV4cCI6MjA4NTk3MjA3NH0.K150PXNMeaMgc5PqQLZgeJnRBAo6umUNiJj1XHfMVT0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class UsuarioService:
    @staticmethod
    def crear_usuario(username: str, email: str, contraseña: str):
        """Crear nuevo usuario"""
        contraseña_hash = make_password(contraseña)
        response = supabase.table("home_usuario").insert({
            "username": username,
            "email": email,
            "contraseña": contraseña_hash,
            "fecha_creacion": "now()"
        }).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def usuario_existe(username: str) -> bool:
        """Verificar si usuario existe"""
        response = supabase.table("home_usuario").select("id_usuario").eq("username", username).execute()
        return len(response.data) > 0

    @staticmethod
    def obtener_usuario(username: str):
        """Obtener usuario por username"""
        response = supabase.table("home_usuario").select("*").eq("username", username).execute()
        return response.data[0] if response.data else None

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
        response = supabase.table("home_conversacion").insert({
            "tipo": tipo,
            "nombre": nombre,
            "id_usuario_1": id_usuario_1,
            "id_usuario_2": id_usuario_2,
            "token": token,
            "fecha_creacion": "now()"
        }).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def obtener_conversacion(id_conversacion: int):
        """Obtener conversación por ID"""
        response = supabase.table("home_conversacion").select("*").eq("id_conversacion", id_conversacion).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def obtener_conversaciones_publicas():
        """Obtener todas las conversaciones públicas"""
        response = supabase.table("home_conversacion").select("*").eq("tipo", "publico").order("fecha_creacion", desc=True).execute()
        return response.data

    @staticmethod
    def obtener_conversaciones_usuario(id_usuario: int):
        """Obtener conversaciones de un usuario (públicas y privadas)"""
        # Públicas
        publicas = supabase.table("home_conversacion").select("*").eq("tipo", "publico").order("fecha_creacion", desc=True).execute()
        
        # Privadas (donde el usuario es participante)
        privadas = supabase.table("home_conversacion").select("*").eq("tipo", "privado").filter(
            "id_usuario_1", "eq", id_usuario
        ).or_(f"id_usuario_2.eq.{id_usuario}").order("fecha_creacion", desc=True).execute()
        
        return {
            "publicas": publicas.data,
            "privadas": privadas.data
        }

    @staticmethod
    def conversacion_privada_existe(id_usuario_1: int, id_usuario_2: int) -> bool:
        """Verificar si una conversación privada ya existe entre dos usuarios"""
        response = supabase.table("home_conversacion").select("id_conversacion").eq("tipo", "privado").filter(
            "id_usuario_1", "eq", id_usuario_1
        ).filter("id_usuario_2", "eq", id_usuario_2).execute()
        
        if response.data:
            return True
        
        # También verificar al revés (usuario_2, usuario_1)
        response = supabase.table("home_conversacion").select("id_conversacion").eq("tipo", "privado").filter(
            "id_usuario_1", "eq", id_usuario_2
        ).filter("id_usuario_2", "eq", id_usuario_1).execute()
        
        return len(response.data) > 0


class MensajeService:
    @staticmethod
    def crear_mensaje(id_conversacion: int, id_usuario: int, texto_plano: str):
        """Crear nuevo mensaje (cifrado)"""
        # Obtener token de la conversación
        conversacion = ConversacionService.obtener_conversacion(id_conversacion)
        if not conversacion:
            return None
        
        token = conversacion["token"]
        # Cifrar mensaje
        f = Fernet(token.encode() if isinstance(token, str) else token)
        mensaje_cifrado = f.encrypt(texto_plano.encode()).decode()
        
        response = supabase.table("home_mensaje").insert({
            "id_conversacion": id_conversacion,
            "id_usuario": id_usuario,
            "mensaje": mensaje_cifrado,
            "fecha_envio": "now()"
        }).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def obtener_mensajes(id_conversacion: int):
        """Obtener todos los mensajes de una conversación"""
        response = supabase.table("home_mensaje").select("*").eq("id_conversacion", id_conversacion).order("fecha_envio", desc=False).execute()
        return response.data

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


class DjangoSessionService:
    """Servicio para manejar sesiones de Django a través de Supabase API"""
    
    @staticmethod
    def crear_sesion(session_key: str, session_data: str, expire_date: str):
        """Crear una sesión en Supabase"""
        try:
            response = supabase.table("django_session").insert({
                "session_key": session_key,
                "session_data": session_data,
                "expire_date": expire_date
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error al crear sesión: {e}")
            return None
    
    @staticmethod
    def obtener_sesion(session_key: str):
        """Obtener una sesión desde Supabase"""
        try:
            response = supabase.table("django_session").select("*").eq("session_key", session_key).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error al obtener sesión: {e}")
            return None
    
    @staticmethod
    def actualizar_sesion(session_key: str, session_data: str, expire_date: str):
        """Actualizar una sesión en Supabase"""
        try:
            response = supabase.table("django_session").update({
                "session_data": session_data,
                "expire_date": expire_date
            }).eq("session_key", session_key).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error al actualizar sesión: {e}")
            return None
    
    @staticmethod
    def eliminar_sesion(session_key: str):
        """Eliminar una sesión desde Supabase"""
        try:
            supabase.table("django_session").delete().eq("session_key", session_key).execute()
            return True
        except Exception as e:
            print(f"Error al eliminar sesión: {e}")
            return False
    
    @staticmethod
    def limpiar_sesiones_expiradas():
        """Eliminar todas las sesiones expiradas"""
        try:
            from datetime import datetime
            ahora = datetime.utcnow().isoformat()
            supabase.table("django_session").delete().lt("expire_date", ahora).execute()
            return True
        except Exception as e:
            print(f"Error al limpiar sesiones: {e}")
            return False


