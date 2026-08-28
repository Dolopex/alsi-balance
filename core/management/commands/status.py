"""Verifica el estado del sistema: DB, Gmail, conteos."""

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Verifica el estado del sistema y muestra estadisticas."

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("=== ESTADO DEL SISTEMA ALSI BALANCE ===\n"))

        # DB
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS("[OK] Base de datos conectada"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"[ERROR] DB: {exc}"))

        # Conteos
        from django.contrib.auth import get_user_model
        from movimientos.models import Movimiento, Comprobante
        from categorias.models import Categoria
        from core.models import ConfiguracionSistema
        from gmail_integration.models import EmailProcesado, ConfiguracionGmail

        U = get_user_model()
        users = U.objects.count()
        admins = U.objects.filter(rol="ADMINISTRADOR").count()
        self.stdout.write(f"\nUsuarios: {users} ({admins} administradores)")

        movs = Movimiento.objects.count()
        ingresos = Movimiento.objects.filter(tipo="INGRESO").count()
        egresos = Movimiento.objects.filter(tipo="EGRESO").count()
        self.stdout.write(f"Movimientos: {movs} ({ingresos} ingresos, {egresos} egresos)")

        cats = Categoria.objects.count()
        cats_activas = Categoria.objects.filter(activo=True).count()
        self.stdout.write(f"Categorias: {cats} ({cats_activas} activas)")

        config = ConfiguracionSistema.objects.first()
        if config:
            self.stdout.write(f"Saldo inicial: ${config.saldo_inicial:,.2f} ({config.banco})")

        # Gmail
        gmail = ConfiguracionGmail.objects.first()
        if gmail and gmail.conectado:
            self.stdout.write(self.style.SUCCESS(f"\n[OK] Gmail conectado: {gmail.email_cuenta}"))
            if gmail.ultima_sincronizacion:
                self.stdout.write(f"  Ultima sync: {gmail.ultima_sincronizacion.strftime('%Y-%m-%d %H:%M')}")
        else:
            self.stdout.write(self.style.WARNING("\n[Gmail no conectado]"))

        correos = EmailProcesado.objects.count()
        correos_exitosos = EmailProcesado.objects.filter(estado="EXITOSO").count()
        correos_ignorados = EmailProcesado.objects.filter(estado="IGNORADO").count()
        correos_errores = EmailProcesado.objects.filter(estado="ERROR").count()
        self.stdout.write(
            f"Correos procesados: {correos} ({correos_exitosos} exitosos, "
            f"{correos_ignorados} ignorados, {correos_errores} errores)"
        )

        # Pendientes de conciliacion
        pendientes = Movimiento.objects.filter(estado_conciliacion="PENDIENTE").count()
        if pendientes:
            self.stdout.write(self.style.WARNING(
                f"\nMovimientos pendientes de conciliacion: {pendientes}"
            ))

        self.stdout.write("")
