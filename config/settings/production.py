"""Ajustes de producción (borrador: NO verificado como listo para producción)."""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import EMAIL_HOST, SECRET_KEY, env_bool, env_list

DEBUG = False

if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY es obligatoria en producción.")

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
CSRF_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", True)
SECURE_CONTENT_TYPE_NOSNIFF = True

# Correo: SMTP en cuanto exista la cuenta no-reply@ (EMAIL_HOST en .env); mientras tanto, a la consola/log.
if not os.getenv("EMAIL_BACKEND"):
    EMAIL_BACKEND = (
        "django.core.mail.backends.smtp.EmailBackend" if EMAIL_HOST else "django.core.mail.backends.console.EmailBackend"
    )

# CSS/JS con hash en el nombre (collectstatic): se pueden cachear mucho tiempo y nunca quedan viejos.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}
