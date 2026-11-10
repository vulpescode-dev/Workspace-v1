from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _sync_permission_catalog(sender, using, **kwargs):
    """Tras cada ``migrate``, los permisos de negocio quedan iguales al catálogo JSON (crea y actualiza;
    nunca borra: para eso ``load_permissions --prune``)."""
    from django.db import connections

    from apps.accounts.models import Permission
    from apps.accounts.services.permission_catalog import read_permissions_json, sync_permissions
    from apps.accounts.services.role_catalog import read_roles_json, sync_roles

    if Permission._meta.db_table not in connections[using].introspection.table_names():
        return   # p. ej. «migrate accounts zero»: la tabla ya no existe
    sync_permissions(read_permissions_json(), using=using)
    # Después de los permisos: los roles básicos que falten (los existentes no se tocan).
    sync_roles(read_roles_json(), using=using)


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        from apps.accounts import signals  # noqa: F401  (conecta los roles por defecto de usuarios nuevos)

        post_migrate.connect(_sync_permission_catalog, sender=self, dispatch_uid="accounts.sync_permission_catalog")
