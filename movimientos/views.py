from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.models import EstadoConciliacion, TipoMovimiento
from categorias.models import Categoria
from usuarios.permissions import administrador_required

from .forms import MovimientoForm
from . import services
from .selectors import listar_movimientos


def _resolver_rango(request):
    """Convierte el parametro 'rango' en (fecha_desde, fecha_hasta).

    Soporta: hoy, semana, mes, mes_anterior, 3m, 6m, 12m, anio, anio_anterior, todo, personalizado.
    Si es personalizado, usa fecha_desde / fecha_hasta del request.

    Default: 'todo' (sin filtro) para que los charts del dashboard siempre
    tengan datos aunque el mes actual este vacio.
    """
    rango = request.GET.get("rango", "todo")
    hoy = timezone.localdate()

    if rango == "hoy":
        return hoy, hoy
    if rango == "semana":
        return hoy - timedelta(days=hoy.weekday()), hoy
    if rango == "mes":
        return hoy.replace(day=1), hoy
    if rango == "mes_anterior":
        if hoy.month == 1:
            desde = hoy.replace(year=hoy.year - 1, month=12, day=1)
            hasta = hoy.replace(day=1) - timedelta(days=1)
        else:
            desde = hoy.replace(month=hoy.month - 1, day=1)
            hasta = hoy.replace(day=1) - timedelta(days=1)
        return desde, hasta
    if rango == "3m":
        desde = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)
        for _ in range(2):
            desde = (desde - timedelta(days=1)).replace(day=1)
        return desde, hoy
    if rango == "6m":
        desde = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)
        for _ in range(5):
            desde = (desde - timedelta(days=1)).replace(day=1)
        return desde, hoy
    if rango == "12m":
        desde = hoy.replace(year=hoy.year - 1, month=hoy.month, day=1)
        if desde > hoy:
            desde = desde.replace(year=hoy.year - 1, month=12, day=1)
        return desde, hoy
    if rango == "anio":
        return hoy.replace(month=1, day=1), hoy
    if rango == "anio_anterior":
        return hoy.replace(year=hoy.year - 1, month=1, day=1), hoy.replace(month=1, day=1) - timedelta(days=1)
    if rango == "todo":
        return None, None
    if rango == "personalizado":
        desde = request.GET.get("fecha_desde") or None
        hasta = request.GET.get("fecha_hasta") or None
        if desde:
            try:
                desde = date.fromisoformat(desde)
            except ValueError:
                desde = None
        if hasta:
            try:
                hasta = date.fromisoformat(hasta)
            except ValueError:
                hasta = None
        return desde, hasta
    # Default: este mes
    return hoy.replace(day=1), hoy


class MovimientoListView(LoginRequiredMixin, ListView):
    template_name = "movimientos/lista.html"
    context_object_name = "movimientos"
    paginate_by = 15

    def get_queryset(self):
        rango = self.request.GET.get("rango", "mes")
        fecha_desde, fecha_hasta = _resolver_rango(self.request)
        filtros = {
            "tipo": self.request.GET.get("tipo") or None,
            "estado": self.request.GET.get("estado") or None,
            "origen": self.request.GET.get("origen") or None,
            "categoria": self.request.GET.get("categoria") or None,
            "tercero": self.request.GET.get("tercero") or None,
            "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
            "q": self.request.GET.get("q") or None,
        }
        self._rango = rango
        self._fecha_desde = fecha_desde
        self._fecha_hasta = fecha_hasta
        return listar_movimientos(filtros)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categorias"] = Categoria.objects.filter(activo=True)
        ctx["filtros"] = self.request.GET
        ctx["rango_activo"] = getattr(self, "_rango", "mes")
        ctx["fecha_desde_filtro"] = getattr(self, "_fecha_desde", None)
        ctx["fecha_hasta_filtro"] = getattr(self, "_fecha_hasta", None)
        # Total de movimientos sin paginar para mostrar conteo
        from .selectors import listar_movimientos as lm
        rango = self.request.GET.get("rango", "mes")
        fecha_desde, fecha_hasta = _resolver_rango(self.request)
        qs_total = lm({
            "tipo": self.request.GET.get("tipo") or None,
            "estado": self.request.GET.get("estado") or None,
            "origen": self.request.GET.get("origen") or None,
            "categoria": self.request.GET.get("categoria") or None,
            "tercero": self.request.GET.get("tercero") or None,
            "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
            "q": self.request.GET.get("q") or None,
        })
        ctx["total_filtrado"] = qs_total.count()
        return ctx


class MovimientoDetailView(LoginRequiredMixin, DetailView):
    model = None  # set below
    template_name = "movimientos/detalle.html"
    context_object_name = "movimiento"


from .models import Movimiento  # noqa: E402

MovimientoDetailView.model = Movimiento


class MovimientoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Movimiento
    form_class = MovimientoForm
    template_name = "movimientos/formulario.html"
    success_url = reverse_lazy("movimientos:lista")
    success_message = "Movimiento creado correctamente."

    @method_decorator(administrador_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = services.crear_movimiento(form, usuario=self.request.user)
        return HttpResponseRedirect(self.get_success_url())


class MovimientoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Movimiento
    form_class = MovimientoForm
    template_name = "movimientos/formulario.html"
    success_url = reverse_lazy("movimientos:lista")
    success_message = "Movimiento actualizado correctamente."

    @method_decorator(administrador_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = services.actualizar_movimiento(
            form.instance, form, usuario=self.request.user
        )
        return HttpResponseRedirect(self.get_success_url())


class MovimientoDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Movimiento
    template_name = "movimientos/eliminar.html"
    success_url = reverse_lazy("movimientos:lista")
    success_message = "Movimiento eliminado."

    @method_decorator(administrador_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        services.eliminar_movimiento(obj, usuario=request.user)
        return HttpResponseRedirect(self.success_url)


@administrador_required
def cambiar_estado_conciliacion(request, pk):
    movimiento = get_object_or_404(Movimiento, pk=pk)
    nuevo = request.POST.get("estado")
    if nuevo not in dict(EstadoConciliacion.choices):
        messages.error(request, "Estado invalido.")
        return redirect("movimientos:detalle", pk=pk)
    services.cambiar_estado_conciliacion(
        movimiento, nuevo, usuario=request.user
    )
    messages.success(request, f"Estado actualizado a {nuevo}.")
    return redirect("movimientos:detalle", pk=pk)
