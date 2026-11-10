"""Responder un formulario.

Cada respuesta se valida contra su tipo de pregunta (ver ``models.questions``): opciones que sean de
esa pregunta y estén vigentes, número dentro de la escala, fechas y horas válidas, mínimos y máximos de
casillas, y que las obligatorias tengan respuesta (en cuadrículas, todas las filas). Si algo falla no
se guarda nada y se devuelven los errores **por pregunta** para mostrarlos junto a cada una.

Con «un envío por persona», un segundo envío se rechaza (se bloquea el formulario mientras se revisa,
así dos envíos al mismo tiempo no pasan los dos).
"""
from datetime import date, time

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.form_builder.models import ANSWER_TEXT_MAX_LENGTH, Answer, DynamicForm, Question, Submission

SHORT_TEXT_MAX_LENGTH = 500
Kind = Question.Kind


class AnswerErrors(Exception):
    """Errores por pregunta: ``{question_id: "mensaje"}``."""

    def __init__(self, errors: dict[int, str]):
        super().__init__("Revisa las respuestas.")
        self.errors = errors


def _ids(value) -> list[int]:
    if value in (None, ""):
        return []
    values = value if isinstance(value, list) else [value]
    try:
        return [int(item) for item in values]
    except (TypeError, ValueError):
        raise ValueError("Elige una opción válida.") from None


def _check(question: Question, payload: dict) -> list[dict]:
    """Devuelve las filas de ``Answer`` a crear (vacía si no contestó). Lanza ``ValueError`` con el mensaje."""
    kind = question.kind
    live = [option for option in question.options.all()]   # ya viene filtrado a opciones vigentes
    columns = {option.pk for option in live if option.role == "option"}
    rows = {option.pk: option for option in live if option.role == "row"}

    if kind in Question.TEXT_KINDS:
        text = str(payload.get("text") or "").replace("\r\n", "\n").strip()
        limit = SHORT_TEXT_MAX_LENGTH if kind == Kind.SHORT_TEXT else ANSWER_TEXT_MAX_LENGTH
        if len(text) > limit:
            raise ValueError(f"Máximo {limit} caracteres.")
        if kind == Kind.SHORT_TEXT and "\n" in text:
            text = " ".join(text.split())
        return [{"text": text}] if text else []

    if kind in Question.CHOICE_KINDS:
        chosen = _ids(payload.get("options"))
        if len(set(chosen)) != len(chosen) or not set(chosen) <= columns:
            raise ValueError("Esa opción ya no está disponible; recarga el formulario.")
        other = " ".join(str(payload.get("other") or "").split()) if question.has_other_option else ""
        if len(other) > 300:
            raise ValueError("«Otro» admite máximo 300 caracteres.")
        count = len(chosen) + (1 if other else 0)
        if count == 0:
            return []
        if kind != Kind.MULTIPLE_CHOICE and count > 1:
            raise ValueError("Elige solo una opción.")
        if kind == Kind.MULTIPLE_CHOICE:
            if question.min_choices and count < question.min_choices:
                raise ValueError(f"Elige al menos {question.min_choices}.")
            if question.max_choices and count > question.max_choices:
                raise ValueError(f"Elige máximo {question.max_choices}.")
        return [{"options": chosen, "text": other}]

    if kind in Question.SCALE_KINDS:
        value = payload.get("number")
        if value in (None, ""):
            return []
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValueError("Elige un valor de la escala.") from None
        low = 1 if kind == Kind.RATING else question.scale_min
        if not low <= number <= question.scale_max:
            raise ValueError(f"Elige un valor entre {low} y {question.scale_max}.")
        return [{"number": number}]

    if kind in Question.GRID_KINDS:
        given = payload.get("rows") or {}
        if not isinstance(given, dict):
            raise ValueError("Respuesta no válida.")
        result = []
        for raw_row, raw_options in given.items():
            row_id = _ids(raw_row)[0] if str(raw_row).strip() else None
            if row_id not in rows:
                raise ValueError("Esa fila ya no está disponible; recarga el formulario.")
            chosen = _ids(raw_options)
            if not chosen:
                continue
            if len(set(chosen)) != len(chosen) or not set(chosen) <= columns:
                raise ValueError("Esa columna ya no está disponible; recarga el formulario.")
            if kind == Kind.SINGLE_CHOICE_GRID and len(chosen) > 1:
                raise ValueError(f"Elige solo una opción en «{rows[row_id].text}».")
            result.append({"row": rows[row_id], "options": chosen})
        if question.is_required and result and len(result) < len(rows):
            raise ValueError("Contesta todas las filas.")
        return result

    if kind == Kind.DATE:
        value = str(payload.get("date") or "").strip()
        if not value:
            return []
        try:
            return [{"date": date.fromisoformat(value)}]
        except ValueError:
            raise ValueError("Escribe una fecha válida.") from None

    if kind == Kind.TIME:
        value = str(payload.get("time") or "").strip()
        if not value:
            return []
        try:
            parsed = time.fromisoformat(value)
        except ValueError:
            raise ValueError("Escribe una hora válida.") from None
        return [{"time": parsed.replace(second=0, microsecond=0)}]
    return []


def submit(*, user, form: DynamicForm, answers) -> Submission:
    """Guarda un envío. ``answers``: lista de ``{"question": id, "text"?, "options"?, "other"?, "number"?,
    "date"?, "time"?, "rows"? ({fila: [columnas]})}``. Errores generales: ``ValidationError``; por pregunta:
    ``AnswerErrors``."""
    if not form.is_accepting_submissions:
        raise ValidationError({"form": "Este formulario ya no recibe respuestas."})
    if not isinstance(answers, list):
        raise ValidationError({"answers": "Las respuestas no son válidas."})

    questions = list(form.questions.all())   # con sus opciones vigentes (selectors.form_with_questions)
    by_id = {question.pk: question for question in questions}
    payloads = {}
    for item in answers:
        question_id = item.get("question") if isinstance(item, dict) else None
        if question_id not in by_id:
            raise ValidationError({"answers": "Hay respuestas a preguntas que ya no existen; recarga el formulario."})
        payloads[question_id] = item

    errors, prepared = {}, {}
    for question in questions:
        try:
            rows = _check(question, payloads.get(question.pk, {}))
        except ValueError as exc:
            errors[question.pk] = str(exc)
            continue
        if question.is_required and not rows:
            errors[question.pk] = "Esta pregunta es obligatoria."
            continue
        prepared[question.pk] = rows
    if errors:
        raise AnswerErrors(errors)

    with transaction.atomic():
        DynamicForm.objects.select_for_update().filter(pk=form.pk).first()
        if form.one_submission_per_user and Submission.objects.filter(form=form, respondent=user).exists():
            raise ValidationError({"form": "Ya respondiste este formulario."})
        submission = Submission.objects.create(form=form, respondent=user)
        for question in questions:
            for row in prepared.get(question.pk, []):
                options = row.pop("options", [])
                answer = Answer.objects.create(submission=submission, question=question, **row)
                if options:
                    answer.options.set(options)
    return submission
