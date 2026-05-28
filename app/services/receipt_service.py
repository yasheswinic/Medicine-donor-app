"""Donation receipt text + QR code (free, local)."""

from __future__ import annotations

import io
from datetime import date
from typing import Any, Optional

from app.utils import get_expiry_date


def generate_qr_png(tracking_id: str, size: int = 280) -> Optional[bytes]:
    """PNG bytes for tracking QR, or None if qrcode not installed."""
    if not tracking_id:
        return None
    try:
        import qrcode

        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(f"meddonate://track/{tracking_id}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1565c0", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def generate_receipt_text(donation: dict[str, Any]) -> str:
    """Plain-text donation receipt for download."""
    mfg = donation.get("manufacturing_date") or donation.get("mfg_date")
    mtype = donation.get("medicine_type", "Tablet")
    expiry = ""
    if mfg:
        try:
            if isinstance(mfg, str):
                mfg_d = date.fromisoformat(mfg[:10])
            else:
                mfg_d = mfg
            expiry = str(get_expiry_date(mfg_d, mtype))
        except Exception:
            expiry = "—"

    lines = [
        "=" * 48,
        "  MedDonate — Donation Receipt",
        "=" * 48,
        "",
        f"Tracking ID:  {donation.get('tracking_id', '—')}",
        f"Date:         {(donation.get('created_at') or '')[:19]}",
        f"Status:       {donation.get('status', 'available')}",
        "",
        "— Donor —",
        f"Name:         {donation.get('name', '—')}",
        f"Email:        {donation.get('email', '—')}",
        f"Phone:        {donation.get('phone', '—')}",
        f"City:         {donation.get('city', '—')}, {donation.get('locality', '—')}",
        "",
        "— Medicine —",
        f"Medicine:     {donation.get('medicine', '—')}",
        f"Type:         {mtype}",
        f"Quantity:     {donation.get('quantity', 1)}",
        f"Category:     {donation.get('category', 'general')}",
        f"Mfg date:     {mfg}",
        f"Est. expiry:  {expiry}",
        "",
        "— Pickup —",
        f"Address:      {donation.get('pickup_address') or '—'}",
        f"Time:         {donation.get('pickup_time') or '—'}",
        f"Pincode:      {donation.get('pincode', '—')}",
        "",
        "Scan the QR code in the app to track this donation.",
        "This is a demo receipt — not a tax or legal document.",
        "=" * 48,
    ]
    return "\n".join(lines)
