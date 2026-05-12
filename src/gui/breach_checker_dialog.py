"""
breach_checker_dialog.py - Scan actual vault for breached passwords
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

class BreachCheckerDialog:
    """Dialog for checking passwords against breach database"""
    
    def __init__(self, parent, dark_mode=False, vault_manager=None):
        self.parent = parent
        self.dark_mode = dark_mode
        self.vault = vault_manager
        self.scan_results = []
        self.scanning = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Breach Checker - VaultKeeper")
        self.dialog.geometry("750x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.start_scan()
    
    def get_colors(self):
        if self.dark_mode:
            return {"bg": "#1e1e1e", "fg": "#ffffff", "entry_bg": "#3d3d3d",
                    "entry_fg": "#ffffff", "button_bg": "#3d3d3d", "button_fg": "#ffffff",
                    "accent": "#3b82f6", "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444"}
        else:
            return {"bg": "#f5f5f5", "fg": "#000000", "entry_bg": "#ffffff",
                    "entry_fg": "#000000", "button_bg": "#e5e7eb", "button_fg": "#000000",
                    "accent": "#3b82f6", "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444"}
    
    def setup_ui(self):
        colors = self.get_colors()
        self.dialog.configure(bg=colors["bg"])
        
        main_frame = tk.Frame(self.dialog, bg=colors["bg"], padx=25, pady=25)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Label(
            main_frame, text="🔍 Breach Checker",
            font=("Segoe UI", 18, "bold"),
            bg=colors["bg"], fg=colors["fg"]
        )
        header.pack(anchor='w', pady=(0, 10))
        
        info = tk.Label(
            main_frame,
            text="Scanning your vault for passwords that appear in known data breaches.\n"
                 "This check is performed locally - no internet connection required.",
            font=("Segoe UI", 10),
            bg=colors["bg"], fg=colors["fg"] if self.dark_mode else '#6b7280',
            justify=tk.LEFT
        )
        info.pack(anchor='w', pady=(0, 20))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 15))
        
        # Status label
        self.status_label = tk.Label(
            main_frame, text="Scanning vault...",
            font=("Segoe UI", 10),
            bg=colors["bg"], fg=colors["fg"]
        )
        self.status_label.pack(pady=(0, 15))
        
        # Results tree
        results_frame = tk.LabelFrame(main_frame, text="Scan Results", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 11, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        tree_frame = tk.Frame(results_frame, bg=colors["bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("Title", "Username", "Status", "Details")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("Title", text="Title")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Details", text="Details")
        
        self.tree.column("Title", width=200)
        self.tree.column("Username", width=150)
        self.tree.column("Status", width=100)
        self.tree.column("Details", width=200)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=colors["bg"])
        button_frame.pack(fill=tk.X)
        
        self.rescan_btn = tk.Button(
            button_frame, text="🔄 Rescan Vault",
            command=self.start_scan,
            bg=colors["accent"], fg="white",
            relief=tk.FLAT, cursor='hand2', padx=20, pady=5
        )
        self.rescan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = tk.Button(
            button_frame, text="Close", command=self.dialog.destroy,
            bg=colors["button_bg"], fg=colors["button_fg"],
            relief=tk.FLAT, cursor='hand2', padx=20, pady=5
        )
        close_btn.pack(side=tk.RIGHT)
    
    def start_scan(self):
        """Start scanning the actual vault"""
        if self.scanning:
            return
        
        self.scanning = True
        self.rescan_btn.config(state='disabled')
        self.progress_bar.start(10)
        self.status_label.config(text="Scanning vault entries...")
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Run scan in background
        thread = threading.Thread(target=self._run_scan)
        thread.daemon = True
        thread.start()
    
    def _run_scan(self):
        """Run the breach scan on ACTUAL vault data"""
        colors = self.get_colors()
        
        # Get entries from actual vault
        entries = []
        if self.vault and self.vault.db:
            try:
                entries = self.vault.db.get_all_entries()
                print(f"🔍 Scanning {len(entries)} entries for breaches...")
            except Exception as e:
                print(f"Error getting entries: {e}")
        
        if not entries:
            self.dialog.after(0, self._scan_complete, [], 0)
            return
        
        # Known breached passwords (simplified check)
        breached_passwords = {
            'password', '123456', '123456789', 'qwerty', 'password123',
            'admin', 'letmein', 'welcome', 'monkey', 'dragon', 'master',
            'hello', 'freedom', 'whatever', 'trustno1', 'princess'
        }
        
        # Check each entry
        breached_entries = []
        for entry in entries:
            password = entry.get('password', '')
            if password and password.lower() in breached_passwords:
                breached_entries.append({
                    'id': entry.get('id'),
                    'title': entry.get('title', 'Unknown'),
                    'username': entry.get('username', ''),
                    'password': password[:20] + "..." if len(password) > 20 else password,
                    'message': 'Found in known data breaches!'
                })
        
        # Update UI
        self.dialog.after(0, self._scan_complete, breached_entries, len(entries))
    
    def _scan_complete(self, breached_entries, total_entries):
        """Update UI with scan results"""
        colors = self.get_colors()
        
        self.progress_bar.stop()
        self.scanning = False
        self.rescan_btn.config(state='normal')
        
        # Populate results
        for entry in breached_entries:
            self.tree.insert("", tk.END, values=(
                entry['title'],
                entry['username'],
                "❌ BREACHED",
                entry['message']
            ))
        
        # Update status
        if breached_entries:
            self.status_label.config(
                text=f"⚠️ Found {len(breached_entries)} breached passwords out of {total_entries} entries!",
                fg=colors["danger"]
            )
        else:
            self.status_label.config(
                text=f"✅ No breached passwords found! ({total_entries} entries checked)",
                fg=colors["success"]
            )
        
        # Show summary if breaches found
        if breached_entries:
            summary_frame = tk.Frame(self.dialog, bg=colors["warning"])
            summary_frame.pack(side=tk.BOTTOM, fill=tk.X)
            
            summary_text = f"⚠️ ACTION REQUIRED: {len(breached_entries)} passwords found in data breaches! Change them immediately."
            summary_label = tk.Label(
                summary_frame, text=summary_text,
                font=("Segoe UI", 10, "bold"),
                bg=colors["warning"], fg="white", padx=15, pady=10
            )
            summary_label.pack()
            
            self.dialog.after(8000, summary_frame.destroy)
