from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages

# Create your views here.

def login_view(request):
    if request.user.is_authenticated:
        # Redirigir al chat si ya está logueado
        return redirect(reverse("chat:chats"))
    
    if request.method == 'POST':
        username = request.POST["usuario"]
        password = request.POST["contraseña"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return HttpResponseRedirect(reverse("chat:chats"))
        else:
            return render(request, 'index/login.html', {"msj":"Los datos ingresados son incorrectos"})
    return render(request, 'index/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Se cerro la sesion correctamente")
    return redirect(reverse("index:login"))
    # return render(request, "index/login.html", {"msj":"la sesion de cerro correctamente"})

def recuperar_contraseña(request):
    return  render(request, 'index/recuperar_contraseña.html')