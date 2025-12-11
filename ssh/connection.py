"""SSH connection management."""

import subprocess
import os
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

