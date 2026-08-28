from django.urls import path

from . import views

app_name = "notificaciones"

urlpatterns = [
    path("subscribe/", views.subscribe, name="subscribe"),
    path("unsubscribe/", views.unsubscribe, name="unsubscribe"),
    path("toggle/", views.toggle, name="toggle"),
    path("probar/", views.probar, name="probar"),
]
