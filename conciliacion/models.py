"""Modelos para conciliacion bancaria.

Esta app queda como placeholder para la Fase 2. Define las clases base
sobre las que se construira el modulo completo de conciliacion.
"""

from django.db import models

from core.models import TipoMovimiento


class CuentaBancaria(models.Model):
    nombre = models.CharField(max_length=120)
    banco = models.CharField(max_length=80, default="Bancolombia")
    numero = models.CharField(max_length=80, blank=True)
    tipo = models.CharField(max_length=40, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cuenta bancaria"
        verbose_name_plural = "Cuentas bancarias"

    def __str__(self) -> str:
        return f"{self.banco} - {self.nombre}"


class Conciliacion(models.Model):
    """Sesion de conciliacion entre el sistema y el banco."""

    cuenta = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.CASCADE,
        related_name="conciliaciones",
    )
    fecha_desde = models.DateField()
    fecha_hasta = models.DateField()
    saldo_banco = models.DecimalField(max_digits=18, decimal_places=2)
    saldo_sistema = models.DecimalField(max_digits=18, decimal_places=2)
    diferencia = models.DecimalField(max_digits=18, decimal_places=2)
    observaciones = models.TextField(blank=True)
    cerrado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conciliacion"
        verbose_name_plural = "Conciliaciones"

    def __str__(self) -> str:
        return f"Conciliacion {self.cuenta} {self.fecha_desde} - {self.fecha_hasta}"
