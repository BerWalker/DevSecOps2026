import requests

from services.analytics.config import Config


class AuthClientError(Exception):
    pass


def introspect_token(token: str) -> dict | None:
    headers = {
        "Accept": "application/json",
        "X-Internal-Key": Config.INTERNAL_API_KEY,
    }
    url = f"{Config.GATEWAY_URL}/api/internal/token/introspect"

    try:
        response = requests.post(url, json={"token": token}, headers=headers, timeout=5)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise AuthClientError("Auth service unavailable.") from exc

    if payload.get("status") != "success":
        raise AuthClientError("Auth service error.")

    data = payload.get("data") or {}
    if not data.get("active"):
        return None

    return data
