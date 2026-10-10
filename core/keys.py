"""Discover private SSH key files without displaying their contents."""
from dataclasses import dataclass
from pathlib import Path
from core.config import KEYS_DIR


@dataclass(frozen=True)
class SSHKey:
    name: str
    path: Path
    location: str


def list_keys(directories=None):
    directories = directories if directories is not None else [(KEYS_DIR, 'Managed'), (Path.home() / '.ssh', 'SSH')]
    keys = []
    seen = set()
    for directory, location in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.name.endswith(('.pub', '-cert.pub')):
                continue
            try:
                resolved = path.resolve()
                if resolved in seen:
                    continue
                with path.open('rb') as file:
                    header = file.readline(256)
                if b'PRIVATE KEY-----' not in header or not header.startswith(b'-----BEGIN '):
                    continue
            except OSError:
                continue
            seen.add(resolved)
            keys.append(SSHKey(path.name, path.absolute(), location))
    return sorted(keys, key=lambda key: (key.name.casefold(), key.location))
