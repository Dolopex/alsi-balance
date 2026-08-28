"""Configuracion de URLs del proyecto ALSI BALANCE."""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import path, include
from django.views.generic import RedirectView

from core.views import healthz, service_worker

OFFLINE_HTML = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b2545">
<title>Sin conexion - ALSI Balance</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;display:flex;align-items:center;
justify-content:center;min-height:100vh;margin:0;background:#f8fafc;color:#1e293b;
text-align:center;padding:24px}
.c{max-width:420px;background:white;padding:40px;border-radius:16px;
box-shadow:0 4px 24px rgba(0,0,0,0.08)}
.icon{font-size:48px;margin-bottom:16px}
h1{color:#0b3666;margin:0 0 16px;font-size:24px}
p{color:#64748b;margin:8px 0;line-height:1.5}
.btn{display:inline-block;margin-top:20px;padding:12px 24px;background:#1f5fa8;
color:white;text-decoration:none;border-radius:8px;font-weight:600}
.btn:hover{background:#0b3666}
</style></head><body>
<div class="c">
  <div class="icon">&#9888;&#65039;</div>
  <h1>Sin conexion</h1>
  <p>No podemos conectar con el servidor en este momento.</p>
  <p>Verifica tu conexion a internet e intenta de nuevo.</p>
  <a href="/" class="btn">&#8634; Reintentar</a>
</div>
</body></html>"""


def offline_view(request):
    return HttpResponse(OFFLINE_HTML, content_type="text/html; charset=utf-8")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("sw.js", service_worker, name="service_worker"),
    path("healthz/", healthz, name="healthz"),
    path("offline/", offline_view, name="offline"),
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
