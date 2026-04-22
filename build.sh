#!/bin/bash
# Build standalone app with PyInstaller
# Mac: produces dist/WolfgangSocialAgent.app
# Windows: run on Windows, produces dist/WolfgangSocialAgent.exe

set -e

pip3 install pyinstaller

pyinstaller \
  --name "WolfgangSocialAgent" \
  --windowed \
  --onedir \
  --add-data "src:src" \
  --hidden-import "customtkinter" \
  --hidden-import "PIL" \
  --hidden-import "PIL._tkinter_finder" \
  --collect-data customtkinter \
  app.py

echo ""
echo "Build fertig → dist/WolfgangSocialAgent/"
echo "Mac: dist/WolfgangSocialAgent.app per Doppelklick starten"
