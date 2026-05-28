"""Free OCR for medicine labels — RapidOCR (onnx, no paid API)."""

from __future__ import annotations

import io
import json
import re
from datetime import date, datetime
from typing import Any, Optional

from app.constants import MEDICINE_TYPES
from app.utils import detect_medicine_category, get_logger

logger = get_logger()

_ocr_engine: Any = None
_OCR_UNAVAILABLE: Optional[str] = None

_RE_EXPIRY = re.compile(
    r"(?:exp(?:iry)?\.?(?:\s*date)?|use\s*before|best\s*before)[\s:.]+"
    r"(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2})",
    re.I,
)
_RE_MFG = re.compile(
    r"(?:(?:mfg|mfd)(?:\.?\s*date)?|manufactur(?:ed|ing)?\s*date)[\s:.]+"
    r"(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2})",
    re.I,
)
_RE_BATCH = re.compile(
    r"(?:batch\s*(?:no\.?|number|#)|lot\s*(?:no\.?|number)?)\s*[:.\s]+([A-Z0-9]{3,})",
    re.I,
)
_RE_QTY = re.compile(r"(?:qty|quantity|net\s*qty|contains)[\s:.]*(\d+)", re.I)
_RE_STRENGTH = re.compile(r"(\d+)\s*\.?\s*mg\b", re.I)
_RE_INGREDIENT = re.compile(
    r"\b([A-Za-z]{4,}(?:misartan|lisartan|sartan|artan|olol|pril|statin|mycin|"
    r"formin|cillin|azole|dipine|done|pam|zole|caine|profen|mol|pine)s?)\b",
    re.I,
)
_RE_BRAND = re.compile(r"\b([A-Z][a-z]{2,}[-]?\d{0,4})\b")
_RE_SCHEDULE_H = re.compile(r"schedule\s*[^\w]*\s*h|scheduleh", re.I)


def _get_engine() -> tuple[Any, Optional[str]]:
    global _ocr_engine, _OCR_UNAVAILABLE
    if _ocr_engine is not None:
        return _ocr_engine, None
    if _OCR_UNAVAILABLE:
        return None, _OCR_UNAVAILABLE
    try:
        from rapidocr_onnxruntime import RapidOCR

        _ocr_engine = RapidOCR()
        return _ocr_engine, None
    except Exception as e:
        _OCR_UNAVAILABLE = (
            f"OCR not available ({e}). Install: pip install rapidocr-onnxruntime opencv-python-headless"
        )
        logger.warning(_OCR_UNAVAILABLE)
        return None, _OCR_UNAVAILABLE


def ocr_available() -> bool:
    engine, err = _get_engine()
    return engine is not None and err is None


def extract_lines_from_bytes(
    image_bytes: bytes,
) -> tuple[list[dict[str, Any]], str, Optional[str]]:
    """
    Run OCR and return structured lines + joined text.
    Each line: {line, text, confidence}
    """
    if not image_bytes:
        return [], "", "No image data"
    engine, err = _get_engine()
    if err or engine is None:
        return [], "", err

    try:
        import numpy as np
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        arr = np.array(img)
        result, _ = engine(arr)
        if not result:
            return [], "", "No text detected — try a clearer, well-lit photo"

        lines: list[dict[str, Any]] = []
        for i, item in enumerate(result, start=1):
            if len(item) < 2:
                continue
            text = str(item[1]).strip()
            if not text:
                continue
            conf = None
            if len(item) > 2:
                try:
                    conf = round(float(item[2]), 3)
                except (TypeError, ValueError):
                    conf = None
            lines.append({"line": i, "text": text, "confidence": conf})

        joined = "\n".join(ln["text"] for ln in lines)
        return lines, joined, None
    except Exception as e:
        logger.exception("OCR failed")
        return [], "", f"OCR failed: {e}"


def extract_text_from_bytes(image_bytes: bytes) -> tuple[str, Optional[str]]:
    """Backward-compatible: plain text only."""
    lines, joined, err = extract_lines_from_bytes(image_bytes)
    return joined, err


def _parse_date(raw: str) -> Optional[date]:
    raw = raw.strip().replace(".", "/").replace("-", "/")
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _iso(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def sanitize_for_json(value: Any) -> Any:
    """Convert OCR result to plain Python types safe for st.json / json.dumps."""
    if value is None:
        return None
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return None if value != value else round(value, 6)  # NaN -> None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_for_json(v) for v in value]
    # numpy / other numeric scalars
    if hasattr(value, "item"):
        try:
            return sanitize_for_json(value.item())
        except Exception:
            pass
    if hasattr(value, "tolist"):
        return sanitize_for_json(value.tolist())
    return str(value)


def _guess_medicine_type(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ("syrup", "suspension", "oral liquid")):
        return "Syrup"
    if "capsule" in lower or "cap." in lower:
        return "Capsule"
    if "injection" in lower or "inj." in lower:
        return "Injection"
    if any(w in lower for w in ("tablet", "tab.", "tabs", "uncoated")):
        return "Tablet"
    return "Tablet"


def _fix_ocr_typos(text: str) -> str:
    """Light fixes for common strip OCR mistakes."""
    t = text
    for old, new in (
        ("tolmi", "telmi"),
        ("tolmisartan", "telmisartan"),
        ("artenf", "artan"),
        ("orug", "drug"),
        ("presceiption", "prescription"),
        ("exhipiehts", "excipients"),
    ):
        t = re.sub(old, new, t, flags=re.I)
    return t


def _extract_strength(joined: str) -> Optional[str]:
    amounts = [int(m.group(1)) for m in _RE_STRENGTH.finditer(joined)]
    valid = [a for a in amounts if 1 <= a <= 2000]
    if not valid:
        return None
    return f"{max(valid)} mg"


def _extract_active_ingredient(lines: list[str], joined: str) -> Optional[str]:
    fixed = _fix_ocr_typos(joined)
    for line in lines:
        line_f = _fix_ocr_typos(line)
        m = _RE_INGREDIENT.search(line_f)
        if m:
            name = m.group(1)
            if len(name) >= 5 and name.lower() not in ("contains", "composition", "excipients"):
                return name.title()
    m = _RE_INGREDIENT.search(fixed)
    return m.group(1).title() if m else None


def _extract_brand_hints(lines: list[str]) -> list[str]:
    hints: list[str] = []
    skip = re.compile(r"schedule|composition|manufactur|contains|each|mrp|batch", re.I)
    for line in lines:
        if skip.search(line) or len(line) > 40:
            continue
        if _RE_INGREDIENT.search(_fix_ocr_typos(line)):
            continue
        m = _RE_BRAND.findall(line)
        for b in m:
            if 3 <= len(b) <= 20 and b not in hints:
                hints.append(b)
    return hints[:5]


def _detect_schedule(joined: str) -> tuple[Optional[str], bool]:
    compact = joined.replace(" ", "").upper()
    if _RE_SCHEDULE_H.search(joined) or "SCHEDULEH" in compact:
        return "H", True
    if re.search(r"\b(rx|prescription)\b", joined, re.I):
        return None, True
    return None, False


def _guess_medicine_name(lines: list[str], joined: str, active: Optional[str]) -> str:
    """Pick the best product title line from OCR output."""
    skip = re.compile(
        r"^(exp|mfg|batch|mrp|qty|manufactured|marketed|contains|each|store|keep|"
        r"schedule|rx|prescription|lic|only|for|use|date|no\.|www\.|http|composition|"
        r"drug|caution|sold|retail|excipient)",
        re.I,
    )
    candidates: list[tuple[int, str]] = []

    for line in lines:
        s = _fix_ocr_typos(line.strip())
        if len(s) < 4 or skip.match(s):
            continue
        if re.match(r"^\d+[\d\s/\-.,]*$", s):
            continue
        score = len(s)
        if re.search(r"tablets?|capsules?|syrup|injection", s, re.I):
            score += 40
        if _RE_STRENGTH.search(s):
            score += 25
        if active and active.lower() in s.lower():
            score += 35
        if s[0].isupper():
            score += 10
        candidates.append((score, s))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1][:150]

    if active:
        mtype = _guess_medicine_type(joined)
        strength = _extract_strength(joined)
        base = active
        if strength:
            base = f"{active} {strength}"
        return f"{base} {mtype}"[:150]

    return _fix_ocr_typos(lines[0].strip())[:150] if lines else ""


def build_ocr_report(
    text: str,
    ocr_lines: Optional[list[dict[str, Any]]] = None,
    *,
    flat: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Structured JSON-friendly report for UI display."""
    lines = [ln["text"] for ln in ocr_lines] if ocr_lines else [ln.strip() for ln in text.splitlines() if ln.strip()]
    joined = " ".join(lines)
    joined_fixed = _fix_ocr_typos(joined)

    expiry_raw = mfg_raw = batch = None
    quantity = None
    for pattern, store in (
        (_RE_EXPIRY, "exp"),
        (_RE_MFG, "mfg"),
        (_RE_BATCH, "batch"),
        (_RE_QTY, "qty"),
    ):
        m = pattern.search(joined_fixed)
        if m and store == "exp":
            expiry_raw = m.group(1)
        elif m and store == "mfg":
            mfg_raw = m.group(1)
        elif m and store == "batch":
            batch = m.group(1)
        elif m and store == "qty":
            quantity = int(m.group(1))

    expiry_date = _parse_date(expiry_raw) if expiry_raw else None
    mfg_date = _parse_date(mfg_raw) if mfg_raw else None
    active = _extract_active_ingredient(lines, joined_fixed)
    strength = _extract_strength(joined_fixed)
    schedule, rx_required = _detect_schedule(joined_fixed)
    brand_hints = _extract_brand_hints(lines)
    medicine = (flat or {}).get("medicine") or _guess_medicine_name(lines, joined_fixed, active)
    medicine_type = (flat or {}).get("medicine_type") or _guess_medicine_type(joined_fixed)
    category = (flat or {}).get("category") or (
        detect_medicine_category(active or medicine) if (active or medicine) else "general"
    )

    avg_conf = None
    if ocr_lines:
        confs = [ln["confidence"] for ln in ocr_lines if ln.get("confidence") is not None]
        if confs:
            avg_conf = round(sum(confs) / len(confs), 3)

    report = {
        "scan_meta": {
            "engine": "RapidOCR",
            "line_count": len(ocr_lines) if ocr_lines else len(lines),
            "average_confidence": avg_conf,
        },
        "summary": {
            "medicine_name": medicine,
            "active_ingredient": active,
            "strength": strength,
            "medicine_type": medicine_type,
            "category": category,
            "prescription_required": rx_required,
            "schedule": schedule,
            "brand_hints": brand_hints,
        },
        "dates": {
            "manufacturing": _iso(mfg_date),
            "expiry": _iso(expiry_date),
        },
        "identifiers": {
            "batch_number": batch,
            "quantity": quantity or 1,
        },
        "composition": {
            "label_found": bool(re.search(r"composition", joined_fixed, re.I)),
            "active_ingredient": active,
            "strength_per_unit": strength,
        },
        "ocr_lines": ocr_lines
        or [{"line": i + 1, "text": ln, "confidence": None} for i, ln in enumerate(lines)],
        "full_text": text,
        "notes": "Auto-extracted from label — verify all fields before donating.",
    }
    return sanitize_for_json(report)


def ensure_ocr_report(parsed: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe report; rebuild if missing or from an older scan."""
    report = parsed.get("report")
    if isinstance(report, dict) and report.get("summary"):
        return sanitize_for_json(report)

    text = ""
    if isinstance(report, dict):
        text = report.get("full_text") or ""
    text = text or parsed.get("raw_text") or ""
    ocr_lines = (report or {}).get("ocr_lines") if isinstance(report, dict) else None
    if not text and ocr_lines:
        text = "\n".join(
            ln.get("text", "") for ln in ocr_lines if isinstance(ln, dict) and ln.get("text")
        )
    if text:
        return build_ocr_report(text, ocr_lines, flat=parsed)

    return sanitize_for_json({
        "scan_meta": {"engine": "RapidOCR", "line_count": 0, "average_confidence": None},
        "summary": {
            "medicine_name": parsed.get("medicine"),
            "active_ingredient": parsed.get("active_ingredient"),
            "strength": parsed.get("strength"),
            "medicine_type": parsed.get("medicine_type"),
            "category": parsed.get("category"),
            "prescription_required": parsed.get("prescription_required", False),
            "schedule": parsed.get("schedule"),
            "brand_hints": parsed.get("brand_hints") or [],
        },
        "dates": {
            "manufacturing": _iso(parsed.get("manufacturing_date")),
            "expiry": _iso(parsed.get("expiry_date")),
        },
        "identifiers": {
            "batch_number": parsed.get("batch_number"),
            "quantity": parsed.get("quantity", 1),
        },
        "composition": {
            "label_found": False,
            "active_ingredient": parsed.get("active_ingredient"),
            "strength_per_unit": parsed.get("strength"),
        },
        "ocr_lines": [],
        "full_text": "",
        "notes": "No OCR text available — scan again.",
    })


def to_json_safe_scan_result(parsed: dict[str, Any]) -> dict[str, Any]:
    """Full scan payload safe for session_state and JSON export."""
    safe = dict(parsed)
    for key in ("manufacturing_date", "expiry_date"):
        if isinstance(safe.get(key), date):
            safe[key] = safe[key].isoformat()
    safe["report"] = ensure_ocr_report(parsed)
    return sanitize_for_json(safe)


def report_to_json_string(report: dict[str, Any], indent: int = 2) -> str:
    """Pretty JSON for download / display."""
    clean = sanitize_for_json(report)
    return json.dumps(clean, indent=indent, ensure_ascii=False)


def parse_medicine_label(
    text: str,
    ocr_lines: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Parse OCR into flat form fields + structured report JSON."""
    lines = [ln["text"] for ln in ocr_lines] if ocr_lines else [ln.strip() for ln in text.splitlines() if ln.strip()]
    joined = " ".join(_fix_ocr_typos(ln) for ln in lines)

    expiry_raw = mfg_raw = batch = None
    quantity = None
    for pattern, store in (
        (_RE_EXPIRY, "exp"),
        (_RE_MFG, "mfg"),
        (_RE_BATCH, "batch"),
        (_RE_QTY, "qty"),
    ):
        m = pattern.search(joined)
        if m and store == "exp":
            expiry_raw = m.group(1)
        elif m and store == "mfg":
            mfg_raw = m.group(1)
        elif m and store == "batch":
            batch = m.group(1)
        elif m and store == "qty":
            quantity = int(m.group(1))

    expiry_date = _parse_date(expiry_raw) if expiry_raw else None
    mfg_date = _parse_date(mfg_raw) if mfg_raw else None
    active = _extract_active_ingredient(lines, joined)
    strength = _extract_strength(joined)
    schedule, rx_required = _detect_schedule(joined)
    medicine = _guess_medicine_name(lines, joined, active)
    medicine_type = _guess_medicine_type(joined)
    category = detect_medicine_category(active or medicine) if (active or medicine) else "general"

    flat = {
        "medicine": medicine,
        "medicine_type": medicine_type if medicine_type in MEDICINE_TYPES else "Tablet",
        "quantity": quantity or 1,
        "manufacturing_date": mfg_date,
        "expiry_date": expiry_date,
        "batch_number": batch,
        "strength": strength,
        "active_ingredient": active,
        "category": category,
        "prescription_required": rx_required,
        "schedule": schedule,
        "brand_hints": _extract_brand_hints(lines),
        "confidence_note": "Review all fields before submitting.",
    }
    flat["report"] = build_ocr_report(text, ocr_lines, flat=flat)
    return flat


def scan_medicine_image(image_bytes: bytes) -> tuple[dict[str, Any], Optional[str]]:
    """Full pipeline: OCR + structured parse. Returns (JSON-safe result, error)."""
    ocr_lines, text, err = extract_lines_from_bytes(image_bytes)
    if err:
        return {}, err
    if not text.strip():
        return {}, "No text found on the label"
    result = parse_medicine_label(text, ocr_lines)
    return to_json_safe_scan_result(result), None
