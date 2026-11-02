"""Seguir y dejar de seguir (inmediato, sin solicitud)."""
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.social.models import Follow


def follow(*, user, target: User) -> None:
    if target.pk == user.pk:
        raise ValidationError({"user": "No puedes seguirte a ti misma/o."})
    if not target.is_active:
        raise ValidationError({"user": "Esta persona ya no está activa."})
    Follow.objects.get_or_create(follower=user, following=target)


def unfollow(*, user, target: User) -> None:
    Follow.objects.filter(follower=user, following=target).delete()
