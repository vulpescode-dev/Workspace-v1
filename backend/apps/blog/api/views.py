from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.permissions import BLOG
from apps.blog.models import Article, ArticleReaction
from apps.blog.selectors.articles import (
    active_categories, article_comments, article_reactions, filter_articles, live_comments_count, readable_articles,
    visible_comment,
)
from apps.blog.services.articles import UNSET, can_write_articles, create_article, delete_article, edit_article
from apps.blog.services.comments import create_comment, delete_comment, edit_comment
from apps.blog.services.reactions import remove_reaction, set_reaction
from apps.catalogs.selectors.reactions import EMPTY_REACTIONS, reaction_summaries_for

from .serializers import (
    ArticleCategorySerializer, ArticleCommentSerializer, ArticleCommentThreadSerializer, ArticleDetailSerializer,
    ArticleInputSerializer, ArticleReactionSerializer, ArticleSerializer, CommentInputSerializer,
    ReactionInputSerializer,
)


def _as_drf_error(exc: DjangoValidationError) -> ValidationError:
    return ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)


def _summaries(article_ids, user) -> dict:
    return reaction_summaries_for(ArticleReaction, "article", article_ids, user)


def _get_article(request, pk) -> Article:
    return get_object_or_404(readable_articles(request.user), pk=pk)


# --- Artículos -----------------------------------------------------------------

class ArticleListCreateView(generics.ListAPIView):
    """GET: artículos publicados, más recientes primero, sin el contenido. Filtros opcionales:
    ``?category=<slug>``, ``?author=<id>``, ``?slug=<slug>``, ``?q=<texto>`` (título y resumen) y
    ``?mine=1`` (los míos en cualquier estado: borradores y programados incluidos).
    POST: crea un artículo (JSON, o multipart si lleva ``cover``). Requiere ``blog.articles.create``."""

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, BLOG]

    def get_queryset(self):
        params = self.request.query_params
        author = params.get("author", "")
        if author and not author.isdigit():
            raise ValidationError({"author": "Debe ser un id de usuario."})
        return filter_articles(
            readable_articles(self.request.user), self.request.user, mine=params.get("mine") == "1",
            category=params.get("category", ""), author=int(author) if author else None,
            slug=params.get("slug", ""), query=params.get("q", "").strip(),
        )

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        context = {**self.get_serializer_context(), "reaction_summaries": _summaries([a.pk for a in page], request.user)}
        return self.get_paginated_response(ArticleSerializer(page, many=True, context=context).data)

    def post(self, request):
        data = ArticleInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        fields = data.validated_data
        try:
            article = create_article(
                author=request.user, title=fields["title"], body=fields.get("body", ""),
                excerpt=fields.get("excerpt", ""), category_id=fields.get("category"), status=fields.get("status"),
                published_at=fields.get("published_at"), cover=request.FILES.get("cover"),
            )
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        article = readable_articles(request.user).get(pk=article.pk)
        return Response(ArticleDetailSerializer(article, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ArticleDetailView(APIView):
    """GET: un artículo completo (con ``body``). PATCH: edita los campos que se manden (solo autor;
    multipart para cambiar ``cover``, ``remove_cover: true`` para quitarla). DELETE: borrado suave
    (solo autor). Lo ajeno responde 403; lo inexistente, eliminado o borrador ajeno, 404."""

    permission_classes = [IsAuthenticated, BLOG]

    def respond(self, article):
        context = {"request": self.request, "reaction_summaries": _summaries([article.pk], self.request.user)}
        return Response(ArticleDetailSerializer(article, context=context).data)

    def get(self, request, pk):
        return self.respond(_get_article(request, pk))

    def patch(self, request, pk):
        article = _get_article(request, pk)
        data = ArticleInputSerializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        fields = dict(data.validated_data)
        remove_cover = fields.pop("remove_cover", False)
        if "category" in fields:
            fields["category_id"] = fields.pop("category")
        cover = request.FILES.get("cover") or (None if remove_cover else UNSET)
        try:
            edit_article(user=request.user, article=article, cover=cover, **fields)
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return self.respond(_get_article(request, pk))

    def delete(self, request, pk):
        delete_article(user=request.user, article=_get_article(request, pk))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ArticleCoverView(APIView):
    """GET: entrega la portada solo si el artículo se puede abrir (nunca rutas de /media/)."""

    permission_classes = [IsAuthenticated, BLOG]

    def get(self, request, pk):
        article = _get_article(request, pk)
        if not article.cover:
            raise Http404
        response = FileResponse(article.cover.open("rb"), content_type="image/webp")
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Disposition"] = "inline"
        response["Cache-Control"] = "private, max-age=86400"
        return response


class BlogPermissionsView(APIView):
    """GET ``{"can_write"}``: si la persona puede escribir artículos (para mostrar «Escribir»).
    La regla real la aplica el servidor al crear."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"can_write": can_write_articles(request.user)})


class CategoryListView(generics.ListAPIView):
    """GET: categorías activas (chips de filtro y formulario). Sin paginar: son pocas."""

    serializer_class = ArticleCategorySerializer
    permission_classes = [IsAuthenticated, BLOG]
    pagination_class = None

    def get_queryset(self):
        return active_categories()


# --- Reacciones ----------------------------------------------------------------

class ArticleReactionView(APIView):
    """Mi reacción en un artículo. PUT ``{"emoji": "<código>"}`` pone o cambia (una por persona);
    DELETE la quita. Ambas responden el resumen actualizado."""

    permission_classes = [IsAuthenticated, BLOG]

    def summary(self, article):
        return _summaries([article.pk], self.request.user).get(article.pk, EMPTY_REACTIONS)

    def put(self, request, pk):
        article = _get_article(request, pk)
        data = ReactionInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            set_reaction(user=request.user, article=article, emoji_code=data.validated_data["emoji"])
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(self.summary(article))

    def delete(self, request, pk):
        article = _get_article(request, pk)
        remove_reaction(user=request.user, article=article)
        return Response(self.summary(article))


class ArticleReactionListView(generics.ListAPIView):
    """GET: quién reaccionó al artículo («Ver todo»), paginado."""

    serializer_class = ArticleReactionSerializer
    permission_classes = [IsAuthenticated, BLOG]

    def get_queryset(self):
        return article_reactions(_get_article(self.request, self.kwargs["pk"]))


# --- Comentarios ---------------------------------------------------------------

class ArticleCommentListCreateView(generics.ListAPIView):
    """GET: hilos del artículo (comentario raíz + respuestas), más antiguos primero, paginado.
    POST ``{"body", "parent"?}``: comenta o responde (solo en publicados). Responde el comentario y ``comments_count``."""

    serializer_class = ArticleCommentThreadSerializer
    permission_classes = [IsAuthenticated, BLOG]

    def get_queryset(self):
        return article_comments(_get_article(self.request, self.kwargs["pk"]))

    def post(self, request, pk):
        article = _get_article(request, pk)
        data = CommentInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            comment = create_comment(
                author=request.user, article=article, body=data.validated_data["body"],
                parent_id=data.validated_data.get("parent"),
            )
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        payload = {
            **ArticleCommentSerializer(comment, context={"request": request}).data,
            "comments_count": live_comments_count(article),
        }
        return Response(payload, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    """PATCH ``{"body"}``: edita (solo autor). DELETE: borrado suave (solo autor); responde
    ``comments_count`` y ``keep_placeholder`` (tiene respuestas vivas: sigue como «Comentario eliminado»)."""

    permission_classes = [IsAuthenticated, BLOG]

    def get_comment(self):
        comment = visible_comment(self.request.user, self.kwargs["pk"])
        if comment is None:
            raise Http404
        return comment

    def patch(self, request, pk):
        comment = self.get_comment()
        data = CommentInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            edit_comment(user=request.user, comment=comment, body=data.validated_data["body"])
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(ArticleCommentSerializer(comment, context={"request": request}).data)

    def delete(self, request, pk):
        comment = self.get_comment()
        delete_comment(user=request.user, comment=comment)
        keep = comment.parent_id is None and comment.replies.filter(deleted_at__isnull=True).exists()
        return Response({"comments_count": live_comments_count(comment.article), "keep_placeholder": keep})
