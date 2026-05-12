"""
system_tray.py - System tray icon for VaultKeeper
"""

import tkinter as tk
import pystray
from PIL import Image, ImageDraw
import threading

class SystemTray:
    """System tray icon manager"""
    
    def __init__(self, app, vault_manager):
        self.app = app
        self.vault = vault_manager
        self.icon = None
        self.icon_thread = None
        self.running = False
    
    def create_image(self):
        """Create icon image"""
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), '#3b82f6')
        draw = ImageDraw.Draw(image)
        draw.rectangle([(width//4, height//4), (width*3//4, height*3//4)], fill='white')
        draw.text((width//2-10, height//2-10), "🔐", fill='#3b82f6')
        return image
    
    def setup(self):
        """Setup system tray icon"""
        menu = pystray.Menu(
            pystray.MenuItem("Show VaultKeeper", self.show_window),
            pystray.MenuItem("Lock Vault", self.lock_vault),
            pystray.MenuItem("Exit", self.exit_app)
        )
        
        self.icon = pystray.Icon("vaultkeeper", self.create_image(), "VaultKeeper", menu)
    
    def show_window(self):
        """Show the main window"""
        self.app.root.deiconify()
        self.app.root.lift()
        self.app.root.focus_force()
    
    def lock_vault(self):
        """Lock the vault"""
        self.app.lock_vault()
    
    def exit_app(self):
        """Exit the application"""
        self.running = False
        if self.icon:
            self.icon.stop()
        self.app.root.quit()
    
    def run(self):
        """Run the system tray in background"""
        self.setup()
        self.running = True
        self.icon.run()
    
    def start(self):
        """Start system tray thread"""
        self.icon_thread = threading.Thread(target=self.run, daemon=True)
        self.icon_thread.start()
    
    def stop(self):
        """Stop system tray"""
        self.running = False
        if self.icon:
            self.icon.stop()
