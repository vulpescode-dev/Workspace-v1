from django.urls import reverse
from rest_framework import serializers

from apps.accounts.api.serializers import AuthorSerializer
from apps.marketplace.models import LISTING_DESCRIPTION_MAX_LENGTH, LISTING_TITLE_MAX_LENGTH, Listing, ListingCategory, ListingImage


class ListingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingCategory
        fields = ["id", "name", "slug"]
        read_only_fields = fields


class ListingImageSerializer(serializers.ModelSerializer):
    """Foto de un artículo. ``url`` pasa por la vista autorizada, nunca directo a /media/."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = ListingImage
        fields = ["id", "url", "width", "height"]
        read_only_fields = fields

    def get_url(self, image) -> str:
        return reverse("marketplace-api:image-file", kwargs={"pk": image.pk})


class ListingSerializer(serializers.ModelSerializer):
    """Lectura de un artículo. ``price`` nulo = «A tratar». ``is_mine``: si quien pide lo publicó
    (el frontend muestra «Editar / Marcar como vendido» solo entonces; la regla real está en ``services``)."""

    seller = AuthorSerializer(read_only=True)
    category = ListingCategorySerializer(read_only=True)
    images = ListingImageSerializer(many=True, read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            "id", "seller", "category", "title", "description", "price", "status", "sold_at", "images",
            "created_at", "updated_at", "is_mine",
        ]
        read_only_fields = fields

    def get_is_mine(self, listing) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and listing.seller_id == request.user.pk)


class ListingCreateSerializer(serializers.Serializer):
    """Entrada al publicar (las fotos llegan aparte, como ``files`` en multipart)."""

    title = serializers.CharField(max_length=LISTING_TITLE_MAX_LENGTH, trim_whitespace=False)
    description = serializers.CharField(
        max_length=LISTING_DESCRIPTION_MAX_LENGTH, required=False, allow_blank=True, trim_whitespace=False, default="",
    )
    price = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    category = serializers.IntegerField(required=False, allow_null=True, default=None)


class ListingEditSerializer(serializers.Serializer):
    """Entrada al editar: solo se cambian los campos que se manden."""

    title = serializers.CharField(max_length=LISTING_TITLE_MAX_LENGTH, required=False, trim_whitespace=False)
    description = serializers.CharField(
        max_length=LISTING_DESCRIPTION_MAX_LENGTH, required=False, allow_blank=True, trim_whitespace=False,
    )
    price = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    category = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Listing.Status.choices, required=False)
