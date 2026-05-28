"""Pytest fixtures with isolated test database."""

import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def test_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DB_PATH", path)
    from app.config import settings

    settings.DB_PATH = path
    from app import db

    db.init_db()
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass
