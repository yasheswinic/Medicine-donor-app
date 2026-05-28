"""Admin authentication — bcrypt stored in SQLite (no credentials in UI)."""

import secrets

import bcrypt

from app.db import execute_query, fetch_one
from app.utils import get_logger, now_iso

logger = get_logger()


def admin_exists() -> bool:
    row = fetch_one("SELECT id FROM admin_users LIMIT 1")
    return row is not None


def create_admin(username: str, password: str) -> None:
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    execute_query(
        "INSERT INTO admin_users (username, password_hash, created_at) VALUES (?, ?, ?)",
        (username.strip().lower(), pw_hash, now_iso()),
    )
    logger.info("Admin account created: %s", username)


def verify_admin(username: str, password: str) -> bool:
    row = fetch_one(
        "SELECT password_hash FROM admin_users WHERE username = ?",
        (username.strip().lower(),),
    )
    if not row:
        return False
    return bcrypt.checkpw(password.encode(), row["password_hash"].encode())


def bootstrap_admin_from_env(username: str, password: str) -> None:
    """One-time silent bootstrap when env credentials exist and DB is empty."""
    if admin_exists() or not username or not password:
        return
    create_admin(username, password)


def reset_admin_to_env(username: str, password: str) -> None:
    """Reset admin account to .env credentials (demo recovery)."""
    from app.db import execute_query

    execute_query("DELETE FROM admin_users")
    create_admin(username, password)
    logger.info("Admin reset to env user: %s", username)


def generate_setup_credentials() -> tuple[str, str]:
    """Generate random credentials for first-time setup suggestion only."""
    user = f"admin_{secrets.token_hex(3)}"
    pwd = secrets.token_urlsafe(10)
    return user, pwd
