"""Ajustes de desarrollo local."""
from .base import *  # noqa: F401,F403
from .base import SECRET_KEY as _SECRET_KEY

DEBUG = True
SECRET_KEY = _SECRET_KEY or "inseguro-solo-para-desarrollo-local"
# Los hosts salen de DJANGO_ALLOWED_HOSTS (.env, p. ej. la IP de tu PC para entrar desde el teléfono);
# aquí solo se agregan los locales que desarrollo siempre necesita (testserver = pruebas automáticas).
ALLOWED_HOSTS = list(dict.fromkeys([*ALLOWED_HOSTS, "localhost", "127.0.0.1", "[::1]", "testserver"]))  # noqa: F405

# En desarrollo la API también muestra la interfaz navegable de DRF.
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# La presentación (showcase.html, en la raíz) muestra la app dentro de un iframe desde otro
# puerto de localhost. Solo en desarrollo se quita el bloqueo de iframes; producción mantiene
# X-Frame-Options: DENY (si se publica la presentación, usar CSP frame-ancestors con su dominio).
MIDDLEWARE = [m for m in MIDDLEWARE if m != "django.middleware.clickjacking.XFrameOptionsMiddleware"]  # noqa: F405

# CSS/JS con ?v=<fecha de modificación>: tras cada cambio el navegador pide el archivo nuevo.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "apps.core.staticfiles.VersionedStaticFilesStorage"},
}
