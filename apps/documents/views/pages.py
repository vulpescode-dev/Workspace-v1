from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.views.common import shell_context


@login_required
def documents(request):
    """Documentos (shell). Por ahora solo la página; el módulo está pendiente (ver docs/backlog.md)."""
    return render(request, "pages/documents/index.html", {**shell_context(request), "active_nav": "documents"})
