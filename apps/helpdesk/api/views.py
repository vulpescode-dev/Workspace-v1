from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.serializers import AuthorSerializer
from apps.helpdesk.models import Ticket, TicketComment
from apps.helpdesk.selectors.tickets import (
    SCOPES, active_categories, attended_department_ids, can_view_all, department_agents, filter_tickets, is_agent,
    visible_attachment, visible_tickets,
)
from apps.helpdesk.services.tickets import add_comment, create_ticket, update_ticket
from apps.org.models import Department

from .serializers import (
    CommentCreateSerializer, TicketCategorySerializer, TicketCreateSerializer, TicketDetailSerializer,
    TicketEditSerializer, TicketSerializer,
)


def _as_drf_error(exc: DjangoValidationError) -> ValidationError:
    return ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)


def _id_param(params, name: str) -> int | None:
    value = params.get(name, "")
    if value and not value.isdigit():
        raise ValidationError({name: "Debe ser un id."})
    return int(value) if value else None


class TicketCategoryListView(generics.ListAPIView):
    """GET: categorías que se pueden elegir al levantar un ticket (``?department=<id>`` opcional). Sin paginar."""

    serializer_class = TicketCategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return active_categories(_id_param(self.request.query_params, "department"))


class TicketListCreateView(generics.ListAPIView):
    """GET: tickets visibles, más recientes primero. Filtros: ``?scope=mine|assigned|queue``,
    ``?status=open,in_progress``, ``?priority=``, ``?department=<id>``, ``?unassigned=1``, ``?q=<texto o folio>``.
    POST: levanta un ticket (multipart con ``category``, ``title``, ``description`` y hasta 5 ``files``)."""

    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        params = self.request.query_params
        scope = params.get("scope", "")
        if scope and scope not in SCOPES:
            raise ValidationError({"scope": f"Usa uno de: {', '.join(SCOPES)}."})
        statuses = params.get("status", "")
        if statuses and not set(statuses.split(",")) <= set(Ticket.Status.values):
            raise ValidationError({"status": "Estado no válido."})
        priority = params.get("priority", "")
        if priority and priority not in Ticket.Priority.values:
            raise ValidationError({"priority": "Prioridad no válida."})
        return filter_tickets(
            visible_tickets(self.request.user), self.request.user, scope=scope, status=statuses, priority=priority,
            department=_id_param(params, "department"), unassigned=params.get("unassigned") == "1",
            query=params.get("q", "").strip()[:100],
        )

    def post(self, request):
        data = TicketCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            ticket = create_ticket(
                requester=request.user, category_id=data.validated_data["category"],
                title=data.validated_data["title"], description=data.validated_data["description"],
                files=request.FILES.getlist("files"),
            )
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(_detail(request, ticket.pk), status=status.HTTP_201_CREATED)


def _detail_queryset(user):
    return visible_tickets(user).prefetch_related(
        "attachments",
        Prefetch("comments", queryset=TicketComment.objects.select_related("author").prefetch_related("attachments")),
        "events__actor",
    )


def _detail(request, pk: int) -> dict:
    ticket = get_object_or_404(_detail_queryset(request.user), pk=pk)
    return TicketDetailSerializer(ticket, context={"request": request}).data


class TicketDetailView(APIView):
    """GET: un ticket con conversación, archivos e historial (404 si no existe o no lo puedes ver).
    PATCH: ``status``, ``priority``, ``assignee`` (id o null) y ``category`` (transferir). Agentes: todo;
    quien lo levantó: solo ``status`` = ``closed`` (cerrar) u ``open`` (reabrir uno resuelto). Lo demás, 403.
    Si al transferirlo dejas de verlo, responde la forma corta con ``"visible": false``."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response(_detail(request, pk))

    def patch(self, request, pk):
        ticket = get_object_or_404(visible_tickets(request.user), pk=pk)
        data = TicketEditSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        changes = dict(data.validated_data)
        for field in ("assignee", "category"):
            if field in changes:
                changes[f"{field}_id"] = changes.pop(field)
        try:
            ticket = update_ticket(user=request.user, ticket=ticket, **changes)
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        if not visible_tickets(request.user).filter(pk=pk).exists():
            # Lo transfirió a un departamento que no atiende: ya no lo ve, solo recibe la forma corta.
            return Response({**TicketSerializer(ticket).data, "visible": False})
        return Response(_detail(request, pk))


class TicketCommentCreateView(APIView):
    """POST (multipart): ``body``, ``is_internal`` (solo agentes) y hasta 5 ``files``. Responde el ticket completo."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        ticket = get_object_or_404(visible_tickets(request.user), pk=pk)
        data = CommentCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            add_comment(
                user=request.user, ticket=ticket, body=data.validated_data["body"],
                is_internal=data.validated_data["is_internal"], files=request.FILES.getlist("files"),
            )
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(_detail(request, pk), status=status.HTTP_201_CREATED)


class TicketAgentsView(APIView):
    """GET: a quién se le puede asignar el ticket (agentes de su departamento). Solo para agentes."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ticket = get_object_or_404(visible_tickets(request.user), pk=pk)
        if not is_agent(request.user, ticket.department_id):
            return Response({"detail": "Solo los agentes del departamento."}, status=status.HTTP_403_FORBIDDEN)
        return Response(AuthorSerializer(department_agents(ticket.department_id), many=True).data)


class HelpdeskMeView(APIView):
    """GET: qué puedo hacer en la mesa de ayuda: departamentos que atiendo (``all_departments`` si son todos)
    y si puedo consultar todos los tickets (``view_all``)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids = attended_department_ids(request.user)
        departments = Department.objects.all() if ids is None else Department.objects.filter(pk__in=ids)
        return Response({
            "all_departments": ids is None,
            "attends": [{"id": d.pk, "name": d.name} for d in departments.order_by("name")],
            "view_all": can_view_all(request.user),
        })


class TicketAttachmentFileView(APIView):
    """GET: descarga un adjunto si su ticket es visible (y, si es de una nota interna, solo para agentes).

    Las imágenes se muestran en el navegador; lo demás siempre se descarga (``attachment``) con su
    nombre original. Nunca rutas de /media/.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        attachment = visible_attachment(request.user, pk)
        if attachment is None or not attachment.file:
            raise Http404
        response = FileResponse(
            attachment.file.open("rb"), content_type=attachment.content_type,
            as_attachment=not attachment.content_type.startswith("image/"),
            filename=attachment.original_name or attachment.file.name.rsplit("/", 1)[-1],
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response
