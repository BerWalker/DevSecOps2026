import csv
import io

from flask import Blueprint, Response, g, jsonify

from services.analytics.campaign_client import CampaignClientError, get_campaign
from services.analytics.jwt_auth import require_auth
from services.analytics.metrics import build_campaign_detail

campaign_analytics_bp = Blueprint(
    "campaign_analytics", __name__, url_prefix="/api/analytics/campaigns"
)


def _error(message: str, status_code: int):
    return jsonify({"status": "error", "message": message}), status_code


@campaign_analytics_bp.route("/<campaign_id>", methods=["GET"])
@require_auth
def campaign_dashboard(campaign_id: str):
    try:
        campaign = get_campaign(campaign_id, g.auth_token)
    except CampaignClientError as exc:
        return _error(str(exc), exc.status_code)

    data = build_campaign_detail(g.user_id, campaign)
    return jsonify({"status": "success", "data": data}), 200


@campaign_analytics_bp.route("/<campaign_id>/export", methods=["GET"])
@require_auth
def export_campaign_csv(campaign_id: str):
    try:
        campaign = get_campaign(campaign_id, g.auth_token)
    except CampaignClientError as exc:
        return _error(str(exc), exc.status_code)

    detail = build_campaign_detail(g.user_id, campaign)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "email",
            "name",
            "group",
            "clicked",
            "click_count",
            "last_ip",
            "country",
            "city",
            "last_click_at",
        ]
    )

    for target in detail["targets"]:
        geo = target.get("geolocation") or {}
        writer.writerow(
            [
                target["email"],
                target.get("name") or "",
                target.get("group_name") or "",
                "yes" if target["clicked"] else "no",
                target["click_count"],
                target.get("last_ip") or "",
                geo.get("country") or "",
                geo.get("city") or "",
                target.get("last_click_at") or "",
            ]
        )

    filename = f"campaign_{campaign_id}_report.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
