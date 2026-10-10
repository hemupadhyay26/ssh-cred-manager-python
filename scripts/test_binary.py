"""Test a standalone executable using isolated storage and a real terminal."""
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tempfile
import time

binary = Path(sys.argv[1]).resolve()
if not binary.is_file():
    raise SystemExit('Binary not found: ' + str(binary))


def run(arguments, environment, *, expected=0, input=None):
    result = subprocess.run([str(binary), *arguments], env=environment, cwd=directory,
                            text=True, input=input, capture_output=True, timeout=60)
    if result.returncode != expected:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout


with tempfile.TemporaryDirectory(prefix='ssc-binary-test-') as directory:
    environment = os.environ.copy()
    environment['SSC_CONFIG_DIR'] = str(Path(directory) / 'config')
    environment['ENV'] = 'production'
    environment['TERM'] = 'xterm-256color'
    assert 'SSH Credential Manager' in run(['version'], environment)
    assert 'tui' in run(['--help'], environment)
    assert 'requires ENV=development' in run(['demo-seed'], environment, expected=1)
    run(['add', 'binary-server', '--host', 'example.test', '--user', 'ops', '--port', '22', '--auth', 'agent'], environment)
    assert 'binary-server' in run(['list'], environment)
    run(['show', 'binary-server'], environment)
    run(['remove', 'binary-server', '--force'], environment)
    run(['keys'], environment)
    environment['ENV'] = 'development'
    assert 'Added 5' in run(['demo-seed'], environment)
    assert 'Added 0' in run(['demo-seed'], environment)
    run(['--_ssc-dashboard-smoke'], environment)
    output = run(['connect', 'demo-web-dev', '--no-panel'], environment, input='whoami\nscroll 200\nexit\n')
    assert '00200' in output and 'Demo session closed' in output

    if not shutil.which('tmux'):
        raise AssertionError('tmux is required for the binary session test')
    import pty
    import fcntl
    import termios
    import struct
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(directory)
        os.execve(str(binary), [str(binary), 'connect', 'demo-web-dev'], environment)
    finished = False
    output = b''
    stage = 0
    try:
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 30, 100, 0, 0))
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if select.select([fd], [], [], 0.1)[0]:
                try:
                    output += os.read(fd, 65536)
                except OSError:
                    pass
            if stage == 0 and b'developer@demo-web-dev:~$' in output:
                os.write(fd, b'scroll 200\n')
                stage = 1
            if stage == 1 and b'00200' in output:
                fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 60, 0, 0))
                os.write(fd, b'exit\n')
                stage = 2
            child, status = os.waitpid(pid, os.WNOHANG)
            if child:
                finished = True
                assert os.waitstatus_to_exitcode(status) == 0, output.decode(errors='replace')
                break
        assert finished and stage == 2, output.decode(errors='replace')
        assert b'SSH | demo-web-dev' in output, 'Persistent bar missing'
        assert b'SSH exited with code' not in output, 'Bundled child session failed'
    finally:
        if not finished:
            os.kill(pid, 9)
            os.waitpid(pid, 0)
        os.close(fd)
    print('Standalone binary passed: CLI, storage, development gate, dashboard, keys, tmux worker, overflow, resize, and disconnect.')
