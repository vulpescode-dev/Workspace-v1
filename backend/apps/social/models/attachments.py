"""Imágenes y videos adjuntos a una publicación (MEDIA, nunca static).

El archivo se guarda como ``social/posts/<post_id>/<attachment_id>.<ext>``: el nombre lo
genera el servidor y el nombre original solo se conserva como dato (``original_name``).
"""
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .posts import Post

POST_MAX_ATTACHMENTS = 10


def post_attachment_path(instance, filename: str) -> str:
    # ``filename`` ya llega como "<id>.<ext>" desde services.attachments.
    return f"social/posts/{instance.post_id}/{filename}"


class PostAttachment(models.Model):
    class Kind(models.TextChoices):
        IMAGE = "image", "Imagen"
        VIDEO = "video", "Video"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="attachments", verbose_name="publicación")
    kind = models.CharField("tipo", max_length=10, choices=Kind.choices)
    file = models.FileField("archivo", upload_to=post_attachment_path, max_length=255, blank=True)
    original_name = models.CharField("nombre original", max_length=255, blank=True)
    content_type = models.CharField("tipo MIME", max_length=50)
    size = models.PositiveBigIntegerField("tamaño (bytes)")
    width = models.PositiveIntegerField("ancho", null=True, blank=True)
    height = models.PositiveIntegerField("alto", null=True, blank=True)
    position = models.PositiveSmallIntegerField("orden", default=0)
    created_at = models.DateTimeField("creado el", auto_now_add=True)

    class Meta:
        verbose_name = "adjunto de publicación"
        verbose_name_plural = "adjuntos de publicación"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return self.file.name or f"adjunto {self.pk}"


@receiver(post_delete, sender=PostAttachment)
def _delete_attachment_file(sender, instance, **kwargs):
    """Al borrar el registro (o su publicación) se borra también el archivo del disco."""
    if instance.file:
        instance.file.delete(save=False)
