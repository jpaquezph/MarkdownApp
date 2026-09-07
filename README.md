# Convertidor a Markdown

App de escritorio (Windows y macOS) para convertir Word, Excel, PowerPoint, PDF e imágenes a Markdown (.md).

## Uso

- **Windows:** instalá `ConvertidorMarkdown_Setup.exe` (Actions → build-windows, o `dist_installer/`).
- **macOS:** abrí `ConvertidorMarkdown_Installer.dmg` y arrastrá la app a `Applications` (Actions → build-macos).

No hace falta instalar Python ni nada más en la máquina del usuario final: todo va empaquetado en el instalador.

En la app: agregá archivos o una carpeta, elegí la carpeta destino (chips de Escritorio/Documentos/Descargas o "Examinar...") y tocá "Convertir a Markdown".

Formatos soportados: `.docx .xlsx .xls .pptx .pdf .csv .html .json .xml .txt .png .jpg .gif .bmp`

> Nota: las imágenes se convierten con metadatos básicos (no hace OCR de texto dentro de la foto/escaneo).

## Bajar el instalador ya compilado (sin tocar código)

Cada push a `main` dispara un build automático en GitHub Actions para Windows y macOS. Andá a la pestaña **Actions** del repo → último run de "Build installers" → **Artifacts**, y bajá `ConvertidorMarkdown-mac` o `ConvertidorMarkdown-windows`.

## Reconstruir desde el código

### macOS

Requiere Python 3.11+ (`python3 --version`).

```bash
bash installer/build_mac.sh
```

Genera `dist_installer/ConvertidorMarkdown_Installer.dmg`.

### Windows

Requiere Python 3.12 con `markitdown`, `pyinstaller` y `pillow` instalados (`pip install -r requirements.txt`), e [Inno Setup 6](https://jrsoftware.org/isinfo.php).

```bash
# 1. Generar el .exe
python -m PyInstaller --noconfirm --onefile --windowed \
  --name "ConvertidorMarkdown" --icon "app/icon.ico" \
  --collect-all magika --collect-all onnxruntime \
  --hidden-import mammoth --hidden-import openpyxl --hidden-import pptx \
  --hidden-import pdfminer --hidden-import pdfminer.six \
  --hidden-import pdfplumber --hidden-import xlrd \
  app/main.py

# 2. Generar el instalador
"ISCC.exe" installer/setup.iss
```

Genera `dist_installer/ConvertidorMarkdown_Setup.exe`.
