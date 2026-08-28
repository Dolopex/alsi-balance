from django.test import TestCase
from django.urls import reverse

from .models import Usuario, Rol


class UsuarioModelTests(TestCase):
    def test_crear_usuario(self):
        u = Usuario.objects.create_user(
            username="douglas",
            password="segura12345",
            email="d@alsi.co",
            rol=Rol.ADMINISTRADOR,
        )
        self.assertEqual(u.rol, Rol.ADMINISTRADOR)
        self.assertTrue(u.es_administrador)

    def test_es_administrador_false(self):
        u = Usuario.objects.create_user(
            username="ana",
            password="segura12345",
            rol=Rol.USUARIO,
        )
        self.assertFalse(u.es_administrador)


class AuthViewTests(TestCase):
    def test_login_view_carga(self):
        resp = self.client.get(reverse("usuarios:login"))
        self.assertEqual(resp.status_code, 200)

    def test_registro_view_carga(self):
        resp = self.client.get(reverse("usuarios:registro"))
        self.assertEqual(resp.status_code, 200)
