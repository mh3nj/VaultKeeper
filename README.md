# VaultKeeper – Offline Password Manager

**Status:** Stable Release v3.0  
**Build Date:** May 11, 2026

A professional offline password manager with **4096-character passwords**, TOTP time drift correction, system-wide auto-type, offline breach checking, emergency access, and attachment gallery – all in one privacy-first, zero-telemetry application.

---

## Why Version 3.0?

VaultKeeper started as a simple idea: "Bitwarden but better, fully offline."

**v1.x (Internal)** – The prototype. Basic password storage, AES-256 encryption, SQLite database. Never released because it was too raw – just a proof of concept.

**v2.x (Internal)** – Added TOTP, password generator, dark mode, import/export. Still not ready for public release due to stability issues and missing critical features.

**v3.0 (Public Release)** – The complete rewrite. Every feature battle-tested, every bug squashed. This is the version you can trust with your passwords.

### What Changed in v3.0

- ✅ Removed demo mode – real master password only
- ✅ **4096-character passwords** (confirmed, actual max)
- ✅ **TOTP time drift slider** – sync with any authenticator app
- ✅ **Persistent drift storage** – save once, works forever
- ✅ **System-wide auto-type** – works in ANY application
- ✅ **Offline breach checker** – privacy first
- ✅ **Emergency access** – time-locked offline
- ✅ **Attachment gallery** – with file icons and preview
- ✅ **Built-in CLI console** – for power users
- ✅ **System tray support** – minimize to tray
- ✅ **Dark/Light theme** – toggle anytime
- ✅ **5 failed attempts lockout** – security first
- ✅ **Fixed TOTP update loop errors**
- ✅ **Fixed drift saving to database**
- ✅ **Fixed clipboard clear** (empty string method)

---

## What VaultKeeper Helps You Do

- Store passwords – AES-256 encrypted, fully offline
- Generate passwords – 4096 characters maximum (Random, Pronounceable, Diceware, PIN, Apple-style)
- Manage 2FA – TOTP with time drift correction (SHA1, SHA256, SHA512 + Steam/Yandex/mOTP)
- Auto-type credentials – Works in ANY application (not just browsers)
- Check for breaches – Offline, your passwords never leave your machine
- Import passwords – From Bitwarden JSON or LastPass CSV
- Attach files – Unlimited attachments with original date preservation
- Emergency access – Time-locked offline access for trusted individuals
- Security reports – Identify weak, duplicate, or expired passwords
- CLI commands – For power users who love the terminal

**Fully offline** | **Dark/Light theme** | **Zero telemetry** | **No cloud** | **Your data, your rules**

---

## Getting Started

### Option 1: From Source (Python required)

```bash
git clone https://github.com/yourusername/VaultKeeper.git
cd VaultKeeper
python -m venv venv
venv\Scripts\activate  (Windows)
# source venv/bin/activate  (Mac/Linux)
pip install -r requirements.txt
python run.py
```

### Option 2: Standalone Executable

Download from GitHub Releases. No Python installation required. Just unzip and run VaultKeeper.exe (or VaultKeeper.pyw for no console window).

---

## First Time Setup

1. **Create a master password** – At least 8 characters. Cannot be recovered if lost.
2. **Import from Bitwarden** – Use Tools → Import/Export → Bitwarden JSON
3. **Start adding entries** – Or import your existing vault

⚠️ **Warning:** Your master password CANNOT be recovered. There is no cloud, no password reset, no backdoor. This is by design.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+C | Copy password (when entry selected) |
| Ctrl+U | Copy username (when entry selected) |
| Ctrl+Shift+A | Auto-type selected entry |
| Ctrl+Shift+T | Toggle Dark/Light theme |
| Ctrl+Shift+R | Refresh entries |

*More shortcuts available in the CLI console (Ctrl+` or Tools → CLI Console)*

---

## Features In Detail

### Password Management

| Feature | Description |
|---------|-------------|
| **4096-char passwords** | Generate passwords up to 4096 characters (verified actual length) |
| **Password generator** | 6 modes: Random, Pronounceable, Diceware, PIN, Apple-style, Hex |
| **Strength meter** | Real-time password strength analysis (0-4 score) |
| **Expiry reminders** | Automatic notifications for old passwords |
| **Favorites** | Star important entries for quick access |
| **Custom fields** | Add unlimited text/hidden/boolean fields |
| **Multiple URIs** | Add multiple websites per entry |
| **Notes** | Rich text notes with markdown support |
| **Attachments** | Unlimited files with original date preservation |

### TOTP / Two-Factor Authentication

| Feature | Description |
|---------|-------------|
| **TOTP support** | SHA1, SHA256, SHA512 algorithms |
| **OTP types** | TOTP, Steam, Yandex, mOTP |
| **Time drift correction** | Slider to sync with any authenticator app |
| **Persistent drift** | Save drift per entry – works forever |
| **URI parsing** | Import from otpauth:// QR codes |
| **Test button** | Verify codes before saving |
| **Auto-refresh** | Live countdown timer |

### Auto-Type (System-Wide)

| Feature | Description |
|---------|-------------|
| **Any application** | Works in browsers, terminals, login windows, SSH, etc. |
| **Custom sequences** | {username}, {password}, {TAB}, {ENTER}, {DELAY}, {CLIPBOARD} |
| **Configurable speed** | Adjust typing delay |
| **Keyboard shortcut** | Ctrl+Shift+A to auto-type selected entry |

### Security & Privacy

| Feature | Description |
|---------|-------------|
| **Offline breach checker** | Local database – your passwords never leave your machine |
| **Security report** | Identifies weak, duplicate, and expired passwords |
| **Emergency access** | Time-locked offline packages for trusted individuals |
| **Auto-lock on idle** | Configurable timeout (1-60 minutes) |
| **Clipboard auto-clear** | Configurable delay (5-60 seconds) |
| **5 failed attempts** | Vault locks after 5 wrong passwords |
| **No cloud** | Your data never leaves your computer |

### Import / Export

| Format | Import | Export |
|--------|--------|--------|
| Bitwarden JSON | ✅ | ✅ |
| LastPass CSV | ✅ | ✅ |
| VaultKeeper encrypted | ✅ | ✅ |
| Plain text (TXT) | ❌ | ✅ (for mobile) |
| CSV | ❌ | ✅ |
| JSON | ✅ | ✅ |

### Attachments

| Feature | Description |
|---------|-------------|
| **Unlimited size** | No file size limits |
| **Any file type** | Images, documents, archives, audio, video |
| **Date preservation** | Original creation dates preserved |
| **Gallery view** | Scrollable list with file icons |
| **Open with default app** | One-click to open |
| **Save to disk** | Extract attachments anytime |

### CLI Console (Built-in)

| Command | Description |
|---------|-------------|
| `list` | List all entries (ID and title) |
| `search <query>` | Search entries by title or username |
| `stats` | Show vault statistics |
| `export` | Export vault to CSV file |
| `generate [length]` | Generate random password up to 4096 chars |
| `clear` | Clear console screen |
| `help` | Show help message |
| `exit` / `quit` | Close CLI console |

---

## Project Structure

```
VaultKeeper/
├── run.py                     # Entry point
├── src/
│   ├── main.py                # Main application
│   ├── core/
│   │   ├── crypto.py          # AES-256 encryption
│   │   ├── database.py        # SQLite operations
│   │   └── vault_manager.py   # Vault lifecycle
│   ├── features/
│   │   ├── password_gen.py    # 4096-char generator
│   │   ├── totp.py            # TOTP with time drift
│   │   ├── auto_type.py       # System-wide auto-type
│   │   ├── breach_detection.py # Offline breach checker
│   │   ├── expiry_manager.py  # Password expiry
│   │   └── emergency_access.py # Time-locked access
│   ├── gui/
│   │   ├── main_window.py     # Main UI
│   │   ├── entry_editor.py    # Add/Edit entries
│   │   ├── password_generator.py
│   │   ├── import_export_dialog.py
│   │   ├── security_report.py
│   │   ├── breach_checker_dialog.py
│   │   ├── smart_copy.py
│   │   └── expiry_dialog.py
│   └── utils/
│       └── helpers.py
├── requirements.txt
└── README.md
```

---

## Requirements

- Python 3.11+
- cryptography
- pyperclip
- pillow
- qrcode
- pyotp
- pystray (optional, for system tray)

---

## Development Timeline

| Phase | Duration | Key Achievements |
|-------|----------|------------------|
| Day 1-2 | ~16 hours | Core: Encryption, database, basic UI, unlock screen |
| Day 3-4 | ~16 hours | Features: Password generator, TOTP, import/export, dark mode |
| Day 5-6 | ~16 hours | Advanced: Auto-type, breach checker, security reports, attachments |
| Day 7-8 | ~16 hours | Polish: TOTP time drift, CLI console, system tray, emergency access |
| Day 9 | ~8 hours | Testing: Bug fixes, drift persistence, error handling, release |

**Total:** ~72 hours | **Lines of code:** 15,000+ | **Features:** 50+ | **Files:** 30+

---

## What Makes VaultKeeper Better Than Bitwarden

| Feature | Bitwarden | VaultKeeper v3.0 |
|---------|-----------|------------------|
| Max password length | 128 characters | **4096 characters** |
| Offline breach checker | ❌ (requires internet) | ✅ |
| Auto-type system-wide | ❌ (browser extension only) | ✅ |
| TOTP time drift correction | ❌ | ✅ |
| Persistent drift per entry | ❌ | ✅ |
| Built-in CLI | ❌ | ✅ |
| Emergency access offline | ❌ (requires cloud) | ✅ |
| Attachment date preservation | ❌ | ✅ |
| Price | Freemium | **FREE** |
| Data ownership | Their servers | **YOUR machine** |

---

## Known Limitations

- No browser extension – copy-paste only (more secure)
- No automatic cloud sync – you manage backups manually
- No mobile app yet – export to TXT for mobile access
- Windows-only for now (Linux/macOS coming soon)

---

## Author

**Mohsen Jafari** - Creator, Developer, Designer

- GitHub: [mh3nj](https://github.com/mh3nj)
- LinkedIn: [mh3nj](https://linkedin.com/in/mh3nj)
- Websites: [Parsegan.com](https://parsegan.com) (logo design), [Dahgan.com](https://dahgan.com) (land surveying/portfolio)

---

## License

MIT License – Free for personal and commercial use.

---

## Acknowledgments

- cryptography team (AES-256, Argon2)
- pyperclip, pillow, qrcode, pyotp
- The open-source community
- Everyone who values privacy and offline-first software

---

*"Trust nothing but math. Protect yourself from everyone; including yourself."*
