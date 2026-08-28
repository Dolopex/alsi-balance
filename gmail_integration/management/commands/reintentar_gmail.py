"""Reintenta procesar correos Gmail marcados como IGNORADO.

Util cuando ajustamos el parser. Borra los registros IGNORADO
para que la siguiente sincronizacion los vuelva a procesar.
"""

from django.core.management.base import BaseCommand

from gmail_integration.models import EmailProcesado


class Command(BaseCommand):
    help = "Reintenta procesar correos Gmail ignorados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--todos",
            action="store_true",
            help="Borra TODOS los registros (no solo los ignorados).",
        )
        parser.add_argument(
            "--si",
            action="store_true",
            help="Confirma la operacion sin pedir confirmacion interactiva.",
        )

    def handle(self, *args, **options):
        qs = EmailProcesado.objects.all()
        if not options["todos"]:
            qs = qs.filter(estado="IGNORADO")

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No hay correos para reintentar."))
            return

        if not options["si"]:
            confirm = input(f"Vas a borrar {total} registros. ¿Continuar? (s/N): ")
            if confirm.lower() not in ("s", "si", "yes", "y"):
                self.stdout.write("Cancelado.")
                return

        borrados, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Se borraron {borrados} registros. La proxima sincronizacion los procesara de nuevo."
        ))
