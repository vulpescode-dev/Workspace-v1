"""Pruebas del perfil: página, API, presentación, foto/portada (WebP, <id>.webp, entrega autorizada) y posts por autor."""
import io
import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.models import Department
from apps.social.models import Post

ME_URL = "/api/accounts/me/"


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


def webp(name="foto.webp", fmt="WEBP", size=(40, 40), color=(0, 102, 204)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


class ProfileApiTests(TestCase):
    def setUp(self):
        self.me = make_user("ana", first_name="Ana", last_name="Ruiz", job_title="Analista",
                            department=Department.objects.create(name="TI"))
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def test_profile_fields(self):
        Post.objects.create(author=self.me, body="hola")
        data = self.client.get(f"/api/accounts/users/{self.me.pk}/").data
        self.assertEqual(
            {k: data[k] for k in ("name", "initials", "job_title", "department", "is_me", "posts_count")},
            {"name": "Ana Ruiz", "initials": "AR", "job_title": "Analista", "department": "TI", "is_me": True, "posts_count": 1},
        )
        self.assertEqual(data["avatar_url"], "")
        self.assertIsNone(data["birthday"])

    def test_birthday_is_day_and_month_only(self):
        from datetime import date

        self.me.birth_date = date(1990, 11, 18)
        self.me.save()
        data = self.client.get(f"/api/accounts/users/{self.me.pk}/").data
        self.assertEqual(data["birthday"], {"day": 18, "month": 11})
        self.assertNotIn("1990", str(data))                                   # nunca el año (la edad)

    def test_other_profile_and_missing_or_inactive(self):
        other = make_user("beto")
        self.assertFalse(self.client.get(f"/api/accounts/users/{other.pk}/").data["is_me"])
        self.assertEqual(self.client.get("/api/accounts/users/999/").status_code, 404)
        gone = make_user("baja", is_active=False)
        self.assertEqual(self.client.get(f"/api/accounts/users/{gone.pk}/").status_code, 404)

    def test_requires_authentication(self):
        self.assertEqual(APIClient().get(f"/api/accounts/users/{self.me.pk}/").status_code, 401)
        self.assertEqual(APIClient().patch(ME_URL, {"bio": "x"}, format="json").status_code, 401)

    def test_edit_bio_normalizes_and_limits(self):
        response = self.client.patch(ME_URL, {"bio": "  Me gusta   el diseño\n y el café  "}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["bio"], "Me gusta el diseño y el café")
        self.assertEqual(self.client.patch(ME_URL, {"bio": "x" * 281}, format="json").status_code, 400)

    def test_cannot_change_hr_fields(self):
        self.client.patch(ME_URL, {"bio": "hola", "job_title": "Director", "department": "Dirección"}, format="json")
        self.me.refresh_from_db()
        self.assertEqual((self.me.job_title, self.me.department.name), ("Analista", "TI"))

    def test_manager_only_when_active(self):
        boss = make_user("jefa", first_name="Jefa", last_name="Uno")
        self.me.manager = boss
        self.me.save()
        self.assertEqual(self.client.get(ME_URL).data["manager"]["name"], "Jefa Uno")
        boss.is_active = False
        boss.save()
        self.assertIsNone(self.client.get(ME_URL).data["manager"])

    def test_posts_filtered_by_author(self):
        other = make_user("beto")
        Post.objects.create(author=self.me, body="mía")
        Post.objects.create(author=other, body="de beto")
        bodies = [p["body"] for p in self.client.get(f"/api/social/posts/?author={other.pk}").data["results"]]
        self.assertEqual(bodies, ["de beto"])
        self.assertEqual(self.client.get("/api/social/posts/?author=abc").status_code, 400)


class ProfileImageTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.me = make_user("ana")
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def upload(self, kind, file):
        return self.client.post(f"{ME_URL}{kind}/", {"file": file}, format="multipart")

    def test_avatar_saved_as_id_webp_and_served_authorized(self):
        response = self.upload("avatar", webp())
        self.assertEqual(response.status_code, 200, response.data)
        self.me.refresh_from_db()
        self.assertEqual(self.me.avatar.name, f"avatars/{self.me.pk}.webp")
        url = response.data["avatar_url"]
        self.assertTrue(url.startswith(f"/api/accounts/users/{self.me.pk}/avatar/?v="))

        image = self.client.get(url)
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image["Content-Type"], "image/webp")
        self.assertEqual(image["X-Content-Type-Options"], "nosniff")
        self.assertEqual(APIClient().get(url).status_code, 401)

    def test_replacing_keeps_name_and_changes_version(self):
        first = self.upload("avatar", webp()).data["avatar_url"]
        second = self.upload("avatar", webp(color=(244, 198, 0))).data["avatar_url"]
        self.me.refresh_from_db()
        self.assertEqual(self.me.avatar.name, f"avatars/{self.me.pk}.webp")
        self.assertEqual(len(list(Path(self.media_root, "avatars").iterdir())), 1)
        self.assertNotEqual(first, second)   # nueva versión: el navegador no muestra la foto vieja

    def test_cover_cannot_be_uploaded(self):
        # La portada es estática: no hay endpoint para cambiarla.
        self.assertEqual(self.upload("cover", webp()).status_code, 404)

    def test_rejects_non_webp_and_dangerous_files(self):
        for file in (webp("foto.png", "PNG"), SimpleUploadedFile("x.php", b"<?php echo 1; ?>", content_type="image/webp")):
            with self.subTest(file.name):
                self.assertEqual(self.upload("avatar", file).status_code, 400)
        self.me.refresh_from_db()
        self.assertFalse(self.me.avatar)

    def test_remove_image_deletes_file(self):
        self.upload("avatar", webp())
        path = Path(self.media_root, f"avatars/{self.me.pk}.webp")
        self.assertTrue(path.exists())
        response = self.client.delete(f"{ME_URL}avatar/")
        self.assertEqual(response.data["avatar_url"], "")
        self.assertFalse(path.exists())

    def test_post_author_avatar_uses_authorized_url(self):
        self.upload("avatar", webp())
        Post.objects.create(author=self.me, body="hola")
        author = self.client.get("/api/social/posts/").data["results"][0]["author"]
        self.assertTrue(author["avatar_url"].startswith(f"/api/accounts/users/{self.me.pk}/avatar/?v="))


class ProfilePhotosTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.beto = make_user("beto")
        self.client = APIClient()
        self.client.force_authenticate(self.beto)

    def attach(self, post, kind="image"):
        from apps.social.models import PostAttachment

        return PostAttachment.objects.create(post=post, kind=kind, content_type="image/webp", size=1, width=10, height=10)

    def test_only_images_of_live_posts_by_author_newest_first(self):
        old = Post.objects.create(author=self.ana, body="vieja")
        new = Post.objects.create(author=self.ana, body="nueva")
        deleted = Post.objects.create(author=self.ana, body="borrada")
        mine = Post.objects.create(author=self.beto, body="de beto")
        old_photo, new_photo = self.attach(old), self.attach(new)
        self.attach(new, kind="video")
        self.attach(deleted)
        self.attach(mine)
        deleted.soft_delete()

        data = self.client.get(f"/api/social/photos/?author={self.ana.pk}").data
        self.assertEqual([p["id"] for p in data["results"]], [new_photo.pk, old_photo.pk])
        self.assertEqual(data["results"][0]["post"], new.pk)
        self.assertTrue(data["results"][0]["url"].endswith(f"/attachments/{new_photo.pk}/file/"))

    def test_requires_author_and_session(self):
        self.assertEqual(self.client.get("/api/social/photos/").status_code, 400)
        self.assertEqual(APIClient().get(f"/api/social/photos/?author={self.ana.pk}").status_code, 401)


class UserAgeTests(TestCase):
    """``User.age``: años cumplidos según la fecha de hoy del servidor."""

    def age_on(self, birth, today):
        from unittest import mock
        with mock.patch("django.utils.timezone.localdate", return_value=today):
            return User(birth_date=birth).age

    def test_age(self):
        from datetime import date
        self.assertEqual(self.age_on(date(1994, 10, 29), date(2026, 10, 28)), 31)
        self.assertEqual(self.age_on(date(1994, 10, 29), date(2026, 10, 29)), 32)
        self.assertEqual(self.age_on(date(2000, 2, 29), date(2026, 3, 1)), 26)
        self.assertIsNone(User(birth_date=None).age)

    def test_gender_and_marital_status_are_optional(self):
        user = make_user("sin-datos")
        self.assertIsNone(user.gender)
        self.assertIsNone(user.marital_status)


class MyAccessTests(TestCase):
    """``access`` en /me: qué puedo hacer (para mostrar u ocultar botones en el frontend)."""

    def setUp(self):
        from apps.accounts.models import Role, UserRole
        Role.objects.update(is_default=False)   # sin «Lector» automático: permisos controlados aquí
        self.me = make_user("ana")
        role = Role.objects.get(name="Blogger")
        UserRole.objects.create(user=self.me, role=role)
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def test_me_lists_my_permissions(self):
        access = self.client.get(ME_URL).data["access"]
        self.assertEqual(access, {"is_superuser": False, "permissions": ["blog.articles.create", "blog.articles.view"]})

    def test_superuser_flag(self):
        boss = User.objects.create_superuser(username="jefa", email="jefa@example.test", password="x-Pass-12345")
        self.client.force_authenticate(boss)
        self.assertTrue(self.client.get(ME_URL).data["access"]["is_superuser"])

    def test_permissions_of_others_never_leak(self):
        other = make_user("beto")
        data = self.client.get(f"/api/accounts/users/{other.pk}/").data
        self.assertNotIn("access", data)

    def test_updating_my_bio_keeps_access(self):
        data = self.client.patch(ME_URL, {"bio": "Hola"}, format="json").data
        self.assertIn("blog.articles.create", data["access"]["permissions"])
