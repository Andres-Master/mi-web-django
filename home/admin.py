from django.contrib import admin
from .models import Mensaje

@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ['nombre_usuario', 'contenido', 'timestamp']
    search_fields = ['nombre_usuario', 'contenido']
