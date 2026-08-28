"""Borra todos los movimientos y vuelve a sincronizar Gmail desde cero.

Util cuando ajustas el parser o quieres empezar con datos limpios.
Conserva: usuarios, categorias, configuracion del sistema.
Borra: Movimiento, EmailProcesado, RegistroAuditoria relacionado.
"""

from django.core.management.base import BaseCommand
from django.core import management


class Command(BaseCommand):
    help = "Borra movimientos y re-sincroniza Gmail."

    def add_arguments(self, parser):
        parser.add_argument(
            "--si",
            action="store_true",
            help="No pedir confirmacion.",
        )
        parser.add_argument(
            "--dias",
            type=int,
            default=30,
            help="Buscar correos de los ultimos N dias.",
        )
        parser.add_argument(
            "--max",
            type=int,
            default=100,
            help="Maximo de correos a procesar.",
        )
        parser.add_argument(
            "--no-gmail",
            action="store_true",
            help="Solo borrar, no sincronizar Gmail.",
        )

    def handle(self, *args, **options):
        from movimientos.models import Movimiento
        from gmail_integration.models import EmailProcesado, ConfiguracionGmail

        total_movs = Movimiento.objects.count()
        total_emails = EmailProcesado.objects.count()

        self.stdout.write(self.style.WARNING(
            f"\nVas a borrar {total_movs} movimientos y {total_emails} registros de email."
        ))

        if not options["si"]:
            confirm = input("¿Continuar? (s/N): ")
            if confirm.lower() not in ("s", "y", "si", "yes"):
                self.stdout.write("Cancelado.")
                return

        # Borrar
        self.stdout.write("Borrando movimientos...")
        Movimiento.objects.all().delete()
        EmailProcesado.objects.all().delete()

        movs_after = Movimiento.objects.count()
        emails_after = EmailProcesado.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Borrado. Quedan {movs_after} movimientos y {emails_after} emails."
        ))

        if options["no_gmail"]:
            return

        # Verificar Gmail conectado
        config = ConfiguracionGmail.objects.first()
        if not config or not config.conectado:
            self.stdout.write(self.style.ERROR(
                "\nGmail no esta conectado. Ve al dashboard y conecta primero."
            ))
            return

        # Sincronizar
        self.stdout.write("\nSincronizando Gmail...")
        from gmail_integration.services import sincronizar_correos
        metricas = sincronizar_correos(
            max_results=options["max"],
            days_back=options["dias"],
        )
        self.stdout.write(self.style.SUCCESS(
            f"\nResultado de la sincronizacion:"
        ))
        self.stdout.write(f"  - Procesados: {metricas['procesados']}")
        self.stdout.write(f"  - Nuevos:     {metricas['nuevos']}")
        self.stdout.write(f"  - Ignorados:  {metricas['ignorados']}")
        self.stdout.write(f"  - Errores:    {metricas['errores']}")

        nuevos = Movimiento.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"\nTotal de movimientos en BD: {nuevos}"
        ))
