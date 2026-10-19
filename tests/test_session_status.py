"""Real PTY regression: persistent status stays outside selected shell content."""
import os
import base64
import re
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from cli.session_status import status_text, connect_with_status
from core.models import SSHCredential


class StatusTests(unittest.TestCase):
    def test_credential_values_cannot_expand_tmux_formats(self):
        self.assertEqual(status_text('srv#(touch /tmp/unwanted)\x1b\n'), 'srv##(touch /tmp/unwanted)')

    def test_noninteractive_connection_falls_back_once(self):
        c = SSHCredential('demo', '192.0.2.10', 'dev', tags=['demo'])
        with patch('cli.session_status.sys.stdin.isatty', return_value=False), patch('ssh.connection.SSHConnection.connect', return_value=7) as connect:
            self.assertEqual(connect_with_status(c), 7)
            connect.assert_called_once_with(c, None)

    @unittest.skipUnless(os.name == 'posix' and shutil.which('tmux'), 'requires Unix PTY and tmux')
    def test_status_is_separate_and_session_cleans_up(self):
        import pty
        import fcntl
        import termios
        import struct
        with tempfile.TemporaryDirectory(prefix='ssc-test-') as directory:
            code = (
                'from contextlib import nullcontext\n'
                'from unittest.mock import patch\n'
                'from cli.session_status import connect_with_status\n'
                'from core.models import SSHCredential\n'
                f'with patch("cli.session_status.tempfile.TemporaryDirectory", return_value=nullcontext({directory!r})):\n'
                '    result = connect_with_status(SSHCredential("demo-pty", "192.0.2.10", "dev", tags=["demo"]))\n'
                'raise SystemExit(result)\n'
            )
            pid, fd = pty.fork()
            if pid == 0:
                environment = os.environ.copy()
                environment['TERM'] = 'xterm-256color'
                environment['ENV'] = 'development'
                os.execve(sys.executable, [sys.executable, '-c', code], environment)
            finished = False
            captured = b''
            try:
                fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 30, 100, 0, 0))
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline and b'demo-pty:~$' not in captured:
                    if select.select([fd], [], [], 0.1)[0]:
                        try:
                            captured += os.read(fd, 65536)
                        except OSError:
                            break
                self.assertIn(b'demo-pty:~$', captured)
                tmux = ['tmux', '-S', str(Path(directory) / 'socket')]
                bar = subprocess.check_output(tmux + ['show-option', '-t', 'ssh', '-v', 'status-format[0]'], text=True)
                self.assertIn('demo-pty', bar)
                pane = subprocess.check_output(tmux + ['capture-pane', '-p', '-t', 'ssh'], text=True)
                self.assertIn('Demo shell:', pane)
                self.assertNotIn('SSH |', pane)
                # Resizing retains the independent status area.
                fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 60, 0, 0))
                self.assertEqual(subprocess.check_output(tmux + ['show-option', '-t', 'ssh', '-v', 'status-position'], text=True).strip(), 'top')
                os.write(fd, b'scroll 3000\n')
                deadline = time.monotonic() + 5
                scrollback = ''
                while time.monotonic() < deadline:
                    if select.select([fd], [], [], 0.05)[0]:
                        os.read(fd, 65536)
                    scrollback = subprocess.check_output(tmux + ['capture-pane', '-p', '-S', '-', '-t', 'ssh'], text=True)
                    if '03000 | demo-pty' in scrollback:
                        break
                self.assertIn('03000 | demo-pty', scrollback)
                self.assertNotIn('SSH |', scrollback)
                self.assertIn('00001 | demo-pty', scrollback)
                self.assertEqual(subprocess.check_output(tmux + ['show-option', '-t', 'ssh', '-v', 'mouse'], text=True).strip(), 'on')
                self.assertEqual(subprocess.check_output(tmux + ['show-option', '-g', '-v', 'history-limit'], text=True).strip(), '100000')

                def wait_mode(expected):
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        if select.select([fd], [], [], 0.05)[0]:
                            os.read(fd, 65536)
                        state = subprocess.check_output(tmux + ['display-message', '-p', '-t', 'ssh', '#{pane_in_mode}'], text=True).strip()
                        if state == expected:
                            return
                    self.fail('scrollback mode did not become ' + expected)

                # Real terminal wheel events must enter scrollback without a prefix.
                os.write(fd, b'\x1b[<64;15;10M')
                wait_mode('1')
                visible = subprocess.check_output(tmux + ['capture-pane', '-p', '-t', 'ssh'], text=True)
                self.assertNotIn('SSH |', visible)
                os.write(fd, b'\x1b')
                wait_mode('0')
                # Page Up is a keyboard alternative; Escape returns input to SSH.
                os.write(fd, b'\x1b[5~')
                wait_mode('1')
                os.write(fd, b'\x1b')
                wait_mode('0')
                # Mouse release copies selected pane text and emits an OSC 52
                # clipboard write; this works without any Ctrl+C keypress.
                os.write(fd, b'echo clipboard-marker\n')
                deadline = time.monotonic() + 3
                lines = []
                while time.monotonic() < deadline:
                    if select.select([fd], [], [], 0.05)[0]:
                        os.read(fd, 65536)
                    lines = subprocess.check_output(tmux + ['capture-pane', '-p', '-t', 'ssh'], text=True).splitlines()
                    if 'clipboard-marker' in lines:
                        break
                self.assertIn('clipboard-marker', lines)
                top = int(subprocess.check_output(tmux + ['display-message', '-p', '-t', 'ssh', '#{pane_top}'], text=True))
                status_lines = int(subprocess.check_output(tmux + ['show-option', '-t', 'ssh', '-v', 'status'], text=True))
                row = top + status_lines + lines.index('clipboard-marker') + 1
                os.write(fd, f'\x1b[<0;1;{row}M'.encode())
                os.write(fd, f'\x1b[<32;17;{row}M'.encode())
                os.write(fd, f'\x1b[<0;17;{row}m'.encode())
                received = b''
                deadline = time.monotonic() + 3
                clipboard_values = []
                while time.monotonic() < deadline:
                    if select.select([fd], [], [], 0.05)[0]:
                        received += os.read(fd, 65536)
                    clipboard_values = [base64.b64decode(value) for value in re.findall(rb'\x1b\]52;[^;]*;([A-Za-z0-9+/=]+)(?:\x07|\x1b\\)', received)]
                    if b'clipboard-marker' in clipboard_values and b'Copied selection' in received:
                        break
                self.assertIn(b'clipboard-marker', clipboard_values)
                self.assertIn(b'Copied selection', received)
                self.assertEqual(subprocess.check_output(tmux + ['show-buffer']), b'clipboard-marker')
                self.assertNotIn('Copied selection', subprocess.check_output(tmux + ['capture-pane', '-p', '-t', 'ssh'], text=True))
                wait_mode('0')
                os.write(fd, b'whoami\nexit\n')
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if select.select([fd], [], [], 0.1)[0]:
                        try:
                            os.read(fd, 65536)
                        except OSError:
                            pass
                    child, status = os.waitpid(pid, os.WNOHANG)
                    if child:
                        finished = True
                        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
                        break
                self.assertTrue(finished, 'connection did not close after exit')
                self.assertEqual((Path(directory) / 'exit-code').read_text(), '0')
                self.assertNotEqual(subprocess.run(tmux + ['list-sessions'], capture_output=True).returncode, 0)
            finally:
                if not finished:
                    os.kill(pid, 9)
                    os.waitpid(pid, 0)
                subprocess.run(['tmux', '-S', str(Path(directory) / 'socket'), 'kill-server'], capture_output=True)
                os.close(fd)
