"""Tests for OCR label parsing (no model download)."""

from datetime import date

import numpy as np

from app.services.ocr_service import (
    build_ocr_report,
    parse_medicine_label,
    report_to_json_string,
    sanitize_for_json,
)


SAMPLE_LABEL = """
Crocin Advance
Paracetamol 650 mg Tablets
Batch No. AB1234
Mfg. Date 01/06/2024
Exp. Date 31/05/2026
Qty 20 Tablets
"""


def test_parse_medicine_name():
    parsed = parse_medicine_label(SAMPLE_LABEL)
    assert "paracetamol" in parsed["medicine"].lower() or "crocin" in parsed["medicine"].lower()


def test_parse_batch_and_qty():
    parsed = parse_medicine_label(SAMPLE_LABEL)
    assert parsed.get("batch_number") == "AB1234"
    assert parsed.get("quantity") == 20


def test_parse_dates():
    parsed = parse_medicine_label(SAMPLE_LABEL)
    assert parsed.get("manufacturing_date") == date(2024, 6, 1)
    assert parsed.get("expiry_date") == date(2026, 5, 31)


def test_parse_category():
    parsed = parse_medicine_label(SAMPLE_LABEL)
    assert parsed.get("category") == "painkiller"


def test_structured_report_json():
    parsed = parse_medicine_label(SAMPLE_LABEL)
    report = parsed.get("report")
    assert report is not None
    assert "summary" in report
    assert "ocr_lines" in report
    assert "dates" in report
    assert report["summary"]["medicine_name"]


TELMA_LABEL = """
Telmisartan Tablets 1.P.40 mg
lelma-48
Telma40240
SCHEDULEH PRESCRIPTION
Composition:
Each uncoated tablet contains
Telmisartan IP 40 mg
"""


def test_json_serializes_numpy_confidence():
    lines = [{"line": 1, "text": "Paracetamol 500 mg", "confidence": np.float32(0.91)}]
    report = build_ocr_report("Paracetamol 500 mg", lines)
    raw = report_to_json_string(report)
    assert "0.91" in raw
    assert "Paracetamol" in raw


def test_telmisartan_label_parsing():
    parsed = parse_medicine_label(TELMA_LABEL)
    assert "telmisartan" in parsed["medicine"].lower()
    assert parsed.get("strength") == "40 mg"
    assert parsed.get("prescription_required") is True
    assert parsed.get("schedule") == "H"
    assert parsed["report"]["summary"]["active_ingredient"] == "Telmisartan"
