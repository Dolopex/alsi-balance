"""Crea datos iniciales (seed) para ALSI BALANCE.

- Crea un superusuario administrador si no existe.
- Crea categorias iniciales de ingresos y egresos.
- Crea una configuracion de sistema con saldo inicial en 0.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Inicializa categorias, configuracion y superusuario administrador."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--password", default="alsi2026")
        parser.add_argument("--email", default="admin@alsi.local")

    @transaction.atomic
    def handle(self, *args, **options):
        from usuarios.models import Usuario, Rol
        from categorias.models import Categoria
        from core.models import ConfiguracionSistema, TipoMovimiento

        username = options["username"]
        password = options["password"]
        email = options["email"]

        # Superusuario administrador
        if not Usuario.objects.filter(username=username).exists():
            Usuario.objects.create_superuser(
                username=username,
                password=password,
                email=email,
                rol=Rol.ADMINISTRADOR,
                first_name="Administrador",
                last_name="ALSI",
            )
            self.stdout.write(self.style.SUCCESS(f"Usuario administrador creado: {username}/{password}"))
        else:
            u = Usuario.objects.get(username=username)
            if not u.es_administrador:
                u.rol = Rol.ADMINISTRADOR
                u.is_staff = True
                u.is_superuser = True
                u.save()
            self.stdout.write(f"Usuario {username} ya existe.")

        # Configuracion del sistema
        config, creado = ConfiguracionSistema.objects.get_or_create(
            defaults={
                "banco": "Bancolombia",
                "nombre_cuenta": "Cuenta principal",
                "saldo_inicial": Decimal("0.00"),
            }
        )
        if creado:
            self.stdout.write(self.style.SUCCESS("Configuracion del sistema creada."))

        # Categorias iniciales
        ingresos = [
            ("Venta de productos", "#10b981", "Venta principal de la operacion."),
            ("Venta de alevinos", "#22c55e", "Venta de alevinos / piscicultura."),
            ("Servicios", "#3b82f6", "Servicios prestados."),
            ("Proyectos", "#6366f1", "Ingresos por proyectos especiales."),
            ("Otros ingresos", "#94a3b8", "Ingresos varios."),
        ]
        egresos = [
            ("Proveedores", "#ef4444", "Pagos a proveedores."),
            ("Nomina", "#f97316", "Pagos de nomina y prestacion."),
            ("Transporte", "#eab308", "Transporte y logistica."),
            ("Servicios publicos", "#0ea5e9", "Energia, agua, internet."),
            ("Compras", "#dc2626", "Compras generales."),
            ("Equipos", "#a855f7", "Compra de equipos."),
            ("Materiales", "#ec4899", "Materiales e insumos."),
            ("Impuestos", "#7c3aed", "Impuestos y obligaciones."),
            ("Comisiones", "#fb923c", "Comisiones bancarias y otros."),
            ("Mantenimiento", "#14b8a6", "Mantenimiento operativo."),
            ("Otros gastos", "#64748b", "Gastos varios."),
        ]

        creados = 0
        for nombre, color, desc in ingresos:
            obj, fue_creado = Categoria.objects.get_or_create(
                nombre=nombre,
                tipo=TipoMovimiento.INGRESO,
                defaults={"color": color, "descripcion": desc},
            )
            if fue_creado:
                creados += 1
        for nombre, color, desc in egresos:
            obj, fue_creado = Categoria.objects.get_or_create(
                nombre=nombre,
                tipo=TipoMovimiento.EGRESO,
                defaults={"color": color, "descripcion": desc},
            )
            if fue_creado:
                creados += 1

        self.stdout.write(self.style.SUCCESS(f"Categorias creadas: {creados}"))
        self.stdout.write(self.style.SUCCESS("Seed completado."))
