"""Run inside the dedicated SSH pane and relay the remote exit code."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.models import SSHCredential
from ssh.connection import SSHConnection


def main(payload_path=None, result_path=None):
    payload, result = map(Path, (payload_path, result_path) if payload_path is not None else sys.argv[1:3])
    while not payload.with_name('ready').exists():
        time.sleep(0.02)
    data = json.loads(payload.read_text())
    credential = SSHCredential.from_dict(data['credential'])
    key = Path(data['key_path']) if data['key_path'] else None
    code = 1
    try:
        code = SSHConnection().connect(credential, key)
    finally:
        result.write_text(str(code))
    return code


if __name__ == '__main__':
    sys.exit(main())
