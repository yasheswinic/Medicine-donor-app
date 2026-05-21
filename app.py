import streamlit as st
import sqlite3
from datetime import date, datetime

# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="Medicine Donation System", layout="wide")

st.markdown("""
<style>
    .main {
        background-color: #f5f7fb;
    }

    h1 {
        text-align: center;
        color: #2b6cb0;
        font-size: 40px;
        font-weight: 800;
    }

    .stButton>button {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 8px 16px;
        border: none;
        transition: 0.3s;
    }

    .stButton>button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #43e97b, #38f9d7);
    }

    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
DB = "data.db"

def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS donors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        medicine TEXT,
        type TEXT,
        mfg_date TEXT,
        city TEXT,
        locality TEXT,
        pincode TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ngos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        city TEXT,
        locality TEXT,
        medicines TEXT,
        pincode TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIC ----------------
def is_valid(mfg_date, mtype):
    try:
        mfg = datetime.strptime(str(mfg_date), "%Y-%m-%d")
        limit = 365 if mtype == "Tablet" else 180
        return (datetime.now() - mfg).days <= limit
    except:
        return False

def is_near(donor_city, ngo_city, donor_pin, ngo_pin):
    if donor_city.lower() == ngo_city.lower():
        return True
    if donor_pin and ngo_pin:
        return donor_pin[:2] == ngo_pin[:2]
    return False

# ---------------- TITLE ----------------
st.markdown("<h1>💊 Medicine Donation System</h1>", unsafe_allow_html=True)
st.markdown("### 🌍 Donate medicines • Save lives • Connect NGOs")

menu = st.sidebar.radio("Navigation", ["Donor Panel", "NGO Panel", "Matching Dashboard"])

# ---------------- DONOR PANEL ----------------
if menu == "Donor Panel":
    st.subheader("👤 Donor Registration")

    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")

    medicine = st.text_input("Medicine Name")
    mtype = st.selectbox("Medicine Type", ["Tablet", "Syrup"])
    mfg_date = st.date_input("Manufacturing Date", value=date.today())

    city = st.text_input("City")
    locality = st.text_input("Locality")
    pincode = st.text_input("Pincode")

    if st.button("Submit Donor"):
        if not is_valid(mfg_date, mtype):
            st.error("❌ Medicine expired or not valid for donation")
        else:
            conn = get_conn()
            cur = conn.cursor()

            cur.execute("""
            INSERT INTO donors (name,email,phone,medicine,type,mfg_date,city,locality,pincode)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, (name,email,phone,medicine,mtype,str(mfg_date),city,locality,pincode))

            conn.commit()
            conn.close()

            st.success("✅ Donor registered successfully")

# ---------------- NGO PANEL ----------------
elif menu == "NGO Panel":
    st.subheader("🏥 NGO Registration")

    name = st.text_input("NGO Name")
    city = st.text_input("City")
    locality = st.text_input("Locality")
    medicines = st.text_input("Accepted Medicines")
    pincode = st.text_input("Pincode")

    if st.button("Submit NGO"):
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO ngos (name,city,locality,medicines,pincode)
        VALUES (?,?,?,?,?)
        """, (name,city,locality,medicines,pincode))

        conn.commit()
        conn.close()

        st.success("✅ NGO registered successfully")

# ---------------- MATCHING ----------------
elif menu == "Matching Dashboard":
    st.subheader("🔍 Nearby NGO Matching System")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM donors")
    donors = cur.fetchall()

    cur.execute("SELECT * FROM ngos")
    ngos = cur.fetchall()

    st.markdown(f"### 👤 Donors: {len(donors)} | 🏥 NGOs: {len(ngos)}")

    st.markdown("## 🏥 Matched NGOs & Donors")

    match_count = 0

    for ngo in ngos:
        for donor in donors:

            if is_near(donor[7], ngo[1], donor[8], ngo[4]):
                match_count += 1

                st.success(f"""
🏥 NGO: {ngo[1]}
📍 {ngo[2]} | {ngo[3]}
💊 Accepts: {ngo[3]}

👤 Donor: {donor[1]}
💊 Medicine: {donor[4]} ({donor[5]})
📍 {donor[7]} | {donor[8]}
""")

    if match_count == 0:
        st.warning("No matches found yet. Add donors and NGOs.")