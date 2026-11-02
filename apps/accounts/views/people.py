from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from .common import shell_context


@login_required
@ensure_csrf_cookie
def people(request):
    """Directorio de personas (shell). Las tarjetas llegan de ``/api/accounts/users/?search=&page=``.

    ``?q=`` precarga la búsqueda (permite compartir o recargar una búsqueda).
    """
    context = {**shell_context(request), "active_nav": "people", "q": request.GET.get("q", "")[:100]}
    return render(request, "pages/people/index.html", context)
