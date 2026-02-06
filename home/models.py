from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from cryptography.fernet import Fernet
import os

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    contraseña = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def set_password(self, raw_password):
        """Encriptar la contraseña"""
        self.contraseña = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Verificar la contraseña"""
        return check_password(raw_password, self.contraseña)
    
    def __str__(self):
        return self.username
    
    class Meta:
        ordering = ['-fecha_creacion']


class Conversacion(models.Model):
    TIPOS = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
    ]
    
    id_conversacion = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    nombre = models.CharField(max_length=200, null=True, blank=True)
    id_usuario_1 = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='conversaciones_1',
        null=True,
        blank=True
    )
    id_usuario_2 = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='conversaciones_2',
        null=True,
        blank=True
    )
    token = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def generar_token(self):
        """Generar un token de encriptación"""
        self.token = Fernet.generate_key().decode()
        return self.token
    
    def __str__(self):
        if self.tipo == 'publico':
            return f"{self.nombre} (Público)"
        else:
            return f"Privado: {self.id_usuario_1.username} - {self.id_usuario_2.username}"
    
    class Meta:
        ordering = ['-fecha_creacion']


class Mensaje(models.Model):
    id_mensaje = models.AutoField(primary_key=True)
    id_conversacion = models.ForeignKey(
        Conversacion, 
        on_delete=models.CASCADE,
        related_name='mensajes'
    )
    id_usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE
    )
    mensaje = models.TextField()  # Mensaje cifrado
    fecha_envio = models.DateTimeField(auto_now_add=True)
    
    def cifrar_mensaje(self, texto_plano, token):
        """Cifrar el mensaje con el token de la conversación"""
        try:
            f = Fernet(token.encode() if isinstance(token, str) else token)
            self.mensaje = f.encrypt(texto_plano.encode()).decode()
        except Exception as e:
            print(f"Error al cifrar: {e}")
            self.mensaje = texto_plano
    
    def descifrar_mensaje(self, token):
        """Descifrar el mensaje para visualizar"""
        try:
            f = Fernet(token.encode() if isinstance(token, str) else token)
            texto_descifrado = f.decrypt(self.mensaje.encode()).decode()
            return texto_descifrado
        except Exception as e:
            print(f"Error al descifrar: {e}")
            return self.mensaje
    
    def __str__(self):
        return f"{self.id_usuario.username} - {self.fecha_envio}"
    
    class Meta:
        ordering = ['fecha_envio']
