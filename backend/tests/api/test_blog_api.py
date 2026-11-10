"""Pruebas de la API del blog /api/blog/: permiso para escribir, borradores y programados,
portada, reacciones y comentarios."""
import io
import shutil
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import Permission, Role, RolePermission, User, UserRole
from apps.blog.models import Article, ArticleCategory

ARTICLES_URL = "/api/blog/articles/"
MEDIA_DIR = tempfile.mkdtemp()


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


def make_writer(username):
    user = make_user(username)
    role, _ = Role.objects.get_or_create(name="Comunicación")
    permission, _ = Permission.objects.get_or_create(codename="blog.articles.create")
    RolePermission.objects.get_or_create(role=role, permission=permission)
    UserRole.objects.create(user=user, role=role)
    return user


def webp(name="portada.webp"):
    buffer = io.BytesIO()
    Image.new("RGB", (60, 40), (244, 198, 0)).save(buffer, "WEBP")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/webp")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@override_settings(MEDIA_ROOT=MEDIA_DIR)
class ArticleApiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_DIR, ignore_errors=True)

    def setUp(self):
        self.writer = make_writer("comunica")
        self.reader = make_user("lectora")
        self.category = ArticleCategory.objects.create(name="RRHH", slug="rrhh")
        self.as_writer = client_for(self.writer)
        self.as_reader = client_for(self.reader)

    def publish(self, title="Bienvenida", **extra):
        return Article.objects.create(title=title, author=self.writer, status=Article.Status.PUBLISHED, **extra)

    def test_requires_login(self):
        self.assertEqual(APIClient().get(ARTICLES_URL).status_code, 401)

    def test_permission_to_write(self):
        self.assertFalse(self.as_reader.get("/api/blog/permissions/").data["can_write"])
        self.assertTrue(self.as_writer.get("/api/blog/permissions/").data["can_write"])
        self.assertEqual(self.as_reader.post(ARTICLES_URL, {"title": "Hola"}, format="json").status_code, 403)

    def test_create_with_cover_and_sanitized_body(self):
        response = self.as_writer.post(ARTICLES_URL, {
            "title": "Talent RH", "body": "<p>Hola</p><script>x()</script>", "category": self.category.pk,
            "status": "published", "cover": webp(),
        }, format="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["body"], "<p>Hola</p>")
        self.assertEqual(response.data["slug"], "talent-rh")
        self.assertIsNotNone(response.data["published_at"])
        cover = self.as_reader.get(response.data["cover_url"])
        self.assertEqual(cover.status_code, 200)
        self.assertEqual(cover["Content-Type"], "image/webp")

    def test_drafts_and_scheduled_only_for_author(self):
        draft = Article.objects.create(title="Borrador", author=self.writer)
        scheduled = self.publish("Futuro", published_at=timezone.now() + timedelta(days=1))
        visible = self.publish("Hoy")

        reader_list = self.as_reader.get(ARTICLES_URL).data
        self.assertEqual([a["id"] for a in reader_list["results"]], [visible.pk])
        self.assertNotIn("body", reader_list["results"][0])
        self.assertEqual(self.as_reader.get(f"{ARTICLES_URL}{draft.pk}/").status_code, 404)
        self.assertEqual(self.as_reader.get(f"{ARTICLES_URL}{scheduled.pk}/").status_code, 404)

        mine = self.as_writer.get(ARTICLES_URL, {"mine": "1"}).data["results"]
        self.assertEqual({a["id"] for a in mine}, {draft.pk, scheduled.pk, visible.pk})
        self.assertTrue(next(a for a in mine if a["id"] == scheduled.pk)["is_scheduled"])

    def test_filters(self):
        self.publish("Posada 2026", category=self.category, excerpt="Fiesta de fin de año")
        self.publish("Nueva política")
        self.assertEqual(self.as_reader.get(ARTICLES_URL, {"category": "rrhh"}).data["count"], 1)
        self.assertEqual(self.as_reader.get(ARTICLES_URL, {"q": "fiesta"}).data["count"], 1)
        self.assertEqual(self.as_reader.get(ARTICLES_URL, {"slug": "nueva-politica"}).data["count"], 1)

    def test_only_author_edits_and_deletes(self):
        article = self.publish()
        url = f"{ARTICLES_URL}{article.pk}/"
        self.assertEqual(self.as_reader.patch(url, {"title": "X"}, format="json").status_code, 403)
        self.assertEqual(self.as_reader.delete(url).status_code, 403)
        response = self.as_writer.patch(url, {"title": "Bienvenida al equipo", "category": self.category.pk}, format="json")
        self.assertEqual(response.data["title"], "Bienvenida al equipo")
        self.assertEqual(response.data["category"]["slug"], "rrhh")
        self.assertEqual(self.as_writer.delete(url).status_code, 204)
        self.assertEqual(self.as_reader.get(url).status_code, 404)

    def test_reactions(self):
        article = self.publish()
        url = f"{ARTICLES_URL}{article.pk}/reaction/"
        summary = self.as_reader.put(url, {"emoji": "clap"}, format="json").data
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["mine"], "clap")
        self.assertEqual(self.as_reader.put(url, {"emoji": "no-existe"}, format="json").status_code, 400)
        self.assertEqual(self.as_reader.get(f"{ARTICLES_URL}{article.pk}/reactions/").data["count"], 1)
        self.assertEqual(self.as_reader.delete(url).data["total"], 0)

    def test_comments_and_replies(self):
        article = self.publish()
        url = f"{ARTICLES_URL}{article.pk}/comments/"
        root = self.as_reader.post(url, {"body": "¡Qué bien!"}, format="json")
        self.assertEqual(root.status_code, 201)
        self.assertEqual(root.data["comments_count"], 1)
        reply = self.as_writer.post(url, {"body": "Gracias", "parent": root.data["id"]}, format="json")
        self.assertEqual(reply.data["parent"], root.data["id"])

        threads = self.as_reader.get(url).data["results"]
        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0]["replies"][0]["body"], "Gracias")

        comment_url = f"/api/blog/comments/{root.data['id']}/"
        self.assertEqual(self.as_writer.patch(comment_url, {"body": "X"}, format="json").status_code, 403)
        deleted = self.as_reader.delete(comment_url).data
        self.assertTrue(deleted["keep_placeholder"])
        self.assertTrue(self.as_reader.get(url).data["results"][0]["is_deleted"])

    def test_cannot_comment_on_draft(self):
        draft = Article.objects.create(title="Borrador", author=self.writer)
        response = self.as_writer.post(f"{ARTICLES_URL}{draft.pk}/comments/", {"body": "Hola"}, format="json")
        self.assertEqual(response.status_code, 400)
