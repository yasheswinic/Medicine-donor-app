"""Secure file upload handling."""

import io
import uuid
from pathlib import Path
from typing import Optional

from app.constants import UPLOADS_DIR
from app.utils import get_logger, validate_image_upload

logger = get_logger()


def ensure_upload_dir() -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOADS_DIR


def save_medicine_image(uploaded_file) -> tuple[Optional[str], Optional[str]]:
    """Save uploaded image with UUID filename; returns (path, error)."""
    if uploaded_file is None:
        return None, None

    content_type = uploaded_file.type or "application/octet-stream"
    size = uploaded_file.size or 0
    filename = uploaded_file.name or "image.jpg"

    valid, msg = validate_image_upload(content_type, size, filename)
    if not valid:
        logger.warning("Upload rejected: %s", msg)
        return None, msg

    ensure_upload_dir()
    ext = Path(filename).suffix.lower() or ".jpg"
    new_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOADS_DIR / new_name

    try:
        data = uploaded_file.getvalue()
        dest.write_bytes(data)
        _save_thumbnail(data, dest)
        logger.info("Saved upload: %s", new_name)
        return str(dest.relative_to(UPLOADS_DIR.parent)), None
    except OSError as e:
        logger.error("Upload save failed: %s", e)
        return None, "Failed to save image"


def _save_thumbnail(image_bytes: bytes, original_path: Path, max_size: int = 320) -> None:
    """Create a small JPEG thumbnail for faster dashboard previews."""
    try:
        from PIL import Image

        thumb_path = original_path.with_name(f"{original_path.stem}_thumb.jpg")
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((max_size, max_size))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(thumb_path, format="JPEG", quality=85)
    except Exception:
        pass  # thumbnail is optional
