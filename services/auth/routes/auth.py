from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from services.auth import email_validation, jwt_tokens, password
from services.auth.extensions import db
from services.auth.jwt_tokens import TokenError, TokenRevokedError
from services.auth.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _error(message: str, status_code: int):
    return jsonify({"status": "error", "message": message}), status_code


def _extract_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    return token or None


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    raw_email = data.get("email")
    raw_password = data.get("password") or ""
    name = (data.get("name") or "").strip() or None

    if raw_email is not None and not isinstance(raw_email, str):
        return _error("Invalid email address.", 400)

    email, email_error = email_validation.validate_and_normalize_email(
        str(raw_email or "")
    )
    if not email and not raw_password:
        return _error("Email and password are required.", 400)
    if email_error:
        return _error(email_error, 400)
    if not raw_password:
        return _error("Email and password are required.", 400)

    password_error = password.get_password_validation_error(raw_password)
    if password_error:
        return _error(password_error, 400)

    user = User(
        email=email,
        password_hash=password.hash_password(raw_password),
        name=name,
    )

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Email is already registered.", 409)
    except Exception:
        db.session.rollback()
        return _error("Internal server error.", 500)

    return (
        jsonify(
            {
                "status": "success",
                "message": "User registered successfully.",
                "data": user.to_public_dict(),
            }
        ),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    raw_email = data.get("email")
    raw_password = data.get("password") or ""

    if raw_email is not None and not isinstance(raw_email, str):
        return _error("Invalid credentials.", 401)

    email, email_error = email_validation.validate_and_normalize_email(
        str(raw_email or "")
    )
    if not email or not raw_password:
        return _error("Email and password are required.", 400)
    if email_error:
        return _error("Invalid credentials.", 401)

    user = User.query.filter_by(email=email).first()
    if not user or not password.verify_password(raw_password, user.password_hash):
        return _error("Invalid credentials.", 401)

    token, expires_in = jwt_tokens.create_access_token(user.id, user.email)

    return (
        jsonify(
            {
                "status": "success",
                "message": "Login successful.",
                "token": token,
                "expires_in": expires_in,
            }
        ),
        200,
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    token = _extract_bearer_token()
    if not token:
        return _error("Missing or invalid authentication token.", 401)

    try:
        payload = jwt_tokens.decode_access_token(token)
    except TokenRevokedError:
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Logout successful.",
                }
            ),
            200,
        )
    except TokenError:
        return _error("Missing or invalid authentication token.", 401)

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return _error("Missing or invalid authentication token.", 401)

    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

    try:
        jwt_tokens.revoke_token(jti, expires_at)
    except Exception:
        db.session.rollback()
        return _error("Internal server error.", 500)

    return (
        jsonify(
            {
                "status": "success",
                "message": "Logout successful.",
            }
        ),
        200,
    )
