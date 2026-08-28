from django.urls import path

from . import views

app_name = "gmail"

urlpatterns = [
    path("conectar/", views.conectar, name="conectar"),
    path("callback/", views.callback, name="callback"),
    path("desconectar/", views.desconectar, name="desconectar"),
    path("sincronizar/", views.sincronizar, name="sincronizar"),
    path("estado/", views.estado, name="estado"),
    path("debug/", views.debug_correos, name="debug"),
    path("webhook/", views.webhook, name="webhook"),
]
