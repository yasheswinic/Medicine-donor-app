# MedDonate — Medicine Donation & NGO Matching

**100% free demo** — Streamlit + SQLite + fuzzy matching. No paid map, OCR, or auth APIs. No email/SMS.

Connect medicine donors with nearby NGOs using validation, in-app notifications, OCR label scanning, and live maps powered by OpenStreetMap.

---

## Features

### Public site (donors & NGOs)

| Area                 | What it does                                                                |
| -------------------- | --------------------------------------------------------------------------- |
| **Home**             | Quick links to donate, NGO register, dashboard, label scan, map             |
| **Donate Medicines** | 4-step flow: profile → medicine → pickup → review & submit                  |
| **Scan & Tools**     | OCR label reader (RapidOCR) + medicine safety checker (blocked substances)  |
| **NGO Portal**       | Register NGO, view incoming donations, accept / schedule / reject           |
| **Dashboard**        | Match cards, KPIs, charts, CSV export, map & analytics tabs                 |
| **Map**              | **India overview** (donors/NGOs by city) + **Live nearby** (GPS or pincode) |
| **Notifications**    | In-app inbox per email (no SMTP)                                            |
| **Help & FAQ**       | Usage notes for OCR, maps, admin, receipts                                  |

### Donation flow extras

- Fuzzy NGO matching (`thefuzz`) by city, locality, medicine, category
- Optional medicine photo upload (local `app/uploads/`)
- **OCR auto-fill** from strip/box photos (name, strength, batch, dates, Schedule H)
- **Structured JSON** OCR report + download
- **Tracking ID**, **QR code**, **text receipt** download
- Duplicate-donation warning (same medicine within 7 days)
- Common medicine picker + expiry validation from manufacturing date

### Map & location (free)

- **Live GPS** via browser geolocation
- **Pincode lookup** via OpenStreetMap Nominatim
- **Real nearby shops** — pharmacies, hospitals, clinics from Overpass API
- **Nearby app data** — donations & NGOs in radius with distance (km)
- India city overview map (Folium + OSM tiles)

### Admin portal (staff only)

Separate from the public app — no shared sidebar with donors/NGOs.

- First-run admin account creation (bcrypt in SQLite)
- Demo login from `.env`: `admin` / `admin123`
- Metrics, donor/NGO/match tables, CSV export, status pipeline

---

## Tech stack (all free)

| Layer                  | Technology                                   |
| ---------------------- | -------------------------------------------- |
| UI                     | Streamlit                                    |
| Database               | SQLite (`data.db`)                           |
| Validation             | Pydantic v2                                  |
| Matching               | thefuzz + python-Levenshtein                 |
| Auth (admin)           | bcrypt                                       |
| Maps                   | Folium, streamlit-folium, OpenStreetMap      |
| Geocoding / nearby POI | Nominatim + Overpass API                     |
| OCR                    | RapidOCR (on-device, `rapidocr-onnxruntime`) |
| QR receipts            | qrcode + Pillow                              |
| Charts                 | Plotly, matplotlib, pandas                   |

---

## Requirements

- Python **3.10+** (tested on 3.13; use `rapidocr-onnxruntime>=1.2.3,<1.3` on 3.13)
- Internet for first OCR model download (~10MB) and live map geocoding

---

## Quick start

```bash
cd med-donation-app
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
streamlit run app/main.py
```

Open the URL shown (usually `http://localhost:8501`).

### First launch

1. Choose **Public site** (donors & NGOs) or **Admin portal** (staff).
2. Public users: use sidebar to navigate.
3. Admin: sign in with `admin` / `admin123` (from `.env`) or create an account on first visit.

### Optional: admin-only entry

```bash
streamlit run app/admin_main.py
```

Skips the portal chooser and opens admin directly.

---

## Configuration (`.env`)

| Variable         | Default       | Purpose                  |
| ---------------- | ------------- | ------------------------ |
| `DB_PATH`        | `./data.db`   | SQLite database file     |
| `APP_ENV`        | `development` | Environment label        |
| `ADMIN_USERNAME` | `admin`       | Bootstrap admin username |
| `ADMIN_PASSWORD` | `admin123`    | Bootstrap admin password |

Change admin credentials before any public deployment.

---

## Project structure

```text
med-donation-app/
├── app/
│   ├── main.py              # Public + portal router
│   ├── admin_main.py        # Admin-only entry
│   ├── config.py            # Settings from .env
│   ├── db.py                # Schema + migrations
│   ├── models.py            # Pydantic models
│   ├── constants.py         # Statuses, blocked medicines, etc.
│   ├── utils.py             # Logging, safety, expiry helpers
│   ├── ui.py                # Sidebars, nav, shared UI
│   ├── ui_ocr.py            # OCR JSON display helper
│   ├── assets/styles.css
│   ├── components/
│   │   └── geolocation.py   # Browser GPS component
│   ├── views/
│   │   ├── portal.py        # Public vs admin chooser
│   │   ├── home.py
│   │   ├── donor.py
│   │   ├── ngo.py
│   │   ├── dashboard.py
│   │   ├── map_view.py      # Overview + live nearby
│   │   ├── tools.py         # OCR + safety checker
│   │   ├── notifications.py
│   │   ├── help.py
│   │   └── admin.py
│   ├── services/
│   │   ├── matching_service.py
│   │   ├── validation_service.py
│   │   ├── upload_service.py
│   │   ├── search_service.py
│   │   ├── map_service.py
│   │   ├── location_service.py   # GPS, geocode, Overpass
│   │   ├── ocr_service.py
│   │   ├── receipt_service.py
│   │   └── auth_service.py
│   ├── repositories/
│   │   ├── donor_repo.py
│   │   ├── ngo_repo.py
│   │   ├── match_repo.py
│   │   └── notification_repo.py
│   └── uploads/             # Local medicine photos
├── tests/                   # pytest (33 tests)
├── logs/                    # app.log (rotating)
├── requirements.txt
├── .env.example
└── .streamlit/config.toml
```

---

## Usage tips

### OCR label scan

1. Go to **Scan & Tools** or **Donate → Step 2 → Scan label**.
2. Upload a clear photo of the medicine strip/box.
3. Review **Structured OCR result (JSON)** and metrics.
4. Use **Use in donation form** to copy fields.

### Live nearby map

1. Go to **Map → Live nearby**.
2. Click **Use my live location** (allow browser permission) **or** enter a 6-digit pincode.
3. Adjust **search radius**; view pharmacies/clinics (OSM) and app donors/NGOs.

### Medicine safety checker

**Scan & Tools → Safety checker** — blocks illegal/withdrawn substances (e.g. heroin, thalidomide). Not medical advice; demo list only.

### Donation statuses

`available` → `pending` → `claimed` → `picked_up` → `completed` (or `expired`)

---

## Tests

```bash
pytest -v
```

Covers validation, matching, DB migration, OCR parsing, geolocation math, and utilities.

---

## Deploy free (Streamlit Cloud)

1. Push the repo to GitHub.
2. [share.streamlit.io](https://share.streamlit.io) → **New app**
3. **Main file path:** `app/main.py`
4. **Secrets** (optional): `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `DB_PATH`

**Limits:** SQLite and `app/uploads/` reset on redeploy — suitable for demos, not production persistence.

---

## Intentionally not included (demo scope)

- Email / SMS / push notifications
- Paid APIs (Google Maps, cloud OCR, Stripe, etc.)
- PostgreSQL / Redis / S3
- Real-time GPS tracking of delivery vehicles (only point-in-time user location + static OSM POIs)

---

## Troubleshooting

| Issue                                   | Fix                                                                                          |
| --------------------------------------- | -------------------------------------------------------------------------------------------- |
| OCR not loading                         | `pip install rapidocr-onnxruntime opencv-python-headless onnxruntime` then restart Streamlit |
| Map empty                               | Install `folium streamlit-folium`; use supported cities or **Live nearby** with GPS/pincode  |
| `rapidocr` install fails on Python 3.13 | Use `rapidocr-onnxruntime>=1.2.3,<1.3` as in `requirements.txt`                              |
| Live location denied                    | Allow location in browser; or use pincode instead                                            |
| No nearby shops                         | OSM data varies by area — try a larger radius or urban pincode                               |

---

## License

MIT
#   M e d i c i n e - d o n o r - a p p  
 