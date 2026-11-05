"""
Location Service (📍 Location / IP API)
Detects city, region/state, and country from the user's public IP.
Priority: ipinfo.io with token (IPINFO_TOKEN) → ip-api.com → ipapi.co → fallback.
"""

import os
import logging
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import unicodedata

REQUEST_HEADERS = {"User-Agent": "CityRegionNewsSummarizer/1.0"}
TIMEOUT = 8

DEFAULT_LOCATION = {
    "ip": "Auto-detected",
    "city": "Rajkot",
    "region": "Gujarat",
    "country": "India",
    "country_code": "IN",
    "loc_string": "Rajkot, Gujarat, India",
    "lat": 22.3039,
    "lon": 70.8022,
    "is_fallback": True,
    "api_provider": "Default Fallback (Rajkot)",
}


def normalize_city_name(name: Optional[str]) -> str:
    """Normalize city name by stripping accents, macrons, and surrounding whitespace."""
    if not name:
        return ""
    # Strip diacritics: Rājkot -> Rajkot, etc.
    normalized = unicodedata.normalize("NFKD", str(name))
    ascii_clean = normalized.encode("ASCII", "ignore").decode("utf-8")
    return ascii_clean.strip()


def get_location_hierarchy(location_name: str, state_region: str = "Gujarat") -> Dict[str, Any]:
    """
    Return location hierarchy & priorities for accurate local news filtering.
    Priority 1: Specific town/village (e.g. Gadhka) and nearby rural areas.
    Priority 2: Major district hub / parent city (e.g. Rajkot).
    Avoid Distant: Explicitly excludes distant cities (e.g. Bhavnagar, Surat, etc.).
    """
    loc_clean = normalize_city_name(location_name).lower()
    
    # Specific knowledge base for regional proximity & hierarchies
    hierarchies = {
        "gadhka": {
            "primary": "Gadhka",
            "district": "Rajkot",
            "state": "Gujarat",
            "nearby_areas": ["Gadhka", "Tramba", "Sardhar", "Kasturbadham", "Kuvadva", "Rajkot Rural"],
            "priority_1_label": "Priority 1: Gadhka & Nearby Areas",
            "priority_2_label": "Priority 2: Rajkot (District Hub)",
            "avoid_distant": ["Bhavnagar", "Surat", "Ahmedabad", "Vadodara", "Jamnagar", "Junagadh", "Morbi"],
        },
        "tramba": {
            "primary": "Tramba",
            "district": "Rajkot",
            "state": "Gujarat",
            "nearby_areas": ["Tramba", "Gadhka", "Sardhar", "Kasturbadham"],
            "priority_1_label": "Priority 1: Tramba & Nearby Areas",
            "priority_2_label": "Priority 2: Rajkot (District Hub)",
            "avoid_distant": ["Bhavnagar", "Surat", "Ahmedabad", "Vadodara"],
        },
        "sardhar": {
            "primary": "Sardhar",
            "district": "Rajkot",
            "state": "Gujarat",
            "nearby_areas": ["Sardhar", "Gadhka", "Tramba", "Kasturbadham"],
            "priority_1_label": "Priority 1: Sardhar & Nearby Areas",
            "priority_2_label": "Priority 2: Rajkot (District Hub)",
            "avoid_distant": ["Bhavnagar", "Surat", "Ahmedabad", "Vadodara"],
        },
        "rajkot": {
            "primary": "Rajkot",
            "district": "Rajkot",
            "state": "Gujarat",
            "nearby_areas": ["Rajkot", "Gadhka", "Metoda", "Shapar", "Paddhari", "Kuvadva", "Sardhar"],
            "priority_1_label": "Priority 1: Rajkot & Nearby Areas (incl. Gadhka)",
            "priority_2_label": "Priority 2: Rajkot District",
            "avoid_distant": ["Bhavnagar", "Surat", "Ahmedabad", "Vadodara"],
        },
        "bhavnagar": {
            "primary": "Bhavnagar",
            "district": "Bhavnagar",
            "state": "Gujarat",
            "nearby_areas": ["Bhavnagar", "Sihor", "Ghogha", "Vartej"],
            "priority_1_label": "Priority 1: Bhavnagar & Nearby Areas",
            "priority_2_label": "Priority 2: Bhavnagar District",
            "avoid_distant": ["Rajkot", "Gadhka", "Surat", "Ahmedabad", "Vadodara"],
        },
    }

    for key, data in hierarchies.items():
        if key in loc_clean:
            return data

    # Dynamic fallback hierarchy for any city
    loc_title = normalize_city_name(location_name).title()
    return {
        "primary": loc_title,
        "district": loc_title,
        "state": state_region or "Gujarat",
        "nearby_areas": [loc_title],
        "priority_1_label": f"Priority 1: {loc_title} & Local Vicinity",
        "priority_2_label": f"Priority 2: {loc_title} District",
        "avoid_distant": [],
    }


def _safe_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def get_location_by_ip(user_ip: Optional[str] = None, ipinfo_token: Optional[str] = None) -> Dict[str, Any]:
    """Detect real IP location. Priority: ipinfo.io (with IPINFO_TOKEN) → ip-api.com → ipapi.co."""
    token_to_use = (ipinfo_token or os.getenv("IPINFO_TOKEN") or "").strip()
    ip_part = (user_ip or "").strip()

    # ── 1. ipinfo.io with token (HIGHEST PRIORITY — most accurate with token)
    if token_to_use:
        try:
            url = (
                f"https://ipinfo.io/{ip_part}/json?token={token_to_use}"
                if ip_part else
                f"https://ipinfo.io/json?token={token_to_use}"
            )
            response = requests.get(url, timeout=TIMEOUT, headers=REQUEST_HEADERS)
            if response.status_code == 200:
                data = response.json()
                raw_city = data.get("city")
                if raw_city and "bogon" not in str(data.get("ip", "")):
                    clean_city = normalize_city_name(raw_city) or "Rajkot"
                    loc = str(data.get("loc") or "22.3039,70.8022").split(",")
                    country_code = data.get("country", "IN")
                    country_map = {"IN": "India", "US": "United States", "GB": "United Kingdom", "AU": "Australia"}
                    country_name = country_map.get(country_code, country_code)
                    region_clean = normalize_city_name(data.get("region")) or "Gujarat"
                    return {
                        "ip": data.get("ip", "Auto-detected"),
                        "city": clean_city,
                        "region": region_clean,
                        "country": country_name,
                        "country_code": country_code,
                        "loc_string": f"{clean_city}, {region_clean}, {country_name}",
                        "lat": _safe_float(loc[0] if loc else None, 22.3039),
                        "lon": _safe_float(loc[1] if len(loc) > 1 else None, 70.8022),
                        "postal": data.get("postal", ""),
                        "timezone": data.get("timezone", ""),
                        "org": data.get("org", ""),
                        "is_fallback": False,
                        "api_provider": "ipinfo.io API ✅ (Token Active)",
                    }
        except Exception as exc:
            logger.warning("ipinfo.io (token) failed: %s", exc)

    # ── 2. ip-api.com — reliable free JSON API
    try:
        url = f"http://ip-api.com/json/{ip_part}" if ip_part else "http://ip-api.com/json"
        response = requests.get(url, timeout=TIMEOUT, headers=REQUEST_HEADERS,
                                params={"fields": "status,message,country,countryCode,regionName,city,lat,lon,query"})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("city"):
                clean_city = normalize_city_name(data.get("city")) or "Rajkot"
                region_clean = normalize_city_name(data.get("regionName")) or "Gujarat"
                return {
                    "ip": data.get("query", "Auto-detected"),
                    "city": clean_city,
                    "region": region_clean,
                    "country": data.get("country", "India"),
                    "country_code": data.get("countryCode", "IN"),
                    "loc_string": f"{clean_city}, {region_clean}, {data.get('country')}",
                    "lat": _safe_float(data.get("lat"), 22.3039),
                    "lon": _safe_float(data.get("lon"), 70.8022),
                    "is_fallback": False,
                    "api_provider": "ip-api.com API",
                }
    except Exception as exc:
        logger.warning("ip-api.com failed: %s", exc)

    # ── 3. ipapi.co
    try:
        url = f"https://ipapi.co/{ip_part}/json/" if ip_part else "https://ipapi.co/json/"
        response = requests.get(url, timeout=TIMEOUT, headers=REQUEST_HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data.get("city"):
                clean_city = normalize_city_name(data.get("city")) or "Rajkot"
                region_clean = normalize_city_name(data.get("region")) or "Gujarat"
                return {
                    "ip": data.get("ip", "Auto-detected"),
                    "city": clean_city,
                    "region": region_clean,
                    "country": data.get("country_name", "India"),
                    "country_code": data.get("country_code", "IN"),
                    "loc_string": f"{clean_city}, {region_clean}, {data.get('country_name')}",
                    "lat": _safe_float(data.get("latitude"), 22.3039),
                    "lon": _safe_float(data.get("longitude"), 70.8022),
                    "is_fallback": False,
                    "api_provider": "ipapi.co API",
                }
    except Exception as exc:
        logger.warning("ipapi.co failed: %s", exc)

    logger.warning("All location APIs failed; using Rajkot fallback.")
    return DEFAULT_LOCATION.copy()


def format_location_info(loc_data: Dict[str, Any], search_type: str = "city") -> Dict[str, Any]:
    """Normalize location fields for the UI and news search."""
    city = normalize_city_name(loc_data.get("city")) or "Rajkot"
    region = normalize_city_name(loc_data.get("region")) or "Gujarat"
    country = loc_data.get("country") or "India"
    is_city = str(search_type).lower().startswith("city")
    search_target = city if is_city else region
    hierarchy = get_location_hierarchy(city, region)

    return {
        "ip_address": loc_data.get("ip", "Auto-detected"),
        "detected_city": city,
        "region_state": region,
        "country": country,
        "country_code": loc_data.get("country_code", "IN"),
        "postal": loc_data.get("postal", ""),
        "timezone": loc_data.get("timezone", ""),
        "org": loc_data.get("org", ""),
        "search_type": "City-based News" if is_city else "Region-based News",
        "location_used_for_search": search_target,
        "search_description": f"{city}, {region}" if is_city else f"{region}, {country}",
        "lat": loc_data.get("lat"),
        "lon": loc_data.get("lon"),
        "api_provider": loc_data.get("api_provider", "Location IP API"),
        "is_fallback": loc_data.get("is_fallback", False),
        "hierarchy": hierarchy,
    }
