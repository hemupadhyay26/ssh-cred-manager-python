# Changelog

## v1.1.1 — 2026-10-19

- Fix scrollback while the persistent SSH status panel is visible: use the mouse wheel or Page Up, then Escape to resume live input.
- Retain up to 100,000 lines of shell history in the isolated tmux session.
- Copy mouse-drag selections immediately on release, with a brief "Copied selection" confirmation in the status area.
- Keep clipboard confirmation and the connection panel out of shell output.
- Extend real-terminal regression tests to cover overflow, scrolling, selection, clipboard writes, and feedback.

Automatic copying uses OSC 52 and requires a terminal that supports and permits clipboard writes. Hold Shift while dragging for native terminal selection. Linux AMD64 and ARM64 binary archives and SHA-256 checksums are attached by the release workflow after validation.

## v1.1.0 — 2026-10-11

- Standalone Linux executables for AMD64 and ARM64, with bundled Python and application dependencies.
- Automated native binary builds, regression tests, and SHA-256 checksums attached to published releases.
- Frozen tmux workers reuse the executable; system SSH, tmux, and rsync use their original library environment.
- Optional `SSC_CONFIG_DIR` isolates credentials, keys, and preferences; development `.env` is read beside the executable.
- Required PR checks cover Python 3.13/3.14, Docker, both binary architectures, and terminal regressions.
- README documents the TUI, Docker, and standalone setup options.

Linux binaries require glibc 2.35+ and system OpenSSH/tmux/rsync. Python and Docker are not needed for the standalone executable.

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
