"""PDF compression logic.

Primary method  : Ghostscript (subprocess) – best compression ratio.
Fallback method : pypdf – pure-Python, lower ratio but no external deps.
"""
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from .utils import OUTPUT_DIR, TARGET_SIZE_BYTES, format_size

# Ghostscript quality presets tried in descending quality order.
# Lower quality → smaller file.
_GS_QUALITY_PRESETS: list[str] = ["printer", "ebook", "screen"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_ghostscript() -> str | None:
    """Return the name of the Ghostscript executable, or *None* if not found."""
    for candidate in ("gs", "gswin64c", "gswin32c", "gsc"):
        if shutil.which(candidate):
            return candidate
    return None


def _ghostscript_compress(input_path: Path, output_path: Path, quality: str) -> bool:
    """Compress *input_path* with Ghostscript at *quality* level.

    Returns *True* on success, *False* otherwise.
    """
    gs = _find_ghostscript()
    if gs is None:
        return False

    cmd: list[str] = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        return result.returncode == 0 and output_path.exists()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _pypdf_compress(input_path: Path, output_path: Path) -> bool:
    """Compress *input_path* using pypdf (pure-Python fallback).

    Returns *True* on success, *False* otherwise.
    """
    try:
        from pypdf import PdfReader, PdfWriter  # type: ignore[import]

        reader = PdfReader(str(input_path))
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        # Compress content streams for each page
        for page in writer.pages:
            page.compress_content_streams()

        with open(output_path, "wb") as fh:
            writer.write(fh)

        return output_path.exists()
    except ImportError:
        return False
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compress_pdf(
    input_path: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> dict:
    """Compress *input_path* and save the result inside ``output-file/``.

    Parameters
    ----------
    input_path:
        Path to the source PDF (already copied to ``input-file/``).
    progress_callback:
        Optional callable that receives short status strings during processing.

    Returns
    -------
    dict with keys:
        ``success``         – bool
        ``output_path``     – Path or None
        ``original_size``   – int (bytes)
        ``compressed_size`` – int or None (bytes)
        ``target_achieved`` – bool
        ``message``         – str (human-readable summary)
    """

    def log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    original_size: int = os.path.getsize(input_path)
    output_filename = f"compressed_{input_path.name}"
    output_path: Path = OUTPUT_DIR / output_filename

    # ── Fast path: already within target ───────────────────────────────────
    if original_size <= TARGET_SIZE_BYTES:
        shutil.copy2(input_path, output_path)
        return {
            "success": True,
            "output_path": output_path,
            "original_size": original_size,
            "compressed_size": original_size,
            "target_achieved": True,
            "message": (
                f"File is already under 2.8 MB ({format_size(original_size)}). "
                "Copied as-is."
            ),
        }

    # ── Ghostscript path ────────────────────────────────────────────────────
    best_path: Path | None = None
    best_size: int = original_size

    if _find_ghostscript():
        log("Ghostscript found. Starting compression…")
        for quality in _GS_QUALITY_PRESETS:
            log(f"Trying quality preset: {quality}…")
            temp_out = OUTPUT_DIR / f"_tmp_{quality}_{output_filename}"

            if _ghostscript_compress(input_path, temp_out, quality):
                candidate_size = os.path.getsize(temp_out)
                if candidate_size < best_size:
                    # Keep this result and discard the previous best
                    if best_path and best_path.exists():
                        best_path.unlink(missing_ok=True)
                    best_size = candidate_size
                    best_path = temp_out
                else:
                    temp_out.unlink(missing_ok=True)

                if best_size <= TARGET_SIZE_BYTES:
                    break  # target reached – no need for lower quality
            else:
                temp_out.unlink(missing_ok=True)

        if best_path and best_path.exists():
            shutil.move(str(best_path), output_path)

        # Remove any leftover temp files
        for q in _GS_QUALITY_PRESETS:
            leftover = OUTPUT_DIR / f"_tmp_{q}_{output_filename}"
            if leftover.exists():
                leftover.unlink(missing_ok=True)

    else:
        # ── pypdf fallback ──────────────────────────────────────────────────
        log("Ghostscript not found. Using pypdf fallback…")
        if _pypdf_compress(input_path, output_path):
            best_size = os.path.getsize(output_path)
        else:
            log("pypdf compression also failed.")

    # ── Result ──────────────────────────────────────────────────────────────
    if not output_path.exists():
        return {
            "success": False,
            "output_path": None,
            "original_size": original_size,
            "compressed_size": None,
            "target_achieved": False,
            "message": "Compression failed – unable to process the file.",
        }

    compressed_size = os.path.getsize(output_path)
    target_achieved = compressed_size <= TARGET_SIZE_BYTES

    if target_achieved:
        message = (
            f"Compression successful! "
            f"Reduced from {format_size(original_size)} "
            f"to {format_size(compressed_size)}."
        )
    else:
        message = (
            f"Target of 2.8 MB could not be reached. "
            f"Best result: {format_size(compressed_size)} "
            f"(original: {format_size(original_size)})."
        )

    return {
        "success": True,
        "output_path": output_path,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "target_achieved": target_achieved,
        "message": message,
    }
