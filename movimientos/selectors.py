"""Selectores (lectura) para movimientos."""

from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum

from core.models import EstadoConciliacion, TipoMovimiento


def listar_movimientos(filtros: dict | None = None):
    """Lista movimientos aplicando filtros basicos."""
    qs = Movimiento.objects.select_related("categoria", "comprobante", "creado_por")
    qs = qs.order_by("-fecha", "-hora", "-id")

    if not filtros:
        return qs

    if tipo := filtros.get("tipo"):
        qs = qs.filter(tipo=tipo)
    if estado := filtros.get("estado"):
        qs = qs.filter(estado_conciliacion=estado)
    if origen := filtros.get("origen"):
        qs = qs.filter(origen=origen)
    if categoria_id := filtros.get("categoria"):
        qs = qs.filter(categoria_id=categoria_id)
    if tercero := filtros.get("tercero"):
        qs = qs.filter(tercero__icontains=tercero)
    if fecha_desde := filtros.get("fecha_desde"):
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta := filtros.get("fecha_hasta"):
        qs = qs.filter(fecha__lte=fecha_hasta)
    if busqueda := filtros.get("q"):
        qs = qs.filter(
            Q(concepto__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
            | Q(referencia__icontains=busqueda)
            | Q(tercero__icontains=busqueda)
        )

    return qs


def totales_por_tipo(qs) -> dict:
    ingresos = qs.filter(tipo=TipoMovimiento.INGRESO).aggregate(s=Sum("valor"))["s"] or Decimal("0.00")
    egresos = qs.filter(tipo=TipoMovimiento.EGRESO).aggregate(s=Sum("valor"))["s"] or Decimal("0.00")
    return {
        "ingresos": ingresos,
        "egresos": egresos,
        "balance": ingresos - egresos,
    }


def ultimos_movimientos(limit: int = 10):
    return listar_movimientos()[:limit]


def cantidad_pendientes_conciliacion() -> int:
    return Movimiento.objects.filter(
        estado_conciliacion=EstadoConciliacion.PENDIENTE
    ).count()


def distribucion_por_categoria(qs, tipo: str):
    return (
        qs.filter(tipo=tipo, categoria__isnull=False)
        .values("categoria__nombre", "categoria__color")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )


def movimiento_por_mes(qs):
    """Agrupa ingresos y egresos por mes (YYYY-MM)."""
    by_month: dict[str, dict[str, Decimal]] = {}
    for m in qs.values("fecha", "tipo", "valor"):
        key = m["fecha"].strftime("%Y-%m")
        slot = by_month.setdefault(key, {"ingresos": Decimal("0.00"), "egresos": Decimal("0.00")})
        if m["tipo"] == TipoMovimiento.INGRESO:
            slot["ingresos"] += m["valor"]
        else:
            slot["egresos"] += m["valor"]
    return by_month


def series_estado_conciliacion(qs) -> dict:
    rows = qs.values("estado_conciliacion").annotate(n=Count("id"))
    out = {estado: 0 for estado, _ in EstadoConciliacion.choices}
    for row in rows:
        out[row["estado_conciliacion"]] = row["n"]
    return out


def movimiento_entre_fechas(fecha_desde: date, fecha_hasta: date):
    return Movimiento.objects.filter(
        fecha__gte=fecha_desde,
        fecha__lte=fecha_hasta,
    )


from .models import Movimiento  # noqa: E402
