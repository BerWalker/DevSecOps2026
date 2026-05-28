import re

from email_validator import EmailNotValidError, validate_email

MAX_EMAIL_LENGTH = 255

# Control chars and CRLF — header/log injection and filter bypass.
_UNSAFE_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\r\n]")


def validate_and_normalize_email(raw: str) -> tuple[str | None, str | None]:
    """Validate format and security constraints. Returns (normalized_email, error)."""
    email = raw.strip().lower()

    if not email:
        return None, "Email is required."
    if len(email) > MAX_EMAIL_LENGTH:
        return None, "Email must not exceed 255 characters."
    if _UNSAFE_CHARS.search(email):
        return None, "Email contains invalid characters."

    try:
        result = validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return None, "Invalid email address."

    normalized = result.normalized
    if len(normalized) > MAX_EMAIL_LENGTH:
        return None, "Email must not exceed 255 characters."

    return normalized, None


def get_email_validation_error(email: str) -> str | None:
    _, error = validate_and_normalize_email(email)
    return error


def is_email_valid(email: str) -> bool:
    return get_email_validation_error(email) is None
