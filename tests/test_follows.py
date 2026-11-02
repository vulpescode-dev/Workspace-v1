"""Pruebas de seguir (inmediato) y de la audiencia de las publicaciones (empresa / solo seguidores)."""
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.social.models import Follow, Post, PostAttachment, PostComment

POSTS_URL = "/api/social/posts/"


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class FollowApiTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana", job_title="Diseño")
        self.beto = make_user("beto")
        self.url = f"/api/social/follows/{self.ana.pk}/"

    def test_follow_is_immediate_and_idempotent(self):
        client = client_for(self.beto)
        response = client.put(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"followers_count": 1, "following_count": 0, "is_following": True, "follows_me": False})
        self.assertEqual(client.put(self.url).data["followers_count"], 1)          # seguir dos veces no duplica
        self.assertEqual(client.delete(self.url).data["is_following"], False)
        self.assertFalse(Follow.objects.exists())

    def test_cannot_follow_self_or_inactive(self):
        self.assertEqual(client_for(self.ana).put(self.url).status_code, 400)
        gone = make_user("baja", is_active=False)
        self.assertEqual(client_for(self.ana).put(f"/api/social/follows/{gone.pk}/").status_code, 404)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(follower=self.ana, following=self.ana)

    def test_requires_session(self):
        self.assertEqual(APIClient().put(self.url).status_code, 403)

    def test_profile_includes_follow_stats(self):
        Follow.objects.create(follower=self.beto, following=self.ana)
        Follow.objects.create(follower=self.ana, following=self.beto)
        follow = client_for(self.beto).get(f"/api/accounts/users/{self.ana.pk}/").data["follow"]
        self.assertEqual(follow, {"followers_count": 1, "following_count": 1, "is_following": True, "follows_me": True})

    def test_followers_and_following_lists(self):
        carla = make_user("carla")
        Follow.objects.create(follower=self.beto, following=self.ana)
        Follow.objects.create(follower=carla, following=self.ana)
        Follow.objects.create(follower=self.beto, following=carla)
        rows = client_for(self.beto).get(f"/api/social/users/{self.ana.pk}/followers/").data["results"]
        self.assertEqual({r["name"]: (r["is_following"], r["is_me"]) for r in rows}, {"carla": (True, False), "beto": (False, True)})
        following = client_for(self.beto).get(f"/api/social/users/{self.beto.pk}/following/").data["results"]
        self.assertEqual({r["name"] for r in following}, {"ana", "carla"})


class AudienceVisibilityTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.fan = make_user("fan")
        self.other = make_user("otro")
        Follow.objects.create(follower=self.fan, following=self.ana)
        self.public = Post.objects.create(author=self.ana, body="para todos")
        self.private = Post.objects.create(author=self.ana, body="solo seguidores", audience=Post.Audience.FOLLOWERS)

    def feed_ids(self, user, url=POSTS_URL):
        return {p["id"] for p in client_for(user).get(url).data["results"]}

    def test_company_for_all_followers_only_for_author_and_followers(self):
        self.assertEqual(self.feed_ids(self.ana), {self.public.pk, self.private.pk})
        self.assertEqual(self.feed_ids(self.fan), {self.public.pk, self.private.pk})
        self.assertEqual(self.feed_ids(self.other), {self.public.pk})

    def test_unfollow_hides_followers_only_posts(self):
        client_for(self.fan).delete(f"/api/social/follows/{self.ana.pk}/")
        self.assertEqual(self.feed_ids(self.fan), {self.public.pk})

    def test_hidden_post_is_404_everywhere_for_non_followers(self):
        attachment = PostAttachment.objects.create(post=self.private, kind="image", content_type="image/webp", size=1)
        PostComment.objects.create(post=self.private, author=self.ana, body="x")
        client = client_for(self.other)
        base = f"{POSTS_URL}{self.private.pk}/"
        for url in (base, f"{base}comments/", f"{base}reactions/", f"/api/social/attachments/{attachment.pk}/file/"):
            self.assertEqual(client.get(url).status_code, 404, url)
        self.assertEqual(client.put(f"{base}reaction/", {"emoji": "joy"}, format="json").status_code, 404)
        self.assertEqual(client.get(f"/api/social/photos/?author={self.ana.pk}").data["count"], 0)

    def test_profile_counts_only_what_viewer_can_see(self):
        url = f"/api/accounts/users/{self.ana.pk}/"
        self.assertEqual(client_for(self.other).get(url).data["posts_count"], 1)
        self.assertEqual(client_for(self.fan).get(url).data["posts_count"], 2)


class AudienceWriteTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.client = client_for(self.ana)

    def test_create_with_audience_and_default(self):
        default = self.client.post(POSTS_URL, {"body": "hola"}, format="json").data
        self.assertEqual(default["audience"], "company")
        private = self.client.post(POSTS_URL, {"body": "hola", "audience": "followers"}, format="json").data
        self.assertEqual(private["audience"], "followers")
        self.assertEqual(self.client.post(POSTS_URL, {"body": "hola", "audience": "secreta"}, format="json").status_code, 400)

    def test_edit_audience(self):
        post = Post.objects.create(author=self.ana, body="hola")
        response = self.client.patch(f"{POSTS_URL}{post.pk}/", {"body": "hola", "audience": "followers"}, format="json")
        self.assertEqual(response.data["audience"], "followers")
        kept = self.client.patch(f"{POSTS_URL}{post.pk}/", {"body": "editado"}, format="json")
        self.assertEqual(kept.data["audience"], "followers")      # sin audiencia en el PATCH, se conserva
