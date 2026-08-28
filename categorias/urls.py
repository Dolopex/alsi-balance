from django.urls import path

from . import views

app_name = "categorias"

urlpatterns = [
    path("", views.CategoriaListView.as_view(), name="lista"),
    path("nueva/", views.CategoriaCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", views.CategoriaUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", views.CategoriaDeleteView.as_view(), name="eliminar"),
]
