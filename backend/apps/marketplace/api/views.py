from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.permissions import MARKETPLACE
from apps.marketplace.models import Listing
from apps.marketplace.selectors.listings import active_categories, filter_listings, visible_image, visible_listings
from apps.marketplace.services.listings import add_images, create_listing, delete_listing, edit_listing, remove_image

from .serializers import (
    ListingCategorySerializer, ListingCreateSerializer, ListingEditSerializer, ListingSerializer,
)


def _as_drf_error(exc: DjangoValidationError) -> ValidationError:
    return ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)


class ListingListCreateView(generics.ListAPIView):
    """GET: artículos paginados, más recientes primero. Filtros opcionales:
    ``?status=available|sold``, ``?category=<slug>``, ``?seller=<id>``, ``?q=<texto>``.
    POST: publica un artículo (multipart con ``title``, ``description``, ``price``, ``category`` y ``files``)."""

    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated, MARKETPLACE]

    def get_queryset(self):
        params = self.request.query_params
        listing_status = params.get("status", "")
        if listing_status and listing_status not in Listing.Status.values:
            raise ValidationError({"status": "Estatus no válido."})
        seller = params.get("seller", "")
        if seller and not seller.isdigit():
            raise ValidationError({"seller": "Debe ser un id de usuario."})
        return filter_listings(
            visible_listings(self.request.user), status=listing_status, category=params.get("category", ""),
            seller=int(seller) if seller else None, query=params.get("q", "").strip(),
        )

    def post(self, request):
        data = ListingCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            listing = create_listing(
                seller=request.user, title=data.validated_data["title"],
                description=data.validated_data["description"], price=data.validated_data["price"],
                category_id=data.validated_data["category"], files=request.FILES.getlist("files"),
            )
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        listing = visible_listings(request.user).get(pk=listing.pk)
        return Response(ListingSerializer(listing, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ListingDetailView(APIView):
    """GET: un artículo. PATCH: edita los campos que se manden, incluido ``status`` (solo quien lo publicó).
    DELETE: borrado suave (solo quien lo publicó). Lo ajeno responde 403; lo inexistente o eliminado, 404."""

    permission_classes = [IsAuthenticated, MARKETPLACE]

    def get_listing(self):
        return get_object_or_404(visible_listings(self.request.user), pk=self.kwargs["pk"])

    def respond(self, listing):
        return Response(ListingSerializer(listing, context={"request": self.request}).data)

    def get(self, request, pk):
        return self.respond(self.get_listing())

    def patch(self, request, pk):
        listing = self.get_listing()
        data = ListingEditSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        changes = dict(data.validated_data)
        if "category" in changes:
            changes["category_id"] = changes.pop("category")
        try:
            edit_listing(user=request.user, listing=listing, **changes)
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return self.respond(self.get_listing())

    def delete(self, request, pk):
        delete_listing(user=request.user, listing=self.get_listing())
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListingImagesView(APIView):
    """POST (multipart, ``files`` repetido; solo quien lo publicó): agrega fotos al final. Responde el artículo."""

    permission_classes = [IsAuthenticated, MARKETPLACE]

    def post(self, request, pk):
        listing = get_object_or_404(visible_listings(request.user), pk=pk)
        try:
            add_images(user=request.user, listing=listing, files=request.FILES.getlist("files"))
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        listing = visible_listings(request.user).get(pk=pk)
        return Response(ListingSerializer(listing, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ListingImageDetailView(APIView):
    """DELETE (solo quien lo publicó): quita una foto del artículo."""

    permission_classes = [IsAuthenticated, MARKETPLACE]

    def delete(self, request, pk):
        image = visible_image(request.user, pk)
        if image is None:
            raise Http404
        remove_image(user=request.user, image=image)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListingCategoryListView(generics.ListAPIView):
    """GET: categorías activas (para los filtros y el formulario). Sin paginar: son pocas."""

    serializer_class = ListingCategorySerializer
    permission_classes = [IsAuthenticated, MARKETPLACE]
    pagination_class = None

    def get_queryset(self):
        return active_categories()


class ListingImageFileView(APIView):
    """GET: entrega una foto solo si su artículo es visible para quien la pide (nunca rutas de /media/)."""

    permission_classes = [IsAuthenticated, MARKETPLACE]

    def get(self, request, pk):
        image = visible_image(request.user, pk)
        if image is None or not image.file:
            raise Http404
        response = FileResponse(image.file.open("rb"), content_type=image.content_type)
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Disposition"] = "inline"
        response["Cache-Control"] = "private, max-age=86400"
        return response
