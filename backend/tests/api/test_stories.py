"""Estados (tipo Instagram): subir foto/video, 24 horas de vida, fila con vistos/sin ver, borrar y entrega autorizada."""
import io
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.social.models import STORY_MAX_ACTIVE, Story, StoryView

STORIES_URL = "/api/social/stories/"
MP4_HEAD = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 64


def webp(name="estado.webp"):
    buffer = io.BytesIO()
    Image.new("RGB", (90, 160), (0, 102, 204)).save(buffer, "WEBP")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/webp")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class StoryTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.ana = User.objects.create_user(username="ana", email="ana@orienta.soy", first_name="Ana", last_name="Robles", password="x")
        self.beto = User.objects.create_user(username="beto", email="beto@orienta.soy", first_name="Beto", last_name="Sáenz", password="x")
        self.carla = User.objects.create_user(username="carla", email="carla@orienta.soy", first_name="Carla", password="x")

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def upload(self, user, file=None):
        return client_for(user).post(STORIES_URL, {"file": file or webp()}, format="multipart")

    def test_upload_image_and_video_expire_in_24_hours(self):
        response = self.upload(self.ana)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["kind"], "image")
        self.assertEqual(data["url"], f"/api/social/stories/{data['id']}/file/")
        story = Story.objects.get(pk=data["id"])
        self.assertAlmostEqual((story.expires_at - story.created_at).total_seconds(), 24 * 3600, delta=5)
        self.assertEqual(Path(story.file.name).name, f"{story.pk}.webp")

        video = SimpleUploadedFile("clip.mp4", MP4_HEAD, content_type="video/mp4")
        self.assertEqual(self.upload(self.ana, video).json()["kind"], "video")

    def test_rejects_files_that_are_not_webp_or_video(self):
        fake = SimpleUploadedFile("foto.webp", b"<script>alert(1)</script>", content_type="image/webp")
        response = self.upload(self.ana, fake)
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json())
        self.assertEqual(client_for(self.ana).post(STORIES_URL, {}, format="multipart").status_code, 400)
        self.assertFalse(Story.objects.exists())

    def test_limit_of_active_stories(self):
        for _ in range(STORY_MAX_ACTIVE):
            Story.objects.create(author=self.ana, kind="image", content_type="image/webp", size=1,
                                 expires_at=timezone.now() + timedelta(hours=1))
        self.assertEqual(self.upload(self.ana).status_code, 400)

    def test_tray_mine_first_then_unseen_then_seen(self):
        seen_story = Story.objects.get(pk=self.upload(self.beto).json()["id"])
        self.upload(self.carla)
        self.upload(self.ana)
        StoryView.objects.create(story=seen_story, viewer=self.ana)

        tray = client_for(self.ana).get(STORIES_URL).json()
        self.assertEqual([group["author"]["id"] for group in tray], [self.ana.pk, self.carla.pk, self.beto.pk])
        self.assertEqual([group["is_mine"] for group in tray], [True, False, False])
        self.assertEqual([group["has_unseen"] for group in tray], [False, True, False])
        self.assertTrue(tray[2]["stories"][0]["seen"])

    def test_expired_and_deleted_stories_are_gone(self):
        story = Story.objects.get(pk=self.upload(self.beto).json()["id"])
        Story.objects.filter(pk=story.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(client_for(self.ana).get(STORIES_URL).json(), [])
        self.assertEqual(client_for(self.ana).get(f"{STORIES_URL}{story.pk}/file/").status_code, 404)

    def test_mark_seen_once_and_not_for_my_own(self):
        story_id = self.upload(self.beto).json()["id"]
        for _ in range(2):
            self.assertEqual(client_for(self.ana).post(f"{STORIES_URL}{story_id}/seen/").status_code, 204)
        self.assertEqual(StoryView.objects.filter(story_id=story_id).count(), 1)
        client_for(self.beto).post(f"{STORIES_URL}{story_id}/seen/")
        self.assertFalse(StoryView.objects.filter(viewer=self.beto).exists())

    def test_only_the_author_deletes(self):
        story_id = self.upload(self.beto).json()["id"]
        self.assertEqual(client_for(self.ana).delete(f"{STORIES_URL}{story_id}/").status_code, 403)
        self.assertEqual(client_for(self.beto).delete(f"{STORIES_URL}{story_id}/").status_code, 204)
        self.assertEqual(client_for(self.ana).get(STORIES_URL).json(), [])

    def test_file_is_served_only_through_the_authorized_view(self):
        story_id = self.upload(self.beto).json()["id"]
        url = f"{STORIES_URL}{story_id}/file/"
        self.assertEqual(APIClient().get(url).status_code, 401)
        response = client_for(self.ana).get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/webp")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_inactive_authors_are_hidden(self):
        self.upload(self.beto)
        User.objects.filter(pk=self.beto.pk).update(is_active=False)
        self.assertEqual(client_for(self.ana).get(STORIES_URL).json(), [])

    def test_only_the_author_sees_who_viewed(self):
        story_id = self.upload(self.beto).json()["id"]
        client_for(self.ana).post(f"{STORIES_URL}{story_id}/seen/")
        client_for(self.carla).post(f"{STORIES_URL}{story_id}/seen/")

        mine = client_for(self.beto).get(STORIES_URL).json()[0]["stories"][0]
        self.assertEqual(mine["views_count"], 2)
        theirs = client_for(self.ana).get(STORIES_URL).json()[0]["stories"][0]
        self.assertIsNone(theirs["views_count"])   # los demás no ven el contador

        viewers = client_for(self.beto).get(f"{STORIES_URL}{story_id}/viewers/").json()["results"]
        self.assertEqual({row["user"]["id"] for row in viewers}, {self.ana.pk, self.carla.pk})
        self.assertEqual(client_for(self.ana).get(f"{STORIES_URL}{story_id}/viewers/").status_code, 403)
