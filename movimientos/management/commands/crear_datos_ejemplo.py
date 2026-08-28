"""Crea datos de ejemplo para probar la aplicacion.

Genera movimientos de los ultimos 90 dias con varios tipos
y categorias para que la app tenga contenido realista.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from categorias.models import Categoria
from core.models import ConfiguracionSistema, EstadoConciliacion, OrigenMovimiento, TipoMovimiento
from movimientos.models import Movimiento
from usuarios.models import Usuario


CATEGORIAS_EGRESOS = [
    "Proveedores", "Compras", "Transporte", "Servicios publicos",
    "Nomina", "Mantenimiento", "Materiales", "Otros gastos",
]
CATEGORIAS_INGRESOS = [
    "Venta de productos", "Venta de alevinos", "Servicios", "Otros ingresos",
]

CONCEPTOS_EGRESO = [
    "Pago a proveedor", "Compra de insumos", "Servicio de transporte",
    "Pago de nomina", "Materiales de oficina", "Mantenimiento equipos",
    "Servicios publicos", "Pago de servicios", "Combustible",
]
CONCEPTOS_INGRESO = [
    "Venta de productos", "Pago de cliente", "Venta de servicios",
    "Consignacion cliente", "Venta de alevinos",
]


class Command(BaseCommand):
    help = "Crea datos de ejemplo para probar la aplicacion."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=90,
            help="Dias hacia atras para generar movimientos.",
        )
        parser.add_argument(
            "--cantidad",
            type=int,
            default=60,
            help="Cantidad de movimientos a crear.",
        )
        parser.add_argument(
            "--borrar",
            action="store_true",
            help="Borrar todos los movimientos antes de crear.",
        )

    def handle(self, *args, **options):
        if options["borrar"]:
            count = Movimiento.objects.count()
            Movimiento.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"Borrados {count} movimientos existentes."
            ))

        # Asegurar configuracion
        config, _ = ConfiguracionSistema.objects.get_or_create(
            defaults={"banco": "Bancolombia", "nombre_cuenta": "Cuenta principal"}
        )
        config.saldo_inicial = Decimal("10000000.00")
        config.save()

        # Asegurar admin
        admin, _ = Usuario.objects.get_or_create(
            username="admin",
            defaults={"rol": "ADMINISTRADOR", "is_staff": True, "is_superuser": True},
        )
        admin.set_password("alsi2026")
        admin.save()

        # Asegurar categorias
        for nombre in CATEGORIAS_EGRESOS + CATEGORIAS_INGRESOS:
            Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "tipo": (TipoMovimiento.EGRESO if nombre in CATEGORIAS_EGRESOS
                              else TipoMovimiento.INGRESO),
                },
            )

        hoy = timezone.localdate()
        count_actual = Movimiento.objects.count()
        self.stdout.write(f"Movimientos existentes: {count_actual}")

        creados = 0
        for i in range(options["cantidad"]):
            # Distribuir fechas en los ultimos N dias
            dias_atras = random.randint(0, options["dias"])
            fecha_mov = hoy - timedelta(days=dias_atras)
            hora = random.randint(7, 19)
            minuto = random.randint(0, 59)
            desde_cuenta = random.random() < 0.3  # 30% probabilidad de no tener

            if random.random() < 0.7:
                # Egreso
                tipo = TipoMovimiento.EGRESO
                categoria = Categoria.objects.filter(tipo=tipo).order_by("?").first()
                valor = Decimal(random.randint(50, 5000) * 1000)
                concepto = random.choice(CONCEPTOS_EGRESO)
                cuenta = "0736"
                cuenta_destino = f"*{random.randint(100000000, 999999999)}"
                nombre_destinatario = ""
            else:
                # Ingreso
                tipo = TipoMovimiento.INGRESO
                categoria = Categoria.objects.filter(tipo=tipo).order_by("?").first()
                valor = Decimal(random.randint(500, 20000) * 1000)
                concepto = random.choice(CONCEPTOS_INGRESO)
                cuenta = "**0736"
                cuenta_destino = ""
                nombre_destinatario = f"Cliente {random.randint(1, 100)}"

            estado = random.choice([
                EstadoConciliacion.PENDIENTE,
                EstadoConciliacion.PENDIENTE,
                EstadoConciliacion.CONCILIADO,
                EstadoConciliacion.OBSERVADO,
            ])

            Movimiento.objects.create(
                tipo=tipo,
                fecha=fecha_mov,
                hora=f"{hora:02d}:{minuto:02d}:00",
                valor=valor,
                concepto=concepto,
                categoria=categoria,
                cuenta=cuenta if not desde_cuenta else "",
                cuenta_destino=cuenta_destino,
                nombre_destinatario=nombre_destinatario,
                banco="Bancolombia",
                estado_conciliacion=estado,
                origen=random.choice([
                    OrigenMovimiento.EMAIL,
                    OrigenMovimiento.EMAIL,
                    OrigenMovimiento.MANUAL,
                ]),
                creado_por=admin,
            )
            creados += 1

        self.stdout.write(self.style.SUCCESS(
            f"Creados {creados} movimientos de ejemplo."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Total movimientos en BD: {Movimiento.objects.count()}"
        ))
