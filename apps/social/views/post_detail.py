from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.accounts.views.common import shell_context


@login_required
@ensure_csrf_cookie
def post_detail(request, pk):
    """Una publicación sola (destino de las notificaciones). Shell: el post llega por la API
    (``/api/social/posts/?id=<pk>``); si ya no existe o no es visible, se ve el estado vacío.

    ``?comments=1`` abre los comentarios al cargar y ``?comment=<id>`` resalta ese comentario.
    """
    comment = request.GET.get("comment", "")
    context = {
        **shell_context(request),
        "active_nav": "post",
        "post_id": pk,
        "feed_url": f"{reverse('social-api:post-list')}?id={pk}",
        "open_comments": request.GET.get("comments") == "1",
        "highlight_comment": comment if comment.isdigit() else "",
    }
    return render(request, "pages/posts/detail.html", context)
