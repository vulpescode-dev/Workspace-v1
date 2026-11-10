"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""


from config.env import load_env
from django.core.wsgi import get_wsgi_application

load_env()   # backend/.env; DJANGO_ENV elige config.settings.<entorno>

application = get_wsgi_application()
