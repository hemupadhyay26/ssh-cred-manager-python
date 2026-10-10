"""Incremental, non-deleting rsync transfers over saved SSH connections."""
from core.runtime import external_environment
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from ssh.connection import SSHConnection


def local_path(value):
    # Absolute local operands prevent rsync interpreting ':' or '-' as remote/options.
    result = str(Path(value).expanduser().absolute())
    return result + "/" if value.endswith("/") and not result.endswith("/") else result


def build_rsync_command(credential, source, destination, *, direction="pull",
                        key_path=None, progress=True, dry_run=False, compress=False,
                        checksum=False, update=False, excludes=(), bandwidth=0):
    if direction not in ("pull", "push"):
        raise ValueError("Direction must be pull or push.")
    if not source or not destination or any(c in source + destination for c in "\x00\n\r"):
        raise ValueError("Source and destination paths are required and must be single-line paths.")
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+", credential.user) or credential.user.startswith("-"):
        raise ValueError("Invalid SSH username.")
    if not re.fullmatch(r"[a-zA-Z0-9_.:%-]+", credential.host) or credential.host.startswith("-"):
        raise ValueError("Invalid SSH host.")
    if not 1 <= credential.port <= 65535:
        raise ValueError("SSH port must be between 1 and 65535.")
    if bandwidth < 0:
        raise ValueError("Bandwidth limit must be zero or greater (KiB/s).")
    ssh = SSHConnection().build_ssh_command(credential, key_path)[:-1]
    # Archive copies recursively and preserves mtimes, enabling rsync's default
    # size/mtime quick check. Protect remote arguments from shell interpretation.
    command = ["rsync", "--archive", "--protect-args"]
    if progress:
        command += ["--info=progress2", "--human-readable"]
    for enabled, flag in ((dry_run, "--dry-run"), (compress, "--compress"),
                          (checksum, "--checksum"), (update, "--update")):
        if enabled:
            command.append(flag)
    if dry_run:
        command.append("--itemize-changes")
    if bandwidth:
        command.append(f"--bwlimit={bandwidth}")
    for pattern in excludes:
        command += ["--exclude", pattern]
    command += ["--rsh", shlex.join(ssh), "--"]
    host = f"[{credential.host}]" if ":" in credential.host else credential.host
    remote = f"{credential.user}@{host}:"
    command += ([remote + source, local_path(destination)] if direction == "pull"
                else [local_path(source), remote + destination])
    return command


def run_rsync(credential, source, destination, **options):
    if SSHConnection.is_demo(credential):
        raise ValueError("Demo servers cannot transfer real files. Select a real server.")
    if not shutil.which("rsync"):
        raise ValueError("rsync is missing. Install it locally and on the SSH server (Ubuntu: sudo apt install rsync), or rebuild the Docker image.")
    command = build_rsync_command(credential, source, destination, **options)
    try:
        # Inherit the terminal for live progress and native SSH password prompts.
        return subprocess.run(command, env=external_environment()).returncode
    except KeyboardInterrupt:
        return 130
