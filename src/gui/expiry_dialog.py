"""
expiry_dialog.py - Password expiry reminder dialog
Shows expiring passwords and allows bulk actions
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pyperclip

class ExpiryReminderDialog:
    """Dialog showing expiring passwords"""
    
    def __init__(self, parent, expiry_manager, dark_mode=False):
        self.parent = parent
        self.expiry_manager = expiry_manager
        self.dark_mode = dark_mode
        self.expiring_entries = []
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Password Expiry Reminders - VaultKeeper")
        self.dialog.geometry("750x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.load_expiring_entries()
    
    def get_colors(self):
        """Get current colors based on dark mode"""
        if self.dark_mode:
            return {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "entry_bg": "#3d3d3d",
                "entry_fg": "#ffffff",
                "button_bg": "#3d3d3d",
                "button_fg": "#ffffff",
                "accent": "#3b82f6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "danger": "#ef4444",
                "border": "#4a4a4a"
            }
        else:
            return {
                "bg": "#f5f5f5",
                "fg": "#000000",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "button_bg": "#e5e7eb",
                "button_fg": "#000000",
                "accent": "#3b82f6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "danger": "#ef4444",
                "border": "#d1d5db"
            }
    
    def setup_ui(self):
        """Setup the dialog UI"""
        colors = self.get_colors()
        self.dialog.configure(bg=colors["bg"])
        
        # Main frame
        main_frame = tk.Frame(self.dialog, bg=colors["bg"], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title = tk.Label(
            header_frame, text="⏰ Password Expiry Reminders",
            font=("Segoe UI", 16, "bold"),
            bg=colors["bg"], fg=colors["fg"]
        )
        title.pack(side=tk.LEFT)
        
        # Refresh button
        refresh_btn = tk.Button(
            header_frame, text="🔄 Refresh",
            command=self.load_expiring_entries,
            bg=colors["button_bg"], fg=colors["button_fg"],
            relief=tk.FLAT, cursor='hand2', padx=10
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        # Info label
        info_label = tk.Label(
            main_frame, 
            text="Passwords that haven't been changed in a while. Update them to keep your accounts secure.",
            font=("Segoe UI", 9),
            bg=colors["bg"], fg=colors["fg"] if self.dark_mode else '#6b7280',
            justify=tk.LEFT
        )
        info_label.pack(anchor='w', pady=(0, 15))
        
        # Treeview for expiring entries
        tree_frame = tk.Frame(main_frame, bg=colors["bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        columns = ("Title", "Username", "Days Left", "Severity", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("Title", text="Title")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Days Left", text="Days Left")
        self.tree.heading("Severity", text="Severity")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("Title", width=200)
        self.tree.column("Username", width=180)
        self.tree.column("Days Left", width=80)
        self.tree.column("Severity", width=80)
        self.tree.column("Status", width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=colors["bg"])
        button_frame.pack(fill=tk.X)
        
        # Select all button
        select_btn = tk.Button(
            button_frame, text="✓ Select All",
            command=self.select_all,
            bg=colors["button_bg"], fg=colors["button_fg"],
            relief=tk.FLAT, cursor='hand2', padx=15
        )
        select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Deselect all button
        deselect_btn = tk.Button(
            button_frame, text="✗ Deselect All",
            command=self.deselect_all,
            bg=colors["button_bg"], fg=colors["button_fg"],
            relief=tk.FLAT, cursor='hand2', padx=15
        )
        deselect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Update selected button
        update_btn = tk.Button(
            button_frame, text="🔧 Update Selected",
            command=self.update_selected,
            bg=colors["accent"], fg="white",
            relief=tk.FLAT, cursor='hand2', padx=15
        )
        update_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Dismiss selected button
        dismiss_btn = tk.Button(
            button_frame, text="⏰ Remind Later",
            command=self.dismiss_selected,
            bg=colors["warning"], fg="white",
            relief=tk.FLAT, cursor='hand2', padx=15
        )
        dismiss_btn.pack(side=tk.LEFT)
        
        # Close button
        close_btn = tk.Button(
            button_frame, text="Close",
            command=self.dialog.destroy,
            bg=colors["button_bg"], fg=colors["button_fg"],
            relief=tk.FLAT, cursor='hand2', padx=20
        )
        close_btn.pack(side=tk.RIGHT)
        
        # Configure tag colors
        self.tree.tag_configure('critical', foreground='#ef4444')
        self.tree.tag_configure('high', foreground='#f59e0b')
        self.tree.tag_configure('medium', foreground='#3b82f6')
    
    def load_expiring_entries(self):
        """Load and display expiring entries"""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get expiring entries
        self.expiring_entries = self.expiry_manager.get_expiring_entries(90)
        
        if not self.expiring_entries:
            # Show no results
            no_items = tk.Label(self.dialog, text="✅ No expiring passwords found!\nAll passwords are up to date.",
                               font=("Segoe UI", 12),
                               bg=self.get_colors()["bg"], fg=self.get_colors()["success"])
            no_items.place(relx=0.5, rely=0.5, anchor='center')
            self.dialog.after(2000, no_items.destroy)
            return
        
        for entry in self.expiring_entries:
            days_left = entry['days_left']
            severity = entry['severity'].upper()
            
            if days_left <= 0:
                status = "EXPIRED"
                tag = 'critical'
            elif days_left <= 7:
                status = "URGENT"
                tag = 'critical'
            elif days_left <= 30:
                status = "Expiring Soon"
                tag = 'high'
            else:
                status = "Notice"
                tag = 'medium'
            
            self.tree.insert("", tk.END, iid=entry['id'],
                           values=(entry['title'], entry['username'], days_left, severity, status),
                           tags=(tag,))
    
    def select_all(self):
        """Select all items in tree"""
        for item in self.tree.get_children():
            self.tree.selection_add(item)
    
    def deselect_all(self):
        """Deselect all items"""
        self.tree.selection_remove(*self.tree.selection())
    
    def update_selected(self):
        """Open password generator for selected entries"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select entries to update.")
            return
        
        from .password_generator import PasswordGeneratorDialog
        
        for item in selected:
            entry_id = int(item)
            entry = next((e for e in self.expiring_entries if e['id'] == entry_id), None)
            if entry:
                # Open generator for this entry
                gen = PasswordGeneratorDialog(self.dialog, self.dark_mode)
                self.dialog.wait_window(gen.dialog)
                if gen.result_password:
                    # Update the password
                    if self.expiry_manager.vault and self.expiry_manager.vault.db:
                        self.expiry_manager.vault.db.update_entry(entry_id, {'password': gen.result_password})
                        self.expiry_manager.update_password_changed(entry_id)
        
        # Refresh the list
        self.load_expiring_entries()
        messagebox.showinfo("Update Complete", "Selected passwords have been updated!")
    
    def dismiss_selected(self):
        """Dismiss selected entries (remind later)"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select entries to dismiss.")
            return
        
        notifier = self.expiry_manager.notifier if hasattr(self.expiry_manager, 'notifier') else None
        
        for item in selected:
            entry_id = int(item)
            if notifier:
                notifier.dismiss_entry(entry_id)
        
        # Refresh the list
        self.load_expiring_entries()
        messagebox.showinfo("Dismissed", "Selected entries will remind you again in 7 days.")
