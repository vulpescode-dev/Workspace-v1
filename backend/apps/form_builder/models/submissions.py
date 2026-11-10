"""Envíos: un ``Submission`` por cada vez que alguien envía el formulario, con sus ``Answer``.

Dónde queda cada tipo de respuesta (ver ``questions.py``):

- ``Answer.text``: respuesta corta, párrafo y el texto de «Otro».
- ``Answer.options`` (tabla ``AnswerChoice``): opciones elegidas (radio, desplegable, casillas y
  columnas de cuadrícula). Una fila por opción elegida: contar respuestas por opción es un
  ``COUNT`` agrupado, sin leer ni separar textos.
- ``Answer.number``: escala lineal y calificación.
- ``Answer.date`` / ``Answer.time``: fecha y hora.
- ``Answer.row``: solo en cuadrículas; un ``Answer`` por fila contestada.

Una pregunta tiene a lo más un ``Answer`` por envío (uno por fila en las cuadrículas).
"""
from django.conf import settings
from django.db import models
from django.db.models import Q

from .forms import DynamicForm
from .questions import Question, QuestionOption

ANSWER_TEXT_MAX_LENGTH = 5000


class Submission(models.Model):
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name="submissions", verbose_name="formulario")
    respondent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="form_submissions", verbose_name="quién respondió"
    )
    submitted_at = models.DateTimeField("enviado el", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "envío"
        verbose_name_plural = "envíos"
        ordering = ["-submitted_at", "-id"]
        indexes = [models.Index(fields=["form", "respondent"], name="submission_form_respondent_idx")]

    def __str__(self) -> str:
        return f"{self.respondent} · {self.form}"


class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers", verbose_name="envío")
    # Si se borra la pregunta, sus respuestas se van con ella (como en Google Forms).
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers", verbose_name="pregunta")
    row = models.ForeignKey(
        QuestionOption, on_delete=models.RESTRICT, null=True, blank=True, related_name="row_answers",
        verbose_name="fila", help_text="Solo cuadrículas.",
    )
    text = models.TextField("texto", max_length=ANSWER_TEXT_MAX_LENGTH, blank=True, help_text="Respuesta libre o texto de «Otro».")
    options = models.ManyToManyField(
        QuestionOption, through="AnswerChoice", related_name="selected_in", blank=True, verbose_name="opciones elegidas",
    )
    number = models.PositiveSmallIntegerField("número", null=True, blank=True, help_text="Escala lineal o calificación.")
    date = models.DateField("fecha", null=True, blank=True)
    time = models.TimeField("hora", null=True, blank=True)

    class Meta:
        verbose_name = "respuesta"
        verbose_name_plural = "respuestas"
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"], condition=Q(row__isnull=True), name="uniq_answer_submission_question",
            ),
            models.UniqueConstraint(
                fields=["submission", "question", "row"], condition=Q(row__isnull=False), name="uniq_answer_submission_question_row",
            ),
        ]
        indexes = [models.Index(fields=["question", "number"], name="answer_question_number_idx")]

    def __str__(self) -> str:
        return f"{self.question}: {self.text[:40]}"


class AnswerChoice(models.Model):
    """Una opción elegida en una respuesta (tabla intermedia de ``Answer.options``)."""

    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="choices", verbose_name="respuesta")
    # RESTRICT: una opción con respuestas no se borra sola, se archiva (``QuestionOption.archived_at``).
    # Sí se va si se borra la pregunta completa (entonces también se borran sus respuestas).
    option = models.ForeignKey(QuestionOption, on_delete=models.RESTRICT, related_name="choices", verbose_name="opción")

    class Meta:
        verbose_name = "opción elegida"
        verbose_name_plural = "opciones elegidas"
        constraints = [models.UniqueConstraint(fields=["answer", "option"], name="uniq_answer_choice")]

    def __str__(self) -> str:
        return f"{self.answer_id} → {self.option}"
