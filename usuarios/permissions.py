"""Decoradores / mixins de permisos."""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def administrador_required(view_func):
    """Requiere usuario autenticado y rol administrador."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not getattr(request.user, "es_administrador", False):
            messages.error(
                request,
                "No tienes permisos para realizar esta accion.",
            )
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return _wrapped
