"""Pruebas de media en publicaciones: validación por contenido, nombres <id>.<ext> y entrega autorizada."""
import io
import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.core import uploads
from apps.social.models import Post, PostAttachment

POSTS_URL = "/api/social/posts/"
MP4_HEAD = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 64
MOV_HEAD = b"\x00\x00\x00\x14ftypqt  \x00\x00\x00\x00qt  " + b"\x00" * 64
WEBM_HEAD = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm" + b"\x00" * 64


def image_file(name="foto.webp", fmt="WEBP", size=(64, 48)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (0, 102, 204)).save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


def raw_file(name, content, content_type="application/octet-stream"):
    return SimpleUploadedFile(name, content, content_type=content_type)


class MediaValidationTests(TestCase):
    """El servidor decide por el contenido, no por el nombre ni el Content-Type."""

    def assert_rejected(self, upload):
        with self.assertRaises(Exception) as ctx:
            uploads.check_media_upload(upload)
        self.assertEqual(type(ctx.exception).__name__, "ValidationError")

    def test_accepts_webp_and_videos(self):
        self.assertEqual(uploads.check_media_upload(image_file()).extension, ".webp")
        self.assertEqual(uploads.check_media_upload(raw_file("v.mp4", MP4_HEAD)).extension, ".mp4")
        self.assertEqual(uploads.check_media_upload(raw_file("v.mov", MOV_HEAD)).extension, ".mov")
        self.assertEqual(uploads.check_media_upload(raw_file("v.webm", WEBM_HEAD)).extension, ".webm")

    def test_webp_dimensions_are_recorded(self):
        info = uploads.check_media_upload(image_file(size=(120, 80)))
        self.assertEqual((info.width, info.height, info.kind), (120, 80, "image"))

    def test_rejects_dangerous_files_even_with_media_names(self):
        for upload in (
            raw_file("virus.exe", b"MZ\x90\x00" + b"\x00" * 100),
            raw_file("foto.webp", b"MZ\x90\x00" + b"\x00" * 100, "image/webp"),     # .exe disfrazado
            raw_file("shell.php", b"<?php system($_GET['c']); ?>"),
            raw_file("img.php.webp", b"<?php echo 1; ?>", "image/webp"),
            raw_file("page.html", b"<html><script>alert(1)</script></html>", "text/html"),
            raw_file("x.svg", b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", "image/svg+xml"),
            raw_file("doc.pdf", b"%PDF-1.7\n1 0 obj << /JavaScript >>", "application/pdf"),
            raw_file("a.zip", b"PK\x03\x04" + b"\x00" * 100, "application/zip"),
            raw_file("vacio.webp", b"", "image/webp"),
        ):
            with self.subTest(upload.name):
                self.assert_rejected(upload)

    def test_rejects_non_webp_images(self):
        # El navegador convierte a WebP; si llega PNG/JPEG es que no pasó por procesarAWebP.
        self.assert_rejected(image_file("foto.png", "PNG"))
        self.assert_rejected(image_file("foto.jpg", "JPEG"))

    def test_rejects_corrupt_webp(self):
        data = image_file().read()
        self.assert_rejected(raw_file("roto.webp", data[:40], "image/webp"))

    def test_rejects_oversized(self):
        with self.settings():
            original = uploads.IMAGE_MAX_BYTES
            uploads.IMAGE_MAX_BYTES = 10
            try:
                self.assert_rejected(image_file())
            finally:
                uploads.IMAGE_MAX_BYTES = original
        self.assert_rejected(image_file(size=(uploads.IMAGE_MAX_SIDE + 1, 10)))


class PostMediaApiTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.client = APIClient()
        self.user = User.objects.create_user(username="ana", email="ana@example.test", password="x")
        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def post(self, **data):
        return self.client.post(POSTS_URL, data, format="multipart")

    def test_creates_post_with_image_and_video_named_by_id(self):
        response = self.post(body="Con fotos", files=[image_file("Vacaciones 2026.webp"), raw_file("clip.mp4", MP4_HEAD)])
        self.assertEqual(response.status_code, 201, response.data)
        image, video = PostAttachment.objects.order_by("position")
        self.assertEqual(Path(image.file.name).name, f"{image.pk}.webp")
        self.assertEqual(Path(video.file.name).name, f"{video.pk}.mp4")
        self.assertEqual(image.original_name, "Vacaciones 2026.webp")
        self.assertTrue(Path(self.media_root, image.file.name).exists())
        kinds = [a["kind"] for a in response.data["attachments"]]
        self.assertEqual(kinds, ["image", "video"])
        self.assertTrue(response.data["attachments"][0]["url"].endswith(f"/attachments/{image.pk}/file/"))

    def test_multipart_line_breaks_are_normalized(self):
        response = self.post(body="Hola\r\nsegunda línea", files=[image_file()])
        self.assertEqual(response.data["body"], "Hola\nsegunda línea")

    def test_post_with_only_media_is_allowed(self):
        self.assertEqual(self.post(body="", files=[image_file()]).status_code, 201)

    def test_one_bad_file_rejects_everything(self):
        response = self.post(body="hola", files=[image_file(), raw_file("x.php", b"<?php ?>")])
        self.assertEqual(response.status_code, 400)
        self.assertIn("files", response.data)
        self.assertFalse(Post.objects.exists())
        self.assertFalse(PostAttachment.objects.exists())

    def test_max_files_per_post(self):
        files = [image_file(f"{n}.webp") for n in range(11)]
        response = self.post(body="muchas", files=files)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Post.objects.exists())

    def test_file_is_served_only_through_authorized_view(self):
        self.post(body="x", files=[image_file()])
        attachment = PostAttachment.objects.get()
        url = f"/api/social/attachments/{attachment.pk}/file/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/webp")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertTrue(b"".join(response.streaming_content).startswith(b"RIFF"))

        self.assertEqual(APIClient().get(url).status_code, 401)
        self.assertEqual(self.client.get("/api/social/attachments/999/file/").status_code, 404)

    def test_deleting_post_removes_files(self):
        self.post(body="x", files=[image_file()])
        path = Path(self.media_root, PostAttachment.objects.get().file.name)
        self.assertTrue(path.exists())
        Post.objects.get().delete()
        self.assertFalse(path.exists())

    def test_feed_query_count_with_attachments(self):
        for n in range(3):
            self.post(body=f"p{n}", files=[image_file()])
        with self.assertNumQueries(4):  # count + página + adjuntos (prefetch) + reacciones
            self.client.get(POSTS_URL)
