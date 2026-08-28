"""Modelo para suscripciones Web Push (notificaciones moviles)."""

from django.conf import settings
from django.db import models


class PushSubscription(models.Model):
    """Una suscripcion a Web Push de un navegador/dispositivo."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.URLField(unique=True, max_length=500)
    p256dh_key = models.CharField(max_length=200)
    auth_key = models.CharField(max_length=100)
    user_agent = models.CharField(max_length=300, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Suscripcion push"
        verbose_name_plural = "Suscripciones push"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.endpoint[:60]}"
