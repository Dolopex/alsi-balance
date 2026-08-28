from django.test import TestCase
from django.urls import reverse

from core.models import TipoMovimiento
from .models import Categoria


class CategoriaModelTests(TestCase):
    def test_crear_categoria_ingreso(self):
        c = Categoria.objects.create(
            nombre="Venta de productos",
            tipo=TipoMovimiento.INGRESO,
        )
        self.assertEqual(str(c), "Venta de productos (Ingreso)")

    def test_unique_nombre_tipo(self):
        Categoria.objects.create(nombre="Servicios", tipo=TipoMovimiento.INGRESO)
        with self.assertRaises(Exception):
            Categoria.objects.create(nombre="Servicios", tipo=TipoMovimiento.INGRESO)


class CategoriaViewTests(TestCase):
    def setUp(self):
        from usuarios.models import Usuario
        self.user = Usuario.objects.create_user(
            username="admin",
            password="segura12345",
        )

    def test_lista_requiere_login(self):
        resp = self.client.get(reverse("categorias:lista"))
        self.assertEqual(resp.status_code, 302)
