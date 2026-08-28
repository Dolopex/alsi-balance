from django.contrib import admin

from .models import Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "activo", "actualizado_en")
    list_filter = ("tipo", "activo")
    search_fields = ("nombre",)
