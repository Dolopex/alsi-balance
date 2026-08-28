"""Servicios para envio de notificaciones push."""

import json
import logging

from django.conf import settings

from .models import PushSubscription

logger = logging.getLogger(__name__)


def _normalize_pem(pem: str) -> str:
    """Normaliza un PEM: convierte \\n literal a newline y reformatea el body.

    Algunos .env guardan la clave privada con el body todo pegado en una linea.
    py_vapid requiere saltos de linea cada 64 chars en el body base64.
    """
    if not pem:
        return pem
    pem = pem.replace("\\n", "\n").strip()
    lines = [ln.strip() for ln in pem.splitlines() if ln.strip()]
    if len(lines) >= 2:
        # Separar marcadores y body
        begin = lines[0]
        end = lines[-1]
        body_lines = lines[1:-1]
        # Si el body esta en una sola linea larga, dividirlo en chunks de 64
        if len(body_lines) == 1 and len(body_lines[0]) > 64:
            body = body_lines[0]
            body_lines = [body[i:i + 64] for i in range(0, len(body), 64)]
        return "\n".join([begin, *body_lines, end])
    return pem


def enviar_notificacion(titulo: str, cuerpo: str, url: str = "/dashboard/") -> int:
    """Envia una notificacion push a todas las suscripciones activas.

    Retorna el numero de envios intentados (no necesariamente exitosos).
    """
    from py_vapid import Vapid
    from pywebpush import webpush, WebPushException

    vapid_private = getattr(settings, "VAPID_PRIVATE_KEY", None)
    vapid_public = getattr(settings, "VAPID_PUBLIC_KEY", None)
    vapid_claims = getattr(settings, "VAPID_CLAIMS", None)

    if not vapid_private or not vapid_public:
        logger.warning("Notificaciones: VAPID keys no configuradas en settings.")
        return 0

    vapid_private = _normalize_pem(vapid_private)

    payload = json.dumps({
        "title": titulo,
        "body": cuerpo,
        "icon": "/static/img/icon-192.png",
        "badge": "/static/img/icon-192.png",
        "url": url,
    })

    enviados = 0
    fallidos = []
    for sub in PushSubscription.objects.filter(activo=True):
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh_key, "auth": sub.auth_key},
                },
                data=payload,
                vapid_private_key=vapid_private,
                vapid_claims=vapid_claims,
            )
            enviados += 1
        except WebPushException as exc:
            # 404/410: subscription invalida, desactivar
            if exc.response and exc.response.status_code in (404, 410):
                sub.activo = False
                sub.save(update_fields=["activo"])
                fallidos.append(sub.pk)
            else:
                logger.warning("Push error: %s", exc)

    if fallidos:
        logger.info("Notificaciones: %d suscripciones expiradas desactivadas.", len(fallidos))

    return enviados
