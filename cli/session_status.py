"""A dedicated tmux status area for interactive SSH sessions."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from rich.console import Console


def status_text(value):
    """Keep credential text literal in tmux formats and strip terminal controls."""
    return ''.join(ch for ch in str(value) if ch.isprintable()).replace('#', '##')


def connect_with_status(credential, key_path=None):
    """Give SSH a separate pane; never repaint over its output."""
    from ssh.connection import SSHConnection
    connection = SSHConnection()
    if not sys.stdin.isatty() or not sys.stdout.isatty() or not shutil.which('tmux'):
        Console().print('[yellow]Persistent connection bar needs tmux and an interactive terminal.[/yellow]')
        return connection.connect(credential, key_path)

    # Use an isolated socket/config: never change the user's existing tmux setup.
    with tempfile.TemporaryDirectory(prefix='ssc-session-') as directory:
        root = Path(directory)
        payload = root / 'session.json'
        result_file = root / 'exit-code'
        data = credential.to_dict()
        data['password_encrypted'] = None
        payload.write_text(json.dumps({'credential': data, 'key_path': str(key_path) if key_path else None}))
        payload.chmod(0o600)
        command = ['tmux', '-S', str(root / 'socket'), '-f', '/dev/null']
        environment = os.environ.copy()
        environment.pop('TMUX', None)
        size = shutil.get_terminal_size()
        runner = Path(__file__).with_name('session_runner.py')
        try:
            subprocess.run(command + ['new-session', '-d', '-s', 'ssh', '-x', str(size.columns), '-y', str(size.lines), sys.executable, str(runner), str(payload), str(result_file)], env=environment, check=True, capture_output=True)
            options = {
                'status': '2', 'status-position': 'top',
                'status-style': 'bg=colour235,fg=colour255',
                'status-interval': '0', 'mouse': 'off',
                'status-format[0]': '#[bold,fg=colour82] SSH | ' + status_text(credential.name) + ' #[default]| ' + status_text(f'{credential.user}@{credential.host}:{credential.port}'),
                'status-format[1]': '#[fg=colour117] Auth: ' + status_text(credential.auth_method) + ' | Key: ' + status_text(key_path.name if key_path else credential.key_name or '(default)') + ' | Ctrl+B [ : copy shell output',
            }
            for option, value in options.items():
                subprocess.run(command + ['set-option', '-t', 'ssh', option, value], env=environment, check=True, capture_output=True)
            (root / 'ready').touch()
            subprocess.run(command + ['attach-session', '-t', 'ssh'], env=environment)
            return int(result_file.read_text()) if result_file.exists() else 130
        finally:
            subprocess.run(command + ['kill-server'], env=environment, capture_output=True)
