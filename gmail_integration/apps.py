import logging
import os
import sys
import threading
import time

from django.apps import AppConfig


logger = logging.getLogger(__name__)


def _es_comando_a_evitar() -> bool:
    """Comandos donde NO debe arrancar el auto-sync (tests, migrate, shell, etc)."""
    if len(sys.argv) <= 1:
        return True
    comando = sys.argv[1]
    evitar = {"test", "migrate", "makemigrations", "collectstatic",
              "shell", "dbshell", "createsuperuser", "check",
              "createsuperuser", "showmigrations", "loaddata",
              "dumpdata", "changepassword", "help"}
    return comando in evitar or comando.startswith("-")


def _loop_autosync(intervalo: int):
    """Loop en background que sincroniza Gmail periodicamente."""
    from django.core import management

    logger.info("ALSI Gmail: auto-sync cada %ss", intervalo)
    while True:
        try:
            management.call_command("sincronizar_gmail", verbosity=1)
        except Exception as exc:
            logger.warning("ALSI Gmail: auto-sync error: %s", exc)
        time.sleep(intervalo)


class GmailIntegrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gmail_integration"
    verbose_name = "Integracion Gmail"

    def ready(self):
        flag = os.environ.get("GMAIL_AUTO_SYNC", "").strip().lower()
        if flag not in ("1", "true", "yes", "on"):
            return
        if _es_comando_a_evitar():
            return
        try:
            intervalo = int(os.environ.get("GMAIL_AUTO_SYNC_INTERVAL", "60"))
        except ValueError:
            intervalo = 60
        if intervalo < 30:
            intervalo = 30
        t = threading.Thread(target=_loop_autosync, args=(intervalo,), daemon=True)
        t.start()
        logger.info("ALSI Gmail: thread de sincronizacion iniciado (cada %ss)", intervalo)
