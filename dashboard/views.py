"""Dashboard view with summary cards and charts."""

import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from core.models import TipoMovimiento
from core.selectors import obtener_configuracion, obtener_saldo_inicial
from core.services import calcular_saldo
from movimientos.views import _resolver_rango
from movimientos.selectors import (
    cantidad_pendientes_conciliacion,
    distribucion_por_categoria,
    listar_movimientos,
    movimiento_por_mes,
    series_estado_conciliacion,
    totales_por_tipo,
    ultimos_movimientos,
)


@login_required
def home(request):
    fecha_desde, fecha_hasta = _resolver_rango(request)
    qs_periodo = listar_movimientos({"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta})

    totales = totales_por_tipo(qs_periodo)
    saldo_inicial = obtener_saldo_inicial()
    # Si el rango es "todo" (sin filtros), usar todos los movimientos
    todos_los_movs = listar_movimientos()
    if fecha_hasta:
        movimientos_hasta = todos_los_movs.filter(fecha__lte=fecha_hasta)
    else:
        movimientos_hasta = todos_los_movs
    saldo_total = calcular_saldo(saldo_inicial, movimientos_hasta)

    ultimos = ultimos_movimientos(limit=8)

    distrib_ing_qs = list(distribucion_por_categoria(qs_periodo, TipoMovimiento.INGRESO))
    distrib_egr_qs = list(distribucion_por_categoria(qs_periodo, TipoMovimiento.EGRESO))

    distrib_ing = {
        "labels": json.dumps([d["categoria__nombre"] for d in distrib_ing_qs]),
        "data": json.dumps([float(d["total"] or 0) for d in distrib_ing_qs]),
    }
    distrib_egr = {
        "labels": json.dumps([d["categoria__nombre"] for d in distrib_egr_qs]),
        "data": json.dumps([float(d["total"] or 0) for d in distrib_egr_qs]),
    }

    estados = series_estado_conciliacion(qs_periodo)
    pendientes = cantidad_pendientes_conciliacion()

    por_mes_dict = movimiento_por_mes(listar_movimientos())
    meses_ordenados = sorted(por_mes_dict.keys())[-12:]
    por_mes = {
        "keys": json.dumps(meses_ordenados),
        "ingresos": json.dumps([float(por_mes_dict[m]["ingresos"]) for m in meses_ordenados]),
        "egresos": json.dumps([float(por_mes_dict[m]["egresos"]) for m in meses_ordenados]),
    }

    ctx = {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "rango_activo": request.GET.get("rango", "mes"),
        "totales": totales,
        "saldo_inicial": saldo_inicial,
        "saldo_total": saldo_total,
        "ultimos": ultimos,
        "distrib_ing_labels": distrib_ing["labels"],
        "distrib_ing_data": distrib_ing["data"],
        "distrib_egr_labels": distrib_egr["labels"],
        "distrib_egr_data": distrib_egr["data"],
        "estados": estados,
        "por_mes_keys": por_mes["keys"],
        "por_mes_ingresos": por_mes["ingresos"],
        "por_mes_egresos": por_mes["egresos"],
        "pendientes_conciliacion": pendientes,
        "config": obtener_configuracion(),
    }
    return render(request, "dashboard/home.html", ctx)
