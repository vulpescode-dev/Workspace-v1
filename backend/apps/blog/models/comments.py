from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .articles import Article

ARTICLE_COMMENT_BODY_MAX_LENGTH = 2000


class ArticleComment(models.Model):
    """Comentario de texto en un artículo (mismas reglas que ``social.PostComment``).

    - Respuestas de un solo nivel: ``parent`` apunta siempre a un comentario raíz del mismo artículo.
    - Borrado suave (``deleted_at``).
    """

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments", verbose_name="artículo")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="article_comments", verbose_name="autor"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies", verbose_name="responde a"
    )
    body = models.TextField("contenido", max_length=ARTICLE_COMMENT_BODY_MAX_LENGTH)
    created_at = models.DateTimeField("creado el", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado el", auto_now=True)
    edited_at = models.DateTimeField("editado el", null=True, blank=True)
    deleted_at = models.DateTimeField("eliminado el", null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "comentario de artículo"
        verbose_name_plural = "comentarios de artículos"
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["article", "created_at"], name="article_comment_created_idx")]

    def __str__(self) -> str:
        return f"{self.author}: {self.body[:40]}"

    def clean(self):
        super().clean()
        if self.parent_id:
            if self.parent.article_id != self.article_id:
                raise ValidationError({"parent": "La respuesta debe pertenecer al mismo artículo."})
            if self.parent.parent_id:
                raise ValidationError({"parent": "Solo se permite un nivel de respuestas."})

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])
