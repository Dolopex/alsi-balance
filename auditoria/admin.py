from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "usuario", "accion", "movimiento")
    list_filter = ("accion", "fecha")
    search_fields = ("usuario__username", "accion", "movimiento__concepto")
    readonly_fields = (
        "fecha",
        "usuario",
        "accion",
        "movimiento",
        "datos_anteriores",
        "datos_nuevos",
        "ip",
        "user_agent",
    )

    def has_add_permission(self, request):
        return False
