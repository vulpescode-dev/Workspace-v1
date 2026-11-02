"""Reaccionar a artículos. La visibilidad del artículo la valida quien llama (la API usa los selectores)."""
from django.core.exceptions import ValidationError

from apps.blog.models import Article, ArticleReaction
from apps.catalogs.selectors.emojis import get_active_emoji


def set_reaction(*, user, article: Article, emoji_code: str) -> ArticleReaction:
    """Pone o cambia la reacción de ``user`` en ``article`` (una por persona)."""
    if not article.is_visible:
        raise ValidationError({"article": "Solo se puede reaccionar a artículos publicados."})
    emoji = get_active_emoji(emoji_code or "")
    if emoji is None:
        raise ValidationError({"emoji": "Emoji no válido."})
    reaction, _ = ArticleReaction.objects.update_or_create(article=article, user=user, defaults={"emoji": emoji})
    return reaction


def remove_reaction(*, user, article: Article) -> None:
    ArticleReaction.objects.filter(article=article, user=user).delete()
