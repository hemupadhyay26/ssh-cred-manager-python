import io
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from core.environment import is_development
from cli.demo_data import seed_demo
from core.credential_manager import CredentialManager
from core.models import SSHCredential
from utils.storage import StorageManager
from ssh.connection import SSHConnection


class DevelopmentGateTests(unittest.TestCase):
    def test_dotenv_opt_in_and_environment_override(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            with patch('core.environment.DOTENV_PATH', path), patch.dict(os.environ, {}, clear=True):
                self.assertFalse(is_development())
                path.write_text('ENV=development\n')
                self.assertTrue(is_development())
                os.environ['ENV'] = 'production'
                self.assertFalse(is_development())

    def test_seed_and_direct_demo_are_blocked_outside_development(self):
        for mode in ('', 'production', 'test', 'Development'):
            with self.subTest(mode=mode), patch.dict(os.environ, {'ENV': mode}):
                manager = Mock()
                with self.assertRaises(RuntimeError):
                    seed_demo(manager)
                manager.add_credential.assert_not_called()
                with patch('ssh.connection.subprocess.run') as process, patch('builtins.input') as prompt, redirect_stdout(io.StringIO()):
                    self.assertEqual(SSHConnection().connect(SSHCredential('demo', '192.0.2.10', 'dev', tags=['demo'])), 1)
                    process.assert_not_called()
                    prompt.assert_not_called()

    def test_demo_visibility_and_seed_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = CredentialManager.__new__(CredentialManager)
            manager.storage = StorageManager(Path(directory) / 'credentials.json')
            manager.add_credential('real', '10.0.0.1', 'ops')
            with patch.dict(os.environ, {'ENV': 'development'}):
                self.assertEqual(seed_demo(manager), 5)
                self.assertEqual(seed_demo(manager), 0)
                self.assertEqual(len(manager.list_credentials()), 6)
            with patch.dict(os.environ, {'ENV': 'production'}):
                self.assertEqual([c.name for c in manager.list_credentials()], ['real'])
                self.assertIsNone(manager.get_credential('demo-web-dev'))
                self.assertEqual(len(manager.storage.load().credentials), 6)
