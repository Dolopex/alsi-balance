from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario, Rol


class UsuarioCrearForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "rol",
            "documento",
            "telefono",
            "cargo",
            "password1",
            "password2",
        )
        widgets = {
            "rol": forms.Select(choices=Rol.choices),
        }


class UsuarioEditarForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = (
            "first_name",
            "last_name",
            "email",
            "rol",
            "documento",
            "telefono",
            "cargo",
            "is_active",
        )
