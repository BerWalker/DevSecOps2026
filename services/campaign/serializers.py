from services.campaign.config import Config
from services.campaign.models.campaign import Campaign, Target, TrackingLink


def tracking_url(token: str) -> str:
    return f"{Config.TRACKING_BASE_URL}/track/{token}"


def target_to_dict(target: Target) -> dict:
    data = {
        "id": str(target.id),
        "email": target.email,
        "name": target.name,
    }
    if target.tracking_link:
        data["tracking"] = {
            "token": target.tracking_link.token,
            "url": tracking_url(target.tracking_link.token),
        }
    return data


def campaign_to_dict(campaign: Campaign, detailed: bool = False) -> dict:
    data = {
        "id": str(campaign.id),
        "name": campaign.name,
        "email_content": campaign.email_content,
        "redirect_url": campaign.redirect_url,
        "created_by": str(campaign.created_by),
        "created_at": campaign.created_at.isoformat(),
        "updated_at": campaign.updated_at.isoformat(),
    }

    if detailed:
        data["target_groups"] = [
            {
                "id": str(group.id),
                "name": group.name,
                "targets": [target_to_dict(t) for t in group.targets],
            }
            for group in campaign.target_groups
        ]
        data["stats"] = _campaign_stats(campaign)
    else:
        data["target_group_count"] = len(campaign.target_groups)
        data["target_count"] = sum(len(g.targets) for g in campaign.target_groups)

    return data


def _campaign_stats(campaign: Campaign) -> dict:
    targets = [t for g in campaign.target_groups for t in g.targets]
    return {
        "target_count": len(targets),
    }


def create_tracking_link(target: Target) -> TrackingLink:
    link = TrackingLink(
        target=target,
        token=TrackingLink.generate_token(),
    )
    return link


def build_target_email_html(
    email_content: str, target: Target, tracking_link_url: str
) -> str:
    replacements = {
        "{{tracking_url}}": tracking_link_url,
        "{{target_name}}": target.name or "",
        "{{target_email}}": target.email,
    }
    body = email_content
    for placeholder, value in replacements.items():
        body = body.replace(placeholder, value)
    return body
