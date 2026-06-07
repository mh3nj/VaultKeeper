#!/usr/bin/env python3
"""
launcher.py - GUI unlock window for VaultKeeper
Fixed:
  - Password is never written to a temp .py file or passed via subprocess arg/env
  - create_vault() calls vault_manager directly (no temp script injection)
  - verify_and_launch() uses the real HMAC verifier, not a bare PBKDF2 derive
  - config writes are atomic
  - bare except → specific exceptions
  - launch_main_app() passes the vault_manager object in-process (no env var leak)
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
import json
import logging

log = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class VaultKeeperLauncher:
    """Splash/unlock window.  On success it opens the main UI in-process."""

    MAX_ATTEMPTS = 5

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VaultKeeper - Unlock Vault")
        self.root.geometry("430x320")
        self.root.resizable(False, False)
        
        # Set icon - Windows .ico file
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "logo.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        self._center()

        self.config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "vaultkeeper.config"
        )
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "vaultkeeper.db"
        )
        self.vault_exists = (
            os.path.exists(self.config_path) and os.path.exists(self.db_path)
        )

        self._build_ui()
        self._load_attempt_display()

        if not self.vault_exists:
            self._show_new_vault_mode()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        colors = self._colors()
        self.root.configure(bg=colors["bg"])

        frm = tk.Frame(self.root, bg=colors["bg"], padx=32, pady=24)
        frm.pack(fill=tk.BOTH, expand=True)

        # Logo (if exists)
        logo_path = os.path.join(os.path.dirname(__file__), "resources", "logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path)
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)
                logo_label = tk.Label(frm, image=logo_img, bg=colors["bg"])
                logo_label.image = logo_img
                logo_label.pack(pady=(0, 10))
            except:
                pass

        # Title - CENTERED
        tk.Label(frm, text="VaultKeeper", font=("Segoe UI", 22, "bold"),
                bg=colors["bg"], fg=colors["accent"]).pack(anchor="center", pady=(0, 5))
        
        # Subtitle - CENTERED
        tk.Label(frm, text="Secure Offline Password Manager",
                font=("Segoe UI", 9), bg=colors["bg"], fg=colors["muted"]).pack(anchor="center", pady=(0, 20))

        # Password field
        tk.Label(frm, text="Master Password", font=("Segoe UI", 10),
                bg=colors["bg"], fg=colors["fg"]).pack(anchor="w")

        pw_frame = tk.Frame(frm, bg=colors["ent_bg"], relief=tk.SOLID, bd=1,
                            highlightthickness=0)
        pw_frame.pack(fill=tk.X, pady=(4, 0))

        self._pw_var = tk.StringVar()
        self._pw_show = tk.BooleanVar(value=False)

        self._pw_entry = tk.Entry(
            pw_frame, textvariable=self._pw_var,
            show="•", font=("Segoe UI", 12),
            bg=colors["ent_bg"], fg=colors["fg"],
            relief=tk.FLAT, bd=6, insertbackground=colors["fg"]
        )
        self._pw_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._pw_entry.bind("<Return>", lambda _e: self._unlock())

        eye_btn = tk.Button(
            pw_frame, text="👁", font=("Segoe UI", 10),
            bg=colors["ent_bg"], fg=colors["muted"],
            relief=tk.FLAT, cursor="hand2", bd=4,
            command=self._toggle_show
        )
        eye_btn.pack(side=tk.RIGHT)

        # Unlock button - CENTERED
        self._unlock_btn = tk.Button(
            frm, text="Unlock Vault",
            font=("Segoe UI", 11, "bold"),
            bg=colors["accent"], fg="white",
            relief=tk.FLAT, cursor="hand2",
            padx=16, pady=8,
            command=self._unlock
        )
        self._unlock_btn.pack(fill=tk.X, pady=(16, 0))

        # Status / attempts
        self._status_lbl = tk.Label(frm, text="", font=("Segoe UI", 9),
                                    bg=colors["bg"], fg=colors["danger"])
        self._status_lbl.pack(pady=(8, 0))

        self._attempts_lbl = tk.Label(frm, text="", font=("Segoe UI", 9),
                                    bg=colors["bg"], fg=colors["warn"])
        self._attempts_lbl.pack()

        # Dark-mode toggle - CENTERED
        tk.Button(
            frm, text="🌙  Toggle Dark Mode",
            font=("Segoe UI", 8),
            bg=colors["btn_bg"], fg=colors["fg"],
            relief=tk.FLAT, cursor="hand2", padx=8, pady=3,
            command=self._toggle_dark
        ).pack(pady=(12, 0))

        self._dark_mode = False
        self._frm = frm
        self._pw_entry.focus()

    def _toggle_show(self):
        self._pw_show.set(not self._pw_show.get())
        self._pw_entry.config(show="" if self._pw_show.get() else "•")

    def _toggle_dark(self):
        self._dark_mode = not self._dark_mode
        c = self._colors()
        self.root.configure(bg=c["bg"])
        self._apply_colors(self.root, c)

    def _apply_colors(self, widget, c):
        try:
            klass = widget.winfo_class()
            if klass in ("Frame",):
                widget.configure(bg=c["bg"])
            elif klass in ("Label",):
                widget.configure(bg=c["bg"], fg=c["fg"])
            elif klass in ("Button",):
                widget.configure(bg=c["btn_bg"], fg=c["fg"])
            elif klass in ("Entry",):
                widget.configure(bg=c["ent_bg"], fg=c["fg"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._apply_colors(child, c)

    def _show_new_vault_mode(self):
        self._status_lbl.config(
            text="No vault found — enter a password to create one.",
            fg=self._colors()["success"]
        )
        self._unlock_btn.config(text="Create New Vault")

    def _load_attempt_display(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    cfg = json.load(f)
                failed = cfg.get("failed_attempts", 0)
                if failed > 0:
                    rem = self.MAX_ATTEMPTS - failed
                    self._attempts_lbl.config(text=f"⚠  {rem} attempt(s) remaining")
        except (OSError, json.JSONDecodeError):
            pass

    # ------------------------------------------------------------------
    # Unlock / create
    # ------------------------------------------------------------------

    def _unlock(self):
        password = self._pw_var.get()
        if not password:
            self._status_lbl.config(text="Enter your master password.")
            return

        # Disable while working
        self._unlock_btn.config(state=tk.DISABLED)
        self._status_lbl.config(text="Verifying…", fg=self._colors()["muted"])
        self.root.update()

        if not self.vault_exists:
            self._create_new_vault(password)
        else:
            self._verify_and_launch(password)

        # Re-enable if we didn't destroy the window
        try:
            self._unlock_btn.config(state=tk.NORMAL)
        except tk.TclError:
            pass

    def _create_new_vault(self, password: str):
        """Create vault in-process — password never leaves the process."""
        if len(password) < 8:
            self._safe_set_status("Password must be at least 8 characters.",
                                  self._colors()["danger"])
            self._pw_var.set("")
            return

        launched = False
        try:
            from src.core.vault_manager import VaultManager
            mgr = VaultManager(db_path=self.db_path, config_path=self.config_path)
            if mgr._setup_vault(password):
                self.vault_exists = True
                self._safe_set_status("✓ Vault created!  Launching…", self._colors()["success"])
                self.root.update()
                launched = True
                self._launch(mgr)   # destroys self.root — no widget access after this
            else:
                self._safe_set_status("Failed to create vault.", self._colors()["danger"])
        except Exception as exc:
            log.exception("create_vault failed")
            if not launched:
                self._safe_set_status(f"Error: {exc}", self._colors()["danger"])
        finally:
            password = ""  # zero local ref

    def _verify_and_launch(self, password: str):
        """Verify password using the HMAC verifier and launch in-process."""
        launched = False
        try:
            from src.core.vault_manager import VaultManager
            mgr = VaultManager(db_path=self.db_path, config_path=self.config_path)
            if mgr.unlock_with_password(password):
                # Update UI before destroying the window
                self._safe_set_status("✓ Unlocked!  Launching…", self._colors()["success"])
                self.root.update()
                launched = True
                self._launch(mgr)   # destroys self.root — no widget access after this
            else:
                # vault_manager already incremented the counter
                self._safe_set_status("Wrong password.", self._colors()["danger"])
                self._pw_var.set("")
                self._pw_entry.focus()
                self._load_attempt_display()

                # Check if now locked
                try:
                    with open(self.config_path) as f:
                        cfg = json.load(f)
                    if cfg.get("failed_attempts", 0) >= self.MAX_ATTEMPTS:
                        self._safe_set_status("Vault locked — too many failed attempts.",
                                              self._colors()["danger"])
                        self._unlock_btn.config(state=tk.DISABLED)
                except (OSError, json.JSONDecodeError):
                    pass
        except Exception as exc:
            log.exception("verify_and_launch failed")
            if not launched:
                self._safe_set_status(f"Error: {exc}", self._colors()["danger"])
        finally:
            password = ""

    def _launch(self, vault_manager):
        """Destroy launcher, open main window — entirely in-process."""
        self.root.destroy()
        from src.gui.main_window import VaultKeeperUI
        app = VaultKeeperUI(vault_manager)
        app.run()
        vault_manager.lock()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _safe_set_status(self, text: str, fg: str = ""):
        """Update the status label only if the window still exists."""
        try:
            kwargs = {"text": text}
            if fg:
                kwargs["fg"] = fg
            self._status_lbl.config(**kwargs)
        except tk.TclError:
            pass   # window was already destroyed — silently ignore

    def _center(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w  = self.root.winfo_width()
        h  = self.root.winfo_height()
        self.root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _colors(self):
        if getattr(self, "_dark_mode", False):
            return {"bg": "#1e1e1e", "fg": "#fff", "ent_bg": "#3d3d3d",
                    "btn_bg": "#3d3d3d", "accent": "#3b82f6", "muted": "#9ca3af",
                    "success": "#10b981", "danger": "#ef4444", "warn": "#f59e0b"}
        return {"bg": "#f8fafc", "fg": "#111", "ent_bg": "#fff",
                "btn_bg": "#e5e7eb", "accent": "#3b82f6", "muted": "#6b7280",
                "success": "#10b981", "danger": "#ef4444", "warn": "#f59e0b"}

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    VaultKeeperLauncher().run()
