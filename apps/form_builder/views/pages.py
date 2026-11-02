from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.views.common import shell_context


@login_required
def forms_home(request):
    """Formularios (shell). Por ahora solo la página; los modelos ya existen y faltan vistas y API."""
    return render(request, "pages/forms/index.html", {**shell_context(request), "active_nav": "forms"})
