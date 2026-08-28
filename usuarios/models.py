"""Modelo de usuario personalizado.

Extiende AbstractUser para permitir roles y campos adicionales.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.TextChoices):
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
    USUARIO = "USUARIO", "Usuario"


class Usuario(AbstractUser):
    """Usuario del sistema con rol."""

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.USUARIO,
    )
    documento = models.CharField(max_length=30, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    cargo = models.CharField(max_length=80, blank=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self) -> str:
        full = self.get_full_name() or self.username
        return f"{full} ({self.get_rol_display()})"

    @property
    def es_administrador(self) -> bool:
        return self.rol == Rol.ADMINISTRADOR or self.is_superuser
