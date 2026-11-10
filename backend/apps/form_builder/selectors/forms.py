"""Quién ve, quién responde y quién administra cada formulario.

- **Crear** formularios: permiso de negocio ``forms.forms.create`` (un superusuario lo tiene).
- **Ver y responder**: cualquier persona activa ve los formularios abiertos o cerrados de la empresa;
  solo responde los que aceptan envíos (``DynamicForm.is_accepting_submissions``).
- Los **borradores** solo los ve quien los creó.
- **Administrar** (editar, preguntas, resultados, eliminar): solo quien lo creó.
- Lo eliminado (borrado suave) nunca se devuelve.
"""
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.utils import timezone

from apps.accounts.services.permissions import has_permission
from apps.form_builder.models import DynamicForm, Question, QuestionOption, Submission

CREATE_PERMISSION = "forms.forms.create"
SCOPES = ("pending", "mine")


def _is_active(user) -> bool:
    return getattr(user, "is_authenticated", False) and user.is_active


def can_create(user) -> bool:
    return _is_active(user) and has_permission(user, CREATE_PERMISSION)


def can_manage(user, form: DynamicForm) -> bool:
    return _is_active(user) and form.owner_id == user.pk


def visible_forms(user):
    """Formularios vivos que ``user`` puede abrir, con su dueño, cuántos envíos tienen y si ya respondió."""
    if not _is_active(user):
        return DynamicForm.objects.none()
    return (
        DynamicForm.objects.filter(deleted_at__isnull=True)
        .filter(~Q(status=DynamicForm.Status.DRAFT) | Q(owner=user))
        .select_related("owner")
        .annotate(
            submissions_count=Count("submissions", distinct=True),
            questions_count=Count("questions", distinct=True),
            submitted=Exists(Submission.objects.filter(form=OuterRef("pk"), respondent=user)),
        )
        .order_by("-created_at", "-id")
    )


def accepting_now():
    """Condición «recibe envíos ahora» para filtrar en la base (igual que ``is_accepting_submissions``)."""
    now = timezone.now()
    return (
        Q(status=DynamicForm.Status.OPEN)
        & (Q(opens_at__isnull=True) | Q(opens_at__lte=now))
        & (Q(closes_at__isnull=True) | Q(closes_at__gt=now))
    )


def filter_forms(qs, user, *, scope: str = "", query: str = ""):
    """``pending``: abiertos que aún no respondo (o que permiten varios envíos). ``mine``: los que creé
    (borradores incluidos). Sin ``scope``: todos los que no son borradores. ``query`` busca en el título."""
    if scope == "mine":
        qs = qs.filter(owner=user)
    else:
        qs = qs.exclude(status=DynamicForm.Status.DRAFT)
        if scope == "pending":
            qs = qs.filter(accepting_now()).filter(Q(submitted=False) | Q(one_submission_per_user=False))
    if query:
        qs = qs.filter(title__icontains=query)
    return qs


def form_with_questions(qs):
    """Agrega las preguntas en orden con sus opciones vigentes (opciones y filas)."""
    live_options = QuestionOption.objects.filter(archived_at__isnull=True).order_by("role", "position", "id")
    return qs.prefetch_related(
        Prefetch("questions", queryset=Question.objects.order_by("position", "id").prefetch_related(
            Prefetch("options", queryset=live_options),
        )),
    )
