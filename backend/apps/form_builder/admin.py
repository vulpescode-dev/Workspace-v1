from django.contrib import admin

from .models import Answer, DynamicForm, Question, QuestionOption, Submission


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ("position", "title", "kind", "is_required", "description")
    show_change_link = True   # las opciones se editan en la página de cada pregunta


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0
    fields = ("role", "position", "text", "archived_at")


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ("question", "row", "text", "chosen", "number", "date", "time")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Las respuestas solo llegan desde el formulario; el admin solo las consulta.
        return False

    @admin.display(description="opciones elegidas")
    def chosen(self, obj):
        return ", ".join(option.text for option in obj.options.all())


@admin.register(DynamicForm)
class DynamicFormAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "status", "opens_at", "closes_at", "created_at", "deleted_at")
    list_filter = ("status", ("deleted_at", admin.EmptyFieldListFilter))
    search_fields = ("title", "owner__username")
    raw_id_fields = ("owner",)
    readonly_fields = ("uuid", "created_at", "updated_at")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "kind", "form", "position", "is_required")
    list_filter = ("kind",)
    search_fields = ("title", "form__title")
    raw_id_fields = ("form",)
    fieldsets = (
        (None, {"fields": ("form", "position", "kind", "title", "description", "is_required")}),
        ("Opciones", {"fields": ("has_other_option", "shuffle_options", "min_choices", "max_choices")}),
        ("Escala", {"fields": ("scale_min", "scale_max", "scale_min_label", "scale_max_label")}),
    )
    inlines = [QuestionOptionInline]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "form", "respondent", "submitted_at")
    list_filter = ("form",)
    raw_id_fields = ("form", "respondent")
    inlines = [AnswerInline]
