from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.social.selectors.posts import (
    author_photos, live_comments_count, post_comments, visible_attachment, visible_comment, visible_posts,
)
from apps.accounts.selectors.profile import profile_user
from apps.social.selectors.follows import follow_stats, follow_suggestions, followed_ids, followers_of, following_of
from apps.social.selectors.reactions import comment_reaction_summaries, post_reactions, reaction_summaries
from apps.social.services.comments import (
    create_comment, delete_comment, edit_comment, remove_comment_reaction, set_comment_reaction,
)
from apps.social.services.follows import follow, unfollow
from apps.social.services.posts import create_post, delete_post, edit_post
from apps.social.services.reactions import remove_reaction, set_reaction

from .serializers import (
    EMPTY_REACTIONS, CommentInputSerializer, CommentThreadSerializer, PersonSerializer, PhotoSerializer,
    PostCommentSerializer, PostCreateSerializer, PostEditSerializer, PostReactionSerializer, PostSerializer,
    ReactionInputSerializer,
)


def _as_drf_error(exc: DjangoValidationError) -> ValidationError:
    return ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)


# --- Publicaciones -----------------------------------------------------------

class PostListCreateView(generics.ListAPIView):
    """GET: feed paginado (más recientes primero) con adjuntos y resumen de reacciones (4 consultas).
    POST: crea una publicación (JSON ``{"body"}`` o multipart con ``body`` y ``files``)."""

    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """``?author=<id>``: solo las publicaciones de esa persona (perfil). ``?id=<id>``: solo esa publicación."""
        qs = visible_posts(self.request.user)
        post_id = self.request.query_params.get("id")
        if post_id:
            if not post_id.isdigit():
                raise ValidationError({"id": "Debe ser un id de publicación."})
            qs = qs.filter(pk=int(post_id))
        author = self.request.query_params.get("author")
        if author:
            if not author.isdigit():
                raise ValidationError({"author": "Debe ser un id de usuario."})
            qs = qs.filter(author_id=int(author))
        return qs

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        context = {**self.get_serializer_context(), "reaction_summaries": reaction_summaries([p.pk for p in page], request.user)}
        return self.get_paginated_response(PostSerializer(page, many=True, context=context).data)

    def post(self, request):
        data = PostCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            post = create_post(
                author=request.user, body=data.validated_data["body"], files=request.FILES.getlist("files"),
                audience=data.validated_data["audience"],
            )
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        post = visible_posts(request.user).get(pk=post.pk)
        return Response(PostSerializer(post, context={"request": request}).data, status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    """GET: una publicación visible. PATCH ``{"body"}``: edita el texto (solo autor).
    DELETE: borrado suave (solo autor). Lo ajeno responde 403; lo inexistente o eliminado, 404."""

    permission_classes = [IsAuthenticated]

    def get_post(self):
        return get_object_or_404(visible_posts(self.request.user), pk=self.kwargs["pk"])

    def respond(self, post):
        context = {"request": self.request, "reaction_summaries": reaction_summaries([post.pk], self.request.user)}
        return Response(PostSerializer(post, context=context).data)

    def get(self, request, pk):
        return self.respond(self.get_post())

    def patch(self, request, pk):
        post = self.get_post()
        data = PostEditSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            edit_post(user=request.user, post=post, body=data.validated_data["body"], audience=data.validated_data.get("audience"))
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return self.respond(self.get_post())

    def delete(self, request, pk):
        delete_post(user=request.user, post=self.get_post())
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostReactionView(APIView):
    """Mi reacción en una publicación.

    PUT ``{"emoji": "<código>"}``: pone o cambia (una por persona). DELETE: la quita.
    Ambas responden el resumen actualizado de reacciones del post.
    """

    permission_classes = [IsAuthenticated]

    def get_post(self):
        return get_object_or_404(visible_posts(self.request.user), pk=self.kwargs["pk"])

    def summary(self, post):
        return reaction_summaries([post.pk], self.request.user).get(post.pk, EMPTY_REACTIONS)

    def put(self, request, pk):
        post = self.get_post()
        data = ReactionInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            set_reaction(user=request.user, post=post, emoji_code=data.validated_data["emoji"])
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(self.summary(post))

    def delete(self, request, pk):
        post = self.get_post()
        remove_reaction(user=request.user, post=post)
        return Response(self.summary(post))


class PostReactionListView(generics.ListAPIView):
    """GET: quién reaccionó a la publicación («Ver todo»), paginado."""

    serializer_class = PostReactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post = get_object_or_404(visible_posts(self.request.user), pk=self.kwargs["pk"])
        return post_reactions(post)


class PhotoListView(generics.ListAPIView):
    """GET ``?author=<id>``: fotos de las publicaciones visibles de esa persona (paginado)."""

    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        author = self.request.query_params.get("author", "")
        if not author.isdigit():
            raise ValidationError({"author": "Indica el id de la persona."})
        return author_photos(self.request.user, int(author))


class AttachmentFileView(APIView):
    """GET: entrega el archivo de un adjunto solo si su publicación es visible para quien lo pide.

    Los nombres en disco son secuenciales (``<id>.webp``), por eso nunca se exponen las rutas
    de /media/: todo pasa por aquí. ``nosniff`` evita que el navegador interprete el archivo
    como otro tipo. Pendiente para producción: delegar la entrega al servidor web
    (X-Accel-Redirect / X-Sendfile) para soportar rangos en video y no ocupar a Django.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        attachment = visible_attachment(request.user, pk)
        if attachment is None or not attachment.file:
            raise Http404
        response = FileResponse(attachment.file.open("rb"), content_type=attachment.content_type)
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Disposition"] = "inline"
        response["Cache-Control"] = "private, max-age=86400"
        return response


# --- Comentarios -------------------------------------------------------------

def _comment_context(request, comments) -> dict:
    """Contexto con reacciones de los comentarios dados y de todas sus respuestas (1 consulta)."""
    ids = []
    for comment in comments:
        ids.append(comment.pk)
        ids.extend(reply.pk for reply in getattr(comment, "live_replies", []))
    return {"request": request, "comment_reactions": comment_reaction_summaries(ids, request.user)}


class PostCommentListCreateView(generics.ListAPIView):
    """GET: hilos del post (comentario raíz + respuestas), más antiguos primero, paginado.
    POST ``{"body", "parent"?}``: comenta o responde. Responde el comentario y ``comments_count``."""

    serializer_class = CommentThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_post(self):
        # Solo se comprueba que el post sea visible: sin cargar sus adjuntos.
        return get_object_or_404(visible_posts(self.request.user).prefetch_related(None), pk=self.kwargs["pk"])

    def get_queryset(self):
        return post_comments(self.get_post())

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        data = CommentThreadSerializer(page, many=True, context=_comment_context(request, page)).data
        return self.get_paginated_response(data)

    def post(self, request, pk):
        post = self.get_post()
        data = CommentInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            comment = create_comment(
                author=request.user, post=post, body=data.validated_data["body"],
                parent_id=data.validated_data.get("parent"),
            )
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        payload = {
            **PostCommentSerializer(comment, context={"request": request}).data,
            "comments_count": live_comments_count(post),
        }
        return Response(payload, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    """PATCH ``{"body"}``: edita (solo autor). DELETE: borrado suave (solo autor).

    DELETE responde ``comments_count`` del post y ``keep_placeholder`` (el comentario tiene
    respuestas vivas y debe seguir como «Comentario eliminado»)."""

    permission_classes = [IsAuthenticated]

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
        return Response(PostCommentSerializer(comment, context=_comment_context(request, [comment])).data)

    def delete(self, request, pk):
        comment = self.get_comment()
        delete_comment(user=request.user, comment=comment)
        keep = comment.parent_id is None and comment.replies.filter(deleted_at__isnull=True).exists()
        return Response({"comments_count": live_comments_count(comment.post), "keep_placeholder": keep})


class CommentReactionView(APIView):
    """Mi reacción en un comentario. PUT ``{"emoji"}`` pone o cambia; DELETE la quita. Responden el resumen."""

    permission_classes = [IsAuthenticated]

    def get_comment(self):
        comment = visible_comment(self.request.user, self.kwargs["pk"])
        if comment is None:
            raise Http404
        return comment

    def summary(self, comment):
        return comment_reaction_summaries([comment.pk], self.request.user).get(comment.pk, EMPTY_REACTIONS)

    def put(self, request, pk):
        comment = self.get_comment()
        data = ReactionInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            set_comment_reaction(user=request.user, comment=comment, emoji_code=data.validated_data["emoji"])
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(self.summary(comment))

    def delete(self, request, pk):
        comment = self.get_comment()
        remove_comment_reaction(user=request.user, comment=comment)
        return Response(self.summary(comment))


# --- Seguir --------------------------------------------------------------------

def _target(request, pk):
    user = profile_user(request.user, pk)
    if user is None:
        raise Http404
    return user


class FollowView(APIView):
    """PUT: seguir a la persona ``pk`` (inmediato). DELETE: dejar de seguirla.
    Ambas responden ``followers_count``, ``following_count``, ``is_following`` y ``follows_me``."""

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        target = _target(request, pk)
        try:
            follow(user=request.user, target=target)
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(follow_stats(target, request.user))

    def delete(self, request, pk):
        target = _target(request, pk)
        unfollow(user=request.user, target=target)
        return Response(follow_stats(target, request.user))


class FollowSuggestionsView(APIView):
    """GET: hasta 5 personas que aún no sigo (misma área primero). Sin paginar: es un widget."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        people = list(follow_suggestions(request.user))
        context = {"viewer_id": request.user.pk, "followed_ids": set()}
        return Response(PersonSerializer(people, many=True, context=context).data)


class _PeopleListView(generics.ListAPIView):
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]
    source = None   # followers_of | following_of

    def get_queryset(self):
        return type(self).source(_target(self.request, self.kwargs["pk"]))

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        context = {"viewer_id": request.user.pk, "followed_ids": followed_ids(request.user, [u.pk for u in page])}
        return self.get_paginated_response(PersonSerializer(page, many=True, context=context).data)


class FollowersListView(_PeopleListView):
    """GET: quiénes siguen a la persona ``pk`` (paginado)."""

    source = staticmethod(followers_of)


class FollowingListView(_PeopleListView):
    """GET: a quiénes sigue la persona ``pk`` (paginado)."""

    source = staticmethod(following_of)
