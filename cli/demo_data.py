"""Explicit, repeatable demo data for local and container UI testing."""

from core.environment import is_development

SERVERS = [
    ("demo-web-dev", "192.0.2.10", "developer", 22, "key", "Development web server", ["demo", "development", "web"]),
    ("demo-api-staging", "192.0.2.20", "deploy", 2222, "agent", "Staging API server", ["demo", "staging", "api"]),
    ("demo-db-prod", "198.51.100.30", "dbadmin", 22, "key", "Production database", ["demo", "production", "database"]),
    ("demo-backup", "198.51.100.40", "backup", 2200, "password", "Backup server (demo, no password)", ["demo", "backup"]),
    ("demo-bastion", "203.0.113.50", "ops", 22, "agent", "SSH jump host", ["demo", "operations", "bastion"]),
]


def seed_demo(manager):
    if not is_development():
        raise RuntimeError("Demo data requires ENV=development in .env.")
    added = 0
    for name, host, user, port, auth, description, tags in SERVERS:
        added += bool(manager.add_credential(name=name, host=host, user=user, port=port,
                      auth_method=auth, description=description, tags=tags))
    return added
