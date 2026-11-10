"""Resultados de un formulario: resumen por pregunta (para las gráficas) y la tabla completa (CSV).

Cuenta con las opciones por id, así que una opción cuyo texto se corrigió sigue sumando, y una
archivada aparece (marcada) si alguien la eligió.
"""
from collections import Counter, defaultdict

from django.db.models import Count, Prefetch
from django.utils import timezone

from apps.form_builder.models import Answer, AnswerChoice, DynamicForm, Question, QuestionOption, Submission

TEXT_SAMPLE = 200   # respuestas libres que se muestran por pregunta (las más recientes)


def _options(question: Question, role: str) -> list[QuestionOption]:
    """Opciones vigentes en orden y, al final, las archivadas que alguien eligió."""
    return [option for option in question.all_options if option.role == role
            and (option.archived_at is None or option.used)]


def form_results(form: DynamicForm) -> dict:
    submissions = Submission.objects.filter(form=form)
    used_ids = set(AnswerChoice.objects.filter(answer__submission__form=form).values_list("option_id", flat=True))
    used_ids |= set(Answer.objects.filter(submission__form=form, row__isnull=False).values_list("row_id", flat=True))
    questions = list(form.questions.order_by("position", "id").prefetch_related(
        Prefetch("options", queryset=QuestionOption.objects.order_by("role", "position", "id"), to_attr="all_options"),
    ))
    for question in questions:
        for option in question.all_options:
            option.used = option.pk in used_ids

    answers = Answer.objects.filter(submission__form=form)
    responses = dict(answers.values("question").annotate(n=Count("submission", distinct=True)).values_list("question", "n"))
    choice_counts = Counter(
        (row["answer__question"], row["answer__row"], row["option"])
        for row in AnswerChoice.objects.filter(answer__submission__form=form).values("answer__question", "answer__row", "option")
    )
    numbers, dates, times, texts, others = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter), defaultdict(list), defaultdict(list)
    for answer in answers.select_related("submission__respondent", "question").order_by("-submission__submitted_at", "-id"):
        if answer.number is not None:
            numbers[answer.question_id][answer.number] += 1
        if answer.date:
            dates[answer.question_id][answer.date.isoformat()] += 1
        if answer.time:
            times[answer.question_id][answer.time.strftime("%H:%M")] += 1
        if answer.text:
            target = others if answer.question.kind in Question.CHOICE_KINDS else texts
            if len(target[answer.question_id]) < TEXT_SAMPLE:
                target[answer.question_id].append({
                    "text": answer.text, "respondent": answer.submission.respondent.display_name,
                    "submitted_at": answer.submission.submitted_at,
                })

    summary = []
    for question in questions:
        item = {"id": question.pk, "kind": question.kind, "title": question.title, "responses": responses.get(question.pk, 0)}
        if question.kind in Question.TEXT_KINDS:
            item["texts"] = texts[question.pk]
        elif question.kind in Question.CHOICE_KINDS:
            item["options"] = [
                {"id": option.pk, "text": option.text, "archived": option.archived_at is not None,
                 "count": choice_counts[(question.pk, None, option.pk)]}
                for option in _options(question, "option")
            ]
            item["other"] = others[question.pk]
        elif question.kind in Question.SCALE_KINDS:
            low = 1 if question.kind == Question.Kind.RATING else question.scale_min
            counts = numbers[question.pk]
            total = sum(counts.values())
            item.update({
                "scale_min": low, "scale_max": question.scale_max,
                "scale_min_label": question.scale_min_label, "scale_max_label": question.scale_max_label,
                "distribution": [{"value": value, "count": counts[value]} for value in range(low, question.scale_max + 1)],
                "average": round(sum(value * n for value, n in counts.items()) / total, 2) if total else None,
            })
        elif question.kind in Question.GRID_KINDS:
            columns = _options(question, "option")
            item["columns"] = [{"id": option.pk, "text": option.text, "archived": option.archived_at is not None} for option in columns]
            item["rows"] = [
                {"id": row.pk, "text": row.text, "archived": row.archived_at is not None,
                 "counts": [choice_counts[(question.pk, row.pk, column.pk)] for column in columns]}
                for row in _options(question, "row")
            ]
        else:
            counts = dates[question.pk] if question.kind == Question.Kind.DATE else times[question.pk]
            item["values"] = [{"value": value, "count": n} for value, n in sorted(counts.items())]
        summary.append(item)

    last = submissions.order_by("-submitted_at").values_list("submitted_at", flat=True).first()
    return {
        "submissions_count": submissions.count(),
        "respondents_count": submissions.values("respondent").distinct().count(),
        "last_submitted_at": last,
        "questions": summary,
    }


def results_table(form: DynamicForm) -> tuple[list[str], list[list[str]]]:
    """Encabezados y filas (un envío por fila, más antiguos primero) para exportar. Las cuadrículas van una
    columna por fila: «Pregunta [fila]»."""
    questions = list(form.questions.order_by("position", "id").prefetch_related(
        Prefetch("options", queryset=QuestionOption.objects.filter(role="row").order_by("position", "id"), to_attr="grid_rows"),
    ))
    columns: list[tuple[int, int | None]] = []
    headers = ["Fecha", "Persona", "Correo"]
    for question in questions:
        if question.kind in Question.GRID_KINDS:
            for row in question.grid_rows:
                columns.append((question.pk, row.pk))
                headers.append(f"{question.title} [{row.text}]")
        else:
            columns.append((question.pk, None))
            headers.append(question.title)

    submissions = (
        Submission.objects.filter(form=form).select_related("respondent").order_by("submitted_at", "id")
        .prefetch_related(Prefetch("answers", queryset=Answer.objects.prefetch_related("options")))
    )
    rows = []
    for submission in submissions:
        cells = {}
        for answer in submission.answers.all():
            parts = [option.text for option in answer.options.all()]
            if answer.text:
                parts.append(answer.text)
            if answer.number is not None:
                parts.append(str(answer.number))
            if answer.date:
                parts.append(answer.date.isoformat())
            if answer.time:
                parts.append(answer.time.strftime("%H:%M"))
            cells[(answer.question_id, answer.row_id)] = "; ".join(parts)
        rows.append([
            timezone.localtime(submission.submitted_at).strftime("%Y-%m-%d %H:%M"), submission.respondent.display_name, submission.respondent.email,
            *[cells.get(key, "") for key in columns],
        ])
    return headers, rows
