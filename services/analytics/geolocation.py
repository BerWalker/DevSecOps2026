import ipaddress
import requests


def lookup_ip(ip: str | None) -> dict:
    if not ip:
        return {}

    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return {}

    if address.is_private or address.is_loopback or address.is_link_local:
        return {}

    url = (
        f"http://ip-api.com/json/{ip}"
        "?fields=status,country,regionName,city,lat,lon"
    )
    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return {}

    if data.get("status") != "success":
        return {}

    return {
        "country": data.get("country"),
        "region": data.get("regionName"),
        "city": data.get("city"),
        "latitude": data.get("lat"),
        "longitude": data.get("lon"),
    }
