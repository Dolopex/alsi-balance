"""Borra todos los datos de la aplicacion.

Util antes de hacer pruebas pesadas o para empezar desde cero.
NO borra usuarios, categorias, configuracion ni datos de Gmail.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Borra movimientos, emails y auditoria."

    def add_arguments(self, parser):
        parser.add_argument(
            "--incluir-auditoria",
            action="store_true",
            help="Tambien borra registros de auditoria.",
        )
        parser.add_argument(
            "--si",
            action="store_true",
            help="No pedir confirmacion.",
        )

    def handle(self, *args, **options):
        from movimientos.models import Movimiento, Comprobante
        from gmail_integration.models import EmailProcesado
        from auditoria.models import RegistroAuditoria

        movs = Movimiento.objects.count()
        comps = Comprobante.objects.count()
        emails = EmailProcesado.objects.count()
        audit = RegistroAuditoria.objects.count()

        self.stdout.write(self.style.WARNING(
            f"Vas a borrar: {movs} movimientos, {comps} comprobantes, "
            f"{emails} emails, {audit} auditoria."
        ))

        if not options["si"]:
            confirm = input("¿Continuar? (s/N): ")
            if confirm.lower() not in ("s", "y", "si", "yes"):
                self.stdout.write("Cancelado.")
                return

        Movimiento.objects.all().delete()
        Comprobante.objects.all().delete()
        EmailProcesado.objects.all().delete()

        if options["incluir_auditoria"]:
            RegistroAuditoria.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(
                "Borrados: movimientos, comprobantes, emails, auditoria."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Borrados: movimientos, comprobantes, emails."
            ))
