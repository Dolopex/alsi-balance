"""Servicios de generacion de reportes financieros."""

from collections import OrderedDict
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from core.models import ConfiguracionSistema, TipoMovimiento
from core.selectors import obtener_saldo_inicial
from movimientos.models import Movimiento
from movimientos.selectors import listar_movimientos


def _rango_mes(fecha: date) -> tuple[date, date]:
    inicio = fecha.replace(day=1)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1) - __import__("datetime").timedelta(days=1)
    else:
        fin = inicio.replace(month=inicio.month + 1) - __import__("datetime").timedelta(days=1)
    return inicio, fin


def _totalizar(qs) -> dict:
    ingresos = qs.filter(tipo=TipoMovimiento.INGRESO).aggregate(s=Sum("valor"))["s"] or Decimal("0.00")
    egresos = qs.filter(tipo=TipoMovimiento.EGRESO).aggregate(s=Sum("valor"))["s"] or Decimal("0.00")
    return {"ingresos": ingresos, "egresos": egresos, "balance": ingresos - egresos}


def _por_categoria(qs, tipo: str):
    return (
        qs.filter(tipo=tipo, categoria__isnull=False)
        .values("categoria__nombre")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )


def generar_reporte(fecha_desde: date, fecha_hasta: date) -> dict:
    """Reporte completo para el rango solicitado."""
    config = ConfiguracionSistema.objects.first()
    saldo_inicial_global = obtener_saldo_inicial()

    # Movimientos anteriores al rango (para acumular saldo)
    qs_previos = Movimiento.objects.filter(fecha__lt=fecha_desde)
    totales_previos = _totalizar(qs_previos)
    saldo_inicial_periodo = saldo_inicial_global + totales_previos["balance"]

    # Movimientos dentro del rango
    qs = Movimiento.objects.filter(fecha__gte=fecha_desde, fecha__lte=fecha_hasta).order_by("fecha", "id")
    totales = _totalizar(qs)

    ingresos_cat = list(_por_categoria(qs, TipoMovimiento.INGRESO))
    egresos_cat = list(_por_categoria(qs, TipoMovimiento.EGRESO))

    saldo_final = saldo_inicial_periodo + totales["balance"]

    return {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "saldo_inicial_global": saldo_inicial_global,
        "saldo_inicial_periodo": saldo_inicial_periodo,
        "ingresos": totales["ingresos"],
        "egresos": totales["egresos"],
        "balance": totales["balance"],
        "saldo_final": saldo_final,
        "ingresos_por_categoria": ingresos_cat,
        "egresos_por_categoria": egresos_cat,
        "movimientos": qs.select_related("categoria"),
        "config": config,
    }


def reporte_mes_actual() -> dict:
    hoy = date.today()
    desde, hasta = _rango_mes(hoy)
    return generar_reporte(desde, hasta)


def reporte_mes_anterior() -> dict:
    hoy = date.today()
    if hoy.month == 1:
        mes_anterior = hoy.replace(year=hoy.year - 1, month=12)
    else:
        mes_anterior = hoy.replace(month=hoy.month - 1)
    desde, hasta = _rango_mes(mes_anterior)
    return generar_reporte(desde, hasta)


def reporte_anio() -> dict:
    hoy = date.today()
    desde = hoy.replace(month=1, day=1)
    return generar_reporte(desde, hoy)
