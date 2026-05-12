"""
smart_copy.py - Smart copy options for entries
Adds right-click context menu and multiple copy formats
"""

import tkinter as tk
from tkinter import messagebox
import pyperclip

class SmartCopyMenu:
    """Smart copy context menu for entries"""
    
    def __init__(self, parent, tree, vault_manager, dark_mode=False):
        self.parent = parent
        self.tree = tree
        self.vault = vault_manager
        self.dark_mode = dark_mode
        
        # Bind right-click to tree
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Also bind Ctrl+C for quick copy
        self.tree.bind("<Control-c>", self.quick_copy_password)
        self.tree.bind("<Control-u>", self.quick_copy_username)
    
    def get_colors(self):
        """Get current colors based on dark mode"""
        if self.dark_mode:
            return {
                "bg": "#2d2d2d",
                "fg": "#ffffff",
                "hover": "#3d3d3d"
            }
        else:
            return {
                "bg": "#ffffff",
                "fg": "#000000",
                "hover": "#e5e7eb"
            }
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Get the item under cursor
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # Select the item
        self.tree.selection_set(item)
        self.tree.focus(item)
        
        # Get entry data
        entry_id = int(item)
        entry = self._get_entry_by_id(entry_id)
        
        if not entry:
            return
        
        colors = self.get_colors()
        
        # Create menu
        menu = tk.Menu(self.parent, tearoff=0, bg=colors["bg"], fg=colors["fg"])
        
        # Copy options header
        menu.add_command(label="📋 Copy Options", state="disabled")
        menu.add_separator()
        
        # Copy username
        menu.add_command(
            label="  Copy Username",
            command=lambda: self.copy_to_clipboard(entry.get('username', ''), "Username")
        )
        
        # Copy password
        menu.add_command(
            label="  Copy Password",
            command=lambda: self.copy_to_clipboard(entry.get('password', ''), "Password")
        )
        
        # Copy URL
        if entry.get('url'):
            menu.add_command(
                label="  Copy URL",
                command=lambda: self.copy_to_clipboard(entry.get('url', ''), "URL")
            )
        
        menu.add_separator()
        
        # Smart copy options
        menu.add_command(label="✨ Smart Copy Options", state="disabled")
        menu.add_separator()
        
        # Copy username:password
        username = entry.get('username', '')
        password = entry.get('password', '')
        if username and password:
            menu.add_command(
                label="  Copy Username:Password",
                command=lambda: self.copy_to_clipboard(f"{username}:{password}", "Username:Password")
            )
        
        # Copy as domain:password
        url = entry.get('url', '')
        if url and password:
            domain = self._extract_domain(url)
            menu.add_command(
                label=f"  Copy {domain}:password",
                command=lambda: self.copy_to_clipboard(f"{domain}:{password}", "Domain:Password")
            )
        
        # Copy for login form (username TAB password)
        if username and password:
            menu.add_command(
                label="  Copy for Login Form (username⏎password)",
                command=lambda: self.copy_to_clipboard(f"{username}\n{password}", "Login Form")
            )
        
        # Copy JSON format
        menu.add_separator()
        menu.add_command(
            label="📄 Copy as JSON",
            command=lambda: self._copy_as_json(entry)
        )
        
        # Copy CSV format
        menu.add_command(
            label="📊 Copy as CSV",
            command=lambda: self._copy_as_csv(entry)
        )
        
        # Separator
        menu.add_separator()
        
        # Edit option
        menu.add_command(
            label="✏️ Edit Entry",
            command=lambda: self._edit_entry(entry)
        )
        
        # Delete option
        menu.add_command(
            label="🗑️ Delete Entry",
            command=lambda: self._delete_entry(entry)
        )
        
        # Show menu at cursor position
        menu.post(event.x_root, event.y_root)
    
    def _get_entry_by_id(self, entry_id):
        """Get entry data by ID"""
        try:
            if self.vault and self.vault.db:
                return self.vault.db.get_entry(entry_id)
        except:
            pass
        
        # Fallback sample data
        sample_entries = {
            1: {'id': 1, 'title': 'Google', 'username': 'user@gmail.com', 'password': 'password123', 'url': 'https://google.com'},
            2: {'id': 2, 'title': 'GitHub', 'username': 'github_user', 'password': 'SecurePass456!', 'url': 'https://github.com'},
            3: {'id': 3, 'title': 'Netflix', 'username': 'netflix_user', 'password': 'MyPassword123', 'url': 'https://netflix.com'},
        }
        return sample_entries.get(entry_id)
    
    def _extract_domain(self, url):
        """Extract domain from URL"""
        import re
        # Remove protocol
        domain = re.sub(r'^https?://', '', url)
        # Remove path
        domain = domain.split('/')[0]
        # Remove www
        domain = re.sub(r'^www\.', '', domain)
        return domain
    
    def copy_to_clipboard(self, value, label):
        """Copy value to clipboard with feedback"""
        if not value:
            messagebox.showwarning("Nothing to Copy", f"No {label} to copy!")
            return
        
        pyperclip.copy(value)
        
        # Show temporary status if status label exists
        if hasattr(self.parent, 'status_label'):
            original_text = self.parent.status_label.cget('text')
            self.parent.status_label.config(text=f"✓ {label} copied to clipboard!")
            self.parent.root.after(2000, lambda: self.parent.status_label.config(text=original_text))
    
    def quick_copy_password(self, event):
        """Ctrl+C to copy password of selected entry"""
        selection = self.tree.selection()
        if not selection:
            return
        
        entry_id = int(selection[0])
        entry = self._get_entry_by_id(entry_id)
        if entry:
            self.copy_to_clipboard(entry.get('password', ''), "Password")
    
    def quick_copy_username(self, event):
        """Ctrl+U to copy username of selected entry"""
        selection = self.tree.selection()
        if not selection:
            return
        
        entry_id = int(selection[0])
        entry = self._get_entry_by_id(entry_id)
        if entry:
            self.copy_to_clipboard(entry.get('username', ''), "Username")
    
    def _copy_as_json(self, entry):
        """Copy entry as JSON"""
        import json
        json_str = json.dumps(entry, indent=2, default=str)
        pyperclip.copy(json_str)
        
        if hasattr(self.parent, 'status_label'):
            self.parent.status_label.config(text="✓ Copied as JSON!")
            self.parent.root.after(2000, lambda: self.parent.status_label.config(text="Ready"))
    
    def _copy_as_csv(self, entry):
        """Copy entry as CSV line"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([entry.get('title', ''), entry.get('username', ''), 
                        entry.get('password', ''), entry.get('url', '')])
        csv_str = output.getvalue().strip()
        pyperclip.copy(csv_str)
        
        if hasattr(self.parent, 'status_label'):
            self.parent.status_label.config(text="✓ Copied as CSV!")
            self.parent.root.after(2000, lambda: self.parent.status_label.config(text="Ready"))
    
    def _edit_entry(self, entry):
        """Open edit dialog for entry"""
        if hasattr(self.parent, 'add_entry'):
            # Call the edit method if it exists
            self.parent.add_entry()
    
    def _delete_entry(self, entry):
        """Delete entry"""
        if messagebox.askyesno("Confirm Delete", f"Delete '{entry.get('title', 'this entry')}'?"):
            if self.vault and self.vault.db:
                self.vault.db.delete_entry(entry['id'])
                # Refresh the tree
                if hasattr(self.parent, 'refresh_entries'):
                    self.parent.refresh_entries()


class QuickCopyBar:
    """Quick copy toolbar for selected entry"""
    
    def __init__(self, parent, vault_manager, dark_mode=False):
        self.parent = parent
        self.vault = vault_manager
        self.dark_mode = dark_mode
        self.current_entry_id = None
        
        self.frame = None
        self.setup_ui()
    
    def get_colors(self):
        """Get current colors based on dark mode"""
        if self.dark_mode:
            return {
                "bg": "#2d2d2d",
                "fg": "#ffffff",
                "btn_bg": "#3d3d3d"
            }
        else:
            return {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "btn_bg": "#e0e0e0"
            }
    
    def setup_ui(self):
        """Setup the quick copy toolbar"""
        colors = self.get_colors()
        
        self.frame = tk.Frame(self.parent, bg=colors["bg"], height=40)
        self.frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.frame.pack_propagate(False)
        
        # Buttons
        btn_style = {
            "bg": colors["btn_bg"],
            "fg": colors["fg"],
            "relief": tk.FLAT,
            "cursor": "hand2",
            "padx": 15,
            "pady": 5
        }
        
        self.username_btn = tk.Button(
            self.frame, text="📋 Copy Username",
            command=self.copy_username, **btn_style
        )
        self.username_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.password_btn = tk.Button(
            self.frame, text="🔑 Copy Password",
            command=self.copy_password, **btn_style
        )
        self.password_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.both_btn = tk.Button(
            self.frame, text="🔗 Copy Both",
            command=self.copy_both, **btn_style
        )
        self.both_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.totp_btn = tk.Button(
            self.frame, text="🔢 Copy TOTP",
            command=self.copy_totp, **btn_style
        )
        self.totp_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Status label
        self.status_label = tk.Label(
            self.frame, text="Select an entry to copy",
            bg=colors["bg"], fg=colors["fg"],
            font=("Segoe UI", 9)
        )
        self.status_label.pack(side=tk.RIGHT, padx=15)
        
        # Initially disable buttons
        self.set_enabled(False)
    
    def set_enabled(self, enabled):
        """Enable or disable all buttons"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.username_btn.config(state=state)
        self.password_btn.config(state=state)
        self.both_btn.config(state=state)
        self.totp_btn.config(state=state)
    
    def set_current_entry(self, entry_id, entry_data):
        """Set the currently selected entry"""
        self.current_entry_id = entry_id
        self.current_entry = entry_data
        self.set_enabled(True)
        
        # Update status
        self.status_label.config(text=f"Ready to copy: {entry_data.get('title', 'Unknown')}")
    
    def copy_username(self):
        """Copy username to clipboard"""
        if self.current_entry:
            username = self.current_entry.get('username', '')
            if username:
                pyperclip.copy(username)
                self._show_feedback("Username copied!")
            else:
                self._show_feedback("No username to copy", error=True)
    
    def copy_password(self):
        """Copy password to clipboard"""
        if self.current_entry:
            password = self.current_entry.get('password', '')
            if password:
                pyperclip.copy(password)
                self._show_feedback("Password copied!")
            else:
                self._show_feedback("No password to copy", error=True)
    
    def copy_both(self):
        """Copy both username and password"""
        if self.current_entry:
            username = self.current_entry.get('username', '')
            password = self.current_entry.get('password', '')
            if username and password:
                pyperclip.copy(f"{username}\t{password}")
                self._show_feedback("Username and password copied (tab separated)!")
            else:
                self._show_feedback("Missing username or password", error=True)
    
    def copy_totp(self):
        """Copy TOTP code if available"""
        if self.current_entry:
            totp_secret = self.current_entry.get('totp_secret', '')
            if totp_secret:
                try:
                    from ..features.totp import TOTP
                    totp = TOTP(secret=totp_secret)
                    code = totp.get_current_code()
                    pyperclip.copy(code)
                    self._show_feedback(f"TOTP code {code} copied!")
                except:
                    self._show_feedback("Invalid TOTP secret", error=True)
            else:
                self._show_feedback("No TOTP configured", error=True)
    
    def _show_feedback(self, message, error=False):
        """Show temporary feedback"""
        self.status_label.config(text=message)
        self.parent.root.after(2000, lambda: self.status_label.config(
            text=f"Ready to copy: {self.current_entry.get('title', 'Unknown')}"
        ))
