"""Crear, marcar como leídas y eliminar notificaciones.

``notify`` es la puerta de entrada para las demás apps (social, blog, documentos, sistema…):
cada una decide título, texto, ícono, color y enlace. Hoy la llama la mesa de ayuda (tickets); en las
demás, generar los avisos desde los eventos está pendiente en docs/backlog.md.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.notifications.models import Notification

TITLE_MAX_LENGTH = Notification._meta.get_field("title").max_length
BODY_MAX_LENGTH = Notification._meta.get_field("body").max_length
URL_MAX_LENGTH = Notification._meta.get_field("url").max_length


def notify(*, recipient, title: str, body: str = "", icon: str = "bx-bell",
           color: str = Notification.Color.PRIMARY, url: str = "") -> Notification | None:
    """Crea una notificación para ``recipient``. Personas inactivas no reciben nada (``None``).

    ``url`` debe ser una ruta interna (``/posts/12/``): nunca se manda a otro sitio.
    """
    if not recipient.is_active:
        return None
    title = " ".join((title or "").split())
    if not title:
        raise ValidationError({"title": "La notificación necesita un título."})
    if color not in Notification.Color.values:
        raise ValidationError({"color": "Color no válido."})
    if url and (not url.startswith("/") or url.startswith("//")):
        raise ValidationError({"url": "Solo rutas internas (empiezan con /)."})
    return Notification.objects.create(
        recipient=recipient, title=title[:TITLE_MAX_LENGTH], body=(body or "").strip()[:BODY_MAX_LENGTH],
        icon=icon or "bx-bell", color=color, url=url[:URL_MAX_LENGTH],
    )


def _ensure_recipient(user, notification: Notification) -> None:
    if notification.recipient_id != user.pk:
        raise PermissionDenied("Esta notificación no es tuya.")


def set_read(*, user, notification: Notification, read: bool = True) -> Notification:
    """Marca como leída (o vuelve a no leída). La fecha de lectura no cambia si ya estaba leída."""
    _ensure_recipient(user, notification)
    if read and notification.read_at is None:
        notification.read_at = timezone.now()
    elif not read:
        notification.read_at = None
    notification.save(update_fields=["read_at"])
    return notification


def mark_all_read(*, user) -> int:
    """Marca como leídas todas mis notificaciones pendientes. Devuelve cuántas cambiaron."""
    return Notification.objects.filter(recipient=user, read_at__isnull=True).update(read_at=timezone.now())


def delete_notification(*, user, notification: Notification) -> None:
    """Las notificaciones son personales: se borran de verdad (no hay borrado suave)."""
    _ensure_recipient(user, notification)
    notification.delete()
