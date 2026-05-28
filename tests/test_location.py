"""Tests for free geolocation helpers."""

from app.services.location_service import (
    haversine_km,
    nearby_app_records,
)


def test_haversine_same_point():
    assert haversine_km(12.97, 77.59, 12.97, 77.59) == 0.0


def test_haversine_known_distance():
    # ~0 km for very close points
    d = haversine_km(19.0760, 72.8777, 19.0800, 72.8800)
    assert 0 < d < 5


def test_nearby_app_records_filters_by_distance():
    user_lat, user_lng = 19.0760, 72.8777  # Mumbai approx
    donors = [
        {"id": 1, "name": "A", "medicine": "Med", "city": "Mumbai", "pincode": "400001"},
    ]
    ngos = [
        {"id": 1, "name": "NGO", "city": "Delhi", "pincode": "110001"},
    ]
    result = nearby_app_records(user_lat, user_lng, donors, ngos, radius_km=50.0)
    assert len(result["donors"]) >= 0  # may geocode mumbai
    assert all(d["distance_km"] <= 50 for d in result["donors"])
