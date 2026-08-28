"""Modelos para la integracion con Gmail."""

from django.conf import settings
from django.db import models


class ConfiguracionGmail(models.Model):
    """Singleton: almacena credenciales OAuth de Gmail."""

    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_uri = models.CharField(max_length=255, blank=True)
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    scopes = models.TextField(blank=True, default="https://www.googleapis.com/auth/gmail.readonly")
    expiry = models.DateTimeField(blank=True, null=True)
    email_cuenta = models.EmailField(blank=True)
    conectado = models.BooleanField(default=False)
    ultima_sincronizacion = models.DateTimeField(blank=True, null=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuracion Gmail"
        verbose_name_plural = "Configuracion Gmail"

    def __str__(self) -> str:
        return f"Gmail: {self.email_cuenta or '(no conectado)'}"


class EmailProcesado(models.Model):
    """Registro de cada correo procesado para evitar duplicados."""

    ESTADO_CHOICES = (
        ("EXITOSO", "Exitoso"),
        ("ERROR", "Error"),
        ("IGNORADO", "Ignorado"),
    )

    message_id = models.CharField(max_length=200, unique=True)
    thread_id = models.CharField(max_length=200, blank=True)
    remitente = models.CharField(max_length=255, blank=True)
    asunto = models.CharField(max_length=500, blank=True)
    fecha_correo = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default="EXITOSO")
    movimiento = models.ForeignKey(
        "movimientos.Movimiento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails_origen",
    )
    datos_extraidos = models.JSONField(blank=True, null=True)
    error = models.TextField(blank=True)
    procesado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Email procesado"
        verbose_name_plural = "Emails procesados"
        ordering = ["-procesado_en"]

    def __str__(self) -> str:
        return f"{self.message_id} ({self.estado})"
