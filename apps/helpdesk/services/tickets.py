"""Operaciones que crean o modifican tickets.

Reglas (las mismas para la API y para futuras vistas):

- Levantar un ticket: cualquier persona activa, eligiendo una categoría activa.
- Atender (estado, prioridad, responsable, transferir de categoría, notas internas): solo agentes del
  departamento del ticket (ver ``selectors.tickets``).
- Quien lo levantó puede comentar, **cerrarlo** (ya no lo necesita o confirma la solución) y
  **reabrirlo** si está «Resuelto». Cerrado es final: ya no se comenta ni se cambia.
- Archivos: hasta ``TICKET_MAX_FILES_PER_MESSAGE`` por mensaje, validados con ``check_document_upload``.
  Se validan todos antes de escribir nada (todo o nada).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.uploads import check_document_upload
from apps.helpdesk.models import (
    COMMENT_BODY_MAX_LENGTH, TICKET_DESCRIPTION_MAX_LENGTH, TICKET_MAX_FILES_PER_MESSAGE, TICKET_TITLE_MAX_LENGTH,
    Ticket, TicketAttachment, TicketComment, TicketEvent,
)
from apps.helpdesk.selectors.tickets import active_categories, department_agents, is_agent
from apps.notifications.models import Notification
from apps.notifications.services.notifications import notify

UNSET = object()   # al editar: distingue «no se mandó» de «se mandó vacío»
Status = Ticket.Status
REQUESTER_STATUSES = {Status.CLOSED, Status.OPEN}   # cerrar o reabrir


def _clean_title(title: str) -> str:
    title = " ".join((title or "").split())
    if not title:
        raise ValidationError({"title": "Escribe un título."})
    if len(title) > TICKET_TITLE_MAX_LENGTH:
        raise ValidationError({"title": f"Máximo {TICKET_TITLE_MAX_LENGTH} caracteres."})
    return title


def _clean_body(text: str, field: str, max_length: int, *, required: bool) -> str:
    # Los formularios multipart mandan los saltos de línea como CRLF: se guardan como LF.
    text = (text or "").replace("\r\n", "\n").strip()
    if required and not text:
        raise ValidationError({field: "Escribe una descripción." if field == "description" else "Escribe un mensaje."})
    if len(text) > max_length:
        raise ValidationError({field: f"Máximo {max_length} caracteres."})
    return text


def _check_files(files) -> list:
    files = list(files or [])
    if len(files) > TICKET_MAX_FILES_PER_MESSAGE:
        raise ValidationError({"files": f"Máximo {TICKET_MAX_FILES_PER_MESSAGE} archivos por mensaje."})
    checked = []
    for upload in files:
        name = getattr(upload, "name", "archivo")
        try:
            checked.append((upload, check_document_upload(upload)))
        except ValidationError as exc:
            raise ValidationError({"files": f"«{name}»: {exc.messages[0]}"}) from exc
    return checked


def _save_files(ticket: Ticket, user, checked, comment: TicketComment | None = None) -> None:
    for upload, info in checked:
        attachment = TicketAttachment.objects.create(
            ticket=ticket, comment=comment, uploaded_by=user,
            original_name=(getattr(upload, "name", "") or "")[:255], content_type=info.content_type, size=info.size,
        )
        attachment.file.save(f"{attachment.pk}{info.extension}", upload, save=True)


def _event(ticket: Ticket, actor, kind: str, old: str = "", new: str = "") -> None:
    TicketEvent.objects.create(ticket=ticket, actor=actor, kind=kind, old_value=old[:200], new_value=new[:200])


def _notify(recipients, *, actor, ticket: Ticket, title: str, body: str = "", color: str = Notification.Color.PRIMARY):
    """Avisa a cada persona (sin repetir y nunca a quien hizo la acción)."""
    seen = {actor.pk}
    for user in recipients:
        if user is None or user.pk in seen:
            continue
        seen.add(user.pk)
        notify(
            recipient=user, title=title, body=body or ticket.title, icon="bx-support", color=color,
            url=f"/helpdesk/?ticket={ticket.pk}",
        )


def _attention_team(ticket: Ticket):
    """A quién avisar cuando habla quien levantó el ticket: su responsable o, si no tiene, los agentes."""
    return [ticket.assignee] if ticket.assignee_id else list(department_agents(ticket.department_id))


def create_ticket(*, requester, category_id, title: str, description: str, files=()) -> Ticket:
    """Levanta un ticket en el departamento de la categoría y avisa a sus agentes."""
    category = active_categories().filter(pk=category_id).first() if category_id else None
    if category is None:
        raise ValidationError({"category": "Elige una categoría válida."})
    title = _clean_title(title)
    description = _clean_body(description, "description", TICKET_DESCRIPTION_MAX_LENGTH, required=True)
    checked = _check_files(files)

    with transaction.atomic():
        ticket = Ticket.objects.create(
            requester=requester, category=category, department=category.department, title=title,
            description=description,
        )
        _event(ticket, requester, TicketEvent.Kind.CREATED, new=category.name)
        _save_files(ticket, requester, checked)
    _notify(
        department_agents(ticket.department_id), actor=requester, ticket=ticket,
        title=f"Nuevo ticket {ticket.folio} para {ticket.department.name}",
    )
    return ticket


def _ensure_not_closed(ticket: Ticket) -> None:
    if ticket.is_closed:
        raise ValidationError({"status": "El ticket está cerrado: ya no se puede cambiar."})


def _set_status(ticket: Ticket, user, new_status: str, *, agent: bool) -> bool:
    """Aplica el cambio de estado (fechas incluidas). Devuelve si cambió."""
    if new_status not in Status.values:
        raise ValidationError({"status": "Estado no válido."})
    if new_status == ticket.status:
        return False
    if not agent:
        if ticket.requester_id != user.pk or new_status not in REQUESTER_STATUSES:
            raise PermissionDenied("Solo los agentes del departamento pueden cambiar ese estado.")
        if new_status == Status.OPEN and ticket.status != Status.RESOLVED:
            raise ValidationError({"status": "Solo se puede reabrir un ticket resuelto."})
    now = timezone.now()
    if new_status == Status.RESOLVED:
        ticket.resolved_at = now
    elif new_status in (Status.OPEN, Status.IN_PROGRESS, Status.WAITING):
        ticket.resolved_at = None
    if new_status == Status.CLOSED:
        ticket.closed_at = now
    _event(ticket, user, TicketEvent.Kind.STATUS, ticket.status, new_status)
    ticket.status = new_status
    return True


def _set_assignee(ticket: Ticket, user, assignee_id) -> bool:
    if assignee_id in (None, ""):
        assignee = None
    else:
        assignee = department_agents(ticket.department_id).filter(pk=assignee_id).first()
        if assignee is None:
            raise ValidationError({"assignee": "Esa persona no atiende tickets de este departamento."})
    if (assignee.pk if assignee else None) == ticket.assignee_id:
        return False
    _event(
        ticket, user, TicketEvent.Kind.ASSIGNEE,
        ticket.assignee.display_name if ticket.assignee_id else "", assignee.display_name if assignee else "",
    )
    ticket.assignee = assignee
    return True


def _set_category(ticket: Ticket, user, category_id) -> bool:
    category = active_categories().filter(pk=category_id).first() if category_id else None
    if category is None:
        raise ValidationError({"category": "Elige una categoría válida."})
    if category.pk == ticket.category_id:
        return False
    _event(ticket, user, TicketEvent.Kind.CATEGORY, ticket.category.name, category.name)
    ticket.category = category
    if category.department_id != ticket.department_id:
        ticket.department = category.department
        # Quien lo tenía puede no atender el nuevo departamento: queda sin responsable.
        if ticket.assignee_id and not department_agents(category.department_id).filter(pk=ticket.assignee_id).exists():
            _event(ticket, user, TicketEvent.Kind.ASSIGNEE, ticket.assignee.display_name, "")
            ticket.assignee = None
    return True


def update_ticket(*, user, ticket: Ticket, status=UNSET, priority=UNSET, assignee_id=UNSET, category_id=UNSET) -> Ticket:
    """Cambia solo lo que se mande. Agentes: todo. Quien lo levantó: solo cerrar o reabrir (``status``)."""
    _ensure_not_closed(ticket)
    agent = is_agent(user, ticket.department_id)
    if not agent and (priority is not UNSET or assignee_id is not UNSET or category_id is not UNSET):
        raise PermissionDenied("Solo los agentes del departamento pueden atender el ticket.")
    if not agent and ticket.requester_id != user.pk:
        raise PermissionDenied("Solo quien levantó el ticket o sus agentes pueden cambiarlo.")

    old_department_id, old_assignee_id = ticket.department_id, ticket.assignee_id
    with transaction.atomic():
        transferred = category_id is not UNSET and _set_category(ticket, user, category_id)
        if priority is not UNSET and priority != ticket.priority:
            if priority not in Ticket.Priority.values:
                raise ValidationError({"priority": "Prioridad no válida."})
            _event(ticket, user, TicketEvent.Kind.PRIORITY, ticket.priority, priority)
            ticket.priority = priority
        if assignee_id is not UNSET:
            _set_assignee(ticket, user, assignee_id)
        status_changed = status is not UNSET and _set_status(ticket, user, status, agent=agent)
        if status_changed and agent and ticket.status == Status.IN_PROGRESS and not ticket.assignee_id:
            _set_assignee(ticket, user, user.pk)   # quien lo pone «En proceso» lo toma
        ticket.save()

    if status_changed:
        label = ticket.get_status_display()
        if agent:
            color = Notification.Color.SUCCESS if ticket.status == Status.RESOLVED else Notification.Color.PRIMARY
            _notify([ticket.requester], actor=user, ticket=ticket, title=f"Tu ticket {ticket.folio} está «{label}»",
                    color=color)
        else:
            _notify(_attention_team(ticket), actor=user, ticket=ticket,
                    title=f"{user.display_name} dejó el ticket {ticket.folio} «{label}»")
    if ticket.assignee_id and ticket.assignee_id != old_assignee_id:
        _notify([ticket.assignee], actor=user, ticket=ticket, title=f"Te asignaron el ticket {ticket.folio}")
    if transferred and ticket.department_id != old_department_id:
        _notify(department_agents(ticket.department_id), actor=user, ticket=ticket,
                title=f"Ticket {ticket.folio} transferido a {ticket.department.name}")
    return ticket


def add_comment(*, user, ticket: Ticket, body: str, is_internal: bool = False, files=()) -> TicketComment:
    """Responde en el ticket. Notas internas: solo agentes. Hace falta mensaje o al menos un archivo."""
    _ensure_not_closed(ticket)
    agent = is_agent(user, ticket.department_id)
    is_requester = ticket.requester_id == user.pk
    if not agent and not is_requester:
        raise PermissionDenied("Solo quien levantó el ticket o sus agentes pueden responder.")
    if is_internal and not agent:
        raise PermissionDenied("Solo los agentes pueden dejar notas internas.")
    checked = _check_files(files)
    body = _clean_body(body, "body", COMMENT_BODY_MAX_LENGTH, required=not checked)

    with transaction.atomic():
        comment = TicketComment.objects.create(ticket=ticket, author=user, body=body, is_internal=is_internal)
        _save_files(ticket, user, checked, comment)
        if agent and not is_requester and not is_internal and ticket.first_response_at is None:
            ticket.first_response_at = comment.created_at
        if is_requester and not agent and ticket.status == Status.WAITING:
            _set_status(ticket, user, Status.IN_PROGRESS, agent=True)   # respondió lo que se le pidió
        ticket.save()

    if is_internal:
        _notify([ticket.assignee], actor=user, ticket=ticket, title=f"Nota interna en el ticket {ticket.folio}",
                body=body)
    elif is_requester:
        _notify(_attention_team(ticket), actor=user, ticket=ticket,
                title=f"{user.display_name} respondió en el ticket {ticket.folio}", body=body)
    else:
        _notify([ticket.requester], actor=user, ticket=ticket, title=f"Respuesta en tu ticket {ticket.folio}",
                body=body)
    return comment
