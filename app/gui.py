"""Tkinter GUI for the compress to pdf application."""
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .compressor import compress_pdf
from .utils import INPUT_DIR, ensure_directories, format_size, get_file_size

# Colour palette
_CLR_BG = "#f5f5f5"
_CLR_SUCCESS = "#2e7d32"
_CLR_WARNING = "#e65100"
_CLR_ERROR = "#c62828"
_CLR_NEUTRAL = "#424242"


class CompressToPdfApp:
    """Main application window for compress to pdf."""

    def __init__(self) -> None:
        ensure_directories()

        self._selected_file: Path | None = None
        self._output_file: Path | None = None

        self._root = tk.Tk()
        self._root.title("compress to pdf")
        self._root.resizable(False, False)
        self._root.configure(bg=_CLR_BG)

        self._build_ui()
        self._center_window()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble all widgets."""
        root = self._root

        # ── Outer padding frame ────────────────────────────────────────
        outer = ttk.Frame(root, padding="24 20 24 20")
        outer.grid(row=0, column=0)

        # ── Title ──────────────────────────────────────────────────────
        ttk.Label(
            outer,
            text="compress to pdf",
            font=("Helvetica", 20, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(0, 18))

        # ── File information card ──────────────────────────────────────
        info = ttk.LabelFrame(outer, text="File information", padding="12 8")
        info.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 16))
        info.columnconfigure(1, weight=1)

        lbl_cfg = {"sticky": "w", "pady": 3}
        val_cfg = {"sticky": "w", "padx": (12, 0), "pady": 3}

        ttk.Label(info, text="File name:").grid(row=0, column=0, **lbl_cfg)
        self._file_name_var = tk.StringVar(value="No file selected")
        ttk.Label(info, textvariable=self._file_name_var, foreground=_CLR_NEUTRAL).grid(
            row=0, column=1, **val_cfg
        )

        ttk.Label(info, text="Original size:").grid(row=1, column=0, **lbl_cfg)
        self._original_size_var = tk.StringVar(value="—")
        ttk.Label(info, textvariable=self._original_size_var).grid(row=1, column=1, **val_cfg)

        ttk.Label(info, text="Compressed size:").grid(row=2, column=0, **lbl_cfg)
        self._compressed_size_var = tk.StringVar(value="—")
        ttk.Label(info, textvariable=self._compressed_size_var).grid(row=2, column=1, **val_cfg)

        ttk.Label(info, text="2.8 MB target:").grid(row=3, column=0, **lbl_cfg)
        self._target_var = tk.StringVar(value="—")
        self._target_lbl = ttk.Label(info, textvariable=self._target_var)
        self._target_lbl.grid(row=3, column=1, **val_cfg)

        # ── Action buttons ─────────────────────────────────────────────
        btn_row = ttk.Frame(outer)
        btn_row.grid(row=2, column=0, columnspan=3, pady=(0, 14))

        btn_cfg = {"width": 14, "padding": "8 5"}

        self._upload_btn = ttk.Button(
            btn_row, text="📂  Upload", command=self._on_upload, **btn_cfg
        )
        self._upload_btn.grid(row=0, column=0, padx=6)

        self._compress_btn = ttk.Button(
            btn_row,
            text="⚙  Compress",
            command=self._on_compress,
            state="disabled",
            **btn_cfg,
        )
        self._compress_btn.grid(row=0, column=1, padx=6)

        self._download_btn = ttk.Button(
            btn_row,
            text="💾  Download",
            command=self._on_download,
            state="disabled",
            **btn_cfg,
        )
        self._download_btn.grid(row=0, column=2, padx=6)

        # ── Progress bar ───────────────────────────────────────────────
        self._progress = ttk.Progressbar(outer, mode="indeterminate", length=420)
        self._progress.grid(row=3, column=0, columnspan=3, pady=(0, 10), sticky="ew")

        # ── Status label ───────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Ready – please upload a PDF file.")
        self._status_lbl = ttk.Label(
            outer,
            textvariable=self._status_var,
            wraplength=420,
            foreground=_CLR_NEUTRAL,
            anchor="center",
            justify="center",
        )
        self._status_lbl.grid(row=4, column=0, columnspan=3, pady=(0, 4))

    def _center_window(self) -> None:
        """Move the window to the centre of the screen."""
        self._root.update_idletasks()
        w = self._root.winfo_reqwidth()
        h = self._root.winfo_reqheight()
        x = (self._root.winfo_screenwidth() - w) // 2
        y = (self._root.winfo_screenheight() - h) // 2
        self._root.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _set_status(self, message: str, color: str = _CLR_NEUTRAL) -> None:
        """Update the status label text and colour."""
        self._status_var.set(message)
        self._status_lbl.configure(foreground=color)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_upload(self) -> None:
        """Open a file dialog and copy the selected PDF to input-file/."""
        filepath = filedialog.askopenfilename(
            title="Select a PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not filepath:
            return  # user cancelled

        src = Path(filepath)
        if src.suffix.lower() != ".pdf":
            messagebox.showerror("Invalid file type", "Please select a .pdf file.")
            return

        dest = INPUT_DIR / src.name
        try:
            shutil.copy2(src, dest)
        except OSError as exc:
            messagebox.showerror("Copy error", f"Could not copy the file:\n{exc}")
            return

        self._selected_file = dest
        self._output_file = None

        # Reset UI for a new file
        self._file_name_var.set(src.name)
        self._original_size_var.set(format_size(get_file_size(dest)))
        self._compressed_size_var.set("—")
        self._target_var.set("—")
        self._target_lbl.configure(foreground=_CLR_NEUTRAL)
        self._compress_btn.configure(state="normal")
        self._download_btn.configure(state="disabled")
        self._set_status(f"File '{src.name}' loaded successfully.", _CLR_SUCCESS)

    def _on_compress(self) -> None:
        """Start compression in a background thread."""
        if not self._selected_file:
            return

        # Lock the UI while compressing
        self._upload_btn.configure(state="disabled")
        self._compress_btn.configure(state="disabled")
        self._download_btn.configure(state="disabled")
        self._progress.start(10)
        self._set_status("Compression in progress…", _CLR_WARNING)

        threading.Thread(target=self._compression_worker, daemon=True).start()

    def _compression_worker(self) -> None:
        """Compression runs here (off the main thread)."""

        def update(msg: str) -> None:
            # Route status updates back to the Tk main thread
            self._root.after(0, lambda m=msg: self._set_status(m, _CLR_WARNING))

        try:
            result = compress_pdf(self._selected_file, progress_callback=update)
        except Exception as exc:  # noqa: BLE001
            self._root.after(0, lambda e=exc: self._handle_error(str(e)))
            return

        self._root.after(0, lambda r=result: self._on_compression_done(r))

    def _on_compression_done(self, result: dict) -> None:
        """Called on the main thread when compression finishes."""
        self._progress.stop()
        self._upload_btn.configure(state="normal")
        self._compress_btn.configure(state="normal")

        if not result["success"]:
            self._set_status(f"Error: {result['message']}", _CLR_ERROR)
            return

        self._output_file = result["output_path"]
        self._compressed_size_var.set(format_size(result["compressed_size"]))

        if result["target_achieved"]:
            self._target_var.set("✓ Achieved")
            self._target_lbl.configure(foreground=_CLR_SUCCESS)
            self._set_status(result["message"], _CLR_SUCCESS)
        else:
            self._target_var.set("✗ Not achieved")
            self._target_lbl.configure(foreground=_CLR_ERROR)
            self._set_status(result["message"], _CLR_ERROR)

        self._download_btn.configure(state="normal")

    def _handle_error(self, error: str) -> None:
        """Handle unexpected compression errors (main thread)."""
        self._progress.stop()
        self._upload_btn.configure(state="normal")
        self._compress_btn.configure(state="normal")
        self._set_status(f"Compression failed: {error}", _CLR_ERROR)

    def _on_download(self) -> None:
        """Save a copy of the compressed PDF to a user-chosen location."""
        if not self._output_file or not self._output_file.exists():
            messagebox.showerror("No file", "No compressed file is available.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save compressed PDF as…",
            defaultextension=".pdf",
            initialfile=self._output_file.name,
            filetypes=[("PDF files", "*.pdf")],
        )
        if not save_path:
            return  # user cancelled

        try:
            shutil.copy2(self._output_file, save_path)
            self._set_status(f"File saved to: {save_path}", _CLR_SUCCESS)
            messagebox.showinfo("Saved", f"File saved successfully!\n\n{save_path}")
        except OSError as exc:
            messagebox.showerror("Save error", f"Could not save the file:\n{exc}")

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self._root.mainloop()
