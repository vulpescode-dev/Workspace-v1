from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.views.common import shell_context


@login_required
def blog(request):
    """Noticias (shell). Por ahora solo la página; los artículos ya están en ``/api/blog/articles/``."""
    return render(request, "pages/blog/index.html", {**shell_context(request), "active_nav": "blog"})
