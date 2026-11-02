from django.urls import reverse
from rest_framework import serializers

from apps.accounts.selectors.profile import avatar_url, initials
from apps.social.models import COMMENT_BODY_MAX_LENGTH, POST_BODY_MAX_LENGTH, Post, PostAttachment, PostComment, PostReaction

EMPTY_REACTIONS = {"reactions": [], "total": 0, "mine": None}


def _is_mine(serializer, obj) -> bool:
    request = serializer.context.get("request")
    return bool(request and request.user.is_authenticated and obj.author_id == request.user.pk)


class PostAuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.SerializerMethodField()
    initials = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    def get_name(self, user) -> str:
        return user.get_full_name() or user.username

    def get_initials(self, user) -> str:
        return initials(self.get_name(user))

    def get_avatar_url(self, user) -> str:
        return avatar_url(user)


class PostAttachmentSerializer(serializers.ModelSerializer):
    """Adjunto de un post. ``url`` pasa por la vista autorizada, nunca directo a /media/."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = PostAttachment
        fields = ["id", "kind", "url", "content_type", "size", "width", "height"]
        read_only_fields = fields

    def get_url(self, attachment) -> str:
        return reverse("social-api:attachment-file", kwargs={"pk": attachment.pk})


class PhotoSerializer(PostAttachmentSerializer):
    """Foto de la pestaña «Fotos» del perfil: el adjunto y la publicación a la que pertenece."""

    class Meta(PostAttachmentSerializer.Meta):
        fields = ["id", "url", "width", "height", "post"]
        read_only_fields = fields


class PostSerializer(serializers.ModelSerializer):
    """Lectura de una publicación.

    - ``reactions`` sale del contexto ``reaction_summaries`` (calculado por la vista para toda la página).
    - ``is_mine``: si quien pide es el autor; el frontend muestra «Editar/Eliminar» solo entonces.
      La regla real la aplica el servidor (``services.posts``).
    """

    author = PostAuthorSerializer(read_only=True)
    attachments = PostAttachmentSerializer(many=True, read_only=True)
    reactions = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(read_only=True, default=0)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id", "author", "body", "audience", "attachments", "created_at", "edited_at", "reactions", "comments_count",
            "is_mine",
        ]
        read_only_fields = fields

    def get_reactions(self, post) -> dict:
        return self.context.get("reaction_summaries", {}).get(post.pk, EMPTY_REACTIONS)

    def get_is_mine(self, post) -> bool:
        return _is_mine(self, post)


class PostCreateSerializer(serializers.Serializer):
    """Entrada para crear una publicación; la regla de negocio vive en ``services.posts``."""

    body = serializers.CharField(max_length=POST_BODY_MAX_LENGTH, allow_blank=True, trim_whitespace=True, required=False, default="")
    audience = serializers.CharField(required=False, allow_blank=True, default="")


class PostEditSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=POST_BODY_MAX_LENGTH, allow_blank=True, trim_whitespace=True)
    audience = serializers.CharField(required=False)


class ReactionInputSerializer(serializers.Serializer):
    emoji = serializers.CharField(max_length=64)


class PostReactionSerializer(serializers.ModelSerializer):
    """Una fila de «Ver todo»: quién reaccionó y con qué."""

    user = PostAuthorSerializer(read_only=True)
    emoji = serializers.CharField(source="emoji.code", read_only=True)

    class Meta:
        model = PostReaction
        fields = ["user", "emoji", "updated_at"]
        read_only_fields = fields


class PostCommentSerializer(serializers.ModelSerializer):
    """Comentario o respuesta.

    Un comentario raíz eliminado (que se muestra solo porque tiene respuestas) llega con
    ``is_deleted: true`` y sin autor ni texto. ``reactions`` sale del contexto ``comment_reactions``.
    """

    author = serializers.SerializerMethodField()
    body = serializers.SerializerMethodField()
    is_deleted = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ["id", "parent", "author", "body", "created_at", "edited_at", "is_deleted", "is_mine", "reactions"]
        read_only_fields = fields

    def get_is_deleted(self, comment) -> bool:
        return comment.deleted_at is not None

    def get_author(self, comment):
        return None if comment.deleted_at else PostAuthorSerializer(comment.author).data

    def get_body(self, comment) -> str:
        return "" if comment.deleted_at else comment.body

    def get_is_mine(self, comment) -> bool:
        return not comment.deleted_at and _is_mine(self, comment)

    def get_reactions(self, comment) -> dict:
        return self.context.get("comment_reactions", {}).get(comment.pk, EMPTY_REACTIONS)


class CommentThreadSerializer(PostCommentSerializer):
    """Comentario raíz con sus respuestas vivas."""

    replies = serializers.SerializerMethodField()

    class Meta(PostCommentSerializer.Meta):
        fields = PostCommentSerializer.Meta.fields + ["replies"]
        read_only_fields = fields

    def get_replies(self, comment) -> list:
        replies = getattr(comment, "live_replies", [])
        return PostCommentSerializer(replies, many=True, context=self.context).data


class CommentInputSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=COMMENT_BODY_MAX_LENGTH, allow_blank=True, trim_whitespace=True)
    parent = serializers.IntegerField(required=False, allow_null=True)


class PersonSerializer(PostAuthorSerializer):
    """Fila de las listas Seguidores / Seguidos. ``followed_ids`` y ``viewer_id`` llegan por contexto."""

    job_title = serializers.CharField(read_only=True)
    is_following = serializers.SerializerMethodField()
    is_me = serializers.SerializerMethodField()

    def get_is_following(self, user) -> bool:
        return user.pk in self.context.get("followed_ids", set())

    def get_is_me(self, user) -> bool:
        return user.pk == self.context.get("viewer_id")
