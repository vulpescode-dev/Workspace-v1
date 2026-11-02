from django.db import models

from apps.catalogs.models import BaseReaction

from .articles import Article


class ArticleReaction(BaseReaction):
    """Reacción con emoji a un artículo (misma regla que las publicaciones: una por persona;
    elegir otro emoji la reemplaza)."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="reactions", verbose_name="artículo")

    class Meta:
        verbose_name = "reacción a artículo"
        verbose_name_plural = "reacciones a artículos"
        constraints = [
            models.UniqueConstraint(fields=["article", "user"], name="uniq_article_reaction_user"),
        ]
        indexes = [
            models.Index(fields=["article", "emoji"], name="article_reaction_emoji_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} · {self.emoji.code} · artículo {self.article_id}"
