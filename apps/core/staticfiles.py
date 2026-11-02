"""Archivos estáticos con versión en la URL, para que el navegador nunca use un CSS/JS viejo.

- Desarrollo: ``VersionedStaticFilesStorage`` agrega ``?v=<fecha de modificación>`` a cada
  ``{% static %}``. Al guardar un cambio la URL cambia y el navegador pide el archivo nuevo
  (sin esto Chrome reutiliza su copia en caché y se ven estilos de antes).
- Producción: ``ManifestStaticFilesStorage`` de Django (``collectstatic`` pone un hash en el nombre).
"""
import os

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage


class VersionedStaticFilesStorage(StaticFilesStorage):
    def url(self, name):
        url = super().url(name)
        path = finders.find(name)
        if not path or isinstance(path, list):
            return url
        return f"{url}{'&' if '?' in url else '?'}v={int(os.path.getmtime(path))}"
