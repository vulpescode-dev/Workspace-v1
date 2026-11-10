"""Pruebas del Marketplace: servicio (fotos, precio, estatus), permisos y API /api/marketplace/."""
import io
import shutil
import tempfile
from pathlib import Path

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.marketplace.models import LISTING_MAX_IMAGES, Listing, ListingCategory
from apps.marketplace.services.listings import add_images, create_listing, delete_listing, edit_listing, remove_image

LISTINGS_URL = "/api/marketplace/listings/"
MEDIA_DIR = tempfile.mkdtemp()


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


def webp(name="foto.webp", fmt="WEBP"):
    buffer = io.BytesIO()
    Image.new("RGB", (40, 40), (0, 102, 204)).save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


@override_settings(MEDIA_ROOT=MEDIA_DIR)
class ListingServiceTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_DIR, ignore_errors=True)

    def setUp(self):
        self.seller = make_user("vende")
        self.other = make_user("otra")
        self.category = ListingCategory.objects.create(name="Hogar", slug="hogar")

    def test_creates_listing_with_images_and_category(self):
        listing = create_listing(
            seller=self.seller, title="  Silla   de oficina ", description="Casi nueva", price="1500",
            category_id=self.category.pk, files=[webp(), webp("b.webp")],
        )
        self.assertEqual(listing.title, "Silla de oficina")
        self.assertEqual(str(listing.price), "1500.00")
        self.assertEqual(listing.status, Listing.Status.AVAILABLE)
        self.assertEqual(listing.images.count(), 2)
        self.assertTrue(listing.images.first().file.name.endswith(".webp"))

    def test_price_is_optional_and_validated(self):
        self.assertIsNone(create_listing(seller=self.seller, title="Libro").price)
        for bad in ("-1", "abc", "NaN"):
            with self.assertRaises(ValidationError):
                create_listing(seller=self.seller, title="Libro", price=bad)

    def test_rejects_more_than_max_images_and_non_webp(self):
        with self.assertRaises(ValidationError):
            create_listing(seller=self.seller, title="X", files=[webp(f"{i}.webp") for i in range(LISTING_MAX_IMAGES + 1)])
        with self.assertRaises(ValidationError):
            create_listing(seller=self.seller, title="X", files=[webp("a.png", fmt="PNG")])
        self.assertFalse(Listing.objects.exists())

    def test_rejects_inactive_category(self):
        self.category.is_active = False
        self.category.save()
        with self.assertRaises(ValidationError):
            create_listing(seller=self.seller, title="X", category_id=self.category.pk)

    def test_mark_sold_and_back(self):
        listing = create_listing(seller=self.seller, title="Bici")
        edit_listing(user=self.seller, listing=listing, status=Listing.Status.SOLD)
        self.assertIsNotNone(listing.sold_at)
        edit_listing(user=self.seller, listing=listing, status=Listing.Status.AVAILABLE)
        self.assertIsNone(listing.sold_at)

    def test_add_and_remove_images(self):
        listing = create_listing(seller=self.seller, title="Bici", files=[webp()])
        add_images(user=self.seller, listing=listing, files=[webp("b.webp"), webp("c.webp")])
        self.assertEqual(list(listing.images.values_list("position", flat=True)), [0, 1, 2])
        with self.assertRaises(ValidationError):
            add_images(user=self.seller, listing=listing, files=[webp(f"{i}.webp") for i in range(LISTING_MAX_IMAGES - 2)])
        with self.assertRaises(PermissionDenied):
            add_images(user=self.other, listing=listing, files=[webp()])
        first = listing.images.first()
        with self.assertRaises(PermissionDenied):
            remove_image(user=self.other, image=first)
        path = first.file.path
        remove_image(user=self.seller, image=first)
        self.assertEqual(listing.images.count(), 2)
        self.assertFalse(Path(path).exists())

    def test_only_seller_can_edit_or_delete(self):
        listing = create_listing(seller=self.seller, title="Bici")
        with self.assertRaises(PermissionDenied):
            edit_listing(user=self.other, listing=listing, status=Listing.Status.SOLD)
        with self.assertRaises(PermissionDenied):
            delete_listing(user=self.other, listing=listing)


@override_settings(MEDIA_ROOT=MEDIA_DIR)
class ListingApiTests(TestCase):
    def setUp(self):
        self.seller = make_user("vende")
        self.other = make_user("otra")
        self.category = ListingCategory.objects.create(name="Electrónica", slug="electronica")
        self.client = APIClient()
        self.client.force_authenticate(self.seller)

    def test_requires_login(self):
        self.assertEqual(APIClient().get(LISTINGS_URL).status_code, 401)

    def test_create_list_and_filter(self):
        response = self.client.post(
            LISTINGS_URL, {"title": "Monitor", "price": "2000", "category": self.category.pk, "files": [webp()]},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data["images"]), 1)
        self.assertTrue(response.data["is_mine"])
        create_listing(seller=self.other, title="Lámpara")

        self.assertEqual(self.client.get(LISTINGS_URL).data["count"], 2)
        self.assertEqual(self.client.get(LISTINGS_URL, {"category": "electronica"}).data["count"], 1)
        self.assertEqual(self.client.get(LISTINGS_URL, {"q": "lámp"}).data["count"], 1)
        self.assertEqual(self.client.get(LISTINGS_URL, {"seller": self.other.pk}).data["count"], 1)
        self.assertEqual(self.client.get(LISTINGS_URL, {"status": "sold"}).data["count"], 0)
        self.assertEqual(self.client.get(LISTINGS_URL, {"status": "otro"}).status_code, 400)

    def test_patch_status_and_permissions(self):
        mine = create_listing(seller=self.seller, title="Bici")
        theirs = create_listing(seller=self.other, title="Patines")
        response = self.client.patch(f"{LISTINGS_URL}{mine.pk}/", {"status": "sold"}, format="json")
        self.assertEqual(response.data["status"], "sold")
        self.assertEqual(response.data["title"], "Bici")
        self.assertEqual(self.client.patch(f"{LISTINGS_URL}{theirs.pk}/", {"status": "sold"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(f"{LISTINGS_URL}{theirs.pk}/").status_code, 403)

    def test_deleted_listing_and_its_images_are_hidden(self):
        listing = create_listing(seller=self.seller, title="Bici", files=[webp()])
        image_url = self.client.get(f"{LISTINGS_URL}{listing.pk}/").data["images"][0]["url"]
        self.assertEqual(self.client.get(image_url).status_code, 200)
        self.assertEqual(self.client.delete(f"{LISTINGS_URL}{listing.pk}/").status_code, 204)
        self.assertEqual(self.client.get(f"{LISTINGS_URL}{listing.pk}/").status_code, 404)
        self.assertEqual(self.client.get(image_url).status_code, 404)

    def test_add_and_remove_images_api(self):
        mine = create_listing(seller=self.seller, title="Bici")
        theirs = create_listing(seller=self.other, title="Patines", files=[webp()])
        response = self.client.post(f"{LISTINGS_URL}{mine.pk}/images/", {"files": [webp(), webp("b.webp")]}, format="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data["images"]), 2)
        self.assertEqual(self.client.post(f"{LISTINGS_URL}{mine.pk}/images/", {}, format="multipart").status_code, 400)
        self.assertEqual(self.client.post(f"{LISTINGS_URL}{theirs.pk}/images/", {"files": [webp()]}, format="multipart").status_code, 403)

        image_id = response.data["images"][0]["id"]
        self.assertEqual(self.client.delete(f"/api/marketplace/images/{image_id}/").status_code, 204)
        self.assertEqual(len(self.client.get(f"{LISTINGS_URL}{mine.pk}/").data["images"]), 1)
        self.assertEqual(self.client.delete(f"/api/marketplace/images/{theirs.images.first().pk}/").status_code, 403)
        self.assertEqual(self.client.delete("/api/marketplace/images/99999/").status_code, 404)

    def test_categories_only_active(self):
        ListingCategory.objects.create(name="Vieja", slug="vieja", is_active=False)
        response = self.client.get("/api/marketplace/categories/")
        self.assertEqual([c["slug"] for c in response.data], ["electronica"])
