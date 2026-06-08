import ipaddress
import json
import urllib.error
import urllib.request


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
        with urllib.request.urlopen(url, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
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
