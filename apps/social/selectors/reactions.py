"""Lectura de reacciones: resúmenes (pastillas con contador) y lista de quién reaccionó.

El resumen lo arma ``catalogs.selectors.reactions`` (mismo formato en toda la app).
"""
from apps.catalogs.selectors.reactions import reaction_summaries_for
from apps.social.models import CommentReaction, PostReaction


def reaction_summaries(post_ids, user) -> dict[int, dict]:
    return reaction_summaries_for(PostReaction, "post", post_ids, user)


def comment_reaction_summaries(comment_ids, user) -> dict[int, dict]:
    return reaction_summaries_for(CommentReaction, "comment", comment_ids, user)


def post_reactions(post):
    """Quién reaccionó a ``post`` (para «Ver todo»), más recientes primero."""
    return (
        PostReaction.objects.filter(post=post)
        .select_related("user", "emoji")
        .order_by("-updated_at", "-id")
    )
