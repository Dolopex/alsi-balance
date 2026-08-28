from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
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


MESES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _parse_int(value, default=None):
    """Convierte un query param a int, retorna default si falla."""
    if not value:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _resolver_periodo_mes(request):
    """Resuelve año y mes de query params.

    Retorna (anio, mes, primer_dia, ultimo_dia) o (None, None, None, None)
    si los params son invalidos.
    """
    hoy = timezone.localdate()
    anio = _parse_int(request.GET.get("anio"), hoy.year)
    mes = _parse_int(request.GET.get("mes"), hoy.month)
    if not (1 <= mes <= 12) or anio < 1900 or anio > 2200:
        return None, None, None, None
    primer_dia = date(anio, mes, 1)
    if mes == 12:
        ultimo_dia = date(anio + 1, 1, 1)
    else:
        ultimo_dia = date(anio, mes + 1, 1)
    from datetime import timedelta
    ultimo_dia = ultimo_dia - timedelta(days=1)
    return anio, mes, primer_dia, ultimo_dia


def _resolver_periodo(request) -> tuple[date, date]:
    """Resuelve rango completo desde query params."""
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
        from datetime import timedelta
        fin = fin - timedelta(days=1)
        return desde, fin
    if rango == "anio":
        return hoy.replace(month=1, day=1), hoy
    if rango == "personalizado":
        desde = request.GET.get("desde") or hoy.isoformat()
        hasta = request.GET.get("hasta") or hoy.isoformat()
        return date.fromisoformat(desde), date.fromisoformat(hasta)
    # default mes actual
    return hoy.replace(day=1), hoy


@login_required
def reporte_view(request):
    fecha_desde, fecha_hasta = _resolver_periodo(request)
    reporte = generar_reporte(fecha_desde, fecha_hasta)
    reporte["rango_activo"] = request.GET.get("rango", "mes")
    return render(request, "reportes/reporte.html", reporte)


def _subtitulo_mes(anio, mes):
    """Genera el subtitulo del Excel: 'Agosto 2026'."""
    if not anio or not mes:
        return ""
    return f"{MESES_ES[mes]} {anio}"


@login_required
def exportar_movimientos_excel(request):
    """Exporta todos los movimientos (o un mes especifico si se pasa anio+mes)."""
    anio, mes, desde, hasta = _resolver_periodo_mes(request)
    filtros = {
        "tipo": request.GET.get("tipo") or None,
        "fecha_desde": desde.isoformat() if desde else (request.GET.get("fecha_desde") or None),
        "fecha_hasta": hasta.isoformat() if hasta else (request.GET.get("fecha_hasta") or None),
        "categoria": request.GET.get("categoria") or None,
        "q": request.GET.get("q") or None,
    }
    qs = listar_movimientos(filtros)
    subtitulo = _subtitulo_mes(anio, mes) if desde else ""
    wb = exportar_movimientos(qs, "Listado de Movimientos", subtitulo)
    sufijo = f"_{anio}{mes:02d}" if anio and mes else ""
    return workbook_to_response(wb, f"alsi_movimientos{sufijo}_{timezone.now():%Y%m%d_%H%M}.xlsx")


@login_required
def exportar_ingresos_excel(request):
    """Exporta solo ingresos."""
    anio, mes, desde, hasta = _resolver_periodo_mes(request)
    filtros = {
        "fecha_desde": desde.isoformat() if desde else (request.GET.get("fecha_desde") or None),
        "fecha_hasta": hasta.isoformat() if hasta else (request.GET.get("fecha_hasta") or None),
    }
    qs = listar_movimientos(filtros).filter(tipo=TipoMovimiento.INGRESO)
    subtitulo = _subtitulo_mes(anio, mes) if desde else ""
    wb = exportar_ingresos(qs, subtitulo)
    sufijo = f"_{anio}{mes:02d}" if anio and mes else ""
    return workbook_to_response(wb, f"alsi_ingresos{sufijo}_{timezone.now():%Y%m%d_%H%M}.xlsx")


@login_required
def exportar_egresos_excel(request):
    """Exporta solo egresos."""
    anio, mes, desde, hasta = _resolver_periodo_mes(request)
    filtros = {
        "fecha_desde": desde.isoformat() if desde else (request.GET.get("fecha_desde") or None),
        "fecha_hasta": hasta.isoformat() if hasta else (request.GET.get("fecha_hasta") or None),
    }
    qs = listar_movimientos(filtros).filter(tipo=TipoMovimiento.EGRESO)
    subtitulo = _subtitulo_mes(anio, mes) if desde else ""
    wb = exportar_egresos(qs, subtitulo)
    sufijo = f"_{anio}{mes:02d}" if anio and mes else ""
    return workbook_to_response(wb, f"alsi_egresos{sufijo}_{timezone.now():%Y%m%d_%H%M}.xlsx")


@login_required
def exportar_reporte_excel(request):
    """Exporta el reporte financiero completo."""
    fecha_desde, fecha_hasta = _resolver_periodo(request)
    reporte = generar_reporte(fecha_desde, fecha_hasta)
    wb = exportar_reporte_financiero(reporte)
    return workbook_to_response(
        wb,
        f"alsi_reporte_{fecha_desde:%Y%m%d}_{fecha_hasta:%Y%m%d}.xlsx",
    )