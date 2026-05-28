"""Pydantic v2 validation models."""

import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.constants import MAX_MEDICINE_LEN, MAX_NAME_LEN, MAX_QUANTITY, MIN_QUANTITY
from app.utils import detect_medicine_category, is_medicine_valid, sanitize_input

PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$")
PINCODE_PATTERN = re.compile(r"^\d{6}$")


class DonorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=MAX_NAME_LEN)
    email: EmailStr
    phone: str
    medicine: str = Field(..., min_length=2, max_length=MAX_MEDICINE_LEN)
    medicine_type: str
    quantity: int = Field(default=1, ge=MIN_QUANTITY, le=MAX_QUANTITY)
    manufacturing_date: date
    city: str = Field(..., min_length=2, max_length=80)
    locality: str = Field(..., min_length=2, max_length=80)
    pincode: str
    medicine_photo: Optional[str] = None

    @field_validator("name", "medicine", "city", "locality", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        return sanitize_input(str(v))

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", "", v.strip())
        if not PHONE_PATTERN.match(cleaned):
            raise ValueError("Invalid Indian phone number (10 digits, starts 6-9)")
        return cleaned

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        cleaned = v.strip()
        if not PINCODE_PATTERN.match(cleaned):
            raise ValueError("Pincode must be exactly 6 digits")
        return cleaned

    @field_validator("medicine_type")
    @classmethod
    def validate_medicine_type(cls, v: str) -> str:
        from app.constants import MEDICINE_TYPES

        if v not in MEDICINE_TYPES:
            raise ValueError(f"Medicine type must be one of: {', '.join(MEDICINE_TYPES)}")
        return v

    def validate_expiry(self) -> bool:
        return is_medicine_valid(self.manufacturing_date, self.medicine_type)

    def category(self) -> str:
        return detect_medicine_category(self.medicine)


class NGOCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=MAX_NAME_LEN)
    email: EmailStr
    phone: str
    city: str = Field(..., min_length=2, max_length=80)
    locality: str = Field(..., min_length=2, max_length=80)
    medicines: str = Field(..., min_length=2, max_length=500)
    pincode: str
    category_preferences: str = "general"

    @field_validator("name", "city", "locality", "medicines", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        return sanitize_input(str(v))

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", "", v.strip())
        if not PHONE_PATTERN.match(cleaned):
            raise ValueError("Invalid Indian phone number")
        return cleaned

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        cleaned = v.strip()
        if not PINCODE_PATTERN.match(cleaned):
            raise ValueError("Pincode must be exactly 6 digits")
        return cleaned


class AdminLogin(BaseModel):
    username: str
    password: str

    @field_validator("username", mode="before")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        return sanitize_input(str(v).strip())
