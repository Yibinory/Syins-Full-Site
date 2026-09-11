from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.content.models import CurrentResearchItem, SiteProfile
from apps.documents.models import Document
from apps.papers.models import RecommendedPaper
from apps.publications.models import Publication
from apps.servers.models import Server


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"])
class ResearchOsApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="admin", email="admin@example.com", password="safe-test-password", is_staff=True)
        SiteProfile.objects.create(pk=1, name="Test Researcher")
        self.client = APIClient()

    def login(self):
        response = self.client.post("/api/v1/auth/login/", {"email": "admin@example.com", "password": "safe-test-password"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_public_content_and_public_records_are_readable_without_login(self):
        Publication.objects.create(slug="public-paper", title="Public paper", year=2026)
        Document.objects.create(slug="public-note", title="Public note", visibility="public", published_at=date(2026, 1, 1), content="# Note")
        Document.objects.create(slug="unlisted-note", title="Unlisted note", visibility="unlisted", content="# Hidden")
        self.assertEqual(self.client.get("/api/v1/auth/session/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/site/content/").status_code, 200)
        publications = self.client.get("/api/v1/publications/").json()
        self.assertEqual(publications["results"][0]["title"], "Public paper")
        documents = self.client.get("/api/v1/docs/?visibility=public").json()
        self.assertEqual(documents["results"][0]["slug"], "public-note")
        self.assertNotIn("unlisted-note", [item["slug"] for item in self.client.get("/api/v1/docs/").json()["results"]])
        self.assertEqual(self.client.get("/api/v1/docs/unlisted-note/").status_code, 200)

    def test_private_workspace_requires_session_and_supports_note_relations(self):
        self.assertEqual(self.client.get("/api/v1/papers/").status_code, 403)
        self.login()
        note = Document.objects.create(slug="linked-note", title="Linked note", visibility="private")
        response = self.client.post("/api/v1/papers/", {
            "title": "A recommended paper", "year": 2026, "recommendedAt": "2026-09-11", "noteIds": [note.id], "tags": ["MRI", "Domain Generalization"],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        paper = RecommendedPaper.objects.get(pk=response.json()["id"])
        self.assertEqual(list(paper.notes.values_list("id", flat=True)), [note.id])
        self.assertEqual(list(paper.tags.values_list("name", flat=True)), ["Domain Generalization", "MRI"])
        self.assertEqual(self.client.patch("/api/v1/papers/{}/".format(paper.id), {"status": "read", "noteIds": []}, format="json").status_code, 200)
        self.assertFalse(paper.notes.exists())

    def test_authenticated_trash_listing_is_separate_and_restorable(self):
        self.login()
        note = Document.objects.create(slug="trash-note", title="Trash note", visibility="private")
        response = self.client.post("/api/v1/docs/{}/trash/".format(note.slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/docs/").json()["count"], 0)
        trash = self.client.get("/api/v1/docs/?trash=1").json()
        self.assertEqual([item["slug"] for item in trash["results"]], ["trash-note"])
        response = self.client.post("/api/v1/docs/{}/restore/".format(note.slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/docs/").json()["results"][0]["slug"], "trash-note")

    def test_tag_rename_merges_relations(self):
        self.login()
        publication = Publication.objects.create(slug="tagged", title="Tagged", year=2026)
        publication.tags.create(name="old-tag")
        response = self.client.post("/api/v1/tags/rename/", {"from": "old-tag", "to": "new-tag"}, format="json")
        self.assertEqual(response.status_code, 200)
        publication.refresh_from_db()
        self.assertEqual(list(publication.tags.values_list("name", flat=True)), ["new-tag"])

    def test_site_content_update_and_media_upload(self):
        self.login()
        response = self.client.put("/api/v1/site/content/", {
            "name": "Updated researcher",
            "researchDirections": "MRI × Generation",
            "currentResearch": [{"id": 999999, "number": "01", "title": "New question", "text": "Summary", "status": "Active", "question": "What changes?", "method": "Compare cohorts", "updated": "Updated today"}],
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Updated researcher")
        self.assertEqual(CurrentResearchItem.objects.count(), 1)
        self.assertNotEqual(response.json()["currentResearch"][0]["id"], 999999)
        upload = SimpleUploadedFile("figure.svg", b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", content_type="image/svg+xml")
        media = self.client.post("/api/v1/media/", {"upload": upload}, format="multipart")
        self.assertEqual(media.status_code, 201)
        self.assertEqual(media.json()["kind"], "image")
        self.assertEqual(self.client.get("/api/v1/media/{}/".format(media.json()["id"])).status_code, 200)

    def test_server_refresh_is_explicit_and_safe(self):
        self.login()
        server = Server.objects.create(name="Mock server", provider="mock", status="online")
        response = self.client.post("/api/v1/servers/{}/actions/".format(server.id), {"action": "refresh_status"}, format="json")
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/v1/servers/{}/actions/".format(server.id), {"action": "run_shell", "command": "uname"}, format="json")
        self.assertEqual(response.status_code, 501)

    def test_authenticated_backup_contains_workspace_records(self):
        self.login()
        response = self.client.get("/api/v1/settings/backup/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn(b"research-os.json", response.content)
