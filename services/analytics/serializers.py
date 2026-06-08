from services.analytics.models.click_event import ClickEvent


def format_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def click_event_to_dict(event: ClickEvent) -> dict:
    return {
        "id": str(event.id),
        "event_type": event.event_type,
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "country": event.country,
        "region": event.region,
        "city": event.city,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "created_at": event.created_at.isoformat(),
    }
