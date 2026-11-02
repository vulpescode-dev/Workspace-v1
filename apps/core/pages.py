"""Páginas generales del sitio: Calendario, Ayuda, Términos y Privacidad (por ahora sin datos propios).

Términos y Privacidad son públicas: se enlazan desde el inicio de sesión y deben poder leerse antes de
entrar. Ayuda pide sesión, como el resto de la app. El texto legal lo redacta o revisa el área Legal.
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import render

from apps.accounts.views.common import shell_context


def _context(request, active_nav: str) -> dict:
    shell = shell_context(request) if request.user.is_authenticated else {}
    return {**shell, "active_nav": active_nav}


@login_required
def calendar_page(request):
    """Calendario (solo frontend por ahora): aún no hay fechas del sistema; la página lo avisa."""
    return render(request, "pages/calendar/index.html", _context(request, "calendar"))


@login_required
def help_page(request):
    return render(request, "pages/help/index.html", _context(request, "help"))


def terms(request):
    return render(request, "pages/legal/terms.html", _context(request, "terms"))


def privacy(request):
    return render(request, "pages/legal/privacy.html", _context(request, "privacy"))


def showcase(request):
    """Solo en desarrollo (/showcase/): la presentación servida por el mismo Django que la app.

    Así teléfono, QR y enlaces usan la misma dirección con la que se abrió (localhost o la IP de la
    PC en DJANGO_ALLOWED_HOSTS) sin editar el archivo, y no hace falta exponer la carpeta con otro servidor.
    """
    response = FileResponse(open(settings.BASE_DIR / "showcase.html", "rb"), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "no-store"   # cada cambio al archivo se ve al recargar
    return response
