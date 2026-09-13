import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Server
from .services import ConnectorError, _save_snapshot, local_snapshot, normalized_snapshot, refresh_server, trust_server_host


RAW = {'hostname': 'internal-node', 'os': 'Linux', 'cpu_percent': 23, 'memory_total_kb': 8388608, 'memory_used_kb': 2097152, 'disk_total_kb': 104857600, 'disk_used_kb': 10485760, 'gpus': [], 'containers': 2}


class ServerRegressionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user(username='monitor-test', password='test-only'))

    def test_refresh_does_not_replace_connection_address(self):
        server = Server.objects.create(name='Remote', hostname='public.example.org', provider='ssh')
        _save_snapshot(server, normalized_snapshot(RAW))
        server.refresh_from_db()
        self.assertEqual(server.hostname, 'public.example.org')
        self.assertEqual(server.metric_samples.first().payload['hostname'], 'internal-node')
        self.assertEqual(server.memory['total'], 8)

    def test_demo_refresh_does_not_fabricate_online_or_history(self):
        server = Server.objects.create(name='Demo', provider='mock', status='offline')
        refresh_server(server)
        server.refresh_from_db()
        self.assertEqual(server.status, 'offline')
        self.assertIsNone(server.last_seen)
        self.assertFalse(server.metric_samples.exists())

    def test_missing_capacity_is_a_failed_sample(self):
        with self.assertRaises(ConnectorError):
            normalized_snapshot({'cpu_percent': 0})

    def test_host_snapshot_scope_and_staleness(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'snapshot.json'
            source.write_text(json.dumps({'collectedAt': time.time(), 'values': RAW}))
            with patch.dict('os.environ', {'HOST_METRICS_FILE': str(source)}):
                self.assertEqual(local_snapshot()['scope'], 'deployment_host')
                source.write_text(json.dumps({'collectedAt': time.time() - 300, 'values': RAW}))
                with self.assertRaises(ConnectorError):
                    local_snapshot()

    def test_host_trust_is_bound_to_confirmed_fingerprint(self):
        server = Server.objects.create(name='SSH', provider='ssh')
        with patch('apps.servers.services._probe_host_key', return_value='SHA256:new'):
            self.assertFalse(trust_server_host(server, 'SHA256:old')[0])
            self.assertEqual(server.host_key_fingerprint, '')
            self.assertTrue(trust_server_host(server, 'SHA256:new')[0])

    def test_create_validate_encrypt_and_edit_connection(self):
        response = self.client.post('/api/v1/servers/', {'name': 'SSH', 'provider': 'ssh'}, format='json')
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/v1/servers/', {'name': 'SSH', 'provider': 'ssh', 'ip': '192.0.2.1', 'username': 'tester', 'password': 'test-only', 'port': 2222}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('password', response.data)
        server = Server.objects.get(pk=response.data['id'])
        self.assertNotEqual(server.encrypted_password, 'test-only')
        server.host_key_fingerprint = 'SHA256:old'
        server.save()
        encrypted = server.encrypted_password
        response = self.client.patch(f'/api/v1/servers/{server.pk}/', {'ip': '192.0.2.2'}, format='json')
        self.assertEqual(response.status_code, 200)
        server.refresh_from_db()
        self.assertEqual(server.encrypted_password, encrypted)
        self.assertEqual(server.host_key_fingerprint, '')

    def test_tcp_connection_has_timeout(self):
        from .services import _transport
        server = Server(name='SSH', hostname='host.example', port=2222)
        with patch('apps.servers.services.socket.create_connection', side_effect=TimeoutError) as connect:
            with self.assertRaises(TimeoutError):
                _transport(server)
            connect.assert_called_once_with(('host.example', 2222), timeout=10)

    def test_explicit_ip_wins_over_display_hostname(self):
        from .services import _host
        server = Server(name='Server', hostname='display-name', ip='192.0.2.15')
        self.assertEqual(_host(server), '192.0.2.15')

    def test_edit_provider_and_delete_remote_host(self):
        server = Server.objects.create(name='Editable', provider='mock')
        response = self.client.patch(f'/api/v1/servers/{server.pk}/', {'provider': 'ssh', 'ip': '192.0.2.15', 'username': 'tester', 'password': 'test-only'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['provider'], 'ssh')
        server.metric_samples.create(cpu_percent=10)
        self.assertEqual(self.client.delete(f'/api/v1/servers/{server.pk}/').status_code, 204)
        self.assertFalse(Server.objects.filter(pk=server.pk).exists())

    def test_hardware_and_precise_capacity_survive_sampling(self):
        server = Server.objects.create(name='Hardware', provider='ssh')
        snapshot = normalized_snapshot({**RAW, 'cpu_model': 'Test CPU', 'cpu_cores': '8', 'cpu_threads': '16', 'memory_speed': '3200 MT/s'})
        _save_snapshot(server, snapshot)
        from .serializers import ServerSerializer
        data = ServerSerializer(server).data
        self.assertEqual(data['hardware']['cpu_model'], 'Test CPU')
        self.assertEqual(data['hardware']['memory_speed'], '3200 MT/s')
        self.assertEqual(data['disk']['totalBytes'], 100 * 1024**3)
