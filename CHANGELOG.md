# Changelog

## v1.0.0 — 2026-10-10

First stable release of SSH Credential Manager.

- Full-screen Textual dashboard with keyboard navigation, search, server CRUD, and deletion confirmation.
- Persistent SSH connection status area using an isolated tmux session, with no overlay writes into shell output.
- SSH key browser, default-key selection, and key picker in server forms.
- Theme selection and reset saved across sessions.
- Docker Compose setup with persistent credential and SSH volumes, including Python, OpenSSH, tmux, and rsync.
- Optional `setup.sh` launchers preserve `ssc` and `ssh-cred` commands; native Python installation remains available.
- Incremental rsync pull/push, progress, dry-run, excludes, compression, and checksum options.
- Development-only demo data and simulated shell overflow testing, enabled by `ENV=development`.
- Encrypted password storage, credential import/export, and existing CLI commands retained.

### Setup

Run `docker compose build`, then `docker compose run --rm ssh-cred tui`.
Optionally run `./setup.sh` to enable `ssc tui` and `ssc connect` from any directory.
For demos, copy `.env.example` to `.env` and run `ssc demo-seed`.
For native installation, run `./install.sh --local` and optionally `./setup.sh --local`.

### Operational notes

Docker stores credentials and SSH keys in named volumes; host keys are not automatically imported.
Persistent status requires an interactive terminal and tmux. Password login remains an interactive SSH prompt.
Rsync must also be installed on the remote server. Demo commands are simulated rather than executed.
