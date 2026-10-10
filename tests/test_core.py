"""Core credential lifecycle, encryption, migration, and public CLI checks."""
import os
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from typer.testing import CliRunner
from core.credential_manager import CredentialManager
from utils.storage import StorageManager
from utils.crypto_utils import EncryptionManager
import main


class CoreFunctionalityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manager = CredentialManager.__new__(CredentialManager)
        self.manager.storage = StorageManager(self.root / 'credentials.json')
        self.manager.crypto = EncryptionManager(self.root / 'master.key')
        environment = patch.dict(os.environ, {'ENV': 'production'})
        environment.start()
        self.addCleanup(environment.stop)

    def test_credential_lifecycle_search_and_encrypted_password_round_trip(self):
        m = self.manager
        self.assertTrue(m.add_credential('server', 'host.example.com', 'ops', password='test-password', tags=['staging']))
        self.assertFalse(m.add_credential('server', 'other.example.com', 'other'))
        self.assertEqual(m.get_password('server'), 'test-password')
        self.assertNotIn('test-password', m.storage.credentials_file.read_text())
        # Reload from disk with the same master key, as in a new app session.
        reopened = CredentialManager.__new__(CredentialManager)
        reopened.storage = StorageManager(m.storage.credentials_file)
        reopened.crypto = EncryptionManager(self.root / 'master.key')
        self.assertEqual(reopened.get_password('server'), 'test-password')
        self.assertEqual([c.name for c in m.search_credentials('STAGING')], ['server'])
        self.assertTrue(m.update_credential('server', port=2222, description='Updated', tags=[]))
        self.assertEqual(m.get_credential('server').port, 2222)
        self.assertEqual(m.get_credential('server').tags, [])
        self.assertEqual(m.get_password('server'), 'test-password')
        m.update_last_used('server')
        self.assertIsNotNone(m.get_credential('server').last_used)
        self.assertTrue(m.delete_credential('server'))
        self.assertFalse(m.delete_credential('server'))
        self.assertIsNone(m.get_credential('server'))
        self.assertFalse(m.update_credential('missing', host='missing.example.com'))

    def test_export_merge_preserves_existing_entries_and_skips_duplicates(self):
        m = self.manager
        m.add_credential('existing', 'host.example.com', 'ops')
        export = self.root / 'export.json'
        m.storage.export_to_file(export)
        data = json.loads(export.read_text())
        data['credentials'][0]['host'] = 'must-not-overwrite.example.com'
        new = dict(data['credentials'][0], name='new', host='new.example.com')
        data['credentials'].extend([new, new])
        export.write_text(json.dumps(data))
        m.storage.import_from_file(export, merge=True)
        self.assertEqual([c.name for c in m.list_credentials()], ['existing', 'new'])
        self.assertEqual(m.get_credential('existing').host, 'host.example.com')
        if os.name == 'posix':
            self.assertEqual(stat.S_IMODE(m.storage.credentials_file.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(export.stat().st_mode), 0o600)

    def test_corrupt_import_does_not_overwrite_existing_storage(self):
        m = self.manager
        m.add_credential('existing', 'host.example.com', 'ops')
        before = m.storage.credentials_file.read_bytes()
        bad = self.root / 'bad.json'
        bad.write_text('{broken')
        with self.assertRaises(ValueError):
            m.storage.import_from_file(bad)
        self.assertEqual(m.storage.credentials_file.read_bytes(), before)
        m.storage.credentials_file.write_text('{broken')
        with self.assertRaisesRegex(ValueError, 'Invalid JSON'):
            m.list_credentials()

    def test_cli_add_list_show_remove_and_version(self):
        runner = CliRunner()
        with patch.object(main, 'manager', self.manager):
            result = runner.invoke(main.app, ['add', 'cli-server', '--host', 'host.example.com', '--user', 'ops', '--auth', 'agent', '--port', '22'])
            self.assertEqual(result.exit_code, 0, result.output)
            result = runner.invoke(main.app, ['list', '--search', 'cli-server'])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn('cli-server', result.output)
            self.assertEqual(runner.invoke(main.app, ['show', 'cli-server']).exit_code, 0)
            self.assertEqual(runner.invoke(main.app, ['remove', 'cli-server', '--force']).exit_code, 0)
            self.assertIsNone(self.manager.get_credential('cli-server'))
            result = runner.invoke(main.app, ['version'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn(main.VERSION, result.output)
            self.assertNotEqual(runner.invoke(main.app, ['show', 'missing']).exit_code, 0)
