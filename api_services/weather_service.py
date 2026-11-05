"""
Weather Service (🌤️ 4th API: Open-Meteo)
Geocodes a city/region name, then fetches live weather for those coordinates.
"""

import logging
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIMEOUT = 8
REQUEST_HEADERS = {"User-Agent": "CityRegionNewsSummarizer/1.0"}

WEATHER_CODE_MAP = {
    0: ("Clear Sky", "Clear and sunny."),
    1: ("Mainly Clear", "Mostly sunny with light clouds."),
    2: ("Partly Cloudy", "Scattered clouds."),
    3: ("Overcast", "Fully overcast sky."),
    45: ("Foggy", "Foggy conditions."),
    48: ("Rime Fog", "Depositing rime fog."),
    51: ("Light Drizzle", "Light rain showers."),
    53: ("Moderate Drizzle", "Moderate rain showers."),
    55: ("Heavy Drizzle", "Dense drizzle."),
    61: ("Slight Rain", "Light rainfall."),
    63: ("Moderate Rain", "Steady rainfall."),
    65: ("Heavy Rain", "Heavy rainfall alert."),
    71: ("Slight Snow", "Light snowfall."),
    73: ("Moderate Snow", "Moderate snowfall."),
    75: ("Heavy Snow", "Heavy snowfall warning."),
    80: ("Rain Showers", "Passing rain showers."),
    81: ("Moderate Rain Showers", "Moderate showers."),
    82: ("Violent Rain Showers", "Heavy rain storm warning."),
    95: ("Thunderstorm", "Thunderstorm in the area."),
    96: ("Thunderstorm with Hail", "Severe thunderstorm with hail."),
}


def geocode_place(place_name: str) -> Optional[Tuple[float, float, str]]:
    """Resolve a city/region name to latitude/longitude via Open-Meteo Geocoding."""
    if not place_name:
        return None
    try:
        url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={quote(place_name)}&count=1&language=en&format=json"
        )
        response = requests.get(url, timeout=TIMEOUT, headers=REQUEST_HEADERS)
        if response.status_code == 200:
            results = response.json().get("results") or []
            if results:
                item = results[0]
                label = ", ".join(
                    part for part in [item.get("name"), item.get("admin1"), item.get("country")] if part
                )
                return float(item["latitude"]), float(item["longitude"]), label
    except Exception as exc:
        logger.warning("Geocoding failed for %s: %s", place_name, exc)
    return None


def get_live_weather(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    location_name: str = "Location",
) -> Dict[str, Any]:
    """Fetch live weather. Geocodes location_name when coordinates are missing."""
    resolved_name = location_name
    if lat is None or lon is None:
        geo = geocode_place(location_name)
        if geo:
            lat, lon, resolved_name = geo
        else:
            lat, lon = 23.0225, 72.5714

    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            "&timezone=auto"
        )
        response = requests.get(url, timeout=TIMEOUT, headers=REQUEST_HEADERS)
        if response.status_code == 200:
            current = response.json().get("current", {})
            code = current.get("weather_code", 0)
            condition_title, condition_desc = WEATHER_CODE_MAP.get(
                code, ("Fair Weather", "Normal weather conditions.")
            )
            return {
                "success": True,
                "temperature": f"{current.get('temperature_2m', 28.0)}°C",
                "condition": condition_title,
                "description": condition_desc,
                "humidity": f"{current.get('relative_humidity_2m', 65)}%",
                "wind_speed": f"{current.get('wind_speed_10m', 12.0)} km/h",
                "location": resolved_name,
                "lat": lat,
                "lon": lon,
                "api_provider": "Open-Meteo Weather API",
            }
    except Exception as exc:
        logger.warning("Weather fetch failed: %s", exc)

    return {
        "success": False,
        "temperature": "—",
        "condition": "Unavailable",
        "description": "Live weather could not be retrieved.",
        "humidity": "—",
        "wind_speed": "—",
        "location": location_name,
        "lat": lat,
        "lon": lon,
        "api_provider": "Weather unavailable",
    }
