from django.contrib import admin

from .models import ConfiguracionSistema


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ("banco", "nombre_cuenta", "saldo_inicial", "actualizado_en")
    readonly_fields = ("actualizado_en",)

    def has_add_permission(self, request):
        # Solo permitir un registro (singleton).
        return not ConfiguracionSistema.objects.exists()
