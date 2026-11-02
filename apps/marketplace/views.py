from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.views.common import shell_context


@login_required
def marketplace(request):
    """Marketplace (shell). Por ahora solo la página; las publicaciones ya están en ``/api/marketplace/listings/``."""
    return render(request, "pages/marketplace/index.html", {**shell_context(request), "active_nav": "marketplace"})
