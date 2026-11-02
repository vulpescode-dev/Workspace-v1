from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.accounts.selectors.profile import avatar_url
from apps.social.selectors import demo


def _display_name(user) -> str:
    return user.first_name or user.username


def _initials(name: str) -> str:
    parts = [p for p in name.replace("_", " ").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


def _greeting() -> str:
    """Saludo según la hora local (no asume ninguna identidad)."""
    hour = timezone.localtime().hour
    if hour < 12:
        return "Buenos días"
    return "Buenas tardes" if hour < 19 else "Buenas noches"


@login_required
@ensure_csrf_cookie
def home(request):
    """Portada (shell). Requiere sesión: sin ella lleva al inicio de sesión y regresa aquí. Las publicaciones NO se renderizan aquí: el navegador las
    pide a ``/api/social/posts/`` y las pinta, igual que lo hará un frontend separado.
    """
    name = _display_name(request.user)
    context = {
        "active_nav": "home",
        "greeting": _greeting(),
        "display_name": name,
        "display_initials": _initials(name),
        "display_avatar_url": avatar_url(request.user),
        "categories": demo.DEMO_CATEGORIES,
    }
    return render(request, "pages/home/index.html", context)
