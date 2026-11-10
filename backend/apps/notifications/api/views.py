from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import SafePageNumberPagination
from apps.notifications.selectors.notifications import my_notifications, my_push_subscriptions, unread_count
from apps.notifications.services.notifications import delete_notification, mark_all_read, set_read
from apps.notifications.services.push import remove_subscription, save_subscription

from .serializers import (
    NotificationSerializer, PushSubscribeSerializer, PushSubscriptionSerializer, PushUnsubscribeSerializer,
    ReadInputSerializer,
)


def _as_drf_error(exc: DjangoValidationError) -> ValidationError:
    return ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)


# --- Notificaciones ------------------------------------------------------------

class NotificationListView(generics.ListAPIView):
    """GET ``?page=&page_size=``: mis notificaciones, más recientes primero (25 por página, máximo 25).
    ``?unread=1``: solo las no leídas."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = SafePageNumberPagination

    def get_queryset(self):
        qs = my_notifications(self.request.user)
        if self.request.query_params.get("unread") == "1":
            qs = qs.filter(read_at__isnull=True)
        return qs


class NotificationDetailView(APIView):
    """GET: una notificación mía. PATCH ``{"is_read": true|false}``: marcar leída / no leída.
    DELETE: eliminarla. Las ajenas o inexistentes responden 404."""

    permission_classes = [IsAuthenticated]

    def get_notification(self):
        return get_object_or_404(my_notifications(self.request.user), pk=self.kwargs["pk"])

    def get(self, request, pk):
        return Response(NotificationSerializer(self.get_notification()).data)

    def patch(self, request, pk):
        notification = self.get_notification()
        data = ReadInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        set_read(user=request.user, notification=notification, read=data.validated_data["is_read"])
        return Response(NotificationSerializer(notification).data)

    def delete(self, request, pk):
        delete_notification(user=request.user, notification=self.get_notification())
        return Response(status=status.HTTP_204_NO_CONTENT)


class UnreadCountView(APIView):
    """GET ``{"unread"}``: cuántas notificaciones no he leído (el globito de la campana)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"unread": unread_count(request.user)})


class MarkAllReadView(APIView):
    """POST: marca todas mis notificaciones como leídas. Responde ``{"updated", "unread"}``."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = mark_all_read(user=request.user)
        return Response({"updated": updated, "unread": unread_count(request.user)})


# --- Push (PWA) ----------------------------------------------------------------

class PushConfigView(APIView):
    """GET ``{"enabled", "public_key"}``: llave pública VAPID para ``PushManager.subscribe()``.
    ``enabled: false`` si el servidor aún no tiene llaves (``WEBPUSH_VAPID_PUBLIC_KEY`` en .env)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        public_key = settings.WEBPUSH_VAPID_PUBLIC_KEY
        return Response({"enabled": bool(public_key), "public_key": public_key})


class PushSubscriptionListView(generics.ListAPIView):
    """GET ``?page=&page_size=``: mis dispositivos con push activo (sin llaves), paginado como toda la API.
    POST: registra este dispositivo con lo que da ``subscription.toJSON()``
    (``{"endpoint", "keys": {"p256dh", "auth"}}``). Idempotente: el mismo endpoint se actualiza."""

    serializer_class = PushSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return my_push_subscriptions(self.request.user)

    def post(self, request):
        data = PushSubscribeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            subscription = save_subscription(
                user=request.user, endpoint=data.validated_data["endpoint"],
                p256dh=data.validated_data["keys"]["p256dh"], auth=data.validated_data["keys"]["auth"],
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(PushSubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class PushSubscriptionDetailView(APIView):
    """DELETE: quita uno de mis dispositivos (desde «Mis dispositivos»). Ajeno o inexistente: 404."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if not remove_subscription(user=request.user, pk=pk):
            raise Http404
        return Response(status=status.HTTP_204_NO_CONTENT)


class PushUnsubscribeView(APIView):
    """POST ``{"endpoint"}``: quita la suscripción de este navegador (el service worker conoce el
    endpoint, no el id). Responde 204 aunque ya no existiera: el resultado es el mismo."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = PushUnsubscribeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        remove_subscription(user=request.user, endpoint=data.validated_data["endpoint"])
        return Response(status=status.HTTP_204_NO_CONTENT)
