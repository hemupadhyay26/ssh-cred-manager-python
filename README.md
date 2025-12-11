# 🔐 SSH Credential Manager

A modern CLI tool to manage SSH credentials easily without manual alias creation, with seamless machine migration support.

---

## ✨ Features

- 🚀 **Interactive Hub** - Main connect interface for all operations
- 🧙 **Quick Wizard** - Add servers in seconds with `ssc wizard user@ip`
- 🔍 **Fuzzy Search** - Find servers by name, host, user, tags, or description
- ⌨️ **Arrow Navigation** - Modern UI with arrow key navigation
- 📊 **Connection Panel** - Sticky info panel during SSH sessions
- 🔑 **Key Management** - Support for SSH keys with default key settings
- 🔐 **Password Auth** - Native SSH password prompts (no storage)
- 📦 **Easy Migration** - Export/import credentials between machines
- ⚡ **Command Shortcuts** - Short aliases for every command

---

## 🚀 Quick Start

### 1. Installation

Run the installation script:

```bash
./install.sh
```

This will:
- Install the package with `uv`
- Create global commands: `ssh-cred` and `ssc`
- Add symlinks to `~/.local/bin/`

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

When you connect to a server, a sticky panel shows on the right side of your terminal:

```
┌─ Connection Info ───┐
│ Server: prod-server │
│ Connect: user@ip    │
│ Key: my-key         │
└─────────────────────┘
```

The panel stays visible even as terminal content scrolls.

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
│   └── connection_panel.py    # Sticky panel
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
