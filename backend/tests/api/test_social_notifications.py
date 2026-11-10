"""Avisos que genera la red social: reacciones, comentarios, respuestas y seguidores.

Sin avisos por acciones propias, sin duplicados al cambiar de emoji y retirados al deshacer o eliminar.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.social.models import Post


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class SocialNotificationTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user(username="ana", email="ana@orienta.soy", first_name="Ana", last_name="Robles", password="x")
        self.beto = User.objects.create_user(username="beto", email="beto@orienta.soy", first_name="Beto", last_name="Sáenz", password="x")
        self.carla = User.objects.create_user(username="carla", email="carla@orienta.soy", first_name="Carla", last_name="Méndez", password="x")
        self.post = Post.objects.create(author=self.ana, body="Hoy lanzamos la nueva intranet")

    def inbox(self, user):
        return list(Notification.objects.filter(recipient=user).order_by("id"))

    def react(self, user, emoji="joy"):
        return client_for(user).put(f"/api/social/posts/{self.post.pk}/reaction/", {"emoji": emoji}, format="json")

    def comment(self, user, body, parent=None):
        response = client_for(user).post(f"/api/social/posts/{self.post.pk}/comments/", {"body": body, "parent": parent}, format="json")
        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    # --- Reacciones ----------------------------------------------------------------

    def test_reaction_notifies_author_once_and_changing_emoji_updates_it(self):
        self.react(self.beto, "joy")
        self.react(self.beto, "smile")
        notifications = self.inbox(self.ana)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].title, "Beto Sáenz reaccionó a tu publicación")
        self.assertTrue(notifications[0].body.startswith("😀"))   # el emoji nuevo
        self.assertEqual(notifications[0].url, f"/posts/{self.post.pk}/")

    def test_removing_the_reaction_withdraws_the_notice(self):
        self.react(self.beto)
        client_for(self.beto).delete(f"/api/social/posts/{self.post.pk}/reaction/")
        self.assertEqual(self.inbox(self.ana), [])

    def test_no_notice_for_my_own_actions(self):
        self.react(self.ana)
        self.comment(self.ana, "Yo misma")
        self.assertEqual(self.inbox(self.ana), [])

    def test_changing_emoji_keeps_it_read(self):
        self.react(self.beto, "joy")
        Notification.objects.filter(recipient=self.ana).update(read_at="2026-11-07T10:00:00Z")
        self.react(self.beto, "smile")
        self.assertIsNotNone(self.inbox(self.ana)[0].read_at)   # no vuelve a «sonar»

    # --- Comentarios y respuestas ----------------------------------------------------

    def test_comment_notifies_post_author_and_opens_comments(self):
        self.comment(self.beto, "¡Felicidades al equipo!")
        notice = self.inbox(self.ana)[0]
        self.assertEqual(notice.title, "Beto Sáenz comentó tu publicación")
        self.assertEqual(notice.body, "«¡Felicidades al equipo!»")
        self.assertEqual(notice.url, f"/posts/{self.post.pk}/?comments=1")

    def test_reply_notifies_the_comment_author_and_the_post_author(self):
        parent = self.comment(self.beto, "¿Ya funciona en el teléfono?")
        Notification.objects.all().delete()
        self.comment(self.carla, "Sí, ya lo probé", parent=parent)
        self.assertEqual([n.title for n in self.inbox(self.beto)], ["Carla Méndez respondió a tu comentario"])
        self.assertEqual([n.title for n in self.inbox(self.ana)], ["Carla Méndez comentó tu publicación"])

    def test_post_author_replying_gets_nothing_and_the_commenter_gets_one(self):
        parent = self.comment(self.beto, "Pregunta")
        Notification.objects.all().delete()
        self.comment(self.ana, "Respuesta de la autora", parent=parent)
        self.assertEqual(self.inbox(self.ana), [])
        self.assertEqual(len(self.inbox(self.beto)), 1)

    def test_deleting_a_comment_withdraws_its_notices_and_editing_updates_them(self):
        comment = self.comment(self.beto, "Primera versión")
        client_for(self.beto).patch(f"/api/social/comments/{comment}/", {"body": "Versión corregida"}, format="json")
        self.assertEqual(self.inbox(self.ana)[0].body, "«Versión corregida»")
        client_for(self.beto).delete(f"/api/social/comments/{comment}/")
        self.assertEqual(self.inbox(self.ana), [])

    def test_comment_reaction_notifies_and_withdraws(self):
        comment = self.comment(self.beto, "Gran trabajo")
        client_for(self.carla).put(f"/api/social/comments/{comment}/reaction/", {"emoji": "joy"}, format="json")
        self.assertEqual([n.title for n in self.inbox(self.beto)], ["Carla Méndez reaccionó a tu comentario"])
        client_for(self.carla).delete(f"/api/social/comments/{comment}/reaction/")
        self.assertEqual(self.inbox(self.beto), [])

    # --- Publicación eliminada y seguidores -------------------------------------------

    def test_deleting_the_post_withdraws_everything_that_points_to_it(self):
        self.react(self.beto)
        comment = self.comment(self.beto, "Hola")
        client_for(self.ana).put(f"/api/social/comments/{comment}/reaction/", {"emoji": "joy"}, format="json")
        self.assertEqual(Notification.objects.count(), 3)
        client_for(self.ana).delete(f"/api/social/posts/{self.post.pk}/")
        self.assertEqual(Notification.objects.count(), 0)

    def test_follow_notifies_once_and_unfollow_withdraws(self):
        for _ in range(2):
            client_for(self.beto).put(f"/api/social/follows/{self.ana.pk}/")
        notices = self.inbox(self.ana)
        self.assertEqual([n.title for n in notices], ["Beto Sáenz empezó a seguirte"])
        self.assertEqual(notices[0].url, f"/profile/{self.beto.pk}")
        client_for(self.beto).delete(f"/api/social/follows/{self.ana.pk}/")
        self.assertEqual(self.inbox(self.ana), [])

    def test_inactive_people_receive_nothing(self):
        User.objects.filter(pk=self.ana.pk).update(is_active=False)
        self.post.author.refresh_from_db()
        self.react(self.beto)
        self.assertEqual(Notification.objects.count(), 0)
