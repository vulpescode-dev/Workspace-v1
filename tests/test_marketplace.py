"""Pruebas del Marketplace: servicio (fotos, precio, estatus), permisos y API /api/marketplace/."""
import io
import shutil
import tempfile

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.marketplace.models import LISTING_MAX_IMAGES, Listing, ListingCategory
from apps.marketplace.services.listings import create_listing, delete_listing, edit_listing

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
        self.assertEqual(APIClient().get(LISTINGS_URL).status_code, 403)

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

    def test_categories_only_active(self):
        ListingCategory.objects.create(name="Vieja", slug="vieja", is_active=False)
        response = self.client.get("/api/marketplace/categories/")
        self.assertEqual([c["slug"] for c in response.data], ["electronica"])
