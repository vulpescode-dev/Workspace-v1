"""Pruebas de Formularios (form_builder, modelo): respuestas libres y cerradas."""
from datetime import date, time, timedelta

from django.db import IntegrityError, transaction
from django.db.models import RestrictedError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.form_builder.models import Answer, AnswerChoice, DynamicForm, Question, QuestionOption, Submission


def make_user(username):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345")


class DynamicFormModelTests(TestCase):
    def setUp(self):
        self.ana, self.beto = make_user("ana"), make_user("beto")
        self.form = DynamicForm.objects.create(title="Encuesta de clima", owner=self.ana)

    def test_accepting_submissions_by_status_dates_and_deletion(self):
        self.assertFalse(self.form.is_accepting_submissions)                     # borrador
        self.form.status = DynamicForm.Status.OPEN
        self.assertTrue(self.form.is_accepting_submissions)
        self.form.opens_at = timezone.now() + timedelta(hours=1)
        self.assertFalse(self.form.is_accepting_submissions)                     # todavía no abre
        self.form.opens_at, self.form.closes_at = None, timezone.now() - timedelta(minutes=1)
        self.assertFalse(self.form.is_accepting_submissions)                     # ya cerró
        self.form.closes_at = None
        self.form.save()
        self.form.soft_delete()
        self.assertFalse(self.form.is_accepting_submissions)

    def test_each_form_has_its_own_public_uuid(self):
        other = DynamicForm.objects.create(title="Otra", owner=self.ana)
        self.assertNotEqual(self.form.uuid, other.uuid)

    def test_questions_in_order_and_one_answer_per_question(self):
        q2 = Question.objects.create(form=self.form, title="¿Qué mejorarías?", kind=Question.Kind.PARAGRAPH, position=2)
        q1 = Question.objects.create(form=self.form, title="Área", is_required=True, position=1)
        self.assertEqual(list(self.form.questions.all()), [q1, q2])

        submission = Submission.objects.create(form=self.form, respondent=self.beto)
        Answer.objects.create(submission=submission, question=q1, text="TI")
        Answer.objects.create(submission=submission, question=q2, text="Más café")
        self.assertEqual([a.text for a in submission.answers.order_by("question__position")], ["TI", "Más café"])
        with self.assertRaises(IntegrityError):
            Answer.objects.create(submission=submission, question=q1, text="otra vez")


class ClosedQuestionModelTests(TestCase):
    """Preguntas cerradas: opciones, casillas, escalas, cuadrículas y reglas de la base de datos."""

    def setUp(self):
        self.ana, self.beto = make_user("ana"), make_user("beto")
        self.form = DynamicForm.objects.create(title="Encuesta de clima", owner=self.ana)
        self.submission = Submission.objects.create(form=self.form, respondent=self.beto)

    def choice_question(self, kind, *texts, **extra):
        question = Question.objects.create(form=self.form, title="Pregunta", kind=kind, **extra)
        options = [QuestionOption.objects.create(question=question, text=t, position=i) for i, t in enumerate(texts)]
        return question, options

    def test_kind_groups(self):
        radio, _ = self.choice_question(Question.Kind.SINGLE_CHOICE, "Sí", "No")
        grid = Question.objects.create(form=self.form, title="Cuadrícula", kind=Question.Kind.MULTIPLE_CHOICE_GRID)
        text = Question.objects.create(form=self.form, title="Libre")
        self.assertTrue(radio.uses_options and not radio.allows_multiple and not radio.is_grid)
        self.assertTrue(grid.uses_options and grid.allows_multiple and grid.is_grid)
        self.assertFalse(text.uses_options)

    def test_checkboxes_store_one_row_per_chosen_option(self):
        question, (coffee, tea, water) = self.choice_question(Question.Kind.MULTIPLE_CHOICE, "Café", "Té", "Agua")
        answer = Answer.objects.create(submission=self.submission, question=question)
        answer.options.add(coffee, water)
        self.assertEqual(list(answer.options.order_by("position")), [coffee, water])
        self.assertEqual(AnswerChoice.objects.filter(option=coffee).count(), 1)
        with self.assertRaises(IntegrityError):
            AnswerChoice.objects.create(answer=answer, option=coffee)          # la misma opción dos veces

    def test_other_option_text_goes_in_answer_text(self):
        question, _ = self.choice_question(Question.Kind.SINGLE_CHOICE, "Sí", "No", has_other_option=True)
        answer = Answer.objects.create(submission=self.submission, question=question, text="Depende del día")
        self.assertEqual(answer.options.count(), 0)
        self.assertEqual(answer.text, "Depende del día")

    def test_option_with_answers_is_archived_not_deleted(self):
        question, (yes, no) = self.choice_question(Question.Kind.DROPDOWN, "Sí", "No")
        Answer.objects.create(submission=self.submission, question=question).options.add(yes)
        with self.assertRaises(RestrictedError):
            yes.delete()
        yes.archived_at = timezone.now()
        yes.save()
        # Archivada, su texto se puede volver a usar y la respuesta sigue contando para ella.
        QuestionOption.objects.create(question=question, text="Sí", position=3)
        self.assertEqual(AnswerChoice.objects.filter(option=yes).count(), 1)

    def test_option_text_is_unique_per_question_and_role(self):
        question, _ = self.choice_question(Question.Kind.SINGLE_CHOICE, "Sí", "No")
        QuestionOption.objects.create(question=question, text="Sí", role=QuestionOption.Role.ROW)   # otro rol: válido
        with self.assertRaises(IntegrityError):
            QuestionOption.objects.create(question=question, text="Sí")

    def test_scale_answer_and_limits(self):
        question = Question.objects.create(
            form=self.form, title="¿Nos recomendarías?", kind=Question.Kind.LINEAR_SCALE,
            scale_min=0, scale_max=10, scale_min_label="Nada", scale_max_label="Mucho",
        )
        Answer.objects.create(submission=self.submission, question=question, number=9)
        self.assertEqual(question.answers.get().number, 9)
        for bad in ({"scale_min": 2}, {"scale_max": 11}, {"scale_max": 1}, {"min_choices": 3, "max_choices": 2}):
            with self.subTest(bad=bad), transaction.atomic(), self.assertRaises(IntegrityError):
                Question.objects.create(form=self.form, title="Mala", kind=Question.Kind.MULTIPLE_CHOICE, **bad)

    def test_grid_has_one_answer_per_row(self):
        question = Question.objects.create(form=self.form, title="Califica", kind=Question.Kind.SINGLE_CHOICE_GRID)
        food, service = (QuestionOption.objects.create(question=question, role=QuestionOption.Role.ROW, text=t) for t in ("Comida", "Servicio"))
        good, bad = (QuestionOption.objects.create(question=question, text=t) for t in ("Bien", "Mal"))
        Answer.objects.create(submission=self.submission, question=question, row=food).options.add(good)
        Answer.objects.create(submission=self.submission, question=question, row=service).options.add(bad)
        self.assertEqual(question.answers.count(), 2)
        with self.assertRaises(IntegrityError):
            Answer.objects.create(submission=self.submission, question=question, row=food)

    def test_date_and_time_answers(self):
        day = Question.objects.create(form=self.form, title="Día", kind=Question.Kind.DATE)
        hour = Question.objects.create(form=self.form, title="Hora", kind=Question.Kind.TIME)
        Answer.objects.create(submission=self.submission, question=day, date=date(2026, 12, 18))
        Answer.objects.create(submission=self.submission, question=hour, time=time(13, 30))
        self.assertEqual(day.answers.get().date, date(2026, 12, 18))
        self.assertEqual(hour.answers.get().time, time(13, 30))

    def test_deleting_question_removes_its_options_and_answers(self):
        question, (yes, _) = self.choice_question(Question.Kind.SINGLE_CHOICE, "Sí", "No")
        Answer.objects.create(submission=self.submission, question=question).options.add(yes)
        question.delete()
        self.assertFalse(QuestionOption.objects.exists())
        self.assertFalse(Answer.objects.exists())
        self.assertFalse(AnswerChoice.objects.exists())
