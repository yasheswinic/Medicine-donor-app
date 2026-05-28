"""Application constants."""

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parent
UPLOADS_DIR = APP_ROOT / "uploads"
LOGS_DIR = PROJECT_ROOT / "logs"
ASSETS_DIR = APP_ROOT / "assets"

MEDICINE_TYPES = ["Tablet", "Syrup", "Capsule", "Injection", "Other"]
MEDICINE_CATEGORIES = [
    "antibiotic",
    "painkiller",
    "vitamin",
    "diabetes",
    "cardiac",
    "respiratory",
    "general",
]

DONATION_STATUSES = [
    "available",
    "pending",
    "claimed",
    "picked_up",
    "completed",
    "expired",
]

MATCH_TYPES = ["exact_match", "partial_match", "low_confidence_match"]

SHELF_LIFE_DAYS = {
    "Tablet": 365,
    "Capsule": 365,
    "Syrup": 180,
    "Injection": 90,
    "Other": 180,
}

# Exact token match (whole words) — avoids false positives like "meth" in "metformin"
BLOCKED_MEDICINE_TERMS = frozenset({
    # Withdrawn / banned pharmaceuticals
    "thalidomide", "fenfluramine", "cisapride", "rofecoxib", "phenylpropanolamine",
    # Illegal opioids & narcotics
    "heroin", "diacetylmorphine", "smack", "cocaine", "crack", "opium",
    # Stimulants & illicit synthetics
    "methamphetamine", "meth", "amphetamine", "mdma", "ecstasy",
    # Hallucinogens & club drugs
    "lsd", "psilocybin", "pcp", "ghb", "rohypnol", "flunitrazepam",
    # Cannabis & derivatives (non-medical donation context)
    "marijuana", "cannabis", "ganja", "hashish", "bhang", "weed", "charas",
    # Other high-risk illicit substances
    "fentanyl", "carfentanil", "krokodil", "bath", "salts",
})

# Multi-word phrases checked as substrings in normalized name
BLOCKED_MEDICINE_PHRASES = (
    "crystal meth",
    "magic mushroom",
    "date rape",
    "bath salts",
)

# Display category when a term is blocked (for safety checker UI)
BLOCKED_TERM_CATEGORIES = {
    "heroin": "narcotic (illegal)",
    "diacetylmorphine": "narcotic (illegal)",
    "smack": "narcotic (illegal)",
    "cocaine": "stimulant (illegal)",
    "crack": "stimulant (illegal)",
    "opium": "narcotic (illegal)",
    "methamphetamine": "stimulant (illegal)",
    "meth": "stimulant (illegal)",
    "crystal meth": "stimulant (illegal)",
    "marijuana": "controlled substance (illegal)",
    "cannabis": "controlled substance (illegal)",
    "ganja": "controlled substance (illegal)",
    "weed": "controlled substance (illegal)",
    "lsd": "hallucinogen (illegal)",
    "mdma": "hallucinogen (illegal)",
    "ecstasy": "hallucinogen (illegal)",
    "fentanyl": "opioid (high-risk)",
    "thalidomide": "withdrawn drug",
}

# Backward-compatible alias
UNSAFE_MEDICINES = BLOCKED_MEDICINE_TERMS

COMMON_MEDICINES = [
    "Paracetamol 500mg",
    "Ibuprofen 400mg",
    "Amoxicillin 500mg",
    "Metformin 500mg",
    "Azithromycin 500mg",
    "Vitamin D3 60k",
    "ORS Sachets",
    "Cetirizine 10mg",
    "Omeprazole 20mg",
    "Salbutamol Inhaler",
]

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

MAX_NAME_LEN = 100
MAX_MEDICINE_LEN = 150
MIN_QUANTITY = 1
MAX_QUANTITY = 10000
