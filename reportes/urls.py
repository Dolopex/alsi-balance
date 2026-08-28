from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.reporte_view, name="reporte"),
    path("exportar/movimientos.xlsx", views.exportar_movimientos_excel, name="exportar_movimientos"),
    path("exportar/ingresos.xlsx", views.exportar_ingresos_excel, name="exportar_ingresos"),
    path("exportar/egresos.xlsx", views.exportar_egresos_excel, name="exportar_egresos"),
    path("exportar/reporte.xlsx", views.exportar_reporte_excel, name="exportar_reporte"),
]
