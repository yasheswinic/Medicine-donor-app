"""Free geolocation — browser GPS + OpenStreetMap (Nominatim + Overpass). No API keys."""

from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from app.services.map_service import resolve_coords
from app.utils import get_logger

logger = get_logger()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "MedDonate/1.0 (education demo; contact support@meddonate.demo)"
_LAST_NOMINATIM_CALL = 0.0
_NOMINATIM_MIN_INTERVAL = 1.1  # OSM usage policy: max 1 req/sec


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two WGS84 points."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def _http_get(url: str, params: dict[str, str], timeout: int = 20) -> Any:
    qs = urllib.parse.urlencode(params)
    full = f"{url}?{qs}" if qs else url
    req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _throttle_nominatim() -> None:
    global _LAST_NOMINATIM_CALL
    elapsed = time.time() - _LAST_NOMINATIM_CALL
    if elapsed < _NOMINATIM_MIN_INTERVAL:
        time.sleep(_NOMINATIM_MIN_INTERVAL - elapsed)
    _LAST_NOMINATIM_CALL = time.time()


def geocode_pincode(pincode: str, country: str = "India") -> Optional[dict[str, Any]]:
    """Pincode → lat/lng via Nominatim (free)."""
    pin = "".join(c for c in pincode if c.isdigit())
    if len(pin) != 6:
        return None
    cache_key = f"pin:{pin}"
    try:
        _throttle_nominatim()
        data = _http_get(
            NOMINATIM_URL,
            {
                "postalcode": pin,
                "country": country,
                "format": "json",
                "limit": "1",
            },
        )
        if not data:
            return None
        row = data[0]
        return {
            "lat": float(row["lat"]),
            "lng": float(row["lon"]),
            "display_name": row.get("display_name", pin),
            "source": "pincode",
        }
    except Exception as e:
        logger.warning("Geocode pincode failed: %s", e)
        return None


def geocode_city(city: str) -> Optional[dict[str, Any]]:
    """City name → lat/lng (local table first, then Nominatim)."""
    coords = resolve_coords(city)
    if coords:
        return {
            "lat": coords[0],
            "lng": coords[1],
            "display_name": city,
            "source": "city_table",
        }
    try:
        _throttle_nominatim()
        data = _http_get(
            NOMINATIM_URL,
            {"q": f"{city}, India", "format": "json", "limit": "1"},
        )
        if not data:
            return None
        row = data[0]
        return {
            "lat": float(row["lat"]),
            "lng": float(row["lon"]),
            "display_name": row.get("display_name", city),
            "source": "nominatim",
        }
    except Exception as e:
        logger.warning("Geocode city failed: %s", e)
        return None


def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """GPS coordinates → place name."""
    try:
        _throttle_nominatim()
        data = _http_get(
            "https://nominatim.openstreetmap.org/reverse",
            {"lat": str(lat), "lon": str(lng), "format": "json"},
        )
        return data.get("display_name")
    except Exception:
        return None


def fetch_nearby_places(
    lat: float,
    lng: float,
    radius_m: int = 3000,
    limit: int = 25,
) -> tuple[list[dict[str, Any]], Optional[str]]:
    """
    Pharmacies, hospitals, clinics near a point — Overpass API (free).
    Returns (places, error).
    """
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"pharmacy|hospital|clinic"](around:{radius_m},{lat},{lng});
      way["amenity"~"pharmacy|hospital|clinic"](around:{radius_m},{lat},{lng});
      node["healthcare"="pharmacy"](around:{radius_m},{lat},{lng});
    );
    out center {limit};
    """
    try:
        payload = urllib.parse.urlencode({"data": query}).encode("utf-8")
        req = urllib.request.Request(
            OVERPASS_URL,
            data=payload,
            headers={"User-Agent": USER_AGENT},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return [], f"Map service busy (HTTP {e.code}). Try again in a minute."
    except Exception as e:
        logger.warning("Overpass failed: %s", e)
        return [], f"Could not load nearby places: {e}"

    places: list[dict[str, Any]] = []
    seen: set[str] = set()

    for el in data.get("elements", []):
        tags = el.get("tags") or {}
        name = tags.get("name") or tags.get("brand") or tags.get("operator")
        if not name:
            continue
        plat = el.get("lat") or (el.get("center") or {}).get("lat")
        plng = el.get("lon") or (el.get("center") or {}).get("lon")
        if plat is None or plng is None:
            continue
        key = f"{name}|{round(plat, 4)}|{round(plng, 4)}"
        if key in seen:
            continue
        seen.add(key)

        amenity = tags.get("amenity") or tags.get("healthcare") or "healthcare"
        dist = haversine_km(lat, lng, float(plat), float(plng))
        places.append({
            "name": name,
            "type": amenity,
            "lat": float(plat),
            "lng": float(plng),
            "distance_km": round(dist, 2),
            "address": tags.get("addr:street") or tags.get("addr:full") or "",
            "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "opening_hours": tags.get("opening_hours") or "",
            "source": "openstreetmap",
        })

    places.sort(key=lambda x: x["distance_km"])
    return places[:limit], None


def attach_coords_to_records(
    records: list[dict],
    *,
    city_key: str = "city",
    pincode_key: str = "pincode",
) -> list[dict]:
    """Add lat/lng to donor/NGO rows using pincode or city geocoding."""
    enriched = []
    for rec in records:
        row = dict(rec)
        lat = lng = None
        pin = row.get(pincode_key) or ""
        if pin:
            geo = geocode_pincode(str(pin))
            if geo:
                lat, lng = geo["lat"], geo["lng"]
        if lat is None and row.get(city_key):
            geo = geocode_city(str(row[city_key]))
            if geo:
                lat, lng = geo["lat"], geo["lng"]
        if lat is not None:
            row["lat"] = lat
            row["lng"] = lng
        enriched.append(row)
    return enriched


def nearby_app_records(
    user_lat: float,
    user_lng: float,
    donors: list[dict],
    ngos: list[dict],
    radius_km: float = 15.0,
) -> dict[str, list[dict]]:
    """Donors/NGOs in the app with distance from user (city/pincode geocoded)."""
    out_donors: list[dict] = []
    out_ngos: list[dict] = []

    for donor in attach_coords_to_records(donors):
        if donor.get("lat") is None:
            continue
        d = haversine_km(user_lat, user_lng, donor["lat"], donor["lng"])
        if d <= radius_km:
            row = dict(donor)
            row["distance_km"] = round(d, 2)
            out_donors.append(row)

    for ngo in attach_coords_to_records(ngos):
        if ngo.get("lat") is None:
            continue
        d = haversine_km(user_lat, user_lng, ngo["lat"], ngo["lng"])
        if d <= radius_km:
            row = dict(ngo)
            row["distance_km"] = round(d, 2)
            out_ngos.append(row)

    out_donors.sort(key=lambda x: x["distance_km"])
    out_ngos.sort(key=lambda x: x["distance_km"])
    return {"donors": out_donors, "ngos": out_ngos}
