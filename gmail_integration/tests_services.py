"""Tests de servicios Gmail y deduplicacion."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from categorias.models import Categoria
from core.models import OrigenMovimiento, TipoMovimiento
from django.contrib.auth import get_user_model
from gmail_integration.models import ConfiguracionGmail, EmailProcesado
from gmail_integration.parser import parsear
from gmail_integration.services import (
    procesar_correo_simulado,
    sincronizar_correos,
    construir_flow_oauth,
)
from movimientos.models import Movimiento


class GmailServiceTests(TestCase):
    def setUp(self):
        ConfiguracionGmail.objects.create()

    def test_procesa_correo_simulado_ingreso(self):
        cuerpo = """
        Bancolombia - Transferencia recibida
        Fecha: 23/08/2026
        Valor: $300.000,00
        Concepto: Pago cliente
        Referencia: REF123
        """
        metricas = procesar_correo_simulado(
            "alertas@bancolombia.com.co",
            "Transferencia recibida",
            cuerpo,
            message_id="msg-001",
        )
        self.assertEqual(metricas["nuevos"], 1)
        self.assertEqual(Movimiento.objects.count(), 1)
        m = Movimiento.objects.first()
        self.assertEqual(m.origen, OrigenMovimiento.EMAIL)
        self.assertEqual(m.email_message_id, "msg-001")
        self.assertEqual(m.valor, Decimal("300000.00"))

    def test_no_duplica_correo(self):
        cuerpo = """
        Bancolombia informa
        Transferencia recibida por $100.000
        Fecha: 23/08/2026
        """
        procesar_correo_simulado(
            "alertas@bancolombia.com.co",
            "Transferencia recibida",
            cuerpo,
            message_id="dup-1",
        )
        metricas2 = procesar_correo_simulado(
            "alertas@bancolombia.com.co",
            "Transferencia recibida",
            cuerpo,
            message_id="dup-1",
        )
        self.assertEqual(metricas2["nuevos"], 0)
        self.assertEqual(metricas2["ignorados"], 1)
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_no_duplica_distinto_message_id(self):
        cuerpo = """
        Bancolombia informa
        Transferencia recibida por $200.000
        Fecha: 23/08/2026
        """
        procesar_correo_simulado(
            "alertas@bancolombia.com.co",
            "Transferencia recibida",
            cuerpo,
            message_id="dup-A",
        )
        procesar_correo_simulado(
            "alertas@bancolombia.com.co",
            "Transferencia recibida",
            cuerpo,
            message_id="dup-B",
        )
        self.assertEqual(Movimiento.objects.count(), 2)

    def test_ignora_correo_no_reconocido(self):
        cuerpo = "Hola mundo"
        metricas = procesar_correo_simulado(
            "amigo@gmail.com", "Saludos", cuerpo, message_id="ign-1"
        )
        self.assertEqual(metricas["nuevos"], 0)
        e = EmailProcesado.objects.filter(message_id="ign-1").first()
        self.assertIsNotNone(e)
        self.assertEqual(e.estado, "IGNORADO")

    def test_registra_email_procesado(self):
        cuerpo = """
        Bancolombia informa
        Compra por $50.000
        Fecha: 22/08/2026
        """
        procesar_correo_simulado(
            "alertas@bancolombia.com.co",
            "Compra realizada",
            cuerpo,
            message_id="reg-1",
        )
        email = EmailProcesado.objects.get(message_id="reg-1")
        self.assertEqual(email.estado, "EXITOSO")
        self.assertIsNotNone(email.movimiento)


class SincronizarCorreosTests(TestCase):
    """Tests del flujo de sincronizacion."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="admin", password="x", rol="ADMINISTRADOR"
        )
        self.config = ConfiguracionGmail.objects.create(conectado=True)

    def test_no_sincroniza_sin_conexion(self):
        self.config.conectado = False
        self.config.save()
        resultado = sincronizar_correos(days_back=7)
        self.assertIn("msg", resultado)
        self.assertIn("Gmail no conectado", resultado["msg"])
        self.assertEqual(resultado["nuevos"], 0)

    def test_no_crea_duplicados_por_message_id(self):
        cuerpo = (
            "Bancolombia: Recibiste una consignacion por 1.000.000 "
            "de TEST USER en tu cuenta **0736 el 26/08/2026 12:00."
        )
        # Primer procesamiento
        m1 = procesar_correo_simulado(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Consignacion",
            cuerpo,
            message_id="dup-1",
        )
        self.assertEqual(m1["nuevos"], 1)
        # Segundo con el mismo message_id debe ser ignorado
        m2 = procesar_correo_simulado(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Consignacion",
            cuerpo,
            message_id="dup-1",
        )
        self.assertEqual(m2["nuevos"], 0)
        self.assertEqual(m2["ignorados"], 1)
        # Solo debe haber un movimiento
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_reprocesa_correo_despues_de_borrar_movimiento(self):
        # Repro: borrar un Movimiento no debe dejar el EmailProcesado
        # bloqueando la proxima sincronizacion.
        cuerpo = (
            "Bancolombia: Recibiste una consignacion por 1.000.000 "
            "de TEST USER en tu cuenta **0736 el 26/08/2026 12:00."
        )
        procesar_correo_simulado(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Consignacion",
            cuerpo,
            message_id="dup-del-1",
        )
        self.assertEqual(Movimiento.objects.count(), 1)
        Movimiento.objects.all().delete()
        self.assertEqual(Movimiento.objects.count(), 0)
        m2 = procesar_correo_simulado(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Consignacion",
            cuerpo,
            message_id="dup-del-1",
        )
        self.assertEqual(m2["nuevos"], 1)
        self.assertEqual(m2["ignorados"], 0)
        self.assertEqual(Movimiento.objects.count(), 1)
        self.assertEqual(EmailProcesado.objects.filter(message_id="dup-del-1").count(), 1)


class EndpointDebugTests(TestCase):
    """Tests del endpoint /gmail/debug/."""

    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="admin", password="x", rol="ADMINISTRADOR"
        )
        self.normal = get_user_model().objects.create_user(
            username="user", password="x", rol="USUARIO"
        )
        self.config = ConfiguracionGmail.objects.create(conectado=True)

    def test_debug_no_acceso_sin_login(self):
        resp = self.client.get("/gmail/debug/")
        self.assertEqual(resp.status_code, 302)  # redirect to login

    def test_debug_acceso_denegado_a_usuario_normal(self):
        self.client.force_login(self.normal)
        resp = self.client.get("/gmail/debug/")
        self.assertEqual(resp.status_code, 403)

    def test_debug_acceso_para_admin(self):
        self.client.force_login(self.admin)
        resp = self.client.get("/gmail/debug/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ultimos", data)
        self.assertIn("total_correos", data)
        self.assertIn("ultima_sincronizacion", data)


class ParserRealBancolombiaTests(TestCase):
    """Tests con fragmentos reales de correos de Bancolombia."""

    def setUp(self):
        from core.models import ConfiguracionSistema
        ConfiguracionSistema.objects.create()

    def test_pagaste_aportes_en_linea(self):
        # Correo real del 26/08/2026
        cuerpo = (
            "Listo! Todo salio bien con tus movimientos "
            "Bancolombia: Pagaste $512.100,00 a APORTES EN LINEA "
            "desde tu producto 0736 el 26/08/2026 08:32:17."
        )
        resultado = parsear(
            "alertasynotificaciones@ayn.notificacionesbancolombia.com",
            "Alertas y Notificaciones",
            cuerpo,
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "EGRESO")
        self.assertEqual(resultado.valor, Decimal("512100.00"))
        self.assertEqual(resultado.cuenta, "0736")
        self.assertIsNotNone(resultado.hora)
        self.assertEqual(resultado.hora.hour, 8)
        self.assertEqual(resultado.hora.minute, 32)

    def test_transferiste_por_qr(self):
        cuerpo = (
            "Bancolombia: Transferiste $8.100,00 por QR "
            "desde tu cuenta 0736 a la cuenta 8615, el 2026/06/29 19:19."
        )
        resultado = parsear(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Alertas y Notificaciones",
            cuerpo,
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "EGRESO")
        # El valor "$8.100,00" = 8 mil 100 pesos colombianos
        self.assertEqual(resultado.valor, Decimal("8100.00"))
