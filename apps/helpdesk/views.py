from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.views.common import shell_context


@login_required
def helpdesk(request):
    """Mesa de ayuda (shell). Por ahora solo la página; la API ya existe (ver docs/api.md)."""
    return render(request, "pages/helpdesk/index.html", {**shell_context(request), "active_nav": "helpdesk"})
