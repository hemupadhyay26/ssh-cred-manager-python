"""Main CLI entry point for SSH Credential Manager."""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from pathlib import Path
import questionary
from questionary import Style

from core.credential_manager import CredentialManager
from core.config import VERSION, DEFAULT_SSH_PORT, AUTH_METHOD_KEY, AUTH_METHOD_PASSWORD, VALID_AUTH_METHODS
from ssh.connection import SSHConnection
from cli.connection_panel import ConnectionPanel

app = typer.Typer(
    name="ssh-cred",
    help="SSH Credential Manager - Manage your SSH credentials easily",
    add_completion=True,
)

console = Console()
manager = CredentialManager()
ssh_connection = SSHConnection()
connection_panel = ConnectionPanel()


@app.command()
def version():
    """Show the version of SSH Credential Manager."""
    console.print(f"[bold green]SSH Credential Manager[/bold green] v{VERSION}")


@app.command()
def wizard(
    connections: Optional[List[str]] = typer.Argument(None, help="Connection strings like 'user@host' or just 'host'")
):
    """🧙 Super easy wizard - use: wizard user@ip or wizard user@ip user@ip2"""
    
    import re
    
    console.print("\n[bold magenta]✨ SSH Server Setup Wizard ✨[/bold magenta]\n")
    
    # Parse connection strings
    parsed_connections = []
    if connections:
        # Regex to parse user@host or just host
        # Supports: user@ip, user@hostname, ip, hostname
        connection_pattern = r'^(?:([^@]+)@)?(.+)$'
        
        for conn in connections:
            match = re.match(connection_pattern, conn)
            if match:
                user = match.group(1)  # May be None
                host = match.group(2)
                parsed_connections.append({'user': user, 'host': host})
                console.print(f"[dim]✓ Parsed:[/dim] [cyan]{conn}[/cyan]")
            else:
                console.print(f"[yellow]⚠ Skipping invalid format:[/yellow] {conn}")
        
        console.print()
    
    # If no valid connections parsed, go interactive
    if not parsed_connections:
        console.print("[dim]No connection strings provided. Let's do it step by step![/dim]\n")
        
        # Ask for connection info
        console.print("[bold cyan]Connection Info:[/bold cyan]")
        console.print("[dim]Enter connection as 'user@host' or separately[/dim]\n")
        
        conn_input = Prompt.ask(
            "[yellow]Connection[/yellow] (user@host or just host)",
            default=""
        )
        
        if conn_input:
            # Try to parse
            match = re.match(r'^(?:([^@]+)@)?(.+)$', conn_input)
            if match:
                user = match.group(1)
                host = match.group(2)
                parsed_connections.append({'user': user, 'host': host})
        
        # If still no connection, ask separately
        if not parsed_connections:
            host = Prompt.ask("[yellow]Hostname or IP[/yellow]")
            user = Prompt.ask("[yellow]Username[/yellow]", default="root")
            parsed_connections.append({'user': user, 'host': host})
    
    # Process each connection
    for idx, conn_info in enumerate(parsed_connections, 1):
        if len(parsed_connections) > 1:
            console.print(f"\n[bold cyan]━━━ Server {idx} of {len(parsed_connections)} ━━━[/bold cyan]\n")
        
        host = conn_info['host']
        user = conn_info['user']
        
        # Show what we got
        console.print(f"[dim]Connection:[/dim] [yellow]{user or '(will ask)'}[/yellow]@[green]{host}[/green]")
        console.print()
        
        # Ask for name
        console.print("[bold cyan]Server Name:[/bold cyan]")
        console.print("[dim]What should we call this server?[/dim]")
        console.print(f"[dim]Connecting to:[/dim] [cyan]{host}[/cyan]")
        
        # Suggest name based on host
        suggested_name = host.replace('.', '-').replace(':', '-')[:20]
        name = Prompt.ask("[yellow]Name[/yellow]", default=suggested_name)
        
        # Check if exists
        if manager.get_credential(name):
            console.print(f"\n[red]✗[/red] '{name}' already exists! Use 'update' to modify it.\n")
            if len(parsed_connections) > 1:
                console.print("[yellow]Skipping to next server...[/yellow]\n")
                continue
            else:
                raise typer.Exit(1)
        
        # Ask for user if not provided
        if user is None:
            console.print()
            user = Prompt.ask("[yellow]Username[/yellow]", default="root")
        
        console.print()
        
        # Smart port detection with arrow keys
        port_choice = questionary.select(
            "SSH port (↑↓ arrows):",
            choices=[
                {"name": "🔌 Standard port 22 (default)", "value": 22},
                {"name": "⚙️  Custom port", "value": "custom"},
            ],
        ).ask()
        
        if not port_choice:
            console.print("\n[yellow]Cancelled.[/yellow]\n")
            if len(parsed_connections) > 1:
                continue
            else:
                return
        
        if port_choice == "custom":
            port_input = Prompt.ask("[yellow]Port number[/yellow]", default="22")
            port = int(port_input)
        else:
            port = port_choice
            console.print("[dim]Using standard port 22 ✓[/dim]")
        
        console.print()
        
        # Authentication (arrow key selection)
        console.print("[bold cyan]Authentication:[/bold cyan]")
        
        auth_choice = questionary.select(
            "Choose authentication method (↑↓ arrows):",
            choices=[
                {"name": "🔑 SSH Key (recommended)", "value": "key"},
                {"name": "🔐 Password", "value": "password"},
            ],
        ).ask()
        
        if not auth_choice:
            console.print("\n[yellow]Cancelled.[/yellow]\n")
            if len(parsed_connections) > 1:
                continue
            else:
                return
        
        if auth_choice == "key":
            auth_method = AUTH_METHOD_KEY
            default_key = manager.get_default_key()
            if default_key:
                console.print(f"[dim]✓ Using default key:[/dim] [cyan]{default_key}[/cyan]")
                key_name = None
            else:
                key_name = None
                console.print("[dim]✓ Will use default key (set one with 'set-default-key')[/dim]")
            password = None
        else:
            auth_method = AUTH_METHOD_PASSWORD
            key_name = None
            password = None
            console.print("[dim]✓ SSH will prompt for password when connecting[/dim]")
            # Note: Password saving removed - sshpass not implemented
            # Passwords are handled by SSH directly during connection
        
        # Optional description with arrow key
        description = None
        console.print()
        add_desc_choice = questionary.select(
            "Add description? (↑↓ arrows):",
            choices=[
                {"name": "⏭️  Skip (no description)", "value": False},
                {"name": "📝 Add description", "value": True},
            ],
        ).ask()
        
        if add_desc_choice:
            description = Prompt.ask("[yellow]Description[/yellow]", default="")
            description = description if description else None
        
        # Summary
        console.print("\n[bold green]━━━ Summary ━━━[/bold green]")
        console.print(f"  Name: [cyan]{name}[/cyan]")
        console.print(f"  Host: [green]{host}[/green]")
        console.print(f"  User: [yellow]{user}[/yellow]")
        console.print(f"  Port: [blue]{port}[/blue]")
        console.print(f"  Auth: [magenta]{auth_method}[/magenta]")
        if description:
            console.print(f"  Desc: {description}")
        console.print()
        
        # Confirm and save with arrow key
        save_choice = questionary.select(
            "Save this server? (↑↓ arrows):",
            choices=[
                {"name": "✅ Yes, save it!", "value": True},
                {"name": "❌ No, cancel", "value": False},
            ],
        ).ask()
        
        if not save_choice:
            console.print("[yellow]Skipped[/yellow]\n")
            continue
        
        # Save
        try:
            success = manager.add_credential(
                name=name,
                host=host,
                user=user,
                port=port,
                auth_method=auth_method,
                key_name=key_name,
                password=password,
                description=description,
                tags=[]
            )
            
            if success:
                console.print(f"\n[bold green]✓[/bold green] '{name}' added!\n")
                if len(parsed_connections) > 1:
                    console.print("[dim]Moving to next server...[/dim]")
            else:
                console.print(f"\n[red]✗[/red] Failed to save '{name}'\n")
                
        except Exception as e:
            console.print(f"\n[red]✗[/red] Error: {e}\n")
            if len(parsed_connections) == 1:
                raise typer.Exit(1)
    
    # Final summary if multiple servers
    if len(parsed_connections) > 1:
        console.print("\n[bold green]━━━ All Done! ━━━[/bold green]")
        console.print(f"Added {len([c for c in parsed_connections])} server(s)")
        console.print("\n[bold cyan]What's next?[/bold cyan]")
        console.print("  • List:    [dim]uv run python main.py list[/dim]")
        console.print("  • Connect: [dim]uv run python main.py connect <name>[/dim]")
        console.print()


@app.command()
def add(
    name: Optional[str] = typer.Argument(None, help="Name/alias for this SSH connection"),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="SSH host address"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="SSH username"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="SSH port"),
    auth_method: Optional[str] = typer.Option(None, "--auth", "-a", help="Authentication method (key/password/agent)"),
    key_name: Optional[str] = typer.Option(None, "--key", "-k", help="SSH key name (uses default if not specified)"),
    password: Optional[str] = typer.Option(None, "--password", help="Password (not recommended, use prompt instead)"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Description of this credential"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated tags"),
    prompt_password: bool = typer.Option(False, "--prompt-password", "-P", help="Prompt for password securely"),
):
    """Add a new SSH credential (interactive mode if arguments not provided)."""
    
    # Detect if in one-line mode (all required params provided) or interactive mode
    is_one_line_mode = name is not None and host is not None and user is not None
    
    if not is_one_line_mode:
        console.print("\n[bold cyan]═══ Add SSH Credential ═══[/bold cyan]\n")
    
    # Interactive mode: Prompt for required fields if not provided
    if name is None:
        name = Prompt.ask("[yellow]Credential name/alias[/yellow]")
    
    # Check if credential already exists
    if manager.get_credential(name):
        if is_one_line_mode:
            console.print(f"[red]✗[/red] Credential '{name}' already exists!")
        else:
            console.print(f"\n[red]✗[/red] Credential '{name}' already exists!")
            console.print("[dim]Use 'update' command to modify it.[/dim]\n")
        raise typer.Exit(1)
    
    if host is None:
        host = Prompt.ask("[yellow]SSH host (IP or domain)[/yellow]")
    
    if user is None:
        user = Prompt.ask("[yellow]SSH username[/yellow]")
    
    # Set default port if not provided
    if port is None:
        if is_one_line_mode:
            port = DEFAULT_SSH_PORT
        else:
            port_input = Prompt.ask("[yellow]SSH port[/yellow]", default=str(DEFAULT_SSH_PORT))
            port = int(port_input)
    
    if auth_method is None:
        if is_one_line_mode:
            auth_method = AUTH_METHOD_KEY  # Default to key auth
        else:
            # Arrow navigation for auth method
            auth_choice = questionary.select(
                "Authentication method (↑↓ arrows):",
                choices=[
                    {"name": "🔑 SSH Key (recommended)", "value": "key"},
                    {"name": "🔐 Password", "value": "password"},
                    {"name": "🔓 SSH Agent", "value": "agent"},
                ],
            ).ask()
            
            if not auth_choice:
                console.print("\n[yellow]Cancelled.[/yellow]\n")
                return
            
            auth_method = auth_choice
    
    # Validate auth method
    if auth_method not in VALID_AUTH_METHODS:
        if is_one_line_mode:
            console.print(f"[red]✗[/red] Invalid auth method. Must be one of: {', '.join(VALID_AUTH_METHODS)}")
        else:
            console.print(f"\n[red]✗[/red] Invalid auth method. Must be one of: {', '.join(VALID_AUTH_METHODS)}\n")
        raise typer.Exit(1)
    
    # Handle key name for key-based auth
    if auth_method == AUTH_METHOD_KEY and key_name is None and not is_one_line_mode:
        default_key = manager.get_default_key()
        if default_key:
            use_default = questionary.select(
                f"Use default key '{default_key}'? (↑↓ arrows):",
                choices=[
                    {"name": f"✅ Yes, use {default_key}", "value": True},
                    {"name": "🔑 Specify different key", "value": False},
                ],
            ).ask()
            
            if not use_default:
                key_name = Prompt.ask("[yellow]Enter key name[/yellow]")
        else:
            key_name_input = Prompt.ask(
                "[yellow]Key name (leave empty for default)[/yellow]",
                default=""
            )
            key_name = key_name_input if key_name_input else None
    
    # Handle password input for password-based auth
    actual_password = None
    if auth_method == AUTH_METHOD_PASSWORD:
        if prompt_password:
            actual_password = Prompt.ask("[yellow]Enter password[/yellow]", password=True)
        elif password:
            actual_password = password
        elif not is_one_line_mode:
            add_password = questionary.select(
                "Save password? (↑↓ arrows):",
                choices=[
                    {"name": "⏭️  Skip (SSH will prompt when connecting)", "value": False},
                    {"name": "💾 Save password now (encrypted)", "value": True},
                ],
            ).ask()
            
            if add_password:
                actual_password = Prompt.ask("[yellow]Enter password[/yellow]", password=True)
                confirm_password = Prompt.ask("[yellow]Confirm password[/yellow]", password=True)
                if actual_password != confirm_password:
                    console.print("\n[red]✗[/red] Passwords don't match!\n")
                    raise typer.Exit(1)
            else:
                console.print("[dim]You can add password later with 'update' command.[/dim]")
    
    # Optional fields
    if description is None and not is_one_line_mode:
        desc_input = Prompt.ask("[yellow]Description (optional, press Enter to skip)[/yellow]", default="")
        description = desc_input if desc_input else None
    
    # Parse tags
    tag_list = []
    if tags is None and not is_one_line_mode:
        tags_input = Prompt.ask(
            "[yellow]Tags (comma-separated, optional)[/yellow]",
            default=""
        )
        if tags_input:
            tag_list = [tag.strip() for tag in tags_input.split(",")]
    elif tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
    
    # Add credential
    try:
        success = manager.add_credential(
            name=name,
            host=host,
            user=user,
            port=port,
            auth_method=auth_method,
            key_name=key_name,
            password=actual_password,
            description=description,
            tags=tag_list
        )
        
        if success:
            if is_one_line_mode:
                console.print(f"[green]✓[/green] Credential '[cyan]{name}[/cyan]' added successfully!")
            else:
                console.print(f"\n[green]✓[/green] Credential '[cyan]{name}[/cyan]' added successfully!\n")
                console.print("╭─ Details ─────────────────────╮")
                console.print(f"│ Host: [cyan]{host}[/cyan]")
                console.print(f"│ User: [yellow]{user}[/yellow]")
                console.print(f"│ Port: [blue]{port}[/blue]")
                console.print(f"│ Auth: [magenta]{auth_method}[/magenta]")
                if key_name:
                    console.print(f"│ Key:  [green]{key_name}[/green]")
                elif auth_method == AUTH_METHOD_KEY:
                    console.print(f"│ Key:  [dim](using default)[/dim]")
                if description:
                    console.print(f"│ Desc: {description}")
                if tag_list:
                    console.print(f"│ Tags: {', '.join(tag_list)}")
                console.print("╰───────────────────────────────╯\n")
        else:
            if is_one_line_mode:
                console.print(f"[red]✗[/red] Credential '{name}' already exists!")
            else:
                console.print(f"\n[red]✗[/red] Credential '{name}' already exists!\n")
            raise typer.Exit(1)
    except Exception as e:
        if is_one_line_mode:
            console.print(f"[red]✗[/red] Error adding credential: {e}")
        else:
            console.print(f"\n[red]✗[/red] Error adding credential: {e}\n")
        raise typer.Exit(1)


@app.command()
def list(
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search credentials by name, host, user, or tags"),
):
    """List all saved SSH credentials."""
    try:
        # Get credentials
        if search:
            credentials = manager.search_credentials(search)
            console.print(f"[bold cyan]SSH Credentials (search: '{search}'):[/bold cyan]\n")
        else:
            credentials = manager.list_credentials()
            console.print("[bold cyan]SSH Credentials:[/bold cyan]\n")
        
        if not credentials:
            console.print("[yellow]No credentials found.[/yellow]")
            return
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Host", style="green")
        table.add_column("User", style="yellow")
        table.add_column("Port", style="blue")
        table.add_column("Auth", style="magenta")
        table.add_column("Key/Tags", style="dim")
        
        # Add credentials to table
        for cred in credentials:
            key_or_tags = ""
            if cred.auth_method == AUTH_METHOD_KEY:
                key_or_tags = cred.key_name if cred.key_name else "[default]"
            elif cred.tags:
                key_or_tags = ", ".join(cred.tags)
            
            table.add_row(
                cred.name,
                cred.host,
                cred.user,
                str(cred.port),
                cred.auth_method,
                key_or_tags
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(credentials)} credential(s)[/dim]")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error listing credentials: {e}")
        raise typer.Exit(1)


@app.command()
def show(
    name: Optional[str] = typer.Argument(None, help="Name of the credential to show"),
):
    """Show detailed information about a credential (interactive mode if name not provided)."""
    try:
        # Interactive mode: Select credential if not provided
        if name is None:
            credentials = manager.list_credentials()
            if not credentials:
                console.print("\n[yellow]No credentials found![/yellow]\n")
                return
            
            console.print("\n[bold cyan]═══ Show Credential Details ═══[/bold cyan]\n")
            
            # Build choices for arrow navigation
            show_choices = []
            for cred in credentials:
                auth_icon = "🔑" if cred.auth_method == "key" else "🔐"
                display = f"{auth_icon} {cred.name} ({cred.user}@{cred.host})"
                show_choices.append({"name": display, "value": cred.name})
            
            name = questionary.select(
                "Select credential to view (↑↓ arrows):",
                choices=show_choices,
            ).ask()
            
            if not name:
                return
        
        cred = manager.get_credential(name)
        
        if not cred:
            console.print(f"\n[red]✗[/red] Credential '{name}' not found!\n")
            raise typer.Exit(1)
        
        console.print(f"\n[bold cyan]╭─ Credential: {name} ─────────────────────[/bold cyan]")
        console.print(f"[bold cyan]│[/bold cyan]")
        console.print(f"[bold cyan]│[/bold cyan] [bold]Host:[/bold]        [green]{cred.host}[/green]")
        console.print(f"[bold cyan]│[/bold cyan] [bold]User:[/bold]        [yellow]{cred.user}[/yellow]")
        console.print(f"[bold cyan]│[/bold cyan] [bold]Port:[/bold]        [blue]{cred.port}[/blue]")
        console.print(f"[bold cyan]│[/bold cyan] [bold]Auth Method:[/bold] [magenta]{cred.auth_method}[/magenta]")
        
        if cred.auth_method == AUTH_METHOD_KEY:
            if cred.key_name:
                console.print(f"[bold cyan]│[/bold cyan] [bold]Key Name:[/bold]    [green]{cred.key_name}[/green]")
            else:
                default_key = manager.get_default_key()
                if default_key:
                    console.print(f"[bold cyan]│[/bold cyan] [bold]Key Name:[/bold]    [dim]{default_key} (default)[/dim]")
                else:
                    console.print(f"[bold cyan]│[/bold cyan] [bold]Key Name:[/bold]    [dim](no default key set)[/dim]")
        
        if cred.description:
            console.print(f"[bold cyan]│[/bold cyan] [bold]Description:[/bold] {cred.description}")
        
        if cred.tags:
            console.print(f"[bold cyan]│[/bold cyan] [bold]Tags:[/bold]        {', '.join(cred.tags)}")
        
        console.print(f"[bold cyan]│[/bold cyan]")
        console.print(f"[bold cyan]│[/bold cyan] [dim]Created:    {cred.created_at}[/dim]")
        
        if cred.last_used:
            console.print(f"[bold cyan]│[/bold cyan] [dim]Last Used:  {cred.last_used}[/dim]")
        else:
            console.print(f"[bold cyan]│[/bold cyan] [dim]Last Used:  Never[/dim]")
        
        console.print(f"[bold cyan]╰────────────────────────────────────────[/bold cyan]\n")
        
    except Exception as e:
        console.print(f"\n[red]✗[/red] Error showing credential: {e}\n")
        raise typer.Exit(1)


@app.command()
def connect(
    name: Optional[str] = typer.Argument(None, help="Name of the SSH connection to use"),
    no_panel: bool = typer.Option(False, "--no-panel", help="Hide connection info panel"),
):
    """🚀 Main hub - search, manage, and connect to servers."""
    try:
        # Interactive Hub Mode
        if name is None:
            while True:
                credentials = manager.list_credentials()
                
                console.print("\n[bold magenta]═══ SSH Connection Hub ═══[/bold magenta]\n")
                
                if not credentials:
                    console.print("[yellow]No credentials found yet![/yellow]\n")
                    empty_choice = questionary.select(
                        "No servers yet. What would you like to do? (↑↓ arrows):",
                        choices=[
                            {"name": "➕ Add new server", "value": "add"},
                            {"name": "❌ Exit", "value": "exit"},
                        ],
                    ).ask()
                    
                    choice = "1" if empty_choice == "add" else "0"
                    
                    if choice == "1":
                        # Call wizard inline
                        console.print("\n[dim]Starting wizard...[/dim]")
                        # Simple redirect - they can use wizard command
                        console.print("[cyan]Run:[/cyan] [dim]uv run python main.py wizard user@ip[/dim]\n")
                        return
                    else:
                        return
                
                # Build choices for arrow key selection
                server_choices = []
                for i, cred in enumerate(credentials, 1):
                    auth_icon = "🔑" if cred.auth_method == "key" else "🔐"
                    desc = f" - {cred.description}" if cred.description else ""
                    display = f"{auth_icon} {cred.name} ({cred.user}@{cred.host}){desc}"
                    server_choices.append({
                        "name": display,
                        "value": cred.name
                    })
                
                # Add action choices
                action_choices = [
                    questionary.Separator("═══ Your Servers ═══"),
                ] + server_choices + [
                    questionary.Separator("═══ Actions ═══"),
                    {"name": "🔍 Search servers", "value": "search"},
                    {"name": "➕ Add new server", "value": "add"},
                    {"name": "✏️  Update server", "value": "update"},
                    {"name": "🗑️  Delete server", "value": "delete"},
                    {"name": "ℹ️  Show server details", "value": "info"},
                    {"name": "🔄 Refresh list", "value": "list"},
                    {"name": "❌ Quit", "value": "quit"},
                ]
                
                # Custom style
                custom_style = Style([
                    ('separator', 'fg:#6c6c6c'),
                    ('question', 'bold fg:#00ffff'),
                    ('pointer', 'fg:#00ff00 bold'),
                    ('highlighted', 'fg:#00ff00 bold'),
                    ('selected', 'fg:#00ff00'),
                ])
                
                choice = questionary.select(
                    "Choose server or action (↑↓ arrows, Enter to select):",
                    choices=action_choices,
                    style=custom_style,
                    use_shortcuts=False,
                    use_arrow_keys=True,
                    use_indicator=False,  # Disable the ○ indicator
                ).ask()
                
                if not choice:
                    return
                
                # Handle search
                if choice == 'search':
                    search_query = Prompt.ask("\n[yellow]Search for[/yellow] (name/host/user/tag/description)")
                    results = manager.search_credentials(search_query)
                    
                    if results:
                        console.print(f"\n[cyan]Found {len(results)} result(s) for '{search_query}':[/cyan]\n")
                        
                        # Build search result choices
                        search_choices = []
                        for cred in results:
                            auth_icon = "🔑" if cred.auth_method == "key" else "🔐"
                            display = f"{auth_icon} {cred.name} ({cred.user}@{cred.host})"
                            search_choices.append({"name": display, "value": cred.name})
                        
                        search_choices.append(questionary.Separator())
                        search_choices.append({"name": "❌ Cancel", "value": None})
                        
                        sel = questionary.select(
                            "Select server to connect (↑↓ arrows):",
                            choices=search_choices,
                            style=custom_style,
                        ).ask()
                        
                        if sel:
                            name = sel
                            break  # Exit to connect
                    else:
                        console.print(f"\n[yellow]No matches found for '{search_query}'.[/yellow]\n")
                    continue
                
                # Handle add - Quick inline wizard
                elif choice == 'add':
                    console.print("\n[bold green]═══ Quick Add Server ═══[/bold green]\n")
                    
                    conn_input = Prompt.ask("[yellow]Connection[/yellow] (user@host)")
                    
                    import re
                    match = re.match(r'^(?:([^@]+)@)?(.+)$', conn_input)
                    if not match:
                        console.print("[red]Invalid format![/red]\n")
                        continue
                    
                    user = match.group(1) or Prompt.ask("[yellow]Username[/yellow]", default="root")
                    host = match.group(2)
                    
                    suggested_name = host.replace('.', '-').replace(':', '-')[:20]
                    add_name = Prompt.ask("[yellow]Server name[/yellow]", default=suggested_name)
                    
                    if manager.get_credential(add_name):
                        console.print(f"[red]✗[/red] '{add_name}' already exists!\n")
                        continue
                    
                    # Arrow key auth choice
                    auth_choice = questionary.select(
                        "Authentication method (↑↓ arrows):",
                        choices=[
                            {"name": "🔑 SSH Key", "value": "key"},
                            {"name": "🔐 Password", "value": "password"},
                        ],
                    ).ask()
                    
                    if not auth_choice:
                        continue
                    
                    auth_method = AUTH_METHOD_KEY if auth_choice == "key" else AUTH_METHOD_PASSWORD
                    
                    # Add it
                    success = manager.add_credential(
                        name=add_name,
                        host=host,
                        user=user,
                        port=DEFAULT_SSH_PORT,
                        auth_method=auth_method,
                        key_name=None,
                        password=None,
                        description=None,
                        tags=[]
                    )
                    
                    if success:
                        console.print(f"\n[green]✓[/green] '{add_name}' added!\n")
                    continue
                
                # Handle update - Quick inline update
                elif choice == 'update':
                    console.print("\n[bold yellow]═══ Quick Update Server ═══[/bold yellow]\n")
                    
                    # Build server choices for update
                    update_choices = []
                    for cred in credentials:
                        auth_icon = "🔑" if cred.auth_method == "key" else "🔐"
                        display = f"{auth_icon} {cred.name} ({cred.user}@{cred.host})"
                        update_choices.append({"name": display, "value": cred.name})
                    
                    update_choices.append(questionary.Separator())
                    update_choices.append({"name": "❌ Cancel", "value": None})
                    
                    update_name = questionary.select(
                        "Select server to update (↑↓ arrows):",
                        choices=update_choices,
                        style=custom_style,
                    ).ask()
                    
                    if not update_name:
                        continue
                    
                    curr = manager.get_credential(update_name)
                    console.print(f"\n[dim]Current:[/dim] {curr.user}@{curr.host}:{curr.port}")
                    
                    # Arrow key selection for what to update
                    update_field_choices = [
                        {"name": f"🌐 Host (current: {curr.host})", "value": "host"},
                        {"name": f"👤 User (current: {curr.user})", "value": "user"},
                        {"name": f"🔌 Port (current: {curr.port})", "value": "port"},
                        {"name": f"📝 Description (current: {curr.description or 'none'})", "value": "description"},
                        {"name": f"🏷️  Tags (current: {', '.join(curr.tags) if curr.tags else 'none'})", "value": "tags"},
                        questionary.Separator(),
                        {"name": "❌ Cancel", "value": None},
                    ]
                    
                    update_choice = questionary.select(
                        "\nWhat to update (↑↓ arrows, Enter to select):",
                        choices=update_field_choices,
                        style=custom_style,
                    ).ask()
                    
                    if not update_choice:
                        continue
                    
                    if update_choice == "host":
                        new_host = Prompt.ask("[yellow]New host[/yellow]", default=curr.host)
                        manager.update_credential(update_name, host=new_host)
                        console.print(f"[green]✓[/green] Host updated!\n")
                    elif update_choice == "user":
                        new_user = Prompt.ask("[yellow]New user[/yellow]", default=curr.user)
                        manager.update_credential(update_name, user=new_user)
                        console.print(f"[green]✓[/green] User updated!\n")
                    elif update_choice == "port":
                        new_port = Prompt.ask("[yellow]New port[/yellow]", default=str(curr.port))
                        manager.update_credential(update_name, port=int(new_port))
                        console.print(f"[green]✓[/green] Port updated!\n")
                    elif update_choice == "description":
                        new_desc = Prompt.ask("[yellow]New description[/yellow]", default=curr.description or "")
                        manager.update_credential(update_name, description=new_desc if new_desc else None)
                        console.print(f"[green]✓[/green] Description updated!\n")
                    elif update_choice == "tags":
                        new_tags = Prompt.ask("[yellow]New tags (comma-separated)[/yellow]", default=", ".join(curr.tags))
                        tag_list = [t.strip() for t in new_tags.split(",") if t.strip()]
                        manager.update_credential(update_name, tags=tag_list)
                        console.print(f"[green]✓[/green] Tags updated!\n")
                    
                    continue
                
                # Handle delete
                elif choice == 'delete':
                    console.print("\n[bold red]═══ Delete Server ═══[/bold red]\n")
                    
                    # Build server choices for delete
                    delete_choices = []
                    for cred in credentials:
                        auth_icon = "🔑" if cred.auth_method == "key" else "🔐"
                        display = f"{auth_icon} {cred.name} ({cred.user}@{cred.host})"
                        delete_choices.append({"name": display, "value": cred.name})
                    
                    delete_choices.append(questionary.Separator())
                    delete_choices.append({"name": "❌ Cancel", "value": None})
                    
                    del_name = questionary.select(
                        "Select server to delete (↑↓ arrows):",
                        choices=delete_choices,
                        style=custom_style,
                    ).ask()
                    
                    if not del_name:
                        continue
                    
                    del_cred = manager.get_credential(del_name)
                    console.print(f"\n[bold]Server to delete:[/bold] [red]{del_name}[/red]")
                    console.print(f"  Host: {del_cred.host}")
                    console.print(f"  User: {del_cred.user}")
                    
                    delete_confirm = questionary.select(
                        f"\n⚠️  Delete '{del_name}'? This cannot be undone! (↑↓ arrows):",
                        choices=[
                            {"name": "❌ No, keep it", "value": False},
                            {"name": "🗑️  Yes, delete it", "value": True},
                        ],
                    ).ask()
                    
                    if delete_confirm:
                        if manager.delete_credential(del_name):
                            console.print(f"\n[green]✓[/green] '{del_name}' deleted!\n")
                        else:
                            console.print(f"\n[red]✗[/red] Failed to delete.\n")
                    continue
                
                # Handle list/refresh
                elif choice == 'list':
                    # Refresh list (already showing)
                    continue
                
                # Handle info/show
                elif choice == 'info':
                    console.print("\n[bold cyan]═══ Server Details ═══[/bold cyan]\n")
                    
                    # Build server choices for info
                    info_choices = []
                    for cred in credentials:
                        auth_icon = "🔑" if cred.auth_method == "key" else "🔐"
                        display = f"{auth_icon} {cred.name} ({cred.user}@{cred.host})"
                        info_choices.append({"name": display, "value": cred.name})
                    
                    info_choices.append(questionary.Separator())
                    info_choices.append({"name": "❌ Cancel", "value": None})
                    
                    info_name = questionary.select(
                        "Select server to view (↑↓ arrows):",
                        choices=info_choices,
                        style=custom_style,
                    ).ask()
                    
                    if not info_name:
                        continue
                    
                    cred = manager.get_credential(info_name)
                    console.print(f"\n[bold cyan]╭─ {info_name} ─────────────────────[/bold cyan]")
                    console.print(f"[bold cyan]│[/bold cyan] Host: [green]{cred.host}[/green]")
                    console.print(f"[bold cyan]│[/bold cyan] User: [yellow]{cred.user}[/yellow]")
                    console.print(f"[bold cyan]│[/bold cyan] Port: [blue]{cred.port}[/blue]")
                    console.print(f"[bold cyan]│[/bold cyan] Auth: [magenta]{cred.auth_method}[/magenta]")
                    if cred.description:
                        console.print(f"[bold cyan]│[/bold cyan] Desc: {cred.description}")
                    if cred.tags:
                        console.print(f"[bold cyan]│[/bold cyan] Tags: {', '.join(cred.tags)}")
                    console.print(f"[bold cyan]╰────────────────────────────────────[/bold cyan]\n")
                    
                    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
                    continue
                
                # Handle quit
                elif choice == 'quit':
                    console.print("\n[dim]Goodbye! 👋[/dim]\n")
                    return
                
                # Handle server selection (connect - choice is server name from questionary)
                else:
                    # Choice is the server name directly from questionary
                    name = choice
                    break  # Exit loop to connect
        
        # Get credential - try exact match first
        cred = manager.get_credential(name)
        
        if not cred:
            # No exact match - try fuzzy search
            console.print(f"\n[yellow]No exact match for '{name}'. Searching...[/yellow]\n")
            
            all_credentials = manager.list_credentials()
            matches = []
            
            # Fuzzy search: check if name appears in credential name, host, user, tags, or description
            search_term = name.lower()
            for c in all_credentials:
                if (search_term in c.name.lower() or
                    search_term in c.host.lower() or
                    search_term in c.user.lower() or
                    any(search_term in tag.lower() for tag in c.tags) or
                    (c.description and search_term in c.description.lower())):
                    matches.append(c)
            
            if not matches:
                console.print(f"[red]✗[/red] No servers found matching '{name}'!\n")
                raise typer.Exit(1)
            elif len(matches) == 1:
                # Only one match - use it
                cred = matches[0]
                name = cred.name  # Update name to actual credential name
                console.print(f"[green]✓[/green] Found: [cyan]{cred.name}[/cyan]\n")
            else:
                # Multiple matches - let user choose
                console.print(f"[cyan]Found {len(matches)} matches:[/cyan]\n")
                
                # Build choices with arrow navigation
                match_choices = []
                for c in matches:
                    auth_icon = "🔑" if c.auth_method == "key" else "🔐"
                    desc = f" - {c.description}" if c.description else ""
                    tags_str = f" [{', '.join(c.tags)}]" if c.tags else ""
                    display = f"{auth_icon} {c.name} ({c.user}@{c.host}){desc}{tags_str}"
                    match_choices.append({"name": display, "value": c.name})
                
                match_choices.append(questionary.Separator())
                match_choices.append({"name": "❌ Cancel", "value": None})
                
                # Custom style
                custom_style = Style([
                    ('separator', 'fg:#6c6c6c'),
                    ('question', 'bold fg:#00ffff'),
                    ('pointer', 'fg:#00ff00 bold'),
                    ('highlighted', 'fg:#00ff00 bold'),
                    ('selected', 'fg:#00ff00'),
                ])
                
                selected = questionary.select(
                    "Select server to connect (↑↓ arrows):",
                    choices=match_choices,
                    style=custom_style,
                    use_indicator=False,
                ).ask()
                
                if not selected:
                    console.print("\n[yellow]Cancelled.[/yellow]\n")
                    return
                
                # Update name to the selected credential name
                name = selected
                # Get the selected credential
                cred = manager.get_credential(selected)
        
        # Get connection string
        connection_string = ssh_connection.get_connection_string(cred)
        
        # Get key path if using key auth
        key_path = None
        key_display_name = None
        if cred.auth_method == AUTH_METHOD_KEY:
            default_key = manager.get_default_key()
            key_path = ssh_connection.get_key_path(cred, default_key)
            
            if key_path:
                key_display_name = key_path.name
            elif cred.key_name:
                key_display_name = cred.key_name
            elif default_key:
                key_display_name = default_key
        
        # Get password if using password auth
        password = None
        if cred.auth_method == AUTH_METHOD_PASSWORD:
            # Note: Saved passwords are not used for now
            # SSH will prompt for password directly during the session
            console.print("\n[yellow]Password authentication:[/yellow] SSH will prompt for password in the session.")
            console.print("[dim]Type your password when SSH asks for it.[/dim]")
        
        # Show connection info
        connection_panel.print_connection_info(
            name=name,
            connection_string=connection_string,
            key_name=key_display_name,
            auth_method=cred.auth_method
        )
        
        # Show sticky panel (enabled by default, use --no-panel to hide)
        show_panel = not no_panel  # Inverted logic
        if show_panel:
            connection_panel.show(
                name=name,
                host=cred.host,
                user=cred.user,
                port=cred.port,
                auth=cred.auth_method,
                key=key_display_name
            )
        
        console.print("[dim]Establishing SSH connection...[/dim]\n")
        
        # Execute SSH connection
        exit_code = ssh_connection.connect(cred, key_path, password)
        
        # Hide panel if it was shown
        if show_panel:
            connection_panel.hide()
        
        # Update last used timestamp
        manager.update_last_used(name)
        
        # Connection closed
        console.print(f"\n[dim]Connection to '{name}' closed.[/dim]")
        
        if exit_code != 0 and exit_code != 130:  # 130 is Ctrl+C
            console.print(f"[yellow]SSH exited with code: {exit_code}[/yellow]")
        
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        console.print("\n\n[dim]Disconnected.[/dim]\n")
    except typer.Exit:
        # Re-raise typer.Exit without extra logging
        raise
    except Exception as e:
        console.print(f"\n[red]✗[/red] Connection error: {e}\n")
        raise typer.Exit(1)


@app.command()
def update(
    name: Optional[str] = typer.Argument(None, help="Name of the credential to update"),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="New SSH host address"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="New SSH username"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="New SSH port"),
    auth_method: Optional[str] = typer.Option(None, "--auth", "-a", help="New authentication method"),
    key_name: Optional[str] = typer.Option(None, "--key", "-k", help="New SSH key name"),
    password: Optional[str] = typer.Option(None, "--password", help="New password"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="New description"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="New comma-separated tags"),
    prompt_password: bool = typer.Option(False, "--prompt-password", "-P", help="Prompt for new password securely"),
):
    """Update an existing SSH credential (interactive mode if arguments not provided)."""
    try:
        # Detect if in one-line mode
        has_any_option = any([host, user, port, auth_method, key_name, password, description, tags, prompt_password])
        is_one_line_mode = name is not None and has_any_option
        
        if not is_one_line_mode:
            console.print("\n[bold cyan]═══ Update SSH Credential ═══[/bold cyan]\n")
        
        # Interactive mode: Select credential if not provided
        if name is None:
            credentials = manager.list_credentials()
            if not credentials:
                console.print("[yellow]No credentials found![/yellow]\n")
                return
            
            # Build choices for arrow navigation
            update_select_choices = []
            for cred in credentials:
                auth_icon = "🔑" if cred.auth_method == "key" else "🔐"
                display = f"{auth_icon} {cred.name} ({cred.user}@{cred.host})"
                update_select_choices.append({"name": display, "value": cred.name})
            
            name = questionary.select(
                "Select credential to update (↑↓ arrows):",
                choices=update_select_choices,
            ).ask()
            
            if not name:
                console.print("\n[yellow]Cancelled.[/yellow]\n")
                return
        
        # Check if credential exists
        current_cred = manager.get_credential(name)
        if not current_cred:
            if is_one_line_mode:
                console.print(f"[red]✗[/red] Credential '{name}' not found!")
            else:
                console.print(f"\n[red]✗[/red] Credential '{name}' not found!\n")
            raise typer.Exit(1)
        
        # Show current values only in interactive mode
        if not is_one_line_mode:
            console.print(f"\n[bold]Current values for '[cyan]{name}[/cyan]':[/bold]")
            console.print(f"  Host: [dim]{current_cred.host}[/dim]")
            console.print(f"  User: [dim]{current_cred.user}[/dim]")
            console.print(f"  Port: [dim]{current_cred.port}[/dim]")
            console.print(f"  Auth: [dim]{current_cred.auth_method}[/dim]")
            if current_cred.key_name:
                console.print(f"  Key:  [dim]{current_cred.key_name}[/dim]")
            if current_cred.description:
                console.print(f"  Desc: [dim]{current_cred.description}[/dim]")
            if current_cred.tags:
                console.print(f"  Tags: [dim]{', '.join(current_cred.tags)}[/dim]")
            
            console.print("\n[dim]Press Enter to keep current value, or type new value:[/dim]\n")
        
        if not is_one_line_mode:
            # Interactive mode - arrow navigation for field selection
            console.print()
            update_fields = questionary.checkbox(
                "Select fields to update (↑↓ arrows, Space to select, Enter to confirm):",
                choices=[
                    {"name": f"🌐 Host (current: {current_cred.host})", "value": "host"},
                    {"name": f"👤 User (current: {current_cred.user})", "value": "user"},
                    {"name": f"🔌 Port (current: {current_cred.port})", "value": "port"},
                    {"name": f"🔑 Auth method (current: {current_cred.auth_method})", "value": "auth"},
                    {"name": f"📝 Description (current: {current_cred.description or 'none'})", "value": "description"},
                    {"name": f"🏷️  Tags (current: {', '.join(current_cred.tags) if current_cred.tags else 'none'})", "value": "tags"},
                ],
            ).ask()
            
            # Check if cancelled (None) or no selection (empty list)
            if update_fields is None:
                console.print("\n[yellow]Update cancelled.[/yellow]\n")
                return
            
            if not update_fields or len(update_fields) == 0:
                console.print("\n[yellow]No fields selected to update.[/yellow]\n")
                console.print("[dim]Tip: Use Space to select fields, then press Enter[/dim]\n")
                return
            
            # Update selected fields
            if "host" in update_fields:
                host = Prompt.ask(f"  New host", default=current_cred.host)
            
            if "user" in update_fields:
                user = Prompt.ask(f"  New user", default=current_cred.user)
            
            if "port" in update_fields:
                port_input = Prompt.ask(f"  New port", default=str(current_cred.port))
                port = int(port_input)
            
            if "auth" in update_fields:
                auth_method = questionary.select(
                    "New authentication method (↑↓ arrows):",
                    choices=[
                        {"name": "🔑 SSH Key", "value": "key"},
                        {"name": "🔐 Password", "value": "password"},
                        {"name": "🔓 SSH Agent", "value": "agent"},
                    ],
                ).ask()
                
                if auth_method == AUTH_METHOD_KEY:
                    update_key = questionary.select(
                        "Update SSH key? (↑↓ arrows):",
                        choices=[
                            {"name": "⏭️  Keep current", "value": False},
                            {"name": "🔑 Change key", "value": True},
                        ],
                    ).ask()
                    
                    if update_key:
                        key_name = Prompt.ask(
                            "  New key name (empty for default)",
                            default=current_cred.key_name or ""
                        )
                        key_name = key_name if key_name else None
                
                elif auth_method == AUTH_METHOD_PASSWORD:
                    update_pass = questionary.select(
                        "Update password? (↑↓ arrows):",
                        choices=[
                            {"name": "⏭️  Keep current", "value": False},
                            {"name": "🔐 Change password", "value": True},
                        ],
                    ).ask()
                    
                    if update_pass:
                        password = Prompt.ask("  New password", password=True)
                        confirm_pass = Prompt.ask("  Confirm password", password=True)
                        if password != confirm_pass:
                            console.print("\n[red]✗[/red] Passwords don't match!\n")
                            raise typer.Exit(1)
            
            if "description" in update_fields:
                description = Prompt.ask(
                    "  New description",
                    default=current_cred.description or ""
                )
                description = description if description else None
            
            if "tags" in update_fields:
                tags = Prompt.ask(
                    "  New tags (comma-separated)",
                    default=", ".join(current_cred.tags) if current_cred.tags else ""
                )
        
        # Handle password prompt
        actual_password = None
        if prompt_password:
            actual_password = Prompt.ask("[yellow]Enter new password[/yellow]", password=True)
        elif password:
            actual_password = password
        
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Update credential
        success = manager.update_credential(
            name=name,
            host=host,
            user=user,
            port=port,
            auth_method=auth_method,
            key_name=key_name,
            password=actual_password,
            description=description,
            tags=tag_list
        )
        
        if success:
            if is_one_line_mode:
                console.print(f"[green]✓[/green] Credential '[cyan]{name}[/cyan]' updated successfully!")
            else:
                console.print(f"\n[green]✓[/green] Credential '[cyan]{name}[/cyan]' updated successfully!\n")
        else:
            if is_one_line_mode:
                console.print(f"[red]✗[/red] Failed to update credential '{name}'")
            else:
                console.print(f"\n[red]✗[/red] Failed to update credential '{name}'\n")
            raise typer.Exit(1)
            
    except Exception as e:
        if is_one_line_mode:
            console.print(f"[red]✗[/red] Error updating credential: {e}")
        else:
            console.print(f"\n[red]✗[/red] Error updating credential: {e}\n")
        raise typer.Exit(1)


@app.command()
def remove(
    name: Optional[str] = typer.Argument(None, help="Name of the credential to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove an SSH credential (interactive mode if name not provided)."""
    try:
        console.print("\n[bold cyan]═══ Remove SSH Credential ═══[/bold cyan]\n")
        
        # Interactive mode: Select credential if not provided
        if name is None:
            credentials = manager.list_credentials()
            if not credentials:
                console.print("[yellow]No credentials found![/yellow]\n")
                return
            
            # Build choices for arrow navigation
            remove_choices = []
            for cred in credentials:
                auth_icon = "🔑" if cred.auth_method == "key" else "🔐"
                display = f"{auth_icon} {cred.name} ({cred.user}@{cred.host})"
                remove_choices.append({"name": display, "value": cred.name})
            
            name = questionary.select(
                "Select credential to remove (↑↓ arrows):",
                choices=remove_choices,
            ).ask()
            
            if not name:
                console.print("\n[yellow]Cancelled.[/yellow]\n")
                return
        
        # Check if credential exists
        cred = manager.get_credential(name)
        if not cred:
            console.print(f"\n[red]✗[/red] Credential '{name}' not found!\n")
            raise typer.Exit(1)
        
        # Show credential details
        console.print(f"\n[bold]Credential to remove:[/bold]")
        console.print(f"  Name: [cyan]{cred.name}[/cyan]")
        console.print(f"  Host: [dim]{cred.host}[/dim]")
        console.print(f"  User: [dim]{cred.user}[/dim]")
        console.print(f"  Port: [dim]{cred.port}[/dim]")
        
        # Confirm deletion
        if not force:
            console.print(f"\n[red bold]⚠ Warning:[/red bold] This action cannot be undone!")
            
            confirm = questionary.select(
                f"Delete '{name}'? (↑↓ arrows):",
                choices=[
                    {"name": "❌ No, keep it", "value": False},
                    {"name": "🗑️  Yes, delete permanently", "value": True},
                ],
            ).ask()
            
            if not confirm:
                console.print("\n[yellow]Cancelled - credential not removed[/yellow]\n")
                return
        
        # Delete credential
        success = manager.delete_credential(name)
        
        if success:
            console.print(f"\n[green]✓[/green] Credential '[cyan]{name}[/cyan]' removed successfully!\n")
        else:
            console.print(f"\n[red]✗[/red] Failed to remove credential '{name}'\n")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"\n[red]✗[/red] Error removing credential: {e}\n")
        raise typer.Exit(1)


@app.command()
def export(
    output_file: str = typer.Option("ssh-creds-export.json", "--output", "-o", help="Output file path"),
):
    """Export all credentials to a file for migration."""
    try:
        export_path = Path(output_file)
        
        # Get credential count
        credentials = manager.list_credentials()
        
        if not credentials:
            console.print("[yellow]No credentials to export![/yellow]")
            return
        
        # Export
        manager.storage.export_to_file(export_path)
        
        console.print(f"[green]✓[/green] Exported {len(credentials)} credential(s) to: [cyan]{export_path}[/cyan]")
        console.print(f"[dim]File permissions set to 600 (owner only)[/dim]")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error exporting credentials: {e}")
        raise typer.Exit(1)


@app.command()
def import_creds(
    input_file: str = typer.Argument(..., help="Input file path to import from"),
    merge: bool = typer.Option(False, "--merge", "-m", help="Merge with existing credentials (skip duplicates)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Import credentials from a file."""
    try:
        import_path = Path(input_file)
        
        if not import_path.exists():
            console.print(f"[red]✗[/red] File not found: {import_path}")
            raise typer.Exit(1)
        
        # Warn about overwrite
        if not merge and not force:
            current_count = len(manager.list_credentials())
            if current_count > 0:
                confirm = questionary.select(
                    f"⚠️  This will replace all {current_count} existing credential(s). Continue? (↑↓ arrows):",
                    choices=[
                        {"name": "❌ No, cancel import", "value": False},
                        {"name": "✅ Yes, replace all", "value": True},
                    ],
                ).ask()
                
                if not confirm:
                    console.print("[yellow]Import cancelled[/yellow]")
                    return
        
        # Import
        before_count = len(manager.list_credentials())
        manager.storage.import_from_file(import_path, merge=merge)
        after_count = len(manager.list_credentials())
        
        if merge:
            added = after_count - before_count
            console.print(f"[green]✓[/green] Imported {added} new credential(s) (total: {after_count})")
        else:
            console.print(f"[green]✓[/green] Imported {after_count} credential(s)")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error importing credentials: {e}")
        raise typer.Exit(1)


@app.command()
def set_default_key(
    key_name: str = typer.Argument(..., help="Name of the default SSH key"),
):
    """Set the default SSH key to use when no key is specified."""
    try:
        manager.set_default_key(key_name)
        console.print(f"[green]✓[/green] Default key set to: [cyan]{key_name}[/cyan]")
        console.print(f"[dim]Key should be located at: ~/.ssh-cred-manager/keys/{key_name}[/dim]")
    except Exception as e:
        console.print(f"[red]✗[/red] Error setting default key: {e}")
        raise typer.Exit(1)


@app.command()
def get_default_key():
    """Show the current default SSH key."""
    try:
        key_name = manager.get_default_key()
        if key_name:
            console.print(f"[cyan]Default key:[/cyan] {key_name}")
        else:
            console.print("[yellow]No default key set[/yellow]")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
