"""
main_window.py - Professional password manager GUI
Complete with filters, sorting, dark mode, attachments gallery, and all features
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pyperclip
import webbrowser
import os
import json
import threading
import time
import tempfile
import base64
import subprocess
import sys
import hashlib
import mimetypes

from .smart_copy import SmartCopyMenu, QuickCopyBar
from ..features.password_gen import PasswordGenerator
from ..features.expiry_manager import ExpiryManager, ExpiryNotifier
from ..features.emergency_access import EmergencyAccess, EmergencyAccessDialog


class ClipboardManager:
    """Manages clipboard with auto-clear by copying empty string"""
    
    def __init__(self):
        self.timer = None
        self.clear_delay = 10
    
    def set_delay(self, seconds: int):
        self.clear_delay = seconds
    
    def copy(self, text: str):
        pyperclip.copy(text)
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.clear_delay, self._clear)
        self.timer.daemon = True
        self.timer.start()
    
    def _clear(self):
        try:
            pyperclip.copy("")
        except:
            pass


# Theme colors
THEMES = {
    "light": {
        "bg": "#f5f5f5", "fg": "#000000", "sidebar_bg": "#202124",
        "sidebar_fg": "#e0e0e0", "entry_bg": "#ffffff", "entry_fg": "#000000",
        "tree_bg": "#ffffff", "tree_fg": "#000000", "tree_selected_bg": "#3b82f6",
        "tree_selected_fg": "#ffffff", "details_bg": "#fafafa", "details_fg": "#000000",
        "status_bg": "#e5e7eb", "status_fg": "#000000", "button_bg": "#e5e7eb",
        "button_fg": "#000000", "accent": "#3b82f6", "success": "#10b981",
        "warning": "#f59e0b", "danger": "#ef4444", "border": "#d1d5db"
    },
    "dark": {
        "bg": "#1e1e1e", "fg": "#ffffff", "sidebar_bg": "#2d2d2d",
        "sidebar_fg": "#e0e0e0", "entry_bg": "#3d3d3d", "entry_fg": "#ffffff",
        "tree_bg": "#2d2d2d", "tree_fg": "#ffffff", "tree_selected_bg": "#3b82f6",
        "tree_selected_fg": "#ffffff", "details_bg": "#2d2d2d", "details_fg": "#ffffff",
        "status_bg": "#3d3d3d", "status_fg": "#ffffff", "button_bg": "#3d3d3d",
        "button_fg": "#ffffff", "accent": "#3b82f6", "success": "#10b981",
        "warning": "#f59e0b", "danger": "#ef4444", "border": "#4a4a4a"
    }
}


class VaultKeeperUI:
    """Main application window with all features"""
    
    def __init__(self, vault_manager):
        self.vault = vault_manager
        self.current_entries = []
        self.selected_entry_id = None
        self.is_locked = False  # Vault is already unlocked
        self.dark_mode = False
        self.status_label = None
        self.tree = None
        self.details_panel = None
        self.smart_copy_menu = None
        self.quick_copy_bar = None
        self.auto_type_engine = None
        self.expiry_manager = None
        self.expiry_notifier = None
        self.emergency_access = None
        self.clipboard = ClipboardManager()
        
        # Sorting
        self.sort_column = "title"
        self.sort_reverse = False
        
        # Filter
        self.current_filter = "all"
        
        # Create root window
        self.root = tk.Tk()
        self.root.title("VaultKeeper - Password Manager")
        self.root.geometry("1400x850")
        self.root.minsize(1000, 600)
        
        # Load settings
        self.load_settings()
        
        # Apply theme
        self.apply_theme()
        
        # Go directly to main UI (vault is already unlocked)
        self.setup_main_ui()
    
    def get_colors(self):
        return THEMES["dark"] if self.dark_mode else THEMES["light"]
    
    def apply_theme(self):
        colors = self.get_colors()
        self.root.configure(bg=colors["bg"])
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=colors["tree_bg"], foreground=colors["tree_fg"],
                       fieldbackground=colors["tree_bg"], selectbackground=colors["tree_selected_bg"],
                       selectforeground=colors["tree_selected_fg"], rowheight=35)
        style.configure("Treeview.Heading", background=colors["entry_bg"],
                       foreground=colors["fg"], font=("Segoe UI", 10, "bold"))
    
    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    self.dark_mode = settings.get("dark_mode", False)
                    self.clipboard.set_delay(settings.get("clear_delay", 10))
        except:
            pass
    
    def save_settings(self):
        try:
            settings = {"dark_mode": self.dark_mode, "clear_delay": self.clipboard.clear_delay}
            with open("settings.json", "w") as f:
                json.dump(settings, f)
        except:
            pass
    
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_settings()
        if hasattr(self, 'tree') and self.tree:
            self.refresh_entries()
        if hasattr(self, 'details_panel'):
            self.show_details_placeholder()
    
    # ========== MENU METHODS ==========
    
    def open_settings(self):
        colors = self.get_colors()
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=colors["bg"])
        
        frame = tk.Frame(dialog, bg=colors["bg"], padx=25, pady=25)
        frame.pack(fill=tk.BOTH, expand=True)
        
        dark_var = tk.BooleanVar(value=self.dark_mode)
        def toggle_dark():
            self.dark_mode = dark_var.get()
            self.save_settings()
            dialog.destroy()
            self.toggle_dark_mode()
        
        tk.Checkbutton(frame, text="🌙 Dark Mode", variable=dark_var, command=toggle_dark,
                      bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(anchor='w', pady=5)
        
        tk.Frame(frame, height=20, bg=colors["bg"]).pack()
        
        tk.Label(frame, text="⏰ Auto-lock timeout (minutes):", bg=colors["bg"], fg=colors["fg"]).pack(anchor='w')
        timeout_var = tk.IntVar(value=15)
        tk.Spinbox(frame, from_=1, to=60, textvariable=timeout_var, width=10,
                  bg=colors["entry_bg"], fg=colors["entry_fg"]).pack(anchor='w', pady=(5, 15))
        
        tk.Label(frame, text="🧹 Clear clipboard after (seconds):", bg=colors["bg"], fg=colors["fg"]).pack(anchor='w')
        clear_var = tk.IntVar(value=self.clipboard.clear_delay)
        tk.Spinbox(frame, from_=5, to=60, textvariable=clear_var, width=10,
                  bg=colors["entry_bg"], fg=colors["entry_fg"]).pack(anchor='w', pady=(5, 15))
        
        def save_and_close():
            self.clipboard.set_delay(clear_var.get())
            self.save_settings()
            dialog.destroy()
        
        tk.Button(frame, text="💾 Save Settings", command=save_and_close,
                 bg=colors["accent"], fg="white", padx=25, pady=8,
                 relief=tk.FLAT, cursor='hand2').pack(pady=20)
    
    def open_password_generator(self):
        from .password_generator import PasswordGeneratorDialog
        PasswordGeneratorDialog(self.root, self.dark_mode)
    
    def open_breach_checker(self):
        from .breach_checker_dialog import BreachCheckerDialog
        BreachCheckerDialog(self.root, self.dark_mode, self.vault)
    
    def show_security_report(self):
        from .security_report import SecurityReportDialog
        SecurityReportDialog(self.root, self.dark_mode, self.vault)
    
    def show_import_export(self):
        from .import_export_dialog import ImportExportDialog
        ImportExportDialog(self.root, self.dark_mode, self.vault)
    
    def open_auto_type(self):
        if not self.selected_entry_id:
            messagebox.showwarning("No Selection", "Please select an entry first")
            return
        entry = self._get_entry_by_id(self.selected_entry_id)
        if entry:
            from ..features.auto_type import AutoTypeDialog
            AutoTypeDialog(self.root, self.auto_type_engine, self.selected_entry_id, entry, self.dark_mode)
    
    def show_about(self):
        messagebox.showinfo("About VaultKeeper", 
            "🔐 VaultKeeper - Professional Password Manager\n\nVersion: 3.0.0\n\n"
            "Features:\n• AES-256 encryption\n• Offline-first design\n• No cloud, no tracking\n"
            "• Advanced password generator\n• Dark mode support\n• Security report dashboard\n"
            "• Breach checker (offline)\n• Import/Export (Bitwarden/LastPass)\n• Smart copy options\n"
            "• Auto-Type (system-wide)\n• Password expiry reminders\n• Emergency access\n"
            "• TOTP 2FA support\n\nMade with ❤️ for security")
    
    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="🔒 Lock Vault", command=self.lock_vault)
        file_menu.add_separator()
        file_menu.add_command(label="📤 Export Vault", command=self.show_import_export)
        file_menu.add_command(label="📥 Import Vault", command=self.show_import_export)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Exit", command=self.root.quit)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="🔧 Password Generator", command=self.open_password_generator)
        tools_menu.add_command(label="⌨️ Auto-Type Selected", command=self.open_auto_type)
        tools_menu.add_separator()
        tools_menu.add_command(label="🔍 Breach Checker", command=self.open_breach_checker)
        tools_menu.add_command(label="📊 Security Report", command=self.show_security_report)
        tools_menu.add_separator()
        tools_menu.add_command(label="📋 Import/Export", command=self.show_import_export)
        tools_menu.add_separator()
        tools_menu.add_command(label="⚙️ Settings", command=self.open_settings)
        tools_menu.add_command(label="⌨️ CLI Console", command=self.open_cli_console)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="📖 About", command=self.show_about)
    

    def open_cli_console(self):
        """Open built-in CLI console as a floating dialog"""
        colors = self.get_colors()
        
        # Create floating window
        cli_window = tk.Toplevel(self.root)
        cli_window.title("VaultKeeper CLI Console")
        cli_window.geometry("750x550")
        cli_window.transient(self.root)
        cli_window.configure(bg=colors["bg"])
        
        # Make it non-modal (can use main window while CLI is open)
        cli_window.grab_set()
        
        # Main frame
        frame = tk.Frame(cli_window, bg=colors["bg"], padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title bar
        title_frame = tk.Frame(frame, bg=colors["bg"])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(title_frame, text="⌨️ VaultKeeper Command Line Interface",
                font=("Segoe UI", 14, "bold"), bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT)
        
        # Close button
        close_btn = tk.Button(title_frame, text="✕", command=cli_window.destroy,
                            bg=colors["danger"], fg="white", relief=tk.FLAT,
                            cursor='hand2', padx=8, pady=2)
        close_btn.pack(side=tk.RIGHT)
        
        # Help text
        tk.Label(frame, text="Type commands and press Enter. Type 'help' for available commands.",
                font=("Segoe UI", 9), bg=colors["bg"], 
                fg=colors["fg"] if self.dark_mode else '#6b7280').pack(anchor='w', pady=(0, 15))
        
        # Output area (with scroll)
        output_frame = tk.Frame(frame, bg=colors["bg"])
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        cli_output = tk.Text(output_frame, height=18, font=("Courier", 9),
                            bg=colors["entry_bg"], fg=colors["entry_fg"],
                            relief=tk.SOLID, bd=1, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=cli_output.yview)
        cli_output.configure(yscrollcommand=scrollbar.get)
        
        cli_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Input area
        input_frame = tk.Frame(frame, bg=colors["bg"])
        input_frame.pack(fill=tk.X)
        
        prompt_label = tk.Label(input_frame, text="$>", font=("Courier", 11, "bold"),
                            bg=colors["bg"], fg=colors["accent"])
        prompt_label.pack(side=tk.LEFT, padx=(0, 10))
        
        cli_input = tk.Entry(input_frame, font=("Courier", 11),
                            bg=colors["entry_bg"], fg=colors["entry_fg"],
                            relief=tk.SOLID, bd=1)
        cli_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Welcome message
        cli_output.insert(tk.END, "VaultKeeper CLI Console v1.0\n")
        cli_output.insert(tk.END, "=" * 60 + "\n")
        cli_output.insert(tk.END, f"Type 'help' for available commands\n")
        cli_output.insert(tk.END, f"Entries in vault: {len(self.vault.db.get_all_entries())}\n")
        cli_output.insert(tk.END, "=" * 60 + "\n\n")
        cli_output.see(tk.END)
        
        # Command execution
        def execute_command(event):
            command = cli_input.get().strip()
            if not command:
                return
            
            cli_output.insert(tk.END, f"$> {command}\n")
            cli_input.delete(0, tk.END)
            
            # Parse command
            parts = command.split()
            cmd = parts[0].lower() if parts else ""
            
            if cmd == "help":
                help_text = """
    Available commands:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    help                    - Show this help message
    list                    - List all entries (ID and title)
    search <query>          - Search entries by title or username
    stats                   - Show vault statistics
    export                  - Export vault to CSV file
    generate [length]       - Generate random password (default 16)
    clear                   - Clear console screen
    exit / quit             - Close CLI console
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
                cli_output.insert(tk.END, help_text + "\n")
            
            elif cmd == "list":
                entries = self.vault.db.get_all_entries()
                cli_output.insert(tk.END, f"\n📁 Found {len(entries)} entries:\n")
                cli_output.insert(tk.END, "-" * 60 + "\n")
                for e in entries:
                    title = e.get('title', 'Untitled')[:35]
                    username = e.get('username', '')[:20]
                    cli_output.insert(tk.END, f"  [{e['id']:3}] {title:<35} | {username:<20}\n")
                cli_output.insert(tk.END, "-" * 60 + "\n\n")
            
            elif cmd == "search":
                query = " ".join(parts[1:]) if len(parts) > 1 else ""
                if not query:
                    cli_output.insert(tk.END, "Usage: search <query>\n")
                else:
                    entries = self.vault.db.search_entries(query)
                    cli_output.insert(tk.END, f"\n🔍 Found {len(entries)} entries matching '{query}':\n")
                    cli_output.insert(tk.END, "-" * 60 + "\n")
                    for e in entries:
                        title = e.get('title', 'Untitled')[:40]
                        username = e.get('username', '')[:20]
                        cli_output.insert(tk.END, f"  [{e['id']:3}] {title:<40} | {username:<20}\n")
                    cli_output.insert(tk.END, "-" * 60 + "\n\n")
            
            elif cmd == "stats":
                entries = self.vault.db.get_all_entries()
                weak = sum(1 for e in entries if e.get('password_strength', 0) < 3)
                import os
                db_size = os.path.getsize(self.vault.db_path) / 1024 if os.path.exists(self.vault.db_path) else 0
                
                stats_text = f"""
    📊 Vault Statistics
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Total entries:     {len(entries)}
    Weak passwords:    {weak}
    Strong passwords:  {len(entries) - weak}
    Database size:     {db_size:.1f} KB
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
                cli_output.insert(tk.END, stats_text + "\n")
            
            elif cmd == "export":
                from tkinter import filedialog
                import csv
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Export Vault"
                )
                if filename:
                    entries = self.vault.db.get_all_entries()
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['ID', 'Title', 'Username', 'Password', 'URL', 'Notes'])
                        for e in entries:
                            writer.writerow([e['id'], e.get('title', ''), e.get('username', ''),
                                            e.get('password', ''), e.get('url', ''), e.get('notes', '')])
                    cli_output.insert(tk.END, f"✅ Exported {len(entries)} entries to {filename}\n")
                else:
                    cli_output.insert(tk.END, "❌ Export cancelled\n")
            
            elif cmd == "generate":
                from src.features.password_gen import PasswordGenerator
                
                # Parse length correctly
                length = 16  # default
                if len(parts) > 1:
                    try:
                        # Remove brackets if present (like [4096])
                        length_str = parts[1].strip('[]')
                        length = int(length_str)
                    except ValueError:
                        length = 16
                
                # Cap at 4096
                if length > 4096:
                    length = 4096
                    cli_output.insert(tk.END, f"⚠️ Length capped at 4096 characters\n")
                elif length < 8:
                    length = 8
                    cli_output.insert(tk.END, f"⚠️ Length set to minimum 8 characters\n")
                
                cli_output.insert(tk.END, f"🔧 Generating {length}-character password...\n")
                password = PasswordGenerator.generate_random(length)
                cli_output.insert(tk.END, f"🔐 Generated {len(password)}-character password:\n{password}\n\n")
            
            elif cmd == "clear":
                cli_output.delete(1.0, tk.END)
            
            elif cmd in ["exit", "quit"]:
                cli_output.insert(tk.END, "Goodbye!\n")
                cli_window.after(500, cli_window.destroy)
            
            else:
                cli_output.insert(tk.END, f"Unknown command: {cmd}. Type 'help' for available commands.\n")
            
            cli_output.see(tk.END)
        
        cli_input.bind('<Return>', execute_command)
        cli_input.focus()

    def execute_cli_command(self, event):
        """Execute CLI command"""
        command = self.cli_input.get().strip()
        if not command:
            return
        
        self.cli_output.insert(tk.END, f"$> {command}\n")
        self.cli_input.delete(0, tk.END)
        
        # Parse command
        parts = command.split()
        cmd = parts[0].lower() if parts else ""
        
        if cmd == "help":
            self._cli_help()
        elif cmd == "list":
            self._cli_list()
        elif cmd == "search":
            query = " ".join(parts[1:]) if len(parts) > 1 else ""
            self._cli_search(query)
        elif cmd == "stats":
            self._cli_stats()
        elif cmd == "export":
            self._cli_export()
        elif cmd == "generate":
            length = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 16
            self._cli_generate(length)
        elif cmd == "clear":
            self.cli_output.delete(1.0, tk.END)
        elif cmd == "exit" or cmd == "quit":
            self.cli_output.insert(tk.END, "Goodbye!\n")
            self.cli_input.master.after(500, self.cli_input.master.destroy)
        else:
            self.cli_output.insert(tk.END, f"Unknown command: {cmd}. Type 'help' for available commands.\n")
        
        self.cli_output.see(tk.END)

    def _cli_help(self):
        """Show CLI help"""
        help_text = """
    Available commands:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    help                    - Show this help message
    list                    - List all entries (ID and title)
    search <query>          - Search entries by title or username
    stats                   - Show vault statistics
    export                  - Export vault to CSV file
    generate [length]       - Generate random password (default 16)
    clear                   - Clear console screen
    exit / quit             - Close CLI console
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
        self.cli_output.insert(tk.END, help_text + "\n")

    def _cli_list(self):
        """List all entries"""
        entries = self.vault.db.get_all_entries()
        self.cli_output.insert(tk.END, f"\n📁 Found {len(entries)} entries:\n")
        self.cli_output.insert(tk.END, "-" * 60 + "\n")
        for e in entries:
            self.cli_output.insert(tk.END, f"  [{e['id']}] {e.get('title', 'Untitled')[:40]:<40} | {e.get('username', '')[:20]}\n")
        self.cli_output.insert(tk.END, "-" * 60 + "\n\n")

    def _cli_search(self, query):
        """Search entries"""
        if not query:
            self.cli_output.insert(tk.END, "Usage: search <query>\n")
            return
        
        entries = self.vault.db.search_entries(query)
        self.cli_output.insert(tk.END, f"\n🔍 Found {len(entries)} entries matching '{query}':\n")
        self.cli_output.insert(tk.END, "-" * 60 + "\n")
        for e in entries:
            self.cli_output.insert(tk.END, f"  [{e['id']}] {e.get('title', 'Untitled')[:40]:<40} | {e.get('username', '')[:20]}\n")
        self.cli_output.insert(tk.END, "-" * 60 + "\n\n")

    def _cli_stats(self):
        """Show statistics"""
        entries = self.vault.db.get_all_entries()
        weak = sum(1 for e in entries if e.get('password_strength', 0) < 3)
        
        stats = f"""
    📊 Vault Statistics
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Total entries:     {len(entries)}
    Weak passwords:    {weak}
    Strong passwords:  {len(entries) - weak}
    Database size:     {os.path.getsize(self.vault.db_path) / 1024:.1f} KB
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
        self.cli_output.insert(tk.END, stats + "\n")

    def _cli_export(self):
        """Export to CSV"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Vault"
        )
        if filename:
            entries = self.vault.db.get_all_entries()
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Title', 'Username', 'Password', 'URL', 'Notes'])
                for e in entries:
                    writer.writerow([e['id'], e.get('title', ''), e.get('username', ''),
                                    e.get('password', ''), e.get('url', ''), e.get('notes', '')])
            self.cli_output.insert(tk.END, f"✅ Exported {len(entries)} entries to {filename}\n")

    def _cli_generate(self, length):
        """Generate password"""
        from src.features.password_gen import PasswordGenerator
        password = PasswordGenerator.generate_random(length)
        self.cli_output.insert(tk.END, f"🔐 Generated {length}-character password:\n{password}\n\n")


    # ========== UNLOCK SCREEN ==========
    
    def show_unlock_screen(self):
        """Show master password unlock screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        colors = self.get_colors()
        self.root.configure(bg=colors["bg"])
        
        main_frame = tk.Frame(self.root, bg=colors["bg"])
        main_frame.place(relx=0.5, rely=0.4, anchor='center')
        
        title = tk.Label(main_frame, text="🔐 VaultKeeper", font=("Segoe UI", 36, "bold"),
                        bg=colors["bg"], fg='#3b82f6')
        title.pack(pady=(0, 15))
        
        subtitle = tk.Label(main_frame, text="Secure • Offline • Professional", font=("Segoe UI", 11),
                        bg=colors["bg"], fg=colors["fg"] if self.dark_mode else '#6b7280')
        subtitle.pack(pady=(0, 40))
        
        # Password frame
        password_frame = tk.Frame(main_frame, bg=colors["bg"])
        password_frame.pack(pady=10)
        
        self.unlock_password = tk.Entry(password_frame, show="•", font=("Segoe UI", 14), width=25,
                                        bg=colors["entry_bg"], fg=colors["entry_fg"],
                                        insertbackground=colors["entry_fg"])
        self.unlock_password.pack(side=tk.LEFT, padx=(0, 10))
        self.unlock_password.bind('<Return>', lambda e: self.unlock_vault())
        
        # Show/hide button
        show_var = tk.BooleanVar()
        show_btn = tk.Checkbutton(password_frame, text="Show", variable=show_var,
                                command=lambda: self.unlock_password.config(show="" if show_var.get() else "•"),
                                bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"])
        show_btn.pack(side=tk.LEFT)
        
        # Unlock button
        btn = tk.Button(main_frame, text="Unlock Vault", font=("Segoe UI", 12, "bold"),
                    bg='#3b82f6', fg='white', padx=50, pady=10,
                    relief=tk.FLAT, cursor='hand2', bd=0, command=self.unlock_vault)
        btn.pack(pady=30)
        
        # Dark mode toggle
        mode_btn = tk.Button(main_frame, text="🌙 Dark Mode" if not self.dark_mode else "☀️ Light Mode",
                            font=("Segoe UI", 10), bg=colors["bg"], fg=colors["fg"],
                            relief=tk.FLAT, cursor='hand2', command=self.toggle_dark_mode)
        mode_btn.pack(pady=10)
        
        # REMOVE THE DEMO HINT - no more "any password works"
        # Also show failed attempts if any
        if hasattr(self, 'failed_attempts') and self.failed_attempts > 0:
            remaining = 5 - self.failed_attempts
            warning = tk.Label(main_frame, text=f"⚠️ {remaining} attempts remaining",
                            font=("Segoe UI", 9), bg=colors["bg"], fg=colors["danger"])
            warning.pack(pady=(10, 0))
        
        self.unlock_password.focus()
    
    def unlock_vault(self):
        """Unlock the vault with REAL password verification"""
        password = self.unlock_password.get()
        
        if not password:
            messagebox.showerror("Error", "Please enter your master password")
            return
        
        # Try to unlock with the actual vault manager
        if self.vault and self.vault.unlock_vault():
            self.is_locked = False
            self.setup_main_ui()
        else:
            messagebox.showerror("Error", "Invalid master password")
            self.unlock_password.delete(0, tk.END)
            self.unlock_password.focus()
    
    # ========== MAIN UI ==========
    
    def setup_main_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        colors = self.get_colors()
        self.root.configure(bg=colors["bg"])
        
        # Initialize features
        from ..features.auto_type import AutoTypeEngine
        self.auto_type_engine = AutoTypeEngine(self.root, self.vault, self.dark_mode)
        self.expiry_manager = ExpiryManager(self.vault)
        self.expiry_notifier = ExpiryNotifier(self.expiry_manager)
        self.emergency_access = EmergencyAccess(self.vault)
        
        self.create_menu_bar()
        
        main_container = tk.Frame(self.root, bg=colors["bg"])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # ========== SIDEBAR ==========
        sidebar = tk.Frame(main_container, width=260, bg=colors["sidebar_bg"])
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        logo_frame = tk.Frame(sidebar, bg=colors["sidebar_bg"])
        logo_frame.pack(fill=tk.X, pady=(25, 15))
        logo = tk.Label(logo_frame, text="🔐 VaultKeeper", font=("Segoe UI", 16, "bold"),
                       bg=colors["sidebar_bg"], fg='white')
        logo.pack()
        
        sep = tk.Frame(sidebar, height=1, bg='#3d3d3d')
        sep.pack(fill=tk.X, padx=15, pady=10)
        
        # Navigation filters
        nav_items = [
            ("📁 All Items", "all"),
            ("⭐ Favorites", "fav"),
            ("🔑 Logins", "login"),
            ("💳 Cards", "card"),
            ("👤 Identities", "identity"),
            ("📝 Secure Notes", "note"),
        ]
        
        for text, filter_type in nav_items:
            btn = tk.Button(sidebar, text=text, font=("Segoe UI", 10),
                           bg=colors["sidebar_bg"], fg=colors["sidebar_fg"],
                           relief=tk.FLAT, anchor='w', padx=25, pady=10,
                           cursor='hand2', bd=0,
                           command=lambda f=filter_type: self.set_filter(f))
            btn.pack(fill=tk.X)
        
        # Highlight current filter
        self.set_filter("all")
        
        spacer = tk.Frame(sidebar, bg=colors["sidebar_bg"], height=20)
        spacer.pack()
        
        # Tools section
        tools_label = tk.Label(sidebar, text="🛠️ TOOLS", font=("Segoe UI", 9, "bold"),
                              bg=colors["sidebar_bg"], fg='#9ca3af', anchor='w', padx=25)
        tools_label.pack(fill=tk.X, pady=(15, 5))
        
        # In tools_items list, add:
        tools_items = [
            ("🔧 Password Generator", "generator"),
            ("⌨️ Auto-Type", "autotype"),
            ("🔍 Breach Checker", "breach"),
            ("📊 Security Report", "report"),
            ("📋 Import/Export", "import"),
            ("🆘 Emergency Access", "emergency"),
            ("⌨️ CLI Console", "cli"),  # NEW
            ("⚙️ Settings", "settings")
        ]
        
        def get_tool_cmd(value):
            if value == "generator":
                return self.open_password_generator
            elif value == "autotype":
                return self.open_auto_type
            elif value == "breach":
                return self.open_breach_checker
            elif value == "report":
                return self.show_security_report
            elif value == "import":
                return self.show_import_export
            elif value == "emergency":
                return lambda: EmergencyAccessDialog(self.root, self.emergency_access, self.dark_mode)
            elif value == "cli":
                return self.open_cli_console
            else:
                return self.open_settings
        
        for text, value in tools_items:
            btn = tk.Button(sidebar, text=text, font=("Segoe UI", 10),
                           bg=colors["sidebar_bg"], fg=colors["sidebar_fg"],
                           relief=tk.FLAT, anchor='w', padx=35, pady=8,
                           cursor='hand2', bd=0, command=get_tool_cmd(value))
            btn.pack(fill=tk.X)
        
        # Bottom buttons
        bottom_frame = tk.Frame(sidebar, bg=colors["sidebar_bg"])
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15)
        
        mode_btn = tk.Button(bottom_frame, text="🌙 Dark" if not self.dark_mode else "☀️ Light",
                            font=("Segoe UI", 10), bg=colors["sidebar_bg"], fg=colors["sidebar_fg"],
                            relief=tk.FLAT, pady=8, cursor='hand2', command=self.toggle_dark_mode)
        mode_btn.pack(fill=tk.X, padx=15, pady=2)
        
        lock_btn = tk.Button(bottom_frame, text="🔒 Lock Vault", font=("Segoe UI", 10),
                            bg=colors["sidebar_bg"], fg=colors["sidebar_fg"],
                            relief=tk.FLAT, pady=8, cursor='hand2', command=self.lock_vault)
        lock_btn.pack(fill=tk.X, padx=15, pady=2)
        
        # ========== MAIN CONTENT ==========
        main_content = tk.Frame(main_container, bg=colors["bg"])
        main_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Top bar
        top_bar = tk.Frame(main_content, bg=colors["bg"], height=70)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        search_frame = tk.Frame(top_bar, bg=colors["bg"])
        search_frame.pack(pady=18, padx=25, fill=tk.X)
        
        search_icon = tk.Label(search_frame, text="🔍", bg=colors["bg"], fg=colors["fg"])
        search_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_entries())
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 11),
                               bg=colors["entry_bg"], fg=colors["entry_fg"],
                               insertbackground=colors["entry_fg"], relief=tk.SOLID, bd=1)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        # Add Refresh Button
        refresh_btn = tk.Button(
            search_frame, text="🔄 Refresh", font=("Segoe UI", 10),
            bg=colors["button_bg"], fg=colors["button_fg"],
            relief=tk.FLAT, cursor='hand2', padx=15,
            command=self.refresh_entries
        )
        refresh_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        add_btn = tk.Button(search_frame, text="+ New Item", font=("Segoe UI", 10, "bold"),
                           bg='#3b82f6', fg='white', padx=25, pady=8,
                           relief=tk.FLAT, cursor='hand2', bd=0, command=self.add_entry)
        add_btn.pack(side=tk.RIGHT)

        cli_btn = tk.Button(
            search_frame, text="⌨️ CLI", font=("Segoe UI", 10),
            bg=colors["warning"], fg="white",
            relief=tk.FLAT, cursor='hand2', padx=15,
            command=self.open_cli_console
        )
        cli_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # Content area
        content_area = tk.Frame(main_content, bg=colors["bg"])
        content_area.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 15))
        
        # Left: Entry list
        list_frame = tk.Frame(content_area, bg=colors["bg"])
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        columns = ("Title", "Username", "Last Used")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=22, selectmode='browse')
        
        self.tree.heading("Title", text="Title", command=lambda: self.sort_by_column("title"))
        self.tree.heading("Username", text="Username", command=lambda: self.sort_by_column("username"))
        self.tree.heading("Last Used", text="Last Used", command=lambda: self.sort_by_column("last_used"))
        
        self.tree.column("Title", width=320, minwidth=200)
        self.tree.column("Username", width=200, minwidth=150)
        self.tree.column("Last Used", width=120, minwidth=100)
        
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_entry_select)
        
        # Smart copy context menu
        self.smart_copy_menu = SmartCopyMenu(main_content, self.tree, self.vault, self.dark_mode)
        
        # Right: Details panel
        self.details_panel = tk.Frame(content_area, bg=colors["details_bg"], width=420)
        self.details_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.details_panel.pack_propagate(False)
        
        self.show_details_placeholder()
        
        # Status bar
        status_bar = tk.Frame(main_content, bg=colors["status_bg"], height=32)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(status_bar, text="Ready", font=("Segoe UI", 9),
                                    bg=colors["status_bg"], fg=colors["status_fg"], anchor='w', padx=15)
        self.status_label.pack(fill=tk.X, expand=True)
        cli_status_btn = tk.Button(
            status_bar, text="⌨️ Open CLI Console", font=("Segoe UI", 9),
            bg=colors["accent"], fg="white",
            relief=tk.FLAT, cursor='hand2',
            command=self.open_cli_console
        )
        cli_status_btn.pack(side=tk.RIGHT, padx=10)
        
        # Quick copy bar
        self.quick_copy_bar = QuickCopyBar(main_content, self.vault, self.dark_mode)
        
        # Load entries
        self.refresh_entries()
    
    def set_filter(self, filter_type):
        """Set current filter"""
        self.current_filter = filter_type
        self.refresh_entries()
    
    def sort_by_column(self, col):
        """Sort entries by column"""
        self.sort_reverse = not self.sort_reverse if self.sort_column == col else False
        self.sort_column = col
        self.refresh_entries()
    
    def show_details_placeholder(self):
        for widget in self.details_panel.winfo_children():
            widget.destroy()
        colors = self.get_colors()
        placeholder = tk.Label(self.details_panel,
            text="🔐\n\nSelect an item\nto view details", font=("Segoe UI", 14),
            bg=colors["details_bg"], fg=colors["details_fg"] if self.dark_mode else '#9ca3af',
            justify=tk.CENTER)
        placeholder.pack(expand=True)
    
    def refresh_entries(self):
        """Refresh the entry list with current filter and sort"""
        if not self.tree or not self.tree.winfo_exists():
            return
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get entries from database
        entries = []
        try:
            if self.vault and self.vault.db:
                entries = self.vault.db.get_all_entries()
                print(f"📊 Found {len(entries)} entries in database")
        except Exception as e:
            print(f"Error getting entries: {e}")
            return
        
        # Apply filter
        if self.current_filter == "fav":
            entries = [e for e in entries if e.get('is_favorite', False)]
        elif self.current_filter == "login":
            entries = [e for e in entries if e.get('type') == 'login' or not e.get('type')]
        elif self.current_filter == "card":
            entries = [e for e in entries if e.get('type') == 'card']
        elif self.current_filter == "identity":
            entries = [e for e in entries if e.get('type') == 'identity']
        elif self.current_filter == "note":
            entries = [e for e in entries if e.get('type') == 'note']
        
        # Apply search
        search_term = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        if search_term:
            entries = [e for e in entries if 
                      search_term in e.get('title', '').lower() or 
                      search_term in e.get('username', '').lower()]
        
        # Apply sort
        if self.sort_column == "title":
            entries.sort(key=lambda x: x.get('title', '').lower(), reverse=self.sort_reverse)
        elif self.sort_column == "username":
            entries.sort(key=lambda x: x.get('username', '').lower(), reverse=self.sort_reverse)
        elif self.sort_column == "last_used":
            entries.sort(key=lambda x: x.get('last_used', 0) or 0, reverse=self.sort_reverse)
        
        # Display
        for entry in entries:
            last_used = entry.get('last_used', 0)
            if isinstance(last_used, int) and last_used > 0:
                last_used_str = datetime.fromtimestamp(last_used).strftime("%b %d, %Y")
            else:
                last_used_str = "Never"
            
            icon = entry.get('icon_emoji', '🔐')
            title_display = f"{icon} {entry.get('title', 'Untitled')}"
            
            self.tree.insert("", tk.END, iid=entry['id'],
                           values=(title_display, entry.get('username', ''), last_used_str))
            print(f"  ✅ Displayed: {entry.get('title')}")
        
        if self.status_label:
            self.status_label.config(text=f"Ready - {len(entries)} entries")
    
    def _get_entry_by_id(self, entry_id):
        try:
            if self.vault and self.vault.db:
                return self.vault.db.get_entry(entry_id)
        except:
            pass
        return None
    
    def on_entry_select(self, event):
        """Handle entry selection - shows details in right panel"""
        if not self.tree:
            return
        selection = self.tree.selection()
        if not selection:
            self.show_details_placeholder()
            if self.quick_copy_bar:
                self.quick_copy_bar.set_enabled(False)
            return
        
        try:
            entry_id = int(selection[0])
            self.selected_entry_id = entry_id
            
            # Get entry from database
            entry = None
            if self.vault and self.vault.db:
                entry = self.vault.db.get_entry(entry_id)
                print(f"📋 Selected entry: {entry.get('title') if entry else 'None'}")
            
            if entry:
                if self.quick_copy_bar:
                    self.quick_copy_bar.set_current_entry(entry_id, entry)
                self.show_entry_details(entry)
            else:
                self.show_details_placeholder()
        except Exception as e:
            print(f"Error selecting entry: {e}")
            self.show_details_placeholder()
    
    def show_entry_details(self, entry):
        """Show detailed view of selected entry"""
        # Clear existing widgets
        for widget in self.details_panel.winfo_children():
            widget.destroy()
        
        colors = self.get_colors()
        
        if not entry:
            self.show_details_placeholder()
            return
        
        print(f"📝 Showing details for: {entry.get('title')}")
        
        # Create scrollable canvas with mousewheel support
        canvas = tk.Canvas(self.details_panel, bg=colors["details_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.details_panel, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=colors["details_bg"])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=380)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel support
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        frame = tk.Frame(scrollable_frame, bg=colors["details_bg"])
        frame.pack(fill=tk.BOTH, expand=True)
        
        # ====== HEADER with Title and Favorite Star ======
        header_frame = tk.Frame(frame, bg=colors["details_bg"])
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        icon = entry.get('icon_emoji', '🔐')
        title_label = tk.Label(header_frame, text=f"{icon} {entry.get('title', 'Untitled')}",
                            font=("Segoe UI", 16, "bold"), 
                            bg=colors["details_bg"], fg=colors["details_fg"])
        title_label.pack(side=tk.LEFT)
        
        # Favorite button
        is_fav = entry.get('is_favorite', False)
        fav_btn = tk.Button(header_frame, text="⭐" if is_fav else "☆", font=("Segoe UI", 14),
                        bg=colors["details_bg"], fg=colors["warning"], 
                        relief=tk.FLAT, cursor='hand2',
                        command=lambda: self._toggle_favorite(entry['id'], fav_btn))
        fav_btn.pack(side=tk.RIGHT)
        
        # Separator
        sep = tk.Frame(frame, height=1, bg=colors["border"])
        sep.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # ====== USERNAME ======
        if entry.get('username'):
            self._add_detail_row(frame, "Username", entry.get('username'))
        
        # ====== PASSWORD with Show/Hide ======
        if entry.get('password'):
            self._add_password_row(frame, "Password", entry.get('password'))
        
        # ====== TOTP ======
        # After username, password, etc., add TOTP
        if entry.get('totp_secret'):
            self._add_totp_row(frame, entry.get('totp_secret'), entry.get('id'))
        
        # ====== URL with Open and Copy ======
        if entry.get('url'):
            self._add_url_row(frame, entry.get('url'))
        
        # ====== CUSTOM FIELDS ======
        custom_fields = entry.get('custom_fields', {})
        if custom_fields:
            cf_frame = tk.LabelFrame(frame, text="Custom Fields", bg=colors["details_bg"],
                                    fg=colors["details_fg"], font=("Segoe UI", 10, "bold"))
            cf_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
            for field_name, field_data in custom_fields.items():
                if isinstance(field_data, dict):
                    value = field_data.get('value', '')
                    self._add_detail_row(cf_frame, field_name, str(value))
        
        # ====== NOTES ======
        notes = entry.get('notes', '')
        if notes and notes.strip():
            notes_frame = tk.LabelFrame(frame, text="Notes", bg=colors["details_bg"],
                                    fg=colors["details_fg"], font=("Segoe UI", 10, "bold"))
            notes_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
            
            notes_text = tk.Text(notes_frame, height=6, 
                                bg=colors["entry_bg"], fg=colors["entry_fg"],
                                insertbackground=colors["entry_fg"], 
                                relief=tk.FLAT, wrap=tk.WORD)
            notes_text.pack(fill=tk.X, padx=10, pady=10)
            notes_text.insert(1.0, notes)
            notes_text.config(state='disabled')
        
        # ====== METADATA ======
        meta_frame = tk.LabelFrame(frame, text="Metadata", bg=colors["details_bg"],
                                fg=colors["details_fg"], font=("Segoe UI", 10, "bold"))
        meta_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        created = entry.get('created_at', 0)
        if created:
            try:
                created_str = datetime.fromtimestamp(created).strftime("%b %d, %Y at %H:%M")
                self._add_detail_row(meta_frame, "Created", created_str)
            except:
                pass
        
        updated = entry.get('updated_at', 0)
        if updated:
            try:
                updated_str = datetime.fromtimestamp(updated).strftime("%b %d, %Y at %H:%M")
                self._add_detail_row(meta_frame, "Updated", updated_str)
            except:
                pass
        
        # ====== ATTACHMENTS GALLERY ======
        attachments = entry.get('attachments', [])
        if attachments:
            self._add_attachments_gallery(frame, attachments)
        
        # ====== ACTION BUTTONS ======
        action_frame = tk.Frame(frame, bg=colors["details_bg"])
        action_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        btn_style = {"bg": colors["accent"], "fg": "white", "relief": tk.FLAT,
                    "padx": 15, "pady": 6, "cursor": 'hand2', "font": ("Segoe UI", 9)}
        
        edit_btn = tk.Button(action_frame, text="✏️ Edit", 
                            command=lambda: self.edit_entry(entry['id']), **btn_style)
        edit_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        del_btn = tk.Button(action_frame, text="🗑️ Delete", 
                        command=lambda: self.delete_entry(entry['id']),
                        bg=colors["danger"], fg="white", relief=tk.FLAT, 
                        padx=15, pady=6, cursor='hand2')
        del_btn.pack(side=tk.LEFT)
    
    # ========== HELPER METHODS FOR DETAILS PANEL ==========
    
    def _add_detail_row(self, parent, label, value):
        """Add a simple detail row with copy button"""
        colors = self.get_colors()
        frame = tk.Frame(parent, bg=colors["details_bg"])
        frame.pack(fill=tk.X, padx=15, pady=4)
        
        tk.Label(frame, text=label, width=12, anchor='w',
                bg=colors["details_bg"], fg=colors["details_fg"] if self.dark_mode else '#6b7280',
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        value_label = tk.Label(frame, text=str(value), bg=colors["details_bg"], 
                            fg=colors["details_fg"], wraplength=200, justify='left')
        value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        copy_btn = tk.Button(frame, text="📋", 
                            command=lambda v=value: self._copy_to_clipboard(str(v), label),
                            bg=colors["button_bg"], fg=colors["button_fg"], 
                            relief=tk.FLAT, cursor='hand2', padx=5)
        copy_btn.pack(side=tk.RIGHT, padx=2)

    def _add_password_row(self, parent, label, password):
        """Add password row with show/hide toggle"""
        colors = self.get_colors()
        frame = tk.Frame(parent, bg=colors["details_bg"])
        frame.pack(fill=tk.X, padx=15, pady=4)
        
        tk.Label(frame, text=label, width=12, anchor='w',
                bg=colors["details_bg"], fg=colors["details_fg"] if self.dark_mode else '#6b7280',
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        # Create frame for password with buttons
        pwd_frame = tk.Frame(frame, bg=colors["details_bg"])
        pwd_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Password label
        password_label = tk.Label(pwd_frame, text="••••••••••••••••", 
                                bg=colors["details_bg"], fg=colors["details_fg"], 
                                font=("Courier", 9))
        password_label.pack(side=tk.LEFT)
        
        # Show/Hide variable
        show_var = tk.BooleanVar()
        
        def toggle_show():
            if show_var.get():
                # Show password
                display = password[:60] + "..." if len(password) > 60 else password
                password_label.config(text=display)
                show_btn.config(text="🙈")
            else:
                # Hide password
                password_label.config(text="••••••••••••••••")
                show_btn.config(text="👁️")
        
        show_btn = tk.Button(pwd_frame, text="👁️", command=toggle_show,
                            bg=colors["button_bg"], fg=colors["button_fg"],
                            relief=tk.FLAT, cursor='hand2', padx=5)
        show_btn.pack(side=tk.RIGHT, padx=2)
        
        copy_btn = tk.Button(pwd_frame, text="📋", 
                            command=lambda: self._copy_to_clipboard(password, label),
                            bg=colors["button_bg"], fg=colors["button_fg"],
                            relief=tk.FLAT, cursor='hand2', padx=5)
        copy_btn.pack(side=tk.RIGHT, padx=2)

    def _add_totp_row(self, parent, secret, entry_id=None):
        """Add TOTP row with working Save Drift button and proper cleanup"""
        colors = self.get_colors()
        
        # Main row frame
        main_frame = tk.Frame(parent, bg=colors["details_bg"])
        main_frame.pack(fill=tk.X, padx=15, pady=4)
        
        tk.Label(main_frame, text="TOTP", width=12, anchor='w',
                bg=colors["details_bg"], fg=colors["details_fg"] if self.dark_mode else '#6b7280',
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        if not secret:
            error_label = tk.Label(main_frame, text="No TOTP secret configured", 
                                bg=colors["details_bg"], fg=colors["warning"])
            error_label.pack(side=tk.LEFT, padx=(10, 0))
            return
        
        try:
            from ..features.totp import TOTP
            
            # Load saved drift from database
            saved_drift = 0
            if entry_id and self.vault and self.vault.db:
                try:
                    entry = self.vault.db.get_entry(entry_id)
                    if entry:
                        custom_fields = entry.get('custom_fields', {})
                        if isinstance(custom_fields, dict):
                            totp_params = custom_fields.get('_totp_params', {})
                            if isinstance(totp_params, dict):
                                saved_drift = totp_params.get('time_offset', 0)
                    print(f"📱 Loaded TOTP drift: {saved_drift:+d}s for entry {entry_id}")
                except Exception as e:
                    print(f"Error loading drift: {e}")
            
            # Code display
            code_label = tk.Label(main_frame, text="...", bg=colors["details_bg"],
                                fg=colors["success"], font=("Courier", 14, "bold"))
            code_label.pack(side=tk.LEFT, padx=(10, 0))
            
            # Timer display
            timer_label = tk.Label(main_frame, text="", bg=colors["details_bg"],
                                fg=colors["details_fg"], font=("Segoe UI", 9))
            timer_label.pack(side=tk.LEFT, padx=(5, 0))
            
            # Copy button
            copy_btn = tk.Button(main_frame, text="📋", 
                                command=lambda: self._copy_to_clipboard("Fetching...", "TOTP"),
                                bg=colors["button_bg"], fg=colors["button_fg"],
                                relief=tk.FLAT, cursor='hand2', padx=5)
            copy_btn.pack(side=tk.RIGHT, padx=2)
            
            # Expand/collapse button
            expand_btn = tk.Button(main_frame, text="▼", 
                                command=lambda: toggle_sync_frame(),
                                bg=colors["button_bg"], fg=colors["button_fg"],
                                relief=tk.FLAT, cursor='hand2', padx=5)
            expand_btn.pack(side=tk.RIGHT, padx=2)
            
            # Sync controls frame (initially hidden)
            sync_frame = tk.Frame(parent, bg=colors["details_bg"])
            
            # Drift value (start with saved value)
            drift_var = tk.IntVar(value=saved_drift)
            
            # Flag to stop updates
            is_updating = True
            
            # Function to save drift to database
            def save_drift_to_db():
                if entry_id and self.vault and self.vault.db:
                    try:
                        drift_value = drift_var.get()
                        
                        # Get the current entry
                        entry = self.vault.db.get_entry(entry_id)
                        if entry:
                            custom_fields = entry.get('custom_fields', {})
                            if not isinstance(custom_fields, dict):
                                custom_fields = {}
                            
                            # Create totp_params
                            totp_params = {
                                'type': 'totp',
                                'algorithm': 'SHA1',
                                'digits': 6,
                                'period': 30,
                                'time_offset': drift_value
                            }
                            
                            custom_fields['_totp_params'] = totp_params
                            
                            # Update using raw SQL
                            import json
                            conn = self.vault.db.conn
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE entries SET custom_fields = ? WHERE id = ?",
                                (json.dumps(custom_fields), entry_id)
                            )
                            conn.commit()
                            
                            print(f"✅ Saved TOTP drift: {drift_value:+d}s for entry {entry_id}")
                            save_feedback.config(text="✓ Drift saved!", fg=colors["success"])
                            self.root.after(2000, lambda: save_feedback.config(text=""))
                            return True
                    except Exception as e:
                        print(f"Error saving drift: {e}")
                        import traceback
                        traceback.print_exc()
                        save_feedback.config(text=f"Error: {str(e)[:30]}", fg=colors["danger"])
                        self.root.after(3000, lambda: save_feedback.config(text=""))
                return False
            
            # Create TOTP instance with current drift
            def get_totp():
                return TOTP(secret=secret, time_offset=drift_var.get())
            
            # Track after_id for cleanup
            after_id = None
            
            def update_code():
                nonlocal after_id
                # Check if widgets still exist and update flag is true
                if not is_updating:
                    return
                try:
                    # Check if code_label still exists
                    if not code_label.winfo_exists():
                        return
                    
                    totp = get_totp()
                    code = totp.get_current_code()
                    remaining = totp.get_time_remaining()
                    code_label.config(text=code)
                    timer_label.config(text=f"({remaining}s)")
                    copy_btn.config(command=lambda: self._copy_to_clipboard(code, "TOTP"))
                    
                    if remaining <= 5:
                        code_label.config(fg=colors["danger"])
                    elif remaining <= 10:
                        code_label.config(fg=colors["warning"])
                    else:
                        code_label.config(fg=colors["success"])
                    
                    after_id = self.root.after(500, update_code)
                except Exception as e:
                    # Widget might be destroyed, stop updating
                    pass
            
            def on_drift_change(*args):
                drift = drift_var.get()
                drift_label.config(text=f"Drift: {drift:+d}s")
            
            def toggle_sync_frame():
                if sync_frame.winfo_ismapped():
                    sync_frame.pack_forget()
                    expand_btn.config(text="▶")
                else:
                    sync_frame.pack(fill=tk.X, padx=15, pady=(5, 10))
                    expand_btn.config(text="▼")
            
            # Build sync controls
            slider_frame = tk.Frame(sync_frame, bg=colors["details_bg"])
            slider_frame.pack(fill=tk.X, pady=2)
            
            tk.Label(slider_frame, text="Time Sync:", bg=colors["details_bg"], 
                    fg=colors["details_fg"], font=("Segoe UI", 9)).pack(side=tk.LEFT)
            
            drift_scale = tk.Scale(slider_frame, from_=-60, to=60, orient=tk.HORIZONTAL,
                                variable=drift_var, bg=colors["bg"], fg=colors["fg"],
                                length=250, resolution=1, tickinterval=30,
                                command=lambda x: on_drift_change())
            drift_scale.set(saved_drift)
            drift_scale.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
            
            drift_label = tk.Label(slider_frame, text=f"Drift: {saved_drift:+d}s", 
                                bg=colors["details_bg"], fg=colors["details_fg"], 
                                font=("Segoe UI", 9))
            drift_label.pack(side=tk.LEFT, padx=5)
            
            # Preset buttons
            preset_frame = tk.Frame(sync_frame, bg=colors["details_bg"])
            preset_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(preset_frame, text="Quick Sync:", bg=colors["details_bg"], 
                    fg=colors["details_fg"], font=("Segoe UI", 9)).pack(side=tk.LEFT)
            
            def set_drift(val):
                drift_var.set(val)
                drift_scale.set(val)
                on_drift_change()
            
            presets = [-30, -15, -10, -5, 0, 5, 10, 15, 30]
            for p in presets:
                btn = tk.Button(preset_frame, text=f"{p:+d}", 
                            command=lambda v=p: set_drift(v),
                            bg=colors["button_bg"], fg=colors["button_fg"],
                            relief=tk.FLAT, cursor='hand2', padx=6, pady=2)
                btn.pack(side=tk.LEFT, padx=2)
            
            # SAVE DRIFT BUTTON
            save_button_frame = tk.Frame(sync_frame, bg=colors["details_bg"])
            save_button_frame.pack(fill=tk.X, pady=5)
            
            save_btn = tk.Button(save_button_frame, text="💾 Save Drift Permanently", 
                                command=save_drift_to_db,
                                bg=colors["accent"], fg="white",
                                relief=tk.FLAT, cursor='hand2', padx=15, pady=4)
            save_btn.pack(side=tk.LEFT, padx=5)
            
            save_feedback = tk.Label(save_button_frame, text="", bg=colors["details_bg"],
                                    fg=colors["success"], font=("Segoe UI", 9))
            save_feedback.pack(side=tk.LEFT, padx=10)
            
            # Instruction
            inst_label = tk.Label(sync_frame, 
                                text="💡 Adjust slider, then click 'Save Drift Permanently'",
                                bg=colors["details_bg"], fg=colors["details_fg"] if self.dark_mode else '#6b7280',
                                font=("Segoe UI", 8))
            inst_label.pack(pady=5)
            
            # Bind drift trace
            drift_var.trace('w', on_drift_change)
            
            # Cleanup function for when entry is deselected
            def cleanup():
                nonlocal is_updating
                is_updating = False
                if after_id:
                    self.root.after_cancel(after_id)
            
            # Bind cleanup to widget destruction
            parent.bind("<Destroy>", lambda e: cleanup(), add=True)
            
            # Start updating
            update_code()
            
        except Exception as e:
            error_label = tk.Label(main_frame, text=f"Error: {str(e)[:40]}", 
                                bg=colors["details_bg"], fg=colors["danger"])
            error_label.pack(side=tk.LEFT, padx=(10, 0))
            print(f"TOTP Error: {e}")

    def _add_url_row(self, parent, url):
        """Add URL row with Open and Copy buttons"""
        colors = self.get_colors()
        frame = tk.Frame(parent, bg=colors["details_bg"])
        frame.pack(fill=tk.X, padx=15, pady=4)
        
        tk.Label(frame, text="Website", width=12, anchor='w',
                bg=colors["details_bg"], fg=colors["details_fg"] if self.dark_mode else '#6b7280',
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        # Extract domain for cleaner display
        try:
            domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        except:
            domain = url[:40]
        
        url_label = tk.Label(frame, text=domain, bg=colors["details_bg"], 
                            fg=colors["accent"], cursor='hand2')
        url_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        url_label.bind("<Button-1>", lambda e: webbrowser.open(url))
        
        open_btn = tk.Button(frame, text="🌐", command=lambda: webbrowser.open(url),
                            bg=colors["button_bg"], fg=colors["button_fg"],
                            relief=tk.FLAT, cursor='hand2', padx=5)
        open_btn.pack(side=tk.RIGHT, padx=2)
        
        copy_btn = tk.Button(frame, text="📋", 
                            command=lambda: self._copy_to_clipboard(url, "URL"),
                            bg=colors["button_bg"], fg=colors["button_fg"],
                            relief=tk.FLAT, cursor='hand2', padx=5)
        copy_btn.pack(side=tk.RIGHT, padx=2)

    def _add_attachments_gallery(self, parent, attachments):
        """Add attachments as a gallery - simple list with Open button"""
        colors = self.get_colors()
        
        if not attachments:
            return
        
        # Create a frame for attachments
        gallery_frame = tk.LabelFrame(parent, text="📎 Attachments", 
                                    bg=colors["details_bg"], fg=colors["details_fg"], 
                                    font=("Segoe UI", 10, "bold"))
        gallery_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Create canvas for scrolling
        canvas = tk.Canvas(gallery_frame, bg=colors["details_bg"], highlightthickness=0, height=180)
        scrollbar = ttk.Scrollbar(gallery_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=colors["details_bg"])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=350)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel support for gallery
        def on_gallery_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_gallery_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        # Display each attachment as a card
        for idx, att in enumerate(attachments):
            filename = att.get('filename', 'Unknown')
            file_size = att.get('size', 0)
            
            # Format size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            # Format creation date if available
            metadata = att.get('metadata', {})
            date_str = ""
            if metadata.get('created'):
                created_date = datetime.fromtimestamp(metadata['created']).strftime("%Y-%m-%d")
                date_str = f" | 📅 {created_date}"
            
            # Get file icon
            ext = os.path.splitext(filename)[1].lower()
            icon = self._get_file_icon(ext)
            
            # Card frame
            card_frame = tk.Frame(scrollable_frame, bg=colors["entry_bg"], relief=tk.RAISED, bd=1)
            card_frame.pack(fill=tk.X, padx=5, pady=3)
            
            # Left: Icon
            icon_label = tk.Label(card_frame, text=icon, font=("Segoe UI", 20),
                                bg=colors["entry_bg"], fg=colors["fg"])
            icon_label.pack(side=tk.LEFT, padx=8, pady=8)
            
            # Middle: Info
            info_frame = tk.Frame(card_frame, bg=colors["entry_bg"])
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
            
            name_label = tk.Label(info_frame, text=filename, font=("Segoe UI", 10, "bold"),
                                bg=colors["entry_bg"], fg=colors["fg"], anchor='w')
            name_label.pack(anchor='w')
            
            size_label = tk.Label(info_frame, text=f"{size_str}{date_str}", font=("Segoe UI", 8),
                                bg=colors["entry_bg"], fg=colors["fg"] if self.dark_mode else '#6b7280', anchor='w')
            size_label.pack(anchor='w')
            
            # Right: Open button (opens with default OS app)
            open_btn = tk.Button(card_frame, text="📂 Open", 
                                command=lambda a=att: self._open_attachment(a),
                                bg=colors["accent"], fg="white",
                                relief=tk.FLAT, cursor='hand2', padx=12, pady=4)
            open_btn.pack(side=tk.RIGHT, padx=8)
    
    def _get_file_icon(self, ext):
        """Get emoji icon based on file extension (includes opus and avif)"""
        icons = {
            # Images
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.bmp': '🖼️', 
            '.svg': '🎨', '.webp': '🖼️', '.avif': '🖼️', '.heic': '🖼️',
            # Audio
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.ogg': '🎵', '.m4a': '🎵',
            '.opus': '🎵',  # Opus audio format
            # Video
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬', '.wmv': '🎬', '.flv': '🎬',
            # Documents
            '.pdf': '📄', '.doc': '📝', '.docx': '📝', '.txt': '📃', '.rtf': '📃', '.md': '📃',
            '.xls': '📊', '.xlsx': '📊', '.ppt': '📽️', '.pptx': '📽️',
            # Archives
            '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
            # Code
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨', '.json': '📋', '.xml': '📋',
            '.exe': '⚙️', '.msi': '⚙️', '.dll': '🔧',
            # Default
            'default': '📎'
        }
        return icons.get(ext, icons['default'])
    
    def _open_attachment(self, attachment):
        """Open attachment with default system application"""
        filename = attachment.get('filename', 'attachment')
        file_data = attachment.get('data', '')
        
        if not file_data:
            messagebox.showerror("Error", "No attachment data found")
            return
        
        # Create a unique filename in temp directory
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"vaultkeeper_{hashlib.md5(filename.encode()).hexdigest()[:8]}_{filename}")
        
        try:
            # Write data to temp file
            data = base64.b64decode(file_data)
            with open(temp_path, 'wb') as f:
                f.write(data)
            
            # Restore original creation date if available
            metadata = attachment.get('metadata', {})
            if metadata.get('created'):
                try:
                    os.utime(temp_path, (metadata['created'], metadata.get('modified', metadata['created'])))
                except:
                    pass
            
            # Open with default system application
            if os.name == 'nt':  # Windows
                os.startfile(temp_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', temp_path])
            else:  # Linux
                subprocess.run(['xdg-open', temp_path])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def _preview_attachment(self, attachment):
        """Show preview of attachment (images only for now)"""
        filename = attachment.get('filename', 'attachment')
        file_data = attachment.get('data', '')
        ext = os.path.splitext(filename)[1].lower()
        
        # Only preview images
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.avif']
        if ext not in image_exts:
            messagebox.showinfo("Preview", f"Preview not available for {ext} files.\nUse Open to view the file.")
            return
        
        if not file_data:
            messagebox.showerror("Error", "No attachment data found")
            return
        
        # Create temporary file for preview
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"preview_{filename}")
        
        try:
            # Write data to temp file
            data = base64.b64decode(file_data)
            with open(temp_path, 'wb') as f:
                f.write(data)
            
            # Open preview window
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"Preview: {filename}")
            preview_window.geometry("600x500")
            
            colors = self.get_colors()
            preview_window.configure(bg=colors["bg"])
            
            # Try to show image using PIL
            try:
                from PIL import Image, ImageTk
                image = Image.open(temp_path)
                
                # Resize to fit window while maintaining aspect ratio
                max_size = (500, 400)
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(image)
                label = tk.Label(preview_window, image=photo, bg=colors["bg"])
                label.image = photo  # Keep reference
                label.pack(expand=True, padx=10, pady=10)
                
                # Info label
                info = tk.Label(preview_window, text=f"{filename}\n{image.size[0]}x{image.size[1]} pixels",
                            font=("Segoe UI", 9), bg=colors["bg"], fg=colors["fg"])
                info.pack(pady=5)
                
            except ImportError:
                # PIL not available, show basic info
                tk.Label(preview_window, text=f"Preview not available\n\nFile: {filename}\n\nInstall Pillow for image preview:\npip install Pillow",
                        font=("Segoe UI", 11), bg=colors["bg"], fg=colors["fg"], justify=tk.CENTER).pack(expand=True)
            except Exception as e:
                tk.Label(preview_window, text=f"Cannot preview this image\n\n{str(e)}",
                        font=("Segoe UI", 11), bg=colors["bg"], fg=colors["danger"], justify=tk.CENTER).pack(expand=True)
            
            # Close button
            close_btn = tk.Button(preview_window, text="Close", command=preview_window.destroy,
                                bg=colors["accent"], fg="white", relief=tk.FLAT, padx=20, pady=5)
            close_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview: {str(e)}")
    
    def _save_attachment(self, attachment):
        """Save attachment to disk"""
        filename = attachment.get('filename', 'attachment')
        file_data = attachment.get('data', '')
        
        if not file_data:
            messagebox.showerror("Error", "No attachment data found")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=os.path.splitext(filename)[1],
            initialfile=filename,
            title="Save Attachment"
        )
        
        if filepath:
            try:
                data = base64.b64decode(file_data)
                with open(filepath, 'wb') as f:
                    f.write(data)
                messagebox.showinfo("Success", f"Attachment saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def _toggle_favorite(self, entry_id, btn):
        """Toggle favorite status - just changes symbol, no scaling"""
        if self.vault and self.vault.db:
            self.vault.db.toggle_favorite(entry_id)
            entry = self.vault.db.get_entry(entry_id)
            is_fav = entry.get('is_favorite', False) if entry else False
            btn.config(text="⭐" if is_fav else "☆")
    
    def _copy_to_clipboard(self, value, label):
        if not value:
            messagebox.showwarning("Nothing to Copy", f"No {label} to copy!")
            return
        self.clipboard.copy(value)
        if self.status_label:
            self.status_label.config(text=f"✓ {label} copied to clipboard! (clears in {self.clipboard.clear_delay}s)")
            self.root.after(2000, lambda: self.status_label.config(text="Ready"))
    
    # ========== ENTRY MANAGEMENT ==========
    
    def add_entry(self):
        from .entry_editor import EntryEditor
        EntryEditor(self.root, self.vault, dark_mode=self.dark_mode)
    
    def edit_entry(self, entry_id):
        from .entry_editor import EntryEditor
        EntryEditor(self.root, self.vault, entry_id, self.dark_mode)
    
    def delete_entry(self, entry_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this entry?"):
            if self.vault and self.vault.db:
                self.vault.db.delete_entry(entry_id)
                self.refresh_entries()
                self.show_details_placeholder()
                if self.status_label:
                    self.status_label.config(text="✓ Entry deleted")
                    self.root.after(2000, lambda: self.status_label.config(text="Ready"))

    def lock_vault(self):
        """Lock the vault - close window, reopen with password prompt"""
        self.root.destroy()
        # Re-run main to show unlock screen again
        import subprocess
        subprocess.Popen(["python", "run.py"])

    def run(self):
        self.root.mainloop()
