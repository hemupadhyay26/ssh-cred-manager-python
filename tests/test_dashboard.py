"""Dashboard interaction and demo-session regression tests."""
import tempfile
import os
import io
import unittest
from contextlib import nullcontext, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from textual.widgets import DataTable, Input, Static
from cli.dashboard import SSHDashboard, CredentialForm, DeleteConfirmation
from core.credential_manager import CredentialManager
from core.models import SSHCredential
from utils.storage import StorageManager
from utils.crypto_utils import EncryptionManager
from ssh.connection import SSHConnection


class DashboardTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {"ENV": "development"})
        environment.start()
        self.addCleanup(environment.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.manager = CredentialManager.__new__(CredentialManager)
        self.manager.storage = StorageManager(Path(self.temp.name) / 'credentials.json')
        self.manager.crypto = EncryptionManager(Path(self.temp.name) / 'master.key')
        self.manager.add_credential('demo-web', '192.0.2.10', 'dev', tags=['demo'])
        self.manager.add_credential('demo-db', '198.51.100.30', 'db', tags=['demo'])

    async def test_search_edit_validation_and_delete_confirmation(self):
        app = SSHDashboard(self.manager, Mock())
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            self.assertEqual(app.query_one(DataTable).row_count, 2)
            await pilot.press('slash')
            app.query_one('#search', Input).value = 'demo-web'
            await pilot.pause()
            self.assertEqual(app.query_one(DataTable).row_count, 1)
            await pilot.press('enter', 'e')
            await pilot.pause()
            self.assertIsInstance(app.screen, CredentialForm)
            app.screen.query_one('#port', Input).value = '70000'
            app.screen.query_one('#save').focus()
            await pilot.press('enter')
            await pilot.pause()
            self.assertIsInstance(app.screen, CredentialForm)
            self.assertIn('65535', str(app.screen.query_one('#error', Static).content))
            app.screen.query_one('#port', Input).value = '2222'
            app.screen.query_one('#description', Input).value = 'Edited using dashboard'
            app.screen.query_one('#save').focus()
            await pilot.press('enter')
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(self.manager.get_credential('demo-web').port, 2222)
            await pilot.press('d')
            await pilot.pause()
            self.assertIsInstance(app.screen, DeleteConfirmation)
            await pilot.press('escape')
            await pilot.pause()
            self.assertIsNotNone(self.manager.get_credential('demo-web'))
            await pilot.press('d')
            await pilot.pause()
            await pilot.click('#delete')
            await pilot.pause()
            self.assertIsNone(self.manager.get_credential('demo-web'))
            self.assertEqual(app.query_one(DataTable).row_count, 0)
            await pilot.press('escape', 'a')
            await pilot.pause()
            form = app.screen
            form.query_one('#name', Input).value = 'new-server'
            form.query_one('#host', Input).value = '203.0.113.5'
            form.query_one('#user', Input).value = 'ops'
            form.query_one('#password', Input).value = 'test-only-password'
            form.query_one('#save').focus()
            await pilot.press('enter')
            await pilot.pause()
            self.assertEqual(self.manager.get_password('new-server'), 'test-only-password')
            self.assertNotIn('test-only-password', self.manager.storage.credentials_file.read_text())

    async def test_enter_connects_selected_row_and_returns(self):
        connect = Mock()
        app = SSHDashboard(self.manager, connect)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            with patch.object(app, 'suspend', return_value=nullcontext()) as suspend:
                await pilot.press('down', 'enter')
                await pilot.pause()
                connect.assert_called_once_with('demo-db')
                suspend.assert_called_once()
            self.assertEqual(app.query_one(DataTable).row_count, 2)


class DemoTests(unittest.TestCase):
    def test_demo_accepts_multiple_commands_without_starting_process(self):
        c = SSHCredential('demo', '192.0.2.10', 'dev', tags=['demo'])
        with patch.dict(os.environ, {'ENV': 'development'}), patch('builtins.input', side_effect=['whoami', 'scroll 50', 'echo demo', '', 'exit']) as prompt, patch('ssh.connection.subprocess.run') as process, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(SSHConnection().connect(c), 0)
            self.assertIn('00050 | demo', output.getvalue())
            self.assertEqual(prompt.call_count, 5)
            process.assert_not_called()

    def test_real_address_or_missing_tag_uses_ssh(self):
        for host, tags in [('192.0.2.10', []), ('10.0.0.1', ['demo'])]:
            with self.subTest(host=host, tags=tags), patch('ssh.connection.subprocess.run') as process:
                process.return_value.returncode = 0
                self.assertEqual(SSHConnection().connect(SSHCredential('server', host, 'ops', tags=tags)), 0)
                process.assert_called_once()


if __name__ == '__main__':
    unittest.main()
