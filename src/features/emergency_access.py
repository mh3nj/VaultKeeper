"""
emergency_access.py - Offline Emergency Access System
Creates time-locked emergency access packages without any cloud dependency
"""

import json
import os
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import base64
import hashlib
import qrcode
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class EmergencyAccess:
    """Creates and manages offline emergency access packages"""
    
    def __init__(self, vault_manager=None):
        self.vault = vault_manager
        self.base_path = os.path.expanduser("~/Documents/VaultKeeper/EmergencyAccess")
        os.makedirs(self.base_path, exist_ok=True)
    
    def create_emergency_package(self, vault_password: str, accessor_name: str, 
                                  wait_days: int = 30, message: str = "") -> str:
        """
        Create an emergency access package
        
        Args:
            vault_password: The master password of the vault
            accessor_name: Name of the person who will get access
            wait_days: Number of days to wait before access is granted
            message: Optional message for the accessor
        
        Returns:
            Path to the created emergency package
        """
        # Create a unique ID for this emergency package
        package_id = hashlib.sha256(f"{accessor_name}{time.time()}".encode()).hexdigest()[:16]
        
        # Create the package data
        package_data = {
            'id': package_id,
            'created_at': datetime.now().isoformat(),
            'accessor_name': accessor_name,
            'wait_days': wait_days,
            'unlock_time': time.time() + (wait_days * 86400),  # Timestamp when it unlocks
            'message': message,
            'vault_password_encrypted': self._encrypt_for_time_lock(vault_password, wait_days),
            'version': 2
        }
        
        # Save the package
        package_path = os.path.join(self.base_path, f"emergency_{package_id}.json")
        with open(package_path, 'w') as f:
            json.dump(package_data, f, indent=2)
        
        # Also create a QR code for easy sharing
        qr_path = self._create_qr_code(package_path, package_id)
        
        return package_path, qr_path
    
    def _encrypt_for_time_lock(self, data: str, wait_days: int) -> str:
        """Encrypt data with time-lock (can only be decrypted after wait_days)"""
        # This is a simplified time-lock encryption
        # In production, use a real time-lock cryptography scheme
        
        # Combine data with future timestamp requirement
        future_time = int(time.time() + (wait_days * 86400))
        combined = f"{data}|{future_time}"
        
        # Simple encryption (in production, use stronger method)
        key = hashlib.sha256(str(future_time).encode()).digest()
        cipher = Fernet(base64.urlsafe_b64encode(key[:32]))
        encrypted = cipher.encrypt(combined.encode())
        
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_time_locked(self, encrypted_data: str) -> str:
        """Decrypt time-locked data (fails if time hasn't been reached)"""
        encrypted = base64.b64decode(encrypted_data.encode())
        
        # Try to decrypt with current time and a range around it (for clock drift)
        current_time = int(time.time())
        for offset in range(-86400, 86401, 3600):  # Check +/- 1 day in 1-hour increments
            test_time = current_time + offset
            try:
                key = hashlib.sha256(str(test_time).encode()).digest()
                cipher = Fernet(base64.urlsafe_b64encode(key[:32]))
                decrypted = cipher.decrypt(encrypted).decode()
                
                # Parse to check if time requirement is met
                parts = decrypted.rsplit('|', 1)
                if len(parts) == 2:
                    required_time = int(parts[1])
                    if current_time >= required_time:
                        return parts[0]
            except:
                continue
        
        raise Exception("Time lock not yet expired or decryption failed")
    
    def _create_qr_code(self, package_path: str, package_id: str) -> str:
        """Create QR code for the emergency package"""
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(package_path)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(self.base_path, f"emergency_{package_id}.png")
        qr_image.save(qr_path)
        
        return qr_path
    
    def get_active_packages(self) -> list:
        """Get all active emergency packages"""
        packages = []
        for file in os.listdir(self.base_path):
            if file.startswith("emergency_") and file.endswith(".json"):
                try:
                    with open(os.path.join(self.base_path, file), 'r') as f:
                        package = json.load(f)
                        packages.append(package)
                except:
                    continue
        return packages
    
    def delete_package(self, package_id: str):
        """Delete an emergency package"""
        package_path = os.path.join(self.base_path, f"emergency_{package_id}.json")
        qr_path = os.path.join(self.base_path, f"emergency_{package_id}.png")
        
        if os.path.exists(package_path):
            os.remove(package_path)
        if os.path.exists(qr_path):
            os.remove(qr_path)


class EmergencyAccessDialog:
    """Dialog for managing emergency access"""
    
    def __init__(self, parent, emergency_access, dark_mode=False):
        self.parent = parent
        self.emergency = emergency_access
        self.dark_mode = dark_mode
        self.current_packages = []
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Emergency Access - VaultKeeper")
        self.dialog.geometry("900x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.load_packages()
    
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
        
        # Main frame with notebook
        main_frame = tk.Frame(self.dialog, bg=colors["bg"], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Label(
            main_frame, text="🆘 Emergency Access",
            font=("Segoe UI", 18, "bold"),
            bg=colors["bg"], fg=colors["fg"]
        )
        header.pack(anchor='w', pady=(0, 10))
        
        # Info text
        info = tk.Label(
            main_frame,
            text="Create time-locked emergency access for trusted individuals.\n"
                 "After the waiting period, they can access your vault without your password.",
            font=("Segoe UI", 10),
            bg=colors["bg"], fg=colors["fg"] if self.dark_mode else '#6b7280',
            justify=tk.LEFT
        )
        info.pack(anchor='w', pady=(0, 20))
        
        # Tab control
        tab_control = ttk.Notebook(main_frame)
        
        # Create tab
        create_tab = tk.Frame(tab_control, bg=colors["bg"])
        tab_control.add(create_tab, text="➕ Create New")
        self.setup_create_tab(create_tab)
        
        # Manage tab
        manage_tab = tk.Frame(tab_control, bg=colors["bg"])
        tab_control.add(manage_tab, text="📋 Manage Packages")
        self.setup_manage_tab(manage_tab)
        
        # Access tab (for accessing emergency packages)
        access_tab = tk.Frame(tab_control, bg=colors["bg"])
        tab_control.add(access_tab, text="🔓 Access Package")
        self.setup_access_tab(access_tab)
        
        tab_control.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Close button
        close_btn = tk.Button(
            main_frame, text="Close", command=self.dialog.destroy,
            bg=colors["button_bg"], fg=colors["button_fg"],
            relief=tk.FLAT, cursor='hand2', padx=25, pady=8
        )
        close_btn.pack()
    
    def setup_create_tab(self, parent):
        """Setup the create emergency access tab"""
        colors = self.get_colors()
        
        frame = tk.Frame(parent, bg=colors["bg"], padx=25, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Accessor name
        tk.Label(frame, text="Accessor Name:", font=("Segoe UI", 10, "bold"),
                bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(0, 5))
        self.accessor_name = tk.Entry(frame, width=40,
                                      bg=colors["entry_bg"], fg=colors["entry_fg"],
                                      relief=tk.SOLID, bd=1)
        self.accessor_name.pack(anchor='w', pady=(0, 15))
        
        # Waiting period
        tk.Label(frame, text="Waiting Period (days):", font=("Segoe UI", 10, "bold"),
                bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(0, 5))
        self.wait_days = tk.IntVar(value=30)
        wait_spin = tk.Spinbox(frame, from_=1, to=365, textvariable=self.wait_days,
                               width=15, bg=colors["entry_bg"], fg=colors["entry_fg"])
        wait_spin.pack(anchor='w', pady=(0, 15))
        
        # Message
        tk.Label(frame, text="Personal Message (optional):", font=("Segoe UI", 10, "bold"),
                bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(0, 5))
        self.message_text = tk.Text(frame, height=5, width=50,
                                   bg=colors["entry_bg"], fg=colors["entry_fg"],
                                   relief=tk.SOLID, bd=1)
        self.message_text.pack(anchor='w', pady=(0, 20))
        
        # Warning
        warning = tk.Label(
            frame,
            text="⚠️ WARNING: After the waiting period, the accessor will be able to\n"
                 "   unlock your vault without your password. Use this feature carefully!",
            font=("Segoe UI", 9),
            bg=colors["bg"], fg=colors["danger"],
            justify=tk.LEFT
        )
        warning.pack(anchor='w', pady=(0, 20))
        
        # Create button
        def create_package():
            name = self.accessor_name.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter an accessor name")
                return
            
            # Get vault password
            from tkinter import simpledialog
            password = simpledialog.askstring("Vault Password", 
                                              "Enter your vault master password:", 
                                              show='*')
            if not password:
                return
            
            try:
                package_path, qr_path = self.emergency.create_emergency_package(
                    password, name, self.wait_days.get(), self.message_text.get(1.0, tk.END).strip()
                )
                
                messagebox.showinfo("Success", 
                    f"Emergency package created!\n\n"
                    f"📁 Package location: {package_path}\n"
                    f"📱 QR Code location: {qr_path}\n\n"
                    f"Share the QR code or file with {name}.\n"
                    f"They will be able to access your vault after {self.wait_days.get()} days.")
                
                self.load_packages()
                self.accessor_name.delete(0, tk.END)
                self.message_text.delete(1.0, tk.END)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create package: {str(e)}")
        
        create_btn = tk.Button(
            frame, text="📦 Create Emergency Package", command=create_package,
            bg=colors["danger"], fg="white", padx=20, pady=10,
            relief=tk.FLAT, cursor='hand2', font=("Segoe UI", 11, "bold")
        )
        create_btn.pack(pady=10)
    
    def setup_manage_tab(self, parent):
        """Setup the manage packages tab"""
        colors = self.get_colors()
        
        frame = tk.Frame(parent, bg=colors["bg"], padx=25, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for packages
        tree_frame = tk.Frame(frame, bg=colors["bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        columns = ("ID", "Accessor", "Created", "Unlocks", "Status")
        self.packages_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        
        self.packages_tree.heading("ID", text="Package ID")
        self.packages_tree.heading("Accessor", text="Accessor")
        self.packages_tree.heading("Created", text="Created")
        self.packages_tree.heading("Unlocks", text="Unlocks On")
        self.packages_tree.heading("Status", text="Status")
        
        self.packages_tree.column("ID", width=150)
        self.packages_tree.column("Accessor", width=150)
        self.packages_tree.column("Created", width=150)
        self.packages_tree.column("Unlocks", width=150)
        self.packages_tree.column("Status", width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.packages_tree.yview)
        self.packages_tree.configure(yscrollcommand=scrollbar.set)
        
        self.packages_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure tags
        self.packages_tree.tag_configure('active', foreground='#10b981')
        self.packages_tree.tag_configure('pending', foreground='#f59e0b')
        self.packages_tree.tag_configure('expired', foreground='#ef4444')
        
        # Delete button
        delete_btn = tk.Button(
            frame, text="🗑️ Delete Selected", command=self.delete_selected_package,
            bg=colors["danger"], fg="white", padx=20, pady=8,
            relief=tk.FLAT, cursor='hand2'
        )
        delete_btn.pack()
    
    def setup_access_tab(self, parent):
        """Setup the access package tab"""
        colors = self.get_colors()
        
        frame = tk.Frame(parent, bg=colors["bg"], padx=25, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Info text
        info = tk.Label(
            frame,
            text="If someone has shared an emergency access package with you,\n"
                 "you can use this section to unlock their vault after the waiting period.",
            font=("Segoe UI", 10),
            bg=colors["bg"], fg=colors["fg"] if self.dark_mode else '#6b7280',
            justify=tk.CENTER
        )
        info.pack(pady=(0, 20))
        
        # Package file selection
        tk.Label(frame, text="Emergency Package File:", font=("Segoe UI", 10, "bold"),
                bg=colors["bg"], fg=colors["fg"]).pack(anchor='w')
        
        file_frame = tk.Frame(frame, bg=colors["bg"])
        file_frame.pack(fill=tk.X, pady=(5, 15))
        
        self.package_path = tk.StringVar()
        path_entry = tk.Entry(file_frame, textvariable=self.package_path, width=50,
                             bg=colors["entry_bg"], fg=colors["entry_fg"])
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(file_frame, text="Browse", command=self.browse_package,
                              bg=colors["button_bg"], fg=colors["button_fg"],
                              relief=tk.FLAT, cursor='hand2')
        browse_btn.pack(side=tk.RIGHT)
        
        # Access button
        access_btn = tk.Button(
            frame, text="🔓 Attempt Emergency Access", command=self.attempt_access,
            bg=colors["warning"], fg="white", padx=25, pady=10,
            relief=tk.FLAT, cursor='hand2', font=("Segoe UI", 11, "bold")
        )
        access_btn.pack(pady=20)
        
        # Info about waiting period
        self.wait_info = tk.Label(
            frame, text="",
            font=("Segoe UI", 10),
            bg=colors["bg"], fg=colors["fg"],
            justify=tk.CENTER
        )
        self.wait_info.pack()
    
    def load_packages(self):
        """Load and display active packages"""
        if not hasattr(self, 'packages_tree'):
            return
        
        # Clear tree
        for item in self.packages_tree.get_children():
            self.packages_tree.delete(item)
        
        packages = self.emergency.get_active_packages()
        now = time.time()
        
        for package in packages:
            created = datetime.fromisoformat(package['created_at']).strftime("%Y-%m-%d")
            unlock_date = datetime.fromtimestamp(package['unlock_time']).strftime("%Y-%m-%d")
            
            if now >= package['unlock_time']:
                status = "READY"
                tag = 'active'
            else:
                days_left = int((package['unlock_time'] - now) / 86400)
                status = f"Locked ({days_left} days)"
                tag = 'pending'
            
            self.packages_tree.insert("", tk.END, iid=package['id'],
                                     values=(package['id'][:8], package['accessor_name'],
                                            created, unlock_date, status),
                                     tags=(tag,))
    
    def delete_selected_package(self):
        """Delete selected emergency package"""
        selection = self.packages_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a package to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", "Delete this emergency package?\nThis cannot be undone."):
            self.emergency.delete_package(selection[0])
            self.load_packages()
            messagebox.showinfo("Success", "Package deleted!")
    
    def browse_package(self):
        """Browse for emergency package file"""
        filename = filedialog.askopenfilename(
            title="Select Emergency Package",
            filetypes=[("Emergency Package", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.package_path.set(filename)
            self.load_package_info(filename)
    
    def load_package_info(self, filepath):
        """Load and display package info"""
        try:
            with open(filepath, 'r') as f:
                package = json.load(f)
            
            now = time.time()
            if now >= package['unlock_time']:
                days_remaining = 0
                status = "✅ READY TO ACCESS"
                color = "#10b981"
            else:
                days_remaining = int((package['unlock_time'] - now) / 86400)
                status = f"⏰ Locked - {days_remaining} days remaining"
                color = "#f59e0b"
            
            info_text = f"""
Package Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Accessor: {package['accessor_name']}
Created: {package['created_at']}
Unlocks On: {datetime.fromtimestamp(package['unlock_time']).strftime('%Y-%m-%d %H:%M:%S')}
Status: {status}

Message from owner:
{package.get('message', '(No message)')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            self.wait_info.config(text=info_text, fg=color)
            
        except Exception as e:
            self.wait_info.config(text=f"Error loading package: {str(e)}", fg="#ef4444")
    
    def attempt_access(self):
        """Attempt to unlock an emergency package"""
        filepath = self.package_path.get()
        if not filepath or not os.path.exists(filepath):
            messagebox.showerror("Error", "Please select a valid emergency package file")
            return
        
        try:
            with open(filepath, 'r') as f:
                package = json.load(f)
            
            # Check if waiting period has passed
            now = time.time()
            if now < package['unlock_time']:
                days_left = int((package['unlock_time'] - now) / 86400)
                messagebox.showerror("Access Denied", 
                    f"This package is time-locked for {days_left} more days.\n"
                    f"Please wait until {datetime.fromtimestamp(package['unlock_time']).strftime('%Y-%m-%d')}")
                return
            
            # Decrypt the vault password
            vault_password = self.emergency._decrypt_time_locked(package['vault_password_encrypted'])
            
            # Show the password to the user
            result = messagebox.askyesno("Emergency Access Granted",
                f"🎉 Emergency access granted!\n\n"
                f"This package was created by {package['accessor_name']}.\n\n"
                f"Vault Password: {vault_password}\n\n"
                f"⚠️ IMPORTANT: This password will only be shown once.\n"
                f"Would you like to copy it to clipboard?")
            
            if result:
                import pyperclip
                pyperclip.copy(vault_password)
                messagebox.showinfo("Copied", "Password copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Access Failed", f"Could not unlock the package: {str(e)}")
