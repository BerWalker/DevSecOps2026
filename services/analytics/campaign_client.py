import json
import urllib.error
import urllib.request
from typing import Any

from services.analytics.config import Config


class CampaignClientError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _request(
    path: str,
    *,
    auth_token: str | None = None,
    internal: bool = False,
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if internal:
        headers["X-Internal-Key"] = Config.INTERNAL_API_KEY
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    url = f"{Config.CAMPAIGN_SERVICE_URL}{path}"
    request = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            message = payload.get("message", "Campaign service error.")
        except (json.JSONDecodeError, UnicodeDecodeError):
            message = "Campaign service unavailable."
        status = exc.code if exc.code in (404, 401) else 502
        raise CampaignClientError(message, status) from exc
    except urllib.error.URLError as exc:
        raise CampaignClientError(
            "Campaign service unavailable.", 502
        ) from exc

    payload = json.loads(body)
    if payload.get("status") != "success":
        message = payload.get("message", "Campaign service error.")
        raise CampaignClientError(message, 502)

    return payload


def resolve_tracking_token(token: str) -> dict[str, Any]:
    payload = _request(
        f"/api/internal/tracking-links/{token}",
        internal=True,
    )
    return payload["data"]


def list_campaigns(auth_token: str) -> list[dict[str, Any]]:
    payload = _request("/api/campaigns", auth_token=auth_token)
    return payload.get("data", [])


def get_campaign(campaign_id: str, auth_token: str) -> dict[str, Any]:
    payload = _request(f"/api/campaigns/{campaign_id}", auth_token=auth_token)
    return payload["data"]
