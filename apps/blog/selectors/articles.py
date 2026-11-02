"""Consultas de lectura del blog.

- Cualquier persona autenticada y activa lee los artículos **publicados** cuya fecha de
  publicación ya llegó (los programados aparecen solos cuando llega su fecha).
- Quien escribió un artículo también ve sus borradores y programados.
- Lo eliminado (borrado suave) nunca se devuelve.
"""
from django.db.models import Count, Prefetch, Q
from django.utils import timezone

from apps.blog.models import Article, ArticleCategory, ArticleComment, ArticleReaction

LIVE_COMMENTS = Q(comments__deleted_at__isnull=True)


def _published_now() -> Q:
    return Q(status=Article.Status.PUBLISHED, published_at__lte=timezone.now())


def readable_articles(user):
    """Artículos que ``user`` puede abrir: los publicados y los suyos (borradores incluidos)."""
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return Article.objects.none()
    return (
        Article.objects.filter(deleted_at__isnull=True)
        .filter(_published_now() | Q(author=user))
        .select_related("author", "category")
        .annotate(comments_count=Count("comments", filter=LIVE_COMMENTS))
        # Explícito: Django no aplica Meta.ordering en consultas con GROUP BY (annotate + Count).
        .order_by("-published_at", "-id")
    )


def filter_articles(qs, user, *, mine: bool = False, category: str = "", author: int | None = None,
                    slug: str = "", query: str = ""):
    """Lista: por omisión solo publicados; ``mine`` = los míos en cualquier estado."""
    qs = qs.filter(author=user) if mine else qs.filter(_published_now())
    if category:
        qs = qs.filter(category__slug=category)
    if author:
        qs = qs.filter(author_id=author)
    if slug:
        qs = qs.filter(slug=slug)
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(excerpt__icontains=query))
    return qs


def active_categories():
    return ArticleCategory.objects.filter(is_active=True)


def article_comments(article):
    """Hilos de ``article``: comentarios raíz (más antiguos primero) con sus respuestas vivas en
    ``live_replies``. Un raíz eliminado solo aparece si aún tiene respuestas vivas."""
    live_replies = Prefetch(
        "replies",
        queryset=ArticleComment.objects.filter(deleted_at__isnull=True).select_related("author").order_by("created_at", "id"),
        to_attr="live_replies",
    )
    return (
        ArticleComment.objects.filter(article=article, parent__isnull=True)
        .annotate(live_replies_count=Count("replies", filter=Q(replies__deleted_at__isnull=True)))
        .filter(Q(deleted_at__isnull=True) | Q(live_replies_count__gt=0))
        .select_related("author")
        .prefetch_related(live_replies)
        .order_by("created_at", "id")
    )


def live_comments_count(article) -> int:
    return ArticleComment.objects.filter(article=article, deleted_at__isnull=True).count()


def visible_comment(user, pk: int) -> ArticleComment | None:
    """Comentario vivo cuyo artículo puede abrir ``user``."""
    comment = ArticleComment.objects.select_related("article").filter(pk=pk, deleted_at__isnull=True).first()
    if comment is None or not readable_articles(user).filter(pk=comment.article_id).exists():
        return None
    return comment


def article_reactions(article):
    """Quién reaccionó a ``article`` («Ver todo»), más recientes primero."""
    return ArticleReaction.objects.filter(article=article).select_related("user", "emoji").order_by("-updated_at", "-id")
