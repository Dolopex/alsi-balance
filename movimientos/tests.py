from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import EstadoConciliacion, OrigenMovimiento, TipoMovimiento
from categorias.models import Categoria

from .models import Movimiento
from .deduplicacion import buscar_duplicados, calcular_similitud


class MovimientoModelTests(TestCase):
    def test_signo_valor_en_egreso(self):
        cat = Categoria.objects.create(nombre="Ventas", tipo=TipoMovimiento.INGRESO)
        m = Movimiento.objects.create(
            tipo=TipoMovimiento.EGRESO,
            valor=Decimal("200.00"),
            fecha=date.today(),
            concepto="Gasto",
            categoria=cat,
        )
        self.assertEqual(m.valor_con_signo, Decimal("-200.00"))


class MovimientoCRUDTests(TestCase):
    def setUp(self):
        from usuarios.models import Usuario
        self.user = Usuario.objects.create_user(
            username="admin",
            password="segura12345",
            rol="ADMINISTRADOR",
        )
        self.client.login(username="admin", password="segura12345")
        self.cat = Categoria.objects.create(
            nombre="Ventas", tipo=TipoMovimiento.INGRESO
        )

    def test_crear_movimiento_via_form(self):
        url = reverse("movimientos:crear")
        data = {
            "tipo": TipoMovimiento.INGRESO,
            "fecha": date.today().isoformat(),
            "hora": "10:00",
            "valor": "150000.00",
            "concepto": "Venta de alevinos",
            "descripcion": "Cliente A",
            "categoria": self.cat.pk,
            "banco": "Bancolombia",
            "estado_conciliacion": EstadoConciliacion.PENDIENTE,
            "origen": OrigenMovimiento.MANUAL,
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Movimiento.objects.count(), 1)
        m = Movimiento.objects.first()
        self.assertEqual(m.valor, Decimal("150000.00"))
        self.assertEqual(m.creado_por, self.user)

    def test_lista_movimientos(self):
        Movimiento.objects.create(
            tipo=TipoMovimiento.INGRESO,
            valor=Decimal("100.00"),
            fecha=date.today(),
            concepto="X",
            categoria=self.cat,
        )
        resp = self.client.get(reverse("movimientos:lista"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "X")

    def test_validacion_valor_mayor_a_cero(self):
        url = reverse("movimientos:crear")
        data = {
            "tipo": TipoMovimiento.INGRESO,
            "fecha": date.today().isoformat(),
            "valor": "0",
            "concepto": "X",
            "categoria": self.cat.pk,
            "banco": "Bancolombia",
            "estado_conciliacion": EstadoConciliacion.PENDIENTE,
            "origen": OrigenMovimiento.MANUAL,
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Movimiento.objects.count(), 0)


class DeduplicacionTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(
            nombre="Ventas", tipo=TipoMovimiento.INGRESO
        )

    def test_detecta_duplicado_exacto(self):
        hoy = date.today()
        m1 = Movimiento.objects.create(
            tipo=TipoMovimiento.INGRESO,
            valor=Decimal("500000.00"),
            fecha=hoy,
            concepto="Venta",
            categoria=self.cat,
            referencia="REF123",
        )
        m2 = Movimiento.objects.create(
            tipo=TipoMovimiento.INGRESO,
            valor=Decimal("500000.00"),
            fecha=hoy,
            concepto="Venta",
            categoria=self.cat,
            referencia="REF123",
        )
        dup = buscar_duplicados(m1, umbral=70)
        self.assertTrue(any(d["movimiento"].pk == m2.pk for d in dup))

    def test_similitud_valor_y_fecha(self):
        hoy = date.today()
        m1 = Movimiento.objects.create(
            tipo=TipoMovimiento.INGRESO,
            valor=Decimal("100.00"),
            fecha=hoy,
            concepto="X",
            categoria=self.cat,
        )
        m2 = Movimiento.objects.create(
            tipo=TipoMovimiento.INGRESO,
            valor=Decimal("100.00"),
            fecha=hoy,
            concepto="X",
            categoria=self.cat,
        )
        score = calcular_similitud(m1, m2)
        self.assertGreaterEqual(score, 70)


class PermisosTests(TestCase):
    """Verifica que solo el administrador puede modificar movimientos."""

    def setUp(self):
        from usuarios.models import Usuario
        self.admin = Usuario.objects.create_user(
            username="admin",
            password="segura12345",
            rol="ADMINISTRADOR",
        )
        self.normal = Usuario.objects.create_user(
            username="empleado",
            password="segura12345",
            rol="USUARIO",
        )
        self.cat = Categoria.objects.create(
            nombre="Ventas", tipo=TipoMovimiento.INGRESO
        )
        self.mov = Movimiento.objects.create(
            tipo=TipoMovimiento.INGRESO,
            valor=Decimal("500.00"),
            fecha=date.today(),
            concepto="Test",
            categoria=self.cat,
        )

    def _data_post(self):
        return {
            "tipo": TipoMovimiento.INGRESO,
            "fecha": date.today().isoformat(),
            "valor": "100.00",
            "concepto": "X",
            "categoria": self.cat.pk,
            "banco": "Bancolombia",
            "estado_conciliacion": EstadoConciliacion.PENDIENTE,
            "origen": OrigenMovimiento.MANUAL,
        }

    def test_usuario_normal_no_puede_crear(self):
        self.client.login(username="empleado", password="segura12345")
        resp = self.client.post(reverse("movimientos:crear"), self._data_post())
        # 302 = redirigido al dashboard con mensaje de error
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Movimiento.objects.filter(concepto="X").count(), 0)

    def test_administrador_puede_crear(self):
        self.client.login(username="admin", password="segura12345")
        resp = self.client.post(reverse("movimientos:crear"), self._data_post())
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Movimiento.objects.filter(concepto="X").count(), 1)

    def test_usuario_normal_no_puede_editar(self):
        self.client.login(username="empleado", password="segura12345")
        resp = self.client.post(
            reverse("movimientos:editar", args=[self.mov.pk]),
            self._data_post(),
        )
        self.assertEqual(resp.status_code, 302)
        # El movimiento conserva su concepto original
        self.mov.refresh_from_db()
        self.assertEqual(self.mov.concepto, "Test")

    def test_usuario_normal_no_puede_eliminar(self):
        self.client.login(username="empleado", password="segura12345")
        resp = self.client.post(reverse("movimientos:eliminar", args=[self.mov.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Movimiento.objects.filter(pk=self.mov.pk).exists())

    def test_usuario_normal_no_puede_cambiar_estado_conciliacion(self):
        self.client.login(username="empleado", password="segura12345")
        resp = self.client.post(
            reverse("movimientos:conciliar", args=[self.mov.pk]),
            {"estado": "CONCILIADO"},
        )
        self.assertEqual(resp.status_code, 302)
        self.mov.refresh_from_db()
        self.assertEqual(self.mov.estado_conciliacion, EstadoConciliacion.PENDIENTE)

    def test_usuario_normal_puede_ver_lista(self):
        self.client.login(username="empleado", password="segura12345")
        resp = self.client.get(reverse("movimientos:lista"))
        self.assertEqual(resp.status_code, 200)

    def test_usuario_normal_puede_ver_detalle(self):
        self.client.login(username="empleado", password="segura12345")
        resp = self.client.get(reverse("movimientos:detalle", args=[self.mov.pk]))
        self.assertEqual(resp.status_code, 200)
        # No debe ver el boton de editar
        self.assertNotContains(resp, ">Editar<")
        self.assertNotContains(resp, ">Eliminar<")
