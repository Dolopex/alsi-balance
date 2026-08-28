"""Modelos principales de movimientos financieros y comprobantes."""

from decimal import Decimal

from django.conf import settings
from django.db import models

from core.models import (
    EstadoConciliacion,
    OrigenMovimiento,
    TipoMovimiento,
)


class Comprobante(models.Model):
    """Imagen o PDF del comprobante asociado a un movimiento."""

    imagen = models.ImageField(
        upload_to="comprobantes/%Y/%m/",
        blank=True,
        null=True,
    )
    archivo = models.FileField(
        upload_to="comprobantes/%Y/%m/",
        blank=True,
        null=True,
    )
    mime_type = models.CharField(max_length=80, blank=True)
    tamano_bytes = models.PositiveIntegerField(default=0)
    texto_ocr = models.TextField(blank=True, help_text="Texto crudo extraido por OCR.")
    subido_en = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comprobantes_subidos",
    )

    class Meta:
        verbose_name = "Comprobante"
        verbose_name_plural = "Comprobantes"

    def __str__(self) -> str:
        return f"Comprobante #{self.id}"


class Movimiento(models.Model):
    """Movimiento financiero (ingreso o egreso)."""

    tipo = models.CharField(max_length=10, choices=TipoMovimiento.choices)
    fecha = models.DateField()
    hora = models.TimeField(blank=True, null=True)
    valor = models.DecimalField(max_digits=18, decimal_places=2)
    concepto = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        "categorias.Categoria",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos",
    )
    subcategoria = models.CharField(max_length=120, blank=True)
    banco = models.CharField(max_length=80, blank=True, default="Bancolombia")
    cuenta = models.CharField(max_length=80, blank=True, help_text="Cuenta origen")
    cuenta_destino = models.CharField(
        max_length=80,
        blank=True,
        help_text="Cuenta destino (para transferencias)",
    )
    nombre_destinatario = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre del destinatario (para transferencias)",
    )
    referencia = models.CharField(max_length=120, blank=True, db_index=True)
    tercero = models.CharField(max_length=200, blank=True)
    saldo_despues = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )
    origen = models.CharField(
        max_length=20,
        choices=OrigenMovimiento.choices,
        default=OrigenMovimiento.MANUAL,
    )
    estado_conciliacion = models.CharField(
        max_length=15,
        choices=EstadoConciliacion.choices,
        default=EstadoConciliacion.PENDIENTE,
    )
    comprobante = models.ForeignKey(
        Comprobante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos",
    )
    email_message_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="ID del correo Gmail cuando el origen es EMAIL.",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_creados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-fecha", "-hora", "-id"]
        indexes = [
            models.Index(fields=["tipo", "fecha"]),
            models.Index(fields=["estado_conciliacion"]),
            models.Index(fields=["origen"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} {self.valor} - {self.fecha}"

    @property
    def es_ingreso(self) -> bool:
        return self.tipo == TipoMovimiento.INGRESO

    @property
    def es_egreso(self) -> bool:
        return self.tipo == TipoMovimiento.EGRESO

    @property
    def valor_con_signo(self) -> Decimal:
        """Valor con signo segun el tipo."""
        if self.es_egreso:
            return -self.valor
        return self.valor
