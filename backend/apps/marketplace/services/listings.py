"""Operaciones que crean o modifican artículos del Marketplace.

Fotos: hasta ``LISTING_MAX_IMAGES`` por artículo, solo imágenes WebP. Se pueden agregar o quitar
después de publicar (solo quien lo publicó); quitar una borra su registro y su archivo.
"""
from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.uploads import KIND_IMAGE, check_media_upload
from apps.marketplace.models import (
    LISTING_DESCRIPTION_MAX_LENGTH, LISTING_MAX_IMAGES, LISTING_TITLE_MAX_LENGTH, Listing, ListingCategory, ListingImage,
)
from apps.accounts.services.permissions import has_permission, require_permission

UNSET = object()   # al editar: distingue «no se mandó» de «se mandó vacío»
PRICE_MAX = Decimal("99999999.99")


def _clean_title(title: str) -> str:
    title = " ".join((title or "").split())
    if not title:
        raise ValidationError({"title": "Escribe un título."})
    if len(title) > LISTING_TITLE_MAX_LENGTH:
        raise ValidationError({"title": f"Máximo {LISTING_TITLE_MAX_LENGTH} caracteres."})
    return title


def _clean_description(description: str) -> str:
    # Los formularios multipart mandan los saltos de línea como CRLF: se guardan como LF.
    description = (description or "").replace("\r\n", "\n").strip()
    if len(description) > LISTING_DESCRIPTION_MAX_LENGTH:
        raise ValidationError({"description": f"Máximo {LISTING_DESCRIPTION_MAX_LENGTH} caracteres."})
    return description


def _clean_price(price) -> Decimal | None:
    """Vacío = «A tratar». Pesos con hasta 2 decimales."""
    if price is None or str(price).strip() == "":
        return None
    try:
        price = Decimal(str(price).strip())
    except InvalidOperation:
        raise ValidationError({"price": "Precio no válido."}) from None
    if not price.is_finite() or price < 0 or price > PRICE_MAX:
        raise ValidationError({"price": "Precio no válido."})
    return price.quantize(Decimal("0.01"))


def _clean_category(category_id) -> ListingCategory | None:
    if category_id in (None, ""):
        return None
    category = ListingCategory.objects.filter(pk=category_id, is_active=True).first()
    if category is None:
        raise ValidationError({"category": "Categoría no válida."})
    return category


def create_listing(*, seller, title: str, description: str = "", price=None, category_id=None, files=()) -> Listing:
    """Publica un artículo con hasta ``LISTING_MAX_IMAGES`` fotos (solo imágenes WebP).

    Todas las fotos se validan ANTES de escribir nada: si una falla, no se crea el artículo.
    Cada foto se guarda como ``<id del registro>.webp``.
    """
    require_permission(seller, "marketplace.listings.create", "No tienes permiso para publicar anuncios.")
    title = _clean_title(title)
    description = _clean_description(description)
    price = _clean_price(price)
    category = _clean_category(category_id)
    checked = _check_images(files, already=0)

    with transaction.atomic():
        listing = Listing.objects.create(
            seller=seller, title=title, description=description, price=price, category=category,
        )
        _save_images(listing, checked, start=0)
    return listing


def _check_images(files, *, already: int) -> list:
    """Valida todas las fotos antes de escribir nada. ``already``: cuántas tiene ya el artículo."""
    files = list(files or [])
    if already + len(files) > LISTING_MAX_IMAGES:
        raise ValidationError({"files": f"Máximo {LISTING_MAX_IMAGES} fotos por artículo."})
    checked = []
    for upload in files:
        name = getattr(upload, "name", "archivo")
        try:
            info = check_media_upload(upload)
        except ValidationError as exc:
            raise ValidationError({"files": f"«{name}»: {exc.messages[0]}"}) from exc
        if info.kind != KIND_IMAGE:
            raise ValidationError({"files": f"«{name}»: solo se permiten fotos."})
        checked.append((upload, info))
    return checked


def _save_images(listing: Listing, checked, *, start: int) -> None:
    """Guarda las fotos ya validadas al final (orden ``start``, ``start + 1``…). Llamar dentro de una transacción."""
    for offset, (upload, info) in enumerate(checked):
        image = ListingImage.objects.create(
            listing=listing, original_name=(getattr(upload, "name", "") or "")[:255],
            content_type=info.content_type, size=info.size, width=info.width, height=info.height,
            position=start + offset,
        )
        image.file.save(f"{image.pk}{info.extension}", upload, save=True)


def _ensure_seller(user, listing: Listing, moderation: str = "marketplace.listings.update.all") -> None:
    """Quien lo publicó, o alguien con ``moderation`` (``marketplace.listings.update.all`` / ``.delete.all``)."""
    if listing.seller_id != user.pk and not has_permission(user, moderation):
        raise PermissionDenied("Solo quien publicó el artículo puede cambiarlo.")


def edit_listing(*, user, listing: Listing, title=UNSET, description=UNSET, price=UNSET, category_id=UNSET,
                 status=UNSET) -> Listing:
    """Cambia solo los campos que se manden (las fotos no se cambian aquí).

    ``status``: «Vendido» guarda la fecha de venta; volver a «Disponible» la borra.
    """
    _ensure_seller(user, listing)
    if title is not UNSET:
        listing.title = _clean_title(title)
    if description is not UNSET:
        listing.description = _clean_description(description)
    if price is not UNSET:
        listing.price = _clean_price(price)
    if category_id is not UNSET:
        listing.category = _clean_category(category_id)
    if status is not UNSET and status != listing.status:
        if status not in Listing.Status.values:
            raise ValidationError({"status": "Estatus no válido."})
        listing.status = status
        listing.sold_at = timezone.now() if status == Listing.Status.SOLD else None
    listing.save()
    return listing


def add_images(*, user, listing: Listing, files) -> Listing:
    """Agrega fotos al final, sin pasar del máximo."""
    _ensure_seller(user, listing)
    if not files:
        raise ValidationError({"files": "Elige al menos una foto."})
    with transaction.atomic():
        # Bloquea el artículo: dos subidas al mismo tiempo no pueden pasarse del máximo.
        Listing.objects.select_for_update().filter(pk=listing.pk).first()
        images = ListingImage.objects.filter(listing=listing)   # sin la caché del prefetch
        checked = _check_images(files, already=images.count())
        last = images.order_by("-position").values_list("position", flat=True).first()
        _save_images(listing, checked, start=0 if last is None else last + 1)
        listing.save(update_fields=["updated_at"])
    return listing


def remove_image(*, user, image: ListingImage) -> None:
    """Quita una foto (registro y archivo). El artículo puede quedarse sin fotos."""
    _ensure_seller(user, image.listing)
    listing = image.listing
    image.delete()
    listing.save(update_fields=["updated_at"])


def delete_listing(*, user, listing: Listing) -> None:
    """Borrado suave: deja de verse. Las fotos se conservan hasta el borrado definitivo (política pendiente)."""
    _ensure_seller(user, listing, "marketplace.listings.delete.all")
    listing.soft_delete()
