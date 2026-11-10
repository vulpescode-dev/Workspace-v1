from rest_framework import serializers

from apps.accounts.api.serializers import AuthorSerializer
from apps.accounts.selectors.profile import avatar_url, initials
from apps.accounts.models import Department


class DepartmentSerializer(serializers.ModelSerializer):
    """Departamento. ``parent_id`` permite armar el árbol en el frontend; ``head`` es el responsable
    (forma corta, o ``null``); ``members_count``, personas activas (llega anotado por el selector)."""

    parent_id = serializers.IntegerField(read_only=True)
    head = serializers.SerializerMethodField()
    members_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Department
        fields = ["id", "name", "description", "parent_id", "head", "members_count"]
        read_only_fields = fields

    def get_head(self, department) -> dict | None:
        head = department.head
        return AuthorSerializer(head).data if head is not None and head.is_active else None


class ChartNodeSerializer(serializers.Serializer):
    """Persona del organigrama con sus personas a cargo (``children``, hasta la profundidad pedida)."""

    id = serializers.IntegerField(source="user.pk")
    name = serializers.CharField(source="user.display_name")
    initials = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    job_title = serializers.CharField(source="user.job_title")
    department = serializers.SerializerMethodField()
    reports_count = serializers.IntegerField()
    children = serializers.SerializerMethodField()

    def get_initials(self, node) -> str:
        return initials(node.user.display_name)

    def get_avatar_url(self, node) -> str:
        return avatar_url(node.user)

    def get_department(self, node) -> dict | None:
        department = node.user.department
        return {"id": department.pk, "name": department.name} if department else None

    def get_children(self, node) -> list:
        return ChartNodeSerializer(node.children, many=True).data
