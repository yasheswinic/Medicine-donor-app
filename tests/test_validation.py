"""Pydantic validation tests."""

from datetime import date

import pytest

from app.models import AdminLogin, DonorCreate, NGOCreate


def test_donor_valid():
    d = DonorCreate(
        name="John Doe",
        email="john@example.com",
        phone="9876543210",
        medicine="Paracetamol",
        medicine_type="Tablet",
        quantity=10,
        manufacturing_date=date.today(),
        city="Mumbai",
        locality="Andheri",
        pincode="400053",
    )
    assert d.validate_expiry() is True
    assert d.category() == "painkiller"


def test_donor_invalid_phone():
    with pytest.raises(Exception):
        DonorCreate(
            name="John",
            email="john@example.com",
            phone="12345",
            medicine="Med",
            medicine_type="Tablet",
            manufacturing_date=date.today(),
            city="Mumbai",
            locality="Andheri",
            pincode="400053",
        )


def test_donor_invalid_pincode():
    with pytest.raises(Exception):
        DonorCreate(
            name="John",
            email="john@example.com",
            phone="9876543210",
            medicine="Med",
            medicine_type="Tablet",
            manufacturing_date=date.today(),
            city="Mumbai",
            locality="Andheri",
            pincode="123",
        )


def test_ngo_valid():
    n = NGOCreate(
        name="Help NGO",
        email="ngo@example.com",
        phone="9123456789",
        city="Delhi",
        locality="Dwarka",
        medicines="paracetamol, vitamins",
        pincode="110075",
    )
    assert n.name == "Help NGO"


def test_admin_login():
    a = AdminLogin(username="admin", password="secret")
    assert a.username == "admin"
