"""Persistent dashboard preferences, separate from SSH credentials."""
import json
import os
from pathlib import Path
import tempfile


class Preferences:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            data = json.loads(self.path.read_text())
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_theme(self, theme):
        data = self.load()
        data['theme'] = theme
        self.path.parent.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent, prefix='.preferences-', delete=False) as file:
                name = file.name
                json.dump(data, file, indent=2)
            os.chmod(name, 0o600)
            os.replace(name, self.path)
        finally:
            if name and Path(name).exists():
                Path(name).unlink()
