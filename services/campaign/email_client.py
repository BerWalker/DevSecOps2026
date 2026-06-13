import json
import urllib.error
import urllib.request

from services.campaign.config import Config


class EmailClientError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def send_campaign_email(
    *,
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> dict:
    payload = {
        "to": to,
        "subject": subject,
        "html_body": html_body,
    }
    if text_body:
        payload["text_body"] = text_body

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Internal-Key": Config.INTERNAL_API_KEY,
    }
    url = f"{Config.GATEWAY_URL}/api/internal/send"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        try:
            error_payload = json.loads(exc.read().decode("utf-8"))
            message = error_payload.get("message", "Email service error.")
        except (json.JSONDecodeError, UnicodeDecodeError):
            message = "Email service unavailable."
        status = exc.code if exc.code in (400, 401) else 502
        raise EmailClientError(message, status) from exc
    except urllib.error.URLError as exc:
        raise EmailClientError("Email service unavailable.", 502) from exc

    result = json.loads(raw)
    if result.get("status") != "success":
        message = result.get("message", "Email service error.")
        raise EmailClientError(message, 502)

    return result.get("data", {})
