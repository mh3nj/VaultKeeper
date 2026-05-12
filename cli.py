#!/usr/bin/env python3
"""
VaultKeeper CLI - Command Line Interface
Usage:
    python cli.py list                    # List all entries
    python cli.py search "query"          # Search entries
    python cli.py add --title "Title" --username "user" --password "pass"
    python cli.py delete <id>             # Delete entry by ID
    python cli.py generate --length 16    # Generate password
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.vault_manager import VaultManager
from src.features.password_gen import PasswordGenerator

class VaultCLI:
    def __init__(self):
        self.vault = VaultManager()
        if not self.vault.initialize():
            print("Failed to open vault")
            sys.exit(1)
    
    def list_entries(self):
        entries = self.vault.get_all_entries()
        print(f"\n📁 Total entries: {len(entries)}\n")
        for e in entries:
            print(f"  [{e['id']}] {e.get('title', 'Untitled')} - {e.get('username', '')}")
    
    def search(self, query):
        entries = self.vault.db.search_entries(query)
        print(f"\n🔍 Found {len(entries)} entries\n")
        for e in entries:
            print(f"  [{e['id']}] {e.get('title', 'Untitled')} - {e.get('username', '')}")
    
    def add(self, title, username, password):
        entry = {'title': title, 'username': username, 'password': password}
        entry_id = self.vault.add_entry(entry)
        print(f"✅ Added entry ID: {entry_id}")
    
    def delete(self, entry_id):
        self.vault.delete_entry(entry_id)
        print(f"✅ Deleted entry ID: {entry_id}")
    
    def generate(self, length):
        password = PasswordGenerator.generate_random(length)
        print(f"\n🔐 Generated password ({length} chars):\n{password}\n")
    
    def close(self):
        self.vault.lock()

def main():
    parser = argparse.ArgumentParser(description='VaultKeeper CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    subparsers.add_parser('list', help='List all entries')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search entries')
    search_parser.add_argument('query', help='Search query')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add entry')
    add_parser.add_argument('--title', required=True, help='Entry title')
    add_parser.add_argument('--username', default='', help='Username')
    add_parser.add_argument('--password', default='', help='Password')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete entry')
    delete_parser.add_argument('id', type=int, help='Entry ID')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate password')
    gen_parser.add_argument('--length', type=int, default=16, help='Password length')
    
    args = parser.parse_args()
    
    cli = VaultCLI()
    
    if args.command == 'list':
        cli.list_entries()
    elif args.command == 'search':
        cli.search(args.query)
    elif args.command == 'add':
        cli.add(args.title, args.username, args.password)
    elif args.command == 'delete':
        cli.delete(args.id)
    elif args.command == 'generate':
        cli.generate(args.length)
    else:
        parser.print_help()
    
    cli.close()

if __name__ == "__main__":
    main()
