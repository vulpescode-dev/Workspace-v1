"""Señales de cuentas. Se conectan en ``AccountsConfig.ready``."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import User
from apps.accounts.services.roles import assign_default_roles


@receiver(post_save, sender=User, dispatch_uid="accounts.assign_default_roles")
def give_default_roles(sender, instance, created, raw=False, **kwargs):
    """Usuario nuevo → recibe los roles por defecto. Se usa una señal (y no el formulario o la vista)
    para cubrir todas las formas de crear usuarios. ``raw``: al cargar fixtures no se toca nada."""
    if created and not raw:
        assign_default_roles(instance)
