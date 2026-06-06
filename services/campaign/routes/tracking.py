from flask import Blueprint, jsonify, request

from services.campaign.extensions import db
from services.campaign.models.campaign import Interaction, TrackingLink
from services.campaign.serializers import interaction_to_dict

tracking_bp = Blueprint("tracking", __name__)

ALLOWED_EVENT_TYPES = frozenset({"click", "open", "submit"})


@tracking_bp.route("/track/<token>", methods=["GET", "POST"])
def track_interaction(token: str):
    link = TrackingLink.query.filter_by(token=token).first()
    if not link:
        return jsonify({"status": "error", "message": "Invalid tracking token."}), 404

    event_type = (request.args.get("event") or "click").strip().lower()
    if event_type not in ALLOWED_EVENT_TYPES:
        return jsonify(
            {
                "status": "error",
                "message": f"Invalid event type. Allowed: {', '.join(sorted(ALLOWED_EVENT_TYPES))}.",
            }
        ), 400

    interaction = Interaction(
        tracking_link=link,
        event_type=event_type,
        ip_address=request.headers.get("X-Real-IP") or request.remote_addr,
        user_agent=(request.headers.get("User-Agent") or "")[:512] or None,
    )

    try:
        db.session.add(interaction)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Internal server error."}), 500

    return jsonify(
        {
            "status": "success",
            "message": "Interaction recorded.",
            "data": {
                "token": token,
                "event_type": event_type,
                "interaction": interaction_to_dict(interaction),
            },
        }
    ), 200
