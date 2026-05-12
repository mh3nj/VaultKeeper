"""
auto_type.py - Auto-type passwords into any application
Uses Windows API to simulate keyboard input
"""

import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip

class AutoTypeEngine:
    """Handles auto-typing of credentials into any application"""
    
    def __init__(self, parent, vault_manager, dark_mode=False):
        self.parent = parent
        self.vault = vault_manager
        self.dark_mode = dark_mode
        self.is_typing = False
        self.shortcut_key = '<Control-Shift-A>'  # Default: Ctrl+Shift+A
        self.delay_between_keystrokes = 0.05  # 50ms between characters
    
    def auto_type(self, username: str, password: str, custom_format: str = "{username}{TAB}{password}{ENTER}"):
        """
        Auto-type credentials into the active window
        
        Format placeholders:
        {username} - The username/email
        {password} - The password
        {TAB} - Press Tab key
        {ENTER} - Press Enter/Return key
        {DELAY} - Short pause (0.5s)
        {CLIPBOARD} - Use clipboard instead of typing
        """
        if self.is_typing:
            return
        
        self.is_typing = True
        
        # Start in a separate thread to not block UI
        thread = threading.Thread(target=self._type_sequence, args=(username, password, custom_format))
        thread.daemon = True
        thread.start()
    
    def _type_sequence(self, username: str, password: str, format_str: str):
        """Execute the typing sequence"""
        try:
            # Give user time to focus target window
            time.sleep(2)  # 2 second delay to switch windows
            
            # Parse and execute format
            text_to_type = format_str
            text_to_type = text_to_type.replace('{username}', username)
            text_to_type = text_to_type.replace('{password}', password)
            
            # Process special commands
            import keyboard
            i = 0
            while i < len(text_to_type):
                if text_to_type[i] == '{':
                    # Find closing brace
                    end = text_to_type.find('}', i)
                    if end != -1:
                        cmd = text_to_type[i+1:end]
                        if cmd == 'TAB':
                            keyboard.press_and_release('tab')
                        elif cmd == 'ENTER':
                            keyboard.press_and_release('enter')
                        elif cmd == 'DELAY':
                            time.sleep(0.5)
                        elif cmd == 'CLIPBOARD':
                            # Use clipboard method instead of typing
                            keyboard.send('ctrl+v')  # Paste
                        i = end
                    else:
                        # No closing brace, type normally
                        keyboard.write(text_to_type[i])
                else:
                    # Normal character
                    if text_to_type[i] == '\n':
                        keyboard.press_and_release('enter')
                    else:
                        keyboard.write(text_to_type[i])
                
                # Small delay between keystrokes
                time.sleep(self.delay_between_keystrokes)
                i += 1
            
            self.is_typing = False
            
        except Exception as e:
            self.is_typing = False
            # Show error in UI thread
            self.parent.after(0, lambda: messagebox.showerror("Auto-Type Error", str(e)))
    
    def quick_auto_type(self, entry_id: int):
        """Quick auto-type using default format"""
        if self.vault and self.vault.db:
            entry = self.vault.db.get_entry(entry_id)
            if entry:
                self.auto_type(
                    entry.get('username', ''),
                    entry.get('password', ''),
                    "{username}{TAB}{password}{ENTER}"
                )
            else:
                messagebox.showwarning("No Data", "No credentials found for this entry")
        else:
            messagebox.showwarning("Not Available", "Auto-type requires a valid vault connection")


class AutoTypeDialog:
    """Dialog for configuring and using auto-type"""
    
    def __init__(self, parent, auto_type_engine, entry_id=None, entry_data=None, dark_mode=False):
        self.parent = parent
        self.auto_type = auto_type_engine
        self.entry_id = entry_id
        self.entry_data = entry_data
        self.dark_mode = dark_mode
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Auto-Type Configuration")
        self.dialog.geometry("650x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        if entry_data is None and entry_id and auto_type_engine.vault:
            self.entry_data = auto_type_engine.vault.db.get_entry(entry_id)
        
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
        """Setup the dialog UI"""
        colors = self.get_colors()
        self.dialog.configure(bg=colors["bg"])
        
        # Main frame
        main_frame = tk.Frame(self.dialog, bg=colors["bg"], padx=25, pady=25)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Label(
            main_frame, text="⌨️ Auto-Type Configuration",
            font=("Segoe UI", 18, "bold"),
            bg=colors["bg"], fg=colors["fg"]
        )
        header.pack(anchor='w', pady=(0, 10))
        
        # Info
        info = tk.Label(
            main_frame, 
            text="Auto-type will automatically type your credentials into any application.\n"
                 "You have 2 seconds to switch to the target window before typing starts.",
            font=("Segoe UI", 10),
            bg=colors["bg"], fg=colors["fg"] if self.dark_mode else '#6b7280',
            justify=tk.LEFT
        )
        info.pack(anchor='w', pady=(0, 20))
        
        # Entry info frame
        if self.entry_data:
            entry_frame = tk.LabelFrame(main_frame, text="Selected Entry", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 10, "bold"))
            entry_frame.pack(fill=tk.X, pady=(0, 15))
            
            entry_info = tk.Frame(entry_frame, bg=colors["bg"], padx=15, pady=10)
            entry_info.pack(fill=tk.X)
            
            tk.Label(entry_info, text=f"Title: {self.entry_data.get('title', 'Unknown')}",
                    bg=colors["bg"], fg=colors["fg"]).pack(anchor='w')
            tk.Label(entry_info, text=f"Username: {self.entry_data.get('username', 'N/A')}",
                    bg=colors["bg"], fg=colors["fg"]).pack(anchor='w')
        
        # Format template
        format_frame = tk.LabelFrame(main_frame, text="Typing Format", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 10, "bold"))
        format_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        format_info = tk.Frame(format_frame, bg=colors["bg"], padx=15, pady=10)
        format_info.pack(fill=tk.X)
        
        tk.Label(format_info, text="Customize how credentials are typed:", 
                bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(0, 10))
        
        # Template presets
        preset_frame = tk.Frame(format_info, bg=colors["bg"])
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(preset_frame, text="Presets:", bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT, padx=(0, 10))
        
        presets = [
            ("Standard Login", "{username}{TAB}{password}{ENTER}"),
            ("Username Only", "{username}{ENTER}"),
            ("Password Only", "{password}{ENTER}"),
            ("With Clipboard", "{CLIPBOARD}{ENTER}"),
            ("Email+Password", "{username}{TAB}{password}{TAB}{ENTER}"),
            ("Slow Typing", "{DELAY}{username}{DELAY}{TAB}{DELAY}{password}{DELAY}{ENTER}"),
        ]
        
        self.format_var = tk.StringVar(value="{username}{TAB}{password}{ENTER}")
        self.format_entry = None
        
        def set_preset(format_str):
            self.format_var.set(format_str)
            if self.format_entry:
                self.format_entry.delete(0, tk.END)
                self.format_entry.insert(0, format_str)
        
        preset_combo = ttk.Combobox(preset_frame, values=[p[0] for p in presets], width=20, state="readonly")
        preset_combo.pack(side=tk.LEFT)
        preset_combo.bind('<<ComboboxSelected>>', lambda e: set_preset(dict(presets)[preset_combo.get()]))
        
        # Custom format entry
        tk.Label(format_info, text="Custom Format:", bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(10, 5))
        self.format_entry = tk.Entry(format_info, textvariable=self.format_var, width=60,
                                     bg=colors["entry_bg"], fg=colors["entry_fg"],
                                     font=("Courier", 10))
        self.format_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Format help
        help_text = """Available placeholders:
{username} - Insert username
{password} - Insert password
{TAB} - Press Tab key
{ENTER} - Press Enter/Return
{DELAY} - Wait 0.5 seconds
{CLIPBOARD} - Paste from clipboard (faster for long passwords)"""
        
        help_label = tk.Label(format_info, text=help_text, font=("Segoe UI", 9),
                              bg=colors["bg"], fg=colors["fg"] if self.dark_mode else '#6b7280',
                              justify=tk.LEFT)
        help_label.pack(anchor='w')
        
        # Settings frame
        settings_frame = tk.LabelFrame(main_frame, text="Settings", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 10, "bold"))
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        settings_inner = tk.Frame(settings_frame, bg=colors["bg"], padx=15, pady=10)
        settings_inner.pack(fill=tk.X)
        
        # Typing speed
        tk.Label(settings_inner, text="Typing speed (seconds between characters):", 
                bg=colors["bg"], fg=colors["fg"]).pack(anchor='w')
        self.speed_var = tk.DoubleVar(value=self.auto_type.delay_between_keystrokes)
        speed_scale = tk.Scale(settings_inner, from_=0.01, to=0.2, resolution=0.01,
                               orient=tk.HORIZONTAL, variable=self.speed_var,
                               bg=colors["bg"], fg=colors["fg"], length=300)
        speed_scale.pack(anchor='w', pady=(5, 10))
        
        # Delay before typing
        tk.Label(settings_inner, text="Delay before typing (seconds):", 
                bg=colors["bg"], fg=colors["fg"]).pack(anchor='w')
        self.delay_var = tk.IntVar(value=2)
        delay_spin = tk.Spinbox(settings_inner, from_=1, to=10, textvariable=self.delay_var,
                                width=10, bg=colors["entry_bg"], fg=colors["entry_fg"])
        delay_spin.pack(anchor='w', pady=(5, 0))
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=colors["bg"])
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        def start_auto_type():
            self.auto_type.delay_between_keystrokes = self.speed_var.get()
            self.auto_type.auto_type(
                self.entry_data.get('username', '') if self.entry_data else '',
                self.entry_data.get('password', '') if self.entry_data else '',
                self.format_var.get()
            )
            self.dialog.destroy()
        
        def save_as_default():
            self.auto_type.delay_between_keystrokes = self.speed_var.get()
            # Save to entry if we have one
            if self.entry_id and self.auto_type.vault:
                self.auto_type.vault.db.update_entry(self.entry_id, {
                    'auto_type_format': self.format_var.get(),
                    'auto_type_delay': self.delay_var.get()
                })
            messagebox.showinfo("Saved", "Auto-type settings saved for this entry!")
        
        start_btn = tk.Button(
            button_frame, text="🚀 Start Auto-Type", command=start_auto_type,
            bg=colors["accent"], fg="white", padx=20, pady=8,
            relief=tk.FLAT, cursor='hand2', font=("Segoe UI", 10, "bold")
        )
        start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_btn = tk.Button(
            button_frame, text="💾 Save as Default", command=save_as_default,
            bg=colors["success"], fg="white", padx=15, pady=8,
            relief=tk.FLAT, cursor='hand2'
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = tk.Button(
            button_frame, text="Cancel", command=self.dialog.destroy,
            bg=colors["button_bg"], fg=colors["button_fg"], padx=20, pady=8,
            relief=tk.FLAT, cursor='hand2'
        )
        cancel_btn.pack(side=tk.LEFT)
        
        # Keyboard shortcut info
        shortcut_frame = tk.Frame(main_frame, bg=colors["bg"])
        shortcut_frame.pack(fill=tk.X)
        
        shortcut_info = tk.Label(
            shortcut_frame, 
            text="💡 Tip: You can also auto-type by selecting an entry and pressing Ctrl+Shift+A",
            font=("Segoe UI", 9),
            bg=colors["bg"], fg=colors["warning"]
        )
        shortcut_info.pack()


class GlobalHotkey:
    """Register global hotkey for auto-type"""
    
    def __init__(self, auto_type_engine):
        self.auto_type = auto_type_engine
        self.hotkey_registered = False
        self.current_hotkey = None
    
    def register_hotkey(self, hotkey='ctrl+shift+a'):
        """Register a global hotkey using keyboard library"""
        try:
            import keyboard
            keyboard.remove_hotkey(self.current_hotkey) if self.current_hotkey else None
            self.current_hotkey = keyboard.add_hotkey(hotkey, self._on_hotkey)
            self.hotkey_registered = True
            return True
        except ImportError:
            return False
        except:
            return False
    
    def _on_hotkey(self):
        """Called when hotkey is pressed"""
        # This would need to get the currently selected entry
        # Implementation depends on main window integration
        pass
