"""Configuracion de URLs del proyecto ALSI BALANCE."""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView

from core.views import service_worker

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sw.js", service_worker, name="service_worker"),
    path("", RedirectView.as_view(pattern_name="dashboard:home", permanent=False)),
    path("usuarios/", include(("usuarios.urls", "usuarios"))),
    path("movimientos/", include(("movimientos.urls", "movimientos"))),
    path("categorias/", include(("categorias.urls", "categorias"))),
    path("dashboard/", include(("dashboard.urls", "dashboard"))),
    path("reportes/", include(("reportes.urls", "reportes"))),
    path("gmail/", include(("gmail_integration.urls", "gmail"))),
    path("configuracion/", include(("core.urls", "core"))),
    path("notificaciones/", include(("notificaciones.urls", "notificaciones"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = f"{settings.APP_NAME} — Administracion"
admin.site.site_title = f"{settings.APP_NAME} Admin"
admin.site.index_title = f"{settings.APP_COMPANY}"
