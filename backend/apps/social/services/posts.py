"""Operaciones que crean o modifican publicaciones."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.uploads import check_media_upload
from apps.social.models import POST_BODY_MAX_LENGTH, POST_MAX_ATTACHMENTS, Post, PostAttachment
from apps.social.services import notifications
from apps.accounts.services.permissions import require_permission


def _clean_audience(audience: str | None) -> str:
    audience = audience or Post.Audience.COMPANY
    if audience not in Post.Audience.values:
        raise ValidationError({"audience": "Audiencia no válida."})
    return audience


def create_post(*, author, body: str, files=(), audience: str | None = None) -> Post:
    """Crea una publicación con texto y/o imágenes y videos.

    Todos los archivos se validan ANTES de escribir nada: si uno falla, no se crea la
    publicación. Cada archivo se guarda como ``<id del adjunto><ext>``.
    """
    require_permission(author, "social.posts.create", "No tienes permiso para publicar.")
    # Los formularios multipart mandan los saltos de línea como CRLF: se guardan como LF.
    body = (body or "").replace("\r\n", "\n").strip()
    files = list(files or [])
    if not body and not files:
        raise ValidationError({"body": "La publicación no puede estar vacía."})
    if len(body) > POST_BODY_MAX_LENGTH:
        raise ValidationError({"body": f"Máximo {POST_BODY_MAX_LENGTH} caracteres."})
    audience = _clean_audience(audience)
    if len(files) > POST_MAX_ATTACHMENTS:
        raise ValidationError({"files": f"Máximo {POST_MAX_ATTACHMENTS} archivos por publicación."})

    checked = []
    for upload in files:
        try:
            checked.append((upload, check_media_upload(upload)))
        except ValidationError as exc:
            name = getattr(upload, "name", "archivo")
            raise ValidationError({"files": f"«{name}»: {exc.messages[0]}"}) from exc

    with transaction.atomic():
        post = Post.objects.create(author=author, body=body, audience=audience)
        for position, (upload, info) in enumerate(checked):
            attachment = PostAttachment.objects.create(
                post=post, kind=info.kind, original_name=(getattr(upload, "name", "") or "")[:255],
                content_type=info.content_type, size=info.size, width=info.width, height=info.height,
                position=position,
            )
            attachment.file.save(f"{attachment.pk}{info.extension}", upload, save=True)
    return post


def _ensure_author(user, post: Post) -> None:
    if post.author_id != user.pk:
        raise PermissionDenied("Solo quien publicó puede cambiar esta publicación.")


def edit_post(*, user, post: Post, body: str, audience: str | None = None) -> Post:
    """Edita el texto y, si se indica, la audiencia (los adjuntos no se cambian aquí).
    Puede quedar sin texto si tiene adjuntos."""
    _ensure_author(user, post)
    require_permission(user, "social.posts.update", "No tienes permiso para editar publicaciones.")
    if audience is not None:
        post.audience = _clean_audience(audience)
    body = (body or "").replace("\r\n", "\n").strip()
    if not body and not post.attachments.exists():
        raise ValidationError({"body": "La publicación no puede estar vacía."})
    if len(body) > POST_BODY_MAX_LENGTH:
        raise ValidationError({"body": f"Máximo {POST_BODY_MAX_LENGTH} caracteres."})
    post.body = body
    post.edited_at = timezone.now()
    post.save(update_fields=["body", "audience", "edited_at", "updated_at"])
    return post


def delete_post(*, user, post: Post) -> None:
    """Borrado suave: deja de verse (con sus comentarios, reacciones y archivos).

    Los archivos se conservan hasta el borrado definitivo (política pendiente, ver docs/backlog.md).
    Quien publicó la borra con ``social.posts.delete``; otra persona solo con ``social.posts.delete.all`` (moderación).
    """
    if post.author_id == user.pk:
        require_permission(user, "social.posts.delete", "No tienes permiso para eliminar publicaciones.")
    else:
        require_permission(user, "social.posts.delete.all", "Solo quien publicó puede cambiar esta publicación.")
    post.soft_delete()
    notifications.post_deleted(post=post)
