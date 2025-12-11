"""Data models for SSH credentials."""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class SSHCredential:
    """Represents a single SSH credential."""
    
    name: str
    host: str
    user: str
    port: int = 22
    auth_method: str = "key"
    key_name: Optional[str] = None
    password_encrypted: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: Optional[str] = None
    last_used: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Convert credential to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "SSHCredential":
        """Create credential from dictionary."""
        return cls(**data)
    
    def update_last_used(self):
        """Update the last used timestamp."""
        self.last_used = datetime.now().isoformat()


@dataclass
class CredentialsData:
    """Root data structure for all credentials."""
    
    version: str = "1.0"
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    default_key: Optional[str] = None
    credentials: list[SSHCredential] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.last_modified is None:
            self.last_modified = datetime.now().isoformat()
    
    def update_modified(self):
        """Update the last modified timestamp."""
        self.last_modified = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "default_key": self.default_key,
            "credentials": [cred.to_dict() for cred in self.credentials]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CredentialsData":
        """Create from dictionary (JSON deserialization)."""
        credentials = [
            SSHCredential.from_dict(cred) 
            for cred in data.get("credentials", [])
        ]
        return cls(
            version=data.get("version", "1.0"),
            created_at=data.get("created_at"),
            last_modified=data.get("last_modified"),
            default_key=data.get("default_key"),
            credentials=credentials
        )

