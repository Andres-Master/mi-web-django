"""Session backend que usa Supabase API en lugar de la base de datos"""

from django.contrib.sessions.backends.base import SessionBase, CreateError
from django.contrib.sessions.models import Session
from django.utils import timezone
from .supabase_client import DjangoSessionService
import json
from datetime import datetime


class SupabaseSessionBackend:
    """Backend de sesiones que almacena en Supabase a través de la API REST"""
    
    def load(self, session_key):
        """Cargar datos de sesión desde Supabase"""
        try:
            session = DjangoSessionService.obtener_sesion(session_key)
            if session:
                # Verificar que no esté expirada
                expire_date = datetime.fromisoformat(session['expire_date'].replace('Z', '+00:00'))
                if expire_date > timezone.now():
                    return session['session_data']
                else:
                    # Sesión expirada, eliminarla
                    DjangoSessionService.eliminar_sesion(session_key)
            return {}
        except Exception as e:
            print(f"Error cargando sesión: {e}")
            return {}
    
    def save(self, session_key, session_dict, expire_date):
        """Guardar datos de sesión en Supabase"""
        try:
            session_data = json.dumps(session_dict)
            expire_date_str = expire_date.isoformat() if hasattr(expire_date, 'isoformat') else expire_date
            
            # Verificar si ya existe
            existing = DjangoSessionService.obtener_sesion(session_key)
            if existing:
                DjangoSessionService.actualizar_sesion(session_key, session_data, expire_date_str)
            else:
                DjangoSessionService.crear_sesion(session_key, session_data, expire_date_str)
            return True
        except Exception as e:
            print(f"Error guardando sesión: {e}")
            return False
    
    def delete(self, session_key):
        """Eliminar una sesión desde Supabase"""
        try:
            DjangoSessionService.eliminar_sesion(session_key)
        except Exception as e:
            print(f"Error eliminando sesión: {e}")
    
    def exists(self, session_key):
        """Verificar si una sesión existe"""
        try:
            session = DjangoSessionService.obtener_sesion(session_key)
            if session:
                expire_date = datetime.fromisoformat(session['expire_date'].replace('Z', '+00:00'))
                return expire_date > timezone.now()
            return False
        except Exception as e:
            print(f"Error verificando sesión: {e}")
            return False
    
    def clear_expired(self):
        """Eliminar sesiones expiradas"""
        try:
            DjangoSessionService.limpiar_sesiones_expiradas()
        except Exception as e:
            print(f"Error limpiando sesiones expiradas: {e}")
