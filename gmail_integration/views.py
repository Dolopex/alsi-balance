"""Vistas para el flujo OAuth de Gmail + sincronizacion."""

import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from usuarios.permissions import administrador_required

from .services import (
    construir_flow_oauth,
    desconectar as svc_desconectar,
    guardar_credenciales,
    obtener_configuracion,
    sincronizar_correos,
)


log = logging.getLogger(__name__)


@administrador_required
def conectar(request):
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        messages.error(
            request,
            "Falta configurar GOOGLE_OAUTH_CLIENT_ID y GOOGLE_OAUTH_CLIENT_SECRET en .env",
        )
        return redirect("dashboard:home")
    flow = construir_flow_oauth()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["gmail_oauth_state"] = state
    return redirect(auth_url)


@administrador_required
def callback(request):
    state = request.session.get("gmail_oauth_state")
    flow = construir_flow_oauth(state=state)
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials

    # Obtener email de la cuenta
    email_cuenta = ""
    try:
        from googleapiclient.discovery import build
        service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
        perfil = service.users().getProfile(userId="me").execute()
        email_cuenta = perfil.get("emailAddress", "")
    except Exception as exc:
        log.warning("No se pudo obtener perfil Gmail: %s", exc)

    guardar_credenciales(credentials, email_cuenta=email_cuenta)
    messages.success(request, f"Gmail conectado: {email_cuenta}")
    return redirect("dashboard:home")


@administrador_required
def desconectar(request):
    svc_desconectar()
    messages.success(request, "Gmail desconectado.")
    return redirect("dashboard:home")


@administrador_required
def sincronizar(request):
    metricas = sincronizar_correos()
    if metricas.get("msg"):
        messages.warning(request, metricas["msg"])
    else:
        messages.success(
            request,
            f"Gmail sincronizado: {metricas['nuevos']} nuevos, {metricas['ignorados']} ya procesados.",
        )
    return redirect("dashboard:home")


@administrador_required
def estado(request):
    config = obtener_configuracion()
    data = {
        "conectado": config.conectado,
        "email_cuenta": config.email_cuenta,
        "ultima_sincronizacion": (
            config.ultima_sincronizacion.isoformat() if config.ultima_sincronizacion else None
        ),
        "oauth_configurado": bool(settings.GOOGLE_OAUTH_CLIENT_ID),
    }
    return JsonResponse(data)


@administrador_required
def debug_correos(request):
    """Lista los ultimos correos de Gmail (no crea movimientos).

    Util para depurar por que un correo no se esta reconociendo.
    """
    from gmail_integration.models import EmailProcesado
    limite = int(request.GET.get("limite", 20))

    correos = EmailProcesado.objects.all().order_by("-procesado_en")[:limite]
    data = {
        "ultima_sincronizacion": None,
        "total_correos": EmailProcesado.objects.count(),
        "ultimos": []
    }
    from gmail_integration.models import ConfiguracionGmail
    config = ConfiguracionGmail.objects.first()
    if config and config.ultima_sincronizacion:
        data["ultima_sincronizacion"] = config.ultima_sincronizacion.isoformat()

    for c in correos:
        item = {
            "message_id": c.message_id[:40],
            "estado": c.estado,
            "remitente": c.remitente[:80] if c.remitente else "",
            "asunto": c.asunto[:80] if c.asunto else "",
            "fecha_correo": c.fecha_correo.isoformat() if c.fecha_correo else None,
            "procesado_en": c.procesado_en.isoformat() if c.procesado_en else None,
        }
        if c.datos_extraidos:
            data_extras = c.datos_extraidos
            item["motivo"] = data_extras.get("motivo", "")
            item["snippet"] = (data_extras.get("snippet", "") or "")[:200]
        data["ultimos"].append(item)

    return JsonResponse(data)


@csrf_exempt
def webhook(request):
    """Webhook para Gmail Push Notifications (Pub/Sub de Google Cloud).

    Cuando llega una notificacion, Google hace POST aqui y el sistema
    sincroniza inmediatamente en lugar de esperar el polling periodico.

    Ver: https://developers.google.com/gmail/api/guides/push

    Configuracion:
    1. Crear topic en Google Cloud Pub/Sub
    2. Configurar Gmail Watch apuntando al topic
    3. Configurar suscripcion push al topic con URL = https://TU_DOMINIO/gmail/webhook/

    Seguridad: validar el header X-Goog-Validation token (configurable en .env).
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    token_esperado = getattr(settings, "GMAIL_WATCH_TOKEN", "")
    if token_esperado:
        header_token = (
            request.headers.get("X-Goog-Validation", "")
            or request.headers.get("X-Goog-Channel-Token", "")
        )
        if header_token and header_token != token_esperado:
            log.warning("ALSI Gmail: webhook token invalido")
            return HttpResponse(status=401)

    try:
        body = request.body.decode("utf-8", errors="ignore") if request.body else ""
        log.info("ALSI Gmail: webhook Pub/Sub recibido (%d bytes)", len(body))
        metricas = sincronizar_correos()
        log.info(
            "ALSI Gmail: webhook sincron -> -> %s",
            {k: metricas.get(k) for k in ("procesados", "nuevos", "ignorados", "errores")},
        )
    except Exception as exc:
        log.exception("ALSI Gmail: webhook error: %s", exc)
        return HttpResponse(status=500)

    return HttpResponse(status=200)
