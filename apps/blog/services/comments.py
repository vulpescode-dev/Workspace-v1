"""Comentar, editar y eliminar comentarios de artículos (mismas reglas que en el muro).

La visibilidad del artículo la valida quien llama (la API usa los selectores). Solo se comenta en
artículos publicados; solo el autor edita o elimina; respuestas de un nivel; borrado suave.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.blog.models import ARTICLE_COMMENT_BODY_MAX_LENGTH, Article, ArticleComment


def _clean_body(body: str) -> str:
    body = (body or "").replace("\r\n", "\n").strip()
    if not body:
        raise ValidationError({"body": "El comentario no puede estar vacío."})
    if len(body) > ARTICLE_COMMENT_BODY_MAX_LENGTH:
        raise ValidationError({"body": f"Máximo {ARTICLE_COMMENT_BODY_MAX_LENGTH} caracteres."})
    return body


def create_comment(*, author, article: Article, body: str, parent_id: int | None = None) -> ArticleComment:
    """Comenta en ``article``. Con ``parent_id`` es una respuesta; responder a una respuesta
    cuelga del mismo hilo (siempre un solo nivel)."""
    if not article.is_visible:
        raise ValidationError({"article": "Solo se puede comentar en artículos publicados."})
    body = _clean_body(body)
    parent = None
    if parent_id:
        parent = ArticleComment.objects.filter(pk=parent_id, article=article, deleted_at__isnull=True).first()
        if parent is None:
            raise ValidationError({"parent": "El comentario al que respondes ya no existe."})
        if parent.parent_id:
            parent = parent.parent
    return ArticleComment.objects.create(article=article, author=author, body=body, parent=parent)


def _ensure_author(user, comment: ArticleComment) -> None:
    if comment.author_id != user.pk:
        raise PermissionDenied("Solo quien escribió el comentario puede cambiarlo.")


def edit_comment(*, user, comment: ArticleComment, body: str) -> ArticleComment:
    _ensure_author(user, comment)
    comment.body = _clean_body(body)
    comment.edited_at = timezone.now()
    comment.save(update_fields=["body", "edited_at", "updated_at"])
    return comment


def delete_comment(*, user, comment: ArticleComment) -> None:
    """Borrado suave. Sus respuestas siguen visibles; el hilo muestra «Comentario eliminado»."""
    _ensure_author(user, comment)
    comment.soft_delete()
