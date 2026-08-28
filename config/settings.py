"""
Configuracion principal del proyecto ALSI BALANCE.

Lee las variables desde el archivo .env mediante python-dotenv.
La arquitectura esta preparada para usar PostgreSQL en produccion
y SQLite para desarrollo local.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.environ.get(name)
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", default=True)

# En Vercel las env vars no definidas vienen como "" (string vacio),
# no como None. Por eso usamos `or "default"` para todos los env vars
# que tengan un valor por defecto.
SECRET_KEY = (
    os.environ.get("DJANGO_SECRET_KEY")
    or "dev-insecure-key-change-me-in-production-alsi-balance"
)

if not DEBUG and SECRET_KEY.startswith("dev-insecure"):
    import warnings

    warnings.warn(
        "DJANGO_SECRET_KEY no configurada. Usando clave insecure de desarrollo. "
        "Configura DJANGO_SECRET_KEY antes de ir a produccion.",
        RuntimeWarning,
    )

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    default=[
        "127.0.0.1", "localhost", "testserver",
        ".vercel.app", ".fly.dev", ".up.railway.app", ".railway.app",
    ],
)

if DEBUG:
    ALLOWED_HOSTS = list(set(ALLOWED_HOSTS + ["127.0.0.1", "localhost", "testserver", "0.0.0.0"]))

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    default=["http://127.0.0.1:8000", "http://localhost:8000"],
)
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = list(set(
        CSRF_TRUSTED_ORIGINS + [
            "https://*.vercel.app",
            "https://*.fly.dev",
            "https://*.up.railway.app",
            "https://*.railway.app",
        ]
    ))

APP_NAME = os.environ.get("APP_NAME", "ALSI BALANCE")
APP_SHORT_NAME = os.environ.get("APP_SHORT_NAME", "ALSI")
APP_COMPANY = os.environ.get(
    "APP_COMPANY", "Agropesquera La Sinuana S.A.S."
)

# ===== Gmail OAuth =====
GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_REDIRECT_URI = os.environ.get(
    "GOOGLE_OAUTH_REDIRECT_URI",
    "http://127.0.0.1:8000/gmail/callback/",
)
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# ===== Web Push (notificaciones moviles) =====
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {
    "sub": os.environ.get("VAPID_CLAIMS_SUB", "mailto:admin@alsi.local"),
}

# Sincronizacion automatica de Gmail
# En Vercel/serverless las env vars no definidas vienen como ""
# (string vacio), no como ausencia. Por eso usamos `or "default"`.
GMAIL_AUTO_SYNC = (os.environ.get("GMAIL_AUTO_SYNC") or "0") == "1"
try:
    _intervalo = int(os.environ.get("GMAIL_AUTO_SYNC_INTERVAL") or "60")
except ValueError:
    _intervalo = 60
GMAIL_AUTO_SYNC_INTERVAL = _intervalo

# Gmail Watch (Pub/Sub) para notificacion en tiempo real
GMAIL_PUBSUB_TOPIC = os.environ.get("GMAIL_PUBSUB_TOPIC", "")
GMAIL_WATCH_TOKEN = os.environ.get("GMAIL_WATCH_TOKEN", "alsi-balance-watch-token")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Apps locales
    "core",
    "usuarios",
    "categorias",
    "movimientos",
    "dashboard",
    "auditoria",
    "conciliacion",
    "reportes",
    "gmail_integration",
    "notificaciones",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.app_brand",
                "core.context_processors.gmail_status",
                "core.context_processors.push_config",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ----- Base de datos -----
# Si se define DATABASE_URL apuntando a postgres, se usa psycopg2.
# En caso contrario se usa SQLite (ideal para desarrollo local).
# Usamos `or` para que Vercel (donde env vars no definidas vienen como "")
# tambien use el default de SQLite en dev.
DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///db.sqlite3"

if DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"):
    from urllib.parse import urlparse
    url = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": url.path.lstrip("/"),
            "USER": url.username or "",
            "PASSWORD": url.password or "",
            "HOST": url.hostname or "",
            "PORT": url.port or "",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_USER_MODEL = "usuarios.Usuario"


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "usuarios:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "usuarios:login"

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Mensajes
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: "bg-gray-100 text-gray-800 border-gray-300",
    message_constants.INFO: "bg-blue-50 text-blue-800 border-blue-300",
    message_constants.SUCCESS: "bg-green-50 text-green-800 border-green-300",
    message_constants.WARNING: "bg-yellow-50 text-yellow-800 border-yellow-300",
    message_constants.ERROR: "bg-red-50 text-red-800 border-red-300",
}
