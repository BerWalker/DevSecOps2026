import uuid
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from services.auth.config import Config
from services.auth.extensions import db
from services.auth.models.revoked_token import RevokedToken


class TokenError(Exception):
    pass


class TokenRevokedError(TokenError):
    pass


def create_access_token(user_id: uuid.UUID, email: str) -> tuple[str, int]:
    expires_seconds = Config.JWT_ACCESS_TOKEN_EXPIRES
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=expires_seconds)
    jti = str(uuid.uuid4())

    payload = {
        "sub": str(user_id),
        "email": email,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        Config.JWT_SECRET_KEY,
        algorithm=Config.JWT_ALGORITHM,
    )
    return token, expires_seconds


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM],
        )
    except InvalidTokenError as exc:
        raise TokenError("Invalid or expired token.") from exc

    return _validate_token_payload(payload)


def decode_access_token_for_refresh(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except InvalidTokenError as exc:
        raise TokenError("Invalid or expired token.") from exc

    exp = payload.get("exp")
    if exp:
        exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        grace = timedelta(seconds=Config.JWT_REFRESH_GRACE_SECONDS)
        if datetime.now(timezone.utc) > exp_dt + grace:
            raise TokenError("Session expired.")

    return _validate_token_payload(payload)


def _validate_token_payload(payload: dict) -> dict:
    jti = payload.get("jti")
    if jti and RevokedToken.query.get(jti):
        raise TokenRevokedError("Token has been revoked.")

    return payload


def revoke_token(jti: str, expires_at: datetime) -> None:
    if RevokedToken.query.get(jti):
        return

    db.session.add(RevokedToken(jti=jti, expires_at=expires_at))
    db.session.commit()
