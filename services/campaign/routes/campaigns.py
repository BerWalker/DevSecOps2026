from flask import Blueprint, g, jsonify, request
from sqlalchemy.orm import joinedload

from services.campaign.extensions import db
from services.campaign.jwt_auth import require_auth
from services.campaign.models.campaign import (
    Campaign,
    Target,
    TargetGroup,
    TrackingLink,
)
from services.campaign.serializers import (
    build_target_email_html,
    campaign_to_dict,
    create_tracking_link,
    tracking_url,
)
from services.campaign.email_client import EmailClientError, send_campaign_email
from services.campaign.validation import (
    parse_target_groups,
    validate_campaign_name,
    validate_email_content,
)

campaigns_bp = Blueprint("campaigns", __name__, url_prefix="/api/campaigns")


def _error(message: str, status_code: int):
    return jsonify({"status": "error", "message": message}), status_code


def _get_campaign_or_404(campaign_id: str):
    try:
        from uuid import UUID

        campaign_uuid = UUID(campaign_id)
    except ValueError:
        return None, _error("Campaign not found.", 404)

    campaign = (
        Campaign.query.options(
            joinedload(Campaign.target_groups)
            .joinedload(TargetGroup.targets)
            .joinedload(Target.tracking_link)
        )
        .filter_by(id=campaign_uuid, created_by=g.user_id)
        .first()
    )
    if not campaign:
        return None, _error("Campaign not found.", 404)
    return campaign, None


def _apply_target_groups(campaign: Campaign, groups: list[dict]) -> None:
    campaign.target_groups.clear()
    for group_data in groups:
        group = TargetGroup(name=group_data["name"], campaign=campaign)
        for target_data in group_data["targets"]:
            target = Target(
                email=target_data["email"],
                name=target_data.get("name"),
                group=group,
            )
            create_tracking_link(target)
            group.targets.append(target)
        campaign.target_groups.append(group)


@campaigns_bp.route("", methods=["GET"])
@require_auth
def list_campaigns():
    campaigns = (
        Campaign.query.options(joinedload(Campaign.target_groups).joinedload(TargetGroup.targets))
        .filter_by(created_by=g.user_id)
        .order_by(Campaign.created_at.desc())
        .all()
    )
    return jsonify(
        {
            "status": "success",
            "data": [campaign_to_dict(c) for c in campaigns],
        }
    ), 200


@campaigns_bp.route("", methods=["POST"])
@require_auth
def create_campaign():
    data = request.get_json(silent=True) or {}

    name = data.get("name") or ""
    if not isinstance(name, str):
        return _error("Campaign name is required.", 400)
    name_error = validate_campaign_name(name)
    if name_error:
        return _error(name_error, 400)

    email_content = data.get("email_content") or ""
    if not isinstance(email_content, str):
        return _error("Email content is required.", 400)
    content_error = validate_email_content(email_content)
    if content_error:
        return _error(content_error, 400)

    groups, groups_error = parse_target_groups(data.get("target_groups", []))
    if groups_error:
        return _error(groups_error, 400)

    campaign = Campaign(
        name=name.strip(),
        email_content=email_content,
        created_by=g.user_id,
    )
    _apply_target_groups(campaign, groups or [])

    try:
        db.session.add(campaign)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _error("Internal server error.", 500)

    campaign = (
        Campaign.query.options(
            joinedload(Campaign.target_groups)
            .joinedload(TargetGroup.targets)
            .joinedload(Target.tracking_link)
        )
        .get(campaign.id)
    )

    return (
        jsonify(
            {
                "status": "success",
                "message": "Campaign created successfully.",
                "data": campaign_to_dict(campaign, detailed=True),
            }
        ),
        201,
    )


@campaigns_bp.route("/<campaign_id>", methods=["GET"])
@require_auth
def get_campaign(campaign_id: str):
    campaign, err = _get_campaign_or_404(campaign_id)
    if err:
        return err
    return jsonify(
        {
            "status": "success",
            "data": campaign_to_dict(campaign, detailed=True),
        }
    ), 200


@campaigns_bp.route("/<campaign_id>", methods=["PUT"])
@require_auth
def update_campaign(campaign_id: str):
    campaign, err = _get_campaign_or_404(campaign_id)
    if err:
        return err

    data = request.get_json(silent=True) or {}

    if "name" in data:
        if not isinstance(data["name"], str):
            return _error("Campaign name is required.", 400)
        name_error = validate_campaign_name(data["name"])
        if name_error:
            return _error(name_error, 400)
        campaign.name = data["name"].strip()

    if "email_content" in data:
        if not isinstance(data["email_content"], str):
            return _error("Email content is required.", 400)
        content_error = validate_email_content(data["email_content"])
        if content_error:
            return _error(content_error, 400)
        campaign.email_content = data["email_content"]

    if "target_groups" in data:
        groups, groups_error = parse_target_groups(data["target_groups"])
        if groups_error:
            return _error(groups_error, 400)
        _apply_target_groups(campaign, groups or [])

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _error("Internal server error.", 500)

    campaign = (
        Campaign.query.options(
            joinedload(Campaign.target_groups)
            .joinedload(TargetGroup.targets)
            .joinedload(Target.tracking_link)
        )
        .get(campaign.id)
    )

    return jsonify(
        {
            "status": "success",
            "message": "Campaign updated successfully.",
            "data": campaign_to_dict(campaign, detailed=True),
        }
    ), 200


@campaigns_bp.route("/<campaign_id>", methods=["DELETE"])
@require_auth
def delete_campaign(campaign_id: str):
    campaign, err = _get_campaign_or_404(campaign_id)
    if err:
        return err

    try:
        db.session.delete(campaign)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _error("Internal server error.", 500)

    return jsonify(
        {
            "status": "success",
            "message": "Campaign deleted successfully.",
        }
    ), 200


@campaigns_bp.route("/<campaign_id>/send", methods=["POST"])
@require_auth
def send_campaign(campaign_id: str):
    campaign, err = _get_campaign_or_404(campaign_id)
    if err:
        return err

    targets = [target for group in campaign.target_groups for target in group.targets]
    if not targets:
        return _error("Campaign has no targets.", 400)

    sent: list[str] = []
    failed: list[dict] = []

    for target in targets:
        if not target.tracking_link:
            failed.append(
                {"email": target.email, "message": "Missing tracking link."}
            )
            continue

        link_url = tracking_url(target.tracking_link.token)
        html_body = build_target_email_html(campaign.email_content, target, link_url)

        try:
            send_campaign_email(
                to=target.email,
                subject=campaign.name,
                html_body=html_body,
                text_body=f"Open this link: {link_url}",
            )
            sent.append(target.email)
        except EmailClientError as exc:
            failed.append({"email": target.email, "message": str(exc)})

    if not sent:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to send campaign emails.",
                    "data": {"sent_count": 0, "failed": failed},
                }
            ),
            502,
        )

    status = "success" if not failed else "partial"
    message = (
        "Campaign emails sent successfully."
        if not failed
        else "Campaign emails sent with some failures."
    )

    return (
        jsonify(
            {
                "status": status,
                "message": message,
                "data": {
                    "campaign_id": str(campaign.id),
                    "sent_count": len(sent),
                    "failed_count": len(failed),
                    "sent": sent,
                    "failed": failed,
                },
            }
        ),
        200,
    )
