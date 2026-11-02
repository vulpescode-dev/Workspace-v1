"""Genera los íconos de la app (PWA, iPhone y favicon) a partir del logo del encabezado.

    python manage.py runscript make_icons

El logo es el glifo ``bxl-xing`` de Boxicons (el mismo ``<i class="bx bxl-xing">`` del header), en azul
de marca sobre fondo blanco. Se dibuja a 4× y se reduce para que los bordes salgan suaves. Solo hace
falta volver a correrlo si cambia el logo o el color; los PNG resultantes se guardan en el repositorio.
"""
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

BRAND = (0, 102, 204)            # #0066CC (primario de bootstrap-theme.css)
BACKGROUND = (255, 255, 255)
GLYPH = chr(0xEF38)              # .bxl-xing:before { content: "\ef38" } en boxicons.min.css
SCALE = 4

ICONS_DIR = Path(settings.BASE_DIR, "static", "assets", "img", "icons")
FONT = Path(settings.BASE_DIR, "static", "assets", "vendor", "boxicons", "fonts", "boxicons.woff2")

# nombre → (tamaño en px, qué parte del lado ocupa el logo)
ICONS = {
    "icon-192.png": (192, 0.62),
    "icon-512.png": (512, 0.62),
    # Maskable: Android recorta con círculos o gotas; el logo cabe en la zona segura (círculo del 80 %).
    "icon-maskable-512.png": (512, 0.46),
    "apple-touch-icon.png": (180, 0.60),
    "favicon-32.png": (32, 0.84),
}


def render(size: int, ratio: float) -> Image.Image:
    big = size * SCALE
    image = Image.new("RGB", (big, big), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT), int(big * ratio))
    left, top, right, bottom = draw.textbbox((0, 0), GLYPH, font=font)
    x = (big - (right - left)) / 2 - left       # centrado por la caja real del glifo, no por la línea base
    y = (big - (bottom - top)) / 2 - top
    draw.text((x, y), GLYPH, font=font, fill=BRAND)
    return image.resize((size, size), Image.LANCZOS)


def run(*args):
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for name, (size, ratio) in ICONS.items():
        render(size, ratio).save(ICONS_DIR / name, optimize=True)
        print(f"  + {name} ({size}×{size})")
    # favicon.ico con varios tamaños (pestaña del navegador, accesos directos de Windows).
    favicon = render(48, 0.84)
    favicon.save(ICONS_DIR / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("  + favicon.ico (16, 32, 48)")
    print(f"Listo: {ICONS_DIR}")
