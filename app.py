import streamlit as st
from datetime import date

st.set_page_config(page_title="Medicine Donation System", layout="wide")

# ---------------- UI STYLE ----------------
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0f172a, #1e293b, #0f172a);
        color: white;
    }

    h1 {
        text-align: center;
        color: #00ffd5;
        font-size: 40px;
        text-shadow: 0px 0px 20px #00ffd5;
    }

    .card {
        background: rgba(255, 255, 255, 0.08);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 0 20px rgba(0,255,213,0.2);
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- DATA STORAGE ----------------
if "donors" not in st.session_state:
    st.session_state.donors = []

if "ngos" not in st.session_state:
    st.session_state.ngos = []

# ---------------- TITLE ----------------
st.title("💊 Medicine Donation & NGO Matching System")
st.markdown("🩺 💉 🏥 🚑 💊 🌿 💖")

# ---------------- MENU ----------------
menu = st.sidebar.radio("Navigation", ["Home", "Donor Panel", "NGO Panel", "Match System"])

# ---------------- HOME ----------------
if menu == "Home":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Welcome 🚀")
    st.write("Donate medicines and connect donors with nearby NGOs instantly")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- DONOR ----------------
elif menu == "Donor Panel":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Donor Registration")

    name = st.text_input("Donor Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")

    medicine = st.text_input("Medicine Name")
    mtype = st.selectbox("Medicine Type", ["Tablet (365 days expiry)", "Syrup (180 days expiry)"])

    mfg_date = st.date_input("Manufacturing Date", value=date.today())

    city = st.text_input("City")
    locality = st.text_input("Locality")
    pincode = st.text_input("Pincode")

    if st.button("Submit Donor"):
        st.session_state.donors.append({
            "name": name,
            "email": email,
            "phone": phone,
            "medicine": medicine,
            "type": mtype,
            "mfg_date": str(mfg_date),
            "city": city,
            "locality": locality,
            "pincode": pincode
        })
        st.success("Donor Registered Successfully ✅")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- NGO ----------------
elif menu == "NGO Panel":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("NGO Registration")

    ngo_name = st.text_input("NGO Name")
    city = st.text_input("City")
    locality = st.text_input("Locality")
    medicines = st.text_input("Accepted Medicines (comma separated)")

    if st.button("Submit NGO"):
        st.session_state.ngos.append({
            "ngo_name": ngo_name,
            "city": city,
            "locality": locality,
            "medicines": medicines.lower()
        })
        st.success("NGO Registered Successfully ✅")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- MATCH SYSTEM ----------------
elif menu == "Match System":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Find Nearby NGOs")

    search_city = st.text_input("Enter City")

    if st.button("Search NGOs"):
        results = [
            ngo for ngo in st.session_state.ngos
            if ngo["city"].lower() == search_city.lower()
        ]

        st.markdown(f"### Found {len(results)} NGOs")

        if not results:
            st.warning("No NGOs found in this city")

        for ngo in results:
            st.success(f"""
🏥 NGO: {ngo['ngo_name']}
📍 City: {ngo['city']}
📌 Locality: {ngo['locality']}
💊 Medicines Accepted: {ngo['medicines']}
""")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Live Donor List")

    for donor in st.session_state.donors:
        st.info(f"""
👤 {donor['name']} | {donor['city']}
💊 {donor['medicine']} ({donor['type']})
📅 MFG: {donor['mfg_date']}
""")