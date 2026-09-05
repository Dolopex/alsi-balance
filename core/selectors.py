"""Selectores de lectura para modelos del nucleo."""

from decimal import Decimal

from .models import ConfiguracionSistema


def obtener_saldo_inicial() -> Decimal:
    """Devuelve el saldo inicial configurado o 0 si no existe ninguno."""
    config = ConfiguracionSistema.objects.first()
    if not config:
        return Decimal("0.00")
    return config.saldo_inicial


def obtener_configuracion() -> ConfiguracionSistema:
    """Devuelve la configuracion del sistema. Si no existe, crea una vacia."""
    config = ConfiguracionSistema.objects.first()
    if not config:
        config = ConfiguracionSistema.objects.create(
            saldo_inicial=Decimal("0.00"),
        )
    return config
