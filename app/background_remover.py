"""Image background removal helpers."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from rembg import remove

from .utils import BACKGROUND_OUTPUT_DIR

_SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def remove_image_background(input_path: Path) -> dict:
    """Remove the background from an image and save a PNG result."""
    if not input_path.exists():
        return {
            "success": False,
            "output_path": None,
            "message": "Selected image file was not found.",
        }

    if input_path.suffix.lower() not in _SUPPORTED_IMAGE_SUFFIXES:
        return {
            "success": False,
            "output_path": None,
            "message": "Unsupported image format. Use PNG, JPG, JPEG or WEBP.",
        }

    output_filename = f"no_background_{input_path.stem}.png"
    output_path = BACKGROUND_OUTPUT_DIR / output_filename

    try:
        with input_path.open("rb") as source_file:
            output_bytes = remove(source_file.read())

        image = Image.open(BytesIO(output_bytes))
        image.save(output_path, format="PNG")
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        return {
            "success": False,
            "output_path": None,
            "message": f"Background removal failed: {exc}",
        }

    return {
        "success": True,
        "output_path": output_path,
        "message": "Background removed successfully!",
    }
