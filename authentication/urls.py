from django.urls import path
from .views import home, exit, register, contacto,perfil,eliminar_cuenta,analistas

urlpatterns = [
    path('', home, name='home'),
    path('analistas/',analistas, name='analistas'),
    path('logout/', exit, name='exit'),
    path('register/', register, name='register'),
    path('contacto/', contacto, name='contacto'),
    path('perfil/', perfil, name='perfil'),
    path('eliminar-cuenta/', eliminar_cuenta, name='eliminar_cuenta'),
]
