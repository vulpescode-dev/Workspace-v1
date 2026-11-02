"""Pruebas del blog (modelo). La API se prueba en test_blog_api.py."""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.blog.models import Article, ArticleCategory, ArticleComment, ArticleReaction
from apps.catalogs.models import Emoji


def make_user(username):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345")


class ArticleModelTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.rrhh = ArticleCategory.objects.create(name="RRHH", slug="rrhh")

    def article(self, **fields):
        return Article.objects.create(**{"title": "Así vivimos el Talent RH", "author": self.ana, **fields})

    def test_body_html_is_sanitized_on_save(self):
        a = self.article(body=(
            '<h2>Hola</h2><p style="text-align:center;color:red" onclick="x()">Texto <strong>fuerte</strong></p>'
            '<script>alert(1)</script><a href="javascript:alert(1)">mal</a><a href="https://ok.test" target="_blank">ok</a>'
            '<iframe src="https://evil.test"></iframe><figure class="image evil"><img src="/media/x.webp" alt="x" onerror="y()"></figure>'
        ))
        a.refresh_from_db()
        self.assertIn("<h2>Hola</h2>", a.body)
        self.assertIn('style="text-align:center"', a.body)
        self.assertIn("<strong>fuerte</strong>", a.body)
        self.assertIn('href="https://ok.test"', a.body)
        self.assertIn('rel="noopener noreferrer"', a.body)
        self.assertIn('<figure class="image"><img src="/media/x.webp" alt="x"></figure>', a.body)
        for bad in ("<script", "alert", "onclick", "onerror", "javascript:", "<iframe", "color:red", "evil"):
            self.assertNotIn(bad, a.body)

    def test_slug_from_title_and_unique(self):
        first, second = self.article(), self.article()
        self.assertEqual(first.slug, "asi-vivimos-el-talent-rh")
        self.assertEqual(second.slug, "asi-vivimos-el-talent-rh-2")
        self.assertEqual(self.article(slug="propio").slug, "propio")

    def test_visibility_draft_published_scheduled_deleted(self):
        draft = self.article()
        self.assertFalse(draft.is_visible)
        self.assertIsNone(draft.published_at)

        published = self.article(status=Article.Status.PUBLISHED, category=self.rrhh)
        self.assertIsNotNone(published.published_at)                   # se fecha al publicar
        self.assertTrue(published.is_visible)

        scheduled = self.article(status=Article.Status.PUBLISHED, published_at=timezone.now() + timedelta(days=1))
        self.assertFalse(scheduled.is_visible)

        published.soft_delete()
        self.assertFalse(published.is_visible)

    def test_category_with_articles_is_protected(self):
        self.article(category=self.rrhh)
        with self.assertRaises(Exception):
            self.rrhh.delete()


class ArticleInteractionTests(TestCase):
    def setUp(self):
        self.ana, self.beto = make_user("ana"), make_user("beto")
        self.article = Article.objects.create(title="Noticia", author=self.ana, status=Article.Status.PUBLISHED)

    def test_one_reaction_per_person(self):
        emoji = Emoji.objects.create(code="heart", codepoint="2764_fe0f", char="❤️", label="Corazón")
        ArticleReaction.objects.create(article=self.article, user=self.beto, emoji=emoji)
        with self.assertRaises(IntegrityError):
            ArticleReaction.objects.create(article=self.article, user=self.beto, emoji=emoji)

    def test_comment_replies_one_level_same_article(self):
        root = ArticleComment.objects.create(article=self.article, author=self.beto, body="¡Felicidades!")
        reply = ArticleComment(article=self.article, author=self.ana, parent=root, body="Gracias")
        reply.full_clean()
        reply.save()
        with self.assertRaises(ValidationError):
            ArticleComment(article=self.article, author=self.beto, parent=reply, body="x").full_clean()
        other = Article.objects.create(title="Otra", author=self.ana)
        with self.assertRaises(ValidationError):
            ArticleComment(article=other, author=self.beto, parent=root, body="x").full_clean()
