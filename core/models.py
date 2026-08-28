"""Modelos del nucleo.

Por ahora expone constantes compartidas (tipos de movimiento,
origenes, estados de conciliacion) y un modelo ConfiguracionSistema
para parametros globales (saldo inicial, etc).
"""

from decimal import Decimal

from django.db import models


class TipoMovimiento(models.TextChoices):
    INGRESO = "INGRESO", "Ingreso"
    EGRESO = "EGRESO", "Egreso"


class OrigenMovimiento(models.TextChoices):
    EMAIL = "EMAIL", "Correo electronico"
    MANUAL = "MANUAL", "Registro manual"
    OCR = "OCR", "OCR comprobante"
    IMPORTACION_EXCEL = "IMPORTACION_EXCEL", "Importacion Excel"
    OTRO = "OTRO", "Otro"


class EstadoConciliacion(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    CONCILIADO = "CONCILIADO", "Conciliado"
    OBSERVADO = "OBSERVADO", "Observado"


class ConfiguracionSistema(models.Model):
    """Parametros globales del sistema, por ejemplo saldo inicial."""

    saldo_inicial = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Saldo inicial con el que arranca el sistema.",
    )
    nombre_cuenta = models.CharField(
        max_length=120,
        default="Cuenta principal",
    )
    banco = models.CharField(max_length=80, default="Bancolombia")
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuracion del sistema"
        verbose_name_plural = "Configuracion del sistema"

    def __str__(self) -> str:
        return f"Configuracion ({self.banco} - {self.nombre_cuenta})"
