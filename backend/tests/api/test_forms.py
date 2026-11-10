"""Pruebas de Formularios: editor de preguntas, quién ve y responde, validación por tipo, un envío por
persona, resultados y CSV (API /api/forms/)."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Permission, Role, RolePermission, User, UserRole
from apps.form_builder.models import DynamicForm, QuestionOption, Submission

FORMS_URL = "/api/forms/forms/"


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


def grant(user, codename="forms.forms.create"):
    permission, _ = Permission.objects.get_or_create(codename=codename)
    role, _ = Role.objects.get_or_create(name=codename)
    RolePermission.objects.get_or_create(role=role, permission=permission)
    UserRole.objects.create(user=user, role=role)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


QUESTIONS = [
    {"kind": "short_text", "title": "Nombre del equipo", "is_required": True},
    {"kind": "single_choice", "title": "Sede", "options": [{"text": "CDMX"}, {"text": "Monterrey"}], "has_other_option": True},
    {"kind": "multiple_choice", "title": "Temas", "options": ["A", "B", "C"], "min_choices": 1, "max_choices": 2},
    {"kind": "linear_scale", "title": "¿Qué tan útil?", "scale_min": 1, "scale_max": 5, "scale_min_label": "Nada"},
    {"kind": "single_choice_grid", "title": "Califica", "rows": ["Comida", "Lugar"], "options": ["Mal", "Bien"], "is_required": True},
    {"kind": "date", "title": "Fecha preferida"},
]


class FormsApiTests(TestCase):
    def setUp(self):
        self.owner = make_user("rrhh")
        grant(self.owner)
        self.person = make_user("persona")
        self.other = make_user("otra")
        self.owner_client = client_for(self.owner)

    def make_form(self, questions=QUESTIONS, open_=True, **settings):
        response = self.owner_client.post(FORMS_URL, {"title": "Encuesta de la posada"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        uuid = response.data["uuid"]
        response = self.owner_client.put(f"{FORMS_URL}{uuid}/questions/", {"questions": questions}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        if open_ or settings:
            payload = {**settings, **({"status": "open"} if open_ else {})}
            self.assertEqual(self.owner_client.patch(f"{FORMS_URL}{uuid}/", payload, format="json").status_code, 200)
        return uuid, self.owner_client.get(f"{FORMS_URL}{uuid}/").data["questions"]

    def answers(self, questions, **override):
        q = {item["title"]: item for item in questions}
        grid = q["Califica"]
        values = {
            "Nombre del equipo": {"text": "Diseño"},
            "Sede": {"options": [q["Sede"]["options"][0]["id"]]},
            "Temas": {"options": [q["Temas"]["options"][0]["id"]]},
            "¿Qué tan útil?": {"number": 4},
            "Califica": {"rows": {str(row["id"]): [grid["options"][1]["id"]] for row in grid["rows"]}},
            "Fecha preferida": {"date": "2026-12-19"},
        }
        values.update(override)
        return [{"question": q[title]["id"], **value} for title, value in values.items()]

    def test_only_permission_can_create_and_drafts_are_private(self):
        self.assertEqual(client_for(self.person).post(FORMS_URL, {"title": "X"}, format="json").status_code, 403)
        uuid, _ = self.make_form(open_=False)
        self.assertEqual(client_for(self.person).get(f"{FORMS_URL}{uuid}/").status_code, 404)
        self.assertEqual(client_for(self.person).get(FORMS_URL).data["count"], 0)
        self.assertEqual(self.owner_client.get(FORMS_URL, {"scope": "mine"}).data["count"], 1)

    def test_cannot_open_without_questions_and_only_owner_edits(self):
        uuid = self.owner_client.post(FORMS_URL, {"title": "Vacía"}, format="json").data["uuid"]
        self.assertEqual(self.owner_client.patch(f"{FORMS_URL}{uuid}/", {"status": "open"}, format="json").status_code, 400)
        self.assertEqual(client_for(self.person).put(f"{FORMS_URL}{uuid}/questions/", {"questions": QUESTIONS}, format="json").status_code, 404)
        uuid, _ = self.make_form()
        self.assertEqual(client_for(self.person).patch(f"{FORMS_URL}{uuid}/", {"title": "Hack"}, format="json").status_code, 403)
        self.assertEqual(client_for(self.person).put(f"{FORMS_URL}{uuid}/questions/", {"questions": []}, format="json").status_code, 403)

    def test_question_validation_messages(self):
        uuid = self.owner_client.post(FORMS_URL, {"title": "X"}, format="json").data["uuid"]
        cases = [
            [{"kind": "single_choice", "title": "Sin opciones", "options": []}],
            [{"kind": "single_choice", "title": "Repetidas", "options": ["Sí", "sí"]}],
            [{"kind": "linear_scale", "title": "Escala", "scale_max": 11}],
            [{"kind": "single_choice_grid", "title": "Sin filas", "options": ["A"]}],
            [{"kind": "multiple_choice", "title": "Mín", "options": ["A", "B"], "min_choices": 3}],
            [{"kind": "nada", "title": "Tipo"}],
            [{"kind": "short_text", "title": ""}],
        ]
        for questions in cases:
            response = self.owner_client.put(f"{FORMS_URL}{uuid}/questions/", {"questions": questions}, format="json")
            self.assertEqual(response.status_code, 400, questions)
            self.assertIn("Pregunta 1", str(response.data["questions"]))

    def test_submit_validates_by_kind_and_required(self):
        uuid, questions = self.make_form()
        client = client_for(self.person)
        url = f"{FORMS_URL}{uuid}/submissions/"
        q = {item["title"]: item for item in questions}
        bad = self.answers(questions, **{
            "Nombre del equipo": {"text": ""},
            "Sede": {"options": [q["Sede"]["options"][0]["id"]], "other": "Guadalajara"},
            "Temas": {"options": [option["id"] for option in q["Temas"]["options"]]},
            "¿Qué tan útil?": {"number": 9},
            "Califica": {"rows": {str(q["Califica"]["rows"][0]["id"]): [q["Califica"]["options"][0]["id"]]}},
            "Fecha preferida": {"date": "19/12/2026"},
        })
        response = client.post(url, {"answers": bad}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data["answers"]), {str(item["id"]) for item in questions})
        self.assertFalse(Submission.objects.exists())

        response = client.post(url, {"answers": self.answers(questions, Sede={"other": "Guadalajara"})}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(client.post(url, {"answers": self.answers(questions)}, format="json").status_code, 400)  # uno por persona

    def test_pending_scope_and_closed_forms(self):
        uuid, questions = self.make_form()
        client = client_for(self.person)
        self.assertEqual(client.get(FORMS_URL, {"scope": "pending"}).data["count"], 1)
        client.post(f"{FORMS_URL}{uuid}/submissions/", {"answers": self.answers(questions)}, format="json")
        listed = client.get(FORMS_URL).data["results"][0]
        self.assertTrue(listed["submitted"])
        self.assertIsNone(listed["submissions_count"])   # los demás no ven cuántos respondieron
        self.assertEqual(client.get(FORMS_URL, {"scope": "pending"}).data["count"], 0)

        DynamicForm.objects.filter(uuid=uuid).update(closes_at=timezone.now() - timedelta(minutes=1))
        response = client_for(self.other).post(f"{FORMS_URL}{uuid}/submissions/", {"answers": self.answers(questions)}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_editing_keeps_answers_archives_used_options_and_blocks_kind_change(self):
        uuid, questions = self.make_form()
        client_for(self.person).post(f"{FORMS_URL}{uuid}/submissions/", {"answers": self.answers(questions)}, format="json")
        edited = [dict(item) for item in questions]
        sede = next(item for item in edited if item["title"] == "Sede")
        sede["options"] = [{"text": "Guadalajara"}]   # quita CDMX (elegida) y Monterrey (sin respuestas)
        response = self.owner_client.put(f"{FORMS_URL}{uuid}/questions/", {"questions": edited}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(QuestionOption.objects.filter(text="CDMX", archived_at__isnull=False).exists())
        self.assertFalse(QuestionOption.objects.filter(text="Monterrey").exists())
        options = next(item for item in response.data["questions"] if item["title"] == "Sede")["options"]
        self.assertEqual([option["text"] for option in options], ["Guadalajara"])

        renamed = [dict(item) for item in response.data["questions"]]
        renamed[0]["kind"] = "paragraph"
        response = self.owner_client.put(f"{FORMS_URL}{uuid}/questions/", {"questions": renamed}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("tipo", response.data["questions"][0])

    def test_results_and_csv(self):
        uuid, questions = self.make_form()
        client_for(self.person).post(f"{FORMS_URL}{uuid}/submissions/", {"answers": self.answers(questions)}, format="json")
        client_for(self.other).post(f"{FORMS_URL}{uuid}/submissions/", {"answers": self.answers(questions, **{"¿Qué tan útil?": {"number": 2}})}, format="json")
        self.assertEqual(client_for(self.person).get(f"{FORMS_URL}{uuid}/results/").status_code, 403)

        results = self.owner_client.get(f"{FORMS_URL}{uuid}/results/").data
        self.assertEqual(results["submissions_count"], 2)
        by_title = {item["title"]: item for item in results["questions"]}
        self.assertEqual(by_title["¿Qué tan útil?"]["average"], 3)
        self.assertEqual([o["count"] for o in by_title["Sede"]["options"]], [2, 0])
        self.assertEqual(by_title["Califica"]["rows"][0]["counts"], [0, 2])
        self.assertEqual(len(by_title["Nombre del equipo"]["texts"]), 2)

        response = self.owner_client.get(f"{FORMS_URL}{uuid}/results.csv")
        self.assertEqual(response.status_code, 200)
        text = response.content.decode("utf-8-sig")
        self.assertIn("Califica [Comida]", text.splitlines()[0])
        self.assertEqual(len(text.strip().splitlines()), 3)
