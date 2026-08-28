from django.contrib import admin

from .models import ConfiguracionGmail, EmailProcesado


@admin.register(ConfiguracionGmail)
class ConfiguracionGmailAdmin(admin.ModelAdmin):
    list_display = ("email_cuenta", "conectado", "ultima_sincronizacion")
    readonly_fields = ("ultima_sincronizacion", "actualizado_en")

    def has_add_permission(self, request):
        return not ConfiguracionGmail.objects.exists()


@admin.register(EmailProcesado)
class EmailProcesadoAdmin(admin.ModelAdmin):
    list_display = ("message_id", "estado", "remitente", "asunto", "procesado_en")
    list_filter = ("estado",)
    search_fields = ("message_id", "remitente", "asunto")
    readonly_fields = (
        "message_id", "thread_id", "remitente", "asunto",
        "fecha_correo", "estado", "movimiento", "datos_extraidos",
        "error", "procesado_en",
    )
