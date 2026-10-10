# 🔐 SSH Credential Manager

Manage SSH servers from a command-line interface or a keyboard-driven terminal
dashboard (TUI). Browse SSH keys, edit server entries, connect with a persistent
status bar, transfer files with rsync, and keep your selected theme between sessions.

## Ways to run

| Option | Start the dashboard | Requirements |
| --- | --- | --- |
| Docker | `docker compose run --rm ssh-cred tui` | Docker Engine and Compose; runtime tools are included in the image |
| Standalone Linux binary | `./ssc tui` | Linux AMD64 or ARM64, glibc 2.35+, system OpenSSH/tmux/rsync |
| Local Python | `ssc tui` after optional setup | `./install.sh --local`, then `./setup.sh --local` |

The same CLI commands work across these options: `list`, `add`, `connect`,
`keys`, and `tui`. Docker passes commands directly to the application.
Standalone binaries bundle Python and the application dependencies. GitHub
Actions builds both architectures automatically and attaches verified archives
and checksums when a release containing the workflow is published. See
[standalone binary instructions](docs/BINARY.md) and [GitHub releases](https://github.com/hemupadhyay26/ssh-cred-manager-python/releases).

## Terminal dashboard

Run `ssc tui`, `./ssc tui`, or `docker compose run --rm ssh-cred tui` for your
chosen setup. Use arrow keys to navigate servers and Enter to connect. The
dashboard supports adding, editing, deleting, searching, key selection, and
file transfers. Press **K** to browse keys and **Ctrl+P** for theme selection
and reset; the selected theme is saved for the next session.

---

## ✨ Features

- 🖥️ **Terminal Dashboard (TUI)** - Keyboard navigation, server CRUD, key browsing, transfers, and saved themes
- 🐳 **Docker Support** - Containerized runtime with persistent credentials and keys
- 📦 **Standalone Linux Binaries** - Automated AMD64 and ARM64 release builds with checksums
- 🚀 **Interactive Hub** - Main connect interface for all operations
- 🧙 **Quick Wizard** - Add servers in seconds with `ssc wizard user@ip`
- 🔍 **Fuzzy Search** - Find servers by name, host, user, tags, or description
- ⌨️ **Arrow Navigation** - Modern UI with arrow key navigation
- 📊 **Connection Panel** - Persistent connection status bar during SSH sessions
- 🔑 **Key Management** - Support for SSH keys with default key settings
- 🔐 **Password Auth** - Native SSH password prompts (no storage)
- 📦 **Easy Migration** - Export/import credentials between machines
- ⚡ **Command Shortcuts** - Short aliases for every command

---

## 🚀 Quick Start

### 1. Installation

Use Docker Compose so Python, tmux, OpenSSH, and application dependencies stay inside the container:

```bash
docker compose build
docker compose run --rm ssh-cred tui
```

Docker Engine and Docker Compose must be available on the host. Short commands are optional and are not installed by the Docker build or `install.sh`. To enable them explicitly:

```bash
./setup.sh
cp .env.example .env  # opt in to development demos
ssc demo-seed
ssc tui
ssc connect demo-web-dev
ssc list
```

`setup.sh` links `ssc` and `ssh-cred` to a lightweight Docker launcher in `~/.local/bin`; it does not install Python, tmux, or application packages on the host. Commands work from any directory and preserve arguments and interactive terminal input. If an old alias overrides the command, run `unalias ssc` and `hash -r` and remove that alias from your shell profile. For native Python installation instead, use `./install.sh --local`, followed by `./setup.sh --local` if you want global short commands. Setup does not edit your Bash/Zsh profile. Until you opt in, use `docker compose run --rm ssh-cred <command>` (for example `add`, `connect`, or `tui`) in place of `ssc <command>` below.

### 2. Add Your First Server

Use the wizard for quick setup:

```bash
ssc wizard admin@192.168.1.100
```

Or use the interactive hub:

```bash
ssc add
```

### 3. Connect

```bash
ssc connect
# Use arrow keys to select and connect
```

That's it! 🎉

---

## 🐳 Run with Docker

Run these commands from the project directory in Ubuntu/WSL with Docker and
Docker Compose available:

```bash
docker compose build
docker compose run --rm ssh-cred
```

The default command opens the interactive connect hub. Pass any CLI command
as arguments (do not prefix it with `ssc`):

```bash
docker compose run --rm ssh-cred tui
docker compose run --rm ssh-cred wizard admin@192.168.1.100
docker compose run --rm ssh-cred list
docker compose run --rm ssh-cred connect prod
docker compose run --rm ssh-cred --help
```

The image runs as a non-root user and includes OpenSSH and tmux for SSH sessions
and the persistent connection bar. Dependencies come from `uv.lock`. No incoming
ports are required. Use `docker compose run` from an interactive terminal for the
hub, dashboard, password prompts, and SSH sessions.

Compose keeps credentials, the encryption master key, and managed keys in the
`credentials` volume. The `ssh` volume keeps SSH configuration and `known_hosts`.
Both survive removal of temporary containers. `docker compose down --volumes`
deletes these stores, so back them up before removing volumes.

### Use existing local credentials and keys

Containers start with separate, empty stores. To use your existing Ubuntu/WSL
files, bind mount them instead of the named volumes for that invocation:

```bash
mkdir -p "$HOME/.ssh-cred-manager" "$HOME/.ssh"
docker compose run --rm \
  -v "$HOME/.ssh-cred-manager:/home/app/.ssh-cred-manager" \
  -v "$HOME/.ssh:/home/app/.ssh" \
  ssh-cred connect
```

These mounts are writable: the app can update credentials and SSH can save host
keys. The container user has UID 1000; if your Linux user has a different UID,
add `--user "$(id -u):$(id -g)"` to the command. Key paths in saved credentials
must refer to files inside the container (or key names found in these mounts).

For SSH agent authentication on Linux/WSL, forward a running agent socket:

```bash
docker compose run --rm \
  --user "$(id -u):$(id -g)" \
  -e SSH_AUTH_SOCK=/run/ssh-agent \
  -v "$SSH_AUTH_SOCK:/run/ssh-agent" \
  ssh-cred connect
```

Use this with an accessible credential store; the default named volumes belong
to UID 1000. SSH targets must be reachable from Docker's network. `localhost`
inside the container refers to the container itself.

### Docker without Compose

```bash
docker build -t ssh-cred-manager:local .
docker run --rm -it \
  -e TERM="${TERM:-xterm-256color}" \
  -v ssh-cred-data:/home/app/.ssh-cred-manager \
  -v ssh-cred-ssh:/home/app/.ssh \
  ssh-cred-manager:local connect
```

For export/import, mount a directory and use its container path:

```bash
mkdir -p backups
docker compose run --rm -v "$PWD/backups:/backups" \
  ssh-cred export --output /backups/credentials.json
```

The backup directory must be writable by the container user. Back up the master
key together with the credential store to preserve encrypted-password access.
SSH private keys and credential files are excluded from the image build context.

---

## 💻 Command Reference

### Main Commands

```bash
ssc <command> [options]
```

| Command | Description |
|---------|-------------|
| `connect` | Main hub - search, manage, and connect to servers |
| `wizard` | Quick add with wizard (easiest way to add servers) |
| `list` | List all servers |
| `show` | Show server details |
| `add` | Add new server |
| `update` | Update server |
| `remove` | Remove server |
| `export` | Export credentials for backup/migration |
| `import-creds` | Import credentials from backup |
| `version` | Show version |
| `set-default-key` | Set default SSH key |
| `get-default-key` | Get current default SSH key |

### Usage Examples

```bash
# Connect hub (most used - main interface)
ssc connect

# Quick add with wizard
ssc wizard user@192.168.1.100
ssc wizard admin@server.com

# List all servers
ssc list
ssc list --search production

# Connect to specific server (fuzzy search)
ssc connect prod
ssc connect 192.168

# Show server details
ssc show prod-server

# Update server
ssc update prod-server

# Remove server
ssc remove old-server

# Export/Import
ssc export -o backup.json
ssc import-creds backup.json

# Version
ssc version

# Key management
ssc set-default-key my-key
ssc get-default-key
```

---

## 🎯 Connect Hub (Main Interface)

The connect hub is your main interface for everything:

```bash
ssc connect
```

**Features:**
- 📋 View all servers
- 🔍 Search servers
- ➕ Add new servers
- ✏️ Update servers
- 🗑️ Delete servers
- ℹ️ Show server info
- 🔄 Refresh list
- 🚀 Connect to servers

---

## 🧙 Wizard Mode

The fastest way to add servers:

```bash
ssc wizard user@host
```

**Examples:**

```bash
# Basic usage
ssc wizard ubuntu@192.168.1.100

# Multiple servers at once
ssc wizard ubuntu@10.0.0.1 admin@10.0.0.2

# Just hostname (prompts for user)
ssc wizard 192.168.1.50
```

The wizard will:
1. Parse the connection string
2. Ask for server name (with smart suggestion)
3. Ask for auth method (key/password)
4. Save the credential

**That's it!** No need to fill in port, description, tags, etc. Add those later if needed with `ssc update server-name`.

---

## 🔍 Fuzzy Search

Connect to servers without remembering exact names:

```bash
# Find by partial name
ssc connect prod        # Matches: prod-server, prod-db, production

# Find by IP
ssc connect 192         # Matches: 192.168.1.100, 192.168.1.50

# Find by user
ssc connect ubuntu      # Matches: ubuntu@anywhere

# Find by tag
ssc connect database    # Matches servers tagged with 'database'
```

If multiple matches are found, you'll get a list to choose from with arrow keys.

---

## 🔑 Key Management

### Set Default Key

```bash
ssc set-default-key my-key
```

### Get Default Key

```bash
ssc get-default-key
```

### Key Behavior

- If a server has a specific key name → Use that key
- If no key specified → Use default key
- If no default key → Use SSH agent or default SSH behavior

**Key Storage:** Place your SSH keys in `~/.ssh/` as usual. Just reference them by name (e.g., "my-key" for `~/.ssh/my-key`).

---

## 🔐 Password Authentication

For password-based SSH:

1. Set auth method to "password" when adding server
2. Don't save the password (we don't store passwords)
3. SSH will prompt for password when connecting

**Why?** Native SSH password prompts are more secure and reliable than storing passwords.

```bash
# Add password-based server
ssc wizard user@host
# Select "🔐 Password" when prompted
# Leave password empty

# Connect
ssc connect server-name
# SSH will ask for password directly
```

---

## 📦 Backup & Migration

### Export Credentials

```bash
ssc export -o backup.json
ssc export -o my-servers.json
```

### Import Credentials

```bash
ssc import-creds backup.json
```

**Perfect for:**
- Migrating to a new machine
- Backing up your server list
- Sharing credentials with team (without passwords)

---

## 📊 Connection Panel

When you connect to a server, a persistent two-line tmux status bar stays at the top of the terminal:

```
SSH | prod-server | user@ip:22
Auth: key | Key: my-key | Ctrl+B [ : copy shell output
```

The bar occupies a dedicated area outside the SSH pane and stays visible while output scrolls or the terminal resizes. It never overwrites shell text. tmux copy mode (Ctrl+B, then [) selects only shell output; a native terminal selection that deliberately crosses the status bar can still select the bar itself. This uses a private tmux server and leaves your existing tmux settings unchanged. Interactive sessions require tmux (`sudo apt install tmux` on Ubuntu). Without tmux or a TTY, the tool falls back to the initial summary and ordinary SSH. The private session is cleaned up on disconnect. Detaching with Ctrl+B, then D closes this managed SSH session.

**Disable for a specific connection:**
```bash
ssc connect server-name --no-panel
```

---

## 💡 Common Workflows

### Daily Usage
```bash
# Quick connect to servers
ssc connect

# Or connect directly by name
ssc connect prod-server
```

### Adding Servers
```bash
# Fastest way - use wizard
ssc wizard admin@192.168.1.100

# Or use interactive add
ssc add
```

### Managing Servers
```bash
# List all
ssc list

# Search
ssc list --search production

# Show details
ssc show server-name

# Update
ssc update server-name

# Remove
ssc remove server-name
```

---

## 🎨 Interactive Features

### Arrow Key Navigation

All interactive menus support arrow keys:
- `↑↓` - Navigate
- `Enter` - Select/Confirm
- `Space` - Toggle (multi-select)

### Multi-Select

When updating servers, select multiple fields to update:
- `↑↓` - Move
- `Space` - Toggle selection
- `Enter` - Confirm

---

## 📋 Configuration

### Data Location

Credentials stored in:
```
~/.ssh-cred-manager/credentials.json
```

### Key Storage

SSH keys should be in:
```
~/.ssh-cred-manager/keys
```

Reference them by name in the credential manager.

---

## 🛠️ Advanced Usage

### One-Line Commands

Add server with all details:
```bash
ssc add my-server --host 192.168.1.100 --user admin --auth key --key my-key
```

Update specific fields:
```bash
ssc update prod-server --port 2222 --description "Production DB"
```

Remove without confirmation (careful!):
```bash
ssc remove old-server
```

### Export with Custom Path

```bash
ssc export --output ~/backups/servers-2024.json
ssc e -o ~/backups/servers-2024.json
```

### Search in List

```bash
ssc list --search production
ssc list --search database
```

---

## 🐛 Troubleshooting

### Command not found

If `ssc` or `ssh-cred` commands are not found:

1. Check if `~/.local/bin` is in your PATH:
   ```bash
   echo $PATH | grep ".local/bin"
   ```

2. If not, add to your `~/.bashrc` or `~/.zshrc`:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

3. Reload shell:
   ```bash
   source ~/.bashrc
   ```

4. Or run the install script again:
   ```bash
   ./install.sh
   ```

### Permission denied

```bash
chmod +x ~/.local/bin/ssh-cred
chmod +x ~/.local/bin/ssc
```

### Connection issues

- Verify credentials: `ssc show server-name`
- Check SSH key permissions: `ls -la ~/.ssh/`
- Test direct SSH: `ssh user@host`
- Check if server is reachable: `ping host`

---

## 🗑️ Uninstallation

To remove SSH Credential Manager:

```bash
# Remove commands
rm ~/.local/bin/ssh-cred
rm ~/.local/bin/ssc

# Uninstall package
uv pip uninstall ssh-cred-manager-python

# Optional: Remove data
rm -rf ~/.ssh-cred-manager/
```

---

## 📊 Project Structure

```
ssh-cred-manager-python/
├── main.py              # CLI entry point
├── core/                # Core functionality
│   ├── config.py        # Configuration
│   ├── models.py        # Data models
│   └── credential_manager.py  # CRUD operations
├── cli/                 # CLI components
│   └── connection_panel.py    # Rich connection summary
├── ssh/                 # SSH functionality
│   └── connection.py    # SSH connections
├── utils/               # Utilities
│   ├── crypto_utils.py  # Encryption
│   └── storage.py       # File I/O
├── pyproject.toml       # Project config
├── install.sh           # Installation script
└── README.md            # This file
```

---

## 🎯 Quick Reference Card

```bash
# Installation
./install.sh

# Most used commands
ssc connect              # Connect hub (main interface)
ssc wizard user@ip       # Quick add
ssc list                 # List all
ssc show server          # Show details

# Management
ssc add                  # Add server
ssc update server        # Update server
ssc remove server        # Remove server

# Backup
ssc export -o file       # Export
ssc import-creds file    # Import

# Keys
ssc set-default-key name # Set default key
ssc get-default-key      # Get default key

# Help
ssc --help               # All commands
ssc connect --help       # Command help
```

---

## 🤝 Contributing

Contributions are welcome! This is a personal project but feel free to fork and customize for your needs.

---

<div align="center">

**Happy SSHing!** 🚀

Made with ❤️ for easier SSH management

---


## Keyboard dashboard

Run `ssc tui` (or `uv run python main.py tui`) to open the full-screen server dashboard.
Use Up/Down to select a row and Enter or C to connect. Press A to add, E to edit,
D to delete with confirmation, / to search, R to refresh, and Ctrl+Q to quit.
Tab moves between fields and buttons; Escape cancels a dialog or clears search.
The dashboard includes buttons for export, merge-import, and setting the default SSH key
(Ctrl+X, Ctrl+O, Ctrl+K). Forms support host, user, port, authentication, SSH key,
description, tags, and an optional encrypted password. Editing keeps the server name fixed.
SSH prompts for the login password itself.

The dashboard suspends while SSH runs and resumes when the connection closes.
Entries tagged `demo` in the documentation IP ranges (192.0.2.x, 198.51.100.x,
203.0.113.x) simulate a shell instead: run repeated commands, then type `exit` to return.
Type `help` for commands, `scroll 200` for wrapped overflow output, `seq 1 1000` for numbered lines, and `clear` to clear the shell pane. Empty Enter keeps the demo open. Demo commands are simulated without running local programs. Other servers use real SSH.


### Docker demo and overflow testing

```bash
docker compose build
cp .env.example .env  # ENV=development
docker compose run --rm ssh-cred demo-seed
docker compose run --rm ssh-cred tui
# Or open the demo shell directly:
docker compose run --rm ssh-cred connect demo-web-dev
```

Inside the demo shell try `help`, `scroll 200`, `scroll 1000`, `seq 1 5000`,
`clear`, and `exit`. The top connection bar stays separate from the scrolling pane.
Demo seeding skips existing names and stores only fake documentation addresses
in the Docker credentials volume; it never imports host credentials.

## Rsync file transfers

Use a saved SSH server for incremental file copies. The defaults are **pull**,
archive mode (recursive copying and preserved modification times), and overall
progress. Rsync skips unchanged files using size and modification time and
transfers differences for changed files. Destination-only files are retained;
no delete or source-removal options are exposed. Existing destination files can
still be overwritten by source files. Use `--dry-run` to preview changes or
`--update` to skip newer destination files.

```bash
ssc rsync prod /var/log/myapp/ ./downloads/
ssc rsync prod ./data/ /srv/data/ --direction push
ssc rsync prod /srv/data/ ./downloads/ --dry-run
ssc rsync prod /srv/data/ ./downloads/ --compress --bwlimit 2048
ssc rsync prod /srv/data/ ./downloads/ --exclude '*.tmp' --exclude 'cache/'
ssc rsync prod /srv/data/ ./downloads/ --checksum --no-progress
```

SSH host, username, port, and credential/default key are reused; SSH agent and
native password prompts work as with connect. Each transfer opens an SSH
transport using those settings. Both the local runtime and remote server need
rsync installed (`sudo apt install rsync` on Ubuntu). Docker includes it after
`docker compose build`.

In `ssc tui`, select a server and click **Rsync** or press **Ctrl+T**. Enter source
and destination, choose pull/push, and configure the transfer options. The
terminal shows live progress and SSH prompts, then returns to the dashboard.
A source ending in `/` copies its contents; without `/`, rsync copies the folder
itself. Excludes use rsync patterns.

For Docker, local paths refer to the container filesystem. Mount a host directory
so transferred files survive container removal (the Docker command launcher
does not automatically mount your current directory):

```bash
mkdir -p downloads
docker compose run --rm -v "$PWD/downloads:/transfer" \
  ssh-cred rsync prod /srv/data/ /transfer/
```

Ensure the mounted directory is writable by container UID 1000, or use the user
and credential-store bind mounts described above. Mount transfer folders when
starting a Docker TUI too. Avoid storing downloads in the container's temporary
filesystem.


Demo data and simulated shell sessions are available only with `ENV=development`
in the project `.env` (or explicitly supplied process environment). Docker Compose
passes this value into the container; local runs read the same `.env`. Missing ENV
or any other value disables seeding, hides saved demo entries from the list/dashboard,
and blocks simulated connections. Saved demo data is retained so it can reappear
when development is enabled again. Real SSH connections remain available.


### Browse SSH keys

In `ssc tui`, press **K** or **Ctrl+K**, or click **Keys**. Use Up/Down to
traverse keys, type in the search field to filter, and press Enter to set the
default key. Escape cancels. Add/edit forms also have **Browse available keys**
to select a key for that server. `ssc keys` lists keys from the command line.
The browser scans `~/.ssh-cred-manager/keys` and `~/.ssh`, excludes public keys
and configuration files, and never displays private key contents. In Docker,
these directories refer to the container's persisted volumes.


### Remember the dashboard theme

Choose a theme through the Textual command palette (Ctrl+P → theme). The
dashboard saves the choice immediately and restores it next time. Preferences
live in `~/.ssh-cred-manager/preferences.json`; Docker keeps this file in the
credentials volume. A missing, invalid, or unavailable saved theme falls back
to the default without preventing the dashboard from opening.

Open the command palette with **Ctrl+P** and choose **Theme** to change themes, or **Reset theme** to restore and save the default (`textual-dark`). Theme controls live only in the palette.


## Stable release

The first stable release is **v1.0.0**. See [CHANGELOG.md](CHANGELOG.md) for features and setup notes.


## Pull request stability checks

Pull requests targeting `main` run the functional suite on Python 3.13 and 3.14,
validate shell scripts, build and smoke-test the installed wheel outside the
source checkout, and build/test Docker. Tests cover credential CRUD, encrypted
password persistence, import/export, CLI operations, keyboard UI, keys, themes,
development gating, rsync, and tmux overflow/copy isolation. Docker smoke checks
use temporary Compose projects and clean only their own volumes.

The **PR stability gate** succeeds only when every validation job succeeds.
It is the required status check for merging into `main`; skipped, cancelled, or
failed validation cannot pass the gate. Run the suite locally with
`.venv/bin/python -m unittest discover -s tests -v`.

Contributor setup, required checks, and the optional pre-commit hook are documented in [CONTRIBUTING.md](CONTRIBUTING.md).


## Standalone Linux binaries

Release automation builds and tests a single `ssc` executable for Linux AMD64
and ARM64, then attaches archives and SHA-256 checksums to the published GitHub
release. Python is bundled; system `ssh`, `tmux`, and `rsync` remain required.
The binaries require glibc 2.35 or newer (Ubuntu 22.04+, Debian 12+).

See [binary setup](docs/BINARY.md) for download and usage instructions. PR checks test both native architectures before the
required stability gate passes. The release tag must match the package version
and include the binary workflow; existing older tags are not rebuilt in place.
