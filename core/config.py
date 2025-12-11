"""Configuration and constants for SSH Credential Manager."""

from pathlib import Path

# Application settings
APP_NAME = "ssh-cred-manager"
VERSION = "0.1.0"

# File paths
CONFIG_DIR = Path.home() / ".ssh-cred-manager"
KEYS_DIR = CONFIG_DIR / "keys"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
MASTER_KEY_FILE = CONFIG_DIR / "master.key"

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
KEYS_DIR.mkdir(parents=True, exist_ok=True)

# Default SSH port
DEFAULT_SSH_PORT = 22

# Auth methods
AUTH_METHOD_KEY = "key"
AUTH_METHOD_PASSWORD = "password"
AUTH_METHOD_AGENT = "agent"

VALID_AUTH_METHODS = [AUTH_METHOD_KEY, AUTH_METHOD_PASSWORD, AUTH_METHOD_AGENT]

