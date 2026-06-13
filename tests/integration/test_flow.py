"""Integration tests for the backend service flow (requires running Docker stack)."""

import os
import uuid

import pytest
import urllib.error
import urllib.request
import json

BASE_URL = os.getenv("INTEGRATION_BASE_URL", "http://localhost:5000")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "change-me-internal-key")


def _request(method: str, path: str, *, headers=None, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers or {},
        method=method,
    )
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


def test_auth_campaign_track_analytics_flow():
    email = f"integration.{uuid.uuid4().hex[:8]}@example.com"
    password = "SenhaSegura123!"

    status, _ = _request(
        "POST",
        "/api/auth/register",
        body={"email": email, "password": password, "name": "Integration Test"},
    )
    assert status == 201

    status, login = _request(
        "POST",
        "/api/auth/login",
        body={"email": email, "password": password},
    )
    assert status == 200
    token = login["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    status, campaign = _request(
        "POST",
        "/api/campaigns",
        headers=auth_headers,
        body={
            "name": "Integration Campaign",
            "email_content": "<p>Track: {{tracking_url}}</p>",
            "target_groups": [
                {
                    "name": "Group A",
                    "targets": [{"email": "bernardoowalkerl@gmail.com", "name": "Target"}],
                }
            ],
        },
    )
    assert status == 201
    campaign_id = campaign["data"]["id"]
    tracking_url = campaign["data"]["target_groups"][0]["targets"][0]["tracking"]["url"]

    status, send_result = _request(
        "POST",
        f"/api/campaigns/{campaign_id}/send",
        headers=auth_headers,
    )
    assert status in (200, 502)
    assert "sent_count" in send_result.get("data", {}) or send_result["status"] == "error"

    status, track = _request("GET", tracking_url.replace(BASE_URL, "") + "?event=click")
    assert status == 200
    assert track["data"]["event_type"] == "click"

    status, analytics = _request(
        "GET",
        f"/api/analytics/campaigns/{campaign_id}",
        headers=auth_headers,
    )
    assert status == 200
    assert analytics["data"]["click_count"] >= 1

    status, _ = _request("POST", "/api/auth/logout", headers=auth_headers)
    assert status == 200

    status, _ = _request("GET", "/api/campaigns", headers=auth_headers)
    assert status == 401
