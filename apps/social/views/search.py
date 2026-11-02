from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.views.common import shell_context


@login_required
def search(request):
    """Buscar (shell). La búsqueda general llega en una etapa posterior; con el filtro «Personas» ya
    lleva al directorio."""
    context = {**shell_context(request), "active_nav": "search"}
    return render(request, "pages/search/index.html", context)
