from django.contrib import admin

from .models import PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "endpoint", "activo", "creado_en")
    list_filter = ("activo", "creado_en")
    search_fields = ("user__username", "endpoint")
    readonly_fields = ("creado_en",)
