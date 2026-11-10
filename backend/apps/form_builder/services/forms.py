"""Crear y editar formularios y sus preguntas (el «editor», como en Google Forms).

- Crear: ``forms.forms.create``. Nace como **borrador** (nadie lo ve ni responde).
- Editar, abrir, cerrar y eliminar: solo quien lo creó. Abrirlo exige al menos una pregunta.
- Las preguntas se guardan **todas juntas** (``save_questions``): la lista que llega es la versión
  nueva completa, en orden. Las preguntas que ya no vienen se borran con sus respuestas; las opciones
  que ya no vienen se borran, o se **archivan** si alguien ya las eligió (sus respuestas se conservan).
- Una pregunta con respuestas no puede cambiar de tipo (las respuestas dejarían de tener sentido).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.form_builder.models import DynamicForm, Question, QuestionOption
from apps.accounts.services.permissions import has_permission
from apps.form_builder.selectors.forms import can_create, can_manage

TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000
MAX_QUESTIONS = 100
MAX_OPTIONS = 50
UNSET = object()   # al editar: distingue «no se mandó» de «se mandó vacío»
Kind = Question.Kind
Role = QuestionOption.Role


def _clean_title(title: str) -> str:
    title = " ".join((title or "").split())
    if not title:
        raise ValidationError({"title": "Escribe un título."})
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError({"title": f"Máximo {TITLE_MAX_LENGTH} caracteres."})
    return title


def _clean_description(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").strip()
    if len(text) > DESCRIPTION_MAX_LENGTH:
        raise ValidationError({"description": f"Máximo {DESCRIPTION_MAX_LENGTH} caracteres."})
    return text


def create_form(*, owner, title: str, description: str = "") -> DynamicForm:
    if not can_create(owner):
        raise PermissionDenied("No tienes permiso para crear formularios.")
    return DynamicForm.objects.create(owner=owner, title=_clean_title(title), description=_clean_description(description))


def _ensure_owner(user, form: DynamicForm, moderation: str = "forms.forms.update.all") -> None:
    """Quien lo creó, o alguien con ``moderation`` (``forms.forms.update.all`` / ``.delete.all``)."""
    if not can_manage(user, form) and not has_permission(user, moderation):
        raise PermissionDenied("Solo quien creó el formulario puede cambiarlo.")


def update_form(*, user, form: DynamicForm, title=UNSET, description=UNSET, status=UNSET, opens_at=UNSET,
                closes_at=UNSET, one_submission_per_user=UNSET) -> DynamicForm:
    """Cambia solo lo que se mande."""
    _ensure_owner(user, form)
    if title is not UNSET:
        form.title = _clean_title(title)
    if description is not UNSET:
        form.description = _clean_description(description)
    if one_submission_per_user is not UNSET:
        form.one_submission_per_user = bool(one_submission_per_user)
    if opens_at is not UNSET:
        form.opens_at = opens_at
    if closes_at is not UNSET:
        form.closes_at = closes_at
    if form.opens_at and form.closes_at and form.closes_at <= form.opens_at:
        raise ValidationError({"closes_at": "La fecha de cierre debe ser después de la de apertura."})
    if status is not UNSET:
        if status not in DynamicForm.Status.values:
            raise ValidationError({"status": "Estado no válido."})
        if status == DynamicForm.Status.OPEN and not form.questions.exists():
            raise ValidationError({"status": "Agrega al menos una pregunta antes de abrirlo."})
        if status == DynamicForm.Status.OPEN and form.closes_at and form.closes_at <= timezone.now():
            raise ValidationError({"closes_at": "La fecha de cierre ya pasó: cámbiala o quítala para abrirlo."})
        form.status = status
    form.save()
    return form


def delete_form(*, user, form: DynamicForm) -> None:
    """Borrado suave: deja de verse; sus envíos se conservan."""
    _ensure_owner(user, form, "forms.forms.delete.all")
    form.soft_delete()


# --- Preguntas ------------------------------------------------------------------

def _text(value, label: str, max_length: int, *, required: bool = False) -> str:
    value = " ".join(str(value or "").split())
    if required and not value:
        raise ValueError(f"escribe {label}.")
    if len(value) > max_length:
        raise ValueError(f"{label} admite máximo {max_length} caracteres.")
    return value


def _int(value, label: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} debe ser un número.") from None


def _clean_choices(items, label: str) -> list[dict]:
    """Lista de ``{"id"?, "text"}`` sin vacíos ni repetidos (sin importar mayúsculas)."""
    if not isinstance(items, list):
        raise ValueError(f"{label} no son válidas.")
    if len(items) > MAX_OPTIONS:
        raise ValueError(f"máximo {MAX_OPTIONS} {label}.")
    cleaned, seen = [], set()
    for item in items:
        item = item if isinstance(item, dict) else {"text": item}
        text = _text(item.get("text"), "el texto de la opción", 300)
        if not text:
            continue
        if text.casefold() in seen:
            raise ValueError(f"«{text}» está repetida.")
        seen.add(text.casefold())
        cleaned.append({"id": _int(item.get("id"), "El id"), "text": text})
    return cleaned


def _clean_question(item) -> dict:
    """Valida una pregunta del editor y devuelve sus campos ya normalizados (lanza ``ValueError``)."""
    if not isinstance(item, dict):
        raise ValueError("no es válida.")
    kind = item.get("kind")
    if kind not in Kind.values:
        raise ValueError("elige un tipo de pregunta.")
    data = {
        "id": _int(item.get("id"), "El id"),
        "kind": kind,
        "title": _text(item.get("title"), "la pregunta", 300, required=True),
        "description": _text(item.get("description"), "la ayuda", 500),
        "is_required": bool(item.get("is_required")),
        "has_other_option": bool(item.get("has_other_option")) and kind in Question.OTHER_OPTION_KINDS,
        "shuffle_options": bool(item.get("shuffle_options")) and kind in Question.CHOICE_KINDS,
        "min_choices": None, "max_choices": None,
        "scale_min": 1, "scale_max": 5, "scale_min_label": "", "scale_max_label": "",
        "options": [], "rows": [],
    }
    if kind in Question.CHOICE_KINDS or kind in Question.GRID_KINDS:
        data["options"] = _clean_choices(item.get("options") or [], "columnas" if kind in Question.GRID_KINDS else "opciones")
        if not data["options"]:
            raise ValueError("agrega al menos una columna." if kind in Question.GRID_KINDS else "agrega al menos una opción.")
    if kind in Question.GRID_KINDS:
        data["rows"] = _clean_choices(item.get("rows") or [], "filas")
        if not data["rows"]:
            raise ValueError("agrega al menos una fila.")
    if kind == Kind.MULTIPLE_CHOICE:
        low, high = _int(item.get("min_choices"), "El mínimo"), _int(item.get("max_choices"), "El máximo")
        available = len(data["options"]) + (1 if data["has_other_option"] else 0)
        if low is not None and not 1 <= low <= available:
            raise ValueError(f"el mínimo de casillas debe estar entre 1 y {available}.")
        if high is not None and not 1 <= high <= available:
            raise ValueError(f"el máximo de casillas debe estar entre 1 y {available}.")
        if low is not None and high is not None and low > high:
            raise ValueError("el mínimo de casillas no puede ser mayor que el máximo.")
        data["min_choices"], data["max_choices"] = low, high
    if kind in Question.SCALE_KINDS:
        low = 1 if kind == Kind.RATING else _int(item.get("scale_min"), "El inicio de la escala")
        high = _int(item.get("scale_max"), "El final de la escala")
        low = 1 if low is None else low
        high = 5 if high is None else high
        if low not in (0, 1):
            raise ValueError("la escala empieza en 0 o en 1.")
        if not 2 <= high <= 10:
            raise ValueError("la escala termina entre 2 y 10.")
        data["scale_min"], data["scale_max"] = low, high
        if kind == Kind.LINEAR_SCALE:
            data["scale_min_label"] = _text(item.get("scale_min_label"), "la etiqueta", 100)
            data["scale_max_label"] = _text(item.get("scale_max_label"), "la etiqueta", 100)
    return data


def _sync_options(question: Question, role: str, items: list[dict]) -> None:
    """Deja las opciones (o filas) de ``question`` iguales a ``items``: actualiza, crea, y borra o archiva."""
    current = {option.pk: option for option in question.options.filter(role=role, archived_at__isnull=True)}
    keep = {item["id"] for item in items if item["id"] in current}
    for option_id, option in current.items():
        if option_id in keep:
            continue
        if option.choices.exists() or option.row_answers.exists():
            option.archived_at = timezone.now()
            option.save(update_fields=["archived_at", "updated_at"])
        else:
            option.delete()
    # Primero un texto temporal: así se pueden intercambiar textos sin chocar con «no repetir».
    for option_id in keep:
        QuestionOption.objects.filter(pk=option_id).update(text=f"__temporal-{option_id}__")
    for position, item in enumerate(items):
        if item["id"] in keep:
            QuestionOption.objects.filter(pk=item["id"]).update(text=item["text"], position=position, updated_at=timezone.now())
        else:
            QuestionOption.objects.create(question=question, role=role, text=item["text"], position=position)


def save_questions(*, user, form: DynamicForm, questions) -> DynamicForm:
    """Guarda la lista completa de preguntas, en orden. Errores: ``{"questions": "Pregunta 3: …"}``."""
    _ensure_owner(user, form)
    if not isinstance(questions, list):
        raise ValidationError({"questions": "La lista de preguntas no es válida."})
    if len(questions) > MAX_QUESTIONS:
        raise ValidationError({"questions": f"Máximo {MAX_QUESTIONS} preguntas por formulario."})
    if not questions and form.status == DynamicForm.Status.OPEN:
        raise ValidationError({"questions": "Un formulario abierto necesita al menos una pregunta."})

    existing = {question.pk: question for question in form.questions.all()}
    cleaned = []
    for number, item in enumerate(questions, start=1):
        try:
            data = _clean_question(item)
            current = existing.get(data["id"])
            if data["id"] is not None and current is None:
                raise ValueError("ya no existe; recarga el formulario.")
            if current and current.kind != data["kind"] and current.answers.exists():
                raise ValueError("ya tiene respuestas: no se puede cambiar de tipo (crea una nueva).")
        except ValueError as exc:
            message = str(exc)
            raise ValidationError({"questions": f"Pregunta {number}: {message[0].lower()}{message[1:]}"}) from None
        cleaned.append(data)

    with transaction.atomic():
        keep = {data["id"] for data in cleaned if data["id"]}
        form.questions.exclude(pk__in=keep).delete()   # con sus respuestas, como en Google Forms
        fields = ["kind", "title", "description", "is_required", "has_other_option", "shuffle_options", "min_choices",
                  "max_choices", "scale_min", "scale_max", "scale_min_label", "scale_max_label"]
        for position, data in enumerate(cleaned):
            values = {field: data[field] for field in fields}
            if data["id"]:
                question = existing[data["id"]]
                for field, value in values.items():
                    setattr(question, field, value)
                question.position = position
                question.save()
            else:
                question = Question.objects.create(form=form, position=position, **values)
            _sync_options(question, Role.OPTION, data["options"])
            _sync_options(question, Role.ROW, data["rows"])
        form.save(update_fields=["updated_at"])
    return form
