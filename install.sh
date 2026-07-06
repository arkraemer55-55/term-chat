#!/usr/bin/env bash

echo "=========================================="
echo "    Term-Chat Client Installer for Linux   "
echo "=========================================="

# 1. Detect Linux Distro & Install SoX System Dependency
if [ -f /etc/arch-release ]; then
  echo "📦 Arch Linux detected. Installing dependencies via pacman..."
  sudo pacman -S --needed --noconfirm sox sound-theme-freedesktop
elif [ -f /etc/debian_version ] || [ -f /etc/lsb-release ]; then
  echo "📦 Ubuntu/Debian detected. Installing dependencies via apt..."
  sudo apt update && sudo apt install -y sox libsox-fmt-all sound-theme-freedesktop
elif [ -f /etc/fedora-release ]; then
  echo "📦 Fedora detected. Installing dependencies via dnf..."
  sudo dnf install -y sox sound-theme-freedesktop
else
  echo "⚠️ Unknown Linux distribution. Please ensure 'sox' is installed manually."
fi

# 2. Deploy the executable to the local user binary PATH
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

echo "🚀 Installing Term-Chat executable to $LOCAL_BIN/termchat..."
cp client.py "$LOCAL_BIN/termchat"
chmod +x "$LOCAL_BIN/termchat"

# 3. Add a quick python interpreter header check
# Ensure the file starts with the proper environment execution line
if ! grep -q "^#!/usr/bin/env python" "$LOCAL_BIN/termchat"; then
  sed -i '1s/^/#!\/usr\/bin\/env python3\n/' "$LOCAL_BIN/termchat"
fi

echo "=========================================="
echo "🎉 Installation Complete!"
echo "Make sure '$LOCAL_BIN' is in your PATH."
echo "You can now launch the app by running: termchat"
echo "=========================================="
