"""Free tools — label OCR scan & medicine safety check."""

import streamlit as st

from app.services.ocr_service import ocr_available, scan_medicine_image
from app.ui import render_footer, render_page_header
from app.ui_ocr import render_ocr_scan_result
from app.utils import detect_medicine_category, get_block_reason, is_medicine_safe


def render() -> None:
    render_page_header(
        "Scan & Tools",
        "OCR label reader and medicine safety checker — 100% free, runs locally",
        "🔬",
    )

    tab_ocr, tab_safety = st.tabs(["📷 Scan medicine label", "🛡️ Safety checker"])

    with tab_ocr:
        st.markdown(
            "Upload a photo of a **medicine strip, box, or bottle**. "
            "We read the label locally (no cloud API) and suggest form fields."
        )
        if ocr_available():
            st.caption("OCR engine: RapidOCR (on-device)")
        else:
            st.warning(
                "OCR engine not loaded. Run: `pip install rapidocr-onnxruntime opencv-python-headless` "
                "then restart the app. First scan may download a small model (~10MB)."
            )

        img = st.file_uploader("Label photo", type=["jpg", "jpeg", "png"], key="tools_ocr_img")
        if img and st.button("Scan label", type="primary", key="tools_scan_btn"):
            with st.spinner("Reading label…"):
                parsed, err = scan_medicine_image(img.getvalue())
            if err:
                st.error(err)
            else:
                st.success("Label scanned — review suggestions below")
                st.session_state.ocr_scan_result = parsed

        if st.session_state.get("ocr_scan_result"):
            p = st.session_state.ocr_scan_result
            render_ocr_scan_result(p)
            dates = (p.get("report") or {}).get("dates") or {}
            if dates.get("manufacturing"):
                st.info(f"Manufacturing date detected: **{dates['manufacturing']}**")
            if dates.get("expiry"):
                st.info(f"Expiry on label: **{dates['expiry']}**")
            if st.button("Use in donation form →", type="primary"):
                draft = st.session_state.get("donor_draft", {})
                draft.update(
                    medicine=p.get("medicine") or draft.get("medicine", ""),
                    medicine_type=p.get("medicine_type", "Tablet"),
                    quantity=p.get("quantity", 1),
                )
                mfg = p.get("manufacturing_date") or (dates.get("manufacturing") if dates else None)
                if mfg:
                    draft["mfg_date"] = mfg
                if p.get("batch_number"):
                    draft["batch_number"] = p["batch_number"]
                if p.get("prescription_required"):
                    draft["prescription_required"] = True
                st.session_state.donor_draft = draft
                st.session_state.donor_step = 1
                st.session_state._ocr_prefill = True
                from app.ui import set_nav

                set_nav("💊 Donate Medicines")
                st.toast("Fields copied — complete your donation", icon="💊")
                st.rerun()

    with tab_safety:
        st.markdown("Check if a medicine name is on our **blocked list** and see its category.")
        name = st.text_input("Medicine name", placeholder="e.g. Paracetamol 500mg")
        if name:
            safe = is_medicine_safe(name)
            cat = detect_medicine_category(name)
            if safe:
                st.success(f"✅ **{name}** can be donated (category: **{cat}**)")
            else:
                reason = get_block_reason(name) or "Blocked substance"
                st.error(
                    f"⛔ **{name}** cannot be accepted.\n\n"
                    f"**Reason:** {reason}\n\n"
                    f"**Classification:** {cat}"
                )
            st.caption(
                "This is a demo safety list for the hackathon — not medical advice. "
                "Always follow prescription and local regulations."
            )

    render_footer()
