"""
import_export_dialog.py - Import/Export vault data
Supports Bitwarden JSON, LastPass CSV, and encrypted VaultKeeper format
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import os
from datetime import datetime

class ImportExportDialog:
    """Dialog for importing and exporting vault data"""
    
    def __init__(self, parent, dark_mode=False, vault_manager=None):
        self.parent = parent
        self.dark_mode = dark_mode
        self.vault = vault_manager
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Import/Export - VaultKeeper")
        self.dialog.geometry("800x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
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
        """Setup the UI with notebook tabs"""
        colors = self.get_colors()
        self.dialog.configure(bg=colors["bg"])
        
        # Main frame
        main_frame = tk.Frame(self.dialog, bg=colors["bg"], padx=25, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Label(
            main_frame, text="📋 Import / Export Vault",
            font=("Segoe UI", 18, "bold"),
            bg=colors["bg"], fg=colors["fg"]
        )
        header.pack(anchor='w', pady=(0, 20))
        
        # Tab control
        tab_control = ttk.Notebook(main_frame)
        
        # Export Tab
        export_tab = tk.Frame(tab_control)
        export_tab.configure(bg=colors["bg"])
        tab_control.add(export_tab, text="📤 Export")
        self.setup_export_tab(export_tab)
        
        # Import Tab
        import_tab = tk.Frame(tab_control)
        import_tab.configure(bg=colors["bg"])
        tab_control.add(import_tab, text="📥 Import")
        self.setup_import_tab(import_tab)
        
        # Backup Tab
        backup_tab = tk.Frame(tab_control)
        backup_tab.configure(bg=colors["bg"])
        tab_control.add(backup_tab, text="💾 Backup")
        self.setup_backup_tab(backup_tab)
        
        tab_control.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Close button
        close_btn = tk.Button(
            main_frame, text="Close", command=self.dialog.destroy,
            bg=colors["button_bg"], fg=colors["button_fg"],
            relief=tk.FLAT, cursor='hand2', padx=25, pady=8
        )
        close_btn.pack()
    
    def _export_txt(self, entries, filename):
        """Export to plain text file for mobile sharing"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("VAULTKEEPER EXPORT - PASSWORD MANAGER\n")
            f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            for entry in entries:
                f.write(f"📁 {entry.get('title', 'Untitled')}\n")
                f.write(f"   Username: {entry.get('username', 'N/A')}\n")
                f.write(f"   Password: {entry.get('password', 'N/A')}\n")
                if entry.get('url'):
                    f.write(f"   URL: {entry.get('url')}\n")
                if entry.get('notes'):
                    f.write(f"   Notes: {entry.get('notes')}\n")
                
                # Custom fields
                custom_fields = entry.get('custom_fields', {})
                if custom_fields:
                    f.write("   Custom Fields:\n")
                    for field_name, field_data in custom_fields.items():
                        value = field_data.get('value', '') if isinstance(field_data, dict) else str(field_data)
                        f.write(f"      • {field_name}: {value}\n")
                
                f.write("\n" + "-" * 40 + "\n\n")
            
            f.write(f"\nTotal entries: {len(entries)}\n")
            f.write("=" * 60 + "\n")
            f.write("⚠️ This file contains plaintext passwords! Keep it secure.\n")

    def setup_export_tab(self, parent):
        """Setup export options"""
        colors = self.get_colors()
        
        frame = tk.Frame(parent, bg=colors["bg"], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Export formats
        tk.Label(
            frame, text="Export Format:",
            font=("Segoe UI", 12, "bold"),
            bg=colors["bg"], fg=colors["fg"]
        ).pack(anchor='w', pady=(0, 15))
        
        self.export_format = tk.StringVar(value="vaultkeeper")
        
        formats_frame = tk.Frame(frame, bg=colors["bg"])
        formats_frame.pack(anchor='w', pady=(0, 20))
        
        formats = [
            ("🔐 VaultKeeper Encrypted (.vault) - Recommended", "vaultkeeper"),
            ("📄 Bitwarden JSON (.json)", "bitwarden"),
            ("📊 LastPass CSV (.csv)", "lastpass"),
            ("📋 Plain Text (.txt) - For mobile", "txt"),
            ("📋 Plain JSON (Unencrypted - Not Recommended)", "plain"),
        ]
        
        for text, value in formats:
            tk.Radiobutton(
                formats_frame, text=text, variable=self.export_format, value=value,
                bg=colors["bg"], fg=colors["fg"],
                selectcolor=colors["bg"], anchor='w',
                padx=10, pady=5
            ).pack(fill=tk.X)
        
        # Export button
        export_btn = tk.Button(
            frame, text="📤 Export Vault", command=self.export_vault,
            bg=colors["accent"], fg="white", padx=30, pady=10,
            relief=tk.FLAT, cursor='hand2', font=("Segoe UI", 11, "bold")
        )
        export_btn.pack(pady=30)
    
    def setup_import_tab(self, parent):
        """Setup import options"""
        colors = self.get_colors()
        
        frame = tk.Frame(parent, bg=colors["bg"], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Import formats
        tk.Label(
            frame, text="Import Format:",
            font=("Segoe UI", 12, "bold"),
            bg=colors["bg"], fg=colors["fg"]
        ).pack(anchor='w', pady=(0, 15))
        
        self.import_format = tk.StringVar(value="bitwarden")
        
        formats_frame = tk.Frame(frame, bg=colors["bg"])
        formats_frame.pack(anchor='w', pady=(0, 20))
        
        formats = [
            ("📄 Bitwarden JSON (.json)", "bitwarden"),
            ("📊 LastPass CSV (.csv)", "lastpass"),
            ("🔐 VaultKeeper Encrypted (.vault)", "vaultkeeper"),
            ("📋 Plain JSON (.json)", "plain"),
        ]
        
        for text, value in formats:
            tk.Radiobutton(
                formats_frame, text=text, variable=self.import_format, value=value,
                bg=colors["bg"], fg=colors["fg"],
                selectcolor=colors["bg"], anchor='w',
                padx=10, pady=5
            ).pack(fill=tk.X)
        
        # Import button
        import_btn = tk.Button(
            frame, text="📥 Import File", command=self.import_vault,
            bg=colors["accent"], fg="white", padx=30, pady=10,
            relief=tk.FLAT, cursor='hand2', font=("Segoe UI", 11, "bold")
        )
        import_btn.pack(pady=30)
        
        # Warning
        warning_text = "⚠️ Import will MERGE data with your existing vault. Duplicates skipped based on title."
        warning_label = tk.Label(
            frame, text=warning_text, font=("Segoe UI", 9),
            bg=colors["entry_bg"], fg=colors["danger"],
            justify=tk.LEFT, padx=15, pady=10
        )
        warning_label.pack(fill=tk.X)
    
    def setup_backup_tab(self, parent):
        """Setup backup and restore options"""
        colors = self.get_colors()
        
        frame = tk.Frame(parent, bg=colors["bg"], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Backup section
        backup_frame = tk.LabelFrame(frame, text="💾 Create Backup", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 11, "bold"))
        backup_frame.pack(fill=tk.X, pady=(0, 20), padx=10)
        
        backup_info = tk.Label(
            backup_frame, text="Create an encrypted backup of your entire vault.",
            bg=colors["bg"], fg=colors["fg"], padx=15, pady=10
        )
        backup_info.pack(anchor='w')
        
        backup_btn = tk.Button(
            backup_frame, text="💾 Create Backup", command=self.create_backup,
            bg=colors["success"], fg="white", padx=20, pady=8,
            relief=tk.FLAT, cursor='hand2'
        )
        backup_btn.pack(pady=10, padx=15, anchor='w')
        
        # Restore section
        restore_frame = tk.LabelFrame(frame, text="🔄 Restore from Backup", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 11, "bold"))
        restore_frame.pack(fill=tk.X, pady=(0, 20), padx=10)
        
        restore_info = tk.Label(
            restore_frame, text="⚠️ This will REPLACE your current vault! Make sure you have a backup first.",
            bg=colors["bg"], fg=colors["warning"], padx=15, pady=10
        )
        restore_info.pack(anchor='w')
        
        restore_btn = tk.Button(
            restore_frame, text="🔄 Restore from Backup", command=self.restore_backup,
            bg=colors["warning"], fg="white", padx=20, pady=8,
            relief=tk.FLAT, cursor='hand2'
        )
        restore_btn.pack(pady=10, padx=15, anchor='w')
    
    def export_vault(self):
        """Export vault in selected format"""
        export_type = self.export_format.get()
        
        extensions = {
            "vaultkeeper": ".vault",
            "bitwarden": ".json",
            "lastpass": ".csv",
            "txt": ".txt",
            "plain": ".json"
        }
        
        filetypes = {
            "vaultkeeper": [("VaultKeeper Vault", "*.vault"), ("All files", "*.*")],
            "bitwarden": [("Bitwarden JSON", "*.json"), ("All files", "*.*")],
            "lastpass": [("LastPass CSV", "*.csv"), ("All files", "*.*")],
            "plain": [("JSON files", "*.json"), ("All files", "*.*")]
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=extensions.get(export_type, ".json"),
            filetypes=filetypes.get(export_type, [("All files", "*.*")]),
            title="Export Vault"
        )
        
        if not filename:
            return
        
        try:
            entries = self.vault.db.get_all_entries() if self.vault and self.vault.db else []
            
            if export_type == "vaultkeeper":
                self._export_vaultkeeper(entries, filename)
            elif export_type == "bitwarden":
                self._export_bitwarden(entries, filename)
            elif export_type == "txt":
                self._export_txt(entries, filename)
            elif export_type == "lastpass":
                self._export_lastpass(entries, filename)
            else:
                self._export_plain(entries, filename)
            
            messagebox.showinfo("Export Complete", f"Exported {len(entries)} entries to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
    
    def _export_vaultkeeper(self, entries, filename):
        """Export to VaultKeeper format"""
        import json
        export_data = {'version': 1, 'exported_at': datetime.now().isoformat(), 'entries': entries}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
    
    def _export_bitwarden(self, entries, filename):
        """Export to Bitwarden JSON format"""
        bitwarden_data = {"encrypted": False, "folders": [], "items": []}
        for entry in entries:
            item = {
                "type": 1, "name": entry.get('title', ''),
                "login": {"username": entry.get('username', ''), "password": entry.get('password', '')},
                "notes": entry.get('notes', ''), "favorite": entry.get('is_favorite', False)
            }
            if entry.get('url'):
                item["login"]["uris"] = [{"uri": entry['url']}]
            bitwarden_data['items'].append(item)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(bitwarden_data, f, indent=2)
    
    def _export_lastpass(self, entries, filename):
        """Export to LastPass CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['url', 'username', 'password', 'name', 'notes'])
            for entry in entries:
                writer.writerow([entry.get('url', ''), entry.get('username', ''), 
                               entry.get('password', ''), entry.get('title', ''), entry.get('notes', '')])
    
    def _export_plain(self, entries, filename):
        """Export to plain JSON"""
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2)
    
    def import_vault(self):
        """Import vault from file"""
        import_type = self.import_format.get()
        
        filetypes = {
            "bitwarden": [("Bitwarden JSON", "*.json"), ("All files", "*.*")],
            "lastpass": [("LastPass CSV", "*.csv"), ("All files", "*.*")],
            "vaultkeeper": [("VaultKeeper Vault", "*.vault"), ("All files", "*.*")],
            "plain": [("JSON files", "*.json"), ("All files", "*.*")]
        }
        
        filename = filedialog.askopenfilename(
            filetypes=filetypes.get(import_type, [("All files", "*.*")]),
            title="Import File"
        )
        
        if not filename:
            return
        
        if not messagebox.askyesno("Confirm Import", "This will MERGE data with your existing vault.\nDuplicates will be skipped.\n\nContinue?"):
            return
        
        try:
            imported_count = 0
            
            if import_type == "bitwarden":
                imported_count = self._import_bitwarden_simple(filename)
            elif import_type == "lastpass":
                imported_count = self._import_lastpass_simple(filename)
            elif import_type == "vaultkeeper":
                imported_count = self._import_vaultkeeper_simple(filename)
            else:
                imported_count = self._import_plain_simple(filename)
            
            # Refresh the main window
            if hasattr(self.parent, 'refresh_entries'):
                self.parent.refresh_entries()
            
            messagebox.showinfo("Import Complete", f"✅ Imported {imported_count} new entries!")
            
        except Exception as e:
            messagebox.showerror("Import Failed", f"Error: {str(e)}")
    
    def _import_bitwarden_simple(self, filename):
        """Import Bitwarden JSON with full custom fields support"""
        import json
        from datetime import datetime
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_count = 0
        existing_titles = set()
        
        # Get existing titles
        if self.vault and self.vault.db:
            existing = self.vault.db.get_all_entries()
            existing_titles = {e.get('title', '').lower() for e in existing}
        
        # Field type mapping
        # 0 = Text, 1 = Hidden, 2 = Boolean, 3 = Linked
        field_type_names = {
            0: 'text',
            1: 'hidden', 
            2: 'boolean',
            3: 'linked'
        }
        
        for item in data.get('items', []):
            title = item.get('name', 'Untitled')
            
            # Skip duplicates
            if title.lower() in existing_titles:
                print(f"⏭️ Skipping duplicate: {title}")
                continue
            
            login = item.get('login', {})
            uris = login.get('uris', [])
            url = uris[0].get('uri', '') if uris else ''
            
            # Parse custom fields from Bitwarden 'fields' array
            custom_fields = {}
            bitwarden_fields = item.get('fields', [])
            
            for field in bitwarden_fields:
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                field_type = field.get('type', 0)
                
                if field_name:
                    # Handle boolean type
                    if field_type == 2:  # Boolean
                        field_value = field_value.lower() == 'true' if field_value else False
                    
                    custom_fields[field_name] = {
                        'value': field_value,
                        'type': field_type_names.get(field_type, 'text'),
                        'hidden': field_type == 1  # Hidden type
                    }
            
            # Also check for any additional fields in the item that might be custom
            # Some Bitwarden exports put custom data elsewhere
            for key, value in item.items():
                if key not in ['id', 'type', 'name', 'notes', 'favorite', 'fields', 'login', 
                            'collectionIds', 'organizationId', 'folderId', 'revisionDate', 
                            'creationDate', 'reprompt', 'passwordHistory']:
                    if value and key not in custom_fields:
                        custom_fields[key] = {
                            'value': str(value),
                            'type': 'text',
                            'hidden': False
                        }
            
            # Extract TOTP secret
            totp_secret = login.get('totp')
            if totp_secret:
                # TOTP secret might be in format "otpauth://totp/...?secret=XXXXX"
                import re
                match = re.search(r'secret=([A-Z2-7]+)', totp_secret)
                if match:
                    totp_secret = match.group(1)
            
            # Build entry
            entry = {
                'title': title,
                'username': login.get('username', ''),
                'password': login.get('password', ''),
                'url': url,
                'notes': item.get('notes', ''),
                'is_favorite': item.get('favorite', False),
                'totp_secret': totp_secret,
                'type': self._get_item_type_name(item.get('type', 1)),
                'created_at': self._parse_timestamp(item.get('creationDate')),
                'updated_at': self._parse_timestamp(item.get('revisionDate')),
                'password_strength': 0,
                'icon_emoji': self._get_icon_for_type(item.get('type', 1)),
                'custom_fields': custom_fields
            }
            
            # Add additional URIs
            if len(uris) > 1:
                additional_uris = [u.get('uri', '') for u in uris[1:] if u.get('uri')]
                if additional_uris:
                    entry['custom_fields']['additional_uris'] = {
                        'value': additional_uris,
                        'type': 'list',
                        'hidden': False
                    }
            
            try:
                self.vault.db.add_entry(entry)
                imported_count += 1
                existing_titles.add(title.lower())
                
                # Print custom fields info for debugging
                if custom_fields:
                    print(f"✅ Imported: {title} with {len(custom_fields)} custom field(s)")
                    for cf_name, cf_data in custom_fields.items():
                        print(f"     - {cf_name}: {cf_data.get('value', '')[:30]}...")
                else:
                    print(f"✅ Imported: {title}")
                    
            except Exception as e:
                print(f"❌ Failed: {title} - {e}")
        
        return imported_count

    def _get_item_type_name(self, item_type):
        """Get item type name from Bitwarden type number"""
        types = {
            1: 'login',
            2: 'card',
            3: 'identity',
            4: 'note',
            5: 'ssh_key'
        }
        return types.get(item_type, 'login')

    def _get_icon_for_type(self, item_type):
        """Get emoji icon based on item type"""
        icons = {
            1: '🔐',  # login
            2: '💳',  # card
            3: '👤',  # identity
            4: '📝',  # note
            5: '🔑'   # ssh_key
        }
        return icons.get(item_type, '🔐')

    def _parse_timestamp(self, timestamp_str):
        """Parse ISO timestamp to Unix timestamp"""
        from datetime import datetime
        if not timestamp_str:
            return int(datetime.now().timestamp())
        
        try:
            # Handle Zulu time
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            dt = datetime.fromisoformat(timestamp_str)
            return int(dt.timestamp())
        except:
            return int(datetime.now().timestamp())
    
    def _import_lastpass_simple(self, filename):
        """Simple LastPass CSV import"""
        imported_count = 0
        existing_titles = set()
        
        if self.vault and self.vault.db:
            existing = self.vault.db.get_all_entries()
            existing_titles = {e.get('title', '').lower() for e in existing}
        
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row.get('name', row.get('url', 'Untitled'))
                
                if title.lower() in existing_titles:
                    continue
                
                entry = {
                    'title': title,
                    'username': row.get('username', ''),
                    'password': row.get('password', ''),
                    'url': row.get('url', ''),
                    'notes': row.get('notes', ''),
                    'type': 'login',
                    'created_at': int(datetime.now().timestamp()),
                    'updated_at': int(datetime.now().timestamp()),
                    'icon_emoji': '🔐'
                }
                
                try:
                    self.vault.db.add_entry(entry)
                    imported_count += 1
                    existing_titles.add(title.lower())
                except Exception as e:
                    print(f"❌ Failed: {title} - {e}")
        
        return imported_count
    
    def _import_vaultkeeper_simple(self, filename):
        """Import from VaultKeeper format"""
        import json
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entries = data.get('entries', [])
        imported_count = 0
        existing_titles = set()
        
        if self.vault and self.vault.db:
            existing = self.vault.db.get_all_entries()
            existing_titles = {e.get('title', '').lower() for e in existing}
        
        for entry in entries:
            title = entry.get('title', 'Untitled')
            if title.lower() in existing_titles:
                continue
            
            entry['created_at'] = int(datetime.now().timestamp())
            entry['updated_at'] = int(datetime.now().timestamp())
            
            try:
                self.vault.db.add_entry(entry)
                imported_count += 1
                existing_titles.add(title.lower())
            except Exception as e:
                print(f"❌ Failed: {title} - {e}")
        
        return imported_count
    
    def _import_plain_simple(self, filename):
        """Import from plain JSON"""
        import json
        with open(filename, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        imported_count = 0
        existing_titles = set()
        
        if self.vault and self.vault.db:
            existing = self.vault.db.get_all_entries()
            existing_titles = {e.get('title', '').lower() for e in existing}
        
        for entry in entries:
            title = entry.get('title', 'Untitled')
            if title.lower() in existing_titles:
                continue
            
            entry['created_at'] = int(datetime.now().timestamp())
            entry['updated_at'] = int(datetime.now().timestamp())
            
            try:
                self.vault.db.add_entry(entry)
                imported_count += 1
                existing_titles.add(title.lower())
            except Exception as e:
                print(f"❌ Failed: {title} - {e}")
        
        return imported_count
    
    def create_backup(self):
        """Create a backup of the vault"""
        backup_dir = os.path.expanduser("~/Documents/VaultKeeper/Backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.vaultbackup")
        
        try:
            entries = self.vault.db.get_all_entries() if self.vault and self.vault.db else []
            
            backup_data = {
                'version': 1,
                'backup_date': datetime.now().isoformat(),
                'entries': entries,
                'entry_count': len(entries)
            }
            
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
            
            messagebox.showinfo("Backup Complete", f"Backup saved to:\n{filename}\n\n{len(entries)} entries backed up.")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))
    
    def restore_backup(self):
        """Restore from backup"""
        filename = filedialog.askopenfilename(
            filetypes=[("VaultKeeper Backup", "*.vaultbackup"), ("All files", "*.*")],
            title="Restore from Backup"
        )
        
        if not filename:
            return
        
        if not messagebox.askyesno("Confirm Restore", 
            "⚠️ WARNING: This will REPLACE your current vault!\nAll current data will be lost.\n\nContinue?"):
            return
        
        try:
            import json
            with open(filename, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            entries = backup_data.get('entries', [])
            
            # Clear existing vault
            if self.vault and self.vault.db:
                existing = self.vault.db.get_all_entries()
                for e in existing:
                    self.vault.db.delete_entry(e['id'])
                
                # Restore entries
                for entry in entries:
                    if 'id' in entry:
                        del entry['id']
                    self.vault.db.add_entry(entry)
            
            # Refresh the main window
            if hasattr(self.parent, 'refresh_entries'):
                self.parent.refresh_entries()
            
            messagebox.showinfo("Restore Complete", f"Restored {len(entries)} entries!")
        except Exception as e:
            messagebox.showerror("Restore Failed", str(e))
