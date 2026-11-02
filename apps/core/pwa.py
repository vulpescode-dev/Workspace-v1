"""Manifest de la app web (PWA): nombre, colores e íconos para «Instalar» / «Agregar a pantalla de inicio».

Se sirve desde Django (``/manifest.webmanifest``) y no como archivo estático para que las rutas de los
íconos salgan de ``static()``: en producción los estáticos llevan hash en el nombre. Es público porque
el navegador lo pide sin cookies. Se enlaza en ``base.html`` (todas las páginas): el navegador solo
ofrece instalar si encuentra el manifest en la página donde estás.

Los íconos se generan con ``python manage.py runscript make_icons`` (logo del encabezado, azul sobre blanco).
"""
from django.http import JsonResponse
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

ICONS = "assets/img/icons/"
THEME_COLOR = "#0066cc"          # primario de la marca (igual que <meta name="theme-color">)
BACKGROUND_COLOR = "#f5f6fa"     # fondo de la app (--ws-page-bg): pantalla de carga al abrirla instalada


def _shortcut(name: str, url: str, description: str) -> dict:
    return {"name": name, "short_name": name, "url": url, "description": description,
            "icons": [{"src": static(ICONS + "icon-192.png"), "sizes": "192x192", "type": "image/png"}]}


@require_GET
@cache_control(max_age=60 * 60 * 24)
def manifest(request):
    data = {
        "id": "/",
        "name": "Workspace",
        "short_name": "Workspace",
        "description": "La intranet de la empresa: publicaciones, avisos, personas y herramientas internas.",
        "lang": "es-MX",
        "dir": "ltr",
        "start_url": reverse("social:home"),
        "scope": "/",
        "display": "standalone",
        "theme_color": THEME_COLOR,
        "background_color": BACKGROUND_COLOR,
        "categories": ["business", "productivity", "social"],
        "icons": [
            {"src": static(ICONS + "icon-192.png"), "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": static(ICONS + "icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": static(ICONS + "icon-maskable-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
        # Accesos directos (mantener presionado el ícono instalado).
        "shortcuts": [
            _shortcut("Avisos", reverse("notifications"), "Comunicados y actividad de tus publicaciones"),
            _shortcut("Buscar", reverse("social:search"), "Personas, documentos, avisos y formularios"),
            _shortcut("Personas", reverse("people"), "Directorio de la empresa"),
            _shortcut("Calendario", reverse("calendar"), "Eventos y fechas importantes"),
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json", json_dumps_params={"ensure_ascii": False})
