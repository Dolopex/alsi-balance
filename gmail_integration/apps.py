import logging
import os

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class GmailIntegrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gmail_integration"
    verbose_name = "Integracion Gmail"

    def ready(self):
        # Auto-sync DESACTIVADO por default en este proyecto.
        # Solo se activa si la variable GMAIL_AUTO_SYNC=1 esta seteada.
        # En deploy serverless (Vercel) NO debe estar activado.
        flag = os.environ.get("GMAIL_AUTO_SYNC", "").strip().lower()
        if flag not in ("1", "true", "yes", "on"):
            logger.info("ALSI Gmail: auto-sync desactivado (manual via UI).")
            return

        # Solo corre en contextos long-running (runserver local, no serverless)
        import sys
        if len(sys.argv) <= 1 or sys.argv[1] not in ("runserver", "runserver_plus"):
            logger.info("ALSI Gmail: auto-sync omitido (no es runserver).")
            return

        import threading
        import time

        try:
            intervalo = int(os.environ.get("GMAIL_AUTO_SYNC_INTERVAL", "60"))
        except ValueError:
            intervalo = 60
        if intervalo < 30:
            intervalo = 30

        def _loop():
            from django.core import management
            while True:
                try:
                    management.call_command("sincronizar_gmail", verbosity=1)
                except Exception as exc:
                    logger.warning("ALSI Gmail: auto-sync error: %s", exc)
                time.sleep(intervalo)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        logger.info("ALSI Gmail: thread de sincronizacion iniciado (cada %ss)", intervalo)
