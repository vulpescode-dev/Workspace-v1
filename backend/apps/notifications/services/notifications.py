"""Crear, marcar como leídas y eliminar notificaciones.

``notify`` es la puerta de entrada para las demás apps (social, mesa de ayuda, documentos, sistema…):
cada una decide título, texto, ícono, color y enlace. Con ``key`` el aviso queda ligado a un evento:
repetirlo lo actualiza (sin duplicar ni volver a avisar) y ``withdraw`` lo retira si se deshace.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.notifications.models import Notification

TITLE_MAX_LENGTH = Notification._meta.get_field("title").max_length
BODY_MAX_LENGTH = Notification._meta.get_field("body").max_length
URL_MAX_LENGTH = Notification._meta.get_field("url").max_length
KEY_MAX_LENGTH = Notification._meta.get_field("key").max_length


def notify(*, recipient, title: str, body: str = "", icon: str = "bx-bell",
           color: str = Notification.Color.PRIMARY, url: str = "", key: str = "") -> Notification | None:
    """Crea una notificación para ``recipient``. Personas inactivas no reciben nada (``None``).

    ``url`` debe ser una ruta interna (``/posts/12/``): nunca se manda a otro sitio.
    ``key``: si ya existe un aviso con esa clave para esa persona, solo se actualizan título, texto y
    enlace (conserva fecha y si ya se leyó): cambiar de emoji no vuelve a avisar.
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
    values = {
        "title": title[:TITLE_MAX_LENGTH], "body": (body or "").strip()[:BODY_MAX_LENGTH],
        "icon": icon or "bx-bell", "color": color, "url": url[:URL_MAX_LENGTH],
    }
    if key:
        existing = Notification.objects.filter(recipient=recipient, key=key).first()
        if existing:
            for field, value in values.items():
                setattr(existing, field, value)
            existing.save(update_fields=list(values))
            return existing
    return Notification.objects.create(recipient=recipient, key=key[:KEY_MAX_LENGTH], **values)


def withdraw(*, key: str = "", prefix: str = "") -> int:
    """Retira los avisos de un evento que se deshizo (``key`` exacta) o de todo lo que cuelga de algo que
    se eliminó (``prefix``, p. ej. todos los de una publicación). Devuelve cuántos se borraron."""
    if key:
        return Notification.objects.filter(key=key).delete()[0]
    if prefix:
        return Notification.objects.filter(key__startswith=prefix).delete()[0]
    return 0


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
