"""Subir, borrar y marcar como vistos los estados."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.uploads import check_media_upload
from apps.social.models import STORY_LIFETIME, STORY_MAX_ACTIVE, Story, StoryView
from apps.accounts.services.permissions import require_permission


def create_story(*, author, upload) -> Story:
    """Crea un estado con una imagen (WebP) o un video. Vence a las 24 horas."""
    require_permission(author, "social.stories.create", "No tienes permiso para subir estados.")
    if not upload:
        raise ValidationError({"file": "Elige una foto o un video."})
    now = timezone.now()
    active = Story.objects.filter(author=author, deleted_at__isnull=True, expires_at__gt=now).count()
    if active >= STORY_MAX_ACTIVE:
        raise ValidationError({"file": f"Puedes tener hasta {STORY_MAX_ACTIVE} estados activos."})
    try:
        info = check_media_upload(upload)
    except ValidationError as exc:
        raise ValidationError({"file": exc.messages[0]}) from exc

    with transaction.atomic():
        story = Story.objects.create(
            author=author, kind=info.kind, content_type=info.content_type, size=info.size,
            width=info.width, height=info.height, expires_at=now + STORY_LIFETIME,
        )
        story.file.save(f"{story.pk}{info.extension}", upload, save=True)
    return story


def delete_story(*, user, story: Story) -> None:
    """Borrado suave. Quien lo subió, con ``social.stories.delete``; otra persona solo con
    ``social.stories.delete.all`` (moderación). El archivo se queda hasta la purga de vencidos."""
    if story.author_id == user.pk:
        require_permission(user, "social.stories.delete", "No tienes permiso para eliminar estados.")
    else:
        require_permission(user, "social.stories.delete.all", "Solo quien subió el estado puede eliminarlo.")
    story.deleted_at = timezone.now()
    story.save(update_fields=["deleted_at"])


def mark_story_seen(*, user, story: Story) -> None:
    """Registra que ``user`` vio el estado (una vez; los propios no cuentan)."""
    if story.author_id != user.pk:
        StoryView.objects.get_or_create(story=story, viewer=user)
