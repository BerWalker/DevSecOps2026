import uuid

from sqlalchemy import func

from services.analytics.extensions import db
from services.analytics.models.click_event import ClickEvent
from services.analytics.serializers import click_event_to_dict, format_rate


def _click_stats_for_owner(owner_id: uuid.UUID) -> dict:
    rows = (
        db.session.query(
            ClickEvent.campaign_id,
            func.count(ClickEvent.id).label("click_count"),
            func.count(func.distinct(ClickEvent.target_id)).label(
                "clicked_target_count"
            ),
        )
        .filter(ClickEvent.owner_id == owner_id)
        .group_by(ClickEvent.campaign_id)
        .all()
    )
    return {
        row.campaign_id: {
            "click_count": row.click_count,
            "clicked_target_count": row.clicked_target_count,
        }
        for row in rows
    }


def build_dashboard(owner_id: uuid.UUID, campaigns: list[dict]) -> dict:
    stats_by_campaign = _click_stats_for_owner(owner_id)

    total_targets = 0
    total_clicks = 0
    campaign_summaries = []

    for campaign in campaigns:
        campaign_id = uuid.UUID(campaign["id"])
        target_count = campaign.get("target_count", 0)
        campaign_stats = stats_by_campaign.get(campaign_id, {})
        click_count = campaign_stats.get("click_count", 0)
        clicked_target_count = campaign_stats.get("clicked_target_count", 0)

        total_targets += target_count
        total_clicks += click_count

        campaign_summaries.append(
            {
                "campaign_id": campaign["id"],
                "name": campaign["name"],
                "target_count": target_count,
                "click_count": click_count,
                "clicked_target_count": clicked_target_count,
                "click_rate": format_rate(clicked_target_count, target_count),
            }
        )

    unique_clicked = (
        db.session.query(func.count(func.distinct(ClickEvent.target_id)))
        .filter(ClickEvent.owner_id == owner_id)
        .scalar()
        or 0
    )

    return {
        "total_campaigns": len(campaigns),
        "total_targets": total_targets,
        "total_clicks": total_clicks,
        "clicked_target_count": unique_clicked,
        "click_rate": format_rate(unique_clicked, total_targets),
        "campaigns": campaign_summaries,
    }


def _events_for_campaign(
    owner_id: uuid.UUID, campaign_id: uuid.UUID
) -> list[ClickEvent]:
    return (
        ClickEvent.query.filter_by(owner_id=owner_id, campaign_id=campaign_id)
        .order_by(ClickEvent.created_at.desc())
        .all()
    )


def build_campaign_detail(owner_id: uuid.UUID, campaign: dict) -> dict:
    campaign_id = uuid.UUID(campaign["id"])
    events = _events_for_campaign(owner_id, campaign_id)

    events_by_target: dict[uuid.UUID, list[ClickEvent]] = {}
    for event in events:
        events_by_target.setdefault(event.target_id, []).append(event)

    targets = []
    for group in campaign.get("target_groups", []):
        for target in group.get("targets", []):
            target_id = uuid.UUID(target["id"])
            target_events = events_by_target.get(target_id, [])
            last_event = target_events[0] if target_events else None

            targets.append(
                {
                    "target_id": target["id"],
                    "email": target["email"],
                    "name": target.get("name"),
                    "group_name": group.get("name"),
                    "clicked": len(target_events) > 0,
                    "click_count": len(target_events),
                    "last_click_at": (
                        last_event.created_at.isoformat() if last_event else None
                    ),
                    "last_ip": last_event.ip_address if last_event else None,
                    "geolocation": (
                        {
                            "country": last_event.country,
                            "region": last_event.region,
                            "city": last_event.city,
                            "latitude": last_event.latitude,
                            "longitude": last_event.longitude,
                        }
                        if last_event
                        else None
                    ),
                    "clicks": [click_event_to_dict(event) for event in target_events],
                }
            )

    target_count = len(targets)
    clicked_target_count = sum(1 for target in targets if target["clicked"])
    click_count = len(events)

    return {
        "campaign_id": campaign["id"],
        "campaign_name": campaign["name"],
        "target_count": target_count,
        "click_count": click_count,
        "clicked_target_count": clicked_target_count,
        "click_rate": format_rate(clicked_target_count, target_count),
        "targets": targets,
    }
