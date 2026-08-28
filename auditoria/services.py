"""Servicios de auditoria."""

from django.contrib.auth.models import AnonymousUser


def registrar_auditoria(
    *,
    usuario=None,
    accion: str,
    movimiento=None,
    datos_anteriores=None,
    datos_nuevos=None,
    request=None,
) -> None:
    """Crea un RegistroAuditoria sin bloquear el flujo principal."""
    from .models import RegistroAuditoria

    if isinstance(usuario, AnonymousUser):
        usuario = None

    ip = None
    user_agent = ""
    if request is not None:
        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

    RegistroAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        movimiento=movimiento,
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
        ip=ip,
        user_agent=user_agent,
    )
