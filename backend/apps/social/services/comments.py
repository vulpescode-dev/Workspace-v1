"""Comentar, editar, eliminar y reaccionar a comentarios.

La visibilidad del post/comentario la valida quien llama (la API usa los selectores). Aquí
se aplican las reglas de negocio: solo el autor edita o elimina; respuestas de un nivel.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.catalogs.selectors.emojis import get_active_emoji
from apps.social.models import COMMENT_BODY_MAX_LENGTH, CommentReaction, Post, PostComment
from apps.social.services import notifications
from apps.accounts.services.permissions import require_permission


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
    require_permission(author, "social.comments.create", "No tienes permiso para comentar.")
    body = _clean_body(body)
    parent = None
    if parent_id:
        parent = PostComment.objects.filter(pk=parent_id, post=post, deleted_at__isnull=True).first()
        if parent is None:
            raise ValidationError({"parent": "El comentario al que respondes ya no existe."})
        if parent.parent_id:
            parent = parent.parent
    comment = PostComment.objects.create(post=post, author=author, body=body, parent=parent)
    notifications.comment_created(comment=comment)
    return comment


def _ensure_author(user, comment: PostComment) -> None:
    if comment.author_id != user.pk:
        raise PermissionDenied("Solo quien escribió el comentario puede cambiarlo.")


def edit_comment(*, user, comment: PostComment, body: str) -> PostComment:
    _ensure_author(user, comment)
    require_permission(user, "social.comments.update", "No tienes permiso para editar comentarios.")
    comment.body = _clean_body(body)
    comment.edited_at = timezone.now()
    comment.save(update_fields=["body", "edited_at", "updated_at"])
    notifications.comment_edited(comment=comment)
    return comment


def delete_comment(*, user, comment: PostComment) -> None:
    """Borrado suave. Sus respuestas siguen visibles; el hilo muestra «Comentario eliminado»."""
    # Quien lo escribió, con «social.comments.delete»; otra persona solo con «social.comments.delete.all» (moderación).
    if comment.author_id == user.pk:
        require_permission(user, "social.comments.delete", "No tienes permiso para eliminar comentarios.")
    else:
        require_permission(user, "social.comments.delete.all", "Solo quien escribió el comentario puede cambiarlo.")
    comment.soft_delete()
    notifications.comment_deleted(comment=comment)


def set_comment_reaction(*, user, comment: PostComment, emoji_code: str) -> CommentReaction:
    require_permission(user, "social.reactions.create", "No tienes permiso para reaccionar.")
    emoji = get_active_emoji(emoji_code or "")
    if emoji is None:
        raise ValidationError({"emoji": "Emoji no válido."})
    reaction, _ = CommentReaction.objects.update_or_create(comment=comment, user=user, defaults={"emoji": emoji})
    notifications.comment_reacted(comment=comment, user=user, emoji=emoji)
    return reaction


def remove_comment_reaction(*, user, comment: PostComment) -> None:
    if CommentReaction.objects.filter(comment=comment, user=user).delete()[0]:
        notifications.comment_reaction_removed(comment=comment, user=user)
