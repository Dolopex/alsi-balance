"""Vistas para suscripcion/registro de Web Push."""

import json

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from usuarios.permissions import administrador_required

from .models import PushSubscription


@require_POST
@csrf_exempt
def subscribe(request):
    """Registra una suscripcion push del navegador actual."""
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
        keys = data.get("keys", {})
        p256dh = keys.get("p256dh", "")
        auth = keys.get("auth", "")
    except Exception:
        return JsonResponse({"ok": False, "error": "datos invalidos"}, status=400)

    if not endpoint or not p256dh or not auth:
        return JsonResponse({"ok": False, "error": "faltan datos"}, status=400)

    sub, created = PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "user": request.user,
            "p256dh_key": p256dh,
            "auth_key": auth,
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:300],
            "activo": True,
        },
    )
    return JsonResponse({"ok": True, "id": sub.pk, "created": created})


@require_http_methods(["DELETE", "POST"])
@csrf_exempt
def unsubscribe(request):
    """Desactiva la suscripcion push actual."""
    try:
        data = json.loads(request.body) if request.body else {}
        endpoint = data.get("endpoint")
    except Exception:
        endpoint = None

    qs = PushSubscription.objects.filter(activo=True)
    if endpoint:
        qs = qs.filter(endpoint=endpoint)
    else:
        qs = qs.filter(user=request.user)
    count = qs.update(activo=False)
    return JsonResponse({"ok": True, "desactivadas": count})


@require_POST
def toggle(request):
    """Alterna el estado de notificaciones de un usuario."""
    action = request.POST.get("action", "")
    if action == "disable":
        PushSubscription.objects.filter(user=request.user, activo=True).update(activo=False)
        return JsonResponse({"ok": True, "notificaciones": False})
    elif action == "enable":
        # La suscripcion la crea el frontend al pedir permiso
        return JsonResponse({"ok": True, "notificaciones": True, "msg": "permite notificacion en el navegador"})
    return JsonResponse({"ok": False}, status=400)


@administrador_required
def probar(request):
    """Pantalla admin-only para enviar notificaciones push de prueba."""
    from .services import enviar_notificacion

    vapid_priv = getattr(settings, "VAPID_PRIVATE_KEY", "")
    vapid_pub = getattr(settings, "VAPID_PUBLIC_KEY", "")
    vapid_ok = bool(vapid_priv and vapid_pub)

    activas = PushSubscription.objects.filter(activo=True).select_related("user")

    if request.method == "POST":
        titulo = (request.POST.get("titulo") or "").strip()
        cuerpo = (request.POST.get("cuerpo") or "").strip()
        url = (request.POST.get("url") or "/dashboard/").strip() or "/dashboard/"
        objetivo = request.POST.get("objetivo", "todas")

        if not titulo or not cuerpo:
            messages.error(request, "Titulo y cuerpo son obligatorios.")
            return redirect("notificaciones:probar")

        if not vapid_ok:
            messages.error(
                request,
                "VAPID keys no configuradas en .env. Corre python manage.py generar_vapid y "
                "agrega VAPID_PUBLIC_KEY y VAPID_PRIVATE_KEY.",
            )
            return redirect("notificaciones:probar")

        if objetivo == "todas":
            from .services import enviar_notificacion
            if activas.count() == 0:
                messages.error(
                    request,
                    "No hay suscripciones activas. Primero activa las notificaciones en este "
                    "navegador con el boton 'Activar notificaciones aqui'.",
                )
                return redirect("notificaciones:probar")
            enviados = enviar_notificacion(titulo=titulo, cuerpo=cuerpo, url=url)
            messages.success(
                request,
                f"Notificacion enviada a {enviados} suscripcion(es) activa(s).",
            )
        else:
            try:
                pk = int(objetivo)
            except (TypeError, ValueError):
                messages.error(request, "Objetivo invalido.")
                return redirect("notificaciones:probar")
            sub = activas.filter(pk=pk).first()
            if not sub:
                messages.error(request, "Suscripcion no encontrada o inactiva.")
                return redirect("notificaciones:probar")
            enviados = _enviar_a_una(sub, titulo, cuerpo, url)
            if enviados:
                messages.success(
                    request,
                    f"Notificacion enviada a la suscripcion #{sub.pk} ({sub.user.username}).",
                )
            else:
                messages.error(request, "Fallo el envio. Revisa los logs del servidor.")

        return redirect("notificaciones:probar")

    ctx = {
        "vapid_ok": vapid_ok,
        "vapid_public": vapid_pub[:60] + ("..." if len(vapid_pub) > 60 else ""),
        "activas": activas,
        "total_activas": activas.count(),
        "ultimo_resultado": request.session.pop("ultimo_resultado", None),
    }
    return render(request, "notificaciones/probar.html", ctx)


def _enviar_a_una(sub: PushSubscription, titulo: str, cuerpo: str, url: str) -> int:
    """Envia una notificacion a una sola suscripcion. Retorna 1 si OK, 0 si fallo."""
    import json
    import logging

    from django.conf import settings

    from py_vapid import Vapid
    from pywebpush import webpush, WebPushException

    from .services import _normalize_pem

    log = logging.getLogger(__name__)
    payload = json.dumps({
        "title": titulo,
        "body": cuerpo,
        "icon": "/static/img/icon-192.png",
        "badge": "/static/img/icon-192.png",
        "url": url,
    })
    vapid_private = _normalize_pem(settings.VAPID_PRIVATE_KEY or "")
    try:
        webpush(
            subscription_info={
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh_key, "auth": sub.auth_key},
            },
            data=payload,
            vapid_private_key=vapid_private,
            vapid_claims=settings.VAPID_CLAIMS,
        )
        return 1
    except WebPushException as exc:
        log.warning("Push test error: %s", exc)
        if exc.response and exc.response.status_code in (404, 410):
            sub.activo = False
            sub.save(update_fields=["activo"])
        return 0
