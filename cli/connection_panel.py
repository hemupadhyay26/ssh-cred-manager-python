"""Render connection details once before SSH takes ownership of the terminal."""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class ConnectionPanel:
    """A static summary that never writes over an active SSH session."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console if console is not None else Console()

    def print_connection_info(
        self,
        name: str,
        connection_string: str,
        key_name: Optional[str],
        auth_method: str,
        port: int = 22,
    ):
        """Print one width-aware panel with literal credential values."""
        content = Text()
        fields = [
            ("Server", name, "green"),
            ("Connection", connection_string, "cyan"),
            ("Port", str(port), "blue"),
            ("Auth", auth_method, "magenta"),
        ]
        if auth_method == "key":
            fields.append(("Key", key_name or "(default)", "yellow"))
        for index, (label, value, style) in enumerate(fields):
            if index:
                content.append("\n")
            content.append(f"{label}: ", style="bold")
            content.append(value, style=style)
        self.console.print(Panel(
            content,
            title="SSH Connection",
            border_style="cyan",
            expand=False,
        ))
