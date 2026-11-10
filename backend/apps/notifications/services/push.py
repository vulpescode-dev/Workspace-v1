"""Registrar y quitar dispositivos para notificaciones push (Web Push / PWA).

El navegador entrega la suscripción con ``PushManager.subscribe()``; ``subscription.toJSON()``
tiene la forma ``{"endpoint": "https://…", "keys": {"p256dh": "…", "auth": "…"}}`` y es lo que
recibe ``save_subscription``. Enviar los mensajes (llave privada VAPID) está pendiente.
"""
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError

from apps.notifications.models import PushSubscription

ENDPOINT_MAX_LENGTH = PushSubscription._meta.get_field("endpoint").max_length
KEY_MAX_LENGTHS = {
    "p256dh": PushSubscription._meta.get_field("p256dh").max_length,
    "auth": PushSubscription._meta.get_field("auth").max_length,
}
USER_AGENT_MAX_LENGTH = PushSubscription._meta.get_field("user_agent").max_length


def _clean_endpoint(endpoint: str) -> str:
    endpoint = (endpoint or "").strip()
    parts = urlsplit(endpoint)
    if parts.scheme != "https" or not parts.netloc or len(endpoint) > ENDPOINT_MAX_LENGTH:
        raise ValidationError({"endpoint": "Endpoint de push no válido (debe ser https)."})
    return endpoint


def save_subscription(*, user, endpoint: str, p256dh: str, auth: str, user_agent: str = "") -> PushSubscription:
    """Guarda (o actualiza) la suscripción de este dispositivo. Idempotente por ``endpoint``.

    Si el mismo navegador estaba suscrito con otra cuenta (equipo compartido), pasa a la cuenta
    actual: un dispositivo solo recibe los avisos de quien tiene la sesión abierta.
    """
    endpoint = _clean_endpoint(endpoint)
    keys = {"p256dh": (p256dh or "").strip(), "auth": (auth or "").strip()}
    for name, value in keys.items():
        if not value or len(value) > KEY_MAX_LENGTHS[name]:
            raise ValidationError({"keys": f"Falta la llave «{name}» o no es válida."})
    subscription, _ = PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={"user": user, **keys, "user_agent": (user_agent or "")[:USER_AGENT_MAX_LENGTH]},
    )
    return subscription


def remove_subscription(*, user, endpoint: str = "", pk: int | None = None) -> int:
    """Quita un dispositivo mío por ``endpoint`` (lo conoce el service worker) o por ``pk`` (lista
    «Mis dispositivos»). Devuelve cuántos se borraron (0 si no existía o no era mío)."""
    subscriptions = PushSubscription.objects.filter(user=user)
    if pk is not None:
        subscriptions = subscriptions.filter(pk=pk)
    elif endpoint:
        subscriptions = subscriptions.filter(endpoint=endpoint.strip())
    else:
        return 0
    deleted, _ = subscriptions.delete()
    return deleted
