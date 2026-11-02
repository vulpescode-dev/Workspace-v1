from rest_framework import serializers

from apps.notifications.models import Notification, PushSubscription


class NotificationSerializer(serializers.ModelSerializer):
    """Notificación lista para mostrar, venga de la app que venga."""

    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "title", "body", "icon", "color", "url", "created_at", "is_read", "read_at"]
        read_only_fields = fields

    def get_is_read(self, n) -> bool:
        return n.read_at is not None


class ReadInputSerializer(serializers.Serializer):
    is_read = serializers.BooleanField()


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """Un dispositivo en «Mis dispositivos». Las llaves nunca se devuelven."""

    class Meta:
        model = PushSubscription
        fields = ["id", "user_agent", "created_at", "last_used_at"]
        read_only_fields = fields


class PushKeysSerializer(serializers.Serializer):
    p256dh = serializers.CharField()
    auth = serializers.CharField()


class PushSubscribeSerializer(serializers.Serializer):
    """Lo que entrega ``subscription.toJSON()`` en el navegador."""

    endpoint = serializers.CharField()
    keys = PushKeysSerializer()


class PushUnsubscribeSerializer(serializers.Serializer):
    endpoint = serializers.CharField()
