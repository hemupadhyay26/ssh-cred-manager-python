import json
import tempfile
import unittest
from pathlib import Path
from core.preferences import Preferences
from core.credential_manager import CredentialManager
from utils.storage import StorageManager
from cli.dashboard import SSHDashboard


class ThemeTests(unittest.IsolatedAsyncioTestCase):
    async def test_theme_selection_is_saved_and_restored_next_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = CredentialManager.__new__(CredentialManager)
            manager.storage = StorageManager(root / 'credentials.json')
            path = root / 'preferences.json'
            path.write_text(json.dumps({'other_preference': True}))
            app = SSHDashboard(manager, lambda name: None)
            async with app.run_test(size=(80, 24)) as pilot:
                await pilot.pause()
                selected = next(name for name in app.available_themes if name != app.theme)
                app.theme = selected
                await pilot.pause()
                self.assertEqual(json.loads(path.read_text())['theme'], selected)
                self.assertTrue(json.loads(path.read_text())['other_preference'])
            next_app = SSHDashboard(manager, lambda name: None)
            self.assertEqual(next_app.theme, selected)
            async with next_app.run_test(size=(80, 24)) as pilot:
                await pilot.pause()
                self.assertEqual(next_app.theme, selected)
                commands = {command.title: command for command in next_app.get_system_commands(next_app.screen)}
                self.assertIn("Theme", commands)
                self.assertIn("Reset theme", commands)
                self.assertNotIn("Screenshot", commands)
                self.assertFalse(next_app.query("#action-themes, #action-reset_theme"))
                commands["Reset theme"].callback()
                await pilot.pause()
                self.assertEqual(next_app.theme, next_app.DEFAULT_THEME)
                self.assertEqual(json.loads(path.read_text())["theme"], next_app.DEFAULT_THEME)
            final_app = SSHDashboard(manager, lambda name: None)
            self.assertEqual(final_app.theme, final_app.DEFAULT_THEME)

    async def test_invalid_and_unavailable_preferences_do_not_break_startup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = CredentialManager.__new__(CredentialManager)
            manager.storage = StorageManager(root / 'credentials.json')
            path = root / 'preferences.json'
            for content in ('{broken', '[]', '{"theme":"missing-theme"}'):
                path.write_text(content)
                app = SSHDashboard(manager, lambda name: None)
                async with app.run_test(size=(80, 24)) as pilot:
                    await pilot.pause()
                    self.assertIn(app.theme, app.available_themes)
