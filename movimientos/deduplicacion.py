"""Deduplicacion de movimientos.

Compara un movimiento nuevo contra los existentes usando una heuristica
de coincidencia por (fecha, valor, referencia). Devuelve posibles duplicados.
"""

from decimal import Decimal

from django.db.models import Q

from .models import Movimiento


def _norm(value) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def calcular_similitud(a: Movimiento, b: Movimiento) -> int:
    """Calcula una puntuacion 0-100 de similitud entre dos movimientos."""
    score = 0

    if a.valor == b.valor:
        score += 40
    elif abs((a.valor or Decimal("0")) - (b.valor or Decimal("0"))) <= Decimal("1.00"):
        score += 20

    if a.fecha == b.fecha:
        score += 30
    elif abs((a.fecha - b.fecha).days) <= 1:
        score += 15

    if _norm(a.referencia) and _norm(a.referencia) == _norm(b.referencia):
        score += 25

    if _norm(a.tercero) and _norm(a.tercero) == _norm(b.tercero):
        score += 5

    return min(score, 100)


def buscar_duplicados(movimiento: Movimiento, umbral: int = 70) -> list[dict]:
    """Busqueda inicial por campos exactos y luego calcula similitud."""
    qs = Movimiento.objects.exclude(pk=movimiento.pk).filter(
        valor=movimiento.valor,
        fecha=movimiento.fecha,
    )
    if movimiento.referencia:
        qs = qs | Movimiento.objects.exclude(pk=movimiento.pk).filter(
            referencia__iexact=movimiento.referencia,
        )

    candidatos = qs.distinct()
    resultados = []
    for candidato in candidatos:
        score = calcular_similitud(movimiento, candidato)
        if score >= umbral:
            resultados.append({"movimiento": candidato, "score": score})
    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados


def es_posible_duplicado(a: Movimiento, b: Movimiento) -> bool:
    """Evalua rapidamente si dos movimientos podrian ser el mismo."""
    if a.valor != b.valor:
        return False
    if a.fecha != b.fecha:
        if abs((a.fecha - b.fecha).days) > 1:
            return False
    if a.referencia and b.referencia and _norm(a.referencia) == _norm(b.referencia):
        return True
    return a.pk == b.pk or (
        _norm(a.concepto) == _norm(b.concepto) and _norm(a.tercero) == _norm(b.tercero)
    )
