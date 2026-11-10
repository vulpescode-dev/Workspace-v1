from rest_framework import serializers

from apps.accounts.api.serializers import AuthorSerializer
from apps.form_builder.models import DynamicForm, Question
from apps.form_builder.selectors.forms import can_manage


class FormSerializer(serializers.ModelSerializer):
    """Tarjeta de un formulario. ``accepting``: recibe envíos ahora. ``submitted``: ya lo respondí.
    ``submissions_count`` solo sale para quien lo creó (los demás no ven cuánta gente respondió)."""

    owner = AuthorSerializer(read_only=True)
    accepting = serializers.BooleanField(source="is_accepting_submissions", read_only=True)
    submitted = serializers.BooleanField(read_only=True, default=False)
    questions_count = serializers.IntegerField(read_only=True, default=0)
    submissions_count = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = DynamicForm
        fields = [
            "uuid", "title", "description", "owner", "status", "opens_at", "closes_at", "one_submission_per_user",
            "accepting", "submitted", "questions_count", "submissions_count", "is_mine", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def _mine(self, form) -> bool:
        request = self.context.get("request")
        return bool(request) and can_manage(request.user, form)

    def get_is_mine(self, form) -> bool:
        return self._mine(form)

    def get_submissions_count(self, form) -> int | None:
        return getattr(form, "submissions_count", 0) if self._mine(form) else None


class QuestionSerializer(serializers.ModelSerializer):
    """Pregunta con sus opciones vigentes (``options``) y, en cuadrículas, sus filas (``rows``)."""

    options = serializers.SerializerMethodField()
    rows = serializers.SerializerMethodField()
    has_answers = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id", "kind", "title", "description", "is_required", "has_other_option", "shuffle_options", "min_choices",
            "max_choices", "scale_min", "scale_max", "scale_min_label", "scale_max_label", "options", "rows", "has_answers",
        ]
        read_only_fields = fields

    def _by_role(self, question, role: str) -> list:
        return [{"id": option.pk, "text": option.text} for option in question.options.all() if option.role == role]

    def get_options(self, question) -> list:
        return self._by_role(question, "option")

    def get_rows(self, question) -> list:
        return self._by_role(question, "row")

    def get_has_answers(self, question) -> bool | None:
        """Solo para el editor: avisa que no se puede cambiar de tipo."""
        answered = self.context.get("answered_questions")
        return None if answered is None else question.pk in answered


class FormDetailSerializer(FormSerializer):
    questions = serializers.SerializerMethodField()

    class Meta(FormSerializer.Meta):
        fields = [*FormSerializer.Meta.fields, "questions"]
        read_only_fields = fields

    def get_questions(self, form) -> list:
        return QuestionSerializer(form.questions.all(), many=True, context=self.context).data


class FormCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=400, trim_whitespace=False)
    description = serializers.CharField(max_length=4000, required=False, allow_blank=True, default="")


class FormEditSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=400, required=False, trim_whitespace=False)
    description = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=DynamicForm.Status.choices, required=False)
    opens_at = serializers.DateTimeField(required=False, allow_null=True)
    closes_at = serializers.DateTimeField(required=False, allow_null=True)
    one_submission_per_user = serializers.BooleanField(required=False)
