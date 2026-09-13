import json
import os
from pathlib import Path
import tempfile
import time
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class DeploymentApiTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env = patch.dict(os.environ, {'DEPLOYMENT_CONTROL_DIR': self.directory.name})
        self.env.start(); self.addCleanup(self.env.stop)
        self.client = APIClient()
        self.owner = get_user_model().objects.create_superuser(username='owner', password='test-only')
        self.status = Path(self.directory.name) / 'status.json'
        self.status.write_text(json.dumps({'heartbeat': time.time(), 'current': {'appPort': 8080, 'databasePort': None}, 'job': None}))

    def test_only_superuser_can_control_deployment(self):
        self.assertIn(self.client.get('/api/v1/settings/deployment/').status_code, (401, 403))
        staff = get_user_model().objects.create_user(username='staff', is_staff=True)
        self.client.force_authenticate(staff)
        self.assertEqual(self.client.post('/api/v1/settings/deployment/', {'appPort': 8090, 'databasePort': None}, format='json').status_code, 403)

    def test_queue_is_atomic_and_does_not_overwrite_pending_request(self):
        self.client.force_authenticate(self.owner)
        payload = {'appPort': 8090, 'databasePort': None}
        first = self.client.post('/api/v1/settings/deployment/', payload, format='json')
        self.assertEqual(first.status_code, 202)
        original = (Path(self.directory.name) / 'request.json').read_text()
        second = self.client.post('/api/v1/settings/deployment/', payload, format='json')
        self.assertEqual(second.status_code, 409)
        self.assertEqual((Path(self.directory.name) / 'request.json').read_text(), original)

    def test_invalid_or_offline_requests_rejected(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post('/api/v1/settings/deployment/', {'appPort': 80, 'databasePort': None}, format='json').status_code, 400)
        self.status.write_text(json.dumps({'heartbeat': 0}))
        self.assertEqual(self.client.post('/api/v1/settings/deployment/', {'appPort': 8090, 'databasePort': None}, format='json').status_code, 503)
