"""Imágenes de relleno para los scripts (WebP, generadas con Pillow; no se descarga nada).

Pasan la misma validación que una foto real (``apps.core.uploads``): WebP de verdad y dentro
de los límites de tamaño.
"""
import io
import random
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Pares de colores (arriba → abajo) para los degradados.
PALETTES = [
    ("#0066cc", "#7cc4ff"), ("#f4c600", "#ff7a59"), ("#22c55e", "#0e7490"), ("#7c3aed", "#ec4899"),
    ("#0f172a", "#334155"), ("#f97316", "#facc15"), ("#06b6d4", "#3b82f6"), ("#be123c", "#fb7185"),
    ("#14532d", "#84cc16"), ("#1e3a8a", "#a855f7"),
]
SIZES = [(1600, 1000), (1200, 1200), (1000, 1350), (1600, 900)]
# Montserrat del proyecto: la fuente por defecto de Pillow (Aileron) no trae acentos ni ñ («Le□n»).
FONT = Path(settings.BASE_DIR, "static", "assets", "fonts", "montserrat", "montserrat-latin-700-normal.woff2")


def _hex(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size)


def _to_upload(image: Image.Image, name: str) -> SimpleUploadedFile:
    buffer = io.BytesIO()
    image.save(buffer, "WEBP", quality=82)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/webp")


def photo(rng: random.Random, caption: str = "", name: str = "foto.webp", size=None) -> SimpleUploadedFile:
    """Imagen tipo «foto»: degradado, formas suaves desenfocadas y un texto opcional."""
    width, height = size or rng.choice(SIZES)
    top, bottom = (_hex(c) for c in rng.choice(PALETTES))
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        t = y / max(height - 1, 1)
        draw.line([(0, y), (width, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))

    shapes = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shape_draw = ImageDraw.Draw(shapes)
    for _ in range(rng.randint(4, 8)):
        r = rng.randint(min(width, height) // 10, min(width, height) // 3)
        x, y = rng.randint(-r, width), rng.randint(-r, height)
        shape_draw.ellipse([x, y, x + 2 * r, y + 2 * r], fill=(255, 255, 255, rng.randint(25, 70)))
    image = Image.alpha_composite(image.convert("RGBA"), shapes.filter(ImageFilter.GaussianBlur(24))).convert("RGB")

    if caption:
        draw = ImageDraw.Draw(image)
        font = _font(max(width // 18, 28))
        box = draw.textbbox((0, 0), caption, font=font)
        x, y = (width - (box[2] - box[0])) // 2, height - (box[3] - box[1]) - height // 10
        draw.text((x + 3, y + 3), caption, font=font, fill=(0, 0, 0))
        draw.text((x, y), caption, font=font, fill=(255, 255, 255))
    return _to_upload(image, name)


def avatar(initials: str, color: str, name: str = "avatar.webp") -> SimpleUploadedFile:
    """Foto de perfil cuadrada con iniciales sobre un color."""
    size = 512
    image = Image.new("RGB", (size, size), _hex(color))
    draw = ImageDraw.Draw(image)
    font = _font(200)
    box = draw.textbbox((0, 0), initials, font=font)
    draw.text(((size - (box[2] - box[0])) // 2 - box[0], (size - (box[3] - box[1])) // 2 - box[1]),
              initials, font=font, fill=(255, 255, 255))
    return _to_upload(image, name)
