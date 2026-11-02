"""Página Buscar (/search/): página propia como Inicio o Avisos, sin datos de demostración."""
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class SearchPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ana", email="ana@example.test", password="x-Pass-12345")

    def test_requires_login(self):
        response = self.client.get(reverse("social:search"))
        self.assertRedirects(response, "/accounts/login/?next=/search/", fetch_redirect_response=False)

    def test_page_marks_search_in_navigation(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("social:search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="ws-search-input"')
        self.assertContains(response, 'data-people-url="/people/"')          # «Personas» busca en el directorio
        self.assertContains(response, 'style="--ws-nav-index: 2"')           # barra inferior: Buscar
        self.assertContains(response, 'href="/search/" class="list-group-item list-group-item-action align-items-center gap-3 ws-sidebar__desktop-only is-current"')
        self.assertNotContains(response, "Búsquedas recientes")             # sin datos de demostración
        self.assertContains(response, 'data-soon="La búsqueda de documentos estará disponible próximamente."')  # nunca un resultado falso

    def test_home_no_longer_embeds_search(self):
        self.client.force_login(self.user)
        home = self.client.get(reverse("social:home"))
        self.assertNotContains(home, 'id="ws-search-input"')
        self.assertContains(home, 'href="/search/"')
