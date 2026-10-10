"""Development-only feature configuration for local and Docker runs."""
import ipaddress
import os
from pathlib import Path
from dotenv import dotenv_values

DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def is_development():
    # Explicit process environment wins; Compose passes ENV from the host .env.
    value = os.environ.get("ENV")
    if value is None:
        value = dotenv_values(DOTENV_PATH).get("ENV")
    return value == "development"


def is_demo_credential(credential):
    if "demo" not in credential.tags:
        return False
    try:
        address = ipaddress.ip_address(credential.host)
    except ValueError:
        return False
    return any(address in ipaddress.ip_network(network) for network in (
        "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24"
    ))
