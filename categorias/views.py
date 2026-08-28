from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin

from usuarios.permissions import administrador_required
from .models import Categoria
from .forms import CategoriaForm


method_decorator(administrador_required, name="dispatch")


class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = "categorias/lista.html"
    context_object_name = "categorias"
    paginate_by = 50

    def get_queryset(self):
        qs = Categoria.objects.all()
        tipo = self.request.GET.get("tipo")
        if tipo in dict(Categoria._meta.get_field("tipo").choices):
            qs = qs.filter(tipo=tipo)
        return qs


class CategoriaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "categorias/formulario.html"
    success_url = reverse_lazy("categorias:lista")
    success_message = "Categoria creada correctamente."

    @method_decorator(administrador_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class CategoriaUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "categorias/formulario.html"
    success_url = reverse_lazy("categorias:lista")
    success_message = "Categoria actualizada correctamente."

    @method_decorator(administrador_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class CategoriaDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Categoria
    template_name = "categorias/eliminar.html"
    success_url = reverse_lazy("categorias:lista")
    success_message = "Categoria eliminada correctamente."

    @method_decorator(administrador_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
