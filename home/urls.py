from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # Autenticación
    path('registro/', views.registro, name='registro'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    # Conversaciones
    path('conversaciones/', views.conversaciones, name='conversaciones'),
    path('conversacion/crear-publica/', views.crear_conversacion_publica, name='crear_publica'),
    path('conversacion/crear-privada/', views.crear_conversacion_privada, name='crear_privada'),
    
    # Chat
    path('chat/<int:id_conversacion>/', views.chat, name='chat'),
]
