"""SSH connection management."""

import subprocess
import os
from core.environment import is_development, is_demo_credential
from pathlib import Path
from typing import Optional

from core.models import SSHCredential
from core.config import KEYS_DIR, AUTH_METHOD_KEY, AUTH_METHOD_PASSWORD, AUTH_METHOD_AGENT


class SSHConnection:
    """Handles SSH connection execution."""
    
    def __init__(self):
        """Initialize SSH connection handler."""
        pass
    
    def get_key_path(self, credential: SSHCredential, default_key: Optional[str]) -> Optional[Path]:
        """Get the full path to the SSH key for a credential."""
        # Determine which key to use
        key_name = credential.key_name
        if not key_name:
            key_name = default_key
        
        if not key_name:
            return None
        
        key_path = KEYS_DIR / key_name
        if key_path.exists():
            return key_path
        
        # Also check in ~/.ssh/
        ssh_key_path = Path.home() / ".ssh" / key_name
        if ssh_key_path.exists():
            return ssh_key_path
        
        return None
    
    def build_ssh_command(
        self,
        credential: SSHCredential,
        key_path: Optional[Path] = None,
        password: Optional[str] = None
    ) -> list[str]:
        """Build the SSH command to execute."""
        # Base command
        cmd = ["ssh"]
        
        # Add key if key-based auth
        if credential.auth_method == AUTH_METHOD_KEY and key_path:
            cmd.extend(["-i", str(key_path)])
        
        # Add port if not default
        if credential.port != 22:
            cmd.extend(["-p", str(credential.port)])
        
        # Add some useful SSH options
        cmd.extend([
            "-o", "ServerAliveInterval=60",  # Keep connection alive
            "-o", "ServerAliveCountMax=3",
        ])
        
        # Build user@host
        connection_string = f"{credential.user}@{credential.host}"
        cmd.append(connection_string)
        
        return cmd
    
    def get_connection_string(self, credential: SSHCredential) -> str:
        """Get the connection string for display."""
        return f"{credential.user}@{credential.host}"
    
    @staticmethod
    def is_demo(credential: SSHCredential) -> bool:
        """Identify fake entries independently of the runtime environment."""
        return is_demo_credential(credential)

    def demo_connect(self, credential: SSHCredential) -> int:
        """Simulate repeatable shell commands and overflow without running processes."""
        if not is_development():
            print("Demo sessions require ENV=development in .env.")
            return 1
        from datetime import datetime
        from rich.console import Console
        from rich.text import Text
        console = Console()
        console.print(Text(f"Demo connected: {credential.user}@{credential.host}:{credential.port}", style="bold green"))
        console.print("[dim]Demo shell: help for commands, scroll 200 for overflow, exit to disconnect.[/dim]")
        while True:
            try:
                command = input(f"{credential.user}@{credential.name}:~$ ").strip()
                if not command:
                    continue
                parts = command.split()
                action = parts[0]
                if command in ("exit", "logout"):
                    break
                if command == "help":
                    console.print("help | whoami | hostname | pwd | ls | date | echo TEXT | clear | scroll [N] | seq [START] END | exit")
                elif command == "whoami":
                    console.print(Text(credential.user))
                elif command == "hostname":
                    console.print(Text(credential.name))
                elif command == "pwd":
                    console.print(Text(f"/home/{credential.user}"))
                elif command == "ls":
                    console.print("app.py  README.md  logs/  backups/  config/")
                elif command == "date":
                    console.print(datetime.now().astimezone().isoformat(timespec="seconds"))
                elif action == "echo":
                    console.print(Text(command[4:].lstrip()))
                elif command == "clear":
                    console.clear()
                elif action in ("scroll", "seq"):
                    try:
                        if action == "scroll" and len(parts) <= 2:
                            start, end = 1, int(parts[1]) if len(parts) == 2 else 200
                        elif action == "seq" and len(parts) in (2, 3):
                            start, end = (1, int(parts[1])) if len(parts) == 2 else (int(parts[1]), int(parts[2]))
                        else:
                            raise ValueError
                        if not 1 <= end - start + 1 <= 10000:
                            raise ValueError
                    except ValueError:
                        console.print("[yellow]Use scroll 1..10000 or seq START END (at most 10000 lines).[/yellow]")
                        continue
                    for number in range(start, end + 1):
                        if action == "seq":
                            console.print(str(number))
                        else:
                            console.print(Text(f"{number:05d} | {credential.name} | demo output for scrolling and copying | " + "sample text " * 8))
                else:
                    console.print(Text(f"Demo: unsupported command '{command}'. Type help for simulated commands."))
            except EOFError:
                break
            except KeyboardInterrupt:
                console.print("\n[dim]Command interrupted. Type exit to disconnect.[/dim]")
        console.print("[dim]Demo session closed.[/dim]")
        return 0

    def connect(
        self,
        credential: SSHCredential,
        key_path: Optional[Path] = None,
        password: Optional[str] = None
    ) -> int:
        """
        Execute SSH connection.
        
        Returns:
            Exit code from SSH command
        """
        if self.is_demo(credential):
            return self.demo_connect(credential)

        # Build SSH command
        cmd = self.build_ssh_command(credential, key_path, password)
        
        # NOTE: Password authentication via sshpass is skipped for now
        # If auth_method is "password", SSH will prompt for password directly in the session
        # This is simpler and more secure than using sshpass
        #
        # Future enhancement: Implement sshpass support for automatic password login
        # if credential.auth_method == AUTH_METHOD_PASSWORD and password:
        #     try:
        #         subprocess.run(["which", "sshpass"], capture_output=True, check=True)
        #         cmd = ["sshpass", "-p", password] + cmd
        #     except (subprocess.CalledProcessError, FileNotFoundError):
        #         pass  # SSH will prompt for password
        
        # Execute SSH command
        try:
            result = subprocess.run(cmd)
            return result.returncode
        except KeyboardInterrupt:
            # User pressed Ctrl+C
            return 130
        except Exception as e:
            print(f"Error executing SSH: {e}")
            return 1

