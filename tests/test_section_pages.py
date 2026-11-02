"""Páginas de sección aún en construcción (Noticias, Documentos, Formularios y Marketplace): existen, piden sesión y están en el menú."""
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class SectionPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ana", email="ana@example.test", password="x-Pass-12345")

    def test_require_login(self):
        for name in ("blog", "documents", "forms", "marketplace"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertRedirects(response, f"/accounts/login/?next={reverse(name)}", fetch_redirect_response=False)

    def test_pages_render_and_mark_menu(self):
        self.client.force_login(self.user)
        for name, title in (("blog", "Noticias"), ("documents", "Documentos"), ("forms", "Formularios"), ("marketplace", "Marketplace")):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f"<title>{title} · Workspace</title>", html=False)
                self.assertContains(response, f'href="{reverse(name)}" class="list-group-item list-group-item-action d-flex align-items-center gap-3 is-current"')


class HelpAndLegalPagesTests(TestCase):
    """Ayuda (con sesión, en «Cuenta») y Términos/Privacidad (públicas, al pie del menú y del login)."""

    def setUp(self):
        self.user = User.objects.create_user(username="ana", email="ana@example.test", password="x-Pass-12345")

    def test_help_requires_login_and_is_in_account_menu(self):
        self.assertRedirects(self.client.get(reverse("help")), "/accounts/login/?next=/help/", fetch_redirect_response=False)
        self.client.force_login(self.user)
        response = self.client.get(reverse("help"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/help/" class="list-group-item list-group-item-action d-flex align-items-center gap-3 is-current"')

    def test_legal_pages_are_public(self):
        for name in ("terms", "privacy"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Iniciar sesión")   # el menú sin sesión ofrece entrar

    def test_legal_links_in_login_and_menu_footer(self):
        login = self.client.get(reverse("accounts:login"))
        self.assertContains(login, 'href="/terms/"')
        self.assertContains(login, 'href="/privacy/"')
        self.client.force_login(self.user)
        home = self.client.get(reverse("social:home"))
        self.assertContains(home, 'class="ws-legal-links ws-sidebar__footer"')
        self.assertContains(home, 'href="/terms/"')


class CalendarPageTests(TestCase):
    """Calendario: solo frontend; avisa que aún no hay fechas del sistema y no inventa eventos."""

    def setUp(self):
        self.user = User.objects.create_user(username="ana", email="ana@example.test", password="x-Pass-12345")

    def test_requires_login(self):
        self.assertRedirects(self.client.get(reverse("calendar")), "/accounts/login/?next=/calendar/", fetch_redirect_response=False)

    def test_page_has_notice_calendar_and_menu_link(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El calendario aún no muestra las fechas del sistema.")
        self.assertContains(response, 'id="ws-calendar"')
        self.assertContains(response, "vendor/fullcalendar/index.global.min.js")
        self.assertContains(response, 'href="/calendar/" class="list-group-item list-group-item-action d-flex align-items-center gap-3 is-current"')
