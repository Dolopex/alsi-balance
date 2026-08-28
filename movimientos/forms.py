from django import forms
from django.utils import timezone

from core.models import (
    EstadoConciliacion,
    OrigenMovimiento,
    TipoMovimiento,
)
from categorias.models import Categoria
from .models import Comprobante, Movimiento


class ComprobanteForm(forms.ModelForm):
    class Meta:
        model = Comprobante
        fields = ("imagen", "archivo")


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = (
            "tipo",
            "fecha",
            "hora",
            "valor",
            "concepto",
            "descripcion",
            "categoria",
            "subcategoria",
            "banco",
            "cuenta",
            "cuenta_destino",
            "nombre_destinatario",
            "referencia",
            "tercero",
            "saldo_despues",
            "estado_conciliacion",
            "origen",
            "comprobante",
        )
        widgets = {
            "fecha": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "hora": forms.TimeInput(attrs={"type": "time"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].initial = timezone.localdate()
        self.fields["categoria"].queryset = Categoria.objects.filter(activo=True)
        self.fields["origen"].initial = OrigenMovimiento.MANUAL
        self.fields["estado_conciliacion"].initial = EstadoConciliacion.PENDIENTE

    def clean_valor(self):
        valor = self.cleaned_data["valor"]
        if valor is None or valor <= 0:
            raise forms.ValidationError("El valor debe ser mayor a cero.")
        return valor
