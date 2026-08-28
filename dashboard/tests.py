from django.test import TestCase
from django.urls import reverse
from datetime import date
from decimal import Decimal

from usuarios.models import Usuario
from categorias.models import Categoria
from core.models import TipoMovimiento
from movimientos.models import Movimiento


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username="admin", password="segura12345"
        )
        self.client.login(username="admin", password="segura12345")
        cat = Categoria.objects.create(nombre="Ventas", tipo=TipoMovimiento.INGRESO)
        Movimiento.objects.create(
            tipo=TipoMovimiento.INGRESO,
            valor=Decimal("100000.00"),
            fecha=date.today(),
            concepto="Venta de prueba",
            categoria=cat,
        )

    def test_dashboard_carga(self):
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "ALSI BALANCE")
        self.assertContains(resp, "Venta de prueba")

    def test_dashboard_requiere_login(self):
        self.client.logout()
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 302)
