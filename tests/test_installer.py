import importlib.util
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch, Mock

spec = importlib.util.spec_from_file_location('installer', Path(__file__).parents[1] / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_busy_port_is_skipped(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
            if port > 65430:
                self.skipTest('No room above ephemeral port')
            self.assertNotEqual(installer.free_port(port), port)

    def test_port_validation(self):
        for port in (0, 80, 65536):
            with self.assertRaises(ValueError):
                installer.free_port(port)

    def test_multiline_rejected(self):
        with self.assertRaises(ValueError):
            installer.quote('name\nSEED_DEMO=true')

    def test_existing_installation_does_not_prompt_or_rewrite_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            initial = 'APP_PORT=8088\nPOSTGRES_PASSWORD=existing\n'
            (root / '.env').write_text(initial)
            response = Mock()
            response.__enter__ = Mock(return_value=Mock(status=200))
            response.__exit__ = Mock(return_value=False)
            with patch.object(installer, 'ROOT', root), patch('sys.argv', ['install.py']), patch('builtins.input', side_effect=AssertionError('No prompts on rerun')), patch.object(installer.shutil, 'which', return_value='docker'), patch.object(installer, 'run'), patch.object(installer.subprocess, 'run', return_value=Mock(returncode=0)), patch('urllib.request.urlopen', return_value=response):
                installer.main()
            self.assertEqual((root / '.env').read_text(), initial)

    def test_fresh_install_retries_binding_race_and_generates_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            response = Mock()
            response.__enter__ = Mock(return_value=Mock(status=200))
            response.__exit__ = Mock(return_value=False)
            results = [Mock(returncode=1, stderr='address already in use'), Mock(returncode=0)]
            with patch.object(installer, 'ROOT', root), patch('sys.argv', ['install.py']), patch('builtins.input', side_effect=['Test site', 'zh', 'owner', '', 'example.test']), patch('getpass.getpass', return_value='A-unique-test-password!'), patch.object(installer.shutil, 'which', return_value='docker'), patch.object(installer, 'run'), patch.object(installer, 'free_port', side_effect=[8081, 8082]), patch.object(installer.subprocess, 'run', side_effect=results), patch('urllib.request.urlopen', return_value=response):
                installer.main()
            values = installer.read_env(root / '.env')
            self.assertEqual(values['APP_PORT'], '8082')
            self.assertIn('http://example.test:8082', values['DJANGO_CSRF_TRUSTED_ORIGINS'])
            self.assertEqual(values['SEED_DEMO'], 'false')
            self.assertEqual(values['SITE_LANGUAGE'], 'zh')
            self.assertEqual(len(values['POSTGRES_PASSWORD']), 48)
            self.assertNotIn('DB_PORT', values)
            self.assertNotIn('DATABASE_URL', values)


if __name__ == '__main__':
    unittest.main()
