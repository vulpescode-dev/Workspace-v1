from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _restore_emojis_if_empty(sender, using, **kwargs):
    """Red de seguridad: si después de ``migrate`` no hay ningún emoji (migraciones regeneradas o
    tabla vaciada), se cargan desde el JSON. Si ya hay emojis no hace nada: los cambios hechos en el
    admin (p. ej. desactivar uno) se respetan; para recargar a propósito, ``load_catalogs``."""
    from django.db import connections

    from apps.catalogs.models import Emoji
    from apps.catalogs.services.emojis import load_emojis, read_emojis_json

    if Emoji._meta.db_table not in connections[using].introspection.table_names():
        return   # p. ej. «migrate catalogs zero»: la tabla ya no existe
    if not Emoji.objects.using(using).exists():
        load_emojis(read_emojis_json())


class CatalogsConfig(AppConfig):
    """Datos de referencia compartidos entre apps (p. ej. emojis de reacciones).

    Solo va aquí lo que usan varias apps; lo que es de una sola app se queda en ella.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalogs"
    verbose_name = "Catálogos"

    def ready(self):
        post_migrate.connect(_restore_emojis_if_empty, sender=self)
