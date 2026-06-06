from services.campaign.config import Config
from services.campaign.models.campaign import Campaign, Interaction, Target, TrackingLink


def tracking_url(token: str) -> str:
    return f"{Config.TRACKING_BASE_URL}/track/{token}"


def interaction_to_dict(interaction: Interaction) -> dict:
    return {
        "id": str(interaction.id),
        "event_type": interaction.event_type,
        "ip_address": interaction.ip_address,
        "user_agent": interaction.user_agent,
        "created_at": interaction.created_at.isoformat(),
    }


def target_to_dict(target: Target, include_interactions: bool = False) -> dict:
    data = {
        "id": str(target.id),
        "email": target.email,
        "name": target.name,
    }
    if target.tracking_link:
        data["tracking"] = {
            "token": target.tracking_link.token,
            "url": tracking_url(target.tracking_link.token),
            "interaction_count": len(target.tracking_link.interactions),
        }
        if include_interactions:
            interactions = sorted(
                target.tracking_link.interactions,
                key=lambda i: i.created_at,
                reverse=True,
            )
            data["tracking"]["interactions"] = [
                interaction_to_dict(i) for i in interactions
            ]
    return data


def campaign_to_dict(campaign: Campaign, detailed: bool = False) -> dict:
    data = {
        "id": str(campaign.id),
        "name": campaign.name,
        "email_content": campaign.email_content,
        "created_by": str(campaign.created_by),
        "created_at": campaign.created_at.isoformat(),
        "updated_at": campaign.updated_at.isoformat(),
    }

    if detailed:
        data["target_groups"] = [
            {
                "id": str(group.id),
                "name": group.name,
                "targets": [target_to_dict(t, include_interactions=True) for t in group.targets],
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
    interaction_count = sum(
        len(t.tracking_link.interactions)
        for t in targets
        if t.tracking_link
    )
    clicked_targets = sum(
        1
        for t in targets
        if t.tracking_link and len(t.tracking_link.interactions) > 0
    )
    return {
        "target_count": len(targets),
        "interaction_count": interaction_count,
        "clicked_target_count": clicked_targets,
    }


def create_tracking_link(target: Target) -> TrackingLink:
    link = TrackingLink(
        target=target,
        token=TrackingLink.generate_token(),
    )
    return link
