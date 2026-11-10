from django.urls import reverse
from rest_framework import serializers

from apps.accounts.api.serializers import AuthorSerializer
from apps.blog.models import ARTICLE_COMMENT_BODY_MAX_LENGTH, Article, ArticleCategory, ArticleComment, ArticleReaction
from apps.blog.services.articles import BODY_MAX_LENGTH, EXCERPT_MAX_LENGTH, TITLE_MAX_LENGTH
from apps.catalogs.selectors.reactions import EMPTY_REACTIONS


def _is_mine(serializer, obj) -> bool:
    request = serializer.context.get("request")
    return bool(request and request.user.is_authenticated and obj.author_id == request.user.pk)


class ArticleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleCategory
        fields = ["id", "name", "slug"]
        read_only_fields = fields


class ArticleSerializer(serializers.ModelSerializer):
    """Tarjeta de un artículo (lista), sin el contenido.

    - ``cover_url`` pasa por la vista autorizada (nunca /media/); vacío si no tiene portada.
    - ``is_scheduled``: publicado con fecha futura (solo lo ve quien lo escribió).
    - ``reactions`` sale del contexto ``reaction_summaries`` (calculado por la vista para toda la página).
    """

    author = AuthorSerializer(read_only=True)
    category = ArticleCategorySerializer(read_only=True)
    cover_url = serializers.SerializerMethodField()
    is_scheduled = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(read_only=True, default=0)
    reactions = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id", "slug", "title", "excerpt", "cover_url", "category", "author", "status", "published_at",
            "is_scheduled", "created_at", "updated_at", "comments_count", "reactions", "is_mine",
        ]
        read_only_fields = fields

    def get_cover_url(self, article) -> str:
        if not article.cover:
            return ""
        return f'{reverse("blog-api:article-cover", kwargs={"pk": article.pk})}?v={int(article.updated_at.timestamp())}'

    def get_is_scheduled(self, article) -> bool:
        return article.status == Article.Status.PUBLISHED and not article.is_visible and article.deleted_at is None

    def get_reactions(self, article) -> dict:
        return self.context.get("reaction_summaries", {}).get(article.pk, EMPTY_REACTIONS)

    def get_is_mine(self, article) -> bool:
        return _is_mine(self, article)


class ArticleDetailSerializer(ArticleSerializer):
    """Artículo completo: agrega ``body`` (HTML ya limpio)."""

    class Meta(ArticleSerializer.Meta):
        fields = ArticleSerializer.Meta.fields + ["body"]
        read_only_fields = fields


class ArticleInputSerializer(serializers.Serializer):
    """Entrada al crear (``title`` obligatorio) o editar (todo opcional). La portada llega como
    archivo ``cover``; ``remove_cover: true`` la quita."""

    title = serializers.CharField(max_length=TITLE_MAX_LENGTH, trim_whitespace=False)
    body = serializers.CharField(max_length=BODY_MAX_LENGTH, required=False, allow_blank=True, trim_whitespace=False)
    excerpt = serializers.CharField(max_length=EXCERPT_MAX_LENGTH, required=False, allow_blank=True)
    category = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Article.Status.choices, required=False)
    published_at = serializers.DateTimeField(required=False, allow_null=True)
    remove_cover = serializers.BooleanField(required=False, default=False)


class ArticleReactionSerializer(serializers.ModelSerializer):
    """Una fila de «Ver todo»: quién reaccionó y con qué."""

    user = AuthorSerializer(read_only=True)
    emoji = serializers.CharField(source="emoji.code", read_only=True)

    class Meta:
        model = ArticleReaction
        fields = ["user", "emoji", "updated_at"]
        read_only_fields = fields


class ReactionInputSerializer(serializers.Serializer):
    emoji = serializers.CharField(max_length=64)


class ArticleCommentSerializer(serializers.ModelSerializer):
    """Comentario o respuesta. Un raíz eliminado (visible porque tiene respuestas) llega con
    ``is_deleted: true`` y sin autor ni texto."""

    author = serializers.SerializerMethodField()
    body = serializers.SerializerMethodField()
    is_deleted = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = ArticleComment
        fields = ["id", "parent", "author", "body", "created_at", "edited_at", "is_deleted", "is_mine"]
        read_only_fields = fields

    def get_is_deleted(self, comment) -> bool:
        return comment.deleted_at is not None

    def get_author(self, comment):
        return None if comment.deleted_at else AuthorSerializer(comment.author).data

    def get_body(self, comment) -> str:
        return "" if comment.deleted_at else comment.body

    def get_is_mine(self, comment) -> bool:
        return not comment.deleted_at and _is_mine(self, comment)


class ArticleCommentThreadSerializer(ArticleCommentSerializer):
    """Comentario raíz con sus respuestas vivas."""

    replies = serializers.SerializerMethodField()

    class Meta(ArticleCommentSerializer.Meta):
        fields = ArticleCommentSerializer.Meta.fields + ["replies"]
        read_only_fields = fields

    def get_replies(self, comment) -> list:
        return ArticleCommentSerializer(getattr(comment, "live_replies", []), many=True, context=self.context).data


class CommentInputSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=ARTICLE_COMMENT_BODY_MAX_LENGTH, allow_blank=True, trim_whitespace=True)
    parent = serializers.IntegerField(required=False, allow_null=True)
