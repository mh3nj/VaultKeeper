#!/usr/bin/env python3
"""
VaultKeeper - Professional Password Manager
Run this to start the application
"""

import sys
import os

# Hide console window on Windows (for .pyw execution)
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
