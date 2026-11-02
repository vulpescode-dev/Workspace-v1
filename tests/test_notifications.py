"""Pruebas de Avisos (= notificaciones), generales para todo Workspace.

API: listar (25 por página), marcar leídas, contador, eliminar y dispositivos push. Todavía no se
generan desde las demás apps.
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.social.models import Post

URL = "/api/notifications/"


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def notification(recipient, minutes_ago=0, **fields):
    defaults = {"title": "Aviso"}
    return Notification.objects.create(
        recipient=recipient, created_at=timezone.now() - timedelta(minutes=minutes_ago), **{**defaults, **fields}
    )


class NotificationListTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.beto = make_user("beto", first_name="Beto", last_name="Sáenz")
        self.client = client_for(self.ana)

    def test_simple_notifications_newest_first(self):
        notification(
            self.ana, minutes_ago=2, title="Mantenimiento de sistemas",
            body="Algunos servicios no estarán disponibles el sábado.", icon="bx-wrench", color="warning",
        )
        notification(
            self.ana, minutes_ago=1, title="Beto Sáenz empezó a seguirte", icon="bx-user-plus",
            url="/posts/1/", read_at=timezone.now(),
        )
        follow, system = self.client.get(URL).data["results"]
        self.assertEqual(
            {k: system[k] for k in ("title", "body", "icon", "color", "url", "is_read")},
            {"title": "Mantenimiento de sistemas", "body": "Algunos servicios no estarán disponibles el sábado.",
             "icon": "bx-wrench", "color": "warning", "url": "", "is_read": False},
        )
        self.assertEqual((follow["color"], follow["url"], follow["is_read"]), ("primary", "/posts/1/", True))
        self.assertIn("created_at", follow)

    def test_only_mine(self):
        notification(self.beto)
        self.assertEqual(self.client.get(URL).data["count"], 0)

    def test_25_per_page_and_missing_page(self):
        for n in range(27):
            notification(self.ana, minutes_ago=n)
        first = self.client.get(URL).data
        self.assertEqual((first["count"], first["total_pages"], len(first["results"])), (27, 2, 25))
        self.assertEqual(len(self.client.get(first["next"]).data["results"]), 2)
        missing = self.client.get(URL, {"page": 9})
        self.assertEqual((missing.status_code, missing.data["total_pages"]), (404, 2))

    def test_query_count_is_constant(self):
        for n in range(6):
            notification(self.ana)
        with self.assertNumQueries(2):   # count + página
            self.client.get(URL)

    def test_requires_session(self):
        self.assertEqual(APIClient().get(URL).status_code, 403)

    def test_actions_do_not_generate_notifications_yet(self):
        # Etapa actual: la generación desde las apps está pendiente (decisión del proyecto).
        post = Post.objects.create(author=self.ana, body="hola")
        beto = client_for(self.beto)
        beto.put(f"/api/social/posts/{post.pk}/reaction/", {"emoji": "joy"}, format="json")
        beto.post(f"/api/social/posts/{post.pk}/comments/", {"body": "hola"}, format="json")
        beto.put(f"/api/social/follows/{self.ana.pk}/")
        self.assertFalse(Notification.objects.exists())


class AvisosPageTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.client.force_login(self.ana)

    def test_bell_and_bottom_tab_go_to_avisos(self):
        home = self.client.get("/").content.decode()
        # campana, pestaña «Avisos», acceso rápido, menú lateral (pantallas grandes) y «Ver todos» del widget
        self.assertEqual(home.count('href="/notifications/"'), 5)
        self.assertNotIn('data-ws-view="avisos"', home)                    # ya no es una vista de la portada
        page = self.client.get("/notifications/")
        self.assertContains(page, "<h1", count=1)
        self.assertContains(page, ">Avisos</h1>")
        self.assertContains(page, 'data-notifications-url="/api/notifications/"')
        self.assertContains(page, 'aria-current="page"')                   # «Avisos» marcada en la barra
        for state in ("loading", "empty", "error", "ready"):
            self.assertContains(page, f'data-notifications-state="{state}"', count=1)

    def test_post_detail_page(self):
        post = Post.objects.create(author=self.ana, body="x")
        page = self.client.get(f"/posts/{post.pk}/?comments=1&comment=7")
        self.assertContains(page, f'data-ws-feed="/api/social/posts/?id={post.pk}"')
        self.assertContains(page, 'data-highlight-comment="7"')


class PushSubscriptionModelTests(TestCase):
    """``PushSubscription``: varios dispositivos por persona; el endpoint no se repite."""

    def test_one_user_many_devices_unique_endpoint(self):
        from django.db import IntegrityError
        from apps.accounts.models import User
        from apps.notifications.models import PushSubscription

        user = User.objects.create_user(username="push", email="push@example.test", password="x-Pass-12345")
        PushSubscription.objects.create(user=user, endpoint="https://push.example/a", p256dh="k", auth="a")
        PushSubscription.objects.create(user=user, endpoint="https://push.example/b", p256dh="k", auth="a")
        self.assertEqual(user.push_subscriptions.count(), 2)
        with self.assertRaises(IntegrityError):
            PushSubscription.objects.create(user=user, endpoint="https://push.example/a", p256dh="k", auth="a")


class NotificationActionsTests(TestCase):
    """Tamaño de página, leídas / no leídas, contador, eliminar y ``notify``."""

    def setUp(self):
        self.ana = make_user("ana")
        self.beto = make_user("beto")
        self.client = client_for(self.ana)

    def test_page_size_up_to_25(self):
        for n in range(30):
            notification(self.ana, minutes_ago=n)
        small = self.client.get(URL, {"page_size": 10}).data
        self.assertEqual((len(small["results"]), small["total_pages"]), (10, 3))
        self.assertEqual(len(self.client.get(URL, {"page_size": 100}).data["results"]), 25)
        self.assertEqual(len(self.client.get(URL, {"page_size": "abc"}).data["results"]), 25)

    def test_read_unread_count_and_read_all(self):
        first, second = notification(self.ana), notification(self.ana)
        self.assertEqual(self.client.get(f"{URL}unread-count/").data, {"unread": 2})
        response = self.client.patch(f"{URL}{first.pk}/", {"is_read": True}, format="json")
        self.assertTrue(response.data["is_read"])
        self.assertEqual(self.client.get(URL, {"unread": "1"}).data["count"], 1)
        self.assertFalse(self.client.patch(f"{URL}{first.pk}/", {"is_read": False}, format="json").data["is_read"])
        self.assertEqual(self.client.post(f"{URL}read-all/").data, {"updated": 2, "unread": 0})
        second.refresh_from_db()
        self.assertIsNotNone(second.read_at)

    def test_cannot_touch_someone_elses(self):
        theirs = notification(self.beto)
        self.assertEqual(self.client.get(f"{URL}{theirs.pk}/").status_code, 404)
        self.assertEqual(self.client.patch(f"{URL}{theirs.pk}/", {"is_read": True}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(f"{URL}{theirs.pk}/").status_code, 404)
        self.client.post(f"{URL}read-all/")
        theirs.refresh_from_db()
        self.assertIsNone(theirs.read_at)

    def test_delete(self):
        mine = notification(self.ana)
        self.assertEqual(self.client.delete(f"{URL}{mine.pk}/").status_code, 204)
        self.assertFalse(Notification.objects.filter(pk=mine.pk).exists())

    def test_notify_service(self):
        from django.core.exceptions import ValidationError
        from apps.notifications.services.notifications import notify

        created = notify(recipient=self.ana, title="  Nuevo   aviso ", url="/posts/1/", color="danger")
        self.assertEqual((created.title, created.color), ("Nuevo aviso", "danger"))
        for bad in ({"title": ""}, {"title": "x", "url": "https://evil.test"}, {"title": "x", "url": "//evil.test"},
                    {"title": "x", "color": "rosa"}):
            with self.assertRaises(ValidationError):
                notify(recipient=self.ana, **bad)
        self.beto.is_active = False
        self.beto.save()
        self.assertIsNone(notify(recipient=self.beto, title="x"))


class PushApiTests(TestCase):
    """Registrar y quitar dispositivos push desde la API."""

    SUBSCRIPTION = {"endpoint": "https://push.example/abc", "keys": {"p256dh": "BPk3", "auth": "a1b2"}}

    def setUp(self):
        self.ana = make_user("ana")
        self.client = client_for(self.ana)

    def test_config_without_keys(self):
        self.assertEqual(self.client.get(f"{URL}push/config/").data, {"enabled": False, "public_key": ""})

    def test_subscribe_is_idempotent_and_hides_keys(self):
        from apps.notifications.models import PushSubscription

        first = self.client.post(f"{URL}push/subscriptions/", self.SUBSCRIPTION, format="json", HTTP_USER_AGENT="Firefox")
        self.assertEqual(first.status_code, 201)
        self.assertNotIn("p256dh", first.data)
        self.client.post(f"{URL}push/subscriptions/", self.SUBSCRIPTION, format="json")
        self.assertEqual(PushSubscription.objects.count(), 1)
        listing = self.client.get(f"{URL}push/subscriptions/").data
        self.assertEqual(listing["count"], 1)   # paginado como toda la API

    def test_shared_device_moves_to_current_user(self):
        from apps.notifications.models import PushSubscription

        self.client.post(f"{URL}push/subscriptions/", self.SUBSCRIPTION, format="json")
        beto = make_user("beto")
        client_for(beto).post(f"{URL}push/subscriptions/", self.SUBSCRIPTION, format="json")
        self.assertEqual(PushSubscription.objects.get().user, beto)

    def test_rejects_invalid_subscription(self):
        bad = {**self.SUBSCRIPTION, "endpoint": "http://push.example/abc"}
        self.assertEqual(self.client.post(f"{URL}push/subscriptions/", bad, format="json").status_code, 400)
        no_keys = {**self.SUBSCRIPTION, "keys": {"p256dh": "", "auth": "x"}}
        self.assertEqual(self.client.post(f"{URL}push/subscriptions/", no_keys, format="json").status_code, 400)

    def test_unsubscribe_by_endpoint_and_by_id(self):
        from apps.notifications.models import PushSubscription

        self.client.post(f"{URL}push/subscriptions/", self.SUBSCRIPTION, format="json")
        response = self.client.post(f"{URL}push/unsubscribe/", {"endpoint": self.SUBSCRIPTION["endpoint"]}, format="json")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(PushSubscription.objects.exists())

        created = self.client.post(f"{URL}push/subscriptions/", self.SUBSCRIPTION, format="json").data
        other = client_for(make_user("beto"))
        self.assertEqual(other.delete(f"{URL}push/subscriptions/{created['id']}/").status_code, 404)
        self.assertEqual(self.client.delete(f"{URL}push/subscriptions/{created['id']}/").status_code, 204)
