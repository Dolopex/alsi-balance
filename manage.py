#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


# Habilitar OAuth sobre HTTP solo en desarrollo local (antes de importar Django).
# Google exige HTTPS para el callback de OAuth en produccion; permitimos HTTP
# solo cuando DJANGO_DEBUG=True para no romper el flujo local.
load_dotenv(Path(__file__).resolve().parent / ".env")
_debug = os.environ.get("DJANGO_DEBUG", "False").strip().lower() in {"1", "true", "yes", "on"}
if _debug:
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
