from django.urls import reverse
from rest_framework import serializers

from apps.accounts.api.serializers import AuthorSerializer
from apps.documents.models import (
    DOCUMENT_DESCRIPTION_MAX_LENGTH, DOCUMENT_TITLE_MAX_LENGTH, VERSION_NOTES_MAX_LENGTH, Document, DocumentCategory,
    DocumentVersion,
)
from apps.documents.selectors.documents import can_manage


class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = ["id", "name", "description"]
        read_only_fields = fields


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Versión. ``url`` pasa por la vista autorizada, nunca directo a /media/."""

    uploaded_by = AuthorSerializer(read_only=True)
    name = serializers.CharField(source="original_name")
    url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVersion
        fields = ["id", "number", "notes", "name", "content_type", "size", "uploaded_by", "created_at", "url"]
        read_only_fields = fields

    def get_url(self, version) -> str:
        return reverse("documents-api:version-file", kwargs={"pk": version.pk})


class DocumentSerializer(serializers.ModelSerializer):
    """Forma corta para la lista: ficha, quién lo ve y la versión vigente."""

    category = DocumentCategorySerializer(read_only=True)
    owner = AuthorSerializer(read_only=True)
    current_version = DocumentVersionSerializer(read_only=True)

    class Meta:
        model = Document
        fields = ["id", "title", "description", "category", "owner", "visibility", "current_version", "created_at",
                  "updated_at"]
        read_only_fields = fields


class DocumentDetailSerializer(DocumentSerializer):
    """Detalle: además, el historial de versiones y, solo para quien lo administra, con quién se comparte."""

    versions = DocumentVersionSerializer(many=True, read_only=True)
    departments = serializers.SerializerMethodField()
    shared_with = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()

    class Meta(DocumentSerializer.Meta):
        fields = [*DocumentSerializer.Meta.fields, "departments", "shared_with", "versions", "can_manage"]
        read_only_fields = fields

    def _manages(self, document) -> bool:
        request = self.context.get("request")
        return bool(request) and can_manage(request.user, document)

    def get_can_manage(self, document) -> bool:
        return self._manages(document)

    def get_departments(self, document) -> list | None:
        if not self._manages(document):
            return None
        return [{"id": d.pk, "name": d.name} for d in document.departments.all()]

    def get_shared_with(self, document) -> list | None:
        if not self._manages(document):
            return None
        return AuthorSerializer(document.shared_with.all(), many=True).data


class DocumentCreateSerializer(serializers.Serializer):
    """Entrada de POST (multipart): ``departments`` y ``users`` se repiten (``users=3&users=8``)."""

    title = serializers.CharField(max_length=DOCUMENT_TITLE_MAX_LENGTH)
    description = serializers.CharField(max_length=DOCUMENT_DESCRIPTION_MAX_LENGTH, required=False, allow_blank=True,
                                        default="")
    category = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(max_length=VERSION_NOTES_MAX_LENGTH, required=False, allow_blank=True, default="")
    visibility = serializers.ChoiceField(choices=Document.Visibility.choices, default=Document.Visibility.PUBLIC)
    departments = serializers.ListField(child=serializers.IntegerField(min_value=1), max_length=200, required=False,
                                        default=list)
    users = serializers.ListField(child=serializers.IntegerField(min_value=1), max_length=500, required=False,
                                  default=list)


class DocumentEditSerializer(serializers.Serializer):
    """Entrada de PATCH: solo cambia lo que se mande."""

    title = serializers.CharField(max_length=DOCUMENT_TITLE_MAX_LENGTH, required=False)
    description = serializers.CharField(max_length=DOCUMENT_DESCRIPTION_MAX_LENGTH, required=False, allow_blank=True)
    category = serializers.IntegerField(min_value=1, required=False)
    visibility = serializers.ChoiceField(choices=Document.Visibility.choices, required=False)
    departments = serializers.ListField(child=serializers.IntegerField(min_value=1), max_length=200, required=False)
    users = serializers.ListField(child=serializers.IntegerField(min_value=1), max_length=500, required=False)


class VersionCreateSerializer(serializers.Serializer):
    notes = serializers.CharField(max_length=VERSION_NOTES_MAX_LENGTH, required=False, allow_blank=True, default="")
