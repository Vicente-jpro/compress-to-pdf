# compress to pdf

A Python 3.14 desktop application that compresses PDF files down to a maximum
size of **2.8 MB** using Ghostscript (primary) or pypdf (fallback).

---

## Project structure

```
compress-to-pdf/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── .gitignore
├── input-file/          # Source PDFs (created automatically)
├── output-file/         # Compressed PDFs (created automatically)
└── app/
    ├── __init__.py
    ├── gui.py           # Tkinter GUI
    ├── compressor.py    # PDF compression logic
    └── utils.py         # Shared constants and helpers
```

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| **Python 3.14+** | Required |
| **Ghostscript** | Strongly recommended – best compression ratio |
| **pypdf ≥ 4** | Pure-Python fallback; installed via `requirements.txt` |

### Install Python dependencies

```bash
pip install -r requirements.txt
```

### Install Ghostscript (recommended)

**Windows**  
Download the installer from <https://www.ghostscript.com/releases/gsdnld.html>
and make sure `gswin64c` (or `gswin32c`) is on your `PATH`.

**macOS**

```bash
brew install ghostscript
```

**Linux (Ubuntu / Debian)**

```bash
sudo apt-get install ghostscript
```

> If Ghostscript is not installed the application falls back to *pypdf*, which
> provides basic compression but typically achieves a smaller reduction ratio.

---

## Usage

1. Run the application:

   ```bash
   python main.py
   ```

2. Click **📂 Upload** – choose a `.pdf` file.  
   The file is copied to `input-file/`.

3. Click **⚙ Compress** – the application compresses the PDF and saves the
   result to `output-file/`.  
   Live status messages are shown in the window.

4. Click **💾 Download** – choose where to save a copy of the compressed file.  
   *(This button is only active after a successful compression.)*

---

## Compression strategy

1. **Ghostscript** is tried first with three quality presets in decreasing
   order (`printer → ebook → screen`).  The loop stops as soon as the file
   fits within **2.8 MB**.
2. If Ghostscript is unavailable, **pypdf** compresses the content streams.
3. If neither method can reach the 2.8 MB target, the smallest achievable
   version is kept and the user is informed of the actual size.

---

## Notes

* `input-file/` and `output-file/` are created automatically on first run.
* Only `.pdf` files are accepted.
* Compression runs in a background thread so the UI stays responsive.
