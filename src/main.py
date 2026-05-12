"""
main.py - Entry point for VaultKeeper
"""

import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.vault_manager import VaultManager
from src.gui.main_window import VaultKeeperUI

def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║     VaultKeeper - Password Manager     ║
    ║                                       ║
    ║   Secure • Offline • Professional      ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
    """)
    
    manager = VaultManager()
    
    # This will handle the unlock interactively
    if not manager.initialize():
        print("Failed to initialize vault. Exiting.")
        sys.exit(1)
    
    # Verify database is connected
    if manager.db is None:
        print("ERROR: Database not connected!")
        sys.exit(1)
    
    print(f"✓ Vault ready. Database: {manager.db_path}")
    print(f"✓ Entries in vault: {len(manager.db.get_all_entries())}")
    
    # Launch GUI with the already UNLOCKED vault manager
    app = VaultKeeperUI(manager)
    app.run()
    
    # Cleanup
    manager.lock()
    print("\nVault locked. Goodbye!")

if __name__ == "__main__":
    main()
