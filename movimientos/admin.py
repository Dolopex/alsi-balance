from django.contrib import admin

from .models import Comprobante, Movimiento


@admin.register(Comprobante)
class ComprobanteAdmin(admin.ModelAdmin):
    list_display = ("id", "subido_en", "subido_por", "mime_type", "tamano_bytes")
    readonly_fields = ("subido_en", "tamano_bytes", "mime_type")


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = (
        "fecha",
        "tipo",
        "valor",
        "concepto",
        "categoria",
        "estado_conciliacion",
        "origen",
    )
    list_filter = ("tipo", "estado_conciliacion", "origen", "categoria", "banco")
    search_fields = ("concepto", "descripcion", "referencia", "tercero")
    autocomplete_fields = ()
    readonly_fields = ("creado_en", "actualizado_en")
