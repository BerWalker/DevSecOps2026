from flask import Blueprint, jsonify, request

from services.auth import email_validation
from services.email.config import Config
from services.email.smtp_client import SmtpSendError, send_email

send_bp = Blueprint("send", __name__, url_prefix="/api/internal")


def _error(message: str, status_code: int):
    return jsonify({"status": "error", "message": message}), status_code


def _unauthorized():
    return _error("Unauthorized.", 401)


def _check_internal_key() -> bool:
    key = request.headers.get("X-Internal-Key", "")
    return bool(key and key == Config.INTERNAL_API_KEY)


@send_bp.route("/send", methods=["POST"])
def send():
    if not _check_internal_key():
        return _unauthorized()

    data = request.get_json(silent=True) or {}
    raw_to = data.get("to")
    subject = (data.get("subject") or "").strip()
    html_body = (data.get("html_body") or "").strip()
    text_body = data.get("text_body")

    if raw_to is not None and not isinstance(raw_to, str):
        return _error("Invalid recipient email.", 400)

    to, email_error = email_validation.validate_and_normalize_email(str(raw_to or ""))
    if email_error:
        return _error(email_error, 400)

    if not subject:
        return _error("Subject is required.", 400)
    if len(subject) > 255:
        return _error("Subject must not exceed 255 characters.", 400)

    if not html_body:
        return _error("html_body is required.", 400)

    if text_body is not None and not isinstance(text_body, str):
        return _error("text_body must be a string.", 400)

    try:
        send_email(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body.strip() if isinstance(text_body, str) else None,
        )
    except SmtpSendError:
        return _error("Failed to send email.", 502)

    return jsonify(
        {
            "status": "success",
            "data": {"to": to, "subject": subject},
        }
    ), 200
