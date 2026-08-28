"""Sincroniza correos recientes de Gmail.

A diferencia de sincronizar_gmail que usa days_back fijo,
este comando busca correos desde la ULTIMA SINCRONIZACION
guardada en ConfiguracionGmail. Si nunca se ha sincronizado,
usa 30 dias por defecto.
"""

from django.core.management.base import BaseCommand

from gmail_integration.services import sincronizar_correos
from gmail_integration.models import ConfiguracionGmail
from datetime import datetime, timezone, timedelta


class Command(BaseCommand):
    help = "Sincroniza correos nuevos desde la ultima sincronizacion."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias-fallback",
            type=int,
            default=30,
            help="Si nunca se ha sincronizado, usar este rango en dias.",
        )
        parser.add_argument(
            "--max",
            type=int,
            default=100,
            help="Maximo de correos a procesar.",
        )
        parser.add_argument(
            "--forzar",
            action="store_true",
            help="Forzar re-sincronizacion de los ultimos N dias (no solo desde la ultima).",
        )
        parser.add_argument(
            "--dias",
            type=int,
            default=7,
            help="Si --forzar, sincronizar los ultimos N dias.",
        )

    def handle(self, *args, **options):
        config = ConfiguracionGmail.objects.first()
        if not config or not config.conectado:
            self.stdout.write(self.style.ERROR(
                "Gmail no esta conectado. Ve al dashboard y haz clic en 'Conectar Gmail'."
            ))
            return

        if options["forzar"]:
            days_back = options["dias"]
            self.stdout.write(f"Forzando sincronizacion de los ultimos {days_back} dias...")
        elif config.ultima_sincronizacion:
            # Buscar correos desde la ultima sincronizacion
            ahora = datetime.now(timezone.utc)
            dias_desde = (ahora - config.ultima_sincronizacion).days + 1
            days_back = max(1, min(dias_desde, 30))
            self.stdout.write(
                f"Ultima sincronizacion: {config.ultima_sincronizacion.strftime('%Y-%m-%d %H:%M')}"
            )
            self.stdout.write(f"Buscando correos de los ultimos {days_back} dias...")
        else:
            days_back = options["dias_fallback"]
            self.stdout.write(
                f"Primera sincronizacion. Buscando ultimos {days_back} dias..."
            )

        metricas = sincronizar_correos(
            max_results=options["max"],
            days_back=days_back,
        )
        self.stdout.write(self.style.SUCCESS(
            f"\nResultado: Procesados={metricas['procesados']} | "
            f"Nuevos={metricas['nuevos']} | "
            f"Ignorados={metricas['ignorados']} | "
            f"Errores={metricas['errores']}"
        ))

        if metricas["nuevos"] > 0:
            self.stdout.write(self.style.SUCCESS(
                f"Se crearon {metricas['nuevos']} movimientos nuevos."
            ))
