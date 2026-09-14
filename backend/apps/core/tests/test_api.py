from datetime import date, timedelta
from io import BytesIO
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.content.models import CurrentResearchItem, SiteProfile
from apps.documents.models import Document
from apps.papers.models import RecommendedPaper
from apps.publications.models import Publication
from apps.servers.models import Server, ServerMetricSample


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

    def test_shared_portrait_persists_and_protects_media(self):
        self.login()
        upload = SimpleUploadedFile("portrait.svg", b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", content_type="image/svg+xml")
        media = self.client.post("/api/v1/media/", {"upload": upload}, format="multipart").json()
        response = self.client.patch("/api/v1/site/content/", {"portraitAssetId": media["id"], "translations": {"zh": {"name": "研究者"}}}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["portraitAssetId"], media["id"])
        self.client.logout()
        self.assertTrue(self.client.get("/api/v1/site/content/").json()["portraitUrl"].endswith("portrait.svg"))
        self.login()
        self.assertEqual(self.client.delete(f"/api/v1/media/{media['id']}/").status_code, 409)
        self.assertEqual(self.client.patch("/api/v1/site/content/", {"portraitAssetId": None}, format="json").json()["portraitUrl"], "")
        self.assertEqual(self.client.delete(f"/api/v1/media/{media['id']}/").status_code, 204)

    def test_server_refresh_is_explicit_and_safe(self):
        self.login()
        server = Server.objects.create(name="Mock server", provider="mock", status="online")
        response = self.client.post("/api/v1/servers/{}/actions/".format(server.id), {"action": "refresh_status"}, format="json")
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/v1/servers/{}/actions/".format(server.id), {"action": "run_shell", "command": "uname"}, format="json")
        self.assertEqual(response.status_code, 501)
        self.assertEqual(ServerMetricSample.objects.filter(server=server).count(), 0)
        history = self.client.get("/api/v1/servers/{}/metrics/".format(server.id)).json()
        self.assertEqual(history["count"], 0)

    def test_server_metrics_limit_keeps_latest_samples_in_time_order(self):
        self.login()
        server = Server.objects.create(name="History server", provider="mock")
        start = timezone.now() - timedelta(minutes=3)
        for index in range(3):
            ServerMetricSample.objects.create(
                server=server,
                recorded_at=start + timedelta(minutes=index),
                cpu_percent=index,
            )
        response = self.client.get("/api/v1/servers/{}/metrics/?limit=2".format(server.id))
        self.assertEqual([sample["cpu"] for sample in response.json()["results"]], [1, 2])

    def test_markdown_upload_and_public_paper_note_access(self):
        self.login()
        upload = SimpleUploadedFile("longitudinal-note.md", b"# Uploaded Note\n\n**A useful finding.**", content_type="text/markdown")
        response = self.client.post("/api/v1/docs/upload/", {"file": upload, "visibility": "private"}, format="multipart")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["title"], "Uploaded Note")
        note = Document.objects.get(pk=response.json()["id"])
        paper = RecommendedPaper.objects.create(title="Public paper memory", year=2026, recommended_at=date(2026, 9, 12), publicly_visible=True)
        paper.notes.add(note)
        self.client.post("/api/v1/auth/logout/", format="json")
        public = self.client.get("/api/v1/public/papers/{}/".format(paper.id))
        self.assertEqual(public.status_code, 200)
        self.assertTrue(public.json()["notes"][0]["requiresAuth"])
        self.assertNotIn("content", public.json()["notes"][0])
        self.login()
        private_public = self.client.get("/api/v1/public/papers/{}/".format(paper.id)).json()
        self.assertNotIn("content", private_public["notes"][0])
        self.assertIn("A useful finding", self.client.get("/api/v1/docs/{}/".format(note.slug)).json()["content"])

    def test_recommended_paper_duplicate_check_returns_conflict(self):
        self.login()
        payload = {"title": "One unique paper", "year": 2026, "recommendedAt": "2026-09-12", "doi": "10.1000/ABC"}
        self.assertEqual(self.client.post("/api/v1/papers/", payload, format="json").status_code, 201)
        duplicate = self.client.post("/api/v1/papers/", {**payload, "doi": "https://doi.org/10.1000/abc"}, format="json")
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.json()["code"], "duplicate_paper")

    def test_public_paper_list_is_paginated_and_orderable(self):
        for index, month in enumerate((1, 2, 3), start=1):
            RecommendedPaper.objects.create(
                title="Ordered paper {}".format(index),
                year=2026,
                recommended_at=date(2026, month, 1),
                publicly_visible=True,
            )
        response = self.client.get("/api/v1/public/papers/?page_size=1&ordering=recommended_at")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 3)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["title"], "Ordered paper 1")

    def test_tag_metadata_and_hierarchy_are_editable(self):
        self.login()
        parent = self.client.post("/api/v1/tags/", {"name": "Imaging", "color": "#204060", "description": "Image methods"}, format="json")
        self.assertEqual(parent.status_code, 201)
        child = self.client.post("/api/v1/tags/", {"name": "MRI", "parentId": parent.json()["id"]}, format="json")
        self.assertEqual(child.status_code, 201)
        updated = self.client.patch("/api/v1/tags/{}/".format(child.json()["id"]), {"color": "#AABBCC", "description": "MR imaging", "parentId": parent.json()["id"]}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["parentId"], parent.json()["id"])
        self.assertEqual(updated.json()["color"], "#AABBCC")

    def test_dashboard_embedded_page_accepts_http_urls_only(self):
        self.login()
        created = self.client.post("/api/v1/integrations/pages/", {"title": "3x-ui", "url": "https://panel.example.com/", "description": "Panel"}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.get("/api/v1/integrations/pages/").json()["results"][0]["title"], "3x-ui")
        duplicate_title = self.client.post("/api/v1/integrations/pages/", {"title": "3x-ui", "url": "https://another.example.com/"}, format="json")
        self.assertEqual(duplicate_title.status_code, 201)
        self.assertNotEqual(duplicate_title.json()["slug"], created.json()["slug"])
        rejected = self.client.post("/api/v1/integrations/pages/", {"title": "Local", "url": "javascript:alert(1)"}, format="json")
        self.assertEqual(rejected.status_code, 400)

    def test_authenticated_backup_contains_workspace_records(self):
        self.login()
        tag = self.client.post("/api/v1/tags/", {"name": "Backup tag", "color": "#123456"}, format="json")
        self.assertEqual(tag.status_code, 201)
        integration = self.client.post("/api/v1/integrations/pages/", {"title": "Backup page", "url": "https://example.com/"}, format="json")
        self.assertEqual(integration.status_code, 201)
        response = self.client.get("/api/v1/settings/backup/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        with ZipFile(BytesIO(response.content)) as archive:
            self.assertIn("research-os.json", archive.namelist())
            backup_json = archive.read("research-os.json").decode("utf-8")
        self.assertIn("Backup tag", backup_json)
        self.assertIn("Backup page", backup_json)

    def test_overview_excludes_mock_and_counts_database_records(self):
        self.assertEqual(self.client.get('/api/v1/overview/').status_code, 403)
        self.login()
        Server.objects.all().delete()
        Server.objects.create(name='Demo', provider='mock', status='online', gpus=[{}, {}, {}])
        Server.objects.create(name='Real', provider='ssh', status='online', gpus=[{}])
        Server.objects.create(name='Failed', provider='ssh', status='warning')
        response = self.client.get('/api/v1/overview/').json()
        self.assertEqual(response['servers'], {'total': 2, 'online': 1, 'gpus': 1})

    def test_external_pages_public_visibility_is_explicit_and_read_only(self):
        self.login()
        private = self.client.post('/api/v1/integrations/pages/', {'title': 'Private panel', 'url': 'https://private.example.com/'}, format='json').json()
        public = self.client.post('/api/v1/integrations/pages/', {'title': 'Shared tool', 'url': 'https://tools.example.com/', 'publiclyVisible': True}, format='json').json()
        self.client.logout()
        self.assertEqual(self.client.get('/api/v1/public/pages/').json()['count'], 1)
        self.assertEqual(self.client.get('/api/v1/public/pages/{}/'.format(private['slug'])).status_code, 404)
        self.assertEqual(self.client.get('/api/v1/public/pages/{}/'.format(public['slug'])).status_code, 200)
        self.assertIn(self.client.post('/api/v1/public/pages/', {'title': 'No write'}, format='json').status_code, [403, 405])
        self.login()
        self.client.patch('/api/v1/integrations/pages/{}/'.format(public['slug']), {'publiclyVisible': False}, format='json')
        self.client.logout()
        self.assertEqual(self.client.get('/api/v1/public/pages/').json()['count'], 0)
