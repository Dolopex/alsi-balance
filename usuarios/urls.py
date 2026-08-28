from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("registro/", views.registrar_usuario, name="registro"),
    path("perfil/", views.perfil, name="perfil"),
]
