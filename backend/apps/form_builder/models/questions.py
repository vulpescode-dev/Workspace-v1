"""Preguntas de un formulario y sus opciones, al estilo de Google Forms.

Tipos (``Question.Kind``) y qué usan:

- Libres: ``short_text``, ``paragraph`` → la respuesta va en ``Answer.text``.
- Cerradas con opciones (``QuestionOption`` con rol ``option``):
  ``single_choice`` (radio, una), ``multiple_choice`` (casillas, varias), ``dropdown`` (select, una).
  Las elegidas van en ``Answer.options`` (tabla ``AnswerChoice``). Con ``has_other_option`` se
  agrega «Otro» y su texto va en ``Answer.text`` (solo radio y casillas, como en Google).
- Escalas: ``linear_scale`` (p. ej. 1 a 5 con etiquetas en los extremos) y ``rating``
  (estrellas, 1 a ``scale_max``) → el número va en ``Answer.number``.
- Cuadrículas: ``single_choice_grid`` y ``multiple_choice_grid``. Las filas son opciones con rol
  ``row`` y las columnas, opciones con rol ``option``. Se guarda un ``Answer`` por fila
  (``Answer.row``) con las columnas elegidas en ``Answer.options``.
- Fecha y hora: ``date`` y ``time`` → ``Answer.date`` / ``Answer.time``.

Las opciones se guardan por id (no por texto): si se corrige la redacción de una opción, las
respuestas que ya existían siguen contando para ella. Una opción con respuestas no se borra, se
archiva (``archived_at``): deja de mostrarse en el formulario y sus respuestas se conservan.

Que cada respuesta sea coherente con su tipo de pregunta (p. ej. que las opciones sean de esa
pregunta, o el número esté dentro de la escala) lo validan los servicios, como en el resto del
proyecto; aquí van las reglas que la base de datos puede asegurar sola.
"""
from django.db import models
from django.db.models import F, Q

from .forms import DynamicForm


class Question(models.Model):
    class Kind(models.TextChoices):
        SHORT_TEXT = "short_text", "Respuesta corta"
        PARAGRAPH = "paragraph", "Párrafo"
        SINGLE_CHOICE = "single_choice", "Opción única (radio)"
        MULTIPLE_CHOICE = "multiple_choice", "Casillas (varias opciones)"
        DROPDOWN = "dropdown", "Desplegable (select)"
        LINEAR_SCALE = "linear_scale", "Escala lineal"
        RATING = "rating", "Calificación (estrellas)"
        SINGLE_CHOICE_GRID = "single_choice_grid", "Cuadrícula de opción única"
        MULTIPLE_CHOICE_GRID = "multiple_choice_grid", "Cuadrícula de casillas"
        DATE = "date", "Fecha"
        TIME = "time", "Hora"

    # Grupos de tipos para servicios, formularios y resultados.
    TEXT_KINDS = frozenset({Kind.SHORT_TEXT, Kind.PARAGRAPH})
    CHOICE_KINDS = frozenset({Kind.SINGLE_CHOICE, Kind.MULTIPLE_CHOICE, Kind.DROPDOWN})
    SCALE_KINDS = frozenset({Kind.LINEAR_SCALE, Kind.RATING})
    GRID_KINDS = frozenset({Kind.SINGLE_CHOICE_GRID, Kind.MULTIPLE_CHOICE_GRID})
    MULTIPLE_KINDS = frozenset({Kind.MULTIPLE_CHOICE, Kind.MULTIPLE_CHOICE_GRID})
    OTHER_OPTION_KINDS = frozenset({Kind.SINGLE_CHOICE, Kind.MULTIPLE_CHOICE})

    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name="questions", verbose_name="formulario")
    kind = models.CharField("tipo", max_length=30, choices=Kind.choices, default=Kind.SHORT_TEXT)
    title = models.CharField("pregunta", max_length=300)
    description = models.CharField("ayuda", max_length=500, blank=True, help_text="Texto opcional debajo de la pregunta.")
    is_required = models.BooleanField(
        "obligatoria", default=False, help_text="En cuadrículas: hay que contestar todas las filas.",
    )
    position = models.PositiveSmallIntegerField("orden", default=0)

    # Opciones (radio, casillas, desplegable y cuadrículas).
    has_other_option = models.BooleanField(
        "incluye «Otro»", default=False, help_text="Solo opción única y casillas: «Otro» con texto libre.",
    )
    shuffle_options = models.BooleanField("orden aleatorio de opciones", default=False)
    min_choices = models.PositiveSmallIntegerField(
        "mínimo de casillas", null=True, blank=True, help_text="Solo casillas. Vacío: sin mínimo.",
    )
    max_choices = models.PositiveSmallIntegerField(
        "máximo de casillas", null=True, blank=True, help_text="Solo casillas. Vacío: sin máximo.",
    )

    # Escala lineal y calificación.
    scale_min = models.PositiveSmallIntegerField("escala desde", default=1, help_text="0 o 1 (la calificación siempre empieza en 1).")
    scale_max = models.PositiveSmallIntegerField("escala hasta", default=5, help_text="De 2 a 10.")
    scale_min_label = models.CharField("etiqueta del mínimo", max_length=100, blank=True, help_text="Ej.: «Nada probable».")
    scale_max_label = models.CharField("etiqueta del máximo", max_length=100, blank=True, help_text="Ej.: «Muy probable».")

    created_at = models.DateTimeField("creada el", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada el", auto_now=True)

    class Meta:
        verbose_name = "pregunta"
        verbose_name_plural = "preguntas"
        ordering = ["position", "id"]
        indexes = [models.Index(fields=["form", "position"], name="question_form_position_idx")]
        constraints = [
            models.CheckConstraint(condition=Q(scale_min__in=[0, 1]), name="question_scale_min_0_or_1"),
            models.CheckConstraint(condition=Q(scale_max__gte=2, scale_max__lte=10), name="question_scale_max_2_to_10"),
            models.CheckConstraint(
                condition=Q(min_choices__isnull=True) | Q(max_choices__isnull=True) | Q(min_choices__lte=F("max_choices")),
                name="question_min_choices_lte_max",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def uses_options(self) -> bool:
        return self.kind in self.CHOICE_KINDS or self.kind in self.GRID_KINDS

    @property
    def is_grid(self) -> bool:
        return self.kind in self.GRID_KINDS

    @property
    def allows_multiple(self) -> bool:
        return self.kind in self.MULTIPLE_KINDS


class QuestionOption(models.Model):
    """Una opción de una pregunta cerrada, o una fila de una cuadrícula."""

    class Role(models.TextChoices):
        OPTION = "option", "Opción (columna en cuadrículas)"
        ROW = "row", "Fila (solo cuadrículas)"

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options", verbose_name="pregunta")
    role = models.CharField("rol", max_length=10, choices=Role.choices, default=Role.OPTION)
    text = models.CharField("texto", max_length=300)
    position = models.PositiveSmallIntegerField("orden", default=0)
    archived_at = models.DateTimeField(
        "archivada el", null=True, blank=True,
        help_text="Ya no se muestra en el formulario; sus respuestas se conservan.",
    )
    created_at = models.DateTimeField("creada el", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada el", auto_now=True)

    class Meta:
        verbose_name = "opción"
        verbose_name_plural = "opciones"
        ordering = ["role", "position", "id"]
        indexes = [models.Index(fields=["question", "role", "position"], name="option_question_role_pos_idx")]
        constraints = [
            # Como en Google Forms: no se repite el texto de una opción vigente en la misma pregunta.
            models.UniqueConstraint(
                fields=["question", "role", "text"], condition=Q(archived_at__isnull=True), name="uniq_option_text_per_question",
            ),
        ]

    def __str__(self) -> str:
        return self.text
