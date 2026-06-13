import uuid
from functools import wraps

from flask import g, jsonify, request

from services.analytics.auth_client import AuthClientError, introspect_token


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
            token_data = introspect_token(token)
        except AuthClientError:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Authentication service unavailable.",
                    }
                ),
                503,
            )

        if not token_data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing or invalid authentication token.",
                    }
                ),
                401,
            )

        sub = token_data.get("sub")
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
