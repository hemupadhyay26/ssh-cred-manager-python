"""Keyboard-driven SSH credential dashboard."""

from typing import Callable

from rich.text import Text
from textual.app import App, ComposeResult, SystemCommand
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, DataTable, Footer, Header, Input, Label, Select, Static


class CredentialForm(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, manager, credential=None):
        super().__init__()
        self.manager = manager
        self.credential = credential

    def compose(self) -> ComposeResult:
        c = self.credential
        with VerticalScroll(id="form"):
            yield Label("Edit server" if c else "Add server", classes="dialog-title")
            fields = [("name", "Name", c.name if c else ""),
                      ("host", "Host", c.host if c else ""),
                      ("user", "Username", c.user if c else ""),
                      ("port", "Port", str(c.port) if c else "22"),
                      ("key", "SSH key name (optional)", c.key_name or "" if c else ""),
                      ("description", "Description", c.description or "" if c else ""),
                      ("tags", "Tags (comma separated)", ", ".join(c.tags) if c else "")]
            for field, label, value in fields:
                yield Label(label)
                yield Input(value=value, id=field, disabled=field == "name" and c is not None)
                if field == "key":
                    yield Button("Browse available keys", id="browse-keys")
            yield Label("Authentication")
            yield Select([(a, a) for a in ("key", "password", "agent")], value=c.auth_method if c else "key", allow_blank=False, id="auth")
            yield Label("New password (blank keeps existing; SSH asks at login)")
            yield Input(password=True, id="password")
            yield Static("", id="error", markup=False)
            with Horizontal(classes="buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    def action_cancel(self):
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed):
        event.stop()
        if event.button.id == "browse-keys":
            def chosen(path):
                if path:
                    self.query_one("#key", Input).value = path
            self.app.push_screen(KeysScreen(self.manager, choose=True), chosen)
            return
        if event.button.id == "cancel":
            self.action_cancel()
            return
        if event.button.id != "save":
            return
        def value(field):
            return self.query_one(f"#{field}", Input).value.strip()
        try:
            name, host, user = value("name"), value("host"), value("user")
            if not all((name, host, user)):
                raise ValueError("Name, host and username are required.")
            if any(ch.isspace() for ch in host + user) or host.startswith("-") or "@" in host + user:
                raise ValueError("Host and username must not contain spaces or @; host cannot start with -.")
            port = int(value("port"))
            if not 1 <= port <= 65535:
                raise ValueError("Port must be between 1 and 65535.")
            password = self.query_one("#password", Input).value or None
            fields = dict(host=host, user=user, port=port,
                          auth_method=self.query_one("#auth", Select).value,
                          key_name=value("key"), password=password,
                          description=value("description"),
                          tags=[tag.strip() for tag in value("tags").split(",") if tag.strip()])
            if self.credential:
                saved = self.manager.update_credential(name, **fields)
            else:
                saved = self.manager.add_credential(name=name, **fields)
            if not saved:
                raise ValueError("Server already exists or was removed. Refresh and try again.")
        except Exception as error:
            self.query_one("#error", Static).update(str(error))
            return
        self.dismiss(name)


class KeysScreen(ModalScreen):
    """Browse private keys; return the exact selected path to the caller."""
    BINDINGS = [("escape", "cancel", "Cancel"), ("r", "refresh", "Refresh")]

    def __init__(self, manager, choose=False):
        super().__init__()
        self.manager = manager
        self.choose = choose

    def compose(self):
        with Vertical(id="key-browser"):
            yield Label("Choose SSH key" if self.choose else "SSH keys — Enter to set default", classes="dialog-title")
            yield Input(placeholder="Search keys by name or location", id="keys-search")
            yield DataTable(id="keys-table", cursor_type="row", zebra_stripes=True)
            yield Static("", id="key-details", markup=False)
            with Horizontal(classes="buttons"):
                yield Button("Choose" if self.choose else "Set default", id="key-select", variant="primary")
                yield Button("Refresh", id="key-refresh")
                yield Button("Cancel", id="key-cancel")

    def on_mount(self):
        self.query_one("#keys-table", DataTable).add_columns("Key", "Location", "Default")
        self.action_refresh()
        self.query_one("#keys-table", DataTable).focus()

    def action_refresh(self):
        from core.keys import list_keys
        table = self.query_one("#keys-table", DataTable)
        table.clear()
        default = self.manager.get_default_key()
        query = self.query_one("#keys-search", Input).value.casefold()
        # Match the same managed-first resolution rule as SSHConnection.
        from ssh.connection import SSHConnection
        from core.models import SSHCredential
        resolved = SSHConnection().get_key_path(SSHCredential('default', '', '', key_name=default), None) if default else None
        for key in list_keys():
            if query not in f"{key.name} {key.location}".casefold():
                continue
            is_default = resolved is not None and resolved.resolve() == key.path.resolve()
            table.add_row(Text(key.name), Text(key.location), "Yes" if is_default else "", key=str(key.path))
        self.show_details()

    def selected_key(self):
        table = self.query_one("#keys-table", DataTable)
        return table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value if table.row_count else None

    def show_details(self):
        self.query_one("#key-details", Static).update(self.selected_key() or "No private keys found. Add keys to ~/.ssh or ~/.ssh-cred-manager/keys. Docker lists keys inside its SSH and credentials volumes.")

    def on_input_changed(self, event):
        event.stop()
        if event.input.id == "keys-search":
            self.action_refresh()

    def on_input_submitted(self, event):
        event.stop()
        self.query_one("#keys-table", DataTable).focus()

    def on_data_table_row_highlighted(self, event):
        event.stop()
        self.show_details()

    def on_data_table_row_selected(self, event):
        event.stop()
        self.select_key()

    def select_key(self):
        from pathlib import Path
        selected = self.selected_key()
        if selected and Path(selected).is_file():
            self.dismiss(selected)
        elif selected:
            self.action_refresh()
            self.app.notify("Key was removed. Select another key.", severity="error")
        else:
            self.app.notify("No key selected.")

    def action_cancel(self):
        self.dismiss(None)

    def on_button_pressed(self, event):
        event.stop()
        if event.button.id == "key-select":
            self.select_key()
        elif event.button.id == "key-refresh":
            self.action_refresh()
        else:
            self.action_cancel()


class TransferForm(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, name):
        super().__init__()
        self.server_name = name

    def compose(self):
        with VerticalScroll(id="form"):
            yield Label(Text(f"Rsync — {self.server_name}"), classes="dialog-title")
            yield Label("Direction")
            yield Select([("Pull: server → local", "pull"), ("Push: local → server", "push")], value="pull", allow_blank=False, id="direction")
            yield Label("Source (remote for pull, local for push)")
            yield Input(id="source")
            yield Label("Destination (local for pull, remote for push)")
            yield Input(id="destination")
            yield Label("Source ending in / copies contents. Existing files may be updated; no files are deleted.")
            yield Checkbox("Show progress", value=True, id="progress")
            yield Checkbox("Dry run (preview only)", id="dry-run")
            yield Checkbox("Compress", id="compress")
            yield Checkbox("Checksum comparison", id="checksum")
            yield Checkbox("Skip newer destination files", id="update")
            yield Label("Exclude pattern (CLI supports repeating --exclude)")
            yield Input(id="exclude")
            yield Label("Bandwidth limit (KiB/s; 0 = unlimited)")
            yield Input(value="0", id="bandwidth", type="integer")
            yield Static("", id="error", markup=False)
            with Horizontal(classes="buttons"):
                yield Button("Start", variant="primary", id="start-transfer")
                yield Button("Cancel", id="cancel")

    def action_cancel(self):
        self.dismiss(None)

    def on_button_pressed(self, event):
        event.stop()
        if event.button.id == "cancel":
            self.action_cancel()
        elif event.button.id == "start-transfer":
            try:
                source = self.query_one("#source", Input).value
                destination = self.query_one("#destination", Input).value
                if not source or not destination:
                    raise ValueError("Source and destination are required.")
                bandwidth = int(self.query_one("#bandwidth", Input).value)
                if bandwidth < 0:
                    raise ValueError("Bandwidth must be zero or greater.")
                pattern = self.query_one("#exclude", Input).value
                options = dict(source=source, destination=destination,
                               direction=self.query_one("#direction", Select).value,
                               bandwidth=bandwidth, exclude=[pattern] if pattern else [])
                for option in ("progress", "dry_run", "compress", "checksum", "update"):
                    options[option] = self.query_one("#" + option.replace("_", "-"), Checkbox).value
            except ValueError as error:
                self.query_one("#error", Static).update(str(error))
                return
            self.dismiss(options)


class DeleteConfirmation(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, name):
        super().__init__()
        self.server_name = name

    def compose(self):
        with Vertical(id="confirm"):
            yield Label(Text(f"Delete '{self.server_name}'?"))
            yield Label("This removes the saved credential.")
            with Horizontal(classes="buttons"):
                yield Button("Cancel", id="cancel", variant="primary")
                yield Button("Delete", id="delete", variant="error")

    def action_cancel(self):
        self.dismiss(False)

    def on_button_pressed(self, event):
        event.stop()
        self.dismiss(event.button.id == "delete")


class SSHDashboard(App):
    DEFAULT_THEME = "textual-dark"
    TITLE = "SSH Credential Manager"
    SUB_TITLE = "Server dashboard"
    CSS = """
    Screen { background: $background; }
    #search { margin: 1 2; }
    #servers { height: 1fr; margin: 0 2; }
    #details { height: auto; min-height: 5; max-height: 9; margin: 1 2; padding: 1 2; border: round $accent; }
    #actions { height: auto; margin: 0 2 1 2; }
    #actions Button { min-width: 8; width: 1fr; }
    CredentialForm, KeysScreen, TransferForm, DeleteConfirmation { align: center middle; }
    #form { width: 70; max-width: 95%; height: 90%; padding: 1 2; border: round $accent; background: $surface; }
    #confirm { width: 60; max-width: 95%; height: auto; padding: 2; border: round $error; background: $surface; }
    .dialog-title { text-style: bold; margin-bottom: 1; }
    .buttons { height: 3; margin-top: 1; }
    .buttons Button { margin-right: 2; }
    #key-browser { width: 90; max-width: 95%; height: 80%; padding: 1 2; border: round $accent; background: $surface; }
    #keys-table { height: 1fr; }
    #key-details { height: auto; padding: 1 0; }
    #error { color: $error; height: auto; }
    """
    BINDINGS = [("a", "add", "Add"), ("e", "edit", "Edit"), ("d", "delete", "Delete"),
                ("c", "connect", "Connect"), ("ctrl+t", "transfer", "Rsync"), ("slash", "search", "Search"),
                ("r", "refresh", "Refresh"), ("escape", "clear_search", "Back"),
                ("ctrl+q", "quit", "Quit"), ("ctrl+x", "tool('export')", "Export"),
                ("ctrl+o", "tool('import')", "Import"), ("k", "keys", "Keys"), ("ctrl+k", "keys", "Keys")]

    def __init__(self, manager, connect: Callable, tools=None, transfer=None, preferences_path=None):
        super().__init__()
        self.manager = manager
        self.connect_server = connect
        self.transfer_files = transfer
        self.tools = tools or {}
        from pathlib import Path
        from core.config import CONFIG_DIR
        from core.preferences import Preferences
        storage_file = getattr(getattr(manager, "storage", None), "credentials_file", None)
        directory = Path(storage_file).parent if isinstance(storage_file, (str, Path)) else CONFIG_DIR
        self.preferences = Preferences(preferences_path or directory / "preferences.json")
        self.theme = self.DEFAULT_THEME
        saved_theme = self.preferences.load().get("theme")
        if isinstance(saved_theme, str) and saved_theme in self.available_themes:
            self.theme = saved_theme
        self._last_saved_theme = self.theme

    def check_action(self, action, parameters):
        return not isinstance(self.screen, ModalScreen)

    def compose(self):
        yield Header()
        yield Input(placeholder="Search name, host, user, tags or description (/)", id="search")
        yield DataTable(id="servers", cursor_type="row", zebra_stripes=True)
        yield Static("Select a server to view details.", id="details", markup=False)
        with Horizontal(id="actions"):
            for label, action in [("Connect", "connect"), ("Rsync", "transfer"), ("Add", "add"), ("Edit", "edit"), ("Delete", "delete"), ("Export", "export"), ("Import", "import"), ("Keys", "keys")]:
                yield Button(label, id=f"action-{action}")
        yield Footer()

    def save_selected_theme(self, theme):
        # Ignore pending notifications from an earlier theme during startup.
        if theme.name != self.theme or theme.name == self._last_saved_theme:
            return
        try:
            self.preferences.save_theme(theme.name)
            self._last_saved_theme = theme.name
        except OSError as error:
            self.notify(f"Could not save theme: {error}", severity="error")

    def on_mount(self):
        self.theme_changed_signal.subscribe(self, self.save_selected_theme)
        self.query_one(DataTable).add_columns("Name", "Host", "User", "Port", "Auth", "Tags")
        self.action_refresh()
        self.query_one(DataTable).focus()

    def selected_name(self):
        table = self.query_one(DataTable)
        if not table.row_count:
            return None
        return table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value

    def action_refresh(self):
        table = self.query_one(DataTable)
        selected = self.selected_name()
        query = self.query_one("#search", Input).value.strip()
        try:
            credentials = self.manager.search_credentials(query) if query else self.manager.list_credentials()
            table.clear()
            for c in credentials:
                table.add_row(*(Text(str(v)) for v in (c.name, c.host, c.user, c.port, c.auth_method, ", ".join(c.tags))), key=c.name)
            if selected:
                for i, c in enumerate(credentials):
                    if c.name == selected:
                        table.move_cursor(row=i)
                        break
            self.update_details()
        except Exception as error:
            self.notify(str(error), severity="error")

    def update_details(self):
        name = self.selected_name()
        c = self.manager.get_credential(name) if name else None
        text = (f"{c.name}  |  {c.user}@{c.host}:{c.port}  |  {c.auth_method}\n"
                f"{c.description or 'No description'}\n"
                f"Key: {c.key_name or '(default)'}  |  Last used: {c.last_used or 'Never'}") if c else "No servers match. Press A to add a server, or / to change your search."
        self.query_one("#details", Static).update(text)

    def on_data_table_row_highlighted(self, event):
        self.update_details()

    def on_data_table_row_selected(self, event):
        self.action_connect()

    def on_input_changed(self, event):
        if event.input.id == "search":
            self.action_refresh()

    def on_input_submitted(self, event):
        if event.input.id == "search":
            self.query_one(DataTable).focus()

    def action_search(self):
        self.query_one("#search", Input).focus()

    def action_clear_search(self):
        self.query_one("#search", Input).value = ""
        self.query_one(DataTable).focus()

    def form_saved(self, name):
        if name:
            self.action_refresh()
            table = self.query_one(DataTable)
            for index, key in enumerate(table.rows):
                if key.value == name:
                    table.move_cursor(row=index)
                    break
            table.focus()
            self.notify(f"Saved {name}")

    def action_add(self):
        self.push_screen(CredentialForm(self.manager), self.form_saved)

    def action_edit(self):
        name = self.selected_name()
        if name:
            self.push_screen(CredentialForm(self.manager, self.manager.get_credential(name)), self.form_saved)
        else:
            self.notify("Select a server first.")

    def action_delete(self):
        name = self.selected_name()
        if not name:
            self.notify("Select a server first.")
            return
        def confirmed(yes):
            if yes:
                try:
                    if not self.manager.delete_credential(name):
                        raise ValueError("Server no longer exists.")
                    self.action_refresh()
                    self.notify(f"Deleted {name}")
                except Exception as error:
                    self.notify(str(error), severity="error")
        self.push_screen(DeleteConfirmation(name), confirmed)

    def action_connect(self):
        name = self.selected_name()
        if not name:
            self.notify("Select a server first.")
            return
        try:
            # Suspend all dashboard rendering and input while SSH owns the TTY.
            with self.suspend():
                self.connect_server(name)
            self.action_refresh()
        except Exception as error:
            self.notify(str(error), severity="error")

    def action_transfer(self):
        name = self.selected_name()
        if not name:
            self.notify("Select a server first.")
            return
        if self.transfer_files is None:
            self.notify("Rsync is unavailable.", severity="error")
            return
        def start(options):
            if options is None:
                return
            try:
                with self.suspend():
                    self.transfer_files(name, options)
                self.action_refresh()
            except Exception as error:
                self.notify(str(error), severity="error")
        self.push_screen(TransferForm(name), start)

    def get_system_commands(self, screen):
        for command in super().get_system_commands(screen):
            if command.title != "Screenshot":
                yield command
        yield SystemCommand("Reset theme", "Restore and save the default theme", self.action_reset_theme)

    def action_reset_theme(self):
        self.theme = self.DEFAULT_THEME
        try:
            self.preferences.save_theme(self.DEFAULT_THEME)
            self._last_saved_theme = self.DEFAULT_THEME
            self.notify("Default theme restored and saved.")
        except OSError as error:
            self.notify(f"Could not save theme: {error}", severity="error")

    def action_keys(self):
        def chosen(path):
            if path:
                try:
                    self.manager.set_default_key(path)
                    self.notify("Default SSH key selected.")
                    self.action_refresh()
                except Exception as error:
                    self.notify(str(error), severity="error")
        self.push_screen(KeysScreen(self.manager), chosen)

    def action_tool(self, tool):
        if tool in self.tools:
            try:
                with self.suspend():
                    self.tools[tool]()
                self.action_refresh()
            except Exception as error:
                self.notify(str(error), severity="error")

    def on_button_pressed(self, event):
        if not event.button.id or not event.button.id.startswith("action-"):
            return
        event.stop()
        action = event.button.id.removeprefix("action-")
        if action in self.tools:
            self.action_tool(action)
        else:
            getattr(self, f"action_{action}")()
