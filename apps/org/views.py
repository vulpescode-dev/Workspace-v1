from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.views.common import shell_context


@login_required
def org_chart(request):
    """Organigrama (shell), pestaña junto al directorio de Personas. Los datos llegan de ``/api/org/chart/``."""
    return render(request, "pages/people/org_chart.html", {**shell_context(request), "active_nav": "people"})
