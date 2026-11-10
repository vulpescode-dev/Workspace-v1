"""Ajustes de desarrollo local (DJANGO_ENV=development)."""
from .base import *  # noqa: F401,F403
from .base import SECRET_KEY as _SECRET_KEY

DEBUG = True
SECRET_KEY = _SECRET_KEY or "inseguro-solo-para-desarrollo-local"
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": SIMPLE_JWT["SIGNING_KEY"] or SECRET_KEY}  # noqa: F405
# Los hosts salen de DJANGO_ALLOWED_HOSTS (.env, p. ej. la IP de tu PC para entrar desde el teléfono);
# aquí solo se agrega «testserver», que usan las pruebas automáticas.
ALLOWED_HOSTS = list(dict.fromkeys([*ALLOWED_HOSTS, "testserver"]))  # noqa: F405

# En desarrollo la API también muestra la interfaz navegable de DRF.
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}
