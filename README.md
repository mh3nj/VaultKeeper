# vaultkeeper

![Version](https://img.shields.io/badge/version-3.1-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-yellow)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20mac%20%7C%20linux-lightgrey)
![Offline](https://img.shields.io/badge/works-offline-brightgreen)
![Security](https://img.shields.io/badge/encryption-AES--256--GCM-red)
![Built in Iran](https://img.shields.io/badge/built%20in-iran-orange)

> **offline password manager. aes-256-gcm. no cloud. no tracking. no subscription.**  
> your credentials never leave your machine. they never touch a server. they never see the internet.


<img src="/assets/banner3.1.png" alt="VaultKeeper v3.1 Banner" width="100%">


---

## the problem this solves

every password manager today wants your data in their cloud. they want a subscription. they want to know what you store, when you access it, and from where.

vaultkeeper takes the opposite approach. everything stays local. the database is encrypted on your disk. the master password is verified using hmac, not stored anywhere. if someone steals your database file, they get nothing without your password. if they try to brute force, the vault locks itself after 5 failed attempts.

built because the existing options either cost money, store data on someone else's servers, or both.

---

## what's new in version 3.1

### encryption upgrade: cbc → gcm

the original version used aes-256-cbc, which provides confidentiality but no tamper detection. a single bit flip in the ciphertext would silently corrupt your data with no warning. the new version uses aes-256-gcm, which authenticates every decryption and raises an error if the ciphertext has been modified. tampering is detected. corrupted data is not loaded.

### real password verification

old behavior: any password would open the database. wrong passwords would produce garbled decrypted content later. you would see random characters instead of your passwords and not know why.

new behavior: vaultkeeper stores an hmac verifier derived from your master password. when you unlock, it verifies your password cryptographically before even touching the database. wrong password = immediate rejection. no confusion. no silent corruption.

### master password change that actually works

the original implementation saved a new salt and config but left every entry encrypted with the old key. the result was permanent vault corruption. changing your password destroyed your database.

the fixed version decrypts every sensitive field with the old key, re-encrypts with the new key, and only then swaps the config. it takes a few seconds. it works correctly.

### emergency access time-lock

the original emergency access feature used sha256(timestamp) as the encryption key and brute-forced ±86,400 offsets on decrypt. the waiting period was bypassable in seconds.

the new scheme uses a guardian key: 32 random bytes that are never stored in the package. the package contains only the gcm-encrypted vault password and an hmac over the unlock time. without the guardian key, decryption is computationally infeasible. the time lock is real.

### breach detection: offline k-anonymity

the old breach checker checked against a hardcoded set of 17 common passwords. useless.

the new implementation uses the haveibeenpwned k-anonymity model, fully offline. compute the sha-1 of your password. look up the first 5 hex characters in a local prefix database. if the full hash appears in that bucket, the password is breached.

the full pwned passwords list is ~900 mb. you can download it once with `scripts/download_hibp.py` or rely on the built-in top-500 common password fallback. either way, no internet required for breach checking after setup.

---

## security architecture

| component | implementation |
|-----------|----------------|
| encryption | aes-256-gcm (authenticated) |
| key derivation | pbkdf2-hmac-sha256, 200,000 iterations |
| password verification | hmac verifier (not just pbkdf2) |
| memory safety | derived keys zeroed after use |
| master password | never stored as attribute |
| failed attempts | vault locks after 5 tries |
| emergency access | guardian key scheme (key not stored) |
| breach detection | hibp k-anonymity with local db |
| database | sqlite with wal journal mode |

---

## features

| category | what's inside |
|----------|---------------|
| core | create vault, unlock with master password, change master password (re-encrypts everything), lock vault, auto-lock timeout |
| password generator | random (up to 4096 chars), pronounceable, diceware (eff word list), pin, apple-style |
| auto-type | system-wide keyboard simulation. supports {username}, {password}, {totp}, {tab}, {enter}, {delay}, {clipboard}. custom format strings. |
| totp 2fa | standard totp (rfc 6238), steam guard, yandex, motp. time drift correction. qr code parsing. |
| breach detection | offline hibp k-anonymity. 900m+ breached passwords. built-in top-500 fallback. |
| security report | password strength distribution, reused password detection, weak password list, security score (0–100), recommendations. |
| expiry reminders | tracks password age. configurable notification days (7, 3, 1). bulk update from reminder dialog. |
| emergency access | create time-locked recovery packages. requires guardian key stored separately. cannot be backdated. |
| import/export | bitwarden json (full custom fields support), lastpass csv, plain json, plain text. |
| backup scheduler | automatic encrypted backups. configurable frequency (daily, weekly, monthly). auto-prunes old backups. |
| attachments | store files with entries. base64 encoded in database. open with default system app. |
| custom fields | key-value storage per entry. supports text, hidden, boolean types. |
| dark/light theme | toggle between themes. persistent across sessions. |
| cli console | built-in command line for power users. list, search, generate, stats, export. |

---

## screenshots

<div align="center">
  <table>
    <tr>
      <td align="center" width="100%"><img src="/screenshots/0.png" width="100%"><br/><sub>Master password</sub></td>
    </tr>
    <tr>
      <td align="center" width="50%"><img src="/screenshots/1.png" width="100%"><br/><sub>Main winsdow dark theme</sub></td>
      <td align="center" width="50%"><img src="/screenshots/2.png" width="100%"><br/><sub>Main winsdow light theme</sub></td>
    </tr>
    <tr>
      <td align="center" width="50%"><img src="/screenshots/3.png" width="100%"><br/><sub>Observing a password</sub></td>
      <td align="center" width="50%"><img src="/screenshots/4.png" width="100%"><br/><sub>Security Report window</sub></td>
    </tr>
    <tr>
      <td align="center" width="50%"><img src="/screenshots/5.png" width="100%"><br/><sub>Password generator</sub></td>
      <td align="center" width="50%"><img src="/screenshots/6.png" width="100%"><br/><sub>Export window</sub></td>
    </tr>
    <tr>
      <td align="center" width="50%"><img src="/screenshots/7.png" width="100%"><br/><sub>Import window</sub></td>
      <td align="center" width="50%"><img src="/screenshots/8.png" width="100%"><br/><sub>Backup window</sub></td>
    </tr>
    <tr>
      <td align="center" width="50%"><img src="/screenshots/9.png" width="100%"><br/><sub>Auto type window</sub></td>
      <td align="center" width="50%"><img src="/screenshots/10.png" width="100%"><br/><sub>Emergency access window</sub></td>
    </tr>
    <tr>
      <td align="center" width="50%"><img src="/screenshots/11.png" width="100%"><br/><sub>Unlock package window</sub></td>
      <td align="center" width="50%"><img src="/screenshots/12.png" width="100%"><br/><sub>Active package window</sub></td>
    </tr>
    <tr>
      <td align="center" width="50%"><img src="/screenshots/13.png" width="100%"><br/><sub>Command Line(CLI) window</sub></td>
      <td align="center" width="50%"><img src="/screenshots/14.png" width="100%"><br/><sub>Settings window</sub></td>
    </tr>
    <tr>
      <td align="center" width="50%"><img src="/screenshots/15.png" width="100%"><br/><sub>Adding new entry window</sub></td>
    </tr>
  </table>
</div>

---

## getting started

### windows

download `launch_vaultkeeper.bat` and double-click it.

the script will check your python version, create a virtual environment, install dependencies, and launch vaultkeeper. if something is missing, it tells you exactly what and where to get it.

```
launch_vaultkeeper.bat
```

if windows defender flags it, click "more info" → "run anyway". the script is readable; you can inspect every line before running.

### mac / linux

download `launch_vaultkeeper.sh`, make it executable, and run it:

```bash
chmod +x launch_vaultkeeper.sh
./launch_vaultkeeper.sh
```

same as the windows version: checks python, sets up the environment, installs dependencies, launches vaultkeeper.

### manual setup (if you prefer)

```bash
git clone https://github.com/mh3nj/vaultkeeper.git
cd vaultkeeper
python -m venv venv

# windows:
venv\Scripts\activate
# mac/linux:
source venv/bin/activate

pip install -r requirements.txt
python run.py
```

### requirements

- python 3.11 or higher
- 2gb ram (4gb recommended if you store many attachments)
- works fully offline after initial setup
- internet only needed for installing dependencies and optional hibp database download

---

## first run

when you launch vaultkeeper for the first time:

1. you will see the unlock window with "no vault found; enter a password to create one"
2. enter a master password (minimum 8 characters, longer is better)
3. click "create new vault"
4. the main window opens with an empty vault

your master password cannot be recovered if lost. there is no password reset. there is no "forgot password" email. back up your vault file regularly and do not lose your password.

---

## keyboard shortcuts

| shortcut | action |
|----------|--------|
| ctrl+1 | dashboard |
| ctrl+2 | all items |
| ctrl+3 | favorites |
| ctrl+f | search |
| ctrl+n | new entry |
| ctrl+e | edit selected entry |
| ctrl+d | delete selected entry |
| ctrl+c | copy password (with selection) |
| ctrl+u | copy username (with selection) |
| ctrl+shift+t | toggle dark/light theme |
| ctrl+l | lock vault |

---

## project structure

```
vaultkeeper/
├── run.py                      # entry point
├── launcher.py                 # unlock window
├── requirements.txt            # dependencies
├── launch_vaultkeeper.bat      # windows launcher
├── launch_vaultkeeper.sh       # mac/linux launcher
├── resources/
│   ├── logo.png
│   └── logo.ico
├── src/
│   ├── core/
│   │   ├── crypto.py           # aes-256-gcm, pbkdf2, hmac verifier
│   │   ├── database.py         # sqlite with wal, row factory
│   │   └── vault_manager.py    # vault lifecycle, encryption orchestration
│   ├── features/
│   │   ├── password_gen.py     # password generation, entropy strength
│   │   ├── totp.py             # totp, steam, yandex, motp
│   │   ├── breach_detection.py # hibp k-anonymity offline
│   │   ├── auto_type.py        # system-wide keyboard simulation
│   │   ├── emergency_access.py # guardian key emergency packages
│   │   ├── backup_scheduler.py # automatic encrypted backups
│   │   ├── expiry_manager.py   # password expiry tracking
│   │   ├── analytics.py        # security score, statistics
│   │   └── bitwarden_import.py # bitwarden json import
│   └── gui/
│       ├── main_window.py      # main vault interface
│       ├── entry_editor.py     # add/edit entries with attachments
│       ├── password_generator.py
│       ├── security_report.py
│       ├── import_export_dialog.py
│       ├── breach_checker_dialog.py
│       ├── expiry_dialog.py
│       ├── smart_copy.py
│       └── system_tray.py
├── scripts/
│   └── download_hibp.py        # download full hibp database
└── screenshots/
    └── (images for readme)
```

---

## dependencies

```
cryptography>=42.0.0    # aes-256-gcm, pbkdf2
keyboard>=0.13.5        # system-wide auto-type
qrcode[pil]>=7.4.2      # emergency access qr codes
pillow>=10.3.0          # image processing, icons
pystray>=0.19.0         # system tray icon
pyperclip>=1.8.2        # clipboard operations
```

---

## known limitations

- auto-type on linux requires root or uinput permissions (`sudo modprobe uinput`)
- the full hibp database is ~900 mb and takes 10–30 minutes to download
- without the hibp database, breach detection falls back to top-500 common passwords
- attachments are stored base64-encoded in the database, which increases size by ~33%
- the emergency access guardian key must be stored separately; losing it makes the package undecryptable

---

## development context

this project was built under internet restrictions in iran, where access to github, pypi, stack overflow, and most development resources was blocked during extended periods. dependencies were researched and downloaded during brief connectivity windows. documentation was consulted from locally cached copies. problems were solved from first principles when references were unavailable.

version control pushes, dependency management, and documentation access required planning around unpredictable connectivity. the application was built anyway. it works. it is documented. it can be cloned and run by anyone.

---

## about the author

**mohsen jafari** is a full-time web developer based in iran, with experience in frontend development, backend systems, and desktop applications.

vaultkeeper was built to solve a real need: a password manager that does not require trusting someone else's cloud, paying a monthly fee, or accepting telemetry. the result is a tool he uses himself, that he built himself, that works entirely offline.

- github: [github.com/mh3nj](https://github.com/mh3nj)
- xing: [xing.com/profile/Mohsen_Jafari093223](https://www.xing.com/profile/Mohsen_Jafari093223/)
- logo design: [parsegan.com](https://parsegan.com)
- portfolio: [dahgan.com](https://dahgan.com)

---

## license

mit. use it, fork it, modify it, ship it. attribution appreciated but not required.

---

## the story behind this

this project was built during a period when the internet in iran was heavily restricted.

no stack overflow. no pypi. no github. no youtube tutorials. no reliable connection to the tools most developers take for granted. just whatever was cached locally, whatever could be reasoned through from first principles, and the determination to ship something real.

55 hours of focused work across one month. 18,000+ lines of code. 30+ features. one developer.

it works. it's useful. it was built under conditions that would have stopped most projects before they started.

**vaultkeeper; your credentials, your machine, your control.**

*— mh3nj*
