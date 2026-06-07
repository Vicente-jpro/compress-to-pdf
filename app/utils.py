"""Shared constants and helper utilities."""
import os
from pathlib import Path

# Maximum target size: 2.8 MB in bytes
TARGET_SIZE_BYTES: int = int(2.8 * 1024 * 1024)

# Project root (two levels up from this file: app/ -> project root)
BASE_DIR: Path = Path(__file__).parent.parent

# Working directories
INPUT_DIR: Path = BASE_DIR / "input-file"
OUTPUT_DIR: Path = BASE_DIR / "output-file"


def ensure_directories() -> None:
    """Create input-file and output-file directories if they don't exist."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def format_size(size_bytes: int) -> str:
    """Return a human-readable file size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_file_size(filepath: str | Path) -> int:
    """Return the size of *filepath* in bytes."""
    return os.path.getsize(filepath)
