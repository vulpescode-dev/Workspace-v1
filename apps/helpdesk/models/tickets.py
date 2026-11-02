"""Tickets de la mesa de ayuda, su conversación, adjuntos e historial.

- ``TicketCategory``: qué se pide y **qué departamento lo atiende**. Las define la empresa en el admin.
- ``Ticket``: lo levanta una persona (``requester``); el departamento sale de la categoría y un
  agente lo toma (``assignee``). Folio legible: ``HD-00042``.
- ``TicketComment``: respuestas públicas y notas internas (solo las ven los agentes).
- ``TicketAttachment``: archivos validados con ``apps.core.uploads.check_document_upload``, guardados
  como ``helpdesk/tickets/<ticket_id>/<id>.<ext>`` y entregados por una vista autorizada.
- ``TicketEvent``: historial («cambió el estado a Resuelto», «asignó a Ana»…).
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

TICKET_TITLE_MAX_LENGTH = 150
TICKET_DESCRIPTION_MAX_LENGTH = 5000
COMMENT_BODY_MAX_LENGTH = 5000
TICKET_MAX_FILES_PER_MESSAGE = 5


class TicketCategory(models.Model):
    """Tipo de ticket y departamento que lo atiende. Desactivada: ya no se puede elegir, los tickets la conservan."""

    class Kind(models.TextChoices):
        INCIDENT = "incident", "Incidencia"
        REQUEST = "request", "Solicitud"

    department = models.ForeignKey(
        "org.Department", on_delete=models.PROTECT, related_name="ticket_categories", verbose_name="departamento",
    )
    name = models.CharField("nombre", max_length=120)
    kind = models.CharField("tipo", max_length=10, choices=Kind.choices, default=Kind.REQUEST)
    description = models.CharField("descripción", max_length=300, blank=True, help_text="Ayuda para elegirla.")
    position = models.PositiveSmallIntegerField("orden", default=0)
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "categoría de ticket"
        verbose_name_plural = "categorías de ticket"
        ordering = ["department__name", "position", "name"]
        constraints = [models.UniqueConstraint(fields=["department", "name"], name="ticket_category_unique_name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.department})"


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Abierto"
        IN_PROGRESS = "in_progress", "En proceso"
        WAITING = "waiting", "En espera"           # esperando a quien lo levantó o a un tercero
        RESOLVED = "resolved", "Resuelto"         # quien lo levantó puede confirmarlo (cerrar) o reabrirlo
        CLOSED = "closed", "Cerrado"              # final

    class Priority(models.TextChoices):
        LOW = "low", "Baja"
        NORMAL = "normal", "Normal"
        HIGH = "high", "Alta"
        URGENT = "urgent", "Urgente"

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_requested",
        verbose_name="levantado por",
    )
    category = models.ForeignKey(
        TicketCategory, on_delete=models.PROTECT, related_name="tickets", verbose_name="categoría",
    )
    department = models.ForeignKey(
        "org.Department", on_delete=models.PROTECT, related_name="tickets", verbose_name="departamento",
        help_text="Sale de la categoría; cambia si el ticket se transfiere a otra categoría.",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tickets_assigned", verbose_name="responsable",
    )
    title = models.CharField("título", max_length=TICKET_TITLE_MAX_LENGTH)
    description = models.TextField("descripción", max_length=TICKET_DESCRIPTION_MAX_LENGTH)
    status = models.CharField("estado", max_length=12, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField("prioridad", max_length=8, choices=Priority.choices, default=Priority.NORMAL)
    created_at = models.DateTimeField("creado el", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("actualizado el", auto_now=True)
    first_response_at = models.DateTimeField("primera respuesta", null=True, blank=True)
    resolved_at = models.DateTimeField("resuelto el", null=True, blank=True)
    closed_at = models.DateTimeField("cerrado el", null=True, blank=True)

    class Meta:
        verbose_name = "ticket"
        verbose_name_plural = "tickets"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["department", "status"], name="ticket_department_status_idx"),
            models.Index(fields=["requester", "-created_at"], name="ticket_requester_created_idx"),
            models.Index(fields=["assignee", "status"], name="ticket_assignee_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.folio} · {self.title}"

    @property
    def folio(self) -> str:
        return f"HD-{self.pk:05d}" if self.pk else "HD-nuevo"

    @property
    def is_closed(self) -> bool:
        return self.status == self.Status.CLOSED


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments", verbose_name="ticket")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_comments", verbose_name="autor(a)",
    )
    body = models.TextField("mensaje", max_length=COMMENT_BODY_MAX_LENGTH)
    is_internal = models.BooleanField("nota interna", default=False, help_text="Solo la ven los agentes.")
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        verbose_name = "comentario de ticket"
        verbose_name_plural = "comentarios de ticket"
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"{self.ticket.folio}: {self.body[:40]}"


def ticket_attachment_path(instance, filename: str) -> str:
    # ``filename`` ya llega como "<id>.<ext>" desde services.tickets.
    return f"helpdesk/tickets/{instance.ticket_id}/{filename}"


class TicketAttachment(models.Model):
    """Archivo del ticket (al crearlo) o de un comentario. Si el comentario es interno, el archivo también."""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments", verbose_name="ticket")
    comment = models.ForeignKey(
        TicketComment, on_delete=models.CASCADE, null=True, blank=True, related_name="attachments",
        verbose_name="comentario",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_attachments", verbose_name="subido por",
    )
    file = models.FileField("archivo", upload_to=ticket_attachment_path, max_length=255, blank=True)
    original_name = models.CharField("nombre original", max_length=255, blank=True)
    content_type = models.CharField("tipo MIME", max_length=100)
    size = models.PositiveBigIntegerField("tamaño (bytes)")
    created_at = models.DateTimeField("subido el", auto_now_add=True)

    class Meta:
        verbose_name = "adjunto de ticket"
        verbose_name_plural = "adjuntos de ticket"
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return self.original_name or self.file.name or f"adjunto {self.pk}"


@receiver(post_delete, sender=TicketAttachment)
def _delete_attachment_file(sender, instance, **kwargs):
    """Al borrar el registro (o su ticket) se borra también el archivo del disco."""
    if instance.file:
        instance.file.delete(save=False)


class TicketEvent(models.Model):
    """Historial del ticket. ``old_value``/``new_value`` guardan el código (estado, prioridad) o el nombre
    (responsable, categoría) tal como estaba en ese momento."""

    class Kind(models.TextChoices):
        CREATED = "created", "Creado"
        STATUS = "status", "Cambio de estado"
        PRIORITY = "priority", "Cambio de prioridad"
        ASSIGNEE = "assignee", "Cambio de responsable"
        CATEGORY = "category", "Cambio de categoría"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="events", verbose_name="ticket")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_events", verbose_name="quién",
    )
    kind = models.CharField("tipo", max_length=10, choices=Kind.choices)
    old_value = models.CharField("antes", max_length=200, blank=True)
    new_value = models.CharField("después", max_length=200, blank=True)
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        verbose_name = "evento de ticket"
        verbose_name_plural = "historial de tickets"
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"{self.ticket.folio}: {self.get_kind_display()}"
