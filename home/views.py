from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Mensaje

def index(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        mensaje = request.POST.get('mensaje')
        
        if nombre and mensaje:
            Mensaje.objects.create(nombre_usuario=nombre, contenido=mensaje)
            return redirect('index')
    
    mensajes = Mensaje.objects.all()
    return render(request, 'index.html', {'mensajes': mensajes})
