"""Comando para sincronizar correos de Gmail manualmente.

Uso:
    python manage.py sincronizar_gmail
"""

from django.core.management.base import BaseCommand

from gmail_integration.services import sincronizar_correos


class Command(BaseCommand):
    help = "Sincroniza correos recientes de Bancolombia desde Gmail."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=30,
            help="Buscar correos de los ultimos N dias (default 30).",
        )
        parser.add_argument(
            "--max",
            type=int,
            default=50,
            help="Numero maximo de correos a procesar (default 50).",
        )

    def handle(self, *args, **options):
        dias = options["dias"]
        maximo = options["max"]
        self.stdout.write(f"Sincronizando Gmail (ultimos {dias} dias, max {maximo})...")
        metricas = sincronizar_correos(max_results=maximo, days_back=dias)
        self.stdout.write(self.style.SUCCESS(
            f"Procesados={metricas['procesados']} | "
            f"Nuevos={metricas['nuevos']} | "
            f"Ignorados={metricas['ignorados']} | "
            f"Errores={metricas['errores']}"
        ))
