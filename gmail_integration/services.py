"""Servicio principal de Gmail: OAuth, lectura, sincronizacion."""

from __future__ import annotations

import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from django.conf import settings
from django.utils import timezone as dj_timezone

from core.models import OrigenMovimiento, TipoMovimiento
from movimientos.models import Movimiento
from .models import ConfiguracionGmail, EmailProcesado
from .parser import MovimientoParseado, parsear


log = logging.getLogger(__name__)


# --- Helpers de OAuth --------------------------------------------------------


def _oauth_flow_class():
    from google_auth_oauthlib.flow import Flow
    return Flow


def obtener_configuracion() -> ConfiguracionGmail:
    config, _ = ConfiguracionGmail.objects.get_or_create(pk=1)
    return config


def construir_flow_oauth(state: Optional[str] = None) -> "Flow":
    """Construye un Flow OAuth con redirect_uri.

    Las credenciales se toman de settings (GOOGLE_OAUTH_CLIENT_ID/SECRET)
    o de la base de datos.
    """
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID or ""
    client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET or ""
    config = obtener_configuracion()
    if not client_id and config.client_id:
        client_id = config.client_id
        client_secret = config.client_secret

    flow = _oauth_flow_class().from_client_config(
        client_config={
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI],
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            }
        },
        scopes=settings.GMAIL_SCOPES,
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
    if state:
        flow.state = state
    return flow


def guardar_credenciales(credentials, email_cuenta: str = "") -> ConfiguracionGmail:
    config = obtener_configuracion()
    config.access_token = credentials.token or ""
    config.refresh_token = credentials.refresh_token or config.refresh_token
    config.token_uri = credentials.token_uri or "https://oauth2.googleapis.com/token"
    config.client_id = credentials.client_id or ""
    config.client_secret = credentials.client_secret or ""
    config.scopes = " ".join(credentials.scopes or settings.GMAIL_SCOPES)
    config.expiry = credentials.expiry
    config.conectado = True
    config.email_cuenta = email_cuenta or config.email_cuenta
    config.save()
    return config


def desconectar() -> None:
    config = obtener_configuracion()
    config.access_token = ""
    config.refresh_token = ""
    config.conectado = False
    config.email_cuenta = ""
    config.save()


def construir_servicio_gmail(credentials):
    from googleapiclient.discovery import build
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


# --- Sincronizacion ----------------------------------------------------------


def _credentials_desde_config(config: ConfiguracionGmail):
    from google.oauth2.credentials import Credentials

    if not config.access_token and not config.refresh_token:
        return None
    return Credentials(
        token=config.access_token or None,
        refresh_token=config.refresh_token or None,
        token_uri=config.token_uri or "https://oauth2.googleapis.com/token",
        client_id=config.client_id or None,
        client_secret=config.client_secret or None,
        scopes=config.scopes.split() if config.scopes else settings.GMAIL_SCOPES,
    )


def _credentials_validos(config: ConfiguracionGmail) -> bool:
    """Verifica si los credenciales son utilizables."""
    if not config.refresh_token and not config.access_token:
        return False
    return True


def _invalidar_credenciales(config: ConfiguracionGmail):
    """Marca los credenciales como expirados. El user debera reconectar."""
    from .models import ConfiguracionGmail

    ConfiguracionGmail.objects.filter(pk=config.pk).update(
        access_token="",
        conectado=False,
    )
    logger.warning("ALSI Gmail: credenciales invalidadas, requiere reconexion")


def listar_correos_bancolombia(
    service,
    max_results: int = 50,
    days_back: int = 30,
):
    """Busca correos recientes de Bancolombia (con metadata basica)."""
    from googleapiclient.errors import HttpError

    despues = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y/%m/%d")
    # El remitente real puede ser de varios subdominios, incluyendo
    # notificacionesbancolombia.com, an.notificacionesbancolombia.com, etc.
    # Usamos varias alternativas para cubrir todos los casos.
    query = (
        f'(from:bancolombia.com OR from:notificacionesbancolombia.com '
        f'OR from:notificacionesbancarias.com '
        f'OR "alertasynotificaciones" OR "Bancolombia") after:{despues}'
    )
    try:
        resultados = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=max_results,
                fields="messages(id,threadId)",
            )
            .execute()
        )
    except HttpError as exc:
        log.warning("Gmail list error: %s", exc)
        return []
    return resultados.get("messages", [])


def _extraer_cuerpo(message) -> str:
    payload = message.get("payload", {}) or {}
    parts = payload.get("parts") or []
    if parts:
        textos = []
        for part in parts:
            if part.get("mimeType", "").startswith("text/") and part.get("body", {}).get("data"):
                try:
                    decoded = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    textos.append(decoded)
                except Exception:
                    continue
        return "\n".join(textos)
    body = payload.get("body", {}) or {}
    if body.get("data"):
        try:
            return base64.urlsafe_b64decode(body["data"]).decode("utf-8", errors="ignore")
        except Exception:
            return ""
    return ""


def _extraer_headers(headers) -> dict:
    out = {}
    for h in headers or []:
        out[h.get("name", "").lower()] = h.get("value", "")
    return out


def _crear_movimiento_desde_parseado(parseado: MovimientoParseado) -> Movimiento:
    # Si tenemos hora explicita, usarla; sino extraer de la fecha
    hora = getattr(parseado, "hora", None)
    if hora is None and isinstance(parseado.fecha, datetime):
        hora = parseado.fecha.time()

    return Movimiento.objects.create(
        tipo=parseado.tipo,
        fecha=parseado.fecha.date() if isinstance(parseado.fecha, datetime) else parseado.fecha,
        hora=hora,
        valor=parseado.valor,
        concepto=parseado.concepto or "",
        descripcion=f"Importado desde correo Bancolombia ({parseado.parser_usado})",
        banco="Bancolombia",
        cuenta=parseado.cuenta,
        cuenta_destino=getattr(parseado, "cuenta_destino", ""),
        nombre_destinatario=parseado.tercero,
        referencia=parseado.referencia,
        tercero=parseado.tercero,
        saldo_despues=parseado.saldo_despues,
        origen=OrigenMovimiento.EMAIL,
    )


def sincronizar_correos(max_results: int = 50, days_back: int = 30) -> dict:
    """Sincroniza correos nuevos de Bancolombia.

    Retorna un diccionario con metricas:
        - procesados: total leidos
        - nuevos: nuevos movimientos creados
        - ignorados: ya existian
        - errores: cantidad de errores
        - msg: mensaje de error si algo fallo (ej: token expirado)
    """
    from google.auth.exceptions import RefreshError

    config = obtener_configuracion()
    if not config.conectado:
        return {"procesados": 0, "nuevos": 0, "ignorados": 0, "errores": 0, "msg": "Gmail no conectado."}

    creds = _credentials_desde_config(config)
    if not creds:
        return {"procesados": 0, "nuevos": 0, "ignorados": 0, "errores": 1, "msg": "Sin credenciales."}

    try:
        service = construir_servicio_gmail(creds)
        metricas = {"procesados": 0, "nuevos": 0, "ignorados": 0, "errores": 0}
        correos = listar_correos_bancolombia(service, max_results=max_results, days_back=days_back)
    except RefreshError as exc:
        # Token expirado o revocado. Invalidar y pedir reconexion.
        _invalidar_credenciales(config)
        logger.warning("ALSI Gmail: RefreshError - %s", exc)
        return {
            "procesados": 0, "nuevos": 0, "ignorados": 0, "errores": 1,
            "msg": "Token de Gmail expirado o revocado. Reconecta Gmail desde el dashboard.",
        }
    except Exception as exc:
        logger.exception("ALSI Gmail: error inesperado en sync: %s", exc)
        return {
            "procesados": 0, "nuevos": 0, "ignorados": 0, "errores": 1,
            "msg": f"Error inesperado: {exc}",
        }

    for ref in correos:
        message_id = ref.get("id")
        if not message_id:
            continue
        if Movimiento.objects.filter(email_message_id=message_id).exists():
            metricas["ignorados"] += 1
            continue
        metricas["procesados"] += 1
        EmailProcesado.objects.filter(message_id=message_id).delete()
        try:
            message = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
        except Exception as exc:
            log.warning("No se pudo obtener mensaje %s: %s", message_id, exc)
            EmailProcesado.objects.create(
                message_id=message_id,
                estado="ERROR",
                error=str(exc)[:500],
            )
            metricas["errores"] += 1
            continue

        headers = _extraer_headers(message.get("payload", {}).get("headers"))
        remitente = headers.get("from", "")
        asunto = headers.get("subject", "")
        snippet = message.get("snippet", "") or ""
        # Intentar obtener cuerpo completo si la metadata no es suficiente
        cuerpo = ""
        try:
            full = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            cuerpo = _extraer_cuerpo(full)
        except Exception:
            pass

        # Si el parser no encuentra nada con el cuerpo, intenta con snippet+headers
        parseado = parsear(remitente, asunto, cuerpo)
        if parseado is None and snippet:
            parseado = parsear(remitente, asunto, snippet)
        if parseado is None:
            EmailProcesado.objects.create(
                message_id=message_id,
                thread_id=ref.get("threadId", ""),
                remitente=remitente[:255],
                asunto=asunto[:500],
                fecha_correo=_parsear_fecha_header(headers.get("date", "")),
                estado="IGNORADO",
                datos_extraidos={
                    "motivo": "no_reconocido",
                    "snippet": snippet[:500],
                    "cuerpo_preview": (cuerpo or "")[:500],
                    "asunto": asunto,
                },
            )
            continue

        # Evitar duplicados: si ya existe un movimiento con el mismo message_id,
        # no crear de nuevo.
        if Movimiento.objects.filter(email_message_id=message_id).exists():
            EmailProcesado.objects.create(
                message_id=message_id,
                estado="IGNORADO",
                datos_extraidos={"motivo": "movimiento_duplicado"},
            )
            metricas["ignorados"] += 1
            continue

        try:
            movimiento = _crear_movimiento_desde_parseado(parseado)
            movimiento.email_message_id = message_id
            movimiento.save(update_fields=["email_message_id"])
        except Exception as exc:
            log.warning("Error creando movimiento desde email %s: %s", message_id, exc)
            EmailProcesado.objects.create(
                message_id=message_id,
                estado="ERROR",
                error=str(exc)[:500],
                datos_extraidos=parseado.to_dict(),
            )
            metricas["errores"] += 1
            continue

        EmailProcesado.objects.create(
            message_id=message_id,
            thread_id=ref.get("threadId", ""),
            remitente=remitente[:255],
            asunto=asunto[:500],
            fecha_correo=_parsear_fecha_header(headers.get("date", "")),
            estado="EXITOSO",
            movimiento=movimiento,
            datos_extraidos={
                **parseado.to_dict(),
                "snippet": snippet[:500],
                "cuerpo_preview": (cuerpo or "")[:500],
            },
        )
        metricas["nuevos"] += 1
        # Notificar push
        try:
            from notificaciones.services import enviar_notificacion
            tipo_texto = "Ingreso" if parseado.tipo == "INGRESO" else "Egreso"
            valor_str = f"${parseado.valor:,.0f}".replace(",", ".")
            enviar_notificacion(
                titulo=f"ALSI - {tipo_texto} detectado",
                cuerpo=f"{parseado.concepto or 'Movimiento'} por {valor_str}",
                url=f"/movimientos/{movimiento.pk}/",
            )
        except Exception as exc:
            log.debug("Notificacion push fallida: %s", exc)

    config.ultima_sincronizacion = dj_timezone.now()
    config.save(update_fields=["ultima_sincronizacion"])
    return metricas


def _parsear_fecha_header(texto: str):
    from email.utils import parsedate_to_datetime
    if not texto:
        return None
    try:
        return parsedate_to_datetime(texto)
    except Exception:
        return None


def procesar_correo_simulado(remitente: str, asunto: str, cuerpo: str, message_id: str = "") -> dict:
    """Procesa un correo simulado (util para tests).

    No consulta Gmail. Devuelve metricas.
    """
    metricas = {"procesados": 0, "nuevos": 0, "ignorados": 0, "errores": 0}
    if not message_id:
        message_id = f"sim-{datetime.now().timestamp()}"
    if Movimiento.objects.filter(email_message_id=message_id).exists():
        metricas["ignorados"] += 1
        return metricas
    EmailProcesado.objects.filter(message_id=message_id).delete()

    metricas["procesados"] += 1
    parseado = parsear(remitente, asunto, cuerpo)
    if parseado is None:
        EmailProcesado.objects.create(
            message_id=message_id,
            estado="IGNORADO",
            datos_extraidos={"motivo": "no_reconocido"},
        )
        return metricas

    if Movimiento.objects.filter(email_message_id=message_id).exists():
        metricas["ignorados"] += 1
        return metricas

    try:
        movimiento = _crear_movimiento_desde_parseado(parseado)
        movimiento.email_message_id = message_id
        movimiento.save(update_fields=["email_message_id"])
        EmailProcesado.objects.create(
            message_id=message_id,
            estado="EXITOSO",
            movimiento=movimiento,
            datos_extraidos=parseado.to_dict(),
        )
        metricas["nuevos"] += 1
    except Exception as exc:
        EmailProcesado.objects.create(
            message_id=message_id,
            estado="ERROR",
            error=str(exc)[:500],
            datos_extraidos=parseado.to_dict(),
        )
        metricas["errores"] += 1
    return metricas
