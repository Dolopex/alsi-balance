from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.configuracion_view, name="configuracion"),
]
