#!/usr/bin/env python3
"""
download_hibp.py - Download and import the HaveIBeenPwned Pwned Passwords list.

The list is ~900 MB compressed. This script downloads it in chunks and imports
it into the local breach database so VaultKeeper can check passwords offline.

Usage:
    python scripts/download_hibp.py

The database is saved to:
    data/hibp_prefixes.db
"""

import os
import sys
import time

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH  = os.path.join(DATA_DIR, "hibp_prefixes.db")

HIBP_URL = "https://downloads.pwnedpasswords.com/passwords/pwned-passwords-sha1-ordered-by-hash-v8.txt.7z"
HIBP_TXT = "https://downloads.pwnedpasswords.com/passwords/pwned-passwords-sha1-ordered-by-hash-v8.txt.gz"

def main():
    try:
        import requests
    except ImportError:
        print("ERROR: This script requires 'requests'.")
        print("Run:   pip install requests")
        sys.exit(1)

    try:
        import py7zr
    except ImportError:
        py7zr = None  # will try gzip instead

    os.makedirs(DATA_DIR, exist_ok=True)

    print(f"Downloading HIBP Pwned Passwords list (~900 MB)...")
    print(f"Destination: {DB_PATH}")
    print()

    # Add the src directory to the path so we can import the module
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from features.breach_detection import BreachDetector

    detector = BreachDetector(DB_PATH)

    # Download
    gz_path = os.path.join(DATA_DIR, "hibp_hashes.txt.gz")
    print("Note: This requires an internet connection (one-time download).")
    print("VaultKeeper is offline-first; breach checks work without this file,")
    print("but with it you get full coverage of 900M+ breached passwords.")
    print()

    try:
        import gzip

        print("Downloading... (this may take 10-30 minutes depending on connection)")
        resp = requests.get(HIBP_TXT, stream=True)
        resp.raise_for_status()

        total     = int(resp.headers.get("content-length", 0))
        received  = 0
        start     = time.time()

        with open(gz_path, "wb") as out:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                out.write(chunk)
                received += len(chunk)
                if total:
                    pct = received / total * 100
                    mb  = received / 1024 / 1024
                    print(f"\r  {pct:.1f}%  ({mb:.0f} MB)  ", end="", flush=True)

        print(f"\nDownload complete in {int(time.time()-start)}s. Importing...")

        # Import line by line from the gzip stream
        count = [0]

        def progress(n):
            if n % 1_000_000 == 0:
                print(f"  Imported {n:,} entries...", flush=True)
            count[0] = n

        txt_path = gz_path.replace(".gz", "")
        with gzip.open(gz_path, "rt", encoding="utf-8") as gz:
            with open(txt_path, "w") as txt:
                for line in gz:
                    txt.write(line)

        total_imported = detector.import_hibp_text(txt_path, progress_cb=progress)
        os.remove(txt_path)
        os.remove(gz_path)

        print(f"\n✅  Done! {total_imported:,} breached password hashes imported.")
        print(f"   Database: {DB_PATH}")

    except Exception as exc:
        print(f"\n❌  Failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
