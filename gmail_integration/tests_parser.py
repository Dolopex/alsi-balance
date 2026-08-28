"""Tests del parser de correos Bancolombia."""

from datetime import datetime
from decimal import Decimal

from django.test import SimpleTestCase

from gmail_integration.parser import (
    MovimientoParseado,
    es_correo_bancolombia,
    parsear,
)


class BancolombiaParserTests(SimpleTestCase):
    def test_detecta_correo_bancolombia_por_remitente(self):
        self.assertTrue(es_correo_bancolombia("alertas@bancolombia.com.co", "Aviso"))
        self.assertTrue(es_correo_bancolombia("notificaciones@Bancolombia.com", ""))
        self.assertTrue(es_correo_bancolombia(
            "alertasynotificaciones@an.notificacionesbancolombia.com", "Movimiento"
        ))
        # Remitente que no es Bancolombia NO debe detectarse
        self.assertFalse(es_correo_bancolombia("otro@gmail.com", "Asunto random"))

    def test_detecta_dominio_notificacionesbancolombia(self):
        self.assertTrue(es_correo_bancolombia(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Notificacion de movimiento",
        ))

    def test_detecta_correo_bancolombia_por_asunto(self):
        self.assertTrue(es_correo_bancolombia(
            "noreply@otro.com",
            "Bancolombia - Transferencia recibida",
        ))

    def test_no_detecta_correo_no_bancolombia(self):
        self.assertFalse(es_correo_bancolombia("amigo@gmail.com", "Hola"))
        self.assertFalse(parsear("amigo@gmail.com", "Saludos", "Cuerpo normal"))

    def test_parsea_ingreso_consignacion(self):
        correo = """
        Bancolombia - Transferencia recibida

        Fecha: 23/08/2026
        Valor: $1.500.000,00
        Concepto: Consignacion
        Referencia: REF123456

        Le informamos que recibio una transferencia.
        """
        resultado = parsear("alertas@bancolombia.com.co", "Transferencia recibida", correo)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "INGRESO")
        self.assertEqual(resultado.valor, Decimal("1500000.00"))
        self.assertEqual(resultado.referencia, "REF123456")

    def test_parsea_egreso_transferencia(self):
        correo = """
        Bancolombia informa

        Se realizo una transferencia enviada por $500.000,00
        Fecha: 22/08/2026
        Concepto: Pago de nomina
        A: Juan Perez
        Referencia: TRX987654
        """
        resultado = parsear("notificaciones@bancolombia.com", "Pago realizado", correo)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "EGRESO")
        self.assertEqual(resultado.valor, Decimal("500000.00"))
        self.assertIn("nomina", resultado.concepto.lower())

    def test_parsea_compra(self):
        correo = """
        Bancolombia - Compra realizada

        Valor: $75.500
        Fecha: 21/08/2026
        Concepto: Compra en establecimiento
        """
        resultado = parsear("alertas@bancolombia.com.co", "Compra con tarjeta", correo)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "EGRESO")
        self.assertEqual(resultado.valor, Decimal("75500.00"))

    def test_parsea_con_dominio_notificacionesbancolombia(self):
        correo = """
        Notificacion de Bancolombia

        Se realizo una transferencia recibida por $250.000,00
        Fecha: 23/08/2026
        Cuenta: *1234
        Referencia: ABC123
        Concepto: Pago cliente
        """
        resultado = parsear(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Bancolombia - Movimiento en cuenta",
            correo,
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "INGRESO")
        self.assertEqual(resultado.valor, Decimal("250000.00"))

    def test_pagaste_con_valor_pesos_colombianos(self):
        correo = """
        Bancolombia: Pagaste 5.000,00 a APORTES EN LINEA
        desde tu cuenta 0736 el 26/08/2026 a las 18:00.
        """
        resultado = parsear(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Pago realizado",
            correo,
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "EGRESO")
        # 5.000,00 pesos colombianos = 5 mil
        self.assertEqual(resultado.valor, Decimal("5000.00"))

    def test_pagaste_cinco_millones(self):
        correo = """
        Bancolombia: Pagaste 5.000.000 desde tu cuenta
        0736 a la cuenta *1234567 el 26/08/2026 14:00.
        """
        resultado = parsear(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Pago realizado",
            correo,
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "EGRESO")
        # 5.000.000 = 5 millones
        self.assertEqual(resultado.valor, Decimal("5000000.00"))

    def test_compra_formato_us(self):
        # Formato US: coma decimal con 2 digitos
        correo = """
        Bancolombia: Compra por 75,50 en ESTABLECIMIENTO XYZ
        el 26/08/2026 12:00.
        """
        resultado = parsear(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Compra realizada",
            correo,
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "EGRESO")
        self.assertEqual(resultado.valor, Decimal("75.50"))

    def test_recibiste_consignacion(self):
        correo = """
        Bancolombia: Recibiste una consignacion por 5.000.000
        de CARLOS PEREZ en tu cuenta **0736 el 26/08/2026 16:00.
        """
        resultado = parsear(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Consignacion recibida",
            correo,
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "INGRESO")
        self.assertEqual(resultado.valor, Decimal("5000000.00"))
        self.assertEqual(resultado.tercero, "CARLOS PEREZ")
        self.assertEqual(resultado.cuenta, "**0736")

    def test_monto_millon_con_punto_y_decimal(self):
        # $1.500.000,00 = 1 millon 500 mil con centavos
        correo = """
        Bancolombia: Transferiste $1.500.000,00 desde tu cuenta
        0736 a la cuenta *987654321 el 26/08/2026 10:00.
        """
        resultado = parsear(
            "alertasynotificaciones@an.notificacionesbancolombia.com",
            "Transferencia",
            correo,
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "EGRESO")
        self.assertEqual(resultado.valor, Decimal("1500000.00"))
        self.assertEqual(resultado.cuenta_destino, "*987654321")

    def test_devuelve_none_sin_tipo_detectable(self):
        correo = """
        Bancolombia informa que su cuenta esta activa.
        """
        self.assertIsNone(parsear("alertas@bancolombia.com.co", "Bienvenida", correo))

    def test_maneja_valor_sin_separadores(self):
        correo = """
        Banco: Bancolombia
        Se realizo un pago por $2500.
        Fecha: 20/08/2026
        Concepto: Compra menor
        """
        resultado = parsear("alertas@bancolombia.com.co", "Pago realizado", correo)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.tipo, "EGRESO")
        self.assertEqual(resultado.valor, Decimal("2500.00"))
