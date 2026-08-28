"""Muestra el contenido completo de los correos IGNORADO."""

from django.core.management.base import BaseCommand

from gmail_integration.models import EmailProcesado


class Command(BaseCommand):
    help = "Muestra el contenido completo de correos ignorados."

    def add_arguments(self, parser):
        parser.add_argument("--limite", type=int, default=5)
        parser.add_argument("--message-id", help="ID especifico a ver")

    def handle(self, *args, **options):
        qs = EmailProcesado.objects.filter(estado="IGNORADO")
        if options.get("message_id"):
            qs = qs.filter(message_id__icontains=options["message_id"])
        correos = qs.order_by("-procesado_en")[:options["limite"]]
        for c in correos:
            self.stdout.write(self.style.HTTP_INFO(f"\n=== {c.message_id} ==="))
            self.stdout.write(f"  Remit: {c.remitente}")
            self.stdout.write(f"  Asun:  {c.asunto}")
            data = c.datos_extraidos or {}
            self.stdout.write(self.style.WARNING(f"\n  snippet:\n{data.get('snippet', '')[:500]}"))
            self.stdout.write(self.style.WARNING(f"\n  cuerpo_preview:\n{data.get('cuerpo_preview', '')[:500]}"))
            self.stdout.write("")
