from django.db import models
from django.utils import timezone

class Mensaje(models.Model):
    nombre_usuario = models.CharField(max_length=100)
    contenido = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.nombre_usuario}: {self.contenido[:50]}"
