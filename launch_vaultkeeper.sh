#!/bin/bash

# VaultKeeper - Password Manager Launcher for Linux/Mac

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Store the starting directory
STARTDIR=$(pwd)

echo "      VaultKeeper: Password Manager"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed!${NC}"
    echo ""
    echo "Please install Python 3.11+ from https://python.org"
    echo "Or use your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-virtualenv python3-pip"
    echo "  Arch: sudo pacman -S python python-pip"
    echo "  macOS: brew install python@3.11"
    echo ""
    exit 1
fi

# Check Python version
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]); then
    echo -e "${RED}[ERROR] Python 3.11+ is required. Detected: $PY_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Python found: $PY_VERSION${NC}"
echo ""

# Check if Git is installed (for updates)
if command -v git &> /dev/null; then
    echo -e "${GREEN}[OK] Git found${NC}"
    git --version
    GIT_AVAILABLE=1
else
    echo -e "${YELLOW}[WARN] Git not found. Updates will not work automatically.${NC}"
    echo "[INFO] You can still run the app, but to update you'll need to download manually."
    echo ""
    GIT_AVAILABLE=0
fi
echo ""

# Check if this is a git repo and update if possible
if [ $GIT_AVAILABLE -eq 1 ] && [ -d ".git" ]; then
    echo -e "${BLUE}[UPDATE] Checking for updates...${NC}"
    git pull origin main
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK] Successfully updated to latest version${NC}"
    else
        echo -e "${YELLOW}[WARN] Git pull failed, continuing with current version...${NC}"
    fi
    echo ""
fi

echo -e "${BLUE}[SETUP] Setting up Python virtual environment...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to create virtual environment!${NC}"
        cd "$STARTDIR"
        exit 1
    fi
    echo -e "${GREEN}[OK] Virtual environment created${NC}"
else
    echo -e "${GREEN}[OK] Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to activate virtual environment!${NC}"
    cd "$STARTDIR"
    exit 1
fi

echo -e "${GREEN}[OK] Virtual environment activated${NC}"
echo ""

# Check for requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}[ERROR] requirements.txt not found!${NC}"
    echo "Please make sure you are in the correct directory."
    cd "$STARTDIR"
    exit 1
fi

# Install/upgrade dependencies
echo -e "${BLUE}[INSTALL] Installing/updating dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[OK] All dependencies installed successfully${NC}"
else
    echo -e "${YELLOW}[ERROR] Failed to install some dependencies!${NC}"
    echo "Trying to continue anyway..."
fi

echo ""
echo -e "${BLUE}[LAUNCH] Starting VaultKeeper...${NC}"
echo ""
echo "   setup complete! starting app..."
echo ""

# Start the application
python run.py

echo ""
echo -e "${GREEN}[DONE] VaultKeeper closed.${NC}"
echo "You can re-run this script anytime to update and launch the app."
echo ""
read -p "Press Enter to exit..."