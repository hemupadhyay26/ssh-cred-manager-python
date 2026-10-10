"""Regression checks for SSH terminal ownership and summary rendering."""

import io
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from rich.console import Console
from cli.connection_panel import ConnectionPanel


class ConnectionPanelTests(unittest.TestCase):
    def test_narrow_panel_renders_literal_values_without_cursor_controls(self):
        output = io.StringIO()
        panel = ConnectionPanel(Console(file=output, width=32, color_system=None))
        panel.print_connection_info("[red]demo[/red]", "ops@example.test", None, "key", 2222)
        rendered = output.getvalue()
        self.assertIn("[red]demo[/red]", rendered)
        self.assertIn("2222", rendered)
        self.assertNotIn("\x1b", rendered)
        self.assertTrue(all(len(line) <= 32 for line in rendered.splitlines()))

    def test_connect_has_no_panel_writes_while_ssh_runs(self):
        import main
        credential = SimpleNamespace(host="example.test", user="ops", port=2222, auth_method="agent")
        for hidden in (False, True):
            with self.subTest(no_panel=hidden):
                panel = Mock(spec=ConnectionPanel)
                manager = Mock()
                manager.get_credential.return_value = credential
                ssh = Mock()
                ssh.get_connection_string.return_value = "ops@example.test"

                def session(*args):
                    # Only the optional initial summary may have touched the terminal.
                    self.assertEqual(len(panel.mock_calls), 0 if hidden else 1)
                    return 0

                ssh.connect.side_effect = session
                with patch.object(main, "manager", manager), patch.object(main, "ssh_connection", ssh), patch.object(main, "connection_panel", panel), patch.object(main, "console", Mock()), patch("cli.session_status.connect_with_status", side_effect=session):
                    main.connect(name="demo", no_panel=hidden)
                self.assertEqual(len(panel.mock_calls), 0 if hidden else 1)
                if not hidden:
                    panel.print_connection_info.assert_called_once_with(name="demo", connection_string="ops@example.test", key_name=None, auth_method="agent", port=2222)
                manager.update_last_used.assert_called_once_with("demo")


if __name__ == "__main__":
    unittest.main()
