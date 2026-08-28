"""Reintenta procesar correos marcados como IGNORADO usando el parser actual.

Util cuando se actualiza el parser y se quieren reprocesar emails
que fueron ignorados por la version anterior.

Uso:
    python manage.py reprocesar_ignorados
    python manage.py reprocesar_ignorados --dry-run  # Solo muestra que haria
"""

from django.core.management.base import BaseCommand

from gmail_integration.models import EmailProcesado
from gmail_integration.parser import parsear


class Command(BaseCommand):
    help = "Reintenta procesar correos IGNORADO con la version actual del parser."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra cuantos emails se reprocesarian sin guardar",
        )
        parser.add_argument(
            "--crear",
            action="store_true",
            help="Crea Movimiento en la DB (requiere confirmacion)",
        )

    def handle(self, *args, **options):
        ignorados = EmailProcesado.objects.filter(estado="IGNORADO").order_by("-procesado_en")

        total = ignorados.count()
        self.stdout.write(f"Encontrados {total} emails en estado IGNORADO")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No hay emails para reprocesar"))
            return

        re_procesados_ok = 0
        re_procesados_fail = 0
        sin_datos = 0

        for email in ignorados:
            datos = email.datos_extraidos or {}
            snippet = datos.get("snippet", "")
            cuerpo = datos.get("cuerpo_preview", "")

            # Intentar con snippet primero, luego con cuerpo
            texto_parsear = cuerpo or snippet
            if not texto_parsear:
                sin_datos += 1
                continue

            try:
                resultado = parsear(email.remitente or "", email.asunto or "", texto_parsear)
            except Exception as exc:
                self.stdout.write(self.style.WARNING(
                    f"  id={email.pk}: error al parsear - {exc}"
                ))
                re_procesados_fail += 1
                continue

            if resultado is None:
                re_procesados_fail += 1
                continue

            self.stdout.write(
                f"  id={email.pk} OK: tipo={resultado.tipo} valor={resultado.valor} "
                f"fecha={resultado.fecha:%Y-%m-%d} cta={resultado.cuenta_destino or '?'}"
            )
            re_procesados_ok += 1

            if options["dry_run"]:
                continue

            if not options["crear"]:
                continue

            # Crear el movimiento
            from movimientos.models import Movimiento
            from core.models import OrigenMovimiento

            try:
                Movimiento.objects.create(
                    tipo=resultado.tipo,
                    fecha=resultado.fecha.date() if hasattr(resultado.fecha, "date") else resultado.fecha,
                    hora=resultado.hora,
                    valor=resultado.valor,
                    concepto=resultado.concepto or "",
                    descripcion=f"Reimportado de email {email.pk} ({email.remitente})",
                    banco="Bancolombia",
                    cuenta=resultado.cuenta,
                    cuenta_destino=resultado.cuenta_destino or "",
                    nombre_destinatario=resultado.tercero or "",
                    referencia=resultado.referencia or "",
                    tercero=resultado.tercero or "",
                    origen=OrigenMovimiento.EMAIL,
                    email_message_id=email.message_id,
                )
                email.estado = "EXITOSO"
                email.save(update_fields=["estado"])
            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f"  id={email.pk}: error al crear Movimiento - {exc}"
                ))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Resultado: {re_procesados_ok} procesables, "
            f"{re_procesados_fail} aun fallan, {sin_datos} sin datos"
        ))

        if options["crear"] and not options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(
                "Movimientos creados en la BD"
            ))
        elif re_procesados_ok > 0 and not options["dry_run"]:
            self.stdout.write(
                "\nPara crear los movimientos, corré con --crear"
            )