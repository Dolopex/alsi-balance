"""Modelo de auditoria: registra acciones sensibles sobre el sistema."""

import json

from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_auditoria",
    )
    accion = models.CharField(max_length=80)
    movimiento = models.ForeignKey(
        "movimientos.Movimiento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_auditoria",
    )
    datos_anteriores = models.JSONField(blank=True, null=True)
    datos_nuevos = models.JSONField(blank=True, null=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Registro de auditoria"
        verbose_name_plural = "Registros de auditoria"
        ordering = ["-fecha"]

    def __str__(self) -> str:
        user = self.usuario.username if self.usuario else "sistema"
        return f"{user} - {self.accion} - {self.fecha:%Y-%m-%d %H:%M}"

    def datos_anteriores_pretty(self) -> str:
        return json.dumps(self.datos_anteriores, indent=2, ensure_ascii=False) if self.datos_anteriores else ""

    def datos_nuevos_pretty(self) -> str:
        return json.dumps(self.datos_nuevos, indent=2, ensure_ascii=False) if self.datos_nuevos else ""
