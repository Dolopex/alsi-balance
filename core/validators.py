from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import ConfiguracionSistema


def validar_saldo_inicial(value):
    if value is None:
        raise ValidationError(_("El saldo inicial no puede ser nulo."))
