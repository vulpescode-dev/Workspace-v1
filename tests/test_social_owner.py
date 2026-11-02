"""Pruebas de opciones del autor (editar / borrado suave), respuestas y reacciones en comentarios."""
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalogs.models import Emoji
from apps.social.models import CommentReaction, Post, PostAttachment, PostComment

POSTS_URL = "/api/social/posts/"
COMMENTS_URL = "/api/social/comments/"


def make_user(username):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class PostOwnerTests(TestCase):
    def setUp(self):
        self.author = make_user("autora")
        self.other = make_user("otro")
        self.post = Post.objects.create(author=self.author, body="original")
        self.url = f"{POSTS_URL}{self.post.pk}/"

    def test_is_mine_flag(self):
        self.assertTrue(client_for(self.author).get(self.url).data["is_mine"])
        self.assertFalse(client_for(self.other).get(self.url).data["is_mine"])

    def test_author_edits_text(self):
        response = client_for(self.author).patch(self.url, {"body": "corregido"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["body"], "corregido")
        self.assertIsNotNone(response.data["edited_at"])

    def test_others_cannot_edit_or_delete(self):
        client = client_for(self.other)
        self.assertEqual(client.patch(self.url, {"body": "hackeado"}, format="json").status_code, 403)
        self.assertEqual(client.delete(self.url).status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.body, "original")
        self.assertIsNone(self.post.deleted_at)

    def test_cannot_leave_empty_without_attachments(self):
        self.assertEqual(client_for(self.author).patch(self.url, {"body": "  "}, format="json").status_code, 400)

    def test_can_leave_empty_with_attachments(self):
        PostAttachment.objects.create(post=self.post, kind="image", content_type="image/webp", size=1)
        self.assertEqual(client_for(self.author).patch(self.url, {"body": ""}, format="json").status_code, 200)

    def test_soft_delete_hides_post_everywhere_but_keeps_row(self):
        attachment = PostAttachment.objects.create(post=self.post, kind="image", content_type="image/webp", size=1)
        client = client_for(self.author)
        self.assertEqual(client.delete(self.url).status_code, 204)

        self.post.refresh_from_db()
        self.assertIsNotNone(self.post.deleted_at)                       # sigue en la base
        self.assertEqual(client.get(POSTS_URL).data["count"], 0)          # no sale en el feed
        for url in (self.url, f"{self.url}comments/", f"{self.url}reactions/", f"/api/social/attachments/{attachment.pk}/file/"):
            self.assertEqual(client.get(url).status_code, 404, url)
        self.assertEqual(client.put(f"{self.url}reaction/", {"emoji": "joy"}, format="json").status_code, 404)
        self.assertEqual(client.delete(self.url).status_code, 404)        # ya no existe para nadie


class CommentThreadTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.beto = make_user("beto")
        self.post = Post.objects.create(author=self.ana, body="hola")
        self.url = f"{POSTS_URL}{self.post.pk}/comments/"

    def comment(self, client, body, parent=None):
        data = {"body": body}
        if parent:
            data["parent"] = parent
        return client.post(self.url, data, format="json")

    def test_reply_and_reply_to_reply_stay_one_level(self):
        ana, beto = client_for(self.ana), client_for(self.beto)
        root = self.comment(ana, "raíz").data
        reply = self.comment(beto, "respuesta", root["id"]).data
        nested = self.comment(ana, "respuesta a respuesta", reply["id"]).data
        self.assertEqual(reply["parent"], root["id"])
        self.assertEqual(nested["parent"], root["id"])                   # cuelga del mismo hilo
        self.assertEqual(nested["comments_count"], 3)

        threads = ana.get(self.url).data["results"]
        self.assertEqual(len(threads), 1)
        self.assertEqual([r["body"] for r in threads[0]["replies"]], ["respuesta", "respuesta a respuesta"])

    def test_parent_must_belong_to_same_post(self):
        other_post = Post.objects.create(author=self.ana, body="otro")
        foreign = PostComment.objects.create(post=other_post, author=self.ana, body="x")
        self.assertEqual(self.comment(client_for(self.ana), "x", foreign.pk).status_code, 400)

    def test_edit_own_comment_only(self):
        comment = self.comment(client_for(self.ana), "con eror").data
        url = f"{COMMENTS_URL}{comment['id']}/"
        self.assertEqual(client_for(self.beto).patch(url, {"body": "x"}, format="json").status_code, 403)
        response = client_for(self.ana).patch(url, {"body": "con error"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["body"], "con error")
        self.assertIsNotNone(response.data["edited_at"])

    def test_delete_own_comment_only_and_soft(self):
        comment = self.comment(client_for(self.ana), "borrar").data
        url = f"{COMMENTS_URL}{comment['id']}/"
        self.assertEqual(client_for(self.beto).delete(url).status_code, 403)
        response = client_for(self.ana).delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"comments_count": 0, "keep_placeholder": False})
        self.assertTrue(PostComment.objects.filter(pk=comment["id"], deleted_at__isnull=False).exists())
        self.assertEqual(client_for(self.ana).get(self.url).data["count"], 0)
        self.assertEqual(client_for(self.ana).get(f"{POSTS_URL}{self.post.pk}/").data["comments_count"], 0)

    def test_deleted_root_with_replies_stays_as_placeholder(self):
        ana, beto = client_for(self.ana), client_for(self.beto)
        root = self.comment(ana, "raíz").data
        self.comment(beto, "respuesta", root["id"])
        response = ana.delete(f"{COMMENTS_URL}{root['id']}/")
        self.assertEqual(response.data, {"comments_count": 1, "keep_placeholder": True})

        thread = beto.get(self.url).data["results"][0]
        self.assertTrue(thread["is_deleted"])
        self.assertEqual((thread["body"], thread["author"], thread["is_mine"]), ("", None, False))
        self.assertEqual(len(thread["replies"]), 1)

    def test_is_mine_on_comments(self):
        self.comment(client_for(self.ana), "mío")
        self.assertTrue(client_for(self.ana).get(self.url).data["results"][0]["is_mine"])
        self.assertFalse(client_for(self.beto).get(self.url).data["results"][0]["is_mine"])

    def test_comment_list_query_count_is_constant(self):
        ana = client_for(self.ana)
        for n in range(4):
            root = self.comment(ana, f"r{n}").data
            self.comment(ana, f"resp{n}", root["id"])
            CommentReaction.objects.create(comment_id=root["id"], user=self.beto, emoji=Emoji.objects.get(code="fire"))
        # post visible + count + raíces + respuestas (prefetch) + reacciones de todo
        with self.assertNumQueries(5):
            ana.get(self.url)


class CommentReactionTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.post = Post.objects.create(author=self.ana, body="hola")
        self.comment = PostComment.objects.create(post=self.post, author=self.ana, body="comentario")
        self.url = f"{COMMENTS_URL}{self.comment.pk}/reaction/"
        self.client = client_for(make_user("beto"))

    def test_set_change_remove(self):
        self.assertEqual(self.client.put(self.url, {"emoji": "joy"}, format="json").data["mine"], "joy")
        response = self.client.put(self.url, {"emoji": "fire"}, format="json")
        self.assertEqual(response.data, {"reactions": [{"emoji": "fire", "count": 1}], "total": 1, "mine": "fire"})
        self.assertEqual(self.client.delete(self.url).data["total"], 0)

    def test_rejects_inactive_emoji(self):
        Emoji.objects.filter(code="rat").update(is_active=False)
        self.assertEqual(self.client.put(self.url, {"emoji": "rat"}, format="json").status_code, 400)

    def test_reactions_listed_with_comment(self):
        self.client.put(self.url, {"emoji": "heart_eyes"}, format="json")
        thread = self.client.get(f"{POSTS_URL}{self.post.pk}/comments/").data["results"][0]
        self.assertEqual(thread["reactions"]["reactions"], [{"emoji": "heart_eyes", "count": 1}])

    def test_deleted_comment_cannot_be_reacted(self):
        self.comment.soft_delete()
        self.assertEqual(self.client.put(self.url, {"emoji": "joy"}, format="json").status_code, 404)
