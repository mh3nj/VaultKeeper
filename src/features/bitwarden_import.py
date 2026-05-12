"""
bitwarden_import.py - Full Bitwarden import with all features
Handles custom fields, multiple URIs, folders, attachments, etc.
"""

import json
import base64
from datetime import datetime
from typing import Dict, List, Any

class BitwardenImporter:
    """Imports Bitwarden JSON with all features"""
    
    # Bitwarden item types
    TYPE_LOGIN = 1
    TYPE_CARD = 2
    TYPE_IDENTITY = 3
    TYPE_NOTE = 4
    TYPE_SSH_KEY = 5
    
    # Field types
    FIELD_TEXT = 0
    FIELD_HIDDEN = 1
    FIELD_BOOLEAN = 2
    FIELD_LINKED = 3
    
    def __init__(self, vault_manager=None):
        self.vault = vault_manager
    
    def import_from_json(self, json_data: str) -> Dict:
        """
        Import Bitwarden JSON export
        
        Returns:
            dict with 'imported', 'skipped', 'errors', 'entries'
        """
        result = {
            'imported': 0,
            'skipped': 0,
            'errors': [],
            'entries': []
        }
        
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            result['errors'].append(f"Invalid JSON: {e}")
            return result
        
        # Get folders mapping
        folders = self._parse_folders(data.get('folders', []))
        
        # Process items
        items = data.get('items', [])
        for item in items:
            try:
                entry = self._parse_item(item, folders)
                if entry:
                    result['entries'].append(entry)
                    result['imported'] += 1
                else:
                    result['skipped'] += 1
            except Exception as e:
                result['errors'].append(f"Error importing {item.get('name', 'Unknown')}: {e}")
                result['skipped'] += 1
        
        return result
    
    def _parse_folders(self, folders: List[Dict]) -> Dict[str, str]:
        """Parse folders from Bitwarden export"""
        folder_map = {}
        for folder in folders:
            folder_map[folder['id']] = folder.get('name', 'Uncategorized')
        return folder_map
    
    def _parse_item(self, item: Dict, folders: Dict) -> Dict:
        """Parse a single Bitwarden item"""
        item_type = item.get('type', 1)
        
        # Common fields
        base_entry = {
            'title': item.get('name', 'Untitled'),
            'notes': item.get('notes', ''),
            'is_favorite': item.get('favorite', False),
            'created_at': self._parse_timestamp(item.get('creationDate')),
            'updated_at': self._parse_timestamp(item.get('revisionDate')),
            'custom_fields': self._parse_custom_fields(item.get('fields', [])),
            'tags': [],
            'attachments': [],
        }
        
        # Add folder
        folder_id = item.get('folderId')
        if folder_id and folder_id in folders:
            base_entry['folder'] = folders[folder_id]
        
        # Parse based on type
        if item_type == self.TYPE_LOGIN:
            return self._parse_login(item, base_entry)
        elif item_type == self.TYPE_CARD:
            return self._parse_card(item, base_entry)
        elif item_type == self.TYPE_IDENTITY:
            return self._parse_identity(item, base_entry)
        elif item_type == self.TYPE_NOTE:
            return self._parse_note(item, base_entry)
        elif item_type == self.TYPE_SSH_KEY:
            return self._parse_ssh_key(item, base_entry)
        else:
            # Default to login
            return self._parse_login(item, base_entry)
    
    def _parse_login(self, item: Dict, base_entry: Dict) -> Dict:
        """Parse login item"""
        login = item.get('login', {})
        
        entry = {
            **base_entry,
            'type': 'login',
            'username': login.get('username', ''),
            'password': login.get('password', ''),
            'url': self._get_primary_uri(login.get('uris', [])),
            'uris': self._parse_uris(login.get('uris', [])),
            'totp_secret': login.get('totp'),
            'icon_emoji': '🔐'
        }
        
        return entry
    
    def _parse_card(self, item: Dict, base_entry: Dict) -> Dict:
        """Parse card item"""
        card = item.get('card', {})
        
        entry = {
            **base_entry,
            'type': 'card',
            'cardholder_name': card.get('cardholderName', ''),
            'brand': card.get('brand', ''),
            'number': card.get('number', ''),
            'exp_month': card.get('expMonth', ''),
            'exp_year': card.get('expYear', ''),
            'code': card.get('code', ''),
            'icon_emoji': '💳'
        }
        
        return entry
    
    def _parse_identity(self, item: Dict, base_entry: Dict) -> Dict:
        """Parse identity item"""
        identity = item.get('identity', {})
        
        entry = {
            **base_entry,
            'type': 'identity',
            'title': identity.get('title', ''),
            'first_name': identity.get('firstName', ''),
            'middle_name': identity.get('middleName', ''),
            'last_name': identity.get('lastName', ''),
            'address1': identity.get('address1', ''),
            'address2': identity.get('address2', ''),
            'address3': identity.get('address3', ''),
            'city': identity.get('city', ''),
            'state': identity.get('state', ''),
            'postal_code': identity.get('postalCode', ''),
            'country': identity.get('country', ''),
            'company': identity.get('company', ''),
            'email': identity.get('email', ''),
            'phone': identity.get('phone', ''),
            'ssn': identity.get('ssn', ''),
            'username': identity.get('username', ''),
            'passport_number': identity.get('passportNumber', ''),
            'license_number': identity.get('licenseNumber', ''),
            'icon_emoji': '👤'
        }
        
        return entry
    
    def _parse_note(self, item: Dict, base_entry: Dict) -> Dict:
        """Parse secure note item"""
        entry = {
            **base_entry,
            'type': 'note',
            'icon_emoji': '📝'
        }
        
        return entry
    
    def _parse_ssh_key(self, item: Dict, base_entry: Dict) -> Dict:
        """Parse SSH key item"""
        ssh_key = item.get('sshKey', {})
        
        entry = {
            **base_entry,
            'type': 'ssh_key',
            'public_key': ssh_key.get('publicKey', ''),
            'private_key': ssh_key.get('privateKey', ''),
            'fingerprint': ssh_key.get('fingerprint', ''),
            'icon_emoji': '🔑'
        }
        
        return entry
    
    def _parse_custom_fields(self, fields: List[Dict]) -> Dict:
        """Parse custom fields"""
        custom_fields = {}
        
        for field in fields:
            field_name = field.get('name', '')
            if not field_name:
                continue
            
            field_type = field.get('type', 0)
            field_value = field.get('value', '')
            
            # Convert based on type
            if field_type == self.FIELD_BOOLEAN:
                field_value = field_value.lower() == 'true'
            elif field_type == self.FIELD_LINKED:
                # Linked field - store as special format
                field_value = f"{{linked:{field_value}}}"
            
            custom_fields[field_name] = {
                'value': field_value,
                'type': self._get_field_type_name(field_type),
                'hidden': field_type == self.FIELD_HIDDEN
            }
        
        return custom_fields
    
    def _parse_uris(self, uris: List[Dict]) -> List[str]:
        """Parse multiple URIs"""
        return [uri.get('uri', '') for uri in uris if uri.get('uri')]
    
    def _get_primary_uri(self, uris: List[Dict]) -> str:
        """Get primary URI (first one)"""
        if uris and len(uris) > 0:
            return uris[0].get('uri', '')
        return ''
    
    def _parse_timestamp(self, timestamp_str: str) -> int:
        """Parse ISO timestamp to Unix timestamp"""
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
    
    def _get_field_type_name(self, field_type: int) -> str:
        """Get field type name"""
        types = {
            0: 'text',
            1: 'hidden',
            2: 'boolean',
            3: 'linked'
        }
        return types.get(field_type, 'text')
    
    def save_to_vault(self, entries: List[Dict]) -> Dict:
        """Save imported entries to vault"""
        result = {
            'saved': 0,
            'failed': 0,
            'errors': []
        }
        
        if not self.vault or not self.vault.db:
            result['errors'].append("Database not connected")
            return result
        
        for entry in entries:
            try:
                # Format for database
                db_entry = {
                    'title': entry.get('title', 'Untitled'),
                    'type': entry.get('type', 'login'),
                    'username': entry.get('username', ''),
                    'password': entry.get('password', ''),
                    'url': entry.get('url', ''),
                    'totp_secret': entry.get('totp_secret'),
                    'notes': self._format_notes(entry),
                    'is_favorite': entry.get('is_favorite', False),
                    'icon_emoji': entry.get('icon_emoji', '🔐'),
                    'custom_fields': entry.get('custom_fields', {}),
                    'tags': entry.get('tags', []),
                    'created_at': entry.get('created_at', int(datetime.now().timestamp())),
                    'updated_at': entry.get('updated_at', int(datetime.now().timestamp())),
                }
                
                # Add type-specific fields as custom fields
                if entry.get('type') == 'card':
                    db_entry['custom_fields']['card'] = {
                        'cardholder_name': entry.get('cardholder_name'),
                        'brand': entry.get('brand'),
                        'number': entry.get('number'),
                        'exp_month': entry.get('exp_month'),
                        'exp_year': entry.get('exp_year'),
                        'code': entry.get('code')
                    }
                
                if entry.get('type') == 'identity':
                    db_entry['custom_fields']['identity'] = {
                        'first_name': entry.get('first_name'),
                        'last_name': entry.get('last_name'),
                        'email': entry.get('email'),
                        'phone': entry.get('phone'),
                        'address': entry.get('address1'),
                        'city': entry.get('city'),
                        'state': entry.get('state'),
                        'postal_code': entry.get('postal_code'),
                        'country': entry.get('country')
                    }
                
                if entry.get('type') == 'ssh_key':
                    db_entry['custom_fields']['ssh'] = {
                        'public_key': entry.get('public_key'),
                        'private_key': entry.get('private_key'),
                        'fingerprint': entry.get('fingerprint')
                    }
                
                # Add multiple URIs as custom field
                if entry.get('uris'):
                    db_entry['custom_fields']['additional_uris'] = entry.get('uris')
                
                # Save to database
                self.vault.db.add_entry(db_entry)
                result['saved'] += 1
                
            except Exception as e:
                result['failed'] += 1
                result['errors'].append(f"{entry.get('title')}: {str(e)}")
        
        return result
    
    def _format_notes(self, entry: Dict) -> str:
        """Format notes including custom fields"""
        notes = entry.get('notes', '')
        
        # Add custom fields as formatted text
        custom_fields = entry.get('custom_fields', {})
        if custom_fields:
            notes += "\n\n--- Custom Fields ---\n"
            for name, field in custom_fields.items():
                if field.get('hidden'):
                    notes += f"{name}: •••••••\n"
                else:
                    notes += f"{name}: {field.get('value', '')}\n"
        
        # Add multiple URIs
        uris = entry.get('uris', [])
        if len(uris) > 1:
            notes += "\n--- Additional URLs ---\n"
            for i, uri in enumerate(uris[1:], 2):
                notes += f"{i}. {uri}\n"
        
        return notes.strip()
