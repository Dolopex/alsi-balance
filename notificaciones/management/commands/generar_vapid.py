"""Genera un par de claves VAPID para Web Push.

Las claves se imprimen en pantalla. Copialas a tu .env:

    VAPID_PUBLIC_KEY=...
    VAPID_PRIVATE_KEY=...
"""

import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Genera un par de claves VAPID para Web Push."

    def handle(self, *args, **options):
        try:
            from py_vapid import Vapid
            from cryptography.hazmat.primitives import serialization
            import base64
        except ImportError:
            self.stderr.write(
                "Faltan dependencias. Ejecuta: pip install pywebpush py-vapid"
            )
            sys.exit(1)

        v = Vapid()
        v.generate_keys()

        # Public key: extraer raw uncompressed + base64 url-safe (lo que requiere Web Push)
        raw = v.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        public_b64 = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

        # Private key: PEM
        private_pem = v.private_pem()
        if isinstance(private_pem, bytes):
            private_pem = private_pem.decode("utf-8")

        self.stdout.write(self.style.SUCCESS(
            "\nAgrega estas 3 lineas a tu archivo .env:\n"
        ))
        self.stdout.write(f"VAPID_PUBLIC_KEY={public_b64}")
        self.stdout.write(f"VAPID_PRIVATE_KEY={private_pem.strip()}")
        self.stdout.write(f"VAPID_CLAIMS_SUB=mailto:admin@alsi.local\n")
        self.stdout.write(self.style.SUCCESS(
            "Listo. Reinicia el servidor y las notificaciones push estaran activas.\n"
        ))
