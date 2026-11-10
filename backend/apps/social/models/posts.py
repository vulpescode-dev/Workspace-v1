"""Publicaciones internas del feed.

Borrado suave: ``deleted_at`` marca la publicación como eliminada (deja de verse en todos
lados); el borrado definitivo se hará más adelante con una política de retención.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

POST_BODY_MAX_LENGTH = 5000


class Post(models.Model):
    """Publicación del feed.

    ``audience``: «Toda la empresa» la ve cualquier persona con sesión; «Solo seguidores» solo
    la ven el autor y quienes lo siguen (``social.Follow``). La regla se aplica en ``selectors.posts``.
    """

    class Audience(models.TextChoices):
        COMPANY = "company", "Toda la empresa"
        FOLLOWERS = "followers", "Solo seguidores"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="posts", verbose_name="autor"
    )
    body = models.TextField("contenido", max_length=POST_BODY_MAX_LENGTH)
    audience = models.CharField("audiencia", max_length=10, choices=Audience.choices, default=Audience.COMPANY)
    created_at = models.DateTimeField("creada el", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("actualizada el", auto_now=True)
    edited_at = models.DateTimeField("editada el", null=True, blank=True)
    deleted_at = models.DateTimeField("eliminada el", null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "publicación"
        verbose_name_plural = "publicaciones"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.author} · {self.body[:40]}"

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])
