import streamlit as st
import sqlite3
from datetime import date, datetime

# ======================================================
# PAGE CONFIG
# ======================================================

st.set_page_config(
    page_title="Medicine Donation System",
    page_icon="💊",
    layout="wide"
)

# ======================================================
# MODERN CLEAN CSS
# ======================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
    color: black !important;
}

/* BACKGROUND */

.stApp {
    background: linear-gradient(
        135deg,
        #f8fbff,
        #eef5ff,
        #ffffff
    );
}

/* TITLE */

.hero-title {
    text-align: center;
    font-size: 64px;
    font-weight: 800;
    color: #1565c0;
    margin-top: 10px;
}

/* SUBTITLE */

.hero-sub {
    text-align: center;
    font-size: 24px;
    font-weight: 700;
    color: black;
    margin-bottom: 25px;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: white !important;
    border-right: 2px solid #dbeafe;
}

[data-testid="stSidebar"] * {
    color: black !important;
    font-weight: 700 !important;
}

/* LABELS */

label {
    color: black !important;
    font-weight: 700 !important;
    font-size: 16px !important;
}

/* INPUT BOXES */

.stTextInput input,
.stDateInput input,
textarea {

    background-color: white !important;
    color: black !important;

    border-radius: 14px !important;
    border: 2px solid #cbd5e1 !important;

    padding: 14px !important;

    font-size: 16px !important;
    font-weight: 600 !important;
}

/* SELECT BOX */

div[data-baseweb="select"] {

    background: white !important;

    border-radius: 14px !important;

    border: 2px solid #cbd5e1 !important;

    min-height: 54px !important;

    display: flex !important;

    align-items: center !important;
}

/* SELECT TEXT */

div[data-baseweb="select"] span {

    color: black !important;

    font-size: 16px !important;

    font-weight: 700 !important;
}

/* BUTTON */

.stButton > button {

    width: 100%;

    border-radius: 14px;

    background: linear-gradient(
        90deg,
        #4facfe,
        #00c6fb
    );

    color: white !important;

    font-size: 18px;

    font-weight: 700;

    border: none;

    padding: 15px;

    transition: 0.3s;

    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
}

.stButton > button:hover {

    transform: scale(1.02);

    background: linear-gradient(
        90deg,
        #43e97b,
        #38f9d7
    );
}

/* METRIC CARDS */

[data-testid="metric-container"] {

    background: white !important;

    border-radius: 18px !important;

    padding: 20px !important;

    border: 2px solid #dbeafe !important;

    box-shadow: 0 5px 20px rgba(0,0,0,0.08) !important;
}

/* METRIC LABEL */

[data-testid="metric-container"] label {

    color: black !important;

    font-size: 20px !important;

    font-weight: 800 !important;
}

/* METRIC NUMBER */

[data-testid="stMetricValue"] {

    color: #1565c0 !important;

    font-size: 42px !important;

    font-weight: 900 !important;
}

/* INFO BOX */

div[data-testid="stInfo"] {

    background: #dbeafe !important;

    border-radius: 16px !important;

    padding: 18px !important;
}

div[data-testid="stInfo"] * {

    color: black !important;

    font-size: 18px !important;

    font-weight: 700 !important;
}

/* SUCCESS BOX */

div[data-testid="stSuccess"] {

    background: #dcfce7 !important;

    border-radius: 16px !important;

    padding: 18px !important;
}

div[data-testid="stSuccess"] * {

    color: black !important;

    font-size: 18px !important;

    font-weight: 700 !important;
}

/* WARNING BOX */

div[data-testid="stWarning"] {

    background-color: white !important;

    border: 3px solid red !important;

    border-left: 10px solid red !important;

    border-radius: 18px !important;

    padding: 20px !important;

    margin-top: 10px !important;
}

/* WARNING TEXT */
div[data-testid="stWarning"],
div[data-testid="stWarning"] *,
div[data-testid="stWarning"] p,
div[data-testid="stWarning"] span,
div[data-testid="stWarning"] div {

    color: red !important;

    font-size: 22px !important;

    font-weight: 900 !important;

    line-height: 1.8 !important;
}

/* HEADINGS */

h1,h2,h3,h4,h5,h6 {
    color: black !important;
    font-weight: 800 !important;
}

/* BLOCK SPACING */

.block-container {
    padding-top: 2rem;
    padding-left: 4rem;
    padding-right: 4rem;
}

/* FOOTER */

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)

# ======================================================
# DATABASE
# ======================================================

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

# ======================================================
# VALIDATION
# ======================================================

def is_valid(mfg_date, mtype):

    try:

        mfg = datetime.strptime(
            str(mfg_date),
            "%Y-%m-%d"
        )

        limit = 365 if mtype == "Tablet" else 180

        return (
            datetime.now() - mfg
        ).days <= limit

    except:
        return False

# ======================================================
# HEADER
# ======================================================

st.markdown("""
<div class="hero-title">
💊 Medicine Donation System
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-sub">
🌍 Donate Medicines • Save Lives • Connect NGOs
</div>
""", unsafe_allow_html=True)

st.info("""
🚀 Smart healthcare platform for real-time donor and NGO medicine matching.
""")

# ======================================================
# SIDEBAR
# ======================================================

menu = st.sidebar.radio(
    "📌 Navigation",
    [
        "🏠 Home",
        "👤 Donor Panel",
        "🏥 NGO Panel",
        "🔍 Matching Dashboard"
    ]
)

# ======================================================
# HOME PAGE
# ======================================================

if menu == "🏠 Home":

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM donors")
    donors = cur.fetchall()

    cur.execute("SELECT * FROM ngos")
    ngos = cur.fetchall()

    matches = 0

    for donor in donors:

        for ngo in ngos:

            if (
                donor[7].strip().lower()
                ==
                ngo[2].strip().lower()

                and

                donor[8].strip().lower()
                ==
                ngo[3].strip().lower()
            ):

                matches += 1

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "👤 Total Donors",
            len(donors)
        )

    with col2:
        st.metric(
            "🏥 Total NGOs",
            len(ngos)
        )

    with col3:
        st.metric(
            "🤝 Total Matches",
            matches
        )

    st.markdown("---")

    st.success("""
✅ Real-time donor and NGO matching

✅ Medicine expiry validation

✅ Nearby locality-based matching

✅ Live healthcare donation platform
""")

# ======================================================
# DONOR PANEL
# ======================================================

elif menu == "👤 Donor Panel":

    st.subheader("👤 Donor Registration")

    st.warning("""
⚠ TABLETS ARE VALID FOR 365 DAYS

⚠ SYRUPS ARE VALID FOR 180 DAYS
""")

    col1, col2 = st.columns(2)

    with col1:

        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        medicine = st.text_input("Medicine Name")

    with col2:

        mtype = st.selectbox(
            "Medicine Type",
            ["Tablet", "Syrup"]
        )

        mfg_date = st.date_input(
            "Manufacturing Date",
            value=date.today()
        )

        city = st.text_input("City")
        locality = st.text_input("Locality")
        pincode = st.text_input("Pincode")

    if st.button("🚀 Submit Donor"):

        if not is_valid(mfg_date, mtype):

            st.error("❌ Medicine expired")

        else:

            conn = get_conn()
            cur = conn.cursor()

            cur.execute("""
            INSERT INTO donors
            VALUES (
            NULL,?,?,?,?,?,?,?,?,?
            )
            """, (
                name,
                email,
                phone,
                medicine,
                mtype,
                str(mfg_date),
                city,
                locality,
                pincode
            ))

            conn.commit()
            conn.close()

            st.balloons()

            st.success("""
✅ Donor Registered Successfully

🏥 Nearby NGOs can now connect.
""")

# ======================================================
# NGO PANEL
# ======================================================

elif menu == "🏥 NGO Panel":

    st.subheader("🏥 NGO Registration")

    col1, col2 = st.columns(2)

    with col1:

        ngo_name = st.text_input("NGO Name")
        city = st.text_input("City")

    with col2:

        locality = st.text_input("Locality")
        medicines = st.text_input("Accepted Medicines")
        pincode = st.text_input("Pincode")

    if st.button("🚀 Submit NGO"):

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO ngos
        VALUES (
        NULL,?,?,?,?,?
        )
        """, (
            ngo_name,
            city,
            locality,
            medicines,
            pincode
        ))

        conn.commit()
        conn.close()

        st.snow()

        st.success("""
✅ NGO Registered Successfully

📍 Nearby donors can now connect.
""")

# ======================================================
# MATCHING DASHBOARD
# ======================================================

elif menu == "🔍 Matching Dashboard":

    st.subheader(
        "🔍 Real-Time NGO Matching Dashboard"
    )

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM donors")
    donors = cur.fetchall()

    cur.execute("SELECT * FROM ngos")
    ngos = cur.fetchall()

    st.caption(
        f"⏱ Last Updated: "
        f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
    )

    matches_count = 0

    for donor in donors:

        donor_city = donor[7].strip().lower()
        donor_locality = donor[8].strip().lower()

        for ngo in ngos:

            ngo_city = ngo[2].strip().lower()
            ngo_locality = ngo[3].strip().lower()

            if (
                donor_city == ngo_city
                and donor_locality == ngo_locality
            ):

                matches_count += 1

                st.success(f"""

🏥 NGO: {ngo[1]}

📍 Location:
{ngo[3]}, {ngo[2]}

💊 Accepts:
{ngo[4]}

-----------------------------------

👤 Donor:
{donor[1]}

💊 Medicine:
{donor[4]} ({donor[5]})

📍 Donor Location:
{donor[8]}, {donor[7]}

📞 Contact:
{donor[3]}

📧 Email:
{donor[2]}
""")

    if matches_count == 0:

        st.warning(
            "No nearby matches found."
        )

    st.metric(
        "🤝 Total Live Matches",
        matches_count
    )

    conn.close()

# ======================================================
# FOOTER
# ======================================================

st.markdown("---")

st.markdown("""
<center>

💙 Final Year Major Project

Medicine Donation System

</center>
""", unsafe_allow_html=True)