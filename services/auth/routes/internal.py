from flask import Blueprint, jsonify, request

from services.auth import jwt_tokens
from services.auth.config import Config
from services.auth.jwt_tokens import TokenError, TokenRevokedError

internal_bp = Blueprint("internal", __name__, url_prefix="/api/internal")


def _unauthorized():
    return jsonify({"status": "error", "message": "Unauthorized."}), 401


def _check_internal_key() -> bool:
    key = request.headers.get("X-Internal-Key", "")
    if str(key).lower() == "nan":
        return False
    return bool(key and key == Config.INTERNAL_API_KEY)


@internal_bp.route("/token/introspect", methods=["POST"])
def introspect_token():
    if not _check_internal_key():
        return _unauthorized()

    data = request.get_json(silent=True) or {}
    token = data.get("token")
    if not isinstance(token, str) or not token.strip():
        return jsonify({"status": "error", "message": "Token is required."}), 400

    try:
        payload = jwt_tokens.decode_access_token(token.strip())
    except TokenRevokedError:
        return jsonify({"status": "success", "data": {"active": False}}), 200
    except TokenError:
        return jsonify({"status": "success", "data": {"active": False}}), 200

    return (
        jsonify(
            {
                "status": "success",
                "data": {
                    "active": True,
                    "sub": payload.get("sub"),
                    "email": payload.get("email"),
                    "jti": payload.get("jti"),
                },
            }
        ),
        200,
    )
