"""Transfer defaults, argument safety, CLI status, and TUI interaction."""
import shutil
import subprocess
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner
from textual.widgets import Checkbox, Input, Select, Static
from core.models import SSHCredential
from ssh.rsync import build_rsync_command, run_rsync
from cli.dashboard import SSHDashboard, TransferForm
import main


class RsyncTests(unittest.TestCase):
    def setUp(self):
        self.credential = SSHCredential("prod", "example.com", "ops", port=2222)

    def test_defaults_key_port_and_safe_paths(self):
        command = build_rsync_command(self.credential, "/data/a b/", "./downloads/",
                                      key_path=Path("/keys/my key"))
        self.assertIn("--archive", command)
        self.assertIn("--info=progress2", command)
        self.assertIn("--protect-args", command)
        self.assertNotIn("--delete", command)
        self.assertIn("2222", command[command.index("--rsh") + 1])
        self.assertIn("'/keys/my key'", command[command.index("--rsh") + 1])
        self.assertEqual(command[-2], "ops@example.com:/data/a b/")
        self.assertTrue(command[-1].endswith("/downloads/"))

    def test_push_configuration_and_ipv6(self):
        self.credential.host = "2001:db8::1"
        command = build_rsync_command(self.credential, "./-data/", "/remote/a; touch nope/",
            direction="push", progress=False, dry_run=True, compress=True,
            checksum=True, update=True, excludes=["*.tmp", "--delete"], bandwidth=1024)
        self.assertEqual(command[-1], "ops@[2001:db8::1]:/remote/a; touch nope/")
        self.assertTrue(command[-2].startswith("/"))
        for flag in ("--dry-run", "--compress", "--checksum", "--update", "--bwlimit=1024"):
            self.assertIn(flag, command)
        self.assertNotIn("--info=progress2", command)
        self.assertEqual(command[command.index("--delete") - 1], "--exclude")

    def test_invalid_inputs_and_demo(self):
        for kwargs in ({"direction": "delete"}, {"bandwidth": -1}):
            with self.assertRaises(ValueError):
                build_rsync_command(self.credential, "/a", "/b", **kwargs)
        with self.assertRaises(ValueError):
            build_rsync_command(self.credential, "", "/b")
        self.credential.host = "example.com; touch nope"
        with self.assertRaises(ValueError):
            build_rsync_command(self.credential, "/a", "/b")
        with patch("ssh.rsync.subprocess.run") as process:
            with self.assertRaises(ValueError):
                run_rsync(SSHCredential("demo", "192.0.2.1", "ops", tags=["demo"]), "/a", "/b")
            process.assert_not_called()

    @unittest.skipUnless(shutil.which("rsync"), "rsync not installed locally")
    def test_actual_incremental_copy_retains_destination_files_and_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            source, dest = Path(directory)/"source", Path(directory)/"dest"
            source.mkdir(); dest.mkdir()
            (source/"data").write_text("original")
            (dest/"keep").write_text("destination only")
            # Exercise the generated defaults using local operands to avoid a real server.
            command = build_rsync_command(self.credential, str(source)+"/", str(dest)+"/")
            index = command.index("--rsh")
            del command[index:index+2]
            command[-2] = str(source)+"/"
            subprocess.run(command, check=True, capture_output=True)
            modified = (dest/"data").stat().st_mtime_ns
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual((dest/"data").stat().st_mtime_ns, modified)
            self.assertEqual((dest/"keep").read_text(), "destination only")
            (source/"data").write_text("changed contents")
            subprocess.run(command[:1]+["--dry-run"]+command[1:], check=True, capture_output=True)
            self.assertEqual((dest/"data").read_text(), "original")
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual((dest/"data").read_text(), "changed contents")

    def test_cli_defaults_exit_status_and_no_delete_option(self):
        with patch.object(main, "manager") as manager, patch("ssh.rsync.run_rsync", return_value=0) as run:
            manager.get_credential.return_value = self.credential
            manager.get_default_key.return_value = None
            result = CliRunner().invoke(main.app, ["rsync", "prod", "/data/", "./downloads/"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue(run.call_args.kwargs["progress"])
            self.assertEqual(run.call_args.kwargs["direction"], "pull")
            run.return_value = 23
            result = CliRunner().invoke(main.app, ["rsync", "prod", "/data/", "./downloads/"])
            self.assertEqual(result.exit_code, 23)
            run.reset_mock()
            result = CliRunner().invoke(main.app, ["rsync", "prod", "/data/", "./downloads/", "--delete"])
            self.assertNotEqual(result.exit_code, 0)
            run.assert_not_called()


class TransferUITests(unittest.IsolatedAsyncioTestCase):
    async def test_form_defaults_validation_cancel_and_transfer(self):
        credential = SSHCredential("prod", "example.com", "ops")
        manager = Mock()
        manager.list_credentials.return_value = [credential]
        manager.get_credential.return_value = credential
        transfer = Mock()
        app = SSHDashboard(manager, Mock(), transfer=transfer)
        async with app.run_test(size=(100, 45)) as pilot:
            await pilot.pause()
            await pilot.press("ctrl+t")
            await pilot.pause()
            self.assertIsInstance(app.screen, TransferForm)
            self.assertTrue(app.screen.query_one("#progress", Checkbox).value)
            self.assertEqual(app.screen.query_one("#direction", Select).value, "pull")
            app.screen.query_one("#start-transfer").focus()
            await pilot.press("enter")
            await pilot.pause()
            self.assertIn("required", str(app.screen.query_one("#error", Static).content))
            await pilot.press("escape")
            await pilot.pause()
            transfer.assert_not_called()
            await pilot.press("ctrl+t")
            await pilot.pause()
            app.screen.query_one("#source", Input).value = "/srv/data/"
            app.screen.query_one("#destination", Input).value = "./downloads/"
            app.screen.query_one("#start-transfer").focus()
            with patch.object(app, "suspend", return_value=nullcontext()):
                await pilot.press("enter")
                await pilot.pause()
            transfer.assert_called_once()
            name, options = transfer.call_args.args
            self.assertEqual(name, "prod")
            self.assertEqual(options["source"], "/srv/data/")
            self.assertTrue(options["progress"])
            self.assertFalse(options["dry_run"])
