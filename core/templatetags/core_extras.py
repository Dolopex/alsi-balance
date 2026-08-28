"""Filtros y template tags del nucleo."""

from decimal import Decimal

from django import template

register = template.Library()


@register.filter(name="abs_valor")
def abs_valor(value) -> Decimal:
    """Devuelve el valor absoluto, soporta Decimal y numeros."""
    try:
        return abs(Decimal(str(value)))
    except Exception:
        return value


@register.filter(name="signo_monto")
def signo_monto(value, tipo: str) -> str:
    """Devuelve '+' si es INGRESO y '-' si es EGRESO."""
    return "+" if tipo == "INGRESO" else "-"


@register.filter(name="moneda")
def moneda(value) -> str:
    """Formatea un valor como COP sin simbolo: 1.234.567,89 (siempre 2 decimales)."""
    from django.contrib.humanize.templatetags.humanize import intcomma
    try:
        n = Decimal(str(value)) if value is not None else Decimal("0")
    except Exception:
        return "0,00"
    # Redondear a 2 decimales
    n = n.quantize(Decimal("0.01"))
    # Separar entero y decimal
    txt = f"{abs(n):.2f}"
    entero, decimales = txt.split(".")
    return f"{intcomma(entero)},{decimales}"


@register.filter(name="cop")
def cop(value) -> str:
    """Formatea un valor como COP sin simbolo y sin decimales: 1.234.567."""
    from django.contrib.humanize.templatetags.humanize import intcomma
    try:
        n = Decimal(str(value)) if value is not None else Decimal("0")
    except Exception:
        return "0"
    n = n.quantize(Decimal("1"))
    return f"{intcomma(int(abs(n)))}"
