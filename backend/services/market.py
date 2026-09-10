"""
services/market.py — Mandi / Market Price Service
===================================================

Data sources:
  1. Government of India MSP (Minimum Support Price) 2024-25 — floor price for 23 crops.
  2. Structured sample mandi price data — representative prices for major markets.
     CLEARLY LABELLED as stored/sample data, NOT live prices.
  3. IBM Granite AI seasonal market commentary.

NO external API calls are made.
data.gov.in, AGMARKNET, and all external market APIs are permanently excluded.

Live market data is not currently connected.
The interface clearly states "Showing stored sample market data" for all price displays.

A live IBM Cloud–connected data source can be plugged in later via the
`_get_live_prices()` function without changing the rest of the service.
"""

import os
import datetime

# ── Structured sample mandi price data ───────────────────────────────────────
# Representative prices from major Indian mandis — 2024-25 season.
# Source: APMC annual reports and agricultural extension bulletins.
# IMPORTANT: This is stored sample data, NOT live mandi prices.
# Live prices fluctuate daily. Check e-NAM, local APMC, or Agri Bazaar for live prices.
# Prices in ₹ per Quintal (100 kg) unless noted.
# Fields: min_price, max_price, modal_price, unit, market, state, season, date_label

SAMPLE_MANDI_DATA: dict[str, list[dict]] = {
    # ── Cereals ──────────────────────────────────────────────────────────────
    "rice": [
        {"market": "Warangal", "state": "Telangana", "min": 2200, "max": 2550, "modal": 2350,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Oct-Nov 2024"},
        {"market": "Nizamabad", "state": "Telangana", "min": 2250, "max": 2600, "modal": 2400,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Oct-Nov 2024"},
        {"market": "Nellore", "state": "Andhra Pradesh", "min": 2300, "max": 2700, "modal": 2450,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Oct-Nov 2024"},
    ],
    "wheat": [
        {"market": "Amritsar", "state": "Punjab", "min": 2200, "max": 2400, "modal": 2275,
         "unit": "Quintal", "season": "Rabi 2024", "date_label": "Apr-May 2024"},
        {"market": "Ludhiana", "state": "Punjab", "min": 2180, "max": 2420, "modal": 2290,
         "unit": "Quintal", "season": "Rabi 2024", "date_label": "Apr-May 2024"},
        {"market": "Hapur", "state": "Uttar Pradesh", "min": 2150, "max": 2380, "modal": 2270,
         "unit": "Quintal", "season": "Rabi 2024", "date_label": "Apr-May 2024"},
    ],
    "maize": [
        {"market": "Warangal", "state": "Telangana", "min": 1900, "max": 2200, "modal": 2050,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Sep-Oct 2024"},
        {"market": "Karimnagar", "state": "Telangana", "min": 1950, "max": 2250, "modal": 2080,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Sep-Oct 2024"},
    ],
    # ── Vegetables ───────────────────────────────────────────────────────────
    "tomato": [
        {"market": "Kurnool", "state": "Andhra Pradesh", "min": 400, "max": 1800, "modal": 900,
         "unit": "Quintal", "season": "Rabi 2024", "date_label": "Dec 2024 - Jan 2025",
         "note": "Tomato prices vary widely by season — low in peak supply, high in lean season."},
        {"market": "Warangal", "state": "Telangana", "min": 500, "max": 2000, "modal": 1000,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Aug-Oct 2024"},
        {"market": "Pune", "state": "Maharashtra", "min": 600, "max": 2500, "modal": 1200,
         "unit": "Quintal", "season": "Mixed", "date_label": "2024"},
    ],
    "potato": [
        {"market": "Agra", "state": "Uttar Pradesh", "min": 800, "max": 1200, "modal": 1000,
         "unit": "Quintal", "season": "Rabi 2024", "date_label": "Mar-Apr 2024"},
        {"market": "Kanpur", "state": "Uttar Pradesh", "min": 750, "max": 1150, "modal": 950,
         "unit": "Quintal", "season": "Rabi 2024", "date_label": "Mar-Apr 2024"},
    ],
    "onion": [
        {"market": "Lasalgaon", "state": "Maharashtra", "min": 600, "max": 2000, "modal": 1100,
         "unit": "Quintal", "season": "Rabi 2024", "date_label": "Mar-Jun 2024",
         "note": "Lasalgaon is Asia's largest onion market. Prices vary sharply by supply."},
        {"market": "Bellary", "state": "Karnataka", "min": 700, "max": 1900, "modal": 1200,
         "unit": "Quintal", "season": "2024", "date_label": "2024"},
    ],
    # ── Pulses ───────────────────────────────────────────────────────────────
    "arhar": [
        {"market": "Gulbarga", "state": "Karnataka", "min": 7000, "max": 8200, "modal": 7550,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Dec 2024 - Jan 2025"},
        {"market": "Nanded", "state": "Maharashtra", "min": 6900, "max": 8000, "modal": 7400,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Dec 2024 - Jan 2025"},
    ],
    "gram": [
        {"market": "Indore", "state": "Madhya Pradesh", "min": 5200, "max": 6000, "modal": 5500,
         "unit": "Quintal", "season": "Rabi 2024", "date_label": "Mar-Apr 2024"},
        {"market": "Jaipur", "state": "Rajasthan", "min": 5300, "max": 6100, "modal": 5600,
         "unit": "Quintal", "season": "Rabi 2024", "date_label": "Mar-Apr 2024"},
    ],
    # ── Oilseeds ─────────────────────────────────────────────────────────────
    "groundnut": [
        {"market": "Kurnool", "state": "Andhra Pradesh", "min": 6200, "max": 7500, "modal": 6800,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Oct-Nov 2024"},
        {"market": "Junagadh", "state": "Gujarat", "min": 6000, "max": 7200, "modal": 6600,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Oct-Nov 2024"},
    ],
    "soybean": [
        {"market": "Indore", "state": "Madhya Pradesh", "min": 4600, "max": 5400, "modal": 4900,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Oct-Nov 2024"},
        {"market": "Nagpur", "state": "Maharashtra", "min": 4500, "max": 5300, "modal": 4800,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Oct-Nov 2024"},
    ],
    # ── Cash / Spices ─────────────────────────────────────────────────────────
    "cotton": [
        {"market": "Warangal", "state": "Telangana", "min": 6500, "max": 8000, "modal": 7200,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Nov-Dec 2024"},
        {"market": "Kurnool", "state": "Andhra Pradesh", "min": 6600, "max": 7900, "modal": 7100,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Nov-Dec 2024"},
        {"market": "Akola", "state": "Maharashtra", "min": 6800, "max": 8200, "modal": 7300,
         "unit": "Quintal", "season": "Kharif 2024", "date_label": "Nov-Dec 2024"},
    ],
    "chilli": [
        {"market": "Guntur", "state": "Andhra Pradesh", "min": 8000, "max": 22000, "modal": 12000,
         "unit": "Quintal", "season": "2024", "date_label": "Feb-Apr 2024",
         "note": "Guntur is Asia's largest dry chilli market. Wide price variation by variety."},
        {"market": "Byadgi", "state": "Karnataka", "min": 10000, "max": 25000, "modal": 16000,
         "unit": "Quintal", "season": "2024", "date_label": "Feb-Apr 2024"},
    ],
    "turmeric": [
        {"market": "Nizamabad", "state": "Telangana", "min": 12000, "max": 22000, "modal": 15000,
         "unit": "Quintal", "season": "2024", "date_label": "Jan-Mar 2024",
         "note": "Nizamabad is one of India's largest turmeric markets."},
        {"market": "Erode", "state": "Tamil Nadu", "min": 13000, "max": 24000, "modal": 17000,
         "unit": "Quintal", "season": "2024", "date_label": "Jan-Mar 2024"},
    ],
    "sugarcane": [
        {"market": "Pune", "state": "Maharashtra", "min": 320, "max": 370, "modal": 340,
         "unit": "Quintal", "season": "2024-25", "date_label": "2024-25",
         "note": "Sugarcane is sold to mills at FRP (Fair and Remunerative Price), not open mandi."},
    ],
}

# ─── Government of India MSP (Minimum Support Price) — 2024-25 ───────────────
# Source: Cabinet Committee on Economic Affairs (CCEA), Government of India
# Ref: https://agricoop.nic.in/en/pressrelease/minimum-support-prices
# All prices in ₹ per Quintal (100 kg).
#
# MSP = guaranteed government floor price.
# IMPORTANT: MSP ≠ mandi/market price. Actual traded prices vary by state,
# season, grade, supply and demand.
MSP_DATA: dict[str, dict] = {
    # ── Cereals ──────────────────────────────────────────────────────────────
    "rice":    {"msp": 2300, "season": "Kharif 2024-25"},
    "wheat":   {"msp": 2275, "season": "Rabi 2024-25"},
    "maize":   {"msp": 2090, "season": "Kharif 2024-25"},
    "jowar":   {"msp": 3371, "season": "Kharif 2024-25"},
    "bajra":   {"msp": 2625, "season": "Kharif 2024-25"},
    "ragi":    {"msp": 4290, "season": "Kharif 2024-25"},
    "barley":  {"msp": 1735, "season": "Rabi 2024-25"},
    "oats":    {"msp": 2500, "season": "Rabi 2024-25"},
    # ── Pulses ───────────────────────────────────────────────────────────────
    "arhar":   {"msp": 7550, "season": "Kharif 2024-25"},
    "moong":   {"msp": 8682, "season": "Kharif 2024-25"},
    "urad":    {"msp": 7400, "season": "Kharif 2024-25"},
    "gram":    {"msp": 5440, "season": "Rabi 2024-25"},
    "masoor":  {"msp": 6425, "season": "Rabi 2024-25"},
    # ── Oilseeds ─────────────────────────────────────────────────────────────
    "groundnut":  {"msp": 6783, "season": "Kharif 2024-25"},
    "soybean":    {"msp": 4892, "season": "Kharif 2024-25"},
    "sunflower":  {"msp": 7280, "season": "Kharif 2024-25"},
    "sesame":     {"msp": 9267, "season": "Kharif 2024-25"},
    "mustard":    {"msp": 5950, "season": "Rabi 2024-25"},
    "linseed":    {"msp": 5940, "season": "Rabi 2024-25"},
    "castor":     {"msp": 6765, "season": "Kharif 2024-25"},
    # ── Cash Crops ───────────────────────────────────────────────────────────
    "cotton":     {"msp": 7121, "season": "Kharif 2024-25"},
    "jute":       {"msp": 5335, "season": "Kharif 2024-25"},
    "sugarcane":  {"msp": 340,  "season": "2024-25"},       # ₹/quintal FRP
    # ── Spice with MSP ───────────────────────────────────────────────────────
    "coriander seed": {"msp": 7000, "season": "Rabi 2024-25"},
}

# ─── Comprehensive product catalog ───────────────────────────────────────────
# Each entry: canonical_name → display_name, unit, category
PRODUCT_CATALOG: dict[str, dict] = {

    # ── VEGETABLES ──────────────────────────────────────────────────────────
    "tomato":           {"display": "Tomato",            "unit": "Quintal", "category": "vegetables"},
    "potato":           {"display": "Potato",            "unit": "Quintal", "category": "vegetables"},
    "onion":            {"display": "Onion",             "unit": "Quintal", "category": "vegetables"},
    "brinjal":          {"display": "Brinjal/Eggplant",  "unit": "Quintal", "category": "vegetables"},
    "cabbage":          {"display": "Cabbage",           "unit": "Quintal", "category": "vegetables"},
    "cauliflower":      {"display": "Cauliflower",       "unit": "Quintal", "category": "vegetables"},
    "carrot":           {"display": "Carrot",            "unit": "Quintal", "category": "vegetables"},
    "radish":           {"display": "Radish",            "unit": "Quintal", "category": "vegetables"},
    "beetroot":         {"display": "Beetroot",          "unit": "Quintal", "category": "vegetables"},
    "beans":            {"display": "Beans",             "unit": "Quintal", "category": "vegetables"},
    "french beans":     {"display": "French Beans",      "unit": "Quintal", "category": "vegetables"},
    "cluster beans":    {"display": "Cluster Beans",     "unit": "Quintal", "category": "vegetables"},
    "okra":             {"display": "Lady Finger/Okra",  "unit": "Quintal", "category": "vegetables"},
    "green peas":       {"display": "Green Peas",        "unit": "Quintal", "category": "vegetables"},
    "green chilli":     {"display": "Green Chilli",      "unit": "Quintal", "category": "vegetables"},
    "capsicum":         {"display": "Capsicum",          "unit": "Quintal", "category": "vegetables"},
    "bell pepper":      {"display": "Bell Pepper",       "unit": "Quintal", "category": "vegetables"},
    "bitter gourd":     {"display": "Bitter Gourd",      "unit": "Quintal", "category": "vegetables"},
    "bottle gourd":     {"display": "Bottle Gourd",      "unit": "Quintal", "category": "vegetables"},
    "ridge gourd":      {"display": "Ridge Gourd",       "unit": "Quintal", "category": "vegetables"},
    "snake gourd":      {"display": "Snake Gourd",       "unit": "Quintal", "category": "vegetables"},
    "sponge gourd":     {"display": "Sponge Gourd",      "unit": "Quintal", "category": "vegetables"},
    "ash gourd":        {"display": "Ash Gourd",         "unit": "Quintal", "category": "vegetables"},
    "pumpkin":          {"display": "Pumpkin",           "unit": "Quintal", "category": "vegetables"},
    "cucumber":         {"display": "Cucumber",          "unit": "Quintal", "category": "vegetables"},
    "drumstick":        {"display": "Drumstick",         "unit": "Quintal", "category": "vegetables"},
    "spinach":          {"display": "Spinach",           "unit": "Quintal", "category": "vegetables"},
    "amaranth":         {"display": "Amaranth",          "unit": "Quintal", "category": "vegetables"},
    "coriander":        {"display": "Coriander Leaves",  "unit": "Quintal", "category": "vegetables"},
    "mint":             {"display": "Mint",              "unit": "Quintal", "category": "vegetables"},
    "fenugreek leaves": {"display": "Fenugreek Leaves",  "unit": "Quintal", "category": "vegetables"},
    "curry leaves":     {"display": "Curry Leaves",      "unit": "Quintal", "category": "vegetables"},
    "sweet corn":       {"display": "Sweet Corn",        "unit": "Quintal", "category": "vegetables"},
    "garlic":           {"display": "Garlic",            "unit": "Quintal", "category": "vegetables"},
    "ginger":           {"display": "Ginger",            "unit": "Quintal", "category": "vegetables"},
    "sweet potato":     {"display": "Sweet Potato",      "unit": "Quintal", "category": "vegetables"},
    "raw banana":       {"display": "Raw Banana",        "unit": "Quintal", "category": "vegetables"},
    "raw mango":        {"display": "Raw Mango",         "unit": "Quintal", "category": "vegetables"},

    # ── FRUITS ────────────────────────────────────────────────────────────
    "apple":            {"display": "Apple",             "unit": "Quintal", "category": "fruits"},
    "banana":           {"display": "Banana",            "unit": "Quintal", "category": "fruits"},
    "mango":            {"display": "Mango",             "unit": "Quintal", "category": "fruits"},
    "orange":           {"display": "Orange",            "unit": "Quintal", "category": "fruits"},
    "mandarin":         {"display": "Mandarin",          "unit": "Quintal", "category": "fruits"},
    "lemon":            {"display": "Lemon",             "unit": "Quintal", "category": "fruits"},
    "papaya":           {"display": "Papaya",            "unit": "Quintal", "category": "fruits"},
    "pomegranate":      {"display": "Pomegranate",       "unit": "Quintal", "category": "fruits"},
    "grapes":           {"display": "Grapes",            "unit": "Quintal", "category": "fruits"},
    "watermelon":       {"display": "Watermelon",        "unit": "Quintal", "category": "fruits"},
    "muskmelon":        {"display": "Muskmelon",         "unit": "Quintal", "category": "fruits"},
    "guava":            {"display": "Guava",             "unit": "Quintal", "category": "fruits"},
    "pineapple":        {"display": "Pineapple",         "unit": "Quintal", "category": "fruits"},
    "jackfruit":        {"display": "Jackfruit",         "unit": "Quintal", "category": "fruits"},
    "custard apple":    {"display": "Custard Apple",     "unit": "Quintal", "category": "fruits"},
    "sapota":           {"display": "Sapota/Chikoo",     "unit": "Quintal", "category": "fruits"},
    "pears":            {"display": "Pears",             "unit": "Quintal", "category": "fruits"},
    "peach":            {"display": "Peach",             "unit": "Quintal", "category": "fruits"},
    "plum":             {"display": "Plum",              "unit": "Quintal", "category": "fruits"},
    "strawberry":       {"display": "Strawberry",        "unit": "Quintal", "category": "fruits"},
    "litchi":           {"display": "Litchi",            "unit": "Quintal", "category": "fruits"},
    "kiwi":             {"display": "Kiwi",              "unit": "Quintal", "category": "fruits"},
    "dragon fruit":     {"display": "Dragon Fruit",      "unit": "Quintal", "category": "fruits"},
    "avocado":          {"display": "Avocado",           "unit": "Quintal", "category": "fruits"},
    "coconut":          {"display": "Coconut",           "unit": "Nos",     "category": "fruits"},
    "amla":             {"display": "Amla",              "unit": "Quintal", "category": "fruits"},
    "fig":              {"display": "Fig",               "unit": "Quintal", "category": "fruits"},
    "dates":            {"display": "Dates",             "unit": "Quintal", "category": "fruits"},
    "ber":              {"display": "Ber/Indian Jujube", "unit": "Quintal", "category": "fruits"},

    # ── CEREALS ───────────────────────────────────────────────────────────
    "rice":             {"display": "Rice",              "unit": "Quintal", "category": "cereals"},
    "wheat":            {"display": "Wheat",             "unit": "Quintal", "category": "cereals"},
    "maize":            {"display": "Maize",             "unit": "Quintal", "category": "cereals"},
    "barley":           {"display": "Barley",            "unit": "Quintal", "category": "cereals"},
    "bajra":            {"display": "Bajra/Pearl Millet","unit": "Quintal", "category": "cereals"},
    "jowar":            {"display": "Jowar/Sorghum",     "unit": "Quintal", "category": "cereals"},
    "ragi":             {"display": "Ragi",              "unit": "Quintal", "category": "cereals"},
    "oats":             {"display": "Oats",              "unit": "Quintal", "category": "cereals"},

    # ── PULSES ────────────────────────────────────────────────────────────
    "gram":             {"display": "Gram/Chickpea",     "unit": "Quintal", "category": "pulses"},
    "arhar":            {"display": "Arhar/Tur Dal",     "unit": "Quintal", "category": "pulses"},
    "moong":            {"display": "Moong/Green Gram",  "unit": "Quintal", "category": "pulses"},
    "urad":             {"display": "Urad/Black Gram",   "unit": "Quintal", "category": "pulses"},
    "masoor":           {"display": "Masoor/Lentil",     "unit": "Quintal", "category": "pulses"},
    "peas":             {"display": "Peas",              "unit": "Quintal", "category": "pulses"},
    "rajma":            {"display": "Rajma",             "unit": "Quintal", "category": "pulses"},

    # ── OILSEEDS ──────────────────────────────────────────────────────────
    "groundnut":        {"display": "Groundnut",         "unit": "Quintal", "category": "oilseeds"},
    "soybean":          {"display": "Soybean",           "unit": "Quintal", "category": "oilseeds"},
    "sunflower":        {"display": "Sunflower",         "unit": "Quintal", "category": "oilseeds"},
    "sesame":           {"display": "Sesame/Til",        "unit": "Quintal", "category": "oilseeds"},
    "mustard":          {"display": "Mustard",           "unit": "Quintal", "category": "oilseeds"},
    "castor":           {"display": "Castor",            "unit": "Quintal", "category": "oilseeds"},
    "linseed":          {"display": "Linseed",           "unit": "Quintal", "category": "oilseeds"},

    # ── SPICES ────────────────────────────────────────────────────────────
    "chilli":           {"display": "Chilli",            "unit": "Quintal", "category": "spices"},
    "turmeric":         {"display": "Turmeric",          "unit": "Quintal", "category": "spices"},
    "cumin":            {"display": "Cumin",             "unit": "Quintal", "category": "spices"},
    "coriander seed":   {"display": "Coriander Seed",    "unit": "Quintal", "category": "spices"},
    "black pepper":     {"display": "Black Pepper",      "unit": "Quintal", "category": "spices"},
    "cardamom":         {"display": "Cardamom",          "unit": "Quintal", "category": "spices"},
    "clove":            {"display": "Clove",             "unit": "Quintal", "category": "spices"},
    "fennel":           {"display": "Fennel",            "unit": "Quintal", "category": "spices"},
    "fenugreek seed":   {"display": "Fenugreek Seed",    "unit": "Quintal", "category": "spices"},

    # ── CASH / OTHER ──────────────────────────────────────────────────────
    "cotton":           {"display": "Cotton",            "unit": "Quintal", "category": "other"},
    "sugarcane":        {"display": "Sugarcane",         "unit": "Quintal", "category": "other"},
    "tobacco":          {"display": "Tobacco",           "unit": "Quintal", "category": "other"},
    "jute":             {"display": "Jute",              "unit": "Quintal", "category": "other"},
    "tea":              {"display": "Tea",               "unit": "Kg",      "category": "other"},
    "coffee":           {"display": "Coffee",            "unit": "Quintal", "category": "other"},
    "rubber":           {"display": "Rubber",            "unit": "Quintal", "category": "other"},
}

# ─── Alias / normalisation map ─────────────────────────────────────────────
ALIASES: dict[str, str] = {
    # Vegetables
    "eggplant": "brinjal", "baingan": "brinjal", "vankai": "brinjal",
    "lady finger": "okra", "ladyfinger": "okra", "bhindi": "okra", "bendakaya": "okra",
    "potatoes": "potato", "aloo": "potato", "alugadda": "potato",
    "tomatoes": "tomato", "tamatar": "tomato", "tamata": "tomato", "tomata": "tomato",
    "onions": "onion", "pyaaz": "onion", "ullipayalu": "onion",
    "coriander leaves": "coriander", "dhania": "coriander", "kothimir": "coriander",
    "methi leaves": "fenugreek leaves", "menthulu aaku": "fenugreek leaves",
    "karela": "bitter gourd", "kakarakaya": "bitter gourd",
    "lauki": "bottle gourd", "soraikkai": "bottle gourd", "sorakaya": "bottle gourd",
    "tinda": "ash gourd",
    "bhopla": "pumpkin", "kaddu": "pumpkin", "gummadikaya": "pumpkin",
    "kheera": "cucumber", "dosakaya": "cucumber",
    "shimla mirch": "capsicum",
    "drumsticks": "drumstick", "murungakkai": "drumstick", "munagakaya": "drumstick",
    "palak": "spinach", "palakura": "spinach",
    "corn": "sweet corn", "makai": "sweet corn",
    "lehsun": "garlic", "vellulli": "garlic",
    "adrak": "ginger", "allam": "ginger",
    "shakarkand": "sweet potato", "chelagadda": "sweet potato",
    "kacha kela": "raw banana", "aratikaya": "raw banana",
    "kairi": "raw mango", "mamidikaya": "raw mango",
    # Fruits
    "apples": "apple", "seb": "apple",
    "bananas": "banana", "kela": "banana", "arati pandu": "banana",
    "mangoes": "mango", "aam": "mango", "mamidi pandu": "mango",
    "oranges": "orange", "santra": "orange",
    "nimbu": "lemon", "nimmakaya": "lemon",
    "papita": "papaya", "papayalu": "papaya",
    "anar": "pomegranate", "dalimba pandu": "pomegranate",
    "angoor": "grapes", "draksha": "grapes",
    "tarbuz": "watermelon", "puchcha kaya": "watermelon",
    "kharbooja": "muskmelon",
    "amrud": "guava", "jama pandu": "guava",
    "ananas": "pineapple",
    "kathal": "jackfruit", "panasa": "jackfruit",
    "sitaphal": "custard apple", "srikaya": "custard apple",
    "chiku": "sapota", "sapodilla": "sapota",
    "nashpati": "pears",
    "aadu": "peach",
    "alu bukhara": "plum",
    "lychee": "litchi",
    "nellikai": "amla", "usirikaya": "amla", "gooseberry": "amla",
    "khajur": "dates",
    "bor": "ber", "jujube": "ber", "regi pandu": "ber",
    "nariyal": "coconut", "kobbari": "coconut",
    # Cereals
    "paddy": "rice", "dhaan": "rice", "vari": "rice",
    "gehun": "wheat", "godhuma": "wheat",
    "makka": "maize", "makkai": "maize", "corn grain": "maize",
    "pearl millet": "bajra", "cambu": "bajra",
    "sorghum": "jowar", "jawar": "jowar",
    "finger millet": "ragi", "nachni": "ragi",
    # Pulses
    "chickpea": "gram", "chana": "gram", "senaga pappu": "gram",
    "arhar dal": "arhar", "tur dal": "arhar", "toor dal": "arhar",
    "toor": "arhar", "tur": "arhar", "pigeon pea": "arhar", "kandi pappu": "arhar",
    "red gram": "arhar",
    "green gram": "moong", "moong dal": "moong", "pesara pappu": "moong",
    "black gram": "urad", "urad dal": "urad", "minumulu": "urad",
    "masur dal": "masoor", "lentil": "masoor", "masoor dal": "masoor",
    "pea": "peas", "matar": "peas",
    "kidney bean": "rajma",
    # Oilseeds
    "peanut": "groundnut", "moongphali": "groundnut", "verusenaga": "groundnut",
    "soya": "soybean", "soya bean": "soybean",
    "sesame seed": "sesame", "til": "sesame", "nuvvulu": "sesame",
    "sarson": "mustard", "avalu": "mustard",
    "castor seed": "castor", "arandee": "castor",
    "flaxseed": "linseed",
    # Spices
    "chillies": "chilli", "chili": "chilli", "lal mirch": "chilli",
    "mirchi": "chilli", "mirch": "chilli",
    "dry chilli": "chilli", "red chilli": "chilli",
    "haldi": "turmeric", "pasupu": "turmeric",
    "jeera": "cumin", "jeerakam": "cumin",
    "coriander seeds": "coriander seed",
    "pepper": "black pepper",
    "elaichi": "cardamom",
    "lavang": "clove",
    "saunf": "fennel",
    "methi seed": "fenugreek seed", "methi dana": "fenugreek seed",
    "fenugreek seeds": "fenugreek seed",
    # Other
    "kapas": "cotton", "patti": "cotton",
    "ganna": "sugarcane",
    "tambaaku": "tobacco",
}


def get_product_info(product: str) -> dict | None:
    """
    Resolve a user-supplied product name to its catalog entry.
    Returns the catalog dict (with key added) or None if not found.
    """
    key = product.lower().strip()
    if key in PRODUCT_CATALOG:
        return {**PRODUCT_CATALOG[key], "key": key}
    resolved = ALIASES.get(key)
    if resolved and resolved in PRODUCT_CATALOG:
        return {**PRODUCT_CATALOG[resolved], "key": resolved}
    return None


def _build_market_prompt(product_key: str, display: str, category: str,
                         msp: int | None, msp_season: str | None,
                         state: str | None, language: str) -> str:
    """Build IBM Granite prompt for market price commentary."""
    _LANG_NAMES = {"en": "English", "hi": "Hindi (हिंदी)", "te": "Telugu (తెలుగు)"}
    lang_name = _LANG_NAMES.get(language, "English")

    msp_block = (
        f"Government MSP for {display}: ₹{msp}/quintal ({msp_season}). "
        "This is the government-guaranteed minimum floor price."
        if msp else
        f"{display} does not have a government MSP. "
        "Market price is determined by supply, demand, and season."
    )
    state_block = f"Target state/region: {state}." if state else "Region: General India."

    return (
        "You are an AI Smart Farming Advisor providing market price guidance.\n"
        f"Answer completely in {lang_name}.\n"
        "Do NOT invent specific live mandi prices — live market data is not available.\n"
        "Use the MSP and general seasonal market knowledge to give useful guidance.\n\n"
        f"Product: {display} (category: {category})\n"
        f"{msp_block}\n"
        f"{state_block}\n\n"
        "Please provide:\n"
        "1. Whether the current season is a good or difficult time to sell this product.\n"
        "2. General price range farmers typically receive (based on MSP or historical norms).\n"
        "3. One or two tips to get a better price at the mandi.\n\n"
        "ANSWER:"
    )


def _get_sample_mandi(product_key: str, state: str | None) -> list[dict]:
    """
    Return stored sample mandi price records for a product.
    Filtered by state if provided.
    Returns empty list if no sample data available.
    """
    records = SAMPLE_MANDI_DATA.get(product_key, [])
    if not records:
        return []
    if state:
        state_lower = state.lower().strip()
        filtered = [r for r in records if state_lower in r.get("state", "").lower()]
        if filtered:
            return filtered
    return records


def get_market_prices(crop: str, state: str | None = None, market: str | None = None,
                      language: str = "en") -> dict:
    """
    Return MSP + sample mandi data + IBM Granite market advisory.

    No external API calls are made.
    All price data is clearly labelled as stored/sample, NOT live.
    Live market data is not currently connected — clearly stated in 'notice' field.

    Returns:
        success          – True if product found
        msp_price        – government MSP or None
        mandi_data       – list of sample mandi records (stored, NOT live)
        ai_advisory      – Granite-generated market commentary
        notice           – disclaimer that this is stored data, not live
    """
    info = get_product_info(crop)
    if info is None:
        return {
            "success":    False,
            "error_type": "product_not_found",
            "product":    crop,
            "message":    (
                f"'{crop}' is not in the supported product catalog. "
                "Please check the product name or select from the category list."
            ),
        }

    product_key = info["key"]
    msp_entry   = MSP_DATA.get(product_key)
    msp_price   = msp_entry["msp"]   if msp_entry else None
    msp_season  = msp_entry["season"] if msp_entry else None

    # Get stored sample mandi data (not live)
    mandi_records = _get_sample_mandi(product_key, state)

    # Call IBM Granite for market commentary (centralized service)
    ai_advisory   = ""
    granite_error = ""
    try:
        from services.granite import call_granite   # type: ignore
        prompt      = _build_market_prompt(
            product_key, info["display"], info["category"],
            msp_price, msp_season, state, language,
        )
        ai_advisory = call_granite(prompt, language=language)
    except Exception as exc:
        granite_error = str(exc)

    notice = (
        "⚠️ Live mandi/market prices are not currently connected. "
        "Showing Government of India MSP (Minimum Support Price) and stored sample mandi data. "
        "For live prices, check e-NAM (enam.gov.in), Agri Bazaar, or your local APMC."
    )

    result: dict = {
        "success":     True,
        "price_type":  "msp_and_sample",
        "product":     product_key,
        "display":     info["display"],
        "category":    info["category"],
        "unit":        info["unit"],
        "notice":      notice,
        "data_source": "Govt. of India CCEA MSP 2024-25 + Stored Sample Mandi Data + IBM Granite AI",
        "data_label":  "Stored/sample data — NOT live market prices",
    }

    # MSP data
    if msp_price is not None:
        result["msp_price"]  = msp_price
        result["msp_season"] = msp_season
        result["has_msp"]    = True
    else:
        result["has_msp"]  = False
        result["msp_note"] = (
            f"{info['display']} does not have a government MSP. "
            "Price is determined by market supply and demand."
        )

    # Sample mandi data
    if mandi_records:
        result["mandi_data"] = [
            {
                "market":      r["market"],
                "state":       r["state"],
                "min_price":   r["min"],
                "max_price":   r["max"],
                "modal_price": r["modal"],
                "unit":        r.get("unit", "Quintal"),
                "season":      r.get("season", ""),
                "date_label":  r.get("date_label", ""),
                "note":        r.get("note", ""),
                "data_label":  "Sample data — NOT live",
            }
            for r in mandi_records
        ]
    else:
        result["mandi_data"] = []
        result["mandi_note"] = (
            f"No stored mandi price data is available for {info['display']}. "
            "Check e-NAM or your local APMC for current prices."
        )

    if state:
        result["state"] = state
    if market:
        result["market"] = market

    if ai_advisory:
        result["ai_advisory"] = ai_advisory
    elif granite_error:
        result["ai_advisory"] = (
            f"AI market advisory unavailable ({granite_error}). "
            "Check government MSP figures above and consult your local APMC mandi."
        )
        result["granite_error"] = granite_error
    else:
        result["ai_advisory"] = (
            "Consult your nearest APMC mandi or e-NAM portal for current market prices."
        )

    return result


def list_supported_products() -> dict:
    """Return the full product catalog grouped by category."""
    result: dict[str, list[dict]] = {}
    for key, info in PRODUCT_CATALOG.items():
        cat = info["category"]
        if cat not in result:
            result[cat] = []
        result[cat].append({"key": key, "display": info["display"]})
    return result


def search_products(query: str, limit: int = 10) -> list[dict]:
    """
    Search the catalog for products matching the query string.
    Returns up to `limit` matches with key, display, and category.
    """
    query = query.lower().strip()
    if not query:
        return []

    matches = []
    seen    = set()

    for key, info in PRODUCT_CATALOG.items():
        if key.startswith(query) and key not in seen:
            matches.append({"key": key, "display": info["display"], "category": info["category"]})
            seen.add(key)
        if len(matches) >= limit:
            break

    if len(matches) < limit:
        for key, info in PRODUCT_CATALOG.items():
            if key not in seen and (query in key or query in info["display"].lower()):
                matches.append({"key": key, "display": info["display"], "category": info["category"]})
                seen.add(key)
            if len(matches) >= limit:
                break

    if len(matches) < limit:
        for alias, canonical in ALIASES.items():
            if alias.startswith(query) and canonical not in seen and canonical in PRODUCT_CATALOG:
                info = PRODUCT_CATALOG[canonical]
                matches.append({"key": canonical, "display": info["display"], "category": info["category"]})
                seen.add(canonical)
            if len(matches) >= limit:
                break

    return matches[:limit]


def list_supported_crops() -> list[str]:
    """Return all supported product keys and aliases (sorted)."""
    return sorted(list(PRODUCT_CATALOG.keys()) + list(ALIASES.keys()))
