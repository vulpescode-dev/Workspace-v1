"""Estados (como las historias de Instagram): una foto o un video que se ve durante 24 horas.

En Inicio se muestran como la foto de la persona con un aro de color (sin abrir) o gris (ya visto).
El archivo se guarda como ``social/stories/<author_id>/<story_id>.<ext>`` y solo se entrega por la
vista autorizada. Al vencer deja de listarse; el borrado definitivo de vencidos es un pendiente.
"""
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

STORY_LIFETIME = timedelta(hours=24)
STORY_MAX_ACTIVE = 20   # estados vivos por persona al mismo tiempo


def story_path(instance, filename: str) -> str:
    # ``filename`` ya llega como "<id>.<ext>" desde services.stories.
    return f"social/stories/{instance.author_id}/{filename}"


class Story(models.Model):
    class Kind(models.TextChoices):
        IMAGE = "image", "Imagen"
        VIDEO = "video", "Video"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stories", verbose_name="autor")
    kind = models.CharField("tipo", max_length=10, choices=Kind.choices)
    file = models.FileField("archivo", upload_to=story_path, max_length=255, blank=True)
    content_type = models.CharField("tipo MIME", max_length=50)
    size = models.PositiveBigIntegerField("tamaño (bytes)")
    width = models.PositiveIntegerField("ancho", null=True, blank=True)
    height = models.PositiveIntegerField("alto", null=True, blank=True)
    created_at = models.DateTimeField("creado el", auto_now_add=True)
    expires_at = models.DateTimeField("vence el", db_index=True)
    deleted_at = models.DateTimeField("eliminado el", null=True, blank=True)

    class Meta:
        verbose_name = "estado"
        verbose_name_plural = "estados"
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["author", "expires_at"])]

    def __str__(self) -> str:
        return f"Estado {self.pk} de {self.author}"


class StoryView(models.Model):
    """Quién ya vio un estado (para pintar el aro gris y, después, la lista «Visto por»)."""

    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="views", verbose_name="estado")
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="story_views", verbose_name="quién lo vio")
    viewed_at = models.DateTimeField("visto el", auto_now_add=True)

    class Meta:
        verbose_name = "vista de estado"
        verbose_name_plural = "vistas de estados"
        constraints = [models.UniqueConstraint(fields=["story", "viewer"], name="unique_story_view")]


@receiver(post_delete, sender=Story)
def _delete_story_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
