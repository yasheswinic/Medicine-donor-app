"""Tests for utility functions."""

from datetime import date, timedelta

from app.utils import (
    detect_medicine_category,
    is_medicine_safe,
    is_medicine_valid,
    normalize_location,
    sanitize_input,
    validate_image_upload,
)


def test_sanitize_input():
    assert sanitize_input("  hello  ") == "hello"
    assert "<script>" not in sanitize_input("<script>alert</script>")


def test_normalize_location():
    city, loc = normalize_location("Mumbai!", "Andheri East")
    assert "mumbai" in city
    assert "andheri" in loc


def test_medicine_valid_tablet():
    recent = date.today() - timedelta(days=30)
    assert is_medicine_valid(recent, "Tablet") is True


def test_medicine_expired():
    old = date.today() - timedelta(days=400)
    assert is_medicine_valid(old, "Tablet") is False


def test_unsafe_medicine():
    assert is_medicine_safe("thalidomide") is False
    assert is_medicine_safe("Paracetamol") is True


def test_heroin_blocked():
    assert is_medicine_safe("heroin") is False
    assert is_medicine_safe("Heroin sulfate") is False
    assert detect_medicine_category("heroin") == "narcotic (illegal)"


def test_metformin_not_blocked_by_meth():
    """'meth' must not match inside metformin."""
    assert is_medicine_safe("Metformin 500mg") is True
    assert detect_medicine_category("Metformin 500mg") == "diabetes"


def test_cocaine_blocked():
    assert is_medicine_safe("cocaine") is False


def test_detect_category():
    assert detect_medicine_category("Paracetamol 500") == "painkiller"
    assert detect_medicine_category("Random Med") == "general"


def test_validate_image():
    ok, _ = validate_image_upload("image/png", 1000, "photo.png")
    assert ok is True
    bad, msg = validate_image_upload("application/pdf", 1000, "doc.pdf")
    assert bad is False
