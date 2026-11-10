"""Consultas de estados.

Visibilidad (por ahora): los estados vivos de **toda la empresa**, como una publicación «Toda la empresa».
Quién puede ver (todos / solo seguidores) queda por decidir; la regla vive solo aquí.
"""
from collections import OrderedDict

from django.db.models import Count, Exists, OuterRef
from django.utils import timezone

from apps.social.models import Story, StoryView

TRAY_MAX_AUTHORS = 50


def live_stories(user):
    """Estados no vencidos ni eliminados de personas activas, con ``seen`` para ``user``."""
    if not user.is_authenticated or not user.is_active:
        return Story.objects.none()
    return (
        Story.objects.filter(deleted_at__isnull=True, expires_at__gt=timezone.now(), author__is_active=True)
        .select_related("author")
        .annotate(
            seen=Exists(StoryView.objects.filter(story=OuterRef("pk"), viewer=user)),
            views_count=Count("views", distinct=True),
        )
    )


def visible_story(user, pk: int) -> Story | None:
    return live_stories(user).filter(pk=pk).first()


def story_tray(user) -> list[dict]:
    """La fila de Inicio: un grupo por persona con sus estados (del más viejo al más nuevo).

    Orden: los míos primero; luego quien tiene estados sin ver; luego los ya vistos. Dentro de cada
    bloque, el estado más reciente primero (como Instagram).
    """
    groups: OrderedDict[int, dict] = OrderedDict()
    for story in live_stories(user).order_by("created_at", "id"):
        group = groups.setdefault(story.author_id, {"author": story.author, "stories": []})
        group["stories"].append(story)

    tray = []
    for group in groups.values():
        stories = group["stories"]
        is_mine = group["author"].pk == user.pk
        tray.append({
            **group,
            "is_mine": is_mine,
            "has_unseen": not is_mine and any(not s.seen for s in stories),
            "latest_at": stories[-1].created_at,
        })
    tray.sort(key=lambda g: g["latest_at"], reverse=True)
    tray.sort(key=lambda g: (not g["is_mine"], not g["has_unseen"]))   # estable: conserva lo reciente
    return tray[:TRAY_MAX_AUTHORS]


def story_viewers(story: Story):
    """Quién vio un estado (solo personas activas), lo más reciente primero. Solo para su autor."""
    return (
        StoryView.objects.filter(story=story, viewer__is_active=True)
        .select_related("viewer")
        .order_by("-viewed_at", "-id")
    )
