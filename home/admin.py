from django.contrib import admin
from .models import Usuario, Conversacion, Mensaje

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'fecha_creacion']
    search_fields = ['username', 'email']
    readonly_fields = ['fecha_creacion', 'id_usuario']

@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ['id_conversacion', 'tipo', 'nombre', 'fecha_creacion']
    search_fields = ['nombre']
    readonly_fields = ['fecha_creacion', 'id_conversacion']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('tipo', 'nombre')
        }),
        ('Usuarios (solo privado)', {
            'fields': ('id_usuario_1', 'id_usuario_2')
        }),
        ('Encriptación', {
            'fields': ('token',)
        }),
        ('Fecha', {
            'fields': ('fecha_creacion',)
        }),
    )

@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ['id_usuario', 'id_conversacion', 'fecha_envio']
    search_fields = ['id_usuario__username']
    readonly_fields = ['fecha_envio', 'id_mensaje']
    
    fieldsets = (
        ('Información del mensaje', {
            'fields': ('id_conversacion', 'id_usuario', 'mensaje')
        }),
        ('Fecha', {
            'fields': ('fecha_envio',)
        }),
    )
