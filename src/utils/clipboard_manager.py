"""
clipboard_manager.py - Smart clipboard management
"""

import pyperclip
import threading
import time

class ClipboardManager:
    """Manages clipboard with auto-clear"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.timer = None
        self.clear_delay = 10  # seconds
    
    def set_delay(self, seconds: int):
        """Set auto-clear delay"""
        self.clear_delay = seconds
    
    def copy(self, text: str):
        """Copy text to clipboard and schedule clear"""
        pyperclip.copy(text)
        
        # Cancel existing timer
        if self.timer:
            self.timer.cancel()
        
        # Schedule clear
        self.timer = threading.Timer(self.clear_delay, self._clear_clipboard)
        self.timer.daemon = True
        self.timer.start()
    
    def _clear_clipboard(self):
        """Clear clipboard by copying empty string"""
        try:
            pyperclip.copy("")  # Empty string overwrites clipboard
        except:
            pass
