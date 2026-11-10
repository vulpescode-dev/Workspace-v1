"""Pruebas de publicaciones: servicio, visibilidad y API /api/social/posts/."""
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalogs.models import Emoji
from apps.social.models import Post, PostComment, PostReaction
from apps.social.selectors.posts import visible_posts
from apps.social.services.posts import create_post

POSTS_URL = "/api/social/posts/"


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


class CreatePostServiceTests(TestCase):
    def setUp(self):
        self.author = make_user("autora")

    def test_creates_trimmed_text_post(self):
        post = create_post(author=self.author, body="  Hola equipo  ")
        self.assertEqual(post.body, "Hola equipo")
        self.assertEqual(post.author, self.author)

    def test_rejects_blank_body(self):
        with self.assertRaises(ValidationError):
            create_post(author=self.author, body="   ")
        self.assertEqual(Post.objects.count(), 0)


class VisibilityTests(TestCase):
    def test_anonymous_and_inactive_see_nothing(self):
        author = make_user("autora")
        Post.objects.create(author=author, body="x")
        self.assertFalse(visible_posts(AnonymousUser()).exists())
        self.assertFalse(visible_posts(make_user("baja", is_active=False)).exists())

    def test_authenticated_user_sees_all_posts_newest_first(self):
        author = make_user("autora")
        first = Post.objects.create(author=author, body="primera")
        second = Post.objects.create(author=author, body="segunda")
        self.assertEqual(list(visible_posts(make_user("otro"))), [second, first])


class PostApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user("empleado", first_name="Laura", last_name="Méndez")

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(POSTS_URL).status_code, 401)
        self.assertEqual(self.client.post(POSTS_URL, {"body": "x"}, format="json").status_code, 401)
        self.assertEqual(Post.objects.count(), 0)

    def test_create_and_list(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(POSTS_URL, {"body": "Mi primera publicación"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["body"], "Mi primera publicación")
        self.assertEqual(response.data["author"]["name"], "Laura Méndez")
        self.assertEqual(response.data["author"]["initials"], "LM")

        listing = self.client.get(POSTS_URL)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["id"], response.data["id"])

    def test_search_by_text_respects_audience(self):
        other = make_user("otra")
        Post.objects.create(author=other, body="La posada será el viernes")
        Post.objects.create(author=other, body="Posada: solo para mis seguidores", audience=Post.Audience.FOLLOWERS)
        Post.objects.create(author=other, body="Nada que ver")
        self.client.force_authenticate(self.user)
        found = self.client.get(POSTS_URL, {"q": "posada"}).data
        self.assertEqual([post["body"] for post in found["results"]], ["La posada será el viernes"])
        self.assertEqual(self.client.get(POSTS_URL, {"q": "  "}).data["count"], 2)   # vacío = sin filtro (la de seguidores no la ve)

    def test_author_comes_from_session_not_payload(self):
        other = make_user("otro")
        self.client.force_authenticate(self.user)
        response = self.client.post(POSTS_URL, {"body": "hola", "author": other.pk}, format="json")
        self.assertEqual(Post.objects.get(pk=response.data["id"]).author, self.user)

    def test_blank_body_returns_400(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(POSTS_URL, {"body": "   "}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("body", response.data)

    def test_detail(self):
        post = Post.objects.create(author=self.user, body="detalle")
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(f"{POSTS_URL}{post.pk}/").data["body"], "detalle")
        self.assertEqual(self.client.get(f"{POSTS_URL}999/").status_code, 404)

    def test_list_query_count_does_not_grow_with_posts(self):
        for n in range(5):
            Post.objects.create(author=make_user(f"u{n}"), body=f"p{n}")
        self.client.force_authenticate(self.user)
        with self.assertNumQueries(5):  # permisos (acceso a la sección) + count + página con autor + adjuntos (prefetch) + resumen de reacciones
            self.client.get(POSTS_URL)

    def test_csrf_is_enforced_for_session_clients(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(POSTS_URL, {"body": "x"}, format="json").status_code, 403)


class PostReactionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = make_user("autora")
        self.user = make_user("empleado")
        self.post = Post.objects.create(author=self.author, body="hola")
        self.url = f"{POSTS_URL}{self.post.pk}/reaction/"
        self.client.force_authenticate(self.user)

    def test_requires_authentication(self):
        self.assertEqual(APIClient().put(self.url, {"emoji": "joy"}, format="json").status_code, 401)

    def test_set_change_and_remove(self):
        response = self.client.put(self.url, {"emoji": "joy"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"reactions": [{"emoji": "joy", "count": 1}], "total": 1, "mine": "joy"})

        response = self.client.put(self.url, {"emoji": "fire"}, format="json")
        self.assertEqual(response.data["mine"], "fire")
        self.assertEqual(PostReaction.objects.filter(post=self.post, user=self.user).count(), 1)

        response = self.client.delete(self.url)
        self.assertEqual(response.data, {"reactions": [], "total": 0, "mine": None})

    def test_rejects_unknown_and_inactive_emoji(self):
        self.assertEqual(self.client.put(self.url, {"emoji": "nope"}, format="json").status_code, 400)
        Emoji.objects.filter(code="rat").update(is_active=False)
        self.assertEqual(self.client.put(self.url, {"emoji": "rat"}, format="json").status_code, 400)
        self.assertFalse(PostReaction.objects.exists())

    def test_unknown_post_is_404(self):
        self.assertEqual(self.client.put(f"{POSTS_URL}999/reaction/", {"emoji": "joy"}, format="json").status_code, 404)

    def test_feed_includes_summary_sorted_by_count(self):
        others = [make_user(f"u{n}") for n in range(3)]
        for user, code in zip(others, ["fire", "fire", "joy"]):
            PostReaction.objects.create(post=self.post, user=user, emoji=Emoji.objects.get(code=code))
        self.client.put(self.url, {"emoji": "joy"}, format="json")
        reactions = self.client.get(POSTS_URL).data["results"][0]["reactions"]
        self.assertEqual(reactions["total"], 4)
        self.assertEqual(reactions["mine"], "joy")
        self.assertEqual({r["emoji"]: r["count"] for r in reactions["reactions"]}, {"fire": 2, "joy": 2})

    def test_feed_query_count_does_not_grow_with_reactions(self):
        for n in range(5):
            post = Post.objects.create(author=self.author, body=f"p{n}")
            PostReaction.objects.create(post=post, user=make_user(f"r{n}"), emoji=Emoji.objects.get(code="joy"))
        with self.assertNumQueries(5):  # permisos (acceso a la sección) + count + página + adjuntos + resumen de reacciones (incluye la mía)
            self.client.get(POSTS_URL)

    def test_reactions_list_shows_who_reacted(self):
        self.client.put(self.url, {"emoji": "heart_eyes"}, format="json")
        response = self.client.get(f"{POSTS_URL}{self.post.pk}/reactions/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["emoji"], "heart_eyes")
        self.assertEqual(response.data["results"][0]["user"]["name"], "empleado")


class PostCommentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user("empleado", first_name="Laura", last_name="Méndez")
        self.post = Post.objects.create(author=make_user("autora"), body="hola")
        self.url = f"{POSTS_URL}{self.post.pk}/comments/"
        self.client.force_authenticate(self.user)

    def test_requires_authentication(self):
        self.assertEqual(APIClient().get(self.url).status_code, 401)
        self.assertEqual(APIClient().post(self.url, {"body": "x"}, format="json").status_code, 401)

    def test_create_returns_comment_and_updated_count(self):
        response = self.client.post(self.url, {"body": "  ¡Felicidades!\r\nEquipo  "}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["body"], "¡Felicidades!\nEquipo")
        self.assertEqual(response.data["author"]["name"], "Laura Méndez")
        self.assertEqual(response.data["comments_count"], 1)

    def test_blank_comment_is_rejected(self):
        self.assertEqual(self.client.post(self.url, {"body": "   "}, format="json").status_code, 400)
        self.assertFalse(PostComment.objects.exists())

    def test_list_is_oldest_first(self):
        first = PostComment.objects.create(post=self.post, author=self.user, body="primero")
        second = PostComment.objects.create(post=self.post, author=self.user, body="segundo")
        ids = [c["id"] for c in self.client.get(self.url).data["results"]]
        self.assertEqual(ids, [first.pk, second.pk])

    def test_unknown_post_is_404(self):
        self.assertEqual(self.client.get(f"{POSTS_URL}999/comments/").status_code, 404)
        self.assertEqual(self.client.post(f"{POSTS_URL}999/comments/", {"body": "x"}, format="json").status_code, 404)

    def test_feed_includes_comments_count_without_extra_queries(self):
        for n in range(3):
            PostComment.objects.create(post=self.post, author=self.user, body=f"c{n}")
        with self.assertNumQueries(5):  # permisos (acceso a la sección) + count + página (con conteo de comentarios) + adjuntos + reacciones
            data = self.client.get(POSTS_URL).data
        self.assertEqual(data["results"][0]["comments_count"], 3)


class FeedPaginationTests(TestCase):
    """El feed usa la misma paginación que el resto de la API: 25 por página (scroll infinito)."""

    def test_25_per_page_and_missing_page(self):
        ana = make_user("ana")
        Post.objects.bulk_create([Post(author=ana, body=f"post {n}") for n in range(27)])
        client = APIClient()
        client.force_authenticate(ana)
        first = client.get(POSTS_URL).data
        self.assertEqual((first["count"], first["total_pages"], len(first["results"])), (27, 2, 25))
        self.assertEqual(len(client.get(first["next"]).data["results"]), 2)
        self.assertEqual(client.get(POSTS_URL, {"page": 9}).status_code, 404)


class DatesTests(TestCase):
    """Las fechas salen con su desfase horario: cada navegador las muestra en su propia zona."""

    def test_api_dates_have_offset_and_server_zone_is_queretaro(self):
        from django.conf import settings

        self.assertEqual(settings.TIME_ZONE, "America/Mexico_City")
        ana = make_user("ana")
        Post.objects.create(author=ana, body="hola")
        client = APIClient()
        client.force_authenticate(ana)
        created = client.get(POSTS_URL).data["results"][0]["created_at"]
        self.assertRegex(created, r"[+-]\d{2}:\d{2}$|Z$")
