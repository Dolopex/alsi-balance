"""Configura Gmail Watch + Pub/Sub para recibir notificaciones en tiempo real.

Google Cloud setup necesario:
  1. Crear proyecto en https://console.cloud.google.com/
  2. Habilitar Gmail API + Pub/Sub API
  3. Crear un topic Pub/Sub
  4. Crear una suscripcion tipo PUSH al topic, con URL = https://TU_DOMINIO/gmail/webhook/
  5. Setear GMAIL_PUBSUB_TOPIC=projects/TU_PROYECTO/topics/TU_TOPIC en .env

Uso:
    python manage.py setup_gmail_watch
"""

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Registra Gmail Watch para recibir notificaciones en tiempo real."

    def handle(self, *args, **options):
        topic = getattr(settings, "GMAIL_PUBSUB_TOPIC", "")
        if not topic:
            self.stderr.write(self.style.ERROR(
                "Falta GMAIL_PUBSUB_TOPIC en .env. Ejemplo: "
                "projects/my-project/topics/gmail-notifications"
            ))
            return

        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from gmail_integration.services import _credentials_desde_config
        except ImportError as exc:
            self.stderr.write(self.style.ERROR(f"Faltan dependencias: {exc}"))
            return

        from gmail_integration.models import ConfiguracionGmail
        config = ConfiguracionGmail.objects.first()
        if not config or not config.conectado:
            self.stderr.write(self.style.ERROR("Gmail no esta conectado"))
            return

        creds = _credentials_desde_config(config)
        if not creds:
            self.stderr.write(self.style.ERROR("Sin credenciales validas"))
            return

        service = build("gmail", "v1", credentials=creds, cache_discovery=False)

        try:
            request_body = {
                "topicName": topic,
                "labelIds": ["INBOX"],
            }
            result = service.users().watch(userId="me", body=request_body).execute()
            self.stdout.write(self.style.SUCCESS(
                f"Gmail Watch registrado. historyId={result.get('historyId')} "
                f"expiration={result.get('expiration')}"
            ))
            self.stdout.write("A partir de ahora Google enviara push a /gmail/webhook/ cuando llegue un correo nuevo.")
            self.stdout.write("El watch expira en ~7 dias. Volve a correr este comando para renovarlo.")
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Error registrando watch: {exc}"))