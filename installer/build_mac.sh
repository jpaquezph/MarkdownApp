#!/usr/bin/env bash
# Build de la app y del instalador (.dmg) para macOS.
# Requiere: Python 3.11+ instalado (python3 --version).
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

pyinstaller --noconfirm --onefile --windowed \
  --name "ConvertidorMarkdown" \
  --icon "app/icon.icns" \
  --collect-all magika \
  --collect-all onnxruntime \
  --hidden-import mammoth \
  --hidden-import openpyxl \
  --hidden-import pptx \
  --hidden-import pdfminer \
  --hidden-import pdfminer.six \
  --hidden-import pdfplumber \
  --hidden-import xlrd \
  app/main.py

APP_NAME="ConvertidorMarkdown"
mkdir -p dist_installer
rm -rf dist_dmg
mkdir -p dist_dmg
cp -R "dist/${APP_NAME}.app" dist_dmg/
ln -s /Applications "dist_dmg/Applications"

hdiutil create -volname "$APP_NAME" -srcfolder dist_dmg -ov -format UDZO \
  "dist_installer/${APP_NAME}_Installer.dmg"

rm -rf dist_dmg
echo "Listo: dist_installer/${APP_NAME}_Installer.dmg"
