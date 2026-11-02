from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.catalogs.models import Emoji

from .serializers import EmojiSerializer


class EmojiListView(generics.ListAPIView):
    """Catálogo de emojis (dato informativo, sin paginar).

    Incluye los desactivados (``is_active: false``) para que las reacciones existentes
    se sigan mostrando; el selector solo ofrece los activos.

    Pendiente: cachear esta respuesta (ver docs/backlog.md).
    """

    serializer_class = EmojiSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Emoji.objects.all()
