"""Modelo de categoria.

Permite agrupar movimientos (ingresos/egresos) en categorias configurables.
"""

from django.db import models
from django.core.exceptions import ValidationError

from core.models import TipoMovimiento


class Categoria(models.Model):
    nombre = models.CharField(max_length=80)
    tipo = models.CharField(max_length=10, choices=TipoMovimiento.choices)
    descripcion = models.CharField(max_length=200, blank=True)
    color = models.CharField(
        max_length=7,
        default="#1e3a8a",
        help_text="Color en formato HEX para las graficas.",
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["tipo", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["nombre", "tipo"],
                name="categoria_nombre_tipo_unico",
            )
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.get_tipo_display()})"

    def clean(self):
        if self.tipo not in dict(TipoMovimiento.choices):
            raise ValidationError({"tipo": "Tipo de categoria invalido."})
