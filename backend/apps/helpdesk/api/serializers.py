from django.urls import reverse
from rest_framework import serializers

from apps.accounts.api.serializers import AuthorSerializer
from apps.helpdesk.models import (
    COMMENT_BODY_MAX_LENGTH, TICKET_DESCRIPTION_MAX_LENGTH, TICKET_TITLE_MAX_LENGTH, Ticket, TicketAttachment,
    TicketCategory, TicketComment, TicketEvent,
)
from apps.helpdesk.selectors.tickets import is_agent, sees_internal
from apps.helpdesk.services.tickets import REQUESTER_STATUSES


def _department(department) -> dict | None:
    return {"id": department.pk, "name": department.name} if department else None


class TicketCategorySerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()

    class Meta:
        model = TicketCategory
        fields = ["id", "name", "kind", "description", "department"]
        read_only_fields = fields

    def get_department(self, category) -> dict:
        return _department(category.department)


class TicketAttachmentSerializer(serializers.ModelSerializer):
    """Adjunto. ``url`` pasa por la vista autorizada, nunca directo a /media/."""

    url = serializers.SerializerMethodField()
    name = serializers.CharField(source="original_name")

    class Meta:
        model = TicketAttachment
        fields = ["id", "name", "content_type", "size", "url", "created_at"]
        read_only_fields = fields

    def get_url(self, attachment) -> str:
        return reverse("helpdesk-api:attachment-file", kwargs={"pk": attachment.pk})


class TicketCommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketComment
        fields = ["id", "author", "body", "is_internal", "attachments", "created_at"]
        read_only_fields = fields


class TicketEventSerializer(serializers.ModelSerializer):
    """Historial. Para estado y prioridad, ``old_label``/``new_label`` traen el texto para mostrar."""

    actor = AuthorSerializer(read_only=True)
    old_label = serializers.SerializerMethodField()
    new_label = serializers.SerializerMethodField()

    class Meta:
        model = TicketEvent
        fields = ["id", "kind", "actor", "old_value", "new_value", "old_label", "new_label", "created_at"]
        read_only_fields = fields

    @staticmethod
    def _label(event, value: str) -> str:
        choices = {TicketEvent.Kind.STATUS: Ticket.Status, TicketEvent.Kind.PRIORITY: Ticket.Priority}.get(event.kind)
        if choices and value in choices.values:
            return choices(value).label
        return value

    def get_old_label(self, event) -> str:
        return self._label(event, event.old_value)

    def get_new_label(self, event) -> str:
        return self._label(event, event.new_value)


class TicketSerializer(serializers.ModelSerializer):
    """Ticket en la lista (sin conversación). ``status_label``/``priority_label`` para mostrar.

    ``category`` y ``department`` son ``null`` en un ticket «Otro» que aún nadie clasifica.
    """

    folio = serializers.CharField(read_only=True)
    requester = AuthorSerializer(read_only=True)
    assignee = AuthorSerializer(read_only=True, allow_null=True)
    category = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "folio", "title", "status", "status_label", "priority", "priority_label", "category", "department",
            "requester", "assignee", "created_at", "updated_at", "first_response_at", "resolved_at", "closed_at",
        ]
        read_only_fields = fields

    def get_category(self, ticket) -> dict | None:
        if not ticket.category_id:
            return None
        return {"id": ticket.category_id, "name": ticket.category.name, "kind": ticket.category.kind}

    def get_department(self, ticket) -> dict | None:
        return _department(ticket.department)


class TicketDetailSerializer(TicketSerializer):
    """Ticket completo. Las notas internas (y sus archivos) solo salen para agentes y ``view.all``.

    ``permissions`` dice qué botones mostrar; la regla real está en ``services.tickets``.
    """

    attachments = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    events = TicketEventSerializer(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta(TicketSerializer.Meta):
        fields = TicketSerializer.Meta.fields + ["description", "attachments", "comments", "events", "permissions"]
        read_only_fields = fields

    def _viewer(self):
        return self.context["request"].user

    def get_attachments(self, ticket) -> list:
        """Archivos del ticket al crearlo (los de cada comentario vienen dentro del comentario)."""
        files = [a for a in ticket.attachments.all() if a.comment_id is None]
        return TicketAttachmentSerializer(files, many=True).data

    def get_comments(self, ticket) -> list:
        comments = ticket.comments.all()
        if not sees_internal(self._viewer(), ticket):
            comments = [c for c in comments if not c.is_internal]
        return TicketCommentSerializer(comments, many=True).data

    def get_permissions(self, ticket) -> dict:
        user = self._viewer()
        agent = is_agent(user, ticket.department_id)
        is_requester = ticket.requester_id == user.pk
        open_ = not ticket.is_closed
        return {
            "attend": open_ and agent,
            "comment": open_ and (agent or is_requester),
            "internal_notes": open_ and agent,
            "close": open_ and (agent or is_requester),
            "reopen": is_requester and ticket.status == Ticket.Status.RESOLVED,
            "requester_statuses": sorted(REQUESTER_STATUSES) if is_requester and not agent else [],
        }


class TicketCreateSerializer(serializers.Serializer):
    """Entrada al levantar un ticket (los archivos llegan aparte, como ``files`` en multipart).

    ``category`` vacío u omitido = «Otro» (el problema no está en la lista).
    """

    category = serializers.IntegerField(required=False, allow_null=True, default=None)
    title = serializers.CharField(max_length=TICKET_TITLE_MAX_LENGTH * 2, trim_whitespace=False)
    description = serializers.CharField(max_length=TICKET_DESCRIPTION_MAX_LENGTH * 2, trim_whitespace=False)


class TicketEditSerializer(serializers.Serializer):
    """Entrada al atender: solo se cambian los campos que se manden. ``assignee`` nulo = sin responsable."""

    status = serializers.ChoiceField(choices=Ticket.Status.choices, required=False)
    priority = serializers.ChoiceField(choices=Ticket.Priority.choices, required=False)
    assignee = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.IntegerField(required=False)


class CommentCreateSerializer(serializers.Serializer):
    body = serializers.CharField(
        max_length=COMMENT_BODY_MAX_LENGTH * 2, required=False, allow_blank=True, trim_whitespace=False, default="",
    )
    is_internal = serializers.BooleanField(required=False, default=False)
