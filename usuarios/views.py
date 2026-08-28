from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .forms import UsuarioCrearForm


class LoginView(auth_views.LoginView):
    template_name = "usuarios/login.html"
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("usuarios:login")


@login_required
def perfil(request):
    return render(request, "usuarios/perfil.html")


def registrar_usuario(request):
    """Crea un nuevo usuario. El primer usuario siempre es administrador."""
    if request.method == "POST":
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario {user.username} creado correctamente.")
            return redirect("usuarios:login")
    else:
        form = UsuarioCrearForm()
    return render(request, "usuarios/registro.html", {"form": form})
