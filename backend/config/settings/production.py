"""Ajustes de producción (DJANGO_ENV=production). Borrador: NO verificado como listo para producción."""
from django.core.exceptions import ImproperlyConfigured

from config.env import env_bool, env_str

from .base import *  # noqa: F401,F403
from .base import EMAIL_HOST, SECRET_KEY

DEBUG = False

if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY es obligatoria en producción.")

SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
CSRF_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", True)
SECURE_CONTENT_TYPE_NOSNIFF = True
JWT_REFRESH_COOKIE = {**JWT_REFRESH_COOKIE, "secure": env_bool("JWT_COOKIE_SECURE", True)}  # noqa: F405

# Correo: SMTP en cuanto exista la cuenta no-reply@ (EMAIL_HOST en .env); mientras tanto, a la consola/log.
if not env_str("EMAIL_BACKEND"):
    EMAIL_BACKEND = (
        "django.core.mail.backends.smtp.EmailBackend" if EMAIL_HOST else "django.core.mail.backends.console.EmailBackend"
    )

# Estáticos del backend (admin, DRF, emojis) con hash en el nombre: se cachean mucho tiempo sin quedar viejos.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}
