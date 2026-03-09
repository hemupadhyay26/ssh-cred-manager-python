# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable mode)
uv pip install -e .

# Run the CLI
ssh-cred <command>
ssc <command>   # short alias

# No test suite or linter configured
```

## Architecture

**SSH Credential Manager** — a Python CLI tool for managing SSH credentials with interactive hub, fuzzy search, encryption, and migration support.

### Layers

```
main.py (CLI commands via Typer)
    └── core/credential_manager.py  (CRUD business logic)
            ├── utils/storage.py    (JSON file I/O at ~/.ssh-cred-manager/credentials.json)
            └── utils/crypto_utils.py (Fernet encryption, master key at ~/.ssh-cred-manager/master.key)
ssh/connection.py   (SSH command builder + subprocess execution)
cli/connection_panel.py  (ANSI terminal popup, background redraw thread)
```

### Key Design Decisions

- **Storage**: Credentials stored as JSON with file permissions `0o600`. All encrypted passwords use a local Fernet master key (also `0o600`).
- **SSH key resolution order**: credential-specific key → default key (`set-default-key`) → `~/.ssh/` directory scan.
- **Password auth**: Passwords can be stored encrypted but SSH prompts are handled by the system SSH binary (no automation via paramiko).
- **Connection panel**: A background thread (`threading.Thread`) redraws the right-side ANSI popup box every 500ms to keep it "sticky" during the SSH session.
- **Fuzzy search**: `search_credentials()` in `credential_manager.py` matches across name, host, user, tags, and description fields.
- **Export/import**: Supports merge-mode import to avoid duplicates.

### Data Models (`core/models.py`)

- `SSHCredential` — dataclass with: `name`, `host`, `user`, `port`, `auth_method`, `key_name`, `password_encrypted`, `description`, `tags`, timestamps.
- `CredentialsData` — root structure wrapping a list of `SSHCredential` with version and metadata.

### CLI Entry Points (`main.py`)

`wizard`, `add`, `connect` (interactive hub), `list`, `show`, `update`, `remove`, `export`, `import-creds`, `set-default-key`, `get-default-key`, `version`.

## Package Management

Uses **UV** (`uv.lock` present). Python ≥ 3.13 required. Key deps: `typer`, `questionary`, `rich`, `cryptography`, `keyring`, `paramiko`, `pyyaml`.
