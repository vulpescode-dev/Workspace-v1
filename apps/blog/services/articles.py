"""Operaciones que crean o modifican artículos del blog.

- Publicar requiere el permiso de negocio ``blog.articles.create`` (un superusuario lo tiene).
- Editar y eliminar: solo quien escribió el artículo.
- El HTML del contenido lo limpia el modelo al guardar (``services.html``).
- La portada es una imagen WebP validada con ``apps.core.uploads`` y se guarda como
  ``blog/articles/<id>/cover-<marca de tiempo>.webp`` (el nombre cambia al reemplazarla, así el
  navegador no muestra la anterior en caché).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.services.permissions import has_permission
from apps.blog.models import Article, ArticleCategory
from apps.core.uploads import KIND_IMAGE, check_media_upload

CREATE_PERMISSION = "blog.articles.create"
TITLE_MAX_LENGTH = 200
EXCERPT_MAX_LENGTH = 300
BODY_MAX_LENGTH = 100_000
UNSET = object()   # al editar: distingue «no se mandó» de «se mandó vacío»


def can_write_articles(user) -> bool:
    return has_permission(user, CREATE_PERMISSION)


def _clean_title(title: str) -> str:
    title = " ".join((title or "").split())
    if not title:
        raise ValidationError({"title": "Escribe un título."})
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError({"title": f"Máximo {TITLE_MAX_LENGTH} caracteres."})
    return title


def _clean_excerpt(excerpt: str) -> str:
    excerpt = " ".join((excerpt or "").split())
    if len(excerpt) > EXCERPT_MAX_LENGTH:
        raise ValidationError({"excerpt": f"Máximo {EXCERPT_MAX_LENGTH} caracteres."})
    return excerpt


def _clean_body(body: str) -> str:
    body = body or ""
    if len(body) > BODY_MAX_LENGTH:
        raise ValidationError({"body": "El contenido es demasiado largo."})
    return body


def _clean_category(category_id) -> ArticleCategory | None:
    if category_id in (None, ""):
        return None
    category = ArticleCategory.objects.filter(pk=category_id, is_active=True).first()
    if category is None:
        raise ValidationError({"category": "Categoría no válida."})
    return category


def _clean_status(status) -> str:
    status = status or Article.Status.DRAFT
    if status not in Article.Status.values:
        raise ValidationError({"status": "Estado no válido."})
    return status


def _check_cover(upload):
    try:
        info = check_media_upload(upload)
    except ValidationError as exc:
        raise ValidationError({"cover": exc.messages[0]}) from exc
    if info.kind != KIND_IMAGE:
        raise ValidationError({"cover": "La portada debe ser una imagen."})
    return info


def _save_cover(article: Article, upload, info) -> None:
    if article.cover:
        article.cover.delete(save=False)
    stamp = timezone.now().strftime("%Y%m%d%H%M%S")
    article.cover.save(f"cover-{stamp}{info.extension}", upload, save=False)
    article.save(update_fields=["cover", "updated_at"])


def create_article(*, author, title: str, body: str = "", excerpt: str = "", category_id=None,
                   status: str | None = None, published_at=None, cover=None) -> Article:
    """Crea un artículo (borrador por omisión). Publicado sin fecha = ahora; con fecha futura = programado."""
    if not can_write_articles(author):
        raise PermissionDenied("No tienes permiso para escribir artículos.")
    title, excerpt, body = _clean_title(title), _clean_excerpt(excerpt), _clean_body(body)
    category, status = _clean_category(category_id), _clean_status(status)
    info = _check_cover(cover) if cover else None

    with transaction.atomic():
        article = Article.objects.create(
            author=author, title=title, excerpt=excerpt, body=body, category=category, status=status,
            published_at=published_at,
        )
        if info:
            _save_cover(article, cover, info)
    return article


def _ensure_author(user, article: Article) -> None:
    if article.author_id != user.pk:
        raise PermissionDenied("Solo quien escribió el artículo puede cambiarlo.")


def edit_article(*, user, article: Article, title=UNSET, body=UNSET, excerpt=UNSET, category_id=UNSET,
                 status=UNSET, published_at=UNSET, cover=UNSET) -> Article:
    """Cambia solo los campos que se manden. ``cover=None`` quita la portada; un archivo la reemplaza."""
    _ensure_author(user, article)
    if title is not UNSET:
        article.title = _clean_title(title)
    if body is not UNSET:
        article.body = _clean_body(body)
    if excerpt is not UNSET:
        article.excerpt = _clean_excerpt(excerpt)
    if category_id is not UNSET:
        article.category = _clean_category(category_id)
    if status is not UNSET:
        article.status = _clean_status(status)
    if published_at is not UNSET:
        article.published_at = published_at
    info = _check_cover(cover) if cover not in (UNSET, None) else None

    with transaction.atomic():
        article.save()
        if info:
            _save_cover(article, cover, info)
        elif cover is None and article.cover:
            article.cover.delete(save=False)
            article.save(update_fields=["cover", "updated_at"])
    return article


def delete_article(*, user, article: Article) -> None:
    """Borrado suave: deja de verse (con sus comentarios y reacciones)."""
    _ensure_author(user, article)
    article.soft_delete()
