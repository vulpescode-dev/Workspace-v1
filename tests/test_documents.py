"""Pruebas de Documentos: quién sube, privacidad (empresa, departamentos, personas), versiones y descargas."""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import Permission, Role, RolePermission, User, UserRole
from apps.documents.models import Document, DocumentCategory, DocumentVersion
from apps.org.models import Department

DOCUMENTS_URL = "/api/documents/documents/"
MEDIA_DIR = tempfile.mkdtemp()
PDF = b"%PDF-1.7\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"


def make_user(username, **extra):
    return User.objects.create_user(
        username=username, email=f"{username}@example.test", password="x-Pass-12345", first_name=username.title(),
        **extra,
    )


def grant(user, codename):
    permission, _ = Permission.objects.get_or_create(codename=codename)
    role, _ = Role.objects.get_or_create(name=codename)
    RolePermission.objects.get_or_create(role=role, permission=permission)
    UserRole.objects.create(user=user, role=role)


def pdf(name="politica.pdf", body=PDF):
    return SimpleUploadedFile(name, body, content_type="application/pdf")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@override_settings(MEDIA_ROOT=MEDIA_DIR)
class DocumentsApiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_DIR, ignore_errors=True)

    def setUp(self):
        self.hr = Department.objects.create(name="Recursos Humanos")
        self.ti = Department.objects.create(name="Sistemas")
        self.author = make_user("autora", department=self.hr)
        grant(self.author, "documents.documents.create")
        self.colleague = make_user("colega", department=self.hr)
        self.techie = make_user("tecnico", department=self.ti)
        self.nobody = make_user("sindepto")
        self.policies = DocumentCategory.objects.create(name="Políticas")

    def create(self, user=None, **data):
        payload = {"title": "Política de vacaciones", "category": self.policies.pk, "file": pdf()}
        payload.update(data)
        return client_for(user or self.author).post(DOCUMENTS_URL, payload, format="multipart")

    def visible_ids(self, user, query=""):
        response = client_for(user).get(DOCUMENTS_URL + query)
        self.assertEqual(response.status_code, 200)
        return {item["id"] for item in response.data["results"]}

    # --- Crear --------------------------------------------------------------------------------

    def test_create_needs_permission_and_starts_at_v1(self):
        self.assertEqual(self.create(user=self.colleague).status_code, 403)
        response = self.create(description="Días y cómo pedirlos.")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["current_version"]["number"], 1)
        self.assertEqual(response.data["current_version"]["notes"], "Versión inicial")
        self.assertEqual(response.data["current_version"]["name"], "politica.pdf")
        self.assertEqual([v["number"] for v in response.data["versions"]], [1])
        self.assertTrue(response.data["can_manage"])
        document = Document.objects.get()
        self.assertTrue(document.current_version.file.name.startswith(f"documents/{document.pk}/"))

    def test_create_validates_category_file_and_audience(self):
        inactive = DocumentCategory.objects.create(name="Vieja", is_active=False)
        self.assertIn("category", self.create(category=inactive.pk).data)
        self.assertIn("file", self.create(file="").data)
        bad = SimpleUploadedFile("virus.pdf", b"MZ\x90\x00 no soy pdf", content_type="application/pdf")
        self.assertIn("file", self.create(file=bad).data)
        self.assertIn("departments", self.create(visibility="departments").data)
        self.assertIn("users", self.create(visibility="users").data)
        self.assertIn("users", self.create(visibility="users", users=[999]).data)
        self.assertFalse(Document.objects.exists())
        self.assertFalse(DocumentVersion.objects.exists())

    # --- Privacidad ---------------------------------------------------------------------------

    def test_visibility_public_departments_and_users(self):
        public = self.create(title="Para todos").data["id"]
        hr_only = self.create(title="Solo RH", visibility="departments", departments=[self.hr.pk]).data["id"]
        shared = self.create(title="Para el técnico", visibility="users", users=[self.techie.pk]).data["id"]

        self.assertEqual(self.visible_ids(self.author), {public, hr_only, shared})       # dueña: todos los suyos
        self.assertEqual(self.visible_ids(self.colleague), {public, hr_only})            # su departamento
        self.assertEqual(self.visible_ids(self.techie), {public, shared})                # compartido con él
        self.assertEqual(self.visible_ids(self.nobody), {public})

        self.assertEqual(client_for(self.nobody).get(f"{DOCUMENTS_URL}{hr_only}/").status_code, 404)
        version = Document.objects.get(pk=hr_only).current_version_id
        self.assertEqual(client_for(self.nobody).get(f"/api/documents/versions/{version}/file/").status_code, 404)
        self.assertEqual(client_for(self.colleague).get(f"/api/documents/versions/{version}/file/").status_code, 200)

    def test_view_all_and_manage_see_everything(self):
        private = self.create(visibility="users", users=[self.colleague.pk]).data["id"]
        auditor, admin = make_user("auditor"), make_user("admin")
        grant(auditor, "documents.documents.view.all")
        grant(admin, "documents.documents.manage")
        self.assertIn(private, self.visible_ids(auditor))
        self.assertIn(private, self.visible_ids(admin))
        # view.all solo consulta: no administra.
        self.assertEqual(client_for(auditor).patch(f"{DOCUMENTS_URL}{private}/", {"title": "x"}).status_code, 403)
        self.assertEqual(client_for(admin).patch(f"{DOCUMENTS_URL}{private}/", {"title": "Nuevo"}).status_code, 200)

    def test_scopes_category_and_search(self):
        mine = self.create(title="Manual de bienvenida").data["id"]
        grant(self.techie, "documents.documents.create")
        manuals = DocumentCategory.objects.create(name="Manuales")
        theirs = self.create(user=self.techie, title="Guía VPN", category=manuals.pk, visibility="departments",
                             departments=[self.hr.pk]).data["id"]
        self.assertEqual(self.visible_ids(self.author, "?scope=mine"), {mine})
        self.assertEqual(self.visible_ids(self.author, "?scope=shared"), {theirs})
        self.assertEqual(self.visible_ids(self.author, f"?category={manuals.pk}"), {theirs})
        self.assertEqual(self.visible_ids(self.author, "?q=bienvenida"), {mine})
        self.assertEqual(client_for(self.author).get(DOCUMENTS_URL + "?scope=otro").status_code, 400)

    def test_changing_privacy_clears_lists_and_hides_from_others(self):
        doc = self.create(visibility="users", users=[self.techie.pk]).data["id"]
        url = f"{DOCUMENTS_URL}{doc}/"
        response = client_for(self.author).patch(url, {"visibility": "departments", "departments": [self.hr.pk]},
                                                 format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["shared_with"], [])
        self.assertEqual([d["id"] for d in response.data["departments"]], [self.hr.pk])
        self.assertNotIn(doc, self.visible_ids(self.techie))
        self.assertIn(doc, self.visible_ids(self.colleague))
        # Quien no lo administra no ve con quién se comparte.
        self.assertIsNone(client_for(self.colleague).get(url).data["departments"])

    # --- Versiones ----------------------------------------------------------------------------

    def test_new_versions_keep_history_and_only_managers_upload(self):
        doc = self.create().data["id"]
        url = f"{DOCUMENTS_URL}{doc}/versions/"
        self.assertEqual(client_for(self.colleague).post(url, {"file": pdf()}, format="multipart").status_code, 403)
        v2 = pdf("politica-2026.pdf", PDF.replace(b"1.7", b"1.6"))
        response = client_for(self.author).post(url, {"file": v2, "notes": "Se agregan días festivos."},
                                                format="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["current_version"]["number"], 2)
        self.assertEqual(response.data["current_version"]["notes"], "Se agregan días festivos.")
        self.assertEqual([v["number"] for v in response.data["versions"]], [2, 1])
        # La v1 sigue descargable, con su contenido de entonces.
        v1 = response.data["versions"][1]
        download = client_for(self.colleague).get(v1["url"])
        self.assertEqual(b"".join(download.streaming_content), PDF)
        self.assertIn("attachment", download["Content-Disposition"])
        self.assertEqual(download["X-Content-Type-Options"], "nosniff")
        self.assertIn("file", client_for(self.author).post(url, {}, format="multipart").data)

    def test_restore_copies_old_version_as_new_one(self):
        doc = self.create().data["id"]
        client = client_for(self.author)
        client.post(f"{DOCUMENTS_URL}{doc}/versions/", {"file": pdf("v2.pdf", PDF.replace(b"1.7", b"1.6"))},
                    format="multipart")
        v1 = DocumentVersion.objects.get(document_id=doc, number=1)
        restore = f"{DOCUMENTS_URL}{doc}/versions/{v1.pk}/restore/"
        self.assertEqual(client_for(self.colleague).post(restore).status_code, 403)
        response = client.post(restore)
        self.assertEqual(response.status_code, 201, response.data)
        current = response.data["current_version"]
        self.assertEqual((current["number"], current["notes"], current["name"]), (3, "Restaurada de la v1", "politica.pdf"))
        new = DocumentVersion.objects.get(document_id=doc, number=3)
        self.assertNotEqual(new.file.name, v1.file.name)                       # copia propia, no el mismo archivo
        with new.file.open("rb") as handle:
            self.assertEqual(handle.read(), PDF)
        self.assertIn("version", client.post(f"{DOCUMENTS_URL}{doc}/versions/{new.pk}/restore/").data)

    # --- Eliminar y permisos ------------------------------------------------------------------

    def test_delete_is_soft_and_only_for_managers(self):
        doc = self.create().data["id"]
        url = f"{DOCUMENTS_URL}{doc}/"
        self.assertEqual(client_for(self.colleague).delete(url).status_code, 403)
        self.assertEqual(client_for(self.author).delete(url).status_code, 204)
        self.assertEqual(client_for(self.author).get(url).status_code, 404)
        self.assertTrue(Document.objects.filter(pk=doc, deleted_at__isnull=False).exists())
        self.assertTrue(DocumentVersion.objects.filter(document_id=doc).exists())

    def test_me_and_categories(self):
        DocumentCategory.objects.create(name="Oculta", is_active=False)
        self.assertEqual(client_for(self.author).get("/api/documents/me/").data,
                         {"can_create": True, "manage_all": False})
        self.assertEqual(client_for(self.colleague).get("/api/documents/me/").data["can_create"], False)
        names = [c["name"] for c in client_for(self.colleague).get("/api/documents/categories/").data]
        self.assertEqual(names, ["Políticas"])
        self.assertEqual(APIClient().get(DOCUMENTS_URL).status_code, 403)
