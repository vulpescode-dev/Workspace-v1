"""Seguir y dejar de seguir (inmediato, sin solicitud)."""
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.social.models import Follow
from apps.social.services import notifications
from apps.accounts.services.permissions import require_permission


def follow(*, user, target: User) -> None:
    require_permission(user, "social.follows.create", "No tienes permiso para seguir a otras personas.")
    if target.pk == user.pk:
        raise ValidationError({"user": "No puedes seguirte a ti misma/o."})
    if not target.is_active:
        raise ValidationError({"user": "Esta persona ya no está activa."})
    _, created = Follow.objects.get_or_create(follower=user, following=target)
    if created:
        notifications.followed(follower=user, target=target)


def unfollow(*, user, target: User) -> None:
    if Follow.objects.filter(follower=user, following=target).delete()[0]:
        notifications.unfollowed(follower=user, target=target)
