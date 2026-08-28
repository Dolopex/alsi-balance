"""Utilidades compartidas del nucleo."""

from decimal import Decimal

from django.db.models import Sum, Q

from core.models import TipoMovimiento


def _sum_movimientos(qs, tipo: str) -> Decimal:
    total = qs.filter(tipo=tipo).aggregate(s=Sum("valor"))["s"]
    return total or Decimal("0.00")


def calcular_balance(qs) -> dict:
    """Calcula totales de ingresos, egresos y balance a partir de un queryset."""
    ingresos = _sum_movimientos(qs, TipoMovimiento.INGRESO)
    egresos = _sum_movimientos(qs, TipoMovimiento.EGRESO)
    return {
        "ingresos": ingresos,
        "egresos": egresos,
        "balance": ingresos - egresos,
    }


def calcular_saldo(
    saldo_inicial: Decimal,
    qs,
) -> Decimal:
    """Saldo = saldo_inicial + ingresos - egresos."""
    totales = calcular_balance(qs)
    return saldo_inicial + totales["balance"]
