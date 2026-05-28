# 💊 MedDonate — Medicine Donation & NGO Matching Platform

A free and open-source medicine donation platform that connects donors with nearby NGOs using OCR label scanning, fuzzy matching, live maps, and admin analytics.

Built entirely with free technologies using Streamlit + SQLite.

---

# 📌 Overview

MedDonate helps reduce medicine wastage by enabling users to donate unused medicines to NGOs and healthcare organizations.

The platform includes:
- Medicine donation workflow
- NGO management portal
- OCR medicine label scanning
- Nearby NGO & pharmacy discovery
- Donation tracking
- Admin dashboard & analytics
- In-app notifications
- QR-based receipts

---

# ✨ Features

## 🏠 Public Portal

### Home
- Central navigation hub
- Quick access to all modules
- Clean and responsive UI

### Donate Medicines
4-step donation workflow:
1. Donor Details
2. Medicine Information
3. Pickup Information
4. Review & Submit

Includes:
- Expiry validation
- Duplicate donation detection
- Medicine category selection
- Tracking ID generation
- QR receipt generation

---

## 🔍 OCR Label Scanner

Upload medicine strip/box images to:
- Extract medicine name
- Detect strength/dosage
- Detect batch number
- Detect expiry/manufacturing dates
- Identify Schedule H medicines
- Auto-fill donation forms

### OCR Stack
- RapidOCR
- ONNX Runtime
- OpenCV

---

## 🗺️ Maps & Nearby Discovery

### Features
- India overview map
- Live nearby mode
- Browser GPS support
- Pincode geolocation
- Nearby pharmacies & clinics
- Nearby NGOs and donors

### Powered By
- OpenStreetMap
- Folium
- Nominatim API
- Overpass API

---

## 🏢 NGO Portal

NGOs can:
- Register organization
- View incoming donations
- Accept/reject donations
- Schedule pickups
- Manage donation pipeline

---

## 📊 Dashboard & Analytics

Includes:
- Donation KPIs
- NGO statistics
- Match analytics
- Charts & graphs
- CSV export
- Location analytics

Libraries:
- Plotly
- matplotlib
- pandas

---

## 🔔 Notifications

In-app notification system:
- No email/SMS dependency
- Inbox-based notifications
- Donation status updates
- NGO communication alerts

---

## 🔐 Admin Portal

Separate admin interface with:
- Secure login
- bcrypt password hashing
- Metrics dashboard
- CSV exports
- Donation management
- NGO management
- Match pipeline tracking

---

# 🧠 Core Functionalities

## Fuzzy NGO Matching

Uses:
- `thefuzz`
- `python-Levenshtein`

Matching factors:
- City
- Locality
- Medicine category
- Donation relevance

---

## Medicine Safety Checker

Blocks unsafe/illegal medicines such as:
- Heroin
- Thalidomide
- Restricted substances

> Demo safety validation only — not medical advice.

---

## Donation Status Pipeline

```text
available
   ↓
pending
   ↓
claimed
   ↓
picked_up
   ↓
completed
```

Expired donations are automatically flagged.

---

# 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Database | SQLite |
| Validation | Pydantic v2 |
| OCR | RapidOCR |
| Matching | thefuzz + Levenshtein |
| Maps | Folium + OpenStreetMap |
| Authentication | bcrypt |
| Charts | Plotly + matplotlib |
| QR Generation | qrcode + Pillow |
| Testing | pytest |

---

# 📂 Project Structure

```text
med-donation-app/
├── app/
│   ├── main.py
│   ├── admin_main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── constants.py
│   ├── utils.py
│   ├── ui.py
│   ├── ui_ocr.py
│   ├── assets/
│   ├── components/
│   ├── views/
│   ├── services/
│   ├── repositories/
│   └── uploads/
├── tests/
├── logs/
├── requirements.txt
├── .env.example
└── .streamlit/
```

---

# ⚙️ Installation

## Requirements

- Python 3.10+
- Internet connection (for OCR model download & live maps)

---

## Setup

```bash
git clone <repository-url>

cd med-donation-app

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS/Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

### Windows

```bash
copy .env.example .env
```

### macOS/Linux

```bash
cp .env.example .env
```

Run application:

```bash
streamlit run app/main.py
```

---

# 🚀 Running Admin Portal Only

```bash
streamlit run app/admin_main.py
```

---

# 🔧 Environment Variables

## `.env`

```env
DB_PATH=./data.db
APP_ENV=development

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

> Change admin credentials before deployment.

---

# 🧪 Running Tests

```bash
pytest -v
```

Covers:
- Validation testing
- OCR parsing tests
- Matching logic
- DB migration tests
- Utility tests
- Geolocation calculations

---

# 🌐 Deployment

## Streamlit Cloud

1. Push project to GitHub
2. Open Streamlit Cloud
3. Create new app
4. Select:

```text
Main file path: app/main.py
```

Optional secrets:
```text
ADMIN_USERNAME
ADMIN_PASSWORD
DB_PATH
```

---

# ⚠️ Limitations

This is a demo-focused project.

Not included:
- Email/SMS notifications
- Payment gateway
- Real-time vehicle tracking
- Cloud storage
- PostgreSQL
- Production authentication
- Enterprise scalability

---

# 🔮 Future Scope

Possible enhancements:
- Mobile application
- AI medicine recommendation
- Barcode scanning
- PostgreSQL migration
- Cloud deployment
- OTP authentication
- NGO verification
- Multi-language OCR
- Real-time tracking
- Push notifications

---

# 🔐 Security & Validation

Implemented:
- Pydantic validation
- bcrypt password hashing
- Expiry checks
- Duplicate donation detection
- Blocked medicine detection
- Safe file upload handling

---

# 📊 Workflow

```text
Donor
   ↓
Donation Form
   ↓
Validation
   ↓
OCR Processing
   ↓
NGO Matching
   ↓
NGO Accepts
   ↓
Pickup Scheduled
   ↓
Donation Completed
```

---

# 🧠 Architecture

The application follows a modular layered architecture:

```text
UI Layer
   ↓
Views
   ↓
Services
   ↓
Repositories
   ↓
SQLite Database
```

Benefits:
- Separation of concerns
- Better maintainability
- Easier testing
- Scalable structure

---

# ❓ Troubleshooting

| Issue | Solution |
|---|---|
| OCR not loading | Install `rapidocr-onnxruntime opencv-python-headless onnxruntime` |
| Map not showing | Install `folium streamlit-folium` |
| Location denied | Enable browser location permissions |
| No nearby POIs | Increase search radius |
| OCR install failure on Python 3.13 | Use `rapidocr-onnxruntime>=1.2.3,<1.3` |

---

# 📈 Why This Project Stands Out

- Real-world healthcare impact
- OCR + Maps + Matching integration
- Fully open-source & free
- Practical NGO coordination workflow
- Analytics dashboard
- Strong modular architecture
- Beginner-friendly but scalable design

---

# 👨‍💻 Developed Using

- Python
- Streamlit
- SQLite
- OpenStreetMap
- RapidOCR
- Plotly
- Pydantic

---

# 📜 License

This project is for educational and demonstration purposes.

---

# ❤️ Acknowledgements

Special thanks to:
- OpenStreetMap
- RapidOCR
- Streamlit
- Open-source Python community

---

# 📬 Contact

For improvements, contributions, or collaboration:
- Create issues
- Submit pull requests
- Fork the repository

---
