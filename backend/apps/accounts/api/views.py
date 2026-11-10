from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.permissions import PEOPLE
from apps.accounts.models import Gender, MaritalStatus
from apps.accounts.selectors.birthdays import upcoming_birthdays
from apps.accounts.selectors.profile import directory, profile_user
from apps.core.pagination import SafePageNumberPagination
from apps.accounts.services.permissions import user_permission_codenames
from apps.accounts.services.profile import remove_profile_image, set_profile_image, update_bio
from apps.social.selectors.follows import follow_stats, followed_ids
from apps.social.selectors.posts import visible_posts

from .serializers import BioInputSerializer, BirthdaySerializer, DirectoryPersonSerializer, ProfileSerializer


def _as_drf_error(exc: DjangoValidationError) -> ValidationError:
    return ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)


def _profile_response(request, user):
    context = {
        "request": request,
        "posts_count": visible_posts(request.user).filter(author=user).count(),
        "follow": follow_stats(user, request.user),
    }
    data = ProfileSerializer(user, context=context).data
    if user.pk == request.user.pk:
        # Solo en mi propio perfil: qué puedo hacer. El superusuario puede todo (no hace falta mirar
        # sus permisos); el frontend decide así: ``access.is_superuser || access.permissions.includes(código)``.
        # Es para mostrar u ocultar botones: el servidor vuelve a validar cada acción.
        data["access"] = {
            "is_superuser": bool(user.is_superuser),
            "permissions": sorted(user_permission_codenames(user)),
        }
    return Response(data)


class ProfileView(APIView):
    """GET: perfil de un empleado activo (404 si no existe o está inactivo)."""

    permission_classes = [IsAuthenticated, PEOPLE]

    def get(self, request, pk):
        user = profile_user(request.user, pk)
        if user is None:
            raise Http404
        return _profile_response(request, user)


class MyProfileView(APIView):
    """GET: mi perfil, con ``access`` = ``{is_superuser, permissions}`` (qué puedo hacer).
    PATCH ``{"bio"}``: cambia mi presentación (lo demás lo administra RRHH/TI)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return _profile_response(request, request.user)

    def patch(self, request):
        data = BioInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            update_bio(user=request.user, bio=data.validated_data["bio"])
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return _profile_response(request, request.user)


class MyProfileImageView(APIView):
    """POST (multipart ``file``, WebP): cambia mi foto. DELETE: la quita. Responden mi perfil."""

    permission_classes = [IsAuthenticated]
    field = None   # "avatar"

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError({"file": "Falta la imagen."})
        try:
            set_profile_image(user=request.user, field=self.field, upload=upload)
        except DjangoValidationError as exc:
            raise ValidationError({"file": exc.messages}) from exc
        return _profile_response(request, request.user)

    def delete(self, request):
        remove_profile_image(user=request.user, field=self.field)
        return _profile_response(request, request.user)


class UserImageView(APIView):
    """GET: foto de un empleado (solo con sesión). La URL lleva ``?v=`` para la caché."""

    permission_classes = [IsAuthenticated]
    field = None

    def get(self, request, pk):
        user = profile_user(request.user, pk)
        image = getattr(user, self.field, None) if user else None
        if not image:
            raise Http404
        response = FileResponse(image.open("rb"), content_type="image/webp")
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Disposition"] = "inline"
        # La versión (?v=) cambia al reemplazar la imagen, así que puede cachearse mucho tiempo.
        response["Cache-Control"] = "private, max-age=31536000, immutable"
        return response


class DirectoryView(generics.ListAPIView):
    """GET ``?search=<texto>&department=<id>&gender=<g>&marital_status=<e>&page=<n>``: directorio de personas
    activas (25 por página, ``?page_size=`` para menos). Los filtros se combinan. ``gender``: ``male``/``female``;
    ``marital_status``: ``single``, ``in_relationship``, ``married``, ``common_law``, ``divorced``, ``widowed``,
    ``complicated``. Un valor que no existe responde 400.

    Una página inexistente responde 404 con ``detail``, ``count`` y ``total_pages``.
    """

    serializer_class = DirectoryPersonSerializer
    permission_classes = [IsAuthenticated, PEOPLE]
    pagination_class = SafePageNumberPagination

    def get_queryset(self):
        params = self.request.query_params
        department = params.get("department", "")
        if department and not department.isdigit():
            raise ValidationError({"department": "Debe ser un id de departamento."})
        choices = {"gender": Gender, "marital_status": MaritalStatus}
        for name, options in choices.items():
            value = params.get(name, "")
            if value and value not in options.values:
                raise ValidationError({name: f"Usa uno de: {', '.join(options.values)}."})
        return directory(self.request.user, params.get("search", "")[:100],
                         department_id=int(department) if department else None,
                         gender=params.get("gender", ""), marital_status=params.get("marital_status", ""))

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        context = {"viewer_id": request.user.pk, "followed_ids": followed_ids(request.user, [u.pk for u in page])}
        return self.get_paginated_response(DirectoryPersonSerializer(page, many=True, context=context).data)


class BirthdaysView(APIView):
    """GET: quién cumple años hoy y en los próximos 30 días (máx. 6), la fecha más cercana primero."""

    permission_classes = [IsAuthenticated, PEOPLE]

    def get(self, request):
        return Response(BirthdaySerializer(upcoming_birthdays(request.user), many=True).data)
