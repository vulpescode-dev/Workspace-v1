"""Pruebas del directorio de personas: página, búsqueda y paginación de 25 con páginas inexistentes."""
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.models import Department
from apps.social.models import Follow

URL = "/api/accounts/users/"


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


class DirectoryPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.me = make_user("yo", first_name="Aaa")
        for n in range(29):                                     # 30 personas activas en total
            make_user(f"persona{n:02d}", first_name=f"Persona {n:02d}")
        make_user("baja", first_name="Baja", is_active=False)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def test_25_per_page_with_page_info(self):
        first = self.client.get(URL).data
        self.assertEqual((first["count"], first["page"], first["total_pages"], len(first["results"])), (30, 1, 2, 25))
        self.assertIsNotNone(first["next"])
        second = self.client.get(first["next"]).data
        self.assertEqual((second["page"], len(second["results"]), second["next"]), (2, 5, None))

    def test_page_size_can_be_smaller_but_never_more_than_25(self):
        for size, expected in (("5", 5), ("10", 10), ("15", 15), ("100", 25), ("0", 25), ("abc", 25)):
            with self.subTest(page_size=size):
                data = self.client.get(URL, {"page_size": size}).data
                self.assertEqual(len(data["results"]), expected)
        ten = self.client.get(URL, {"page_size": 10}).data
        self.assertEqual(ten["total_pages"], 3)
        self.assertIn("page_size=10", ten["next"])                         # la siguiente página conserva el tamaño
        self.assertEqual(len(self.client.get(ten["next"]).data["results"]), 10)

    def test_page_that_does_not_exist(self):
        for page in ("3", "999", "0", "-1", "abc"):
            with self.subTest(page=page):
                response = self.client.get(URL, {"page": page})
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.data["count"], 30)
                self.assertEqual(response.data["total_pages"], 2)
                self.assertEqual(response.data["detail"], f"La página «{page}» no existe.")

    def test_first_page_is_valid_even_without_results(self):
        response = self.client.get(URL, {"search": "nadie-se-llama-asi"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.data["count"], response.data["total_pages"], response.data["results"]), (0, 1, []))

    def test_inactive_people_are_excluded_and_order_is_by_name(self):
        names = [p["name"] for p in self.client.get(URL).data["results"]]
        self.assertNotIn("Baja", names)
        self.assertEqual(names[0], "Aaa")
        self.assertEqual(names, sorted(names))


class DirectorySearchTests(TestCase):
    def setUp(self):
        self.me = make_user("yo")
        self.tech = Department.objects.create(name="Tecnología")
        self.ana = make_user("ana", first_name="Ana", last_name="Ruiz", job_title="Analista", department=self.tech)
        self.beto = make_user("beto", first_name="Beto", last_name="Sáenz", department=Department.objects.create(name="Ventas"))
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def names(self, search):
        return {p["name"] for p in self.client.get(URL, {"search": search}).data["results"]}

    def test_search_by_name_email_job_and_department(self):
        self.assertEqual(self.names("ana"), {"Ana Ruiz"})
        self.assertEqual(self.names("beto@example"), {"Beto Sáenz"})
        self.assertEqual(self.names("analista"), {"Ana Ruiz"})
        self.assertEqual(self.names("ventas"), {"Beto Sáenz"})

    def test_filter_by_department(self):
        rows = self.client.get(URL, {"department": self.tech.pk}).data["results"]
        self.assertEqual([(p["name"], p["department"], p["department_id"]) for p in rows], [("Ana Ruiz", "Tecnología", self.tech.pk)])
        self.assertEqual(self.client.get(URL, {"department": "abc"}).status_code, 400)

    def test_filter_by_gender_and_marital_status_combined_with_search_and_pages(self):
        self.ana.gender, self.ana.marital_status = "female", "married"
        self.ana.save()
        self.beto.gender, self.beto.marital_status = "male", "married"
        self.beto.save()
        for n in range(3):
            make_user(f"carla{n}", first_name=f"Carla {n}", gender="female", marital_status="single")

        def names(**params):
            return [p["name"] for p in self.client.get(URL, params).data["results"]]

        self.assertEqual(names(gender="female"), ["Ana Ruiz", "Carla 0", "Carla 1", "Carla 2"])
        self.assertEqual(names(gender="male"), ["Beto Sáenz"])
        self.assertEqual(names(marital_status="married"), ["Ana Ruiz", "Beto Sáenz"])
        self.assertEqual(names(gender="female", marital_status="married"), ["Ana Ruiz"])
        self.assertEqual(names(gender="female", department=self.tech.pk), ["Ana Ruiz"])
        self.assertEqual(names(gender="female", search="carla"), ["Carla 0", "Carla 1", "Carla 2"])
        page = self.client.get(URL, {"gender": "female", "page_size": 3, "page": 2}).data
        self.assertEqual((page["count"], [p["name"] for p in page["results"]]), (4, ["Carla 2"]))
        self.assertIn("gender=female", page["previous"])                     # los enlaces conservan el filtro
        self.assertEqual(self.client.get(URL, {"gender": "otro"}).status_code, 400)
        self.assertEqual(self.client.get(URL, {"marital_status": "casado"}).status_code, 400)

    def test_every_word_must_match(self):
        self.assertEqual(self.names("ana tecnología"), {"Ana Ruiz"})
        self.assertEqual(self.names("ana ventas"), set())

    def test_follow_flags(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        rows = {p["name"]: (p["is_following"], p["is_me"]) for p in self.client.get(URL).data["results"]}
        self.assertEqual(rows["Ana Ruiz"], (True, False))
        self.assertEqual(rows["Beto Sáenz"], (False, False))
        self.assertEqual(rows["yo"], (False, True))

    def test_requires_session(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)
