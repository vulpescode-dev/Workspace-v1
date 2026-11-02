"""Lectura de notificaciones y de mis dispositivos con push."""
from apps.notifications.models import Notification, PushSubscription


def my_notifications(user):
    """Mis notificaciones, más recientes primero."""
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return Notification.objects.none()
    return Notification.objects.filter(recipient=user).order_by("-created_at", "-id")


def unread_count(user) -> int:
    return my_notifications(user).filter(read_at__isnull=True).count()


def my_push_subscriptions(user):
    """Dispositivos donde activé las notificaciones push, el más reciente primero."""
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return PushSubscription.objects.none()
    return PushSubscription.objects.filter(user=user).order_by("-created_at", "-id")
