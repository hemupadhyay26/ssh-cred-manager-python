"""High-level CRUD operations for SSH credentials."""

from typing import Optional, List
from pathlib import Path

from core.models import SSHCredential, CredentialsData
from utils.storage import StorageManager
from utils.crypto_utils import EncryptionManager
from core.config import MASTER_KEY_FILE, KEYS_DIR, DEFAULT_SSH_PORT, AUTH_METHOD_KEY


class CredentialManager:
    """Manages SSH credentials with CRUD operations."""
    
    def __init__(self):
        """Initialize managers."""
        self.storage = StorageManager()
        self.crypto = EncryptionManager(MASTER_KEY_FILE)
    
    def add_credential(
        self,
        name: str,
        host: str,
        user: str,
        port: int = DEFAULT_SSH_PORT,
        auth_method: str = AUTH_METHOD_KEY,
        key_name: Optional[str] = None,
        password: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Add a new credential. Returns True if successful, False if name exists."""
        data = self.storage.load()
        
        # Check if name already exists
        if self.get_credential(name):
            return False
        
        # Encrypt password if provided
        password_encrypted = None
        if password:
            password_encrypted = self.crypto.encrypt(password)
        
        # Create credential
        credential = SSHCredential(
            name=name,
            host=host,
            user=user,
            port=port,
            auth_method=auth_method,
            key_name=key_name,
            password_encrypted=password_encrypted,
            description=description,
            tags=tags or []
        )
        
        # Add to data
        data.credentials.append(credential)
        
        # Save
        self.storage.save(data)
        return True
    
    def get_credential(self, name: str) -> Optional[SSHCredential]:
        """Get a credential by name."""
        data = self.storage.load()
        for cred in data.credentials:
            if cred.name == name:
                return cred
        return None
    
    def list_credentials(self) -> List[SSHCredential]:
        """Get all credentials."""
        data = self.storage.load()
        return data.credentials
    
    def update_credential(
        self,
        name: str,
        host: Optional[str] = None,
        user: Optional[str] = None,
        port: Optional[int] = None,
        auth_method: Optional[str] = None,
        key_name: Optional[str] = None,
        password: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Update a credential. Returns True if successful, False if not found."""
        data = self.storage.load()
        
        # Find credential
        credential = None
        for cred in data.credentials:
            if cred.name == name:
                credential = cred
                break
        
        if not credential:
            return False
        
        # Update fields
        if host is not None:
            credential.host = host
        if user is not None:
            credential.user = user
        if port is not None:
            credential.port = port
        if auth_method is not None:
            credential.auth_method = auth_method
        if key_name is not None:
            credential.key_name = key_name
        if password is not None:
            credential.password_encrypted = self.crypto.encrypt(password)
        if description is not None:
            credential.description = description
        if tags is not None:
            credential.tags = tags
        
        # Save
        self.storage.save(data)
        return True
    
    def delete_credential(self, name: str) -> bool:
        """Delete a credential. Returns True if successful, False if not found."""
        data = self.storage.load()
        
        # Find and remove
        for i, cred in enumerate(data.credentials):
            if cred.name == name:
                data.credentials.pop(i)
                self.storage.save(data)
                return True
        
        return False
    
    def get_password(self, name: str) -> Optional[str]:
        """Get decrypted password for a credential."""
        credential = self.get_credential(name)
        if not credential or not credential.password_encrypted:
            return None
        
        return self.crypto.decrypt(credential.password_encrypted)
    
    def update_last_used(self, name: str):
        """Update the last used timestamp for a credential."""
        data = self.storage.load()
        
        for cred in data.credentials:
            if cred.name == name:
                cred.update_last_used()
                self.storage.save(data)
                break
    
    def get_key_path(self, credential: SSHCredential) -> Optional[Path]:
        """Get the full path to the SSH key for a credential."""
        data = self.storage.load()
        
        # Determine which key to use
        key_name = credential.key_name
        if not key_name:
            # Use default key
            key_name = data.default_key
        
        if not key_name:
            return None
        
        key_path = KEYS_DIR / key_name
        if key_path.exists():
            return key_path
        
        return None
    
    def set_default_key(self, key_name: str):
        """Set the default SSH key."""
        data = self.storage.load()
        data.default_key = key_name
        self.storage.save(data)
    
    def get_default_key(self) -> Optional[str]:
        """Get the default SSH key name."""
        data = self.storage.load()
        return data.default_key
    
    def search_credentials(self, query: str) -> List[SSHCredential]:
        """Search credentials by name, host, user, tags, or description."""
        query = query.lower()
        results = []
        
        for cred in self.list_credentials():
            # Search in multiple fields for better context
            if (query in cred.name.lower() or
                query in cred.host.lower() or
                query in cred.user.lower() or
                any(query in tag.lower() for tag in cred.tags) or
                (cred.description and query in cred.description.lower())):
                results.append(cred)
        
        return results

