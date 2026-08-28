"""Procesa un correo pegado como texto (sin Gmail API).

Permite probar el parser con correos reales sin tener que sincronizar Gmail.
"""

from django.core.management.base import BaseCommand

from gmail_integration.parser import parsear
from gmail_integration.services import procesar_correo_simulado


class Command(BaseCommand):
    help = "Probar el parser con un correo pegado como texto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--remitente",
            default="alertasynotificaciones@an.notificacionesbancolombia.com",
            help="Remitente del correo",
        )
        parser.add_argument(
            "--asunto",
            default="Bancolombia - Movimiento en cuenta",
            help="Asunto del correo",
        )
        parser.add_argument(
            "--cuerpo",
            help="Cuerpo del correo (texto plano)",
        )
        parser.add_argument(
            "--no-guardar",
            action="store_true",
            help="Solo parsear, no crear movimiento",
        )

    def handle(self, *args, **options):
        cuerpo = options.get("cuerpo")
        if not cuerpo:
            self.stderr.write("Debes pasar --cuerpo con el texto del correo.")
            return

        resultado = parsear(options["remitente"], options["asunto"], cuerpo)
        if resultado is None:
            self.stdout.write(self.style.WARNING(
                "El parser NO reconocio este correo. Revisa las palabras clave y el formato."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Movimiento detectado: {resultado.tipo} ${resultado.valor:,.2f} "
            f"fecha={resultado.fecha} cuenta={resultado.cuenta} hora={resultado.hora}"
        ))
        self.stdout.write(f"  Tipo:       {resultado.tipo}")
        self.stdout.write(f"  Valor:      ${resultado.valor:,.2f}")
        self.stdout.write(f"  Fecha:      {resultado.fecha}")
        self.stdout.write(f"  Concepto:   {resultado.concepto}")
        self.stdout.write(f"  Referencia: {resultado.referencia}")
        self.stdout.write(f"  Cuenta:     {resultado.cuenta}")
        self.stdout.write(f"  Destino:    {resultado.cuenta_destino}")
        self.stdout.write(f"  Tercero:    {resultado.tercero}")
        self.stdout.write(f"  Saldo:      {resultado.saldo_despues}")
        self.stdout.write(f"  Parser:     {resultado.parser_usado}")

        if not options["no_guardar"]:
            message_id = "test-" + str(hash(cuerpo))
            metricas = procesar_correo_simulado(
                options["remitente"],
                options["asunto"],
                cuerpo,
                message_id=message_id,
            )
            self.stdout.write(self.style.SUCCESS(
                f"\nMetricas: {metricas}"
            ))
