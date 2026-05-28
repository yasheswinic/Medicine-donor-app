"""Donor flow — profile, multi-step donation, dashboard, timeline."""

from datetime import date, time

import streamlit as st

from app.constants import COMMON_MEDICINES, MEDICINE_TYPES
from app.repositories import donor_repo, match_repo
from app.services.ocr_service import ocr_available, scan_medicine_image
from app.ui_ocr import render_ocr_scan_result
from app.services.receipt_service import generate_qr_png, generate_receipt_text
from app.repositories.notification_repo import add as notify
from app.services.matching_service import find_matches_for_donor
from app.services.upload_service import save_medicine_image
from app.services.validation_service import validate_donor
from app.ui import (
    NAV_MAIN,
    confidence_badge,
    donor_status_pill,
    empty_state,
    render_breadcrumb,
    render_page_header,
    render_timeline,
)
from app.utils import get_expiry_date, is_medicine_valid, new_tracking_id


STEPS = ["Profile", "Medicine", "Pickup", "Review & submit"]


def _save_draft(**fields) -> None:
    st.session_state.donor_draft = {**st.session_state.get("donor_draft", {}), **fields}


def _render_profile_step() -> None:
    st.markdown("#### Step 1 — Your profile")
    d = st.session_state.donor_draft
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Full name *", value=d.get("name", ""), key="p_name")
        email = st.text_input("Email *", value=d.get("email", ""), key="p_email")
    with c2:
        phone = st.text_input("Phone *", value=d.get("phone", ""), key="p_phone")
        city = st.text_input("City *", value=d.get("city", ""), key="p_city")
    locality = st.text_input("Locality *", value=d.get("locality", ""), key="p_loc")
    if st.button("Save & continue →", type="primary", use_container_width=True):
        if not all([name, email, phone, city, locality]):
            st.error("Please fill all fields.")
        else:
            _save_draft(name=name, email=email, phone=phone, city=city, locality=locality)
            st.session_state.user_role = "donor"
            st.session_state.donor_profile = {
                "name": name, "email": email, "phone": phone, "city": city, "locality": locality,
            }
            st.session_state.donor_step = 1
            st.rerun()


def _render_medicine_step() -> None:
    st.markdown("#### Step 2 — Medicine details")
    if st.session_state.pop("_ocr_prefill", False):
        st.success("Fields pre-filled from label scan — please verify before continuing.")

    d = st.session_state.donor_draft
    use_common = st.checkbox("Pick from common medicines", value=bool(d.get("from_common")))
    if use_common:
        picked = st.selectbox("Common medicine", [""] + COMMON_MEDICINES, key="common_med_pick")
        if picked:
            d["medicine"] = picked
    c1, c2 = st.columns(2)
    with c1:
        medicine = st.text_input("Medicine name *", value=d.get("medicine", ""))
        quantity = st.number_input("Quantity", 1, 10000, int(d.get("quantity", 1)))
    with c2:
        type_idx = MEDICINE_TYPES.index(d["medicine_type"]) if d.get("medicine_type") in MEDICINE_TYPES else 0
        medicine_type = st.selectbox("Type", MEDICINE_TYPES, index=type_idx)
        default_mfg = d.get("mfg_date", date.today())
        if isinstance(default_mfg, str):
            try:
                default_mfg = date.fromisoformat(default_mfg[:10])
            except ValueError:
                default_mfg = date.today()
        mfg_date = st.date_input("Manufacturing date", value=default_mfg, max_value=date.today())
    if d.get("batch_number"):
        st.caption(f"Batch (from scan): `{d['batch_number']}`")
    prescription = st.checkbox("Prescription required?", value=d.get("prescription_required", False))

    with st.expander("📷 Scan label with OCR (auto-fill)", expanded=False):
        st.caption(
            "Take a clear photo of the medicine strip or box. "
            + ("OCR ready." if ocr_available() else "Install rapidocr-onnxruntime for OCR.")
        )
        ocr_photo = st.file_uploader("Label photo for OCR", type=["jpg", "jpeg", "png"], key="donor_ocr_photo")
        if ocr_photo and st.button("Scan & fill fields", key="donor_ocr_scan"):
            with st.spinner("Reading label…"):
                parsed, err = scan_medicine_image(ocr_photo.getvalue())
            if err:
                st.error(err)
            else:
                if parsed.get("medicine"):
                    medicine = parsed["medicine"]
                if parsed.get("medicine_type") in MEDICINE_TYPES:
                    medicine_type = parsed["medicine_type"]
                if parsed.get("quantity"):
                    quantity = int(parsed["quantity"])
                if parsed.get("manufacturing_date"):
                    mfg_date = parsed["manufacturing_date"]
                _save_draft(
                    medicine=medicine,
                    medicine_type=medicine_type,
                    quantity=quantity,
                    mfg_date=mfg_date,
                    batch_number=parsed.get("batch_number"),
                    ocr_category=parsed.get("category"),
                    prescription_required=parsed.get("prescription_required", False),
                )
                st.session_state._donor_photo = ocr_photo
                st.session_state.last_ocr_scan = parsed
                st.toast("Label scanned — verify the fields above", icon="📷")
                st.rerun()

        if st.session_state.get("last_ocr_scan"):
            render_ocr_scan_result(st.session_state.last_ocr_scan, show_metrics=False)

    photo = st.file_uploader("Medicine photo (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if mfg_date and medicine_type:
        if is_medicine_valid(mfg_date, medicine_type):
            st.success(f"Valid until {get_expiry_date(mfg_date, medicine_type)}")
        else:
            st.warning("Near expiry or expired — may be rejected.")
    c1, c2 = st.columns(2)
    if c1.button("← Back"):
        st.session_state.donor_step = 0
        st.rerun()
    if c2.button("Continue →", type="primary"):
        _save_draft(
            medicine=medicine, medicine_type=medicine_type, quantity=quantity,
            mfg_date=mfg_date, prescription_required=prescription, photo_pending=photo is not None,
        )
        st.session_state._donor_photo = photo
        st.session_state.donor_step = 2
        st.rerun()


def _render_pickup_step() -> None:
    st.markdown("#### Step 3 — Pickup details")
    d = st.session_state.donor_draft
    pincode = st.text_input("Pincode *", value=d.get("pincode", ""))
    address = st.text_area("Pickup address *", value=d.get("pickup_address", ""))
    pickup_time = st.time_input("Preferred pickup time", value=time(10, 0))
    c1, c2 = st.columns(2)
    if c1.button("← Back"):
        st.session_state.donor_step = 1
        st.rerun()
    if c2.button("Preview matches →", type="primary"):
        _save_draft(pincode=pincode, pickup_address=address, pickup_time=str(pickup_time))
        st.session_state.donor_step = 3
        st.rerun()


def _render_review_and_submit() -> None:
    st.markdown("#### Step 4 — Review & nearby NGOs")
    d = st.session_state.donor_draft
    st.json({k: str(v) for k, v in d.items() if k != "photo_pending"}, expanded=False)

    mfg = d.get("mfg_date", date.today())
    preview = {
        "name": d.get("name"), "email": d.get("email"), "phone": d.get("phone"),
        "medicine": d.get("medicine"), "medicine_type": d.get("medicine_type", "Tablet"),
        "quantity": d.get("quantity", 1), "manufacturing_date": mfg,
        "city": d.get("city"), "locality": d.get("locality"),
        "pincode": d.get("pincode") or "400001",
    }
    try:
        model, err = validate_donor(preview)
    except Exception:
        model, err = None, "Validation failed"

    matches = []
    if model and not err:
        fake_donor = {**preview, "id": 0, "category": model.category()}
        matches = find_matches_for_donor(fake_donor, persist=False)

    email = d.get("email")
    if email and d.get("medicine"):
        dup = donor_repo.find_recent_similar_donation(email, d["medicine"])
        if dup:
            st.warning(
                f"You donated **{dup.get('medicine')}** recently "
                f"(`{dup.get('tracking_id')}`). Submit again only if this is a new batch."
            )

    if matches:
        st.success(f"**{len(matches)}** NGO(s) likely to match in your area")
        for m in matches[:5]:
            ngo = m["ngo"]
            st.markdown(
                f'<div class="glass-card"><b>{ngo["name"]}</b> — {ngo["city"]}<br>'
                f'{confidence_badge(m["confidence_score"], m["match_type"])}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No NGOs matched yet — your donation will be visible when NGOs register nearby.")

    c1, c2 = st.columns(2)
    if c1.button("← Back"):
        st.session_state.donor_step = 2
        st.rerun()
    if c2.button("✅ Submit donation", type="primary"):
        if err:
            st.error(err)
            return
        if not is_medicine_valid(d.get("mfg_date", date.today()), d.get("medicine_type", "Tablet")):
            st.error("Cannot submit expired medicine.")
            return
        with st.spinner("Submitting…"):
            photo = st.session_state.get("_donor_photo")
            photo_path, upload_err = save_medicine_image(photo)
            if upload_err:
                st.error(upload_err)
                return
            tid = new_tracking_id()
            donor_id = donor_repo.create_donor({
                "name": model.name,
                "email": str(model.email),
                "phone": model.phone,
                "medicine": model.medicine,
                "medicine_type": model.medicine_type,
                "quantity": model.quantity,
                "manufacturing_date": model.manufacturing_date,
                "city": model.city,
                "locality": model.locality,
                "pincode": model.pincode,
                "category": model.category(),
                "medicine_photo": photo_path,
                "tracking_id": tid,
                "pickup_address": d.get("pickup_address"),
                "pickup_time": d.get("pickup_time"),
                "prescription_required": d.get("prescription_required"),
            })
            donor = donor_repo.get_donor(donor_id)
            find_matches_for_donor(donor)
            notify(
                str(model.email),
                "Donation submitted",
                f"Tracking ID {tid}. We are matching NGOs near {model.city}.",
                "success",
            )
        st.session_state.last_donation = donor
        st.session_state.donor_draft = {}
        st.session_state.donor_step = 5
        st.balloons()
        st.rerun()


def _render_success() -> None:
    d = st.session_state.get("last_donation") or {}
    tid = d.get("tracking_id", "—")
    st.success("Donation submitted successfully!")
    st.markdown(f"### Tracking ID: `{tid}`")

    c1, c2 = st.columns([1, 2])
    with c1:
        qr = generate_qr_png(tid)
        if qr:
            st.image(qr, caption="Scan to track (demo)", width=200)
        else:
            st.caption("Install `qrcode` for tracking QR")
    with c2:
        render_timeline(d.get("status", "available"))
        top = match_repo.get_matches_with_details()
        mine = [m for m in top if m.get("donor_id") == d.get("id")][:1]
        if mine:
            st.info(f"Assigned NGO: **{mine[0].get('ngo_name')}**")

    receipt = generate_receipt_text(d)
    st.download_button(
        "📄 Download receipt",
        receipt,
        file_name=f"receipt-{tid}.txt",
        mime="text/plain",
        use_container_width=True,
    )
    if st.button("Go to my dashboard"):
        st.session_state.donor_step = 0
        st.rerun()


def _render_dashboard() -> None:
    email = st.session_state.donor_profile.get("email")
    donations = donor_repo.get_by_email(email) if email else []
    active = [x for x in donations if x.get("status") not in ("completed", "expired")]
    history = [x for x in donations if x.get("status") in ("completed", "expired")]

    t1, t2, t3 = st.tabs(["Active", "History", "Notifications"])
    with t1:
        if not active:
            empty_state("📭", "No active donations", "Submit a new donation to get started.")
        for d in active:
            with st.container(border=True):
                st.markdown(f"**{d.get('medicine')}** · `{d.get('tracking_id', '')}`")
                st.markdown(donor_status_pill(d.get("status", "available")), unsafe_allow_html=True)
                render_timeline(d.get("status", "available"))
                st.download_button(
                    "Receipt",
                    generate_receipt_text(d),
                    file_name=f"receipt-{d.get('tracking_id', 'donation')}.txt",
                    key=f"rcpt_{d.get('id')}",
                )
    with t2:
        for d in history:
            st.caption(f"{d.get('medicine')} — {d.get('status')} — {d.get('created_at', '')[:10]}")
    with t3:
        st.caption("Open **Notifications** in the sidebar for full inbox.")


def render() -> None:
    render_page_header(
        "Donate Medicines",
        "Guided donation flow — profile, medicine, pickup, and tracking",
        "💊",
    )
    render_breadcrumb("Home", "Donor")

    if st.session_state.get("donor_step") == 5:
        _render_success()
        return

    tab_new, tab_dash = st.tabs(["New donation", "My dashboard"])

    with tab_new:
        step = st.session_state.get("donor_step", 0)
        st.progress((step + 1) / len(STEPS), text=f"Step {min(step + 1, len(STEPS))} of {len(STEPS)}: {STEPS[min(step, len(STEPS)-1)]}")
        if step == 0:
            _render_profile_step()
        elif step == 1:
            _render_medicine_step()
        elif step == 2:
            _render_pickup_step()
        elif step == 3:
            _render_review_and_submit()

    with tab_dash:
        if st.session_state.get("user_role") != "donor":
            st.info("Complete **Step 1 — Profile** in New donation to unlock your dashboard.")
        else:
            _render_dashboard()
