from django.shortcuts import render, redirect
from django.contrib.auth import logout
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

def home(request):
    return render(request, 'home.html')


def exit(request):
    logout(request)
    return redirect('home')

def register(request):
    data = {
        'form': CustomUserCreationForm()
    }
    if request.method == 'POST':
        user_creation_form = CustomUserCreationForm(data=request.POST)

        if user_creation_form.is_valid():
            user_creation_form.save()

            user=authenticate(username=user_creation_form.cleaned_data['username'], password=user_creation_form.cleaned_data['password1'])
            login(request, user)
            return redirect('home')
    return render(request, 'registration/register.html', data)

def contacto(request):
    return render(request, 'contacto.html')


@login_required
def perfil(request):
    usuario = request.user
    form = None  # Inicializar la variable form fuera del bloque condicional

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('perfil')
    else:
        form = PasswordChangeForm(request.user)  # Si el método no es POST, inicializar el form aquí

    return render(request, 'perfil.html', {'usuario': usuario, 'form': form})

def eliminar_cuenta(request):
    usuario = request.user
    usuario.delete()
    logout(request)
    messages.success(request, 'Tu cuenta ha sido eliminada.')
    return redirect('home')