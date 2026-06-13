import json
import urllib.error
import urllib.request

from services.campaign.config import Config


class AuthClientError(Exception):
    pass


def introspect_token(token: str) -> dict | None:
    body = json.dumps({"token": token}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Internal-Key": Config.INTERNAL_API_KEY,
    }
    url = f"{Config.GATEWAY_URL}/api/internal/token/introspect"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read().decode("utf-8")
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise AuthClientError("Auth service unavailable.") from exc

    payload = json.loads(raw)
    if payload.get("status") != "success":
        raise AuthClientError("Auth service error.")

    data = payload.get("data") or {}
    if not data.get("active"):
        return None

    return data
