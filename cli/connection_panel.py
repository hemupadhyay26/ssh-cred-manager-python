"""Connection panel for displaying active SSH connection info - Popup Box Style."""

import sys
import shutil
import threading
import time
from typing import Optional


class ConnectionPanel:
    """Manages the connection information panel on the right side - Popup style."""
    
    def __init__(self):
        """Initialize connection panel."""
        self.active = False
        self.connection_info = {}
        self.redraw_thread = None
        self.stop_redraw = False
    
    def _get_terminal_width(self) -> int:
        """Get terminal width."""
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80  # Default fallback
    
    def _save_cursor(self):
        """Save cursor position using ANSI escape code."""
        sys.stdout.write("\x1b7")
        sys.stdout.flush()
    
    def _restore_cursor(self):
        """Restore cursor position using ANSI escape code."""
        sys.stdout.write("\x1b8")
        sys.stdout.flush()
    
    def _move_cursor(self, row: int, col: int):
        """Move cursor to specific position."""
        sys.stdout.write(f"\x1b[{row};{col}H")
        sys.stdout.flush()
    
    def show_popup_box(
        self,
        server_name: str,
        hostname: str,
        user: str = "",
        key: str = ""
    ):
        """Show popup box on the right side of terminal."""
        # Calculate box dimensions
        connection_str = f"{user}@{hostname}" if user else hostname
        max_len = max(len(server_name), len(connection_str), len(key) if key else 0)
        box_width = max_len + 4
        
        # Get terminal width and calculate position
        terminal_width = self._get_terminal_width()
        popup_x = terminal_width - box_width - 2
        popup_y = 2  # Fixed vertical position
        
        # Create box lines with colors (ANSI color codes)
        top_border = "┌" + "─" * box_width + "┐"
        bottom_border = "└" + "─" * box_width + "┘"
        
        # Format content lines with proper spacing
        server_padding = " " * (box_width - len(server_name) - 2)
        connection_padding = " " * (box_width - len(connection_str) - 2)
        
        server_line = f"│ \x1b[32m{server_name}\x1b[0m{server_padding} │"
        connection_line = f"│ \x1b[36m{connection_str}\x1b[0m{connection_padding} │"
        
        # Save cursor position
        self._save_cursor()
        
        # Draw the box
        self._move_cursor(popup_y, popup_x)
        sys.stdout.write(top_border)
        
        self._move_cursor(popup_y + 1, popup_x)
        sys.stdout.write(server_line)
        
        self._move_cursor(popup_y + 2, popup_x)
        sys.stdout.write(connection_line)
        
        # Add key line if provided
        if key:
            key_padding = " " * (box_width - len(key) - 2)
            key_line = f"│ \x1b[35m{key}\x1b[0m{key_padding} │"
            self._move_cursor(popup_y + 3, popup_x)
            sys.stdout.write(key_line)
            
            self._move_cursor(popup_y + 4, popup_x)
            sys.stdout.write(bottom_border)
        else:
            self._move_cursor(popup_y + 3, popup_x)
            sys.stdout.write(bottom_border)
        
        # Restore cursor position
        self._restore_cursor()
        sys.stdout.flush()
    
    def clear_popup_box(self):
        """Clear the popup box from terminal."""
        terminal_width = self._get_terminal_width()
        box_width = 40  # Approximate width
        popup_x = terminal_width - box_width - 2
        popup_y = 2
        
        empty_space = " " * (box_width + 2)
        
        # Save cursor
        self._save_cursor()
        
        # Clear each line of the box
        for i in range(5):  # Clear 5 lines (enough for box)
            self._move_cursor(popup_y + i, popup_x)
            sys.stdout.write(empty_space)
        
        # Restore cursor
        self._restore_cursor()
        sys.stdout.flush()
    
    def _redraw_loop(self):
        """Continuously redraw the popup to keep it visible."""
        while not self.stop_redraw and self.active:
            if self.connection_info:
                name = self.connection_info.get("name", "")
                host = self.connection_info.get("host", "")
                user = self.connection_info.get("user", "")
                key = self.connection_info.get("key", "")
                
                key_display = f"Key: {key}" if key else ""
                self.show_popup_box(
                    server_name=name,
                    hostname=host,
                    user=user,
                    key=key_display
                )
            time.sleep(0.5)  # Redraw every 500ms
    
    def show(
        self,
        name: str,
        host: str,
        user: str,
        port: int,
        auth: str,
        key: Optional[str] = None
    ):
        """Show the connection panel with info."""
        self.connection_info = {
            "name": name,
            "host": host,
            "user": user,
            "port": port,
            "auth": auth,
            "key": key or "(default)"
        }
        self.active = True
        self.stop_redraw = False
        
        # Initial draw
        key_display = f"Key: {key}" if key else ""
        self.show_popup_box(
            server_name=name,
            hostname=host,
            user=user,
            key=key_display
        )
        
        # Start redraw thread to keep it sticky
        self.redraw_thread = threading.Thread(target=self._redraw_loop, daemon=True)
        self.redraw_thread.start()
    
    def hide(self):
        """Hide the connection panel."""
        # Stop redraw thread
        self.stop_redraw = True
        if self.redraw_thread and self.redraw_thread.is_alive():
            self.redraw_thread.join(timeout=1.0)
        
        # Clear the box
        if self.active:
            self.clear_popup_box()
        
        self.active = False
        self.connection_info = {}
    
    def print_connection_info(
        self,
        name: str,
        connection_string: str,
        key_name: Optional[str],
        auth_method: str
    ):
        """Print connection info in a simple format."""
        print()
        print("\x1b[1;36m╭─ SSH Connection Info ────────────────────\x1b[0m")
        print("\x1b[1;36m│\x1b[0m")
        print(f"\x1b[1;36m│\x1b[0m \x1b[1mConnecting to:\x1b[0m \x1b[32m{name}\x1b[0m")
        print(f"\x1b[1;36m│\x1b[0m \x1b[1mConnection:\x1b[0m    \x1b[33m{connection_string}\x1b[0m")
        
        if auth_method == "key":
            if key_name:
                print(f"\x1b[1;36m│\x1b[0m \x1b[1mUsing key:\x1b[0m     \x1b[35m{key_name}\x1b[0m")
            else:
                print(f"\x1b[1;36m│\x1b[0m \x1b[1mUsing key:\x1b[0m     \x1b[2m(default)\x1b[0m")
        else:
            print(f"\x1b[1;36m│\x1b[0m \x1b[1mAuth method:\x1b[0m   \x1b[35m{auth_method}\x1b[0m")
        
        print("\x1b[1;36m│\x1b[0m")
        print("\x1b[1;36m╰──────────────────────────────────────────\x1b[0m")
        print()
