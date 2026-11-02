"""Reaccionar a publicaciones. La visibilidad del post la valida quien llama (la API usa ``visible_posts``)."""
from django.core.exceptions import ValidationError

from apps.catalogs.selectors.emojis import get_active_emoji
from apps.social.models import Post, PostReaction


def set_reaction(*, user, post: Post, emoji_code: str) -> PostReaction:
    """Pone o cambia la reacción de ``user`` en ``post`` (una por persona)."""
    emoji = get_active_emoji(emoji_code or "")
    if emoji is None:
        raise ValidationError({"emoji": "Emoji no válido."})
    reaction, _ = PostReaction.objects.update_or_create(post=post, user=user, defaults={"emoji": emoji})
    return reaction


def remove_reaction(*, user, post: Post) -> None:
    PostReaction.objects.filter(post=post, user=user).delete()
