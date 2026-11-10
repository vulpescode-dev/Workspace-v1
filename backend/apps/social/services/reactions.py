"""Reaccionar a publicaciones. La visibilidad del post la valida quien llama (la API usa ``visible_posts``)."""
from django.core.exceptions import ValidationError

from apps.catalogs.selectors.emojis import get_active_emoji
from apps.social.models import Post, PostReaction
from apps.social.services import notifications
from apps.accounts.services.permissions import require_permission


def set_reaction(*, user, post: Post, emoji_code: str) -> PostReaction:
    """Pone o cambia la reacción de ``user`` en ``post`` (una por persona)."""
    require_permission(user, "social.reactions.create", "No tienes permiso para reaccionar.")
    emoji = get_active_emoji(emoji_code or "")
    if emoji is None:
        raise ValidationError({"emoji": "Emoji no válido."})
    reaction, _ = PostReaction.objects.update_or_create(post=post, user=user, defaults={"emoji": emoji})
    notifications.post_reacted(post=post, user=user, emoji=emoji)
    return reaction


def remove_reaction(*, user, post: Post) -> None:
    if PostReaction.objects.filter(post=post, user=user).delete()[0]:
        notifications.post_reaction_removed(post=post, user=user)
