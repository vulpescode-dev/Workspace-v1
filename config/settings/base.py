"""Configuración base de Workspace (compartida por desarrollo y producción)."""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "django_extensions",   # runscript, shell_plus, show_urls…
    "allauth",             # «Continuar con Google» (ver apps/accounts/adapters.py)
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # Workspace
    "apps.accounts",
    "apps.catalogs",
    "apps.social",
    "apps.notifications",
    "apps.blog",
    "apps.documents",
    "apps.form_builder",
    "apps.marketplace",
    "apps.org",
    "apps.helpdesk",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de datos -----------------------------------------------------------
# Etapa inicial: SQLite. Las variables permiten elegir otro motor más adelante,
# pero cambiar de motor exige validar tipos, restricciones, índices y migraciones.
DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.sqlite3")
if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": BASE_DIR / os.getenv("DB_NAME", "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.getenv("DB_NAME", ""),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", ""),
            "PORT": os.getenv("DB_PORT", ""),
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Autenticación -----------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    # Usuario o correo + contraseña (incluye todo lo de ModelBackend: permisos, cuentas activas).
    "apps.accounts.backends.UsernameOrEmailBackend",
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# --- Inicio de sesión con Google (django-allauth) -----------------------------
# Solo cuentas del Google Workspace de la empresa. Las credenciales se crean en Google Cloud
# (ID de cliente OAuth, aplicación web, pantalla de consentimiento «Interna») y van en .env.
# Sin ellas el botón aparece deshabilitado en desarrollo y oculto en producción.
GOOGLE_ALLOWED_DOMAIN = os.getenv("GOOGLE_ALLOWED_DOMAIN", "orienta.soy")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Notificaciones push (PWA). Llave pública VAPID (base64url) que usa el navegador para suscribirse.
# Vacía: /api/notifications/push/config/ responde enabled=false. La privada se agregará al implementar el envío.
WEBPUSH_VAPID_PUBLIC_KEY = os.getenv("WEBPUSH_VAPID_PUBLIC_KEY", "")
GOOGLE_LOGIN_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

ACCOUNT_ADAPTER = "apps.accounts.adapters.AccountAdapter"            # sin registro con contraseña
SOCIALACCOUNT_ADAPTER = "apps.accounts.adapters.SocialAccountAdapter" # solo @GOOGLE_ALLOWED_DOMAIN
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*"]
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none"         # el correo ya lo verifica Google
SOCIALACCOUNT_AUTO_SIGNUP = True            # primera vez con Google = cuenta creada
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True   # mismo correo que una cuenta existente → entra a esa cuenta…
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True   # …y queda vinculada
SOCIALACCOUNT_LOGIN_ON_GET = False          # el botón envía un POST con CSRF (sin pantalla intermedia)
SOCIALACCOUNT_STORE_TOKENS = False          # solo identidad; no se guardan tokens de Google
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [{"client_id": GOOGLE_CLIENT_ID, "secret": GOOGLE_CLIENT_SECRET, "key": ""}] if GOOGLE_LOGIN_ENABLED else [],
        "SCOPE": ["profile", "email"],
        # hd: Google solo ofrece cuentas de ese dominio (la validación real está en el adaptador).
        "AUTH_PARAMS": {"hd": GOOGLE_ALLOWED_DOMAIN, "prompt": "select_account"},
        "EMAIL_AUTHENTICATION": True,
    },
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalización ----------------------------------------------------
LANGUAGE_CODE = "es"
# Zona del servidor (admin, correos, reportes): la sede está en Querétaro. La API manda las fechas
# en ISO 8601 con desfase (p. ej. 2026-10-25T09:00:00-06:00) y el navegador las muestra en la
# zona de quien las ve: en Tijuana, Querétaro o donde sea, la hora sale correcta.
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "America/Mexico_City")
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos y de usuario -----------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Django REST Framework (única raíz: /api/, sin versionado) --------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.SafePageNumberPagination",
    "EXCEPTION_HANDLER": "apps.core.pagination.api_exception_handler",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# --- Correo (apps/core/mail.py) — PREPARADO, la cuenta no-reply@ aún no existe ---
# Remitente fijo «Workspace <no-reply@dominio>»: nadie responde a esa dirección. Todo sale del .env.
# Mientras no haya servidor SMTP, los correos se imprimen en la consola del servidor (no se pierden ni
# truenan). Para enviar de verdad: EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend + EMAIL_HOST…
# (en producción basta con definir EMAIL_HOST). Probar la conexión: python manage.py sendtestemail tu@correo
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)      # puerto 587 (STARTTLS)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)     # puerto 465; nunca junto con TLS
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", f"Workspace <no-reply@{GOOGLE_ALLOWED_DOMAIN}>")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)        # remitente de los errores del servidor
EMAIL_SUBJECT_PREFIX = "[Workspace] "                                # solo para correos a administradores
# Dirección pública del sitio para armar enlaces completos dentro de los correos (sin «/» al final).
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000").rstrip("/")

# --- JWT (djangorestframework-simplejwt) — INSTALADO, AÚN NO SE USA -----------
# La API funciona solo con sesión. Esto deja lista la configuración para cuando llegue un frontend
# aparte (React, app móvil…). Para activarlo:
#   1. INSTALLED_APPS += "rest_framework_simplejwt.token_blacklist" y ``migrate`` (revocar refresh).
#   2. DEFAULT_AUTHENTICATION_CLASSES += "rest_framework_simplejwt.authentication.JWTAuthentication".
#   3. Rutas de token (TokenObtainPairView, TokenRefreshView, TokenBlacklistView) en apps/accounts/api.
# Access corto (va en cada petición) y refresh más largo (solo sirve para pedir otro access); cada
# refresh se usa una vez. Firma con DJANGO_SECRET_KEY, o con JWT_SIGNING_KEY si se define.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
if os.getenv("JWT_SIGNING_KEY"):
    SIMPLE_JWT["SIGNING_KEY"] = os.getenv("JWT_SIGNING_KEY")
