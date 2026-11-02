from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import DocumentVersion
from apps.documents.selectors.documents import (
    SCOPES, active_categories, can_create, can_manage_all, filter_documents, visible_documents, visible_version,
)
from apps.documents.services.documents import (
    add_version, create_document, delete_document, restore_version, update_document,
)

from .serializers import (
    DocumentCategorySerializer, DocumentCreateSerializer, DocumentDetailSerializer, DocumentEditSerializer,
    DocumentSerializer, VersionCreateSerializer,
)


def _as_drf_error(exc: DjangoValidationError) -> ValidationError:
    return ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)


def _id_param(params, name: str) -> int | None:
    value = params.get(name, "")
    if value and not value.isdigit():
        raise ValidationError({name: "Debe ser un id."})
    return int(value) if value else None


class DocumentCategoryListView(generics.ListAPIView):
    """GET: categorías activas (para filtrar y para elegir al subir). Sin paginar."""

    serializer_class = DocumentCategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return active_categories()


class DocumentListCreateView(generics.ListAPIView):
    """GET: documentos visibles, los actualizados más recientemente primero. Filtros: ``?scope=mine|shared``,
    ``?category=<id>``, ``?q=<texto>``.
    POST (multipart, ``documents.documents.create``): ``title``, ``category``, ``file``, y opcionales
    ``description``, ``notes`` (de la v1), ``visibility`` (``public``/``departments``/``users``) con
    ``departments`` o ``users`` (ids, repetidos)."""

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        params = self.request.query_params
        scope = params.get("scope", "")
        if scope and scope not in SCOPES:
            raise ValidationError({"scope": f"Usa uno de: {', '.join(SCOPES)}."})
        return filter_documents(
            visible_documents(self.request.user), self.request.user, scope=scope,
            category=_id_param(params, "category"), query=params.get("q", "").strip()[:100],
        )

    def post(self, request):
        data = DocumentCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        try:
            document = create_document(
                owner=request.user, title=values["title"], description=values["description"],
                category_id=values["category"], file=request.FILES.get("file"), notes=values["notes"],
                visibility=values["visibility"], department_ids=values["departments"], user_ids=values["users"],
            )
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(_detail(request, document.pk), status=status.HTTP_201_CREATED)


def _detail(request, pk: int) -> dict:
    qs = visible_documents(request.user).prefetch_related(
        Prefetch("versions", queryset=DocumentVersion.objects.select_related("uploaded_by")),
        "departments", "shared_with",
    )
    document = get_object_or_404(qs, pk=pk)
    return DocumentDetailSerializer(document, context={"request": request}).data


class DocumentDetailView(APIView):
    """GET: un documento con su historial de versiones (404 si no existe o no lo puedes ver).
    PATCH (dueño o ``manage``): ``title``, ``description``, ``category``, ``visibility``, ``departments``, ``users``.
    DELETE (dueño o ``manage``): borrado suave. Si con el cambio dejas de verlo, responde ``{"visible": false}``."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response(_detail(request, pk))

    def patch(self, request, pk):
        document = get_object_or_404(visible_documents(request.user), pk=pk)
        data = DocumentEditSerializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        changes = dict(data.validated_data)
        for field, target in (("category", "category_id"), ("departments", "department_ids"), ("users", "user_ids")):
            if field in changes:
                changes[target] = changes.pop(field)
        try:
            update_document(user=request.user, document=document, **changes)
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        if not visible_documents(request.user).filter(pk=pk).exists():
            return Response({"id": pk, "visible": False})
        return Response(_detail(request, pk))

    def delete(self, request, pk):
        document = get_object_or_404(visible_documents(request.user), pk=pk)
        delete_document(user=request.user, document=document)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentVersionCreateView(APIView):
    """POST (multipart, dueño o ``manage``): ``file`` y ``notes`` (qué cambió). Queda como la versión vigente."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        document = get_object_or_404(visible_documents(request.user), pk=pk)
        data = VersionCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            add_version(user=request.user, document=document, file=request.FILES.get("file"),
                        notes=data.validated_data["notes"])
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(_detail(request, pk), status=status.HTTP_201_CREATED)


class DocumentVersionRestoreView(APIView):
    """POST (dueño o ``manage``): copia la versión ``version_pk`` como versión nueva y vigente."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk, version_pk):
        document = get_object_or_404(visible_documents(request.user), pk=pk)
        version = get_object_or_404(DocumentVersion, pk=version_pk, document=document)
        try:
            restore_version(user=request.user, document=document, version=version)
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(_detail(request, pk), status=status.HTTP_201_CREATED)


class DocumentsMeView(APIView):
    """GET: qué puedo hacer en Documentos: subir (``can_create``) y administrar todos (``manage_all``)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"can_create": can_create(request.user), "manage_all": can_manage_all(request.user)})


class DocumentVersionFileView(APIView):
    """GET: descarga una versión si su documento es visible. Las imágenes se muestran en el navegador;
    lo demás siempre se descarga (``attachment``) con su nombre original. Nunca rutas de /media/."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        version = visible_version(request.user, pk)
        if version is None or not version.file:
            raise Http404
        response = FileResponse(
            version.file.open("rb"), content_type=version.content_type,
            as_attachment=not version.content_type.startswith("image/"),
            filename=version.original_name or version.file.name.rsplit("/", 1)[-1],
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response
