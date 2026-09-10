"""
services/weather.py — Agricultural Weather Advisory Service
============================================================
Architecture:
  1. STRUCTURED STORED DATA — a curated table of typical seasonal climate
     conditions for 30+ Indian cities/districts.  Clearly labelled as
     stored/typical data, NOT live measurements.
  2. IBM GRANITE AI — generates a seasonal farming advisory using the
     structured data + RAG context.  Never claims to provide live weather.
  3. MODULAR — live data can be plugged in later (IBM Environmental
     Intelligence Suite or any IBM Cloud-managed source) by replacing
     `_get_location_data()` without changing any other logic.

NO external API calls are made.
Open-Meteo and all third-party weather APIs are permanently excluded.

Supported languages: en (English), hi (Hindi), te (Telugu)
"""

import datetime

# ── Structured seasonal climate data for Indian locations ─────────────────────
# This is stored/typical data — NOT live observations.
# Source: IMD climatological normals and state agriculture departments.
# Format: location_key → list of 12 monthly records (Jan–Dec)
# Each record: temp_min_c, temp_max_c, humidity_pct, rainfall_typical_mm, condition

_SEASONAL_DATA: dict[str, dict] = {
    # ── Telangana ──────────────────────────────────────────────────────────────
    "warangal": {
        "state": "Telangana", "region": "Deccan Plateau",
        "elevation_m": 299, "annual_rainfall_mm": 1000,
        "major_crops": "Rice, Cotton, Maize, Turmeric",
        "soil": "Mixed red and black cotton soil",
        "months": [
            {"month": "Jan", "tmin": 14, "tmax": 29, "humidity": 65, "rain_mm": 10,  "condition": "Cool and dry"},
            {"month": "Feb", "tmin": 17, "tmax": 33, "humidity": 58, "rain_mm": 12,  "condition": "Warm and dry"},
            {"month": "Mar", "tmin": 22, "tmax": 38, "humidity": 48, "rain_mm": 14,  "condition": "Hot and dry"},
            {"month": "Apr", "tmin": 26, "tmax": 41, "humidity": 43, "rain_mm": 20,  "condition": "Very hot"},
            {"month": "May", "tmin": 27, "tmax": 42, "humidity": 46, "rain_mm": 45,  "condition": "Pre-monsoon hot"},
            {"month": "Jun", "tmin": 25, "tmax": 36, "humidity": 68, "rain_mm": 110, "condition": "Monsoon onset"},
            {"month": "Jul", "tmin": 23, "tmax": 30, "humidity": 82, "rain_mm": 180, "condition": "Peak monsoon"},
            {"month": "Aug", "tmin": 23, "tmax": 30, "humidity": 84, "rain_mm": 165, "condition": "Peak monsoon"},
            {"month": "Sep", "tmin": 22, "tmax": 31, "humidity": 80, "rain_mm": 145, "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 20, "tmax": 31, "humidity": 73, "rain_mm": 70,  "condition": "Post-monsoon"},
            {"month": "Nov", "tmin": 16, "tmax": 30, "humidity": 65, "rain_mm": 25,  "condition": "Cool and dry"},
            {"month": "Dec", "tmin": 13, "tmax": 27, "humidity": 66, "rain_mm": 12,  "condition": "Cool and dry"},
        ],
    },
    "hyderabad": {
        "state": "Telangana", "region": "Deccan Plateau",
        "elevation_m": 542, "annual_rainfall_mm": 790,
        "major_crops": "Rice, Maize, Cotton, Vegetables",
        "soil": "Red loam and black cotton soil",
        "months": [
            {"month": "Jan", "tmin": 15, "tmax": 28, "humidity": 66, "rain_mm": 8,   "condition": "Cool and pleasant"},
            {"month": "Feb", "tmin": 18, "tmax": 31, "humidity": 55, "rain_mm": 10,  "condition": "Warm and dry"},
            {"month": "Mar", "tmin": 22, "tmax": 36, "humidity": 44, "rain_mm": 14,  "condition": "Hot"},
            {"month": "Apr", "tmin": 26, "tmax": 39, "humidity": 40, "rain_mm": 22,  "condition": "Very hot"},
            {"month": "May", "tmin": 28, "tmax": 41, "humidity": 42, "rain_mm": 38,  "condition": "Pre-monsoon hot"},
            {"month": "Jun", "tmin": 25, "tmax": 34, "humidity": 65, "rain_mm": 100, "condition": "Monsoon onset"},
            {"month": "Jul", "tmin": 23, "tmax": 29, "humidity": 81, "rain_mm": 155, "condition": "Monsoon"},
            {"month": "Aug", "tmin": 23, "tmax": 29, "humidity": 83, "rain_mm": 145, "condition": "Peak monsoon"},
            {"month": "Sep", "tmin": 22, "tmax": 30, "humidity": 79, "rain_mm": 130, "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 19, "tmax": 30, "humidity": 70, "rain_mm": 70,  "condition": "Post-monsoon"},
            {"month": "Nov", "tmin": 15, "tmax": 28, "humidity": 63, "rain_mm": 22,  "condition": "Cool"},
            {"month": "Dec", "tmin": 13, "tmax": 26, "humidity": 65, "rain_mm": 8,   "condition": "Cool and dry"},
        ],
    },
    "nizamabad": {
        "state": "Telangana", "region": "Northern Telangana",
        "elevation_m": 384, "annual_rainfall_mm": 960,
        "major_crops": "Turmeric, Rice, Maize, Soybean",
        "soil": "Red and mixed soils",
        "months": [
            {"month": "Jan", "tmin": 13, "tmax": 29, "humidity": 67, "rain_mm": 10,  "condition": "Cool"},
            {"month": "Feb", "tmin": 16, "tmax": 33, "humidity": 58, "rain_mm": 10,  "condition": "Warm"},
            {"month": "Mar", "tmin": 21, "tmax": 38, "humidity": 47, "rain_mm": 15,  "condition": "Hot"},
            {"month": "Apr", "tmin": 26, "tmax": 42, "humidity": 42, "rain_mm": 22,  "condition": "Very hot"},
            {"month": "May", "tmin": 27, "tmax": 43, "humidity": 45, "rain_mm": 50,  "condition": "Hot, pre-monsoon"},
            {"month": "Jun", "tmin": 24, "tmax": 35, "humidity": 70, "rain_mm": 120, "condition": "Monsoon onset"},
            {"month": "Jul", "tmin": 23, "tmax": 30, "humidity": 83, "rain_mm": 190, "condition": "Peak monsoon"},
            {"month": "Aug", "tmin": 22, "tmax": 29, "humidity": 85, "rain_mm": 175, "condition": "Peak monsoon"},
            {"month": "Sep", "tmin": 22, "tmax": 31, "humidity": 82, "rain_mm": 155, "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 19, "tmax": 31, "humidity": 73, "rain_mm": 65,  "condition": "Post-monsoon"},
            {"month": "Nov", "tmin": 15, "tmax": 29, "humidity": 66, "rain_mm": 22,  "condition": "Cool"},
            {"month": "Dec", "tmin": 12, "tmax": 26, "humidity": 67, "rain_mm": 10,  "condition": "Cool and dry"},
        ],
    },
    # ── Andhra Pradesh ─────────────────────────────────────────────────────────
    "guntur": {
        "state": "Andhra Pradesh", "region": "Krishna-Guntur delta",
        "elevation_m": 31, "annual_rainfall_mm": 960,
        "major_crops": "Chilli, Cotton, Paddy, Tobacco",
        "soil": "Alluvial and black cotton soil",
        "months": [
            {"month": "Jan", "tmin": 18, "tmax": 30, "humidity": 72, "rain_mm": 12,  "condition": "Mild and dry"},
            {"month": "Feb", "tmin": 20, "tmax": 33, "humidity": 65, "rain_mm": 10,  "condition": "Warm"},
            {"month": "Mar", "tmin": 24, "tmax": 37, "humidity": 58, "rain_mm": 15,  "condition": "Hot"},
            {"month": "Apr", "tmin": 28, "tmax": 40, "humidity": 55, "rain_mm": 20,  "condition": "Very hot"},
            {"month": "May", "tmin": 30, "tmax": 42, "humidity": 57, "rain_mm": 45,  "condition": "Extremely hot"},
            {"month": "Jun", "tmin": 27, "tmax": 37, "humidity": 72, "rain_mm": 80,  "condition": "Monsoon onset"},
            {"month": "Jul", "tmin": 25, "tmax": 32, "humidity": 83, "rain_mm": 150, "condition": "Monsoon"},
            {"month": "Aug", "tmin": 25, "tmax": 32, "humidity": 84, "rain_mm": 155, "condition": "Monsoon"},
            {"month": "Sep", "tmin": 24, "tmax": 33, "humidity": 82, "rain_mm": 160, "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 22, "tmax": 33, "humidity": 76, "rain_mm": 170, "condition": "Post-monsoon rains"},
            {"month": "Nov", "tmin": 19, "tmax": 30, "humidity": 73, "rain_mm": 60,  "condition": "Receding monsoon"},
            {"month": "Dec", "tmin": 17, "tmax": 28, "humidity": 74, "rain_mm": 22,  "condition": "Mild"},
        ],
    },
    "kurnool": {
        "state": "Andhra Pradesh", "region": "Rayalaseema",
        "elevation_m": 268, "annual_rainfall_mm": 640,
        "major_crops": "Cotton, Groundnut, Sunflower, Maize",
        "soil": "Black cotton and red loam",
        "months": [
            {"month": "Jan", "tmin": 16, "tmax": 29, "humidity": 62, "rain_mm": 8,   "condition": "Cool and dry"},
            {"month": "Feb", "tmin": 19, "tmax": 33, "humidity": 52, "rain_mm": 8,   "condition": "Warm"},
            {"month": "Mar", "tmin": 24, "tmax": 38, "humidity": 42, "rain_mm": 12,  "condition": "Hot"},
            {"month": "Apr", "tmin": 27, "tmax": 41, "humidity": 40, "rain_mm": 20,  "condition": "Very hot and dry"},
            {"month": "May", "tmin": 29, "tmax": 43, "humidity": 44, "rain_mm": 40,  "condition": "Extremely hot"},
            {"month": "Jun", "tmin": 26, "tmax": 37, "humidity": 62, "rain_mm": 55,  "condition": "Pre-monsoon"},
            {"month": "Jul", "tmin": 23, "tmax": 32, "humidity": 75, "rain_mm": 110, "condition": "Monsoon"},
            {"month": "Aug", "tmin": 23, "tmax": 31, "humidity": 77, "rain_mm": 120, "condition": "Monsoon"},
            {"month": "Sep", "tmin": 22, "tmax": 32, "humidity": 74, "rain_mm": 120, "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 20, "tmax": 32, "humidity": 70, "rain_mm": 90,  "condition": "Post-monsoon"},
            {"month": "Nov", "tmin": 17, "tmax": 29, "humidity": 63, "rain_mm": 30,  "condition": "Cool"},
            {"month": "Dec", "tmin": 15, "tmax": 27, "humidity": 63, "rain_mm": 12,  "condition": "Cool and dry"},
        ],
    },
    # ── Maharashtra ─────────────────────────────────────────────────────────────
    "nagpur": {
        "state": "Maharashtra", "region": "Vidarbha",
        "elevation_m": 310, "annual_rainfall_mm": 1200,
        "major_crops": "Cotton, Soybean, Orange, Wheat",
        "soil": "Deep black cotton soil",
        "months": [
            {"month": "Jan", "tmin": 11, "tmax": 29, "humidity": 63, "rain_mm": 18,  "condition": "Cool and dry"},
            {"month": "Feb", "tmin": 14, "tmax": 32, "humidity": 52, "rain_mm": 18,  "condition": "Warm"},
            {"month": "Mar", "tmin": 19, "tmax": 38, "humidity": 39, "rain_mm": 16,  "condition": "Hot"},
            {"month": "Apr", "tmin": 25, "tmax": 42, "humidity": 32, "rain_mm": 12,  "condition": "Very hot"},
            {"month": "May", "tmin": 28, "tmax": 44, "humidity": 35, "rain_mm": 30,  "condition": "Extremely hot"},
            {"month": "Jun", "tmin": 25, "tmax": 37, "humidity": 62, "rain_mm": 165, "condition": "Monsoon onset"},
            {"month": "Jul", "tmin": 23, "tmax": 30, "humidity": 83, "rain_mm": 315, "condition": "Peak monsoon"},
            {"month": "Aug", "tmin": 23, "tmax": 30, "humidity": 84, "rain_mm": 300, "condition": "Peak monsoon"},
            {"month": "Sep", "tmin": 22, "tmax": 30, "humidity": 82, "rain_mm": 185, "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 19, "tmax": 31, "humidity": 71, "rain_mm": 70,  "condition": "Post-monsoon"},
            {"month": "Nov", "tmin": 14, "tmax": 29, "humidity": 60, "rain_mm": 25,  "condition": "Cool"},
            {"month": "Dec", "tmin": 10, "tmax": 27, "humidity": 60, "rain_mm": 15,  "condition": "Cool and dry"},
        ],
    },
    "pune": {
        "state": "Maharashtra", "region": "Pune",
        "elevation_m": 560, "annual_rainfall_mm": 720,
        "major_crops": "Jowar, Groundnut, Sugarcane, Onion, Grapes",
        "soil": "Black cotton and red laterite",
        "months": [
            {"month": "Jan", "tmin": 11, "tmax": 30, "humidity": 60, "rain_mm": 8,   "condition": "Pleasant and dry"},
            {"month": "Feb", "tmin": 13, "tmax": 33, "humidity": 50, "rain_mm": 8,   "condition": "Warm"},
            {"month": "Mar", "tmin": 18, "tmax": 37, "humidity": 38, "rain_mm": 10,  "condition": "Hot"},
            {"month": "Apr", "tmin": 22, "tmax": 39, "humidity": 33, "rain_mm": 18,  "condition": "Hot"},
            {"month": "May", "tmin": 24, "tmax": 38, "humidity": 38, "rain_mm": 38,  "condition": "Pre-monsoon"},
            {"month": "Jun", "tmin": 22, "tmax": 31, "humidity": 69, "rain_mm": 100, "condition": "Monsoon onset"},
            {"month": "Jul", "tmin": 20, "tmax": 27, "humidity": 86, "rain_mm": 175, "condition": "Peak monsoon"},
            {"month": "Aug", "tmin": 20, "tmax": 27, "humidity": 87, "rain_mm": 150, "condition": "Peak monsoon"},
            {"month": "Sep", "tmin": 20, "tmax": 29, "humidity": 83, "rain_mm": 110, "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 18, "tmax": 32, "humidity": 68, "rain_mm": 60,  "condition": "Post-monsoon"},
            {"month": "Nov", "tmin": 14, "tmax": 31, "humidity": 57, "rain_mm": 28,  "condition": "Cool and dry"},
            {"month": "Dec", "tmin": 11, "tmax": 29, "humidity": 55, "rain_mm": 10,  "condition": "Pleasant"},
        ],
    },
    # ── Punjab / Haryana ───────────────────────────────────────────────────────
    "ludhiana": {
        "state": "Punjab", "region": "Indo-Gangetic plain",
        "elevation_m": 244, "annual_rainfall_mm": 700,
        "major_crops": "Wheat, Rice, Maize, Potatoes",
        "soil": "Fertile alluvial soil",
        "months": [
            {"month": "Jan", "tmin": 4,  "tmax": 18, "humidity": 78, "rain_mm": 50,  "condition": "Cold and foggy"},
            {"month": "Feb", "tmin": 7,  "tmax": 21, "humidity": 72, "rain_mm": 48,  "condition": "Cold"},
            {"month": "Mar", "tmin": 12, "tmax": 26, "humidity": 60, "rain_mm": 38,  "condition": "Pleasant"},
            {"month": "Apr", "tmin": 18, "tmax": 34, "humidity": 47, "rain_mm": 22,  "condition": "Warm"},
            {"month": "May", "tmin": 23, "tmax": 39, "humidity": 38, "rain_mm": 22,  "condition": "Hot"},
            {"month": "Jun", "tmin": 26, "tmax": 41, "humidity": 48, "rain_mm": 52,  "condition": "Very hot, pre-monsoon"},
            {"month": "Jul", "tmin": 26, "tmax": 36, "humidity": 72, "rain_mm": 185, "condition": "Monsoon"},
            {"month": "Aug", "tmin": 25, "tmax": 34, "humidity": 76, "rain_mm": 168, "condition": "Monsoon"},
            {"month": "Sep", "tmin": 22, "tmax": 34, "humidity": 68, "rain_mm": 60,  "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 16, "tmax": 31, "humidity": 57, "rain_mm": 18,  "condition": "Pleasant"},
            {"month": "Nov", "tmin": 9,  "tmax": 25, "humidity": 66, "rain_mm": 12,  "condition": "Cool"},
            {"month": "Dec", "tmin": 5,  "tmax": 18, "humidity": 76, "rain_mm": 28,  "condition": "Cold"},
        ],
    },
    # ── Rajasthan ─────────────────────────────────────────────────────────────
    "jaipur": {
        "state": "Rajasthan", "region": "Semi-arid Rajasthan",
        "elevation_m": 431, "annual_rainfall_mm": 640,
        "major_crops": "Bajra, Mustard, Wheat, Jowar",
        "soil": "Sandy loam and arid soils",
        "months": [
            {"month": "Jan", "tmin": 8,  "tmax": 22, "humidity": 65, "rain_mm": 12,  "condition": "Cold and dry"},
            {"month": "Feb", "tmin": 12, "tmax": 26, "humidity": 55, "rain_mm": 12,  "condition": "Pleasant"},
            {"month": "Mar", "tmin": 17, "tmax": 32, "humidity": 40, "rain_mm": 8,   "condition": "Warm"},
            {"month": "Apr", "tmin": 23, "tmax": 38, "humidity": 28, "rain_mm": 5,   "condition": "Hot"},
            {"month": "May", "tmin": 27, "tmax": 42, "humidity": 26, "rain_mm": 12,  "condition": "Very hot"},
            {"month": "Jun", "tmin": 27, "tmax": 40, "humidity": 42, "rain_mm": 55,  "condition": "Hot, pre-monsoon"},
            {"month": "Jul", "tmin": 24, "tmax": 35, "humidity": 71, "rain_mm": 195, "condition": "Monsoon"},
            {"month": "Aug", "tmin": 23, "tmax": 32, "humidity": 76, "rain_mm": 175, "condition": "Monsoon"},
            {"month": "Sep", "tmin": 22, "tmax": 32, "humidity": 63, "rain_mm": 58,  "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 17, "tmax": 32, "humidity": 44, "rain_mm": 15,  "condition": "Post-monsoon"},
            {"month": "Nov", "tmin": 11, "tmax": 27, "humidity": 46, "rain_mm": 5,   "condition": "Cool"},
            {"month": "Dec", "tmin": 7,  "tmax": 22, "humidity": 57, "rain_mm": 8,   "condition": "Cold"},
        ],
    },
    # ── Uttar Pradesh ─────────────────────────────────────────────────────────
    "lucknow": {
        "state": "Uttar Pradesh", "region": "Central UP",
        "elevation_m": 125, "annual_rainfall_mm": 1020,
        "major_crops": "Wheat, Rice, Sugarcane, Potato",
        "soil": "Deep alluvial",
        "months": [
            {"month": "Jan", "tmin": 7,  "tmax": 19, "humidity": 82, "rain_mm": 28,  "condition": "Cold and foggy"},
            {"month": "Feb", "tmin": 9,  "tmax": 23, "humidity": 74, "rain_mm": 22,  "condition": "Cold"},
            {"month": "Mar", "tmin": 15, "tmax": 30, "humidity": 60, "rain_mm": 14,  "condition": "Pleasant"},
            {"month": "Apr", "tmin": 21, "tmax": 37, "humidity": 42, "rain_mm": 8,   "condition": "Warm"},
            {"month": "May", "tmin": 26, "tmax": 42, "humidity": 34, "rain_mm": 18,  "condition": "Very hot"},
            {"month": "Jun", "tmin": 28, "tmax": 41, "humidity": 50, "rain_mm": 65,  "condition": "Hot, pre-monsoon"},
            {"month": "Jul", "tmin": 26, "tmax": 34, "humidity": 78, "rain_mm": 220, "condition": "Monsoon"},
            {"month": "Aug", "tmin": 25, "tmax": 33, "humidity": 82, "rain_mm": 245, "condition": "Peak monsoon"},
            {"month": "Sep", "tmin": 24, "tmax": 32, "humidity": 77, "rain_mm": 180, "condition": "Late monsoon"},
            {"month": "Oct", "tmin": 18, "tmax": 31, "humidity": 64, "rain_mm": 40,  "condition": "Post-monsoon"},
            {"month": "Nov", "tmin": 11, "tmax": 27, "humidity": 64, "rain_mm": 12,  "condition": "Cool"},
            {"month": "Dec", "tmin": 7,  "tmax": 22, "humidity": 76, "rain_mm": 16,  "condition": "Cold"},
        ],
    },
}

# Alias map for fuzzy location lookup
_LOCATION_ALIASES: dict[str, str] = {
    "telangana":        "warangal",
    "t.s.":             "hyderabad",
    "ts":               "hyderabad",
    "nizam":            "nizamabad",
    "ap":               "guntur",
    "andhra":           "guntur",
    "andhra pradesh":   "guntur",
    "rayalaseema":      "kurnool",
    "vidarbha":         "nagpur",
    "maharashtra":      "pune",
    "punjab":           "ludhiana",
    "haryana":          "ludhiana",
    "rajasthan":        "jaipur",
    "up":               "lucknow",
    "uttar pradesh":    "lucknow",
}

# ── Indian season detection ────────────────────────────────────────────────────
_MONTH_TO_SEASON = {
    1:  ("Rabi",   "Winter/Rabi season — cool and dry; ideal for wheat, mustard, gram."),
    2:  ("Rabi",   "Late Rabi — wheat heading season; watch for rust and aphids."),
    3:  ("Zaid",   "Summer/Zaid season starting — consider short-duration vegetables."),
    4:  ("Zaid",   "Summer/Zaid peak — irrigate frequently; protect crops from heat stress."),
    5:  ("Zaid",   "Pre-monsoon summer — prepare fields; repair bunds before June."),
    6:  ("Kharif", "Monsoon onset — Kharif sowing time; rice, maize, cotton, groundnut."),
    7:  ("Kharif", "Kharif growing — ensure drainage; monitor for fungal diseases."),
    8:  ("Kharif", "Peak Kharif — high rainfall expected; pest pressure increases."),
    9:  ("Kharif", "Late Kharif — prepare for harvest; watch post-harvest rain damage."),
    10: ("Rabi",   "Kharif harvest / Rabi land preparation — start sowing wheat, gram."),
    11: ("Rabi",   "Early Rabi — wheat sowing complete; apply basal fertilizers."),
    12: ("Rabi",   "Rabi growing — cold nights; protect nurseries from frost."),
}

# Season-specific farming tips
_SEASON_TIPS: dict[str, list[str]] = {
    "Kharif": [
        "Ensure field drainage channels are clear to prevent waterlogging.",
        "Monitor crops weekly for Fall Armyworm (maize), Brown Plant Hopper (rice), and bollworm (cotton).",
        "Apply nitrogen fertilizer in split doses — avoid heavy doses during heavy rainfall.",
        "High humidity (>80%) increases risk of fungal diseases; spray preventive fungicide if needed.",
        "Avoid pesticide spray before expected rain — wait for dry periods of at least 6 hours.",
    ],
    "Rabi": [
        "Irrigate wheat at crown root initiation (21 DAS), jointing, heading, and grain-filling stages.",
        "Watch for yellow/brown rust in wheat — apply Propiconazole at first sign.",
        "Protect nurseries from frost below 5°C using plastic mulch or light irrigation.",
        "Apply phosphorus and potassium as basal dose before sowing.",
        "Aphid pressure increases in cool dry conditions — monitor mustard and wheat.",
    ],
    "Zaid": [
        "Irrigate frequently — every 4–6 days for vegetables during peak summer.",
        "Apply mulch (dry straw or plastic) to retain soil moisture and reduce evaporation.",
        "Avoid transplanting between 11 AM and 3 PM on hot days.",
        "Use drip irrigation for watermelon, cucumber, and muskmelon.",
        "Heat stress above 38°C — foliar spray of potassium nitrate (0.5%) helps recovery.",
    ],
}


def _find_location(location: str) -> dict | None:
    """
    Look up stored weather data for the given location.
    Returns the location dict or None if not found.
    """
    loc_lower = location.lower().strip()

    # Direct key match
    for key in _SEASONAL_DATA:
        if key in loc_lower or loc_lower in key:
            return {**_SEASONAL_DATA[key], "location_key": key}

    # Alias lookup
    for alias, key in _LOCATION_ALIASES.items():
        if alias in loc_lower:
            return {**_SEASONAL_DATA[key], "location_key": key}

    return None


def _build_weather_prompt(
    location: str,
    season: str,
    month_ctx: str,
    month_data: dict | None,
    region_info: str,
    language: str,
) -> str:
    """Build the Granite prompt for weather-based farming advice."""
    _LANG_NAMES = {"en": "English", "hi": "Hindi (हिंदी)", "te": "Telugu (తెలుగు)"}
    lang_name = _LANG_NAMES.get(language, "English")

    if month_data:
        climate_block = (
            f"Typical conditions for {location} this month:\n"
            f"  Temperature: {month_data['tmin']}°C to {month_data['tmax']}°C\n"
            f"  Humidity: ~{month_data['humidity']}%\n"
            f"  Typical rainfall: ~{month_data['rain_mm']} mm\n"
            f"  General condition: {month_data['condition']}"
        )
    else:
        climate_block = f"Seasonal context: {month_ctx}"

    region_block = f"\nRegion farming context: {region_info}" if region_info else ""

    return (
        "You are an AI Smart Farming Advisor.\n"
        f"Answer completely in {lang_name}.\n"
        "Give practical, seasonal farming advice.\n"
        "Do NOT claim to provide live or real-time weather data.\n"
        "Be concise and actionable for a small/medium Indian farmer.\n\n"
        f"Location: {location}\n"
        f"Current Indian agricultural season: {season}\n"
        f"{climate_block}"
        f"{region_block}\n\n"
        "Please provide:\n"
        "1. What farming activities are most important right now for this season.\n"
        "2. Key weather-related risks to watch for this season.\n"
        "3. Two or three specific actionable steps the farmer should take this week.\n\n"
        "ANSWER:"
    )


def get_weather(location: str, language: str = "en") -> dict:
    """
    Return seasonal weather advisory for the given location.

    Data hierarchy:
    1. If location matches stored dataset → return that location's typical
       monthly climate data (clearly labelled as stored/typical).
    2. Always generate IBM Granite seasonal farming advisory.
    3. Always include notice that this is NOT live data.

    The service is modular: a live IBM-connected source can be plugged in
    by adding a live-data path in _find_location() without changing any
    other code.

    Args:
        location: City / district / state name.
        language: ISO code — 'en', 'hi', or 'te'.

    Returns:
        dict with keys: location, season, month, month_context, advisory_source,
        tips, notice, stored_data (if found), ai_advisory, advice
    """
    if not location or not location.strip():
        return {"error": "Location name is required."}

    location = location.strip()
    today    = datetime.date.today()
    month_idx = today.month - 1   # 0-based for monthly array

    season, month_ctx = _MONTH_TO_SEASON.get(
        today.month,
        ("Kharif", "Growing season — monitor crops regularly.")
    )
    tips = _SEASON_TIPS.get(season, [])

    # Try to find stored climate data for this location
    loc_data   = _find_location(location)
    month_data = None
    region_info = ""

    if loc_data:
        month_data  = loc_data["months"][month_idx]
        region_info = (
            f"{loc_data.get('state','')} — {loc_data.get('region','')}. "
            f"Major crops: {loc_data.get('major_crops','')}. "
            f"Soil: {loc_data.get('soil','')}. "
            f"Annual rainfall: {loc_data.get('annual_rainfall_mm','')} mm."
        )

    # Call IBM Granite for AI advisory
    granite_advice = ""
    granite_error  = ""
    try:
        from services.granite import call_granite   # type: ignore
        from rag import retrieve                    # type: ignore

        prompt      = _build_weather_prompt(location, season, month_ctx, month_data, region_info, language)
        rag_context = retrieve(f"weather farming {season} {location}")
        full_prompt = (
            f"{prompt}\n\n"
            f"Retrieved agricultural context (use if relevant):\n{rag_context}\n\nANSWER:"
        )
        granite_advice = call_granite(full_prompt, language=language)
    except Exception as exc:
        granite_error = str(exc)

    notice = (
        "⚠️ Live real-time weather data is not currently connected. "
        "Showing stored typical climate data for this location and IBM Granite AI seasonal advice. "
        "For live weather, please check the India Meteorological Department (IMD) website or Kisan Suvidha app."
    )

    result: dict = {
        "location":        location,
        "season":          season,
        "month":           today.month,
        "month_context":   month_ctx,
        "advisory_source": "IBM Granite AI + Stored Climate Data (typical/seasonal, no live data)",
        "tips":            tips,
        "notice":          notice,
        "data_type":       "seasonal_advisory",
    }

    # Include stored climate data if found
    if loc_data and month_data:
        result["stored_data"] = {
            "state":             loc_data.get("state", ""),
            "region":            loc_data.get("region", ""),
            "data_label":        "Typical monthly climate (stored data — NOT live)",
            "month_name":        month_data["month"],
            "temp_min_c":        month_data["tmin"],
            "temp_max_c":        month_data["tmax"],
            "humidity_pct":      month_data["humidity"],
            "typical_rain_mm":   month_data["rain_mm"],
            "condition":         month_data["condition"],
            "annual_rainfall_mm": loc_data.get("annual_rainfall_mm"),
            "major_crops":       loc_data.get("major_crops", ""),
            "soil_type":         loc_data.get("soil", ""),
        }
        result["region_info"] = region_info
    else:
        result["stored_data"] = None
        result["note"] = (
            f"No stored climate data is available for '{location}'. "
            "Showing general seasonal advisory only."
        )

    if granite_advice:
        result["advice"]      = granite_advice
        result["ai_advisory"] = granite_advice
    elif granite_error:
        fallback = f"Season: {season}. {month_ctx}"
        if month_data:
            fallback += (
                f" Typical temperature: {month_data['tmin']}-{month_data['tmax']}°C, "
                f"humidity ~{month_data['humidity']}%."
            )
        result["advice"]       = fallback
        result["ai_advisory"]  = fallback
        result["granite_error"] = granite_error
    else:
        result["advice"]      = f"Season: {season}. {month_ctx}"
        result["ai_advisory"] = result["advice"]

    return result
