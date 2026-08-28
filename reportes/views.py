from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from core.models import TipoMovimiento
from movimientos.selectors import listar_movimientos

from .exporters import (
    exportar_egresos,
    exportar_ingresos,
    exportar_movimientos,
    exportar_reporte_financiero,
    workbook_to_response,
)
from .services import (
    generar_reporte,
    reporte_anio,
    reporte_mes_actual,
    reporte_mes_anterior,
)


def _resolver_periodo(request) -> tuple[date, date]:
    rango = request.GET.get("rango", "mes")
    hoy = timezone.localdate()
    if rango == "mes_anterior":
        if hoy.month == 1:
            mes = hoy.replace(year=hoy.year - 1, month=12)
        else:
            mes = hoy.replace(month=hoy.month - 1)
        desde = mes.replace(day=1)
        if desde.month == 12:
            fin = desde.replace(year=desde.year + 1, month=1)
        else:
            fin = desde.replace(month=desde.month + 1)
        fin = fin - __import__("datetime").timedelta(days=1)
        return desde, fin
    if rango == "anio":
        return hoy.replace(month=1, day=1), hoy
    if rango == "personalizado":
        desde = request.GET.get("desde") or hoy.isoformat()
        hasta = request.GET.get("hasta") or hoy.isoformat()
        return date.fromisoformat(desde), date.fromisoformat(hasta)
    # default mes actual
    desde = hoy.replace(day=1)
    return desde, hoy


@login_required
def reporte_view(request):
    fecha_desde, fecha_hasta = _resolver_periodo(request)
    reporte = generar_reporte(fecha_desde, fecha_hasta)
    reporte["rango_activo"] = request.GET.get("rango", "mes")
    return render(request, "reportes/reporte.html", reporte)


@login_required
def exportar_movimientos_excel(request):
    filtros = {
        "tipo": request.GET.get("tipo") or None,
        "fecha_desde": request.GET.get("fecha_desde") or None,
        "fecha_hasta": request.GET.get("fecha_hasta") or None,
        "categoria": request.GET.get("categoria") or None,
        "q": request.GET.get("q") or None,
    }
    qs = listar_movimientos(filtros)
    wb = exportar_movimientos(qs)
    return workbook_to_response(wb, f"alsi_movimientos_{timezone.now():%Y%m%d_%H%M}.xlsx")


@login_required
def exportar_ingresos_excel(request):
    filtros = {
        "fecha_desde": request.GET.get("fecha_desde") or None,
        "fecha_hasta": request.GET.get("fecha_hasta") or None,
    }
    qs = listar_movimientos(filtros).filter(tipo=TipoMovimiento.INGRESO)
    wb = exportar_ingresos(qs)
    return workbook_to_response(wb, f"alsi_ingresos_{timezone.now():%Y%m%d_%H%M}.xlsx")


@login_required
def exportar_egresos_excel(request):
    filtros = {
        "fecha_desde": request.GET.get("fecha_desde") or None,
        "fecha_hasta": request.GET.get("fecha_hasta") or None,
    }
    qs = listar_movimientos(filtros).filter(tipo=TipoMovimiento.EGRESO)
    wb = exportar_egresos(qs)
    return workbook_to_response(wb, f"alsi_egresos_{timezone.now():%Y%m%d_%H%M}.xlsx")


@login_required
def exportar_reporte_excel(request):
    fecha_desde, fecha_hasta = _resolver_periodo(request)
    reporte = generar_reporte(fecha_desde, fecha_hasta)
    wb = exportar_reporte_financiero(reporte)
    return workbook_to_response(
        wb,
        f"alsi_reporte_{fecha_desde:%Y%m%d}_{fecha_hasta:%Y%m%d}.xlsx",
    )
