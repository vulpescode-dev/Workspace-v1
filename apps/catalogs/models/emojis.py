"""Emojis autorizados para reaccionar (Noto Animated Emoji).

Los archivos viven en ``static/assets/emoji/<code>/`` (``emoji.svg`` y ``lottie.json``);
la tabla solo guarda el catálogo. La carga inicial sale de ``apps/catalogs/data/emojis.json``
mediante ``python manage.py load_catalogs``.
"""
from django.conf import settings
from django.db import models
from django.templatetags.static import static

EMOJI_STATIC_DIR = "assets/emoji"


class Emoji(models.Model):
    code = models.SlugField("código", max_length=64, unique=True)
    codepoint = models.CharField("codepoint Unicode", max_length=32, help_text="Formato Noto, p. ej. 1f600 o 2764_fe0f.")
    char = models.CharField("carácter", max_length=16)
    label = models.CharField("etiqueta", max_length=80)
    position = models.PositiveSmallIntegerField("orden", default=0)
    is_active = models.BooleanField(
        "activo", default=True,
        help_text="Desactivado: deja de aparecer en el selector, pero las reacciones existentes se conservan.",
    )

    class Meta:
        verbose_name = "emoji"
        verbose_name_plural = "emojis"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"{self.char} {self.label}"

    @property
    def svg_url(self) -> str:
        return static(f"{EMOJI_STATIC_DIR}/{self.code}/emoji.svg")

    @property
    def lottie_url(self) -> str:
        return static(f"{EMOJI_STATIC_DIR}/{self.code}/lottie.json")


class BaseReaction(models.Model):
    """Base de las reacciones de cada app (``social.PostReaction``, luego blogs, marketplace…).

    Cada app hereda y agrega la relación con su objeto y sus propias restricciones.
    ``PROTECT``: un emoji con reacciones no se borra; se desactiva.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s_set",
        verbose_name="usuario",
    )
    emoji = models.ForeignKey(Emoji, on_delete=models.PROTECT, related_name="+", verbose_name="emoji")
    created_at = models.DateTimeField("creada el", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada el", auto_now=True)

    class Meta:
        abstract = True
