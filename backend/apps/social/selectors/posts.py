"""Consultas de lectura de publicaciones y comentarios.

La visibilidad se decide aquí, en el servidor (nunca en el frontend):
- «Toda la empresa»: cualquier persona autenticada y activa.
- «Solo seguidores»: el autor y quienes lo siguen.
Lo eliminado (borrado suave, ``deleted_at``) nunca se devuelve.
"""
from django.db.models import Count, Exists, OuterRef, Prefetch, Q

from apps.social.models import Follow, Post, PostAttachment, PostComment

LIVE_COMMENTS = Q(comments__deleted_at__isnull=True)


def visible_posts(user):
    """Publicaciones que ``user`` puede ver, con autor, adjuntos y número de comentarios vivos."""
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return Post.objects.none()
    i_follow_author = Exists(Follow.objects.filter(follower=user, following=OuterRef("author")))
    qs = (
        Post.objects.filter(deleted_at__isnull=True)
        .filter(Q(audience=Post.Audience.COMPANY) | Q(author=user) | (Q(audience=Post.Audience.FOLLOWERS) & i_follow_author))
        .select_related("author")
        .prefetch_related("attachments")
        .annotate(comments_count=Count("comments", filter=LIVE_COMMENTS))
        # Explícito: Django no aplica Meta.ordering en consultas con GROUP BY (annotate + Count).
        .order_by("-created_at", "-id")
    )
    return qs


def visible_attachment(user, pk: int) -> PostAttachment | None:
    """Un adjunto solo se entrega si su publicación es visible para ``user``."""
    attachment = PostAttachment.objects.filter(pk=pk).first()
    if attachment is None or not visible_posts(user).filter(pk=attachment.post_id).exists():
        return None
    return attachment


def live_comments_count(post) -> int:
    return PostComment.objects.filter(post=post, deleted_at__isnull=True).count()


def post_comments(post):
    """Hilos de ``post``: comentarios raíz (más antiguos primero) con sus respuestas vivas en ``live_replies``.

    Un comentario raíz eliminado solo aparece si aún tiene respuestas vivas (se muestra como
    «Comentario eliminado»).
    """
    live_replies = Prefetch(
        "replies",
        queryset=PostComment.objects.filter(deleted_at__isnull=True).select_related("author").order_by("created_at", "id"),
        to_attr="live_replies",
    )
    return (
        PostComment.objects.filter(post=post, parent__isnull=True)
        .annotate(live_replies_count=Count("replies", filter=Q(replies__deleted_at__isnull=True)))
        .filter(Q(deleted_at__isnull=True) | Q(live_replies_count__gt=0))
        .select_related("author")
        .prefetch_related(live_replies)
        .order_by("created_at", "id")
    )


def visible_comment(user, pk: int) -> PostComment | None:
    """Comentario vivo cuya publicación es visible para ``user``."""
    comment = PostComment.objects.select_related("post").filter(pk=pk, deleted_at__isnull=True).first()
    if comment is None or not visible_posts(user).filter(pk=comment.post_id).exists():
        return None
    return comment


def author_photos(user, author_id: int):
    """Imágenes de las publicaciones visibles de ``author_id`` (perfil → «Fotos»), más recientes primero."""
    posts = visible_posts(user).filter(author_id=author_id).values("pk")
    return (
        PostAttachment.objects.filter(post__in=posts, kind=PostAttachment.Kind.IMAGE)
        .order_by("-post__created_at", "-post_id", "position", "id")
    )
