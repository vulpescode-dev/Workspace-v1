from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.accounts.views.common import shell_context


@login_required
@ensure_csrf_cookie
def notifications(request):
    """Mis notificaciones (shell). La lista llega de ``/api/notifications/`` (25 por página)."""
    return render(request, "pages/notifications/index.html", {**shell_context(request), "active_nav": "notifications"})
