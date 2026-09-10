"""
app.py — Smart Farming AI Advisor — Flask Backend
==================================================
Architecture:
  Frontend → Flask → services/granite.py → IBM watsonx.ai (Granite)
                  → services/weather.py  → IBM Granite seasonal advisory
                  → services/market.py   → MSP data + IBM Granite commentary
                  → rag.py               → ICAR/KVK knowledge base

Security:
  - All IBM credentials are read ONLY from environment variables / .env file.
  - Credentials are NEVER sent to the browser, logged, or included in responses.
  - IAM Bearer tokens are cached in-memory (services/granite.py) and refreshed
    5 minutes before expiry.

Environment variables required:
  IBM_API_KEY        IBM Cloud API key (to obtain IAM Bearer tokens)
  IBM_PROJECT_ID     watsonx.ai project ID
  IBM_WATSONX_URL    (optional) watsonx.ai base URL; defaults to eu-de endpoint

Supported languages: en (English), hi (Hindi), te (Telugu)

Run:
    cd backend
    python app.py
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# ── Load .env before anything else ────────────────────────────────────────────
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_env_path, override=True)

# ── Ensure service imports resolve from this directory ────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Internal service imports ──────────────────────────────────────────────────
from services.granite import (
    call_granite,
    get_granite_status,
    GraniteConfigError,
    GraniteAuthError,
    GraniteTimeoutError,
    GraniteServiceError,
    GraniteError,
    GRANITE_MODEL_ID,
)
from rag import (
    retrieve, retrieve_for_display,
    build_prompt, build_crop_prompt, build_pest_prompt,
)
from services.weather import get_weather
from services.market import (
    get_market_prices,
    list_supported_crops,
    list_supported_products,
    search_products,
    get_product_info,
)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False   # preserve Telugu/Hindi Unicode in JSON
CORS(app)


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SUPPORT
# ══════════════════════════════════════════════════════════════════════════════

_SUPPORTED_LANGS = {"en", "hi", "te"}

_LANG_MAP = {
    "english": "en", "hindi": "hi", "telugu": "te",
    "en": "en",      "hi":    "hi", "te":     "te",
}

_LANG_NAMES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "te": "Telugu (తెలుగు)",
}

# User-facing error messages per language
_ERR_MSG = {
    "en": {
        "ai_unavailable":   "Unable to connect to the AI service. Please try again later.",
        "ai_timeout":       "The AI service took too long to respond. Please try again.",
        "ai_config":        "The AI service is not configured on the server. Please contact the administrator.",
        "question_empty":   "Please enter a question before sending.",
        "question_long":    "Your question is too long. Please keep it under 1500 characters.",
        "missing_fields":   "Please fill in all required fields.",
        "server_error":     "An unexpected error occurred. Please try again.",
    },
    "hi": {
        "ai_unavailable":   "AI सेवा से कनेक्ट नहीं हो सका। कृपया बाद में पुनः प्रयास करें।",
        "ai_timeout":       "AI सेवा की प्रतिक्रिया में बहुत समय लगा। कृपया पुनः प्रयास करें।",
        "ai_config":        "सर्वर पर AI सेवा कॉन्फ़िगर नहीं है। कृपया व्यवस्थापक से संपर्क करें।",
        "question_empty":   "भेजने से पहले कृपया प्रश्न दर्ज करें।",
        "question_long":    "आपका प्रश्न बहुत लंबा है। कृपया 1500 अक्षरों के भीतर रखें।",
        "missing_fields":   "कृपया सभी आवश्यक फ़ील्ड भरें।",
        "server_error":     "एक अप्रत्याशित त्रुटि हुई। कृपया पुनः प्रयास करें।",
    },
    "te": {
        "ai_unavailable":   "AI సేవకు కనెక్ట్ కాలేకపోయాము. దయచేసి తర్వాత మళ్ళీ ప్రయత్నించండి.",
        "ai_timeout":       "AI సేవ స్పందించడానికి చాలా సమయం పట్టింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
        "ai_config":        "సర్వర్‌లో AI సేవ కాన్ఫిగర్ కాలేదు. దయచేసి నిర్వాహకులను సంప్రదించండి.",
        "question_empty":   "దయచేసి పంపే ముందు ఒక ప్రశ్న నమోదు చేయండి.",
        "question_long":    "మీ ప్రశ్న చాలా పెద్దది. దయచేసి 1500 అక్షరాల లోపు ఉంచండి.",
        "missing_fields":   "దయచేసి అన్ని అవసరమైన ఫీల్డ్‌లను పూరించండి.",
        "server_error":     "అనుకోని లోపం సంభవించింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    },
}


def normalise_lang(lang: str) -> str:
    """Normalise to one of: en, hi, te.  Defaults to 'en'."""
    code = _LANG_MAP.get((lang or "").lower().strip(), "en")
    return code if code in _SUPPORTED_LANGS else "en"


def err_msg(lang: str, key: str) -> str:
    """Return a translated user-facing error message."""
    return _ERR_MSG.get(lang, _ERR_MSG["en"]).get(key, _ERR_MSG["en"].get(key, key))


def _err(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


def _handle_granite_error(exc: Exception, lang: str):
    """
    Convert any Granite exception to the appropriate HTTP error response.
    User-facing message is taken from the exception when available.
    """
    if isinstance(exc, GraniteConfigError):
        msg = getattr(exc, "user_message", None) or err_msg(lang, "ai_config")
        return _err(msg, 503)
    if isinstance(exc, GraniteAuthError):
        msg = getattr(exc, "user_message", None) or err_msg(lang, "ai_unavailable")
        return _err(msg, 503)
    if isinstance(exc, GraniteTimeoutError):
        msg = getattr(exc, "user_message", None) or err_msg(lang, "ai_timeout")
        return _err(msg, 504)
    if isinstance(exc, (GraniteServiceError, GraniteError)):
        msg = getattr(exc, "user_message", None) or err_msg(lang, "ai_unavailable")
        return _err(msg, 502)
    # Fallback for unexpected exceptions
    return _err(err_msg(lang, "server_error"), 500)


# ══════════════════════════════════════════════════════════════════════════════
# MANAGEMENT / DIAGNOSTIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/v1/rag-debug", methods=["GET", "POST"])
def rag_debug():
    """
    RAG transparency endpoint — shows what the retrieval step actually fetches.

    GET  /api/v1/rag-debug?q=What+crop+for+black+soil
    POST /api/v1/rag-debug  { "query": "..." }

    Response: { query, keywords, matches:[{score, section, preview}], context }
    This proves that Granite receives real KB context, not hallucinated content.
    """
    if request.method == "POST":
        body  = request.get_json(silent=True) or {}
        query = (body.get("query") or body.get("q") or "").strip()
    else:
        query = (request.args.get("q") or request.args.get("query") or "").strip()

    if not query:
        return _err("'q' or 'query' parameter is required.")

    result = retrieve_for_display(query)
    return jsonify({
        "query":    query,
        "keywords": result.get("keywords", []),
        "matches":  result.get("matches", []),
        "context":  result.get("context", ""),
        "note":     "This exact 'context' text is inserted into the Granite prompt.",
    }), 200


@app.route("/", methods=["GET"])
def health():
    """Health-check — confirms backend is alive and IBM credentials are present."""
    status = get_granite_status()
    return jsonify({
        "status":        "ok",
        "service":       "Smart Farming AI Advisor",
        "model":         status["model"],
        "IBM_API_KEY":   status["IBM_API_KEY"],
        "IBM_PROJECT_ID": status["IBM_PROJECT_ID"],
        "IBM_WATSONX_URL": status["IBM_WATSONX_URL"],
        "granite_ready": status["ready"],
        "external_apis": "none — IBM Granite only",
    }), 200


@app.route("/api/v1/granite-status", methods=["GET"])
def granite_status():
    """
    Detailed Granite service status — safe to expose (no secrets).
    Returns model name, endpoint URL, env var presence, token cache state.
    """
    return jsonify(get_granite_status()), 200


@app.route("/api/v1/reload-config", methods=["POST"])
def reload_config():
    """Reload .env from disk and confirm. Token cache is NOT cleared."""
    load_dotenv(dotenv_path=_env_path, override=True)
    return jsonify({
        "success": True,
        "message": "Configuration reloaded from .env",
        "granite": get_granite_status(),
    })


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main AI chatbot endpoint.

    Request JSON:
        {
          "question": "What crop is best this season?",   (required)
          "language": "en" | "hi" | "te",                 (optional, default "en")
          "location": "Telangana"                          (optional)
        }

    "query" is accepted as an alias for "question".

    Response JSON (200):
        { "answer": "…", "context": "…", "model": "ibm/granite-4-h-small" }

    Error JSON (4xx/5xx):
        { "error": "<translated message>" }
    """
    body     = request.get_json(silent=True) or {}
    question = (body.get("question") or body.get("query") or "").strip()
    lang     = normalise_lang(body.get("language") or "en")
    location = (body.get("location") or "India").strip()

    if not question:
        return _err(err_msg(lang, "question_empty"))
    if len(question) > 1500:
        return _err(err_msg(lang, "question_long"))

    context = retrieve(question)
    prompt  = build_prompt(
        question=question,
        language=lang,
        location=location,
        context=context,
    )

    try:
        answer = call_granite(prompt, language=lang)
    except Exception as exc:
        return _handle_granite_error(exc, lang)

    return jsonify({
        "answer":  answer,
        "context": context,
        "model":   GRANITE_MODEL_ID,
    }), 200


@app.route("/api/weather", methods=["GET"])
def weather():
    """GET /api/weather?location=Warangal&language=en"""
    location = (request.args.get("location") or "").strip()
    lang     = normalise_lang(request.args.get("language") or "en")
    if not location:
        return _err("'location' query parameter is required.")
    result = get_weather(location, language=lang)
    status = 404 if "error" in result else 200
    return jsonify(result), status


@app.route("/api/market", methods=["GET", "POST"])
def market():
    """
    Market price endpoint — accepts GET and POST.

    POST body:
        { "crop": "tomato", "state": "Andhra Pradesh", "market": "Visakhapatnam", "language": "en" }

    GET params:
        ?crop=tomato&state=Andhra+Pradesh&market=Visakhapatnam
    """
    if request.method == "POST":
        body   = request.get_json(silent=True) or {}
        crop   = (body.get("crop") or body.get("product") or "").strip()
        state  = (body.get("state")  or "").strip() or None
        mkt    = (body.get("market") or body.get("city") or "").strip() or None
        lang   = normalise_lang(body.get("language") or "en")
    else:
        crop   = (request.args.get("crop") or request.args.get("product") or "").strip()
        state  = (request.args.get("state")  or "").strip() or None
        mkt    = (request.args.get("market") or request.args.get("city") or "").strip() or None
        lang   = normalise_lang(request.args.get("language") or "en")

    if not crop:
        return _err("'crop' / 'product' field is required.")

    result = get_market_prices(crop, state=state, market=mkt, language=lang)
    return jsonify(result), 200


@app.route("/api/market/catalog", methods=["GET"])
def market_catalog():
    """Return the full product catalog grouped by category."""
    return jsonify(list_supported_products()), 200


@app.route("/api/market/search", methods=["GET"])
def market_search():
    """GET /api/market/search?q=tom&limit=8 — autocomplete search."""
    query = (request.args.get("q") or "").strip()
    limit = min(int(request.args.get("limit", 10)), 20)
    return jsonify({"results": search_products(query, limit)}), 200


@app.route("/api/market/crops", methods=["GET"])
def supported_crops():
    """Legacy endpoint — returns flat list of all keys + aliases."""
    return jsonify({"crops": list_supported_crops()}), 200


@app.route("/api/crop-recommend", methods=["POST"])
def crop_recommend():
    """
    Request JSON:
        { "soil_type", "season", "location", "water", "language" }

    Uses dedicated build_crop_prompt() which retrieves soil + season specific
    context from the agricultural KB and strictly grounds Granite's answer.
    """
    body     = request.get_json(silent=True) or {}
    soil     = (body.get("soil_type") or "").strip()
    season   = (body.get("season")    or "").strip()
    location = (body.get("location")  or "India").strip()
    water    = (body.get("water")     or "rainfed").strip()
    lang     = normalise_lang(body.get("language") or "en")

    if not soil or not season:
        return _err(err_msg(lang, "missing_fields"))

    # RAG: retrieve context targeted at soil + season combination
    rag_query = f"{soil} soil {season} season {location} crop recommendation water {water}"
    context   = retrieve(rag_query)

    prompt = build_crop_prompt(
        soil_type=soil,
        season=season,
        location=location,
        water=water,
        language=lang,
        context=context,
    )

    try:
        answer = call_granite(prompt, language=lang)
    except Exception as exc:
        return _handle_granite_error(exc, lang)

    return jsonify({
        "recommendation": answer,
        "context":        context,
        "model":          GRANITE_MODEL_ID,
        "rag_query":      rag_query,
    }), 200


@app.route("/api/pest-control", methods=["POST"])
def pest_control():
    """
    Request JSON:
        { "crop", "problem", "language", "location" }

    Uses dedicated build_pest_prompt() which retrieves IPM + pest-specific
    context and instructs Granite to only cite chemical doses from the KB.
    """
    body     = request.get_json(silent=True) or {}
    crop     = (body.get("crop")     or "").strip()
    problem  = (body.get("problem")  or "").strip()
    lang     = normalise_lang(body.get("language") or "en")
    location = (body.get("location") or "India").strip()

    if not crop or not problem:
        return _err(err_msg(lang, "missing_fields"))

    # RAG: retrieve context targeted at the specific crop + pest/disease
    rag_query = f"{crop} {problem} pest disease control management identification"
    context   = retrieve(rag_query)

    prompt = build_pest_prompt(
        crop=crop,
        problem=problem,
        location=location,
        language=lang,
        context=context,
    )

    try:
        answer = call_granite(prompt, language=lang)
    except Exception as exc:
        return _handle_granite_error(exc, lang)

    return jsonify({
        "advice":    answer,
        "context":   context,
        "model":     GRANITE_MODEL_ID,
        "rag_query": rag_query,
    }), 200


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    status = get_granite_status()
    print("=" * 60)
    print("  Smart Farming AI Advisor")
    print("=" * 60)
    print(f"  Model      : {status['model']}")
    print(f"  Endpoint   : {status['endpoint']}")
    print(f"  IBM_API_KEY: {status['IBM_API_KEY']}")
    print(f"  IBM_PROJECT_ID: {status['IBM_PROJECT_ID']}")
    print(f"  Granite ready: {status['ready']}")
    print(f"  External APIs: none — IBM Granite only")
    if not status["ready"]:
        print()
        print("  WARNING: AI features will not work until credentials are set.")
        print("  Set IBM_API_KEY and IBM_PROJECT_ID in backend/.env and restart.")
    print("=" * 60)
    print(f"  Starting on http://0.0.0.0:{port}")
    print("=" * 60)

    app.run(host="0.0.0.0", port=port, debug=debug)
