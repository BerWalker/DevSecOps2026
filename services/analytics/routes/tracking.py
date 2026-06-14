import uuid

from flask import Blueprint, jsonify, redirect, request

from services.analytics.campaign_client import CampaignClientError, resolve_tracking_token
from services.analytics.extensions import db
from services.analytics.geolocation import lookup_ip
from services.analytics.models.click_event import ClickEvent
from services.analytics.serializers import click_event_to_dict

tracking_bp = Blueprint("tracking", __name__)

ALLOWED_EVENT_TYPES = frozenset({"click", "open", "submit"})


@tracking_bp.route("/track/<token>", methods=["GET", "POST"])
def track_interaction(token: str):
    try:
        link_data = resolve_tracking_token(token)
    except CampaignClientError as exc:
        status = 404 if exc.status_code == 404 else 502
        return jsonify({"status": "error", "message": str(exc)}), status

    event_type = (request.args.get("event") or "click").strip().lower()
    if event_type not in ALLOWED_EVENT_TYPES:
        return jsonify(
            {
                "status": "error",
                "message": (
                    "Invalid event type. Allowed: "
                    f"{', '.join(sorted(ALLOWED_EVENT_TYPES))}."
                ),
            }
        ), 400

    ip_address = request.headers.get("X-Real-IP") or request.remote_addr
    geo = lookup_ip(ip_address)

    event = ClickEvent(
        campaign_id=uuid.UUID(link_data["campaign_id"]),
        target_id=uuid.UUID(link_data["target_id"]),
        owner_id=uuid.UUID(link_data["owner_id"]),
        token=token,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=(request.headers.get("User-Agent") or "")[:512] or None,
        country=geo.get("country"),
        region=geo.get("region"),
        city=geo.get("city"),
        latitude=geo.get("latitude"),
        longitude=geo.get("longitude"),
    )

    try:
        db.session.add(event)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Internal server error."}), 500

    redirect_url = (link_data.get("redirect_url") or "").strip()
    if (
        request.method == "GET"
        and event_type == "click"
        and redirect_url
        and request.accept_mimetypes.best != "application/json"
    ):
        return redirect(redirect_url, code=302)

    return jsonify(
        {
            "status": "success",
            "message": "Interaction recorded.",
            "data": {
                "token": token,
                "event_type": event_type,
                "interaction": click_event_to_dict(event),
            },
        }
    ), 200
