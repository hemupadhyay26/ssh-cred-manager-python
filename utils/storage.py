"""File storage operations for credentials."""

import json
import os
from pathlib import Path
from typing import Optional

from core.models import CredentialsData
from core.config import CREDENTIALS_FILE


class StorageManager:
    """Manages reading and writing credentials to disk."""
    
    def __init__(self, credentials_file: Path = CREDENTIALS_FILE):
        """Initialize with credentials file path."""
        self.credentials_file = credentials_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure credentials file exists, create if not."""
        if not self.credentials_file.exists():
            # Create empty credentials structure
            empty_data = CredentialsData()
            self.save(empty_data)
    
    def load(self) -> CredentialsData:
        """Load credentials from file."""
        try:
            with open(self.credentials_file, 'r') as f:
                data = json.load(f)
                return CredentialsData.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in credentials file: {e}")
        except Exception as e:
            raise Exception(f"Failed to load credentials: {e}")
    
    def save(self, data: CredentialsData):
        """Save credentials to file."""
        try:
            # Update last modified timestamp
            data.update_modified()
            
            # Write to file
            with open(self.credentials_file, 'w') as f:
                json.dump(data.to_dict(), f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.credentials_file, 0o600)
        except Exception as e:
            raise Exception(f"Failed to save credentials: {e}")
    
    def backup(self, backup_path: Path):
        """Create a backup of the credentials file."""
        if self.credentials_file.exists():
            import shutil
            shutil.copy2(self.credentials_file, backup_path)
            os.chmod(backup_path, 0o600)
    
    def export_to_file(self, export_path: Path):
        """Export credentials to a specified file."""
        data = self.load()
        with open(export_path, 'w') as f:
            json.dump(data.to_dict(), f, indent=2)
        os.chmod(export_path, 0o600)
    
    def import_from_file(self, import_path: Path, merge: bool = False):
        """Import credentials from a file."""
        with open(import_path, 'r') as f:
            imported_data = json.load(f)
        
        imported_creds = CredentialsData.from_dict(imported_data)
        
        if merge:
            # Merge with existing credentials
            existing_data = self.load()
            existing_names = {cred.name for cred in existing_data.credentials}
            
            # Add only new credentials (avoid duplicates)
            for cred in imported_creds.credentials:
                if cred.name not in existing_names:
                    existing_data.credentials.append(cred)
            
            self.save(existing_data)
        else:
            # Replace all credentials
            self.save(imported_creds)

