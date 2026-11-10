"""Pruebas de la mesa de ayuda: agentes, visibilidad, flujo de estados, notas internas, adjuntos y avisos."""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import Permission, Role, RolePermission, User, UserRole
from apps.helpdesk.models import Ticket, TicketAttachment, TicketCategory, TicketEvent
from apps.notifications.models import Notification
from apps.accounts.models import Department

TICKETS_URL = "/api/helpdesk/tickets/"
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


def pdf(name="evidencia.pdf"):
    return SimpleUploadedFile(name, PDF, content_type="application/pdf")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@override_settings(MEDIA_ROOT=MEDIA_DIR)
class HelpdeskApiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_DIR, ignore_errors=True)

    def setUp(self):
        self.ti = Department.objects.create(name="Sistemas")
        self.cleaning = Department.objects.create(name="Áreas Públicas")
        self.head = make_user("jefa", department=self.ti)
        self.ti.head = self.head
        self.ti.save()
        self.agent = make_user("agente", department=self.ti)
        grant(self.agent, "helpdesk.tickets.attend")
        self.member = make_user("miembro", department=self.ti)                  # de TI, pero sin permiso
        self.cleaner = make_user("limpieza", department=self.cleaning)
        grant(self.cleaner, "helpdesk.tickets.attend")
        self.requester = make_user("pide")
        self.stranger = make_user("ajena")
        self.erp = TicketCategory.objects.create(name="Acceso a ERP", department=self.ti, kind="request")
        self.floor = TicketCategory.objects.create(name="Limpieza de piso", department=self.cleaning)

    def create(self, user=None, **data):
        payload = {"category": self.erp.pk, "title": "Sin acceso al ERP", "description": "No me deja entrar."}
        payload.update(data)
        return client_for(user or self.requester).post(TICKETS_URL, payload, format="multipart")

    def ticket_url(self, ticket_id, suffix=""):
        return f"{TICKETS_URL}{ticket_id}/{suffix}"

    # --- Crear y ver ----------------------------------------------------------------------------

    def test_create_routes_to_category_department_and_notifies_agents(self):
        response = self.create(files=[pdf()])
        self.assertEqual(response.status_code, 201, response.data)
        data = response.data
        self.assertEqual((data["department"]["name"], data["status"], data["priority"]), ("Sistemas", "open", "normal"))
        self.assertTrue(data["folio"].startswith("HD-"))
        self.assertEqual([a["name"] for a in data["attachments"]], ["evidencia.pdf"])
        self.assertEqual(data["events"][0]["kind"], "created")
        notified = set(Notification.objects.values_list("recipient__username", flat=True))
        self.assertEqual(notified, {"jefa", "agente"})                         # ni el miembro sin permiso ni quien pide

    def test_create_validates_category_text_and_files(self):
        self.assertEqual(self.create(category=999).status_code, 400)
        self.erp.is_active = False
        self.erp.save()
        self.assertEqual(self.create().status_code, 400)
        self.assertEqual(self.create(category=self.floor.pk, title="  ").status_code, 400)
        bad = SimpleUploadedFile("virus.pdf", b"MZ\x90\x00" + b"\x00" * 50)
        response = self.create(category=self.floor.pk, files=[bad])
        self.assertEqual(response.status_code, 400)
        self.assertIn("virus.pdf", str(response.data["files"]))
        self.assertEqual(self.create(category=self.floor.pk, files=[pdf(f"{i}.pdf") for i in range(6)]).status_code, 400)
        self.assertFalse(Ticket.objects.exists())

    def test_visibility(self):
        ticket_id = self.create().data["id"]
        for user, visible in ((self.requester, True), (self.agent, True), (self.head, True), (self.member, False),
                              (self.cleaner, False), (self.stranger, False)):
            with self.subTest(user.username):
                status = client_for(user).get(self.ticket_url(ticket_id)).status_code
                self.assertEqual(status, 200 if visible else 404)
        auditor = make_user("auditora")
        grant(auditor, "helpdesk.tickets.view.all")
        self.assertEqual(client_for(auditor).get(self.ticket_url(ticket_id)).status_code, 200)
        self.assertEqual(client_for(auditor).patch(self.ticket_url(ticket_id), {"priority": "high"}).status_code, 403)

    def test_list_scopes_and_filters(self):
        mine = self.create().data["id"]
        other = self.create(user=self.stranger, title="Impresora").data["id"]
        floor = self.create(category=self.floor.pk, title="Piso mojado").data["id"]
        ids = lambda user, **params: [t["id"] for t in client_for(user).get(TICKETS_URL, params).data["results"]]
        self.assertEqual(ids(self.requester), [floor, mine])
        self.assertEqual(ids(self.agent), [other, mine])
        self.assertEqual(ids(self.agent, scope="mine"), [])
        self.assertEqual(ids(self.agent, q="impresora"), [other])
        self.assertEqual(ids(self.agent, q=f"HD-{mine:05d}"), [mine])
        self.assertEqual(ids(self.agent, unassigned="1", status="open,in_progress"), [other, mine])
        self.assertEqual(client_for(self.agent).get(TICKETS_URL, {"status": "nope"}).status_code, 400)
        self.assertEqual(client_for(self.agent).get(TICKETS_URL, {"scope": "all"}).status_code, 400)

    # --- Atender --------------------------------------------------------------------------------

    def test_agent_flow_assign_progress_resolve_and_requester_closes(self):
        ticket_id = self.create().data["id"]
        agent = client_for(self.agent)
        data = agent.patch(self.ticket_url(ticket_id), {"status": "in_progress", "priority": "high"}).data
        self.assertEqual((data["status"], data["priority"], data["assignee"]["id"]), ("in_progress", "high", self.agent.pk))
        self.assertTrue(data["permissions"]["attend"])
        data = agent.patch(self.ticket_url(ticket_id), {"status": "resolved"}).data
        self.assertIsNotNone(data["resolved_at"])
        self.assertTrue(Notification.objects.filter(recipient=self.requester, color="success").exists())

        requester = client_for(self.requester)
        self.assertTrue(requester.get(self.ticket_url(ticket_id)).data["permissions"]["reopen"])
        data = requester.patch(self.ticket_url(ticket_id), {"status": "open"}).data      # reabre
        self.assertEqual((data["status"], data["resolved_at"]), ("open", None))
        data = requester.patch(self.ticket_url(ticket_id), {"status": "closed"}).data
        self.assertIsNotNone(data["closed_at"])
        kinds = [(e["kind"], e["new_label"]) for e in data["events"]]
        self.assertIn(("status", "Cerrado"), kinds)
        # Cerrado es final.
        self.assertEqual(agent.patch(self.ticket_url(ticket_id), {"status": "open"}).status_code, 400)
        self.assertEqual(requester.post(self.ticket_url(ticket_id, "comments/"), {"body": "hola"}).status_code, 400)

    def test_requester_limits(self):
        ticket_id = self.create().data["id"]
        requester = client_for(self.requester)
        self.assertEqual(requester.patch(self.ticket_url(ticket_id), {"priority": "urgent"}).status_code, 403)
        self.assertEqual(requester.patch(self.ticket_url(ticket_id), {"status": "resolved"}).status_code, 403)
        self.assertEqual(requester.patch(self.ticket_url(ticket_id), {"status": "in_progress"}).status_code, 403)
        client_for(self.agent).patch(self.ticket_url(ticket_id), {"status": "waiting"})
        self.assertEqual(requester.patch(self.ticket_url(ticket_id), {"status": "open"}).status_code, 400)  # no resuelto

    def test_assign_only_to_department_agents(self):
        ticket_id = self.create().data["id"]
        agent = client_for(self.agent)
        # Sin «assign» solo puede tomarlo para sí; dárselo a otra persona → 403.
        self.assertEqual(agent.patch(self.ticket_url(ticket_id), {"assignee": self.head.pk}, format="json").status_code, 403)
        self.assertEqual(agent.patch(self.ticket_url(ticket_id), {"assignee": self.agent.pk}, format="json").data["assignee"]["id"], self.agent.pk)
        grant(self.agent, "helpdesk.tickets.assign")
        self.agent.refresh_from_db()
        self.agent.__dict__.pop("_ws_perm_cache", None)   # los permisos se guardan en la instancia
        agent = client_for(self.agent)
        self.assertEqual(agent.patch(self.ticket_url(ticket_id), {"assignee": self.member.pk}).status_code, 400)
        self.assertEqual(agent.patch(self.ticket_url(ticket_id), {"assignee": self.cleaner.pk}).status_code, 400)
        data = agent.patch(self.ticket_url(ticket_id), {"assignee": self.head.pk}, format="json").data
        self.assertEqual(data["assignee"]["id"], self.head.pk)
        self.assertTrue(Notification.objects.filter(recipient=self.head, title__startswith="Te asignaron").exists())
        data = agent.patch(self.ticket_url(ticket_id), {"assignee": None}, format="json").data
        self.assertIsNone(data["assignee"])
        candidates = {p["id"] for p in agent.get(self.ticket_url(ticket_id, "agents/")).data}
        self.assertEqual(candidates, {self.head.pk, self.agent.pk})
        self.assertEqual(client_for(self.requester).get(self.ticket_url(ticket_id, "agents/")).status_code, 403)

    def test_transfer_to_another_department(self):
        ticket_id = self.create(title="En realidad es limpieza").data["id"]
        agent = client_for(self.agent)
        agent.patch(self.ticket_url(ticket_id), {"status": "in_progress"})
        data = agent.patch(self.ticket_url(ticket_id), {"category": self.floor.pk}).data
        self.assertEqual((data["department"]["name"], data["assignee"], data["visible"]), ("Áreas Públicas", None, False))
        self.assertTrue(Notification.objects.filter(recipient=self.cleaner, title__contains="transferido").exists())
        self.assertEqual(agent.get(self.ticket_url(ticket_id)).status_code, 404)        # ya no es de su departamento
        self.assertEqual(client_for(self.cleaner).get(self.ticket_url(ticket_id)).status_code, 200)

    # --- «Otro»: no está en la lista -----------------------------------------------------------

    def create_other(self, **data):
        payload = {"title": "Algo raro con la impresora del piso 3", "description": "No sé de quién es."}
        payload.update(data)
        return client_for(self.requester).post(TICKETS_URL, payload, format="multipart")

    def test_other_ticket_has_no_department_and_notifies_every_agent(self):
        for response in (self.create_other(), self.create_other(category="")):
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual((response.data["category"], response.data["department"]), (None, None))
        self.assertEqual(TicketEvent.objects.filter(kind="created").first().new_value, "Otro")
        notified = set(Notification.objects.filter(title__contains="sin clasificar").values_list("recipient__username", flat=True))
        self.assertEqual(notified, {"jefa", "agente", "limpieza"})   # agentes de todos los departamentos, nadie más

    def test_other_ticket_is_visible_to_any_agent_only(self):
        ticket_id = self.create_other().data["id"]
        for user, code in ((self.agent, 200), (self.cleaner, 200), (self.head, 200), (self.requester, 200),
                           (self.member, 404), (self.stranger, 404)):
            self.assertEqual(client_for(user).get(self.ticket_url(ticket_id)).status_code, code, user.username)
        queue = client_for(self.cleaner).get(TICKETS_URL, {"scope": "queue"}).data["results"]
        self.assertEqual([t["id"] for t in queue], [ticket_id])
        unclassified = client_for(self.agent).get(TICKETS_URL, {"unclassified": "1"}).data["results"]
        self.assertEqual([t["id"] for t in unclassified], [ticket_id])
        self.assertTrue(client_for(self.cleaner).get(self.ticket_url(ticket_id)).data["permissions"]["attend"])
        agents = {a["name"] for a in client_for(self.agent).get(self.ticket_url(ticket_id, "agents/")).data}
        self.assertEqual(agents, {"Jefa", "Agente", "Limpieza"})

    def test_classifying_other_ticket_moves_it_to_that_department(self):
        ticket_id = self.create_other().data["id"]
        data = client_for(self.agent).patch(self.ticket_url(ticket_id), {"category": self.floor.pk}).data
        self.assertEqual((data["category"]["name"], data["department"]["name"], data["visible"]),
                         ("Limpieza de piso", "Áreas Públicas", False))
        event = TicketEvent.objects.get(kind="category")
        self.assertEqual((event.old_value, event.new_value), ("Otro", "Limpieza de piso"))
        self.assertTrue(Notification.objects.filter(recipient=self.cleaner, title__contains="clasificado para").exists())
        self.assertEqual(client_for(self.agent).get(self.ticket_url(ticket_id)).status_code, 404)
        self.assertEqual(client_for(self.cleaner).get(self.ticket_url(ticket_id)).status_code, 200)

    def test_requester_cannot_classify_other_ticket(self):
        ticket_id = self.create_other().data["id"]
        response = client_for(self.requester).patch(self.ticket_url(ticket_id), {"category": self.erp.pk})
        self.assertEqual(response.status_code, 403)

    # --- Conversación ---------------------------------------------------------------------------

    def test_comments_internal_notes_and_first_response(self):
        ticket_id = self.create().data["id"]
        agent = client_for(self.agent)
        requester = client_for(self.requester)
        response = agent.post(self.ticket_url(ticket_id, "comments/"), {"body": "Revisar con proveedor", "is_internal": True,
                                                                       "files": [pdf("interno.pdf")]})
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["first_response_at"])                           # una nota interna no cuenta
        data = agent.post(self.ticket_url(ticket_id, "comments/"), {"body": "¿Qué usuario usas?"}).data
        self.assertIsNotNone(data["first_response_at"])

        seen_by_requester = requester.get(self.ticket_url(ticket_id)).data["comments"]
        self.assertEqual([c["body"] for c in seen_by_requester], ["¿Qué usuario usas?"])
        self.assertEqual(len(agent.get(self.ticket_url(ticket_id)).data["comments"]), 2)
        self.assertEqual(
            requester.post(self.ticket_url(ticket_id, "comments/"), {"body": "x", "is_internal": True}).status_code, 403,
        )
        self.assertEqual(client_for(self.stranger).post(self.ticket_url(ticket_id, "comments/"), {"body": "x"}).status_code, 404)
        self.assertEqual(requester.post(self.ticket_url(ticket_id, "comments/"), {"body": "  "}).status_code, 400)

        internal_file = TicketAttachment.objects.get(original_name="interno.pdf")
        url = f"/api/helpdesk/attachments/{internal_file.pk}/file/"
        self.assertEqual(requester.get(url).status_code, 404)
        response = agent.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_requester_reply_moves_waiting_to_in_progress(self):
        ticket_id = self.create().data["id"]
        client_for(self.agent).patch(self.ticket_url(ticket_id), {"status": "waiting"})
        data = client_for(self.requester).post(self.ticket_url(ticket_id, "comments/"), {"body": "Mi usuario es pide"}).data
        self.assertEqual(data["status"], "in_progress")
        self.assertTrue(TicketEvent.objects.filter(ticket_id=ticket_id, kind="status", new_value="in_progress").exists())

    def test_attachment_download_follows_ticket_visibility(self):
        ticket_id = self.create(files=[pdf()]).data["id"]
        attachment = TicketAttachment.objects.get(ticket_id=ticket_id)
        self.assertTrue(attachment.file.name.endswith(f"{attachment.pk}.pdf"))
        url = f"/api/helpdesk/attachments/{attachment.pk}/file/"
        self.assertEqual(client_for(self.requester).get(url).status_code, 200)
        self.assertEqual(client_for(self.stranger).get(url).status_code, 404)
        self.assertEqual(APIClient().get(url).status_code, 401)

    # --- Catálogo y «qué puedo hacer» -----------------------------------------------------------

    def test_categories_and_me(self):
        names = {c["name"] for c in client_for(self.requester).get("/api/helpdesk/categories/").data}
        self.assertEqual(names, {"Acceso a ERP", "Limpieza de piso"})
        only_ti = client_for(self.requester).get("/api/helpdesk/categories/", {"department": self.ti.pk}).data
        self.assertEqual([c["name"] for c in only_ti], ["Acceso a ERP"])
        self.assertEqual(client_for(self.agent).get("/api/helpdesk/me/").data["attends"], [{"id": self.ti.pk, "name": "Sistemas"}])
        self.assertEqual(client_for(self.member).get("/api/helpdesk/me/").data["attends"], [])
        admin = User.objects.create_superuser("root", "root@example.test", "x-Pass-12345")
        self.assertTrue(client_for(admin).get("/api/helpdesk/me/").data["all_departments"])

    def test_requires_session(self):
        for url in (TICKETS_URL, "/api/helpdesk/categories/", "/api/helpdesk/me/"):
            self.assertEqual(APIClient().get(url).status_code, 401)
