from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from services.campaign.config import Config
from services.campaign.models.campaign import Target, TargetGroup, TrackingLink

internal_bp = Blueprint("internal", __name__, url_prefix="/api/internal")


def _unauthorized():
    return jsonify({"status": "error", "message": "Unauthorized."}), 401


def _check_internal_key():
    key = request.headers.get("X-Internal-Key", "")
    return key and key == Config.INTERNAL_API_KEY


@internal_bp.route("/tracking-links/<token>", methods=["GET"])
def resolve_tracking_link(token: str):
    if not _check_internal_key():
        return _unauthorized()

    link = (
        TrackingLink.query.filter_by(token=token)
        .options(
            joinedload(TrackingLink.target)
            .joinedload(Target.group)
            .joinedload(TargetGroup.campaign)
        )
        .first()
    )
    if not link:
        return jsonify({"status": "error", "message": "Invalid tracking token."}), 404

    target = link.target
    campaign = target.group.campaign

    return jsonify(
        {
            "status": "success",
            "data": {
                "token": token,
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "target_id": str(target.id),
                "target_email": target.email,
                "target_name": target.name,
                "owner_id": str(campaign.created_by),
            },
        }
    ), 200
