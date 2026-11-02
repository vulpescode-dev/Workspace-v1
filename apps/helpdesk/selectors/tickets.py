"""Quién atiende qué y qué tickets puede ver cada persona.

- **Agente** de un departamento: su responsable (``Department.head``) o una persona de ese
  departamento con el permiso de negocio ``helpdesk.tickets.attend``. Un superusuario atiende todos.
- **Ver** un ticket: quien lo levantó, los agentes de su departamento y quien tenga
  ``helpdesk.tickets.view.all`` (solo consulta: no concede atender).
- Las **notas internas** (y sus adjuntos) solo las ven agentes y ``view.all``.
"""
from django.db.models import Q

from apps.accounts.models import User
from apps.accounts.services.permissions import has_permission, has_view_all
from apps.helpdesk.models import Ticket, TicketAttachment, TicketCategory
from apps.org.models import Department

ATTEND_PERMISSION = "helpdesk.tickets.attend"
TICKETS_RESOURCE = "helpdesk.tickets"


def _is_active(user) -> bool:
    return getattr(user, "is_authenticated", False) and user.is_active


def attended_department_ids(user) -> set[int] | None:
    """Departamentos que ``user`` atiende (``None`` = todos, superusuario). Cacheado por instancia."""
    if not _is_active(user):
        return set()
    if user.is_superuser:
        return None
    cached = getattr(user, "_ws_helpdesk_departments", None)
    if cached is None:
        cached = set(Department.objects.filter(head=user).values_list("pk", flat=True))
        if user.department_id and has_permission(user, ATTEND_PERMISSION):
            cached.add(user.department_id)
        user._ws_helpdesk_departments = cached
    return cached


def is_agent(user, department_id: int) -> bool:
    ids = attended_department_ids(user)
    return ids is None or department_id in ids


def can_view_all(user) -> bool:
    return _is_active(user) and has_view_all(user, TICKETS_RESOURCE)


def sees_internal(user, ticket: Ticket) -> bool:
    """¿Ve notas internas de ``ticket``? Agentes de su departamento y ``view.all``."""
    return is_agent(user, ticket.department_id) or can_view_all(user)


def department_agents(department_id: int):
    """Personas activas que pueden atender (y recibir) tickets del departamento, por nombre."""
    department = Department.objects.filter(pk=department_id).only("head_id").first()
    if department is None:
        return User.objects.none()
    members = Q(department_id=department_id) & (
        Q(is_superuser=True)
        | Q(
            user_roles__role__is_active=True,
            user_roles__role__role_permissions__permission__codename=ATTEND_PERMISSION,
        )
    )
    condition = members | Q(pk=department.head_id) if department.head_id else members
    return (
        User.objects.filter(is_active=True).filter(condition).distinct()
        .order_by("first_name", "last_name", "username", "id")
    )


def visible_tickets(user):
    if not _is_active(user):
        return Ticket.objects.none()
    qs = Ticket.objects.select_related("requester", "assignee", "category", "department")
    if user.is_superuser or can_view_all(user):
        return qs
    return qs.filter(Q(requester=user) | Q(department_id__in=attended_department_ids(user)))


SCOPES = ("mine", "assigned", "queue")


def filter_tickets(qs, user, *, scope: str = "", status: str = "", priority: str = "", department: int | None = None,
                   unassigned: bool = False, query: str = ""):
    """Filtros de la lista.

    ``scope``: ``mine`` (los que levanté), ``assigned`` (asignados a mí), ``queue`` (de los departamentos
    que atiendo). ``status`` acepta varios separados por coma (``open,in_progress``). ``query`` busca en
    el título o por folio (``HD-00042`` o ``42``).
    """
    if scope == "mine":
        qs = qs.filter(requester=user)
    elif scope == "assigned":
        qs = qs.filter(assignee=user)
    elif scope == "queue":
        ids = attended_department_ids(user)
        if ids is not None:
            qs = qs.filter(department_id__in=ids)
    if status:
        qs = qs.filter(status__in=status.split(","))
    if priority:
        qs = qs.filter(priority=priority)
    if department:
        qs = qs.filter(department_id=department)
    if unassigned:
        qs = qs.filter(assignee__isnull=True)
    if query:
        number = query.upper().removeprefix("HD-").lstrip("0")
        condition = Q(title__icontains=query)
        if number.isdigit():
            condition |= Q(pk=int(number))
        qs = qs.filter(condition)
    return qs


def visible_attachment(user, pk: int) -> TicketAttachment | None:
    """Un adjunto se entrega si su ticket es visible y, si es de una nota interna, solo a quien la puede ver."""
    attachment = TicketAttachment.objects.select_related("ticket", "comment").filter(pk=pk).first()
    if attachment is None or not visible_tickets(user).filter(pk=attachment.ticket_id).exists():
        return None
    if attachment.comment and attachment.comment.is_internal and not sees_internal(user, attachment.ticket):
        return None
    return attachment


def active_categories(department_id: int | None = None):
    """Categorías que se pueden elegir (activas y de un departamento activo)."""
    qs = TicketCategory.objects.filter(is_active=True, department__is_active=True).select_related("department")
    if department_id:
        qs = qs.filter(department_id=department_id)
    return qs
