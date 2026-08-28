from django.urls import path

from . import views

app_name = "movimientos"

urlpatterns = [
    path("", views.MovimientoListView.as_view(), name="lista"),
    path("nuevo/", views.MovimientoCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.MovimientoDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.MovimientoUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", views.MovimientoDeleteView.as_view(), name="eliminar"),
    path(
        "<int:pk>/conciliacion/",
        views.cambiar_estado_conciliacion,
        name="conciliar",
    ),
]
