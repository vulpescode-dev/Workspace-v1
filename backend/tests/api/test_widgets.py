"""Widgets de la columna 3 de Inicio: cumpleaños y «Personas que quizás conozcas»."""
from datetime import date
from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.models import Department
from apps.social.models import Follow

BIRTHDAYS = "/api/accounts/birthdays/"
SUGGESTIONS = "/api/social/follows/suggestions/"


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@mock.patch("apps.accounts.selectors.birthdays.timezone.localdate", return_value=date(2026, 10, 25))
class BirthdaysTests(TestCase):
    def setUp(self):
        self.me = make_user("yo")

    def test_today_and_next_30_days_closest_first_without_year(self, _today):
        make_user("hoy", first_name="Hoy", birth_date=date(1990, 10, 25))
        make_user("pronto", first_name="Pronto", birth_date=date(1985, 11, 2))
        make_user("lejos", first_name="Lejos", birth_date=date(1990, 12, 25))          # 61 días: fuera
        make_user("paso", first_name="Paso", birth_date=date(1990, 10, 24))            # ayer: el próximo es en un año
        make_user("inactivo", birth_date=date(1990, 10, 26), is_active=False)
        data = client_for(self.me).get(BIRTHDAYS).json()
        self.assertEqual([(b["name"], b["day"], b["month"], b["days_until"], b["is_today"]) for b in data],
                         [("Hoy", 25, 10, 0, True), ("Pronto", 2, 11, 8, False)])
        self.assertNotIn("1990", str(data))                                        # nunca el año ni la edad
        self.assertNotIn("birth_date", data[0])

    def test_crosses_new_year_and_leap_day(self, today):
        today.return_value = date(2027, 2, 20)
        make_user("bisiesto", first_name="Bisiesto", birth_date=date(1996, 2, 29))  # 2027 no es bisiesto → 28 feb
        make_user("enero", first_name="Enero", birth_date=date(1990, 1, 5))         # ya pasó en 2027
        data = client_for(self.me).get(BIRTHDAYS).json()
        self.assertEqual([(b["name"], b["day"], b["month"]) for b in data], [("Bisiesto", 28, 2)])

    def test_requires_session(self, _today):
        self.assertEqual(APIClient().get(BIRTHDAYS).status_code, 401)


class SuggestionsTests(TestCase):
    def test_people_i_do_not_follow_same_area_first(self):
        tech = Department.objects.create(name="Tecnología")
        me = make_user("yo", department=tech)
        followed = make_user("seguida", department=tech)
        Follow.objects.create(follower=me, following=followed)
        same_area = make_user("misma", department=tech)
        other = make_user("otra", department=Department.objects.create(name="Finanzas"))
        make_user("inactiva", department=tech, is_active=False)
        data = client_for(me).get(SUGGESTIONS).json()
        ids = [p["id"] for p in data]
        self.assertEqual(ids[0], same_area.pk)
        self.assertIn(other.pk, ids)
        self.assertNotIn(me.pk, ids)
        self.assertNotIn(followed.pk, ids)
        self.assertEqual(len(ids), 2)
        self.assertFalse(data[0]["is_following"])

    def test_at_most_five(self):
        me = make_user("yo")
        for n in range(8):
            make_user(f"p{n}")
        self.assertEqual(len(client_for(me).get(SUGGESTIONS).json()), 5)
