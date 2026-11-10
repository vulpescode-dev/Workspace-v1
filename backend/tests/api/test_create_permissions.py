"""Todo lo que se crea pasa por permisos, aunque «todos lo tengan»: sin el rol → 403; con los roles por
defecto (Influencer, Vendedor, Solicitante de soporte) → permitido. El superusuario pasa directo."""
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.social.models import Post, PostComment

POSTS_URL = "/api/social/posts/"
LISTINGS_URL = "/api/marketplace/listings/"
TICKETS_URL = "/api/helpdesk/tickets/"
STORIES_URL = "/api/social/stories/"


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class CreatePermissionTests(TestCase):
    def setUp(self):
        self.author = make_user("autora")
        self.post = Post.objects.create(author=self.author, body="Hola")
        self.comment = PostComment.objects.create(post=self.post, author=self.author, body="Primero")

    def attempts(self, client):
        """Una petición por cada acción de «crear» que exige permiso."""
        return {
            "publicar": client.post(POSTS_URL, {"body": "Nuevo"}, format="multipart"),
            "comentar": client.post(f"{POSTS_URL}{self.post.pk}/comments/", {"body": "Va"}, format="json"),
            "reaccionar a post": client.put(f"{POSTS_URL}{self.post.pk}/reaction/", {"emoji": "thumbs_up"}, format="json"),
            "reaccionar a comentario": client.put(f"/api/social/comments/{self.comment.pk}/reaction/", {"emoji": "thumbs_up"}, format="json"),
            "seguir": client.put(f"/api/social/follows/{self.author.pk}/"),
            "subir estado": client.post(STORIES_URL, {}, format="multipart"),
            "vender": client.post(LISTINGS_URL, {"title": "Silla"}, format="multipart"),
            "levantar ticket": client.post(TICKETS_URL, {"title": "Algo", "description": "Falla"}, format="multipart"),
        }

    def test_without_roles_everything_is_forbidden(self):
        user = make_user("sinrol")
        UserRole.objects.filter(user=user).delete()
        for action, response in self.attempts(client_for(user)).items():
            with self.subTest(action):
                self.assertEqual(response.status_code, 403, response.data)
        self.assertEqual(Post.objects.count(), 1)

    def test_default_roles_allow_the_basics(self):
        user = make_user("nueva")
        self.assertEqual(
            set(user.user_roles.values_list("role__name", flat=True)),
            {"Lector", "Influencer", "Vendedor", "Solicitante de soporte"},
        )
        for action, response in self.attempts(client_for(user)).items():
            with self.subTest(action):
                # Puede fallar por datos (p. ej. un estado sin archivo → 400), nunca por permiso.
                self.assertNotEqual(response.status_code, 403, response.data)

    def test_superuser_needs_no_roles(self):
        boss = User.objects.create_superuser(username="jefa", email="jefa@example.test", password="x-Pass-12345")
        UserRole.objects.filter(user=boss).delete()
        for action, response in self.attempts(client_for(boss)).items():
            with self.subTest(action):
                self.assertNotEqual(response.status_code, 403, response.data)

    def test_removing_one_role_only_blocks_its_actions(self):
        user = make_user("sinventa")
        UserRole.objects.filter(user=user, role__name="Vendedor").delete()
        results = self.attempts(client_for(user))
        self.assertEqual(results["vender"].status_code, 403)
        self.assertNotEqual(results["publicar"].status_code, 403)


SECTION_URLS = {
    "Personas": "/api/accounts/users/",
    "Departamentos": "/api/org/departments/",
    "Organigrama": "/api/org/chart/",
    "Publicaciones": POSTS_URL,
    "Estados": STORIES_URL,
    "Noticias": "/api/blog/articles/",
    "Documentos": "/api/documents/documents/",
    "Formularios": "/api/forms/forms/",
    "Mesa de ayuda": TICKETS_URL,
    "Marketplace": LISTINGS_URL,
}


class SectionAccessTests(TestCase):
    """Cada sección exige su permiso ``view`` (o uno que ya implique verla)."""

    def test_without_reader_role_sections_are_closed(self):
        user = make_user("sinlector")
        UserRole.objects.filter(user=user).delete()
        client = client_for(user)
        for name, url in SECTION_URLS.items():
            with self.subTest(name):
                self.assertEqual(client.get(url).status_code, 403)
        # Lo personal sigue abierto: mi perfil y mis avisos.
        self.assertEqual(client.get("/api/accounts/me/").status_code, 200)
        self.assertEqual(client.get("/api/notifications/").status_code, 200)

    def test_reader_role_opens_every_section(self):
        client = client_for(make_user("lectora"))
        for name, url in SECTION_URLS.items():
            with self.subTest(name):
                self.assertEqual(client.get(url).status_code, 200)

    def test_a_permission_that_implies_viewing_is_enough(self):
        user = make_user("agente")
        UserRole.objects.filter(user=user).exclude(role__name="Solicitante de soporte").delete()
        self.assertEqual(client_for(user).get(TICKETS_URL).status_code, 200)
        self.assertEqual(client_for(user).get(LISTINGS_URL).status_code, 403)


class OwnContentPermissionTests(TestCase):
    """Editar o borrar lo propio pide ``update``/``delete``; lo ajeno, ``delete.all`` (moderación)."""

    def setUp(self):
        self.author = make_user("autora")
        self.post = Post.objects.create(author=self.author, body="Hola")
        self.comment = PostComment.objects.create(post=self.post, author=self.author, body="Primero")

    def test_without_influencer_own_content_cannot_be_changed(self):
        UserRole.objects.filter(user=self.author, role__name="Influencer").delete()
        client = client_for(self.author)
        self.assertEqual(client.patch(f"{POSTS_URL}{self.post.pk}/", {"body": "Cambio"}, format="json").status_code, 403)
        self.assertEqual(client.delete(f"{POSTS_URL}{self.post.pk}/").status_code, 403)
        self.assertEqual(client.patch(f"/api/social/comments/{self.comment.pk}/", {"body": "Otro"}, format="json").status_code, 403)
        self.assertEqual(client.delete(f"/api/social/comments/{self.comment.pk}/").status_code, 403)

    def test_influencer_changes_own_but_not_others(self):
        other = client_for(make_user("otra"))
        self.assertEqual(other.delete(f"{POSTS_URL}{self.post.pk}/").status_code, 403)
        self.assertEqual(client_for(self.author).patch(f"{POSTS_URL}{self.post.pk}/", {"body": "Cambio"}, format="json").status_code, 200)

    def test_moderator_with_delete_all_removes_others_content(self):
        from apps.accounts.models import Permission, Role, RolePermission
        moderation = Role.objects.create(name="Moderación")
        for code in ("social.posts.delete.all", "social.comments.delete.all"):
            RolePermission.objects.create(role=moderation, permission=Permission.objects.get(codename=code))
        moderator = make_user("moderadora")
        UserRole.objects.create(user=moderator, role=moderation)
        client = client_for(moderator)
        self.assertIn(client.delete(f"/api/social/comments/{self.comment.pk}/").status_code, (200, 204))
        self.assertEqual(client.delete(f"{POSTS_URL}{self.post.pk}/").status_code, 204)
        self.assertEqual(client_for(self.author).get(f"{POSTS_URL}{self.post.pk}/").status_code, 404)


class ModerationAndExtraPermissionTests(TestCase):
    """Permisos de funciones que ya existían: descargar, resultados/CSV ajenos, asignar y moderar (.all)."""

    def setUp(self):
        self.owner = make_user("duena")
        self.other = make_user("otra")

    def grant(self, user, *codes):
        from apps.accounts.models import Permission, Role, RolePermission
        role = Role.objects.create(name=f"extra-{user.username}-{len(codes)}-{codes[0]}")
        for code in codes:
            RolePermission.objects.create(role=role, permission=Permission.objects.get(codename=code))
        UserRole.objects.create(user=user, role=role)
        return User.objects.get(pk=user.pk)   # instancia nueva: los permisos se guardan en la instancia

    def test_download_needs_permission_unless_you_manage_the_document(self):
        from apps.documents.models import Document, DocumentCategory
        from apps.documents.selectors.documents import can_download
        category = DocumentCategory.objects.create(name="Pruebas de descarga")
        document = Document.objects.create(title="Manual", category=category, owner=self.owner)
        self.assertTrue(can_download(self.other, document))       # Lector (por defecto) trae «download»
        UserRole.objects.filter(user=self.other).delete()
        self.assertFalse(can_download(User.objects.get(pk=self.other.pk), document))
        UserRole.objects.filter(user=self.owner).delete()
        self.assertTrue(can_download(User.objects.get(pk=self.owner.pk), document))   # su dueña, siempre

    def test_blog_moderation(self):
        from django.core.exceptions import PermissionDenied
        from apps.blog.models import Article
        from apps.blog.services.articles import delete_article, edit_article
        article = Article.objects.create(title="Nota", author=self.owner, status=Article.Status.PUBLISHED)
        with self.assertRaises(PermissionDenied):
            edit_article(user=self.other, article=article, title="Cambio")
        with self.assertRaises(PermissionDenied):
            delete_article(user=self.other, article=article)
        editor = self.grant(self.other, "blog.articles.update.all")
        self.assertEqual(edit_article(user=editor, article=article, title="Cambio").title, "Cambio")
        with self.assertRaises(PermissionDenied):
            delete_article(user=editor, article=article)
        delete_article(user=self.grant(self.other, "blog.articles.delete.all"), article=article)

    def test_marketplace_moderation(self):
        from django.core.exceptions import PermissionDenied
        from apps.marketplace.models import Listing
        from apps.marketplace.services.listings import delete_listing, edit_listing
        listing = Listing.objects.create(seller=self.owner, title="Silla")
        with self.assertRaises(PermissionDenied):
            delete_listing(user=self.other, listing=listing)
        editor = self.grant(self.other, "marketplace.listings.update.all")
        self.assertEqual(edit_listing(user=editor, listing=listing, title="Silla gamer").title, "Silla gamer")
        delete_listing(user=self.grant(self.other, "marketplace.listings.delete.all"), listing=listing)

    def test_forms_moderation_and_results(self):
        from django.core.exceptions import PermissionDenied
        from apps.form_builder.api.views import _can_see_results
        from apps.form_builder.models import DynamicForm
        from apps.form_builder.services.forms import delete_form, update_form
        form = DynamicForm.objects.create(owner=self.owner, title="Encuesta")
        self.assertTrue(_can_see_results(self.owner, form))
        self.assertFalse(_can_see_results(self.other, form))
        with self.assertRaises(PermissionDenied):
            update_form(user=self.other, form=form, title="Otra")
        auditor = self.grant(self.other, "forms.submissions.view.all")
        self.assertTrue(_can_see_results(auditor, form))
        editor = self.grant(self.other, "forms.forms.update.all")
        self.assertEqual(update_form(user=editor, form=form, title="Otra").title, "Otra")
        with self.assertRaises(PermissionDenied):
            delete_form(user=editor, form=form)
        delete_form(user=self.grant(self.other, "forms.forms.delete.all"), form=form)
