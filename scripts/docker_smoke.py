"""Exercise a fresh Docker store without touching users' Compose volumes."""
import os
from pathlib import Path
import subprocess
import uuid

root = Path(__file__).resolve().parent.parent
compose = ["docker", "compose", "--project-directory", str(root), "-f", str(root / "compose.yaml"), "--project-name", "ssc-smoke-" + uuid.uuid4().hex[:12]]


def run(args, *, mode="production", input=None, code=0):
    result = subprocess.run(compose + ["run", "--rm", "-T", "-e", "ENV=" + mode] + args,
                            cwd=root, input=input, text=True, capture_output=True)
    if result.returncode != code:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout


try:
    run(["ssh-cred", "version"])
    assert "requires ENV=development" in run(["ssh-cred", "demo-seed"], code=1)
    assert "Added 5" in run(["ssh-cred", "demo-seed"], mode="development")
    assert "Added 0" in run(["ssh-cred", "demo-seed"], mode="development")
    assert "demo-web-dev" in run(["ssh-cred", "list"], mode="development")
    assert "demo-web-dev" not in run(["ssh-cred", "list"])
    output = run(["ssh-cred", "connect", "demo-web-dev"], mode="development", input="whoami\nscroll 200\nexit\n")
    assert "00200" in output and "Demo session closed" in output
    run(["--entrypoint", "sh", "ssh-cred", "-c", "tmux -V && ssh -V && rsync --version"])
    print("Docker smoke checks passed: startup, dependencies, demo gating, persistence, and overflow.")
finally:
    subprocess.run(compose + ["down", "--volumes"], cwd=root, check=True)
