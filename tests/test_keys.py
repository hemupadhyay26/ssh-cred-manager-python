import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core.keys import list_keys, SSHKey
from core.credential_manager import CredentialManager
from utils.storage import StorageManager
from cli.dashboard import SSHDashboard, KeysScreen, CredentialForm
from textual.widgets import DataTable, Input


class KeyTests(unittest.TestCase):
    def test_discovery_filters_non_keys_and_keeps_duplicate_names_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a, b = root / 'managed', root / 'ssh'
            a.mkdir(); b.mkdir()
            for base in (a, b):
                (base / 'id_ed25519').write_text('-----BEGIN OPENSSH PRIVATE KEY-----\nFAKE TEST FIXTURE\n')
                (base / 'id_ed25519.pub').write_text('ssh-ed25519 public-fixture')
                (base / 'config').write_text('Host server\n')
                (base / 'known_hosts').write_text('host ssh-rsa fixture')
            keys = list_keys([(a, 'Managed'), (b, 'SSH')])
            self.assertEqual(len(keys), 2)
            self.assertNotEqual(keys[0].path, keys[1].path)
            self.assertEqual({key.location for key in keys}, {'Managed', 'SSH'})


class KeyUITests(unittest.IsolatedAsyncioTestCase):
    async def test_keyboard_default_and_form_picker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = CredentialManager.__new__(CredentialManager)
            manager.storage = StorageManager(root / 'credentials.json')
            catalog = []
            for name in ('first-key', 'second-key'):
                path = root / name
                path.write_text('-----BEGIN OPENSSH PRIVATE KEY-----\nFAKE TEST FIXTURE\n')
                catalog.append(SSHKey(name, path, 'Managed'))
            app = SSHDashboard(manager, lambda name: None)
            with patch('core.keys.list_keys', return_value=catalog):
                async with app.run_test(size=(100, 40)) as pilot:
                    await pilot.pause()
                    await pilot.press('k')
                    await pilot.pause()
                    self.assertIsInstance(app.screen, KeysScreen)
                    self.assertEqual(app.screen.query_one('#keys-table', DataTable).row_count, 2)
                    await pilot.press('down', 'enter')
                    await pilot.pause()
                    self.assertEqual(manager.get_default_key(), str(catalog[1].path))
                    await pilot.press('a')
                    await pilot.pause()
                    self.assertIsInstance(app.screen, CredentialForm)
                    app.screen.query_one('#browse-keys').focus()
                    await pilot.press('enter')
                    await pilot.pause()
                    self.assertIsInstance(app.screen, KeysScreen)
                    app.screen.query_one('#keys-search', Input).value = 'first'
                    await pilot.pause()
                    self.assertEqual(app.screen.query_one('#keys-table', DataTable).row_count, 1)
                    await pilot.press('enter')
                    await pilot.pause()
                    self.assertIsInstance(app.screen, CredentialForm)
                    self.assertEqual(app.screen.query_one('#key', Input).value, str(catalog[0].path))
                    await pilot.press('escape')
                    await pilot.pause()
                    self.assertEqual(manager.list_credentials(), [])
