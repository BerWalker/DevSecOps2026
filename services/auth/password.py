import re

import bcrypt

MIN_PASSWORD_LENGTH = 8


def get_password_validation_error(password: str) -> str | None:
    if not password:
        return "Password is required."
    if len(password) < MIN_PASSWORD_LENGTH:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "Password must contain at least one symbol."
    return None


def is_password_valid(password: str) -> bool:
    return get_password_validation_error(password) is None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )
