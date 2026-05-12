"""
password_generator.py - Professional password generator dialog
With multiple generation modes: Random, Pronounceable, Diceware, PIN, Apple-style
Supports up to 4096 characters for random passwords
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
import secrets

class PasswordGeneratorDialog:
    """Professional password generator with multiple modes"""
    
    def __init__(self, parent, dark_mode=False):
        self.parent = parent
        self.dark_mode = dark_mode
        self.result_password = ""
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Password Generator")
        self.dialog.geometry("800x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.generate_password()
    
    def get_colors(self):
        """Get current colors based on dark mode"""
        if self.dark_mode:
            return {
                "bg": "#1e1e1e", "fg": "#ffffff", "entry_bg": "#3d3d3d",
                "entry_fg": "#ffffff", "button_bg": "#3d3d3d", "button_fg": "#ffffff",
                "accent": "#3b82f6", "success": "#10b981", "border": "#4a4a4a"
            }
        else:
            return {
                "bg": "#f5f5f5", "fg": "#000000", "entry_bg": "#ffffff",
                "entry_fg": "#000000", "button_bg": "#e5e7eb", "button_fg": "#000000",
                "accent": "#3b82f6", "success": "#10b981", "border": "#d1d5db"
            }
    
    def setup_ui(self):
        """Setup the generator UI"""
        colors = self.get_colors()
        self.dialog.configure(bg=colors["bg"])
        
        # Main container
        main_frame = tk.Frame(self.dialog, bg=colors["bg"], padx=25, pady=25)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(main_frame, text="🔐 Password Generator", font=("Segoe UI", 18, "bold"),
                        bg=colors["bg"], fg=colors["fg"])
        title.pack(anchor='w', pady=(0, 5))
        
        subtitle = tk.Label(main_frame, text="Generate strong, secure passwords (up to 4096 characters)",
                           font=("Segoe UI", 10), bg=colors["bg"],
                           fg=colors["fg"] if self.dark_mode else '#6b7280')
        subtitle.pack(anchor='w', pady=(0, 20))
        
        # Separator
        sep = tk.Frame(main_frame, height=1, bg=colors["border"])
        sep.pack(fill=tk.X, pady=(0, 20))
        
        # Generated password display - Text widget for long passwords
        display_frame = tk.Frame(main_frame, bg=colors["bg"])
        display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        tk.Label(display_frame, text="Generated Password:", font=("Segoe UI", 10, "bold"),
                bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(0, 5))
        
        # Text widget with scrollbar
        text_frame = tk.Frame(display_frame, bg=colors["bg"])
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.password_display = tk.Text(text_frame, font=("Courier", 10), height=10, wrap=tk.WORD,
                                        bg=colors["entry_bg"], fg=colors["entry_fg"],
                                        relief=tk.SOLID, bd=1)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.password_display.yview)
        self.password_display.configure(yscrollcommand=scrollbar.set)
        
        self.password_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Length info
        self.length_info = tk.Label(display_frame, text="", font=("Segoe UI", 9),
                                    bg=colors["bg"], fg=colors["success"])
        self.length_info.pack(anchor='w', pady=(5, 0))
        
        # Action buttons
        action_frame = tk.Frame(display_frame, bg=colors["bg"])
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.copy_btn = tk.Button(action_frame, text="📋 Copy to Clipboard", command=self.copy_password,
                                 bg=colors["accent"], fg="white", relief=tk.FLAT, cursor='hand2',
                                 padx=15, pady=5)
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_btn = tk.Button(action_frame, text="🔄 Generate New", command=self.generate_password,
                                    bg=colors["button_bg"], fg=colors["button_fg"],
                                    relief=tk.FLAT, cursor='hand2', padx=15, pady=5)
        self.refresh_btn.pack(side=tk.LEFT)
        
        # Tab control
        tab_control = ttk.Notebook(main_frame)
        
        # Tab 1: Random Password (4096 chars)
        self.random_tab = tk.Frame(tab_control, bg=colors["bg"])
        tab_control.add(self.random_tab, text="🎲 Random (4096 max)")
        self.setup_random_tab()
        
        # Tab 2: Pronounceable
        self.pronounce_tab = tk.Frame(tab_control, bg=colors["bg"])
        tab_control.add(self.pronounce_tab, text="🗣️ Pronounceable")
        self.setup_pronounce_tab()
        
        # Tab 3: Diceware
        self.diceware_tab = tk.Frame(tab_control, bg=colors["bg"])
        tab_control.add(self.diceware_tab, text="🎯 Diceware")
        self.setup_diceware_tab()
        
        # Tab 4: PIN
        self.pin_tab = tk.Frame(tab_control, bg=colors["bg"])
        tab_control.add(self.pin_tab, text="🔢 PIN")
        self.setup_pin_tab()
        
        # Tab 5: Apple-style
        self.apple_tab = tk.Frame(tab_control, bg=colors["bg"])
        tab_control.add(self.apple_tab, text="🍎 Apple-style")
        self.setup_apple_tab()
        
        tab_control.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Password strength indicator
        strength_frame = tk.Frame(main_frame, bg=colors["bg"])
        strength_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(strength_frame, text="Password Strength:", font=("Segoe UI", 10, "bold"),
                bg=colors["bg"], fg=colors["fg"]).pack(anchor='w')
        
        self.strength_bar = tk.Canvas(strength_frame, height=8, bg=colors["entry_bg"], highlightthickness=0)
        self.strength_bar.pack(fill=tk.X, pady=(5, 5))
        
        self.strength_label = tk.Label(strength_frame, text="", font=("Segoe UI", 9),
                                       bg=colors["bg"], fg=colors["fg"])
        self.strength_label.pack(anchor='w')
        
        # Close button
        close_btn = tk.Button(main_frame, text="Close", command=self.dialog.destroy,
                             bg=colors["button_bg"], fg=colors["button_fg"],
                             relief=tk.FLAT, cursor='hand2', padx=20, pady=5)
        close_btn.pack()
    
    def setup_random_tab(self):
        """Setup random password tab - TRUE 4096 character support"""
        colors = self.get_colors()
        
        # Length selector frame
        length_frame = tk.Frame(self.random_tab, bg=colors["bg"])
        length_frame.pack(fill=tk.X, pady=10, padx=20)
        
        tk.Label(length_frame, text="Password Length:", bg=colors["bg"], fg=colors["fg"],
                font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.random_length = tk.IntVar(value=128)
        
        # Scale - GOING TO 4096
        length_scale = tk.Scale(length_frame, from_=8, to=4096, orient=tk.HORIZONTAL,
                               variable=self.random_length, bg=colors["bg"], fg=colors["fg"],
                               length=350, showvalue=True, resolution=1)
        length_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Entry for exact value
        length_entry = tk.Entry(length_frame, textvariable=self.random_length, width=6,
                               bg=colors["entry_bg"], fg=colors["entry_fg"], font=("Courier", 10))
        length_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Length preset buttons
        preset_frame = tk.Frame(self.random_tab, bg=colors["bg"])
        preset_frame.pack(fill=tk.X, pady=5, padx=20)
        
        def set_length(l):
            self.random_length.set(l)
        
        presets = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
        for p in presets:
            btn = tk.Button(preset_frame, text=str(p), command=lambda l=p: set_length(l),
                           bg=colors["button_bg"], fg=colors["button_fg"],
                           relief=tk.FLAT, cursor='hand2', padx=8, pady=2)
            btn.pack(side=tk.LEFT, padx=2)
        
        # Character set options
        options_frame = tk.LabelFrame(self.random_tab, text="Character Sets", bg=colors["bg"],
                                      fg=colors["fg"], font=("Segoe UI", 10, "bold"),
                                      padx=15, pady=10)
        options_frame.pack(fill=tk.X, pady=15, padx=20)
        
        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)
        self.avoid_ambiguous = tk.BooleanVar(value=True)
        
        row1 = tk.Frame(options_frame, bg=colors["bg"])
        row1.pack(fill=tk.X)
        
        tk.Checkbutton(row1, text="Uppercase (A-Z)", variable=self.use_upper,
                      bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(row1, text="Lowercase (a-z)", variable=self.use_lower,
                      bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(side=tk.LEFT, padx=10)
        
        row2 = tk.Frame(options_frame, bg=colors["bg"])
        row2.pack(fill=tk.X, pady=5)
        
        tk.Checkbutton(row2, text="Numbers (0-9)", variable=self.use_digits,
                      bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(row2, text="Symbols (!@#$%)", variable=self.use_symbols,
                      bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(side=tk.LEFT, padx=10)
        
        tk.Checkbutton(options_frame, text="Avoid ambiguous characters (il1Lo0O)", variable=self.avoid_ambiguous,
                      bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(anchor='w', pady=5)
        
        # Generate button
        gen_btn = tk.Button(self.random_tab, text="Generate Random Password", command=self.generate_random_password,
                           bg=colors["accent"], fg="white", relief=tk.FLAT, cursor='hand2',
                           padx=25, pady=8, font=("Segoe UI", 11, "bold"))
        gen_btn.pack(pady=20)
        
        # Bind events
        self.random_length.trace('w', lambda *args: self.update_length_info())
        self.update_length_info()
    
    def update_length_info(self):
        """Update the length info display"""
        try:
            length = self.random_length.get()
            self.length_info.config(text=f"✓ Will generate {length:,} characters")
        except:
            pass
    
    def setup_pronounce_tab(self):
        """Setup pronounceable password tab"""
        colors = self.get_colors()
        
        frame = tk.Frame(self.pronounce_tab, bg=colors["bg"])
        frame.pack(fill=tk.X, pady=20, padx=20)
        
        tk.Label(frame, text="Length (characters):", bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(0, 5))
        
        self.pronounce_length = tk.IntVar(value=12)
        length_spin = tk.Spinbox(frame, from_=6, to=30, textvariable=self.pronounce_length,
                                width=10, bg=colors["entry_bg"], fg=colors["entry_fg"],
                                relief=tk.SOLID, bd=1)
        length_spin.pack(anchor='w', pady=(0, 15))
        
        gen_btn = tk.Button(frame, text="Generate Pronounceable", command=self.generate_pronounceable,
                           bg=colors["accent"], fg="white", relief=tk.FLAT, cursor='hand2',
                           padx=20, pady=5)
        gen_btn.pack(pady=10)
    
    def setup_diceware_tab(self):
        """Setup diceware passphrase tab"""
        colors = self.get_colors()
        
        frame = tk.Frame(self.diceware_tab, bg=colors["bg"])
        frame.pack(fill=tk.X, pady=20, padx=20)
        
        tk.Label(frame, text="Number of words:", bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(0, 5))
        
        self.diceware_words = tk.IntVar(value=6)
        words_spin = tk.Spinbox(frame, from_=3, to=12, textvariable=self.diceware_words,
                               width=10, bg=colors["entry_bg"], fg=colors["entry_fg"],
                               relief=tk.SOLID, bd=1)
        words_spin.pack(anchor='w', pady=(0, 15))
        
        tk.Label(frame, text="Separator:", bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(0, 5))
        
        self.diceware_sep = tk.StringVar(value=" ")
        sep_entry = tk.Entry(frame, textvariable=self.diceware_sep, width=10,
                            bg=colors["entry_bg"], fg=colors["entry_fg"],
                            relief=tk.SOLID, bd=1)
        sep_entry.pack(anchor='w', pady=(0, 15))
        
        gen_btn = tk.Button(frame, text="Generate Diceware", command=self.generate_diceware,
                           bg=colors["accent"], fg="white", relief=tk.FLAT, cursor='hand2',
                           padx=20, pady=5)
        gen_btn.pack(pady=10)
    
    def setup_pin_tab(self):
        """Setup PIN generation tab"""
        colors = self.get_colors()
        
        frame = tk.Frame(self.pin_tab, bg=colors["bg"])
        frame.pack(fill=tk.X, pady=20, padx=20)
        
        tk.Label(frame, text="PIN Length:", bg=colors["bg"], fg=colors["fg"]).pack(anchor='w', pady=(0, 5))
        
        self.pin_length = tk.IntVar(value=6)
        length_spin = tk.Spinbox(frame, from_=4, to=12, textvariable=self.pin_length,
                                width=10, bg=colors["entry_bg"], fg=colors["entry_fg"],
                                relief=tk.SOLID, bd=1)
        length_spin.pack(anchor='w', pady=(0, 15))
        
        gen_btn = tk.Button(frame, text="Generate PIN", command=self.generate_pin,
                           bg=colors["accent"], fg="white", relief=tk.FLAT, cursor='hand2',
                           padx=20, pady=5)
        gen_btn.pack(pady=10)
    
    def setup_apple_tab(self):
        """Setup Apple-style password tab"""
        colors = self.get_colors()
        
        frame = tk.Frame(self.apple_tab, bg=colors["bg"])
        frame.pack(fill=tk.X, pady=20, padx=20)
        
        info_text = """Apple-style passwords follow the pattern:
        noun-verb-number
        
        Examples:
        • grape-jump-843
        • storm-fly-521
        • river-swim-679
        
        Easy to remember, hard to guess."""
        
        info_label = tk.Label(frame, text=info_text, bg=colors["bg"],
                             fg=colors["fg"] if self.dark_mode else '#6b7280',
                             justify=tk.LEFT, font=("Segoe UI", 10))
        info_label.pack(anchor='w', pady=(0, 20))
        
        gen_btn = tk.Button(frame, text="Generate Apple-style Password", command=self.generate_apple,
                           bg=colors["accent"], fg="white", relief=tk.FLAT, cursor='hand2',
                           padx=20, pady=5)
        gen_btn.pack(pady=10)
    
    def generate_random_password(self):
        """Generate random password based on options - EXACT length with verification"""
        from src.features.password_gen import PasswordGenerator
        
        try:
            length = self.random_length.get()
            print(f"🔧 DEBUG: Requested length = {length}")
        except:
            length = 128
        
        # Ensure length is within bounds
        if length < 1:
            length = 8
        if length > 4096:
            length = 4096
        
        # Generate EXACT length password
        password = PasswordGenerator.generate_random(
            length=length,
            use_upper=self.use_upper.get(),
            use_lower=self.use_lower.get(),
            use_digits=self.use_digits.get(),
            use_symbols=self.use_symbols.get(),
            avoid_ambiguous=self.avoid_ambiguous.get()
        )
        
        # Verify length
        actual_len = len(password)
        print(f"🔧 DEBUG: Actual generated length = {actual_len}")
        
        if actual_len != length:
            print(f"⚠️ WARNING: Length mismatch! Expected {length}, got {actual_len}")
            # If mismatch, force correct length
            if actual_len < length:
                # Need more characters
                password += PasswordGenerator.generate_random(length - actual_len)
            elif actual_len > length:
                # Truncate
                password = password[:length]
            print(f"🔧 DEBUG: Corrected length = {len(password)}")
        
        self.update_display(password)
    
    def generate_pronounceable(self):
        """Generate pronounceable password"""
        from src.features.password_gen import PasswordGenerator
        password = PasswordGenerator.generate_pronounceable(self.pronounce_length.get())
        self.update_display(password)
    
    def generate_diceware(self):
        """Generate diceware passphrase"""
        from src.features.password_gen import PasswordGenerator
        password = PasswordGenerator.generate_diceware(
            word_count=self.diceware_words.get(),
            separator=self.diceware_sep.get()
        )
        self.update_display(password)
    
    def generate_pin(self):
        """Generate PIN"""
        from src.features.password_gen import PasswordGenerator
        password = PasswordGenerator.generate_pin(self.pin_length.get())
        self.update_display(password)
    
    def generate_apple(self):
        """Generate Apple-style password"""
        from src.features.password_gen import PasswordGenerator
        password = PasswordGenerator.generate_apple_style()
        self.update_display(password)
    
    def generate_password(self):
        """Generate password based on active tab"""
        self.generate_random_password()
    
    def update_display(self, password):
        """Update the password display and strength meter"""
        from src.features.password_gen import PasswordGenerator
        
        self.result_password = password
        self.password_display.delete(1.0, tk.END)
        self.password_display.insert(1.0, password)
        
        # Show ACTUAL character count
        actual_len = len(password)
        target_len = self.random_length.get() if hasattr(self, 'random_length') else "?"
        self.length_info.config(text=f"✓ Generated {actual_len:,} characters (target: {target_len:,})")
        
        # Update strength meter
        strength = PasswordGenerator.check_strength(password)
        self.update_strength_meter(strength)
    
    def update_strength_meter(self, strength):
        """Update the password strength visual indicator"""
        colors = self.get_colors()
        
        self.strength_bar.delete("all")
        
        if strength['score'] == 4:
            bar_color = "#10b981"
            text = f"✓ Excellent - {strength['rating']}"
        elif strength['score'] == 3:
            bar_color = "#3b82f6"
            text = f"✓ Good - {strength['rating']}"
        elif strength['score'] == 2:
            bar_color = "#f59e0b"
            text = f"⚠️ Fair - {strength['rating']}"
        else:
            bar_color = "#ef4444"
            text = f"⚠️ Weak - {strength['rating']}"
        
        width = int((strength['score'] / 4) * 400)
        self.strength_bar.create_rectangle(0, 0, width, 8, fill=bar_color, outline="")
        self.strength_label.config(text=text)
    
    def copy_password(self):
        """Copy generated password to clipboard"""
        if self.result_password:
            pyperclip.copy(self.result_password)
            original_text = self.copy_btn.cget("text")
            self.copy_btn.config(text="✓ Copied!", bg="#10b981")
            self.dialog.after(1500, lambda: self.copy_btn.config(text=original_text, bg=self.get_colors()["accent"]))
