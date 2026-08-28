"""Lista correos de Gmail ignorados/no reconocidos con su contenido.

Ayuda a depurar el parser mostrando el snippet y cuerpo de cada correo
que no se pudo interpretar automaticamente.
"""

from django.core.management.base import BaseCommand

from gmail_integration.models import EmailProcesado


class Command(BaseCommand):
    help = "Lista correos Gmail no reconocidos para depurar el parser."

    def add_arguments(self, parser):
        parser.add_argument(
            "--estado",
            default="IGNORADO",
            help="Filtra por estado (IGNORADO, ERROR, EXITOSO)",
        )
        parser.add_argument(
            "--limite",
            type=int,
            default=10,
            help="Numero maximo de correos a mostrar",
        )
        parser.add_argument(
            "--todos",
            action="store_true",
            help="Muestra todos los correos (no solo los ignorados)",
        )

    def handle(self, *args, **options):
        estado = None if options["todos"] else options["estado"]
        limite = options["limite"]

        qs = EmailProcesado.objects.all().order_by("-procesado_en")
        if estado:
            qs = qs.filter(estado=estado)

        correos = qs[:limite]
        total = qs.count()

        if not correos:
            self.stdout.write(self.style.WARNING(
                "No hay correos con esos filtros."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Mostrando {len(correos)} de {total} correos con estado"
            f" {estado or 'todos'}:"
        ))
        self.stdout.write("")

        for i, c in enumerate(correos, 1):
            self.stdout.write(self.style.HTTP_INFO(
                f"#{i} [{c.estado}] message_id={c.message_id[:40]}..."
            ))
            self.stdout.write(f"  De:      {c.remitente}")
            self.stdout.write(f"  Asunto:  {c.asunto}")
            self.stdout.write(f"  Fecha:   {c.fecha_correo}")
            self.stdout.write(f"  Creado:  {c.procesado_en}")

            data = c.datos_extraidos or {}
            if data:
                self.stdout.write(self.style.WARNING("  Datos:"))
                for k, v in data.items():
                    if isinstance(v, str) and len(v) > 200:
                        v = v[:200] + "..."
                    self.stdout.write(f"    {k}: {v}")
            self.stdout.write("")
