from rest_framework import serializers

from apps.catalogs.models import Emoji


class EmojiSerializer(serializers.ModelSerializer):
    svg_url = serializers.CharField(read_only=True)
    lottie_url = serializers.CharField(read_only=True)

    class Meta:
        model = Emoji
        fields = ["code", "char", "label", "svg_url", "lottie_url", "is_active"]
        read_only_fields = fields
