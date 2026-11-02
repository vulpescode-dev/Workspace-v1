"""Pruebas de departamentos y organigrama: modelo (ciclos), API /api/org/."""
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.org.models import Department

DEPARTMENTS_URL = "/api/org/departments/"
CHART_URL = "/api/org/chart/"


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


class DepartmentModelTests(TestCase):
    def test_name_is_unique_ignoring_case(self):
        Department.objects.create(name="Sistemas")
        with self.assertRaises(IntegrityError):
            Department.objects.create(name="sistemas")

    def test_parent_cannot_form_a_cycle(self):
        ops = Department.objects.create(name="Operaciones")
        public = Department.objects.create(name="Áreas Públicas", parent=ops)
        ops.parent = public
        with self.assertRaises(ValidationError):
            ops.full_clean()
        public.parent = public
        with self.assertRaises(ValidationError):
            public.full_clean()


class ManagerCycleTests(TestCase):
    def test_manager_cannot_be_self_or_a_report(self):
        boss = make_user("jefa")
        report = make_user("ana", manager=boss)
        boss.manager = report
        with self.assertRaises(ValidationError):
            boss.full_clean()
        boss.manager = boss
        with self.assertRaises(ValidationError):
            boss.full_clean()


class DepartmentApiTests(TestCase):
    def setUp(self):
        self.me = make_user("yo")
        self.head = make_user("jefa", first_name="Jefa", last_name="TI")
        self.ti = Department.objects.create(name="Sistemas", head=self.head)
        Department.objects.create(name="Vieja", is_active=False)
        self.child = Department.objects.create(name="Soporte", parent=self.ti)
        make_user("ana", department=self.ti)
        make_user("baja", department=self.ti, is_active=False)
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def test_list_only_active_with_counts_and_head(self):
        rows = {d["name"]: d for d in self.client.get(DEPARTMENTS_URL).data}
        self.assertEqual(list(rows), ["Sistemas", "Soporte"])            # activos y por nombre
        self.assertEqual(rows["Sistemas"]["members_count"], 1)
        self.assertEqual(rows["Sistemas"]["head"]["name"], "Jefa TI")
        self.assertEqual(rows["Soporte"]["parent_id"], self.ti.pk)
        self.assertIsNone(rows["Soporte"]["head"])

    def test_detail_and_missing(self):
        self.assertEqual(self.client.get(f"{DEPARTMENTS_URL}{self.ti.pk}/").data["name"], "Sistemas")
        inactive = Department.objects.get(name="Vieja")
        self.assertEqual(self.client.get(f"{DEPARTMENTS_URL}{inactive.pk}/").status_code, 404)

    def test_requires_session(self):
        self.assertEqual(APIClient().get(DEPARTMENTS_URL).status_code, 403)
        self.assertEqual(APIClient().get(CHART_URL).status_code, 403)


class OrgChartPageTests(TestCase):
    def test_page_requires_login_and_loads_the_chart(self):
        self.assertEqual(self.client.get("/people/org/").status_code, 302)
        self.client.force_login(make_user("yo"))
        response = self.client.get("/people/org/")
        self.assertContains(response, 'data-org-chart-url="/api/org/chart/?depth=10"')
        self.assertContains(response, "vendor/d3-org-chart/d3-org-chart.min.js")
        self.assertContains(response, 'aria-current="page"', count=2)       # menú «Personas» + pestaña «Organigrama»
        self.assertContains(self.client.get("/people/"), 'href="/people/org/"')


class OrgChartApiTests(TestCase):
    """CEO → (Dir. A → Ana, Beto), (Dir. B); «suelta» sin jefe ni personas a cargo."""

    def setUp(self):
        self.ti = Department.objects.create(name="Sistemas")
        self.ceo = make_user("ceo", first_name="Carla", last_name="CEO", job_title="Dirección general")
        self.dir_a = make_user("dira", first_name="Dir", last_name="A", manager=self.ceo, department=self.ti)
        self.dir_b = make_user("dirb", first_name="Dir", last_name="B", manager=self.ceo)
        self.ana = make_user("ana", first_name="Ana", manager=self.dir_a)
        self.beto = make_user("beto", first_name="Beto", manager=self.dir_a)
        make_user("suelta", first_name="Suelta")
        make_user("baja", first_name="Baja", manager=self.dir_a, is_active=False)
        self.client = APIClient()
        self.client.force_authenticate(self.ana)

    def test_full_tree(self):
        data = self.client.get(CHART_URL).data
        self.assertEqual(data["unassigned_count"], 1)
        self.assertEqual(len(data["roots"]), 1)
        root = data["roots"][0]
        self.assertEqual((root["name"], root["job_title"], root["reports_count"]), ("Carla CEO", "Dirección general", 2))
        dir_a = next(c for c in root["children"] if c["id"] == self.dir_a.pk)
        self.assertEqual(dir_a["department"], {"id": self.ti.pk, "name": "Sistemas"})
        self.assertEqual([c["name"] for c in dir_a["children"]], ["Ana", "Beto"])   # sin la persona inactiva

    def test_depth_cuts_children_but_keeps_counts(self):
        root = self.client.get(CHART_URL, {"depth": 1}).data["roots"][0]
        self.assertEqual((root["children"], root["reports_count"]), ([], 2))
        self.assertEqual(self.client.get(CHART_URL, {"depth": 99}).data["depth"], 10)
        self.assertEqual(self.client.get(CHART_URL, {"depth": "0"}).status_code, 400)

    def test_subtree_from_root(self):
        data = self.client.get(CHART_URL, {"root": self.dir_a.pk}).data
        self.assertEqual([r["id"] for r in data["roots"]], [self.dir_a.pk])
        self.assertEqual(len(data["roots"][0]["children"]), 2)
        self.assertEqual(self.client.get(CHART_URL, {"root": 999}).status_code, 404)
        self.assertEqual(self.client.get(CHART_URL, {"root": "x"}).status_code, 400)

    def test_inactive_manager_makes_a_new_root(self):
        self.ceo.is_active = False
        self.ceo.save()
        roots = {r["id"] for r in self.client.get(CHART_URL).data["roots"]}
        self.assertEqual(roots, {self.dir_a.pk})   # Dir. B queda sin jefe ni personas a cargo
        self.assertEqual(self.client.get(CHART_URL).data["unassigned_count"], 2)
