from django.test import TestCase

from datetime import date
from decimal import Decimal

from core.models import ConfiguracionSistema, TipoMovimiento
from core.services import calcular_balance, calcular_saldo
from core.selectors import obtener_configuracion, obtener_saldo_inicial


class CoreServicesTests(TestCase):
    def test_obtener_saldo_inicial_sin_config_retorna_cero(self):
        self.assertEqual(obtener_saldo_inicial(), Decimal("0.00"))

    def test_obtener_saldo_inicial_con_config(self):
        ConfiguracionSistema.objects.create(saldo_inicial=Decimal("1500.00"))
        self.assertEqual(obtener_saldo_inicial(), Decimal("1500.00"))

    def test_obtener_configuracion(self):
        self.assertIsNone(obtener_configuracion())
        c = ConfiguracionSistema.objects.create(saldo_inicial=Decimal("100.00"))
        self.assertEqual(obtener_configuracion().id, c.id)

    def test_calcular_balance_y_saldo_con_movimientos(self):
        from movimientos.models import Movimiento
        from categorias.models import Categoria

        cat = Categoria.objects.create(nombre="General", tipo=TipoMovimiento.INGRESO)
        Movimiento.objects.create(
            tipo=TipoMovimiento.INGRESO,
            valor=Decimal("1000.00"),
            fecha=date(2026, 8, 23),
            concepto="Venta",
            categoria=cat,
        )
        cat_e = Categoria.objects.create(nombre="Gastos", tipo=TipoMovimiento.EGRESO)
        Movimiento.objects.create(
            tipo=TipoMovimiento.EGRESO,
            valor=Decimal("300.00"),
            fecha=date(2026, 8, 23),
            concepto="Compra",
            categoria=cat_e,
        )
        qs = Movimiento.objects.all()
        bal = calcular_balance(qs)
        self.assertEqual(bal["ingresos"], Decimal("1000.00"))
        self.assertEqual(bal["egresos"], Decimal("300.00"))
        self.assertEqual(bal["balance"], Decimal("700.00"))
        self.assertEqual(calcular_saldo(Decimal("5000.00"), qs), Decimal("5700.00"))
