"""
entry_editor.py - Complete Bitwarden-style entry editor with attachments and OTP
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import webbrowser
import os
import base64
import pyperclip
import time

class EntryEditor:
    """Bitwarden-style entry editor dialog with attachments and OTP"""
    
    def __init__(self, parent, vault_manager, entry_id=None, dark_mode=False):
        self.parent = parent
        self.vault = vault_manager
        self.entry_id = entry_id
        self.dark_mode = dark_mode
        self.uris = []
        self.custom_fields = []
        self.attachments = []
        self.existing_entry = None
        self.canvas = None
        self.attachments_frame = None
        self.totp_entry = None
        self.otp_type = None
        self.totp_algorithm = None
        self.totp_digits = None
        self.totp_period = None
        
        if entry_id and vault_manager and vault_manager.db:
            self.existing_entry = vault_manager.db.get_entry(entry_id)
        
        self.dialog = tk.Toplevel(parent)
        title = "Edit Entry" if self.existing_entry else "Add New Entry"
        self.dialog.title(f"{title} - VaultKeeper")
        self.dialog.geometry("850x980")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.load_existing_data()
    
    def get_colors(self):
        if self.dark_mode:
            return {
                "bg": "#1e1e1e", "fg": "#ffffff", "entry_bg": "#3d3d3d",
                "entry_fg": "#ffffff", "button_bg": "#3d3d3d", "button_fg": "#ffffff",
                "accent": "#3b82f6", "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444"
            }
        else:
            return {
                "bg": "#f5f5f5", "fg": "#000000", "entry_bg": "#ffffff",
                "entry_fg": "#000000", "button_bg": "#e5e7eb", "button_fg": "#000000",
                "accent": "#3b82f6", "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444"
            }
    
    def setup_ui(self):
        colors = self.get_colors()
        self.dialog.configure(bg=colors["bg"])
        
        # Create scrollable canvas
        self.canvas = tk.Canvas(self.dialog, bg=colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dialog, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollable_frame = tk.Frame(self.canvas, bg=colors["bg"])
        
        scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=810)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel support
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        frame = tk.Frame(scrollable_frame, bg=colors["bg"], padx=25, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Item Details
        self.create_item_details_section(frame)
        
        # Login Credentials
        self.create_login_section(frame)
        
        # URIs Section
        self.create_uris_section(frame)
        
        # Notes
        self.create_notes_section(frame)
        
        # Custom Fields
        self.create_custom_fields_section(frame)
        
        # Attachments Section
        self.create_attachments_section(frame)
        
        # Buttons
        button_frame = tk.Frame(frame, bg=colors["bg"])
        button_frame.pack(fill=tk.X, pady=20)
        
        save_btn = tk.Button(button_frame, text="💾 Save Entry", command=self.save_entry,
                            bg=colors["accent"], fg="white", padx=30, pady=8,
                            relief=tk.FLAT, cursor='hand2', font=("Segoe UI", 11, "bold"))
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                              bg=colors["button_bg"], fg=colors["button_fg"], padx=30, pady=8,
                              relief=tk.FLAT, cursor='hand2', font=("Segoe UI", 11))
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def create_item_details_section(self, parent):
        colors = self.get_colors()
        section = tk.LabelFrame(parent, text="Item Details", bg=colors["bg"], fg=colors["fg"],
                                font=("Segoe UI", 11, "bold"), padx=15, pady=10)
        section.pack(fill=tk.X, pady=(0, 15))
        
        row_frame = tk.Frame(section, bg=colors["bg"])
        row_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(row_frame, text="Name *", width=15, anchor='w',
                bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        self.name_entry = tk.Entry(row_frame, width=50,
                                   bg=colors["entry_bg"], fg=colors["entry_fg"],
                                   insertbackground=colors["entry_fg"])
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Icon selection
        icon_frame = tk.Frame(section, bg=colors["bg"])
        icon_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(icon_frame, text="Icon", width=15, anchor='w',
                bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT)
        
        icons = ["🔐", "🔑", "📧", "🐙", "📺", "🎨", "💻", "📦", "🎵", "🎮", "🏦", "📷", "✉️", "📱", "💳", "🆔"]
        self.icon_var = tk.StringVar(value="🔐")
        icon_combo = ttk.Combobox(icon_frame, textvariable=self.icon_var, values=icons, width=10)
        icon_combo.pack(side=tk.LEFT, padx=(10, 0))
    
    def create_login_section(self, parent):
        colors = self.get_colors()
        section = tk.LabelFrame(parent, text="Login Credentials", bg=colors["bg"], fg=colors["fg"],
                                font=("Segoe UI", 11, "bold"), padx=15, pady=10)
        section.pack(fill=tk.X, pady=(0, 15))
        
        # Username
        row_frame = tk.Frame(section, bg=colors["bg"])
        row_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(row_frame, text="Username", width=15, anchor='w',
                bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT)
        
        self.username_entry = tk.Entry(row_frame, width=50,
                                       bg=colors["entry_bg"], fg=colors["entry_fg"],
                                       insertbackground=colors["entry_fg"])
        self.username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Password
        row_frame2 = tk.Frame(section, bg=colors["bg"])
        row_frame2.pack(fill=tk.X, pady=5)
        
        tk.Label(row_frame2, text="Password", width=15, anchor='w',
                bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT)
        
        self.password_entry = tk.Entry(row_frame2, width=30, show="•",
                                       bg=colors["entry_bg"], fg=colors["entry_fg"],
                                       insertbackground=colors["entry_fg"])
        self.password_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        def open_password_generator():
            from .password_generator import PasswordGeneratorDialog
            gen = PasswordGeneratorDialog(self.dialog, self.dark_mode)
            self.dialog.wait_window(gen.dialog)
            if hasattr(gen, 'result_password') and gen.result_password:
                self.password_entry.delete(0, tk.END)
                self.password_entry.insert(0, gen.result_password)
        
        gen_btn = tk.Button(row_frame2, text="Generate", command=open_password_generator,
                           bg=colors["accent"], fg="white", relief=tk.FLAT, cursor='hand2')
        gen_btn.pack(side=tk.LEFT, padx=5)
        
        # Show/hide password
        self.show_password_var = tk.BooleanVar()
        def toggle_show():
            self.password_entry.config(show="" if self.show_password_var.get() else "•")
        
        show_check = tk.Checkbutton(row_frame2, text="Show", variable=self.show_password_var,
                                    command=toggle_show, bg=colors["bg"], fg=colors["fg"],
                                    selectcolor=colors["bg"])
        show_check.pack(side=tk.LEFT, padx=5)
        
        # OTP Section
        otp_frame = tk.LabelFrame(section, text="One-Time Password (2FA)", 
                                   bg=colors["bg"], fg=colors["fg"],
                                   font=("Segoe UI", 10, "bold"), padx=10, pady=5)
        otp_frame.pack(fill=tk.X, pady=(10, 0))
        
        # OTP Secret
        row_frame3 = tk.Frame(otp_frame, bg=colors["bg"])
        row_frame3.pack(fill=tk.X, pady=5)
        
        tk.Label(row_frame3, text="Secret Key", width=15, anchor='w',
                bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT)
        
        self.totp_entry = tk.Entry(row_frame3, width=35,
                                   bg=colors["entry_bg"], fg=colors["entry_fg"],
                                   insertbackground=colors["entry_fg"])
        self.totp_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Parse URI button
        def parse_otp_uri():
            uri = self.totp_entry.get().strip()
            if uri.startswith('otpauth://'):
                import re
                # Extract type
                type_match = re.search(r'otpauth://([^/]+)/', uri)
                if type_match:
                    otp_type_val = type_match.group(1)
                    # Map to our supported types
                    if otp_type_val in ["totp", "steam", "yandex", "motp"]:
                        self.otp_type.set(otp_type_val)
                
                # Extract secret
                secret_match = re.search(r'secret=([A-Z2-7]+)', uri, re.IGNORECASE)
                if secret_match:
                    self.totp_entry.delete(0, tk.END)
                    self.totp_entry.insert(0, secret_match.group(1))
                
                # Extract algorithm
                algo_match = re.search(r'algorithm=(\w+)', uri, re.IGNORECASE)
                if algo_match:
                    algo = algo_match.group(1).upper()
                    if algo in ["SHA1", "SHA256", "SHA512", "MD5"]:
                        self.totp_algorithm.set(algo)
                
                # Extract digits
                digits_match = re.search(r'digits=(\d+)', uri)
                if digits_match:
                    self.totp_digits.set(digits_match.group(1))
                
                # Extract period
                period_match = re.search(r'period=(\d+)', uri)
                if period_match:
                    self.totp_period.set(period_match.group(1))
                
                messagebox.showinfo("Success", "OTP parameters extracted from URI!")
            else:
                messagebox.showinfo("Info", "Paste an otpauth:// URI to parse")
        
        parse_btn = tk.Button(row_frame3, text="📱 Parse URI", command=parse_otp_uri,
                             bg=colors["accent"], fg="white", relief=tk.FLAT, cursor='hand2', padx=8)
        parse_btn.pack(side=tk.RIGHT, padx=5)
        
        # OTP Type
        row_frame7 = tk.Frame(otp_frame, bg=colors["bg"])
        row_frame7.pack(fill=tk.X, pady=5)
        
        tk.Label(row_frame7, text="OTP Type", width=15, anchor='w',
                bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT)
        
        self.otp_type = tk.StringVar(value="totp")
        type_combo = ttk.Combobox(row_frame7, textvariable=self.otp_type,
                                   values=["totp", "steam", "yandex", "motp"], width=15)
        type_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Algorithm
        row_frame4 = tk.Frame(otp_frame, bg=colors["bg"])
        row_frame4.pack(fill=tk.X, pady=5)
        
        tk.Label(row_frame4, text="Algorithm", width=15, anchor='w',
                bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT)
        
        self.totp_algorithm = tk.StringVar(value="SHA1")
        algo_combo = ttk.Combobox(row_frame4, textvariable=self.totp_algorithm,
                                   values=["SHA1", "SHA256", "SHA512", "MD5"], width=15)
        algo_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Digits
        row_frame5 = tk.Frame(otp_frame, bg=colors["bg"])
        row_frame5.pack(fill=tk.X, pady=5)
        
        tk.Label(row_frame5, text="Digits", width=15, anchor='w',
                bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT)
        
        self.totp_digits = tk.StringVar(value="6")
        digits_combo = ttk.Combobox(row_frame5, textvariable=self.totp_digits,
                                     values=["6", "8"], width=15)
        digits_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Period
        row_frame6 = tk.Frame(otp_frame, bg=colors["bg"])
        row_frame6.pack(fill=tk.X, pady=5)
        
        tk.Label(row_frame6, text="Period (seconds)", width=15, anchor='w',
                bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT)
        
        self.totp_period = tk.StringVar(value="30")
        period_combo = ttk.Combobox(row_frame6, textvariable=self.totp_period,
                                     values=["30", "60"], width=15)
        period_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Test OTP button
        def test_otp():
            secret = self.totp_entry.get().strip()
            if not secret:
                messagebox.showwarning("No Secret", "Enter an OTP secret first")
                return
            
            try:
                from ..features.totp import TOTP
                
                totp = TOTP(secret=secret,
                           digits=int(self.totp_digits.get()),
                           interval=int(self.totp_period.get()),
                           algorithm=self.totp_algorithm.get(),
                           otp_type=self.otp_type.get())
                
                code = totp.get_current_code()
                remaining = totp.get_time_remaining()
                
                messagebox.showinfo("OTP Test", 
                    f"✓ Current code: {code}\n"
                    f"  Expires in: {remaining} seconds\n\n"
                    f"  Type: {self.otp_type.get()}\n"
                    f"  Algorithm: {self.totp_algorithm.get()}\n"
                    f"  Digits: {self.totp_digits.get()}\n"
                    f"  Period: {self.totp_period.get()}s")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid secret: {str(e)}")
        
        test_btn = tk.Button(otp_frame, text="🔢 Test Code", command=test_otp,
                            bg=colors["success"], fg="white", relief=tk.FLAT, cursor='hand2', padx=10)
        test_btn.pack(pady=5)
    
    def create_uris_section(self, parent):
        colors = self.get_colors()
        section = tk.LabelFrame(parent, text="Websites (URIs)", bg=colors["bg"], fg=colors["fg"],
                                font=("Segoe UI", 11, "bold"), padx=15, pady=10)
        section.pack(fill=tk.X, pady=(0, 15))
        
        self.uri_container = tk.Frame(section, bg=colors["bg"])
        self.uri_container.pack(fill=tk.X)
        
        add_uri_btn = tk.Button(section, text="+ Add Website", command=self.add_uri_row,
                                bg=colors["button_bg"], fg=colors["button_fg"],
                                relief=tk.FLAT, cursor='hand2')
        add_uri_btn.pack(pady=(10, 0))
        
        # Add initial empty row
        self.add_uri_row()
    
    def add_uri_row(self, uri_value=""):
        colors = self.get_colors()
        row_frame = tk.Frame(self.uri_container, bg=colors["bg"])
        row_frame.pack(fill=tk.X, pady=2)
        
        uri_entry = tk.Entry(row_frame, width=50,
                             bg=colors["entry_bg"], fg=colors["entry_fg"],
                             insertbackground=colors["entry_fg"])
        uri_entry.insert(0, uri_value)
        uri_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        del_btn = tk.Button(row_frame, text="🗑️",
                            command=lambda: row_frame.destroy(),
                            bg=colors["danger"], fg="white",
                            relief=tk.FLAT, cursor='hand2', padx=10)
        del_btn.pack(side=tk.RIGHT, padx=2)
        
        self.uris.append(uri_entry)
    
    def create_notes_section(self, parent):
        colors = self.get_colors()
        section = tk.LabelFrame(parent, text="Notes", bg=colors["bg"], fg=colors["fg"],
                                font=("Segoe UI", 11, "bold"), padx=15, pady=10)
        section.pack(fill=tk.X, pady=(0, 15))
        
        self.notes_text = tk.Text(section, height=5, width=70,
                                  bg=colors["entry_bg"], fg=colors["entry_fg"],
                                  insertbackground=colors["entry_fg"])
        self.notes_text.pack(fill=tk.X, pady=5)
    
    def create_custom_fields_section(self, parent):
        colors = self.get_colors()
        section = tk.LabelFrame(parent, text="Custom Fields", bg=colors["bg"], fg=colors["fg"],
                                font=("Segoe UI", 11, "bold"), padx=15, pady=10)
        section.pack(fill=tk.X, pady=(0, 15))
        
        self.custom_fields_container = tk.Frame(section, bg=colors["bg"])
        self.custom_fields_container.pack(fill=tk.X)
        
        add_field_btn = tk.Button(section, text="+ Add Custom Field", command=self.add_custom_field_row,
                                  bg=colors["button_bg"], fg=colors["button_fg"],
                                  relief=tk.FLAT, cursor='hand2')
        add_field_btn.pack(pady=(10, 0))
    
    def add_custom_field_row(self, field_name="", field_value="", field_type="text"):
        colors = self.get_colors()
        
        row_frame = tk.Frame(self.custom_fields_container, bg=colors["bg"])
        row_frame.pack(fill=tk.X, pady=2)
        
        name_entry = tk.Entry(row_frame, width=20,
                              bg=colors["entry_bg"], fg=colors["entry_fg"],
                              insertbackground=colors["entry_fg"])
        name_entry.insert(0, field_name)
        name_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        type_var = tk.StringVar(value=field_type)
        type_combo = ttk.Combobox(row_frame, textvariable=type_var, 
                                   values=["text", "hidden", "boolean"], width=10)
        type_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        value_entry = tk.Entry(row_frame, width=30,
                               bg=colors["entry_bg"], fg=colors["entry_fg"],
                               insertbackground=colors["entry_fg"])
        value_entry.insert(0, field_value)
        value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        del_btn = tk.Button(row_frame, text="🗑️",
                            command=lambda: row_frame.destroy(),
                            bg=colors["danger"], fg="white",
                            relief=tk.FLAT, cursor='hand2', padx=10)
        del_btn.pack(side=tk.RIGHT)
        
        self.custom_fields.append({
            'frame': row_frame,
            'name': name_entry,
            'type': type_var,
            'value': value_entry
        })
    
    def create_attachments_section(self, parent):
        """Create attachments section with file picker"""
        colors = self.get_colors()
        
        section = tk.LabelFrame(parent, text="📎 Attachments", bg=colors["bg"], fg=colors["fg"],
                                font=("Segoe UI", 11, "bold"), padx=15, pady=10)
        section.pack(fill=tk.X, pady=(0, 15))
        
        # Button frame
        btn_frame = tk.Frame(section, bg=colors["bg"])
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add file button
        add_file_btn = tk.Button(btn_frame, text="📁 Add File", command=self.add_attachment,
                                 bg=colors["accent"], fg="white", relief=tk.FLAT, cursor='hand2',
                                 padx=15, pady=5)
        add_file_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Attachments list frame (scrollable)
        self.attachments_container = tk.Frame(section, bg=colors["bg"])
        self.attachments_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling attachments
        self.attachments_canvas = tk.Canvas(self.attachments_container, bg=colors["bg"], highlightthickness=0, height=150)
        attach_scrollbar = ttk.Scrollbar(self.attachments_container, orient=tk.VERTICAL, command=self.attachments_canvas.yview)
        self.attachments_frame = tk.Frame(self.attachments_canvas, bg=colors["bg"])
        
        self.attachments_frame.bind("<Configure>", lambda e: self.attachments_canvas.configure(scrollregion=self.attachments_canvas.bbox("all")))
        self.attachments_canvas.create_window((0, 0), window=self.attachments_frame, anchor="nw", width=700)
        self.attachments_canvas.configure(yscrollcommand=attach_scrollbar.set)
        
        self.attachments_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        attach_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel for attachments
        def on_attach_mousewheel(event):
            self.attachments_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.attachments_canvas.bind("<Enter>", lambda e: self.attachments_canvas.bind_all("<MouseWheel>", on_attach_mousewheel))
        self.attachments_canvas.bind("<Leave>", lambda e: self.attachments_canvas.unbind_all("<MouseWheel>"))
    
    def add_attachment(self):
        """Add a file attachment"""
        filepath = filedialog.askopenfilename(title="Select file to attach")
        if not filepath:
            return
        
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        
        # Read file as base64
        with open(filepath, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Get file metadata
        creation_time = os.path.getctime(filepath)
        mod_time = os.path.getmtime(filepath)
        
        self._add_attachment_row(filename, file_data, file_size, {
            'created': creation_time,
            'modified': mod_time,
            'original_path': filepath
        })
    
    def _add_attachment_row(self, filename, file_data, file_size, extra_metadata=None):
        """Add an attachment row to the UI"""
        colors = self.get_colors()
        
        row_frame = tk.Frame(self.attachments_frame, bg=colors["bg"])
        row_frame.pack(fill=tk.X, pady=2)
        
        # File icon based on extension
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.bmp': '🖼️',
            '.pdf': '📄', '.doc': '📝', '.docx': '📝', '.txt': '📃',
            '.zip': '📦', '.rar': '📦', '.7z': '📦',
            '.mp3': '🎵', '.mp4': '🎬', '.avi': '🎬', '.opus': '🎵', '.avif': '🖼️',
            '.exe': '⚙️', '.msi': '⚙️'
        }
        icon = icons.get(ext, '📎')
        
        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        # Format creation date
        date_str = ""
        if extra_metadata and extra_metadata.get('created'):
            created_date = datetime.fromtimestamp(extra_metadata['created']).strftime("%Y-%m-%d")
            date_str = f" | 📅 {created_date}"
        
        # File info label
        info_label = tk.Label(row_frame, text=f"{icon} {filename} ({size_str}){date_str}",
                              bg=colors["bg"], fg=colors["fg"], anchor='w', font=("Segoe UI", 9))
        info_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Delete button
        def delete_attachment():
            if messagebox.askyesno("Confirm Delete", f"Remove '{filename}' from this entry?"):
                row_frame.destroy()
                for i, att in enumerate(self.attachments):
                    if att['filename'] == filename:
                        self.attachments.pop(i)
                        break
        
        del_btn = tk.Button(row_frame, text="🗑️", command=delete_attachment,
                            bg=colors["danger"], fg="white",
                            relief=tk.FLAT, cursor='hand2', padx=8)
        del_btn.pack(side=tk.RIGHT, padx=2)
        
        # Store attachment data
        self.attachments.append({
            'filename': filename,
            'data': file_data,
            'size': file_size,
            'frame': row_frame,
            'metadata': extra_metadata or {}
        })
    
    def load_existing_data(self):
        """Load existing entry data including attachments, OTP, and saved time offset"""
        if not self.existing_entry:
            return
        
        # Load basic data
        self.name_entry.insert(0, self.existing_entry.get('title', ''))
        self.icon_var.set(self.existing_entry.get('icon_emoji', '🔐'))
        self.username_entry.insert(0, self.existing_entry.get('username', ''))
        self.password_entry.insert(0, self.existing_entry.get('password', ''))
        
        # Load OTP data
        totp_secret = self.existing_entry.get('totp_secret', '')
        if totp_secret:
            self.totp_entry.insert(0, totp_secret)
            
            # Load saved OTP parameters including time offset
            custom_fields = self.existing_entry.get('custom_fields', {})
            if not isinstance(custom_fields, dict):
                custom_fields = {}
            
            totp_params = custom_fields.get('_totp_params', {})
            if not isinstance(totp_params, dict):
                totp_params = {}
            
            # Set OTP type if valid
            otp_type = totp_params.get('type', 'totp')
            if otp_type in ["totp", "steam", "yandex", "motp"]:
                self.otp_type.set(otp_type)
            
            # Set algorithm
            algorithm = totp_params.get('algorithm', 'SHA1')
            if algorithm in ["SHA1", "SHA256", "SHA512", "MD5"]:
                self.totp_algorithm.set(algorithm)
            
            # Set digits
            digits = totp_params.get('digits', 6)
            self.totp_digits.set(str(digits))
            
            # Set period
            period = totp_params.get('period', 30)
            self.totp_period.set(str(period))
            
            # Load saved time offset (for drift correction)
            saved_offset = totp_params.get('time_offset', 0)
            print(f"📱 Loaded TOTP time offset: {saved_offset:+d}s for {self.existing_entry.get('title')}")
        
        # Load notes
        notes = self.existing_entry.get('notes', '')
        if notes:
            self.notes_text.insert(1.0, notes)
        
        # Load URIs
        url = self.existing_entry.get('url', '')
        if url:
            self.add_uri_row(url)
        
        # Load custom fields (skip special internal ones)
        custom_fields = self.existing_entry.get('custom_fields', {})
        if isinstance(custom_fields, dict):
            for field_name, field_data in custom_fields.items():
                if field_name not in ['additional_uris', 'card', 'identity', 'ssh', '_totp_params', '_otp_params']:
                    if isinstance(field_data, dict):
                        field_value = field_data.get('value', '')
                        field_type = field_data.get('type', 'text')
                    else:
                        field_value = str(field_data)
                        field_type = 'text'
                    self.add_custom_field_row(field_name, str(field_value), field_type)
            
            # Load additional URIs from custom fields
            additional_uris = custom_fields.get('additional_uris', {})
            if isinstance(additional_uris, dict):
                uris_list = additional_uris.get('value', [])
                if isinstance(uris_list, list):
                    for uri in uris_list:
                        if uri:
                            self.add_uri_row(uri)
        
        # Load attachments
        attachments = self.existing_entry.get('attachments', [])
        if isinstance(attachments, list):
            for att in attachments:
                if att.get('data'):
                    self._add_attachment_row(
                        att.get('filename', 'unknown'),
                        att.get('data', ''),
                        att.get('size', 0),
                        att.get('metadata', {})
                    )


    def save_entry(self):
        """Save the entry including attachments, OTP, and time offset"""
        entry_title = self.name_entry.get().strip()
        if not entry_title:
            messagebox.showerror("Error", "Name is required")
            return
        
        # Collect URIs
        uris = [entry.get().strip() for entry in self.uris if entry.get().strip()]
        primary_uri = uris[0] if uris else ''
        
        # Collect custom fields
        custom_fields = {}
        for field in self.custom_fields:
            field_name = field['name'].get().strip()
            if not field_name:
                continue
            
            field_type = field['type'].get()
            field_value = field['value'].get()
            
            custom_fields[field_name] = {
                'value': field_value,
                'type': field_type,
                'hidden': field_type == 'hidden'
            }
        
        # Add additional URIs to custom fields
        if len(uris) > 1:
            custom_fields['additional_uris'] = {
                'value': uris[1:],
                'type': 'list',
                'hidden': False
            }
        
        # Store OTP parameters if secret exists
        otp_secret = self.totp_entry.get().strip()
        if otp_secret:
            # Try to get existing time offset if this is an update
            saved_offset = 0
            if self.existing_entry:
                existing_custom = self.existing_entry.get('custom_fields', {})
                if isinstance(existing_custom, dict):
                    existing_params = existing_custom.get('_totp_params', {})
                    if isinstance(existing_params, dict):
                        saved_offset = existing_params.get('time_offset', 0)
            
            # Store as a proper dictionary
            custom_fields['_totp_params'] = {
                'type': self.otp_type.get(),
                'algorithm': self.totp_algorithm.get(),
                'digits': int(self.totp_digits.get()),
                'period': int(self.totp_period.get()),
                'time_offset': saved_offset
            }
        
        # Prepare attachments data
        attachments_data = []
        for att in self.attachments:
            attachments_data.append({
                'filename': att['filename'],
                'data': att['data'],
                'size': att['size'],
                'metadata': att.get('metadata', {})
            })
        
        entry_data = {
            'title': entry_title,
            'icon_emoji': self.icon_var.get(),
            'username': self.username_entry.get().strip(),
            'password': self.password_entry.get(),
            'url': primary_uri,
            'totp_secret': otp_secret or None,
            'notes': self.notes_text.get(1.0, tk.END).strip(),
            'is_favorite': self.existing_entry.get('is_favorite', False) if self.existing_entry else False,
            'custom_fields': custom_fields,
            'attachments': attachments_data,
            'updated_at': int(datetime.now().timestamp())
        }
        
        if not self.existing_entry:
            entry_data['created_at'] = int(datetime.now().timestamp())
            entry_data['password_strength'] = 0
            entry_data['type'] = 'login'
        
        try:
            if self.existing_entry:
                self.vault.db.update_entry(self.entry_id, entry_data)
                message = f"Entry '{entry_title}' updated successfully!"
            else:
                self.vault.db.add_entry(entry_data)
                message = f"Entry '{entry_title}' added successfully!"
            
            if hasattr(self.parent, 'refresh_entries'):
                self.parent.refresh_entries()
            
            messagebox.showinfo("Success", message)
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
