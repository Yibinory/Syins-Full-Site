import os
from unittest.mock import patch
from django.test import TestCase
from django.core.management import call_command, CommandError
from django.contrib.auth import get_user_model
from apps.content.models import SiteProfile, ResearchProject
from apps.papers.models import RecommendedPaper
from apps.publications.models import Publication
from apps.documents.models import Document


class BootstrapTests(TestCase):
    @patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': 'A-unique-test-secret-582!', 'DJANGO_SUPERUSER_USERNAME': 'owner', 'SITE_NAME': 'My lab'})
    def test_clean_and_idempotent(self):
        call_command('bootstrap')
        user = get_user_model().objects.get(username='owner')
        self.assertTrue(user.check_password('A-unique-test-secret-582!'))
        self.assertTrue(user.is_superuser)
        self.assertEqual(SiteProfile.get_solo().name, 'My lab')
        for model in (ResearchProject, RecommendedPaper, Publication, Document):
            self.assertEqual(model.objects.count(), 0)
        SiteProfile.objects.update(name='Edited name')
        with patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': 'different-secret-582!', 'DJANGO_SUPERUSER_USERNAME': 'another'}):
            call_command('bootstrap')
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(SiteProfile.get_solo().name, 'Edited name')
        user.refresh_from_db()
        self.assertTrue(user.check_password('A-unique-test-secret-582!'))

    @patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': 'replace-with-an-admin-password'})
    def test_placeholder_rejected_without_partial_data(self):
        with self.assertRaises(CommandError):
            call_command('bootstrap')
        self.assertFalse(get_user_model().objects.exists())
        self.assertFalse(SiteProfile.objects.exists())

    def test_existing_non_admin_is_not_promoted(self):
        user = get_user_model().objects.create_user(username='existing')
        call_command('bootstrap')
        user.refresh_from_db()
        self.assertFalse(user.is_superuser)
