"""Configuración base del backend (compartida por desarrollo y producción).

Todo lo que cambia entre equipos o servidores sale de ``backend/.env`` (ver ``.env.example``); aquí
solo quedan valores por defecto razonables. El backend es solo API (``/api/``) + ``/admin/``: la
interfaz vive en ``frontend/`` (React).
"""
from datetime import timedelta

from config.env import BASE_DIR, env_bool, env_int, env_list, env_str, load_env

load_env()

# --- Proyecto ------------------------------------------------------------------
# Nombre visible (API, admin, correos) y código corto (prefijo de cookies, emisor de los JWT).
PROJECT_NAME = env_str("PROJECT_NAME", "Workspace")
PROJECT_CODE = env_str("PROJECT_CODE", "ws").lower()

SECRET_KEY = env_str("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
# Origen del frontend (React). Sirve para armar enlaces y, si está en otro dominio, para CORS/CSRF.
FRONTEND_URL = env_str("FRONTEND_URL", "http://localhost:5173").rstrip("/")
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True   # la cookie del refresh token viaja con las peticiones a /api/auth/
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",   # refresh tokens revocados (logout y rotación)
    "django_extensions",   # runscript, shell_plus, show_urls…
    "allauth",             # «Continuar con Google» (reglas en apps/accounts/adapters.py; pantalla en otra tanda)
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # Proyecto
    "apps.accounts",
    "apps.catalogs",
    "apps.social",
    "apps.notifications",
    "apps.blog",
    "apps.documents",
    "apps.form_builder",
    "apps.marketplace",
    "apps.helpdesk",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# Plantillas: solo correos (backend/templates/emails/) y las de terceros (admin, DRF).
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
DB_ENGINE = env_str("DB_ENGINE", "django.db.backends.sqlite3")
if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": BASE_DIR / env_str("DB_NAME", "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": env_str("DB_NAME"),
            "USER": env_str("DB_USER"),
            "PASSWORD": env_str("DB_PASSWORD"),
            "HOST": env_str("DB_HOST"),
            "PORT": env_str("DB_PORT"),
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Autenticación -----------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    # Usuario o correo + contraseña (incluye todo lo de ModelBackend: permisos, cuentas activas).
    "apps.accounts.backends.UsernameOrEmailBackend",
]
# El login lo hace React (/login); /admin/ conserva su propio formulario.
LOGIN_URL = "admin:login"
SESSION_COOKIE_NAME = f"{PROJECT_CODE}_sessionid"
CSRF_COOKIE_NAME = f"{PROJECT_CODE}_csrftoken"

# --- Inicio de sesión con Google (django-allauth) -----------------------------
# Solo cuentas del Google Workspace de la empresa. Las credenciales se crean en Google Cloud
# (ID de cliente OAuth, aplicación web, pantalla de consentimiento «Interna») y van en .env.
# La pantalla en React y el canje por JWT llegan en otra tanda; las reglas de dominio ya están.
GOOGLE_ALLOWED_DOMAIN = env_str("GOOGLE_ALLOWED_DOMAIN", "orienta.soy")
GOOGLE_CLIENT_ID = env_str("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = env_str("GOOGLE_CLIENT_SECRET")
GOOGLE_LOGIN_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

# Notificaciones push (PWA). Llave pública VAPID (base64url) que usa el navegador para suscribirse.
# Vacía: /api/notifications/push/config/ responde enabled=false. La privada se agregará al implementar el envío.
WEBPUSH_VAPID_PUBLIC_KEY = env_str("WEBPUSH_VAPID_PUBLIC_KEY")

ACCOUNT_ADAPTER = "apps.accounts.adapters.AccountAdapter"            # sin registro con contraseña
SOCIALACCOUNT_ADAPTER = "apps.accounts.adapters.SocialAccountAdapter" # solo @GOOGLE_ALLOWED_DOMAIN
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*"]
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none"         # el correo ya lo verifica Google
SOCIALACCOUNT_AUTO_SIGNUP = True            # primera vez con Google = cuenta creada
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True   # mismo correo que una cuenta existente → entra a esa cuenta…
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True   # …y queda vinculada
SOCIALACCOUNT_LOGIN_ON_GET = False
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
LANGUAGE_CODE = env_str("DJANGO_LANGUAGE_CODE", "es")
# Zona del servidor (admin, correos, reportes): la sede está en Querétaro. La API manda las fechas
# en ISO 8601 con desfase (p. ej. 2026-10-25T09:00:00-06:00) y el navegador las muestra en la
# zona de quien las ve: en Tijuana, Querétaro o donde sea, la hora sale correcta.
TIME_ZONE = env_str("DJANGO_TIME_ZONE", "America/Mexico_City")
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos y de usuario -----------------------------------------
# static/ solo guarda datos del backend (emojis del catálogo) y lo que necesitan admin y DRF.
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Django REST Framework (única raíz: /api/, sin versionado) --------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # React manda «Authorization: Bearer <access>». La sesión queda para quien ya entró al /admin/.
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.SafePageNumberPagination",
    "EXCEPTION_HANDLER": "apps.core.pagination.api_exception_handler",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    # Límite de intentos de login por IP (protege contra adivinar contraseñas).
    "DEFAULT_THROTTLE_RATES": {"auth": env_str("AUTH_THROTTLE_RATE", "10/min")},
}

# --- JWT (djangorestframework-simplejwt) ----------------------------------------
# Access corto: viaja en cada petición y React lo guarda solo en memoria. Refresh largo: va en una
# cookie httpOnly (JavaScript no la puede leer) limitada a /api/auth/, se usa una sola vez (rotación)
# y al cerrar sesión queda en la lista negra. Detalle en docs/backend/autenticacion.md.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_MINUTES", 60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_DAYS", 7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ISSUER": PROJECT_CODE,
    "SIGNING_KEY": env_str("JWT_SIGNING_KEY") or SECRET_KEY,
}
JWT_REFRESH_COOKIE = {
    "key": f"{PROJECT_CODE}_refresh",
    "path": "/api/auth/",
    "httponly": True,
    "secure": env_bool("JWT_COOKIE_SECURE", False),
    "samesite": env_str("JWT_COOKIE_SAMESITE", "Strict"),
}

# --- Correo (apps/core/mail.py) — PREPARADO, la cuenta no-reply@ aún no existe ---
# Remitente fijo «PROJECT_NAME <no-reply@dominio>»: nadie responde a esa dirección. Todo sale del .env.
# Mientras no haya servidor SMTP, los correos se imprimen en la consola del servidor (no se pierden ni
# truenan). Para enviar de verdad: EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend + EMAIL_HOST…
# (en producción basta con definir EMAIL_HOST). Probar la conexión: python manage.py sendtestemail tu@correo
EMAIL_BACKEND = env_str("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env_str("EMAIL_HOST")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)      # puerto 587 (STARTTLS)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)     # puerto 465; nunca junto con TLS
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL") or f"{PROJECT_NAME} <no-reply@{GOOGLE_ALLOWED_DOMAIN}>"
SERVER_EMAIL = env_str("SERVER_EMAIL") or DEFAULT_FROM_EMAIL        # remitente de los errores del servidor
EMAIL_SUBJECT_PREFIX = f"[{PROJECT_NAME}] "                          # solo para correos a administradores
# Dirección pública del sitio (el frontend) para armar enlaces completos dentro de los correos.
SITE_URL = env_str("SITE_URL").rstrip("/") or FRONTEND_URL
