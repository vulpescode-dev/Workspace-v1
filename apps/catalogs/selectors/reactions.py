"""Resumen de reacciones de cualquier modelo que herede de ``BaseReaction`` (posts, artículos…).

El resumen es el mismo en toda la app: ``{"reactions": [{"emoji", "count"}], "total", "mine"}``.
"""
from collections import defaultdict

from django.db.models import Count, Min, Q

EMPTY_REACTIONS = {"reactions": [], "total": 0, "mine": None}


def reaction_summaries_for(model, fk: str, object_ids, user) -> dict[int, dict]:
    """Resumen por objeto en UNA consulta. Orden: más usadas primero; a igualdad, la que llegó antes.

    ``fk`` es el nombre del campo que apunta al objeto (``"post"``, ``"article"``…).
    """
    object_ids = list(object_ids)
    summaries = {pk: {"reactions": [], "total": 0, "mine": None} for pk in object_ids}
    if not object_ids:
        return summaries

    user_id = user.pk if getattr(user, "is_authenticated", False) else None
    key = f"{fk}_id"
    rows = (
        model.objects.filter(**{f"{key}__in": object_ids})
        .values(key, "emoji__code")
        .annotate(count=Count("id"), first=Min("created_at"), mine=Count("id", filter=Q(user_id=user_id)))
        .order_by(key, "-count", "first")
    )
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[key]].append({"emoji": row["emoji__code"], "count": row["count"]})
        if row["mine"]:
            summaries[row[key]]["mine"] = row["emoji__code"]
    for pk, reactions in grouped.items():
        summaries[pk]["reactions"] = reactions
        summaries[pk]["total"] = sum(r["count"] for r in reactions)
    return summaries
