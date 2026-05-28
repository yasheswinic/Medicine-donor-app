"""Validation service."""

from typing import Optional

from app.models import AdminLogin, DonorCreate, NGOCreate
from app.repositories import donor_repo, ngo_repo
from app.utils import get_logger, is_medicine_safe, normalize_location

logger = get_logger()


def validate_donor(data: dict) -> tuple[Optional[DonorCreate], Optional[str]]:
    try:
        model = DonorCreate(**data)
    except Exception as e:
        logger.warning("Donor validation failed: %s", e)
        return None, str(e)

    if not is_medicine_safe(model.medicine):
        return None, "This medicine cannot be accepted for safety reasons"

    if not model.validate_expiry():
        return None, "Medicine has expired based on shelf-life rules"

    city, locality = normalize_location(model.city, model.locality)
    data["city"] = city.title() if city else model.city
    data["locality"] = locality.title() if locality else model.locality
    return model, None


def validate_ngo(data: dict) -> tuple[Optional[NGOCreate], Optional[str]]:
    try:
        model = NGOCreate(**data)
    except Exception as e:
        logger.warning("NGO validation failed: %s", e)
        return None, str(e)

    if ngo_repo.email_exists(model.email):
        return None, "Email already registered"

    city, locality = normalize_location(model.city, model.locality)
    data["city"] = city.title() if city else model.city
    data["locality"] = locality.title() if locality else model.locality
    return model, None


def validate_admin(credentials: dict) -> tuple[Optional[AdminLogin], Optional[str]]:
    try:
        return AdminLogin(**credentials), None
    except Exception as e:
        return None, str(e)
