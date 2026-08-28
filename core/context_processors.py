"""Context processors compartidos para todo el proyecto."""

from django.conf import settings


def app_brand(request):
    """Inyecta el nombre de marca y la empresa en todas las plantillas."""
    return {
        "APP_NAME": settings.APP_NAME,
        "APP_SHORT_NAME": settings.APP_SHORT_NAME,
        "APP_COMPANY": settings.APP_COMPANY,
    }


def gmail_status(request):
    """Inyecta el estado de conexion de Gmail en todas las plantillas autenticadas."""
    from gmail_integration.services import obtener_configuracion

    try:
        config = obtener_configuracion()
    except Exception:
        return {"gmail_conectado": False, "gmail_email": "", "gmail_ultima": None}
    return {
        "gmail_conectado": bool(getattr(config, "conectado", False)),
        "gmail_email": getattr(config, "email_cuenta", "") or "",
        "gmail_ultima": getattr(config, "ultima_sincronizacion", None),
    }


def push_config(request):
    """Inyecta la clave publica VAPID para suscripcion push desde el frontend."""
    from django.conf import settings

    return {
        "vapid_public_key": getattr(settings, "VAPID_PUBLIC_KEY", "") or "",
        "push_soportado": (
            "granted" if getattr(request, "user", None) and request.user.is_authenticated else False
        ),
    }
