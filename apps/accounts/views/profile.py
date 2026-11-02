from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from .common import shell_context


@login_required
@ensure_csrf_cookie
def profile(request):
    """Perfil: ``/profile/`` (el mío) o ``/profile/?user_id=<id>`` (el de otra persona).

    La página es un *shell*: los datos del perfil y sus publicaciones llegan por la API
    (``/api/accounts/users/<id>/`` y ``/api/social/posts/?author=<id>``). Si el id no es válido
    se muestra el mío; si no existe, la API responde 404 y la página muestra el estado de error.
    """
    raw = request.GET.get("user_id", "")
    profile_id = int(raw) if raw.isdigit() else request.user.pk
    is_me = profile_id == request.user.pk
    context = {
        **shell_context(request),
        # «Perfil» del menú es el mío; el de un compañero se marca como «Personas».
        "active_nav": "profile" if is_me else "people",
        "profile_id": profile_id,
        "is_me": is_me,
        "feed_url": f"{reverse('social-api:post-list')}?author={profile_id}",
    }
    return render(request, "pages/profile/index.html", context)
