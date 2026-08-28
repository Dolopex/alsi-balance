"""Vistas de configuración del sistema."""

from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET

from core.models import ConfiguracionSistema
from core.selectors import obtener_configuracion
from core.services import calcular_saldo
from movimientos.selectors import listar_movimientos


@login_required
def configuracion_view(request):
    """Pantalla de configuración: saldo inicial y diagnóstico."""
    config = obtener_configuracion()
    movs = listar_movimientos()
    ingresos = sum(
        m.valor for m in movs if m.tipo == "INGRESO"
    )
    egresos = sum(
        m.valor for m in movs if m.tipo == "EGRESO"
    )
    saldo_calculado = config.saldo_inicial + ingresos - egresos

    if request.method == "POST":
        saldo_in = request.POST.get("saldo_inicial", "0")
        try:
            from decimal import Decimal
            saldo = Decimal(str(saldo_in).replace(".", "").replace(",", "."))
        except Exception:
            saldo = None
        if saldo is None or saldo < 0:
            messages.error(request, "El saldo inicial debe ser un número válido.")
            return redirect("core:configuracion")

        if config is None:
            config = ConfiguracionSistema()
        config.saldo_inicial = saldo
        config.banco = request.POST.get("banco", "Bancolombia")
        config.nombre_cuenta = request.POST.get("nombre_cuenta", "Cuenta principal")
        # Solo un administrador puede editar
        if request.user.es_administrador:
            config.save()
            messages.success(request, "Configuracion actualizada.")
            return redirect("core:configuracion")
        else:
            messages.error(request, "Solo un administrador puede modificar la configuracion.")
            return redirect("dashboard:home")

    ctx = {
        "config": config,
        "total_ingresos": ingresos,
        "total_egresos": egresos,
        "saldo_calculado": saldo_calculado,
    }
    return render(request, "core/configuracion.html", ctx)


@require_GET
def service_worker(request):
    """Sirve /sw.js desde raiz para que el Service Worker tenga scope '/'.

    Push API requiere que el SW controle todo el origen; servirlo bajo
    /static/js/ solo da scope a esa carpeta y el push falla.
    """
    candidates = []
    if getattr(settings, "STATIC_ROOT", None):
        candidates.append(Path(settings.STATIC_ROOT) / "js" / "sw.js")
    if getattr(settings, "STATICFILES_DIRS", None):
        for d in settings.STATICFILES_DIRS:
            candidates.append(Path(d) / "js" / "sw.js")

    sw_path = next((p for p in candidates if p.exists()), None)
    if sw_path is None:
        return HttpResponseNotFound("Service worker no encontrado.")

    response = HttpResponse(sw_path.read_bytes(), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response
