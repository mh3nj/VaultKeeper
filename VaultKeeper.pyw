#!/usr/bin/env python3
"""
VaultKeeper - Password Manager (No Console)
Run this file to start without terminal window
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
