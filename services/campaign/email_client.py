import requests

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

    headers = {
        "Accept": "application/json",
        "X-Internal-Key": Config.INTERNAL_API_KEY,
    }
    url = f"{Config.GATEWAY_URL}/api/internal/send"

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.HTTPError as exc:
        try:
            error_payload = exc.response.json()
            message = error_payload.get("message", "Email service error.")
        except ValueError:
            message = "Email service unavailable."
        status = exc.response.status_code if exc.response.status_code in (400, 401) else 502
        raise EmailClientError(message, status) from exc
    except requests.RequestException as exc:
        raise EmailClientError("Email service unavailable.", 502) from exc

    if result.get("status") != "success":
        message = result.get("message", "Email service error.")
        raise EmailClientError(message, 502)

    return result.get("data", {})
