import uuid
from functools import wraps

import jwt
from flask import g, jsonify, request
from jwt.exceptions import InvalidTokenError

from services.analytics.config import Config


class TokenError(Exception):
    pass


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM],
        )
    except InvalidTokenError as exc:
        raise TokenError("Invalid or expired token.") from exc


def _extract_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    return token or None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing or invalid authentication token.",
                    }
                ),
                401,
            )

        try:
            payload = decode_access_token(token)
        except TokenError:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing or invalid authentication token.",
                    }
                ),
                401,
            )

        sub = payload.get("sub")
        if not sub:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing or invalid authentication token.",
                    }
                ),
                401,
            )

        try:
            g.user_id = uuid.UUID(str(sub))
        except ValueError:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing or invalid authentication token.",
                    }
                ),
                401,
            )

        g.auth_token = token
        return f(*args, **kwargs)

    return decorated
