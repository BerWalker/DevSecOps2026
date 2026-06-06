import uuid
from functools import wraps

import jwt
from flask import g, jsonify, request
from jwt.exceptions import InvalidTokenError

from services.campaign.config import Config
from services.campaign.extensions import db
from services.campaign.models.revoked_token import RevokedToken


class TokenError(Exception):
    pass


class TokenRevokedError(TokenError):
    pass


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM],
        )
    except InvalidTokenError as exc:
        raise TokenError("Invalid or expired token.") from exc

    jti = payload.get("jti")
    if jti and db.session.get(RevokedToken, jti):
        raise TokenRevokedError("Token has been revoked.")

    return payload


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
        except TokenRevokedError:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing or invalid authentication token.",
                    }
                ),
                401,
            )
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

        return f(*args, **kwargs)

    return decorated
