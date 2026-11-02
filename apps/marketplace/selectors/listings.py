"""Consultas de lectura del Marketplace.

Cualquier persona autenticada y activa ve todos los artículos (disponibles y vendidos);
lo eliminado (borrado suave) nunca se devuelve.
"""
from django.db.models import Q

from apps.marketplace.models import Listing, ListingCategory, ListingImage


def visible_listings(user):
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return Listing.objects.none()
    return (
        Listing.objects.filter(deleted_at__isnull=True)
        .select_related("seller", "category")
        .prefetch_related("images")
    )


def filter_listings(qs, *, status: str = "", category: str = "", seller: int | None = None, query: str = ""):
    """Filtros de la lista: estatus, categoría (slug), vendedor(a) y texto en título o descripción."""
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category__slug=category)
    if seller:
        qs = qs.filter(seller_id=seller)
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return qs


def active_categories():
    return ListingCategory.objects.filter(is_active=True)


def visible_image(user, pk: int) -> ListingImage | None:
    """Una foto solo se entrega si su artículo es visible para ``user``."""
    image = ListingImage.objects.filter(pk=pk).first()
    if image is None or not visible_listings(user).filter(pk=image.listing_id).exists():
        return None
    return image
