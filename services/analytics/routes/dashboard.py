from flask import Blueprint, g, jsonify

from services.analytics.campaign_client import CampaignClientError, list_campaigns
from services.analytics.jwt_auth import require_auth
from services.analytics.metrics import build_dashboard

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/analytics")


@dashboard_bp.route("/dashboard", methods=["GET"])
@require_auth
def aggregate_dashboard():
    try:
        campaigns = list_campaigns(g.auth_token)
    except CampaignClientError as exc:
        return jsonify({"status": "error", "message": str(exc)}), exc.status_code

    data = build_dashboard(g.user_id, campaigns)
    return jsonify({"status": "success", "data": data}), 200
