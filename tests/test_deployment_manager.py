import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from deployment_manager import Manager, validate_ports, replace_env, update_origins


class DeploymentTests(unittest.TestCase):
    def test_port_validation_and_origins(self):
        for ports in ({'appPort': True, 'databasePort': None}, {'appPort': 8080, 'databasePort': 8080}, {'appPort': 80, 'databasePort': None}):
            with self.assertRaises(ValueError):
                validate_ports(ports)
        self.assertEqual(update_origins('http://localhost:8080,https://example.org', 8080, 8090), 'http://localhost:8090,https://example.org')
        self.assertEqual(replace_env('SECRET="$unchanged"\nAPP_PORT=8080\n', {'APP_PORT': 8090}), 'SECRET="$unchanged"\nAPP_PORT=\'8090\'\n')

    def test_failed_apply_restores_files_and_old_ports(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = "SECRET='existing'\nAPP_PORT=8080\n"
            (root / '.env').write_text(original)
            manager = Manager(root)
            manager.overlay.write_text('original overlay')
            calls = []
            def compose(*args):
                calls.append(args)
                if args == ('config', '--quiet'):
                    raise RuntimeError('Bad new configuration')
                return ''
            def prepare(*args):
                manager.env.write_text('changed')
                manager.overlay.write_text('changed')
            with patch.object(manager, 'configured_ports', return_value={'appPort': 8080, 'databasePort': None}), patch.object(manager, 'available'), patch.object(manager, 'prepare', side_effect=prepare), patch.object(manager, 'compose', side_effect=compose), patch.object(manager, 'ready') as ready:
                manager.apply({'id': '12345678-1234-1234-1234-123456789abc', 'ports': {'appPort': 8090, 'databasePort': 5432}})
            self.assertEqual(manager.env.read_text(), original)
            self.assertEqual(manager.overlay.read_text(), 'original overlay')
            self.assertEqual(manager.state['job']['status'], 'rolled_back')
            ready.assert_called_once_with(8080)
            self.assertFalse(manager.journal.exists())

    def test_busy_port_does_not_modify_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = Manager(Path(folder))
            manager.env.write_text('unchanged')
            with patch.object(manager, 'configured_ports', return_value={'appPort': 8080, 'databasePort': None}), patch.object(manager, 'available', side_effect=ValueError('Port 8090 is already in use.')):
                manager.apply({'id': '12345678-1234-1234-1234-123456789abc', 'ports': {'appPort': 8090, 'databasePort': None}})
            self.assertEqual(manager.env.read_text(), 'unchanged')
            self.assertEqual(manager.state['job']['status'], 'failed')
            self.assertFalse(manager.journal.exists())

    def test_crash_journal_restored_before_new_work(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = Manager(Path(folder))
            manager.env.write_text('new')
            manager.journal.write_text(json.dumps({'id': 'recovery', 'snapshot': {'env': 'old', 'overlay': None}, 'previous': {'appPort': 8080, 'databasePort': None}}))
            with patch.object(manager, 'compose'), patch.object(manager, 'ready'):
                manager.recover()
            self.assertEqual(manager.env.read_text(), 'old')
            self.assertFalse(manager.journal.exists())
            self.assertEqual(manager.state['job']['status'], 'rolled_back')


if __name__ == '__main__':
    unittest.main()
