"""Shared utilities: logging, sanitization, medicine helpers."""

import logging
import re
from datetime import date, datetime, timezone
from typing import Optional
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.constants import (
    BLOCKED_MEDICINE_PHRASES,
    BLOCKED_MEDICINE_TERMS,
    BLOCKED_TERM_CATEGORIES,
    LOGS_DIR,
    MEDICINE_CATEGORIES,
    SHELF_LIFE_DAYS,
)

_logger: logging.Logger | None = None


def setup_logging() -> logging.Logger:
    """Configure rotating file + console logging."""
    global _logger
    if _logger is not None:
        return _logger

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "app.log"

    logger = logging.getLogger("med_donation")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    return setup_logging()


def sanitize_input(value: str) -> str:
    """Strip dangerous characters from user input."""
    if not value:
        return ""
    cleaned = value.strip()
    cleaned = re.sub(r"[<>\"';\\]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:500]


def normalize_location(city: str, locality: str) -> tuple[str, str]:
    """Normalize city and locality for matching."""
    city_n = sanitize_input(city).lower()
    locality_n = sanitize_input(locality).lower()
    city_n = re.sub(r"[^a-z0-9\s]", "", city_n)
    locality_n = re.sub(r"[^a-z0-9\s]", "", locality_n)
    return city_n, locality_n


def is_medicine_valid(mfg_date: date, medicine_type: str) -> bool:
    """Check medicine is within shelf life."""
    if isinstance(mfg_date, str):
        mfg_date = datetime.strptime(mfg_date, "%Y-%m-%d").date()
    limit = SHELF_LIFE_DAYS.get(medicine_type, 180)
    days_old = (date.today() - mfg_date).days
    return 0 <= days_old <= limit


def get_expiry_date(mfg_date: date, medicine_type: str) -> date:
    """Calculate expiry date from manufacturing date."""
    from datetime import timedelta

    limit = SHELF_LIFE_DAYS.get(medicine_type, 180)
    return mfg_date + timedelta(days=limit)


def _normalize_medicine_name(medicine_name: str) -> str:
    """Lowercase name with only letters, digits, spaces, and slashes."""
    name = medicine_name.lower().strip()
    return re.sub(r"[^a-z0-9\s/]", " ", name)


def _medicine_tokens(name: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", name))


def find_blocked_match(medicine_name: str) -> Optional[str]:
    """
    Return the blocked term or phrase that matched, or None if allowed.
    Uses whole-word matching for single terms to avoid blocking 'metformin' for 'meth'.
    """
    normalized = _normalize_medicine_name(medicine_name)
    if not normalized:
        return None

    tokens = _medicine_tokens(normalized)
    for term in sorted(BLOCKED_MEDICINE_TERMS, key=len, reverse=True):
        if term in tokens:
            return term

    for phrase in BLOCKED_MEDICINE_PHRASES:
        if phrase in normalized:
            return phrase

    return None


def is_medicine_safe(medicine_name: str) -> bool:
    """Block illegal, withdrawn, and other non-donatable medicines."""
    return find_blocked_match(medicine_name) is None


def get_block_reason(medicine_name: str) -> Optional[str]:
    """Human-readable reason when a medicine is blocked."""
    match = find_blocked_match(medicine_name)
    if not match:
        return None
    category = BLOCKED_TERM_CATEGORIES.get(match, "blocked substance")
    return f"Matches blocked term '{match}' — {category}"


def detect_medicine_category(medicine_name: str) -> str:
    """Detect medicine category from name keywords."""
    blocked = find_blocked_match(medicine_name)
    if blocked:
        return BLOCKED_TERM_CATEGORIES.get(blocked, "blocked")

    name = medicine_name.lower()
    keywords = {
        "antibiotic": ["amoxicillin", "azithromycin", "ciprofloxacin", "antibiotic"],
        "painkiller": ["paracetamol", "ibuprofen", "aspirin", "diclofenac", "pain"],
        "vitamin": ["vitamin", "b12", "d3", "calcium", "zinc"],
        "diabetes": ["metformin", "insulin", "glimepiride", "diabetes"],
        "cardiac": ["atorvastatin", "amlodipine", "heart", "cardiac"],
        "respiratory": ["salbutamol", "cough", "asthma", "respiratory"],
    }
    for category, words in keywords.items():
        if any(w in name for w in words):
            return category
    return "general"


def validate_image_upload(content_type: str, size: int, filename: str) -> tuple[bool, str]:
    """Validate uploaded image MIME, size, and extension."""
    from app.constants import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, "Only JPG and PNG images are allowed"
    if content_type not in ALLOWED_IMAGE_TYPES:
        return False, f"Invalid MIME type: {content_type}"
    if size > MAX_UPLOAD_BYTES:
        return False, "File exceeds 5MB limit"
    return True, "OK"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def new_tracking_id() -> str:
    import uuid

    return f"MD-{uuid.uuid4().hex[:8].upper()}"
