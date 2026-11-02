"""Pruebas de portada, admin protegido y estructura de la API (etapa 1)."""
import re

from django.conf import settings
from django.test import TestCase
from django.urls import Resolver404, resolve


class SiteTests(TestCase):
    def test_home_requires_login_and_comes_back_after(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/accounts/login/?next=/", fetch_redirect_response=False)
        from apps.accounts.models import User

        User.objects.create_user(username="ana", email="ana@example.test", password="x-Pass-12345")
        response = self.client.post("/accounts/login/?next=/", {"username": "ana", "password": "x-Pass-12345", "next": "/"})
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        home = self.client.get("/")
        self.assertContains(home, "css/theme.css")
        self.assertContains(home, 'action="/accounts/logout/"')             # «Cerrar sesión» en el menú

    def test_logout_from_menu_sends_csrf_token(self):
        # El menú se incluye con «only»: sin pasarle csrf_token, el formulario salía sin token (403).
        import re as _re

        from apps.accounts.models import User

        User.objects.create_user(username="ana", email="ana@example.test", password="x-Pass-12345")
        client = self.client_class(enforce_csrf_checks=True)
        client.login(username="ana", password="x-Pass-12345")
        html = client.get("/").content.decode()
        form = html.split('action="/accounts/logout/"', 1)[1].split("</form>", 1)[0]
        token = _re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', form)
        self.assertIsNotNone(token)
        response = client.post("/accounts/logout/", {"csrfmiddlewaretoken": token.group(1)})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", client.session)

    def test_admin_requires_login(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_api_root_lives_under_api_without_version(self):
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("social.posts", response.json()["endpoints"])
        self.assertEqual(self.client.get("/api/v1/").status_code, 404)

    def test_no_api_route_uses_version_prefix(self):
        for path in ("/api/v1/", "/api/v2/"):
            with self.assertRaises(Resolver404):
                resolve(path)

    def test_database_is_sqlite_and_custom_user_configured(self):
        self.assertEqual(settings.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")

    def test_csrf_middleware_enabled(self):
        self.assertIn("django.middleware.csrf.CsrfViewMiddleware", settings.MIDDLEWARE)


class HomeLayoutTests(TestCase):
    """Estructura visual de la portada (diseño móvil)."""

    def setUp(self):
        from apps.accounts.models import User

        self.client.force_login(User.objects.create_user(username="ana", email="ana@example.test", password="x"))
        self.response = self.client.get("/")
        self.html = self.response.content.decode()

    def test_home_renders_with_page_template_and_layouts(self):
        self.assertTemplateUsed(self.response, "pages/home/index.html")
        self.assertTemplateUsed(self.response, "layouts/app.html")
        self.assertTemplateUsed(self.response, "base.html")

    def test_bottom_nav_has_four_destinations_without_profile_or_favorites(self):
        nav = self.html.split('id="ws-bottom-nav"', 1)[1].split("</nav>", 1)[0]
        labels = ["Inicio", "Avisos", "Buscar", "Más"]
        positions = [nav.index(f"<span>{label}</span>") for label in labels]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(re.findall(r'class="ws-nav-item', nav)), 4)
        for forbidden in ("Perfil", "Favoritos"):
            self.assertNotIn(forbidden, nav)

    def test_post_card_comes_from_shared_component(self):
        # Una sola tarjeta, dentro de <template>; el JS la clona por cada publicación de la API.
        self.assertTemplateUsed(self.response, "components/posts/post_card.html")
        self.assertEqual(self.html.count('class="card border-0 shadow-sm rounded-4 mb-3 overflow-hidden ws-post"'), 1)

    def test_assets_are_local_and_not_cdn(self):
        for path in (
            "/static/assets/css/bootstrap-theme.css",
            "/static/assets/css/theme.css",
            "/static/assets/js/workspace.js",
            "/static/assets/vendor/bootstrap/bootstrap.min.css",
            "/static/assets/vendor/boxicons/css/boxicons.min.css",
        ):
            self.assertContains(self.response, path)
        for cdn in ("cdn.jsdelivr.net", "unpkg.com", "fonts.googleapis.com", "code.jquery.com"):
            self.assertNotContains(self.response, cdn)

    def test_static_files_exist(self):
        from django.contrib.staticfiles import finders

        for path in (
            "assets/css/theme.css", "assets/css/fonts.css", "assets/js/workspace.js",
            "assets/vendor/bootstrap/bootstrap.bundle.min.js",
            "assets/vendor/jquery/jquery.min.js",
            "assets/vendor/dayjs/dayjs.min.js",
            "assets/vendor/dayjs/plugin/relativeTime.js",
            "assets/vendor/dayjs/locale/es.js",
            "assets/vendor/boxicons/fonts/boxicons.woff2",
            "assets/fonts/montserrat/montserrat-latin-500-normal.woff2",
        ):
            self.assertIsNotNone(finders.find(path), path)

    def test_pending_actions_do_not_show_fake_success(self):
        # Documentos y Formularios ya tienen página (en construcción): los accesos llevan a ella.
        self.assertContains(self.response, 'href="/documents/"')
        self.assertContains(self.response, 'href="/forms/"')
        self.assertNotContains(self.response, "guardado")

    def test_page_zoom_is_not_disabled(self):
        self.assertNotContains(self.response, "user-scalable=no")


class AuthPagesTests(TestCase):
    def test_login_page_renders_and_logs_in(self):
        from apps.accounts.models import User

        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'autocomplete="username"')
        self.assertContains(response, "Usuario o correo")
        User.objects.create_user(username="ana", email="ana@example.test", password="x-Pass-12345")
        response = self.client.post("/accounts/login/", {"username": "ana", "password": "x-Pass-12345"})
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_login_with_email_case_insensitive(self):
        from apps.accounts.models import User

        User.objects.create_user(username="ana", email="ana@orienta.soy", password="x-Pass-12345")
        response = self.client.post("/accounts/login/", {"username": "  Ana@Orienta.SOY ", "password": "x-Pass-12345"})
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_unknown_account_and_inactive_get_same_generic_error(self):
        from apps.accounts.models import User

        User.objects.create_user(username="ana", email="ana@orienta.soy", password="x-Pass-12345")
        User.objects.create_user(username="beto", email="beto@orienta.soy", password="x-Pass-12345", is_active=False)
        for identifier, password in (("ana", "mala"), ("ana@orienta.soy", "mala"), ("nadie", "x"), ("nadie@orienta.soy", "x"),
                                     ("beto", "x-Pass-12345")):
            with self.subTest(identifier=identifier):
                response = self.client.post("/accounts/login/", {"username": identifier, "password": password})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Usuario, correo o contraseña incorrectos.")
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_keeps_next(self):
        from apps.accounts.models import User

        User.objects.create_user(username="ana", email="ana@orienta.soy", password="x-Pass-12345")
        response = self.client.post("/accounts/login/", {"username": "ana@orienta.soy", "password": "x-Pass-12345", "next": "/people/"})
        self.assertRedirects(response, "/people/", fetch_redirect_response=False)

    def test_logout_requires_post(self):
        from apps.accounts.models import User

        self.client.force_login(User.objects.create_user(username="ana", email="ana@example.test", password="x"))
        self.assertEqual(self.client.post("/accounts/logout/").status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class TemplateCommentsTests(TestCase):
    """Los comentarios {# #} de Django solo funcionan en UNA línea; si se parten, salen como texto en la página."""

    def test_no_multiline_django_comments(self):
        from pathlib import Path

        offenders = []
        for path in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "{#" in line and "#}" not in line:
                    offenders.append(f"{path.name}:{number}")
        self.assertEqual(offenders, [], "Usa {% comment %} para comentarios de varias líneas")

    def test_no_template_tags_split_across_lines(self):
        # {% include ... %} partido en dos líneas no se interpreta: el menú dejó de salir por esto.
        import re
        from pathlib import Path

        offenders = []
        for path in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"\{%(?!.*%\})", line):
                    offenders.append(f"{path.name}:{number}")
        self.assertEqual(offenders, [], "Cada etiqueta {% %} debe ir completa en una sola línea")


class TemplateHiddenTests(TestCase):
    """Las utilidades d-flex/d-inline-flex/d-block/d-grid de Bootstrap son !important y ganan al
    atributo hidden: el elemento NO se oculta. Pasó varias veces; esta prueba lo evita."""

    def test_no_display_utilities_with_hidden(self):
        import re
        from pathlib import Path

        tag = re.compile(r"<[a-z][^>]*>", re.S)
        utility = re.compile(r'class="[^"]*\bd-(?:flex|inline-flex|block|inline-block|grid)\b[^"]*"')
        hidden = re.compile(r"\shidden(?=[\s>/=]|$)")
        # Los estados (skeleton/vacío/lista) los oculta el JS con hidden: tampoco pueden llevar d-*.
        state = re.compile(r"\sdata-[a-z-]*state=")
        offenders = []
        for path in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            for match in tag.finditer(path.read_text(encoding="utf-8")):
                element = match.group(0)
                if utility.search(element) and (hidden.search(element) or state.search(element)):
                    offenders.append(f"{path.name}: {element[:80]}")
        self.assertEqual(offenders, [], "Quita la utilidad d-* o usa una clase propia con display en CSS")


class StaticVersioningTests(TestCase):
    """CSS/JS con versión en la URL: el navegador nunca usa una copia vieja (pasó con theme.css)."""

    def test_static_urls_carry_version_in_development(self):
        from django.templatetags.static import static

        url = static("assets/css/theme.css")
        self.assertRegex(url, r"/static/assets/css/theme\.css\?v=\d+$")
        self.assertEqual(static("no/existe.css"), "/static/no/existe.css")       # sin archivo, sin versión
