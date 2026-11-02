"""Artículos del blog (en la referencia: «Noticias»).

No confundir con ``social.Post``: un post es corto y vive en el feed; un artículo tiene título,
portada y un cuerpo largo en **HTML** escrito con un editor enriquecido.

- ``body`` se limpia al guardar (``services.html.clean_article_html``): solo HTML permitido.
- Visible cuando ``status`` es «Publicado», ``published_at`` ya llegó y no está eliminado; así
  también se pueden programar publicaciones a futuro.
- Borrado suave con ``deleted_at``, igual que las publicaciones.
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

from apps.blog.services.html import clean_article_html

from .categories import ArticleCategory


def article_cover_path(instance, filename: str) -> str:
    # ``filename`` lo genera el servidor (p. ej. "cover.webp"); nunca el nombre original.
    return f"blog/articles/{instance.pk}/{filename}"


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicado"

    title = models.CharField("título", max_length=200)
    slug = models.SlugField(
        "slug", max_length=220, unique=True, blank=True,
        help_text="Parte de la URL (/blog/<slug>/). Si se deja vacío se genera del título.",
    )
    excerpt = models.CharField("resumen", max_length=300, blank=True, help_text="Texto corto opcional para la tarjeta.")
    body = models.TextField("contenido (HTML)", blank=True)
    cover = models.FileField("portada", upload_to=article_cover_path, max_length=255, blank=True)
    category = models.ForeignKey(
        ArticleCategory, on_delete=models.PROTECT, null=True, blank=True, related_name="articles",
        verbose_name="categoría",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="articles", verbose_name="autor"
    )
    status = models.CharField("estado", max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(
        "fecha de publicación", null=True, blank=True, db_index=True,
        help_text="La que se muestra en la tarjeta. Al publicar sin fecha se usa el momento actual.",
    )
    created_at = models.DateTimeField("creado el", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado el", auto_now=True)
    deleted_at = models.DateTimeField("eliminado el", null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "artículo"
        verbose_name_plural = "artículos"
        ordering = ["-published_at", "-id"]
        indexes = [
            models.Index(fields=["status", "-published_at"], name="article_status_published_idx"),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        self.body = clean_article_html(self.body)
        if not self.slug:
            self.slug = self._unique_slug()
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = {*kwargs["update_fields"], "body", "slug", "published_at"}
        super().save(*args, **kwargs)

    def _unique_slug(self) -> str:
        base = slugify(self.title)[:200] or "articulo"
        slug, n = base, 2
        while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug, n = f"{base}-{n}", n + 1
        return slug

    @property
    def is_visible(self) -> bool:
        return (
            self.status == self.Status.PUBLISHED and self.deleted_at is None
            and self.published_at is not None and self.published_at <= timezone.now()
        )

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])


@receiver(post_delete, sender=Article)
def _delete_cover_file(sender, instance, **kwargs):
    """Al borrar el artículo se borra también su portada del disco."""
    if instance.cover:
        instance.cover.delete(save=False)
