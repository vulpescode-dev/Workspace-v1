"""Artículos del Marketplace, sus fotos y sus categorías.

Borrado suave: ``deleted_at`` marca el artículo como eliminado (deja de verse en todos lados),
igual que las publicaciones del muro. Las fotos se guardan como
``marketplace/listings/<listing_id>/<image_id>.webp`` y se entregan por una vista autorizada.
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

LISTING_TITLE_MAX_LENGTH = 120
LISTING_DESCRIPTION_MAX_LENGTH = 3000
LISTING_MAX_IMAGES = 10


class ListingCategory(models.Model):
    """Categoría para filtrar («Electrónica», «Hogar», «Ropa»…). Las define la empresa desde el admin.

    Desactivada: deja de aparecer en los filtros y no se puede elegir, pero sus artículos la conservan.
    """

    name = models.CharField("nombre", max_length=60, unique=True)
    slug = models.SlugField("slug", max_length=70, unique=True)
    position = models.PositiveSmallIntegerField("orden", default=0)
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "categoría del marketplace"
        verbose_name_plural = "categorías del marketplace"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name


class Listing(models.Model):
    """Artículo publicado por una persona. Lo ve toda la empresa; solo quien lo publicó lo cambia."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponible"
        SOLD = "sold", "Vendido"

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="listings", verbose_name="vendedor(a)"
    )
    category = models.ForeignKey(
        ListingCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="listings",
        verbose_name="categoría",
    )
    title = models.CharField("título", max_length=LISTING_TITLE_MAX_LENGTH)
    description = models.TextField("descripción", max_length=LISTING_DESCRIPTION_MAX_LENGTH, blank=True)
    price = models.DecimalField(
        "precio (MXN)", max_digits=10, decimal_places=2, null=True, blank=True, help_text="Vacío: «A tratar».",
    )
    status = models.CharField("estatus", max_length=10, choices=Status.choices, default=Status.AVAILABLE)
    sold_at = models.DateTimeField("vendido el", null=True, blank=True)
    created_at = models.DateTimeField("publicado el", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("actualizado el", auto_now=True)
    deleted_at = models.DateTimeField("eliminado el", null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "artículo en venta"
        verbose_name_plural = "artículos en venta"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["status", "-created_at"], name="listing_status_created_idx")]

    def __str__(self) -> str:
        return self.title

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])


def listing_image_path(instance, filename: str) -> str:
    # ``filename`` ya llega como "<id>.webp" desde services.listings.
    return f"marketplace/listings/{instance.listing_id}/{filename}"


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="images", verbose_name="artículo")
    file = models.FileField("archivo", upload_to=listing_image_path, max_length=255, blank=True)
    original_name = models.CharField("nombre original", max_length=255, blank=True)
    content_type = models.CharField("tipo MIME", max_length=50)
    size = models.PositiveBigIntegerField("tamaño (bytes)")
    width = models.PositiveIntegerField("ancho", null=True, blank=True)
    height = models.PositiveIntegerField("alto", null=True, blank=True)
    position = models.PositiveSmallIntegerField("orden", default=0)
    created_at = models.DateTimeField("subida el", auto_now_add=True)

    class Meta:
        verbose_name = "foto del artículo"
        verbose_name_plural = "fotos del artículo"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return self.file.name or f"foto {self.pk}"


@receiver(post_delete, sender=ListingImage)
def _delete_image_file(sender, instance, **kwargs):
    """Al borrar el registro (o su artículo) se borra también el archivo del disco."""
    if instance.file:
        instance.file.delete(save=False)
