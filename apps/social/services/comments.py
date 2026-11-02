"""Comentar, editar, eliminar y reaccionar a comentarios.

La visibilidad del post/comentario la valida quien llama (la API usa los selectores). Aquí
se aplican las reglas de negocio: solo el autor edita o elimina; respuestas de un nivel.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.catalogs.selectors.emojis import get_active_emoji
from apps.social.models import COMMENT_BODY_MAX_LENGTH, CommentReaction, Post, PostComment


def _clean_body(body: str) -> str:
    body = (body or "").replace("\r\n", "\n").strip()
    if not body:
        raise ValidationError({"body": "El comentario no puede estar vacío."})
    if len(body) > COMMENT_BODY_MAX_LENGTH:
        raise ValidationError({"body": f"Máximo {COMMENT_BODY_MAX_LENGTH} caracteres."})
    return body


def create_comment(*, author, post: Post, body: str, parent_id: int | None = None) -> PostComment:
    """Comenta en ``post``. Con ``parent_id`` es una respuesta; responder a una respuesta
    cuelga del mismo hilo (siempre un solo nivel)."""
    body = _clean_body(body)
    parent = None
    if parent_id:
        parent = PostComment.objects.filter(pk=parent_id, post=post, deleted_at__isnull=True).first()
        if parent is None:
            raise ValidationError({"parent": "El comentario al que respondes ya no existe."})
        if parent.parent_id:
            parent = parent.parent
    return PostComment.objects.create(post=post, author=author, body=body, parent=parent)


def _ensure_author(user, comment: PostComment) -> None:
    if comment.author_id != user.pk:
        raise PermissionDenied("Solo quien escribió el comentario puede cambiarlo.")


def edit_comment(*, user, comment: PostComment, body: str) -> PostComment:
    _ensure_author(user, comment)
    comment.body = _clean_body(body)
    comment.edited_at = timezone.now()
    comment.save(update_fields=["body", "edited_at", "updated_at"])
    return comment


def delete_comment(*, user, comment: PostComment) -> None:
    """Borrado suave. Sus respuestas siguen visibles; el hilo muestra «Comentario eliminado»."""
    _ensure_author(user, comment)
    comment.soft_delete()


def set_comment_reaction(*, user, comment: PostComment, emoji_code: str) -> CommentReaction:
    emoji = get_active_emoji(emoji_code or "")
    if emoji is None:
        raise ValidationError({"emoji": "Emoji no válido."})
    reaction, _ = CommentReaction.objects.update_or_create(comment=comment, user=user, defaults={"emoji": emoji})
    return reaction


def remove_comment_reaction(*, user, comment: PostComment) -> None:
    CommentReaction.objects.filter(comment=comment, user=user).delete()
