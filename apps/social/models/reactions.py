from django.db import models

from apps.catalogs.models import BaseReaction

from .comments import PostComment
from .posts import Post


class PostReaction(BaseReaction):
    """Reacción con emoji a una publicación.

    Regla del proyecto (confirmada): una reacción por persona y publicación; elegir otro
    emoji la reemplaza.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions", verbose_name="publicación")

    class Meta:
        verbose_name = "reacción a publicación"
        verbose_name_plural = "reacciones a publicaciones"
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="uniq_post_reaction_user"),
        ]
        indexes = [
            models.Index(fields=["post", "emoji"], name="post_reaction_emoji_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} · {self.emoji.code} · {self.post_id}"


class CommentReaction(BaseReaction):
    """Reacción con emoji a un comentario (misma regla: una por persona)."""

    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name="reactions", verbose_name="comentario")

    class Meta:
        verbose_name = "reacción a comentario"
        verbose_name_plural = "reacciones a comentarios"
        constraints = [
            models.UniqueConstraint(fields=["comment", "user"], name="uniq_comment_reaction_user"),
        ]
        indexes = [
            models.Index(fields=["comment", "emoji"], name="comment_reaction_emoji_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} · {self.emoji.code} · comentario {self.comment_id}"
