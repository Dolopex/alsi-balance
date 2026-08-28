from django import forms

from core.models import TipoMovimiento
from .models import Categoria


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "tipo", "descripcion", "color", "activo"]
        widgets = {
            "tipo": forms.Select(choices=TipoMovimiento.choices),
            "color": forms.TextInput(attrs={"type": "color"}),
        }
