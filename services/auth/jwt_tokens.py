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

    jti = payload.get("jti")
    if jti and RevokedToken.query.get(jti):
        raise TokenRevokedError("Token has been revoked.")

    return payload


def revoke_token(jti: str, expires_at: datetime) -> None:
    if RevokedToken.query.get(jti):
        return

    db.session.add(RevokedToken(jti=jti, expires_at=expires_at))
    db.session.commit()
