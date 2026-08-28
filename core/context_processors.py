"""Context processors compartidos para todo el proyecto."""

from datetime import date

from django.conf import settings


MESES_ES = [
    (1, "Enero"), (2, "Febrero"), (3, "Marzo"), (4, "Abril"),
    (5, "Mayo"), (6, "Junio"), (7, "Julio"), (8, "Agosto"),
    (9, "Septiembre"), (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre"),
]


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


def periodo_selector(request):
    """Inyecta lista de años/meses disponibles para selectores de export."""
    hoy = date.today()
    current_year = hoy.year
    current_month = hoy.month
    available_years = list(range(current_year - 5, current_year + 2))
    available_months = [{"num": n, "name": name} for n, name in MESES_ES]
    return {
        "available_years": available_years,
        "available_months": available_months,
        "current_year": current_year,
        "current_month": current_month,
    }
