"""Shared OCR result display for Streamlit views."""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.services.ocr_service import ensure_ocr_report, report_to_json_string


def render_ocr_scan_result(parsed: dict[str, Any], *, show_metrics: bool = True) -> None:
    """Show structured JSON report + optional field metrics."""
    report = ensure_ocr_report(parsed)

    if show_metrics:
        summary = report.get("summary") or {}
        c1, c2 = st.columns(2)
        c1.metric("Medicine", summary.get("medicine_name") or parsed.get("medicine") or "—")
        c2.metric("Type", summary.get("medicine_type") or parsed.get("medicine_type") or "—")
        c3, c4, c5 = st.columns(3)
        c3.metric("Strength", summary.get("strength") or parsed.get("strength") or "—")
        c4.metric("Batch", (report.get("identifiers") or {}).get("batch_number") or "—")
        c5.metric("Category", summary.get("category") or parsed.get("category") or "—")
        if summary.get("prescription_required"):
            st.warning(f"Prescription likely required (Schedule {summary.get('schedule') or '—'})")

    json_text = report_to_json_string(report)

    tab_tree, tab_raw = st.tabs(["JSON tree", "JSON text"])

    with tab_tree:
        try:
            st.json(report)
        except Exception:
            st.warning("Tree view unavailable — use the JSON text tab.")
            st.code(json_text, language="json")

    with tab_raw:
        st.code(json_text, language="json")

    st.download_button(
        "⬇ Download JSON",
        json_text,
        file_name="label-scan.json",
        mime="application/json",
        use_container_width=True,
        key=f"dl_json_{hash(json_text) % 10**8}",
    )

    with st.expander("Plain text from label"):
        st.text(report.get("full_text") or parsed.get("raw_text") or "—")
