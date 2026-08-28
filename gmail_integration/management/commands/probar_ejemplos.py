"""Procesa correos de prueba directamente en la base de datos.

Util para verificar que el parser funciona con correos especificos
que el usuario quiere probar, sin tener que sincronizar Gmail.
"""

from django.core.management.base import BaseCommand

from gmail_integration.services import procesar_correo_simulado


CORREOS_EJEMPLO = [
    {
        "nombre": "Transferiste 1 millon (5.000.000 con comas)",
        "remitente": "alertasynotificaciones@an.notificacionesbancolombia.com",
        "asunto": "Transferencia enviada",
        "cuerpo": "Bancolombia: Transferiste 5.000.000 desde tu cuenta 0736 a la cuenta *987654321 el 26/08/2026 14:32.",
    },
    {
        "nombre": "Pagaste 5 mil (5.000,00 pesos)",
        "remitente": "alertasynotificaciones@an.notificacionesbancolombia.com",
        "asunto": "Pago realizado",
        "cuerpo": "Bancolombia: Pagaste 5.000,00 a APORTES EN LINEA desde tu cuenta 0736 el 26/08/2026 18:00.",
    },
    {
        "nombre": "Consignacion recibida con destinatario",
        "remitente": "alertasynotificaciones@an.notificacionesbancolombia.com",
        "asunto": "Consignacion",
        "cuerpo": "Bancolombia: Recibiste una consignacion por 1.500.000 de CARLOS PEREZ en tu cuenta **0736 el 26/08/2026 16:00.",
    },
    {
        "nombre": "Compra con formato US (75,50)",
        "remitente": "alertasynotificaciones@an.notificacionesbancolombia.com",
        "asunto": "Compra",
        "cuerpo": "Bancolombia: Compra por 75,50 en ESTABLECIMIENTO XYZ el 26/08/2026 12:00.",
    },
    {
        "nombre": "Correo que NO es de Bancolombia (debe ser IGNORADO)",
        "remitente": "newsletter@tienda-online.com",
        "asunto": "Oferta del dia",
        "cuerpo": "Aprovecha esta oferta unica! 50% de descuento en todos los productos.",
    },
]


class Command(BaseCommand):
    help = "Procesa correos de ejemplo predefinidos para verificar el parser."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-guardar",
            action="store_true",
            help="Solo parsear, no crear movimientos.",
        )
        parser.add_argument(
            "--solo",
            type=int,
            help="Solo procesar el correo numero N (1-indexed).",
        )

    def handle(self, *args, **options):
        from gmail_integration.models import EmailProcesado
        from movimientos.models import Movimiento
        from gmail_integration.parser import parsear, es_correo_bancolombia

        movs_antes = Movimiento.objects.count()
        if not options["no_guardar"]:
            # Borrar movimientos creados por pruebas anteriores
            Movimiento.objects.filter(email_message_id__startswith="demo-").delete()
            EmailProcesado.objects.filter(message_id__startswith="demo-").delete()

        correos = CORREOS_EJEMPLO
        if options.get("solo"):
            correos = [correos[options["solo"] - 1]]

        self.stdout.write(self.style.HTTP_INFO(
            f"Procesando {len(correos)} correos de ejemplo...\n"
        ))

        for i, datos in enumerate(correos, 1):
            self.stdout.write(f"\n--- Correo {i}: {datos['nombre']} ---")
            message_id = f"demo-{i}-{abs(hash(datos['cuerpo'])) % 1000000}"

            # Primero verificar si es de Bancolombia
            es_bancolombia = es_correo_bancolombia(
                datos["remitente"], datos["asunto"]
            )
            self.stdout.write(f"  Es Bancolombia: {es_bancolombia}")

            metricas = procesar_correo_simulado(
                datos["remitente"],
                datos["asunto"],
                datos["cuerpo"],
                message_id=message_id,
            )
            self.stdout.write(
                f"  Resultado: nuevos={metricas['nuevos']} | "
                f"ignorados={metricas['ignorados']} | "
                f"errores={metricas['errores']}"
            )

        movs_despues = Movimiento.objects.count()
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Movimientos antes: {movs_antes} | despues: {movs_despues} | "
            f"creados: {movs_despues - movs_antes}"
        ))
