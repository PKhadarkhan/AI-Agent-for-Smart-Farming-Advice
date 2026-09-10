"""
_test_routes.py -- Flask route integration tests (Windows-safe UTF-8)
======================================================================
Tests all API routes using the Flask test client.
No real IBM credentials are needed -- Granite calls gracefully fail with
a 503 when env vars are absent, and the route still returns valid JSON.

Run from the backend directory:
    cd AI-Agent-for-Smart-Farming-Advice-main/backend
    python _test_routes.py
"""

import sys
import os

# Windows: force UTF-8 output so Hindi/Telugu strings don't crash the terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # Python < 3.7 fallback

# Ensure backend root is on sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Load .env if present (won't fail if missing)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_HERE, ".env"), override=True)
except ImportError:
    pass

import json

# ── Import Flask app ───────────────────────────────────────────────────────────
try:
    from app import app
except Exception as e:
    print(f"[FAIL] Could not import app: {e}")
    sys.exit(1)

app.config["TESTING"] = True
client = app.test_client()

# ── Test helpers ───────────────────────────────────────────────────────────────
_PASS = 0
_FAIL = 0


def check(label: str, condition: bool, detail: str = ""):
    global _PASS, _FAIL
    if condition:
        _PASS += 1
        print(f"  [PASS] {label}")
    else:
        _FAIL += 1
        print(f"  [FAIL] {label}" + (f" -- {detail}" if detail else ""))


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Health check endpoint
# ══════════════════════════════════════════════════════════════════════════════
section("TEST 1 — GET / (health check)")
r = client.get("/")
check("Status 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("Body has 'status'",        "status"        in body)
check("Body has 'model'",         "model"         in body)
check("Body has 'external_apis'", "external_apis" in body)
check("external_apis == none",    "none" in body.get("external_apis","").lower())

# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Granite status endpoint
# ══════════════════════════════════════════════════════════════════════════════
section("TEST 2 — GET /api/v1/granite-status")
r = client.get("/api/v1/granite-status")
check("Status 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("Has 'model'",          "model"          in body)
check("Has 'IBM_API_KEY'",    "IBM_API_KEY"    in body)
check("Has 'IBM_PROJECT_ID'", "IBM_PROJECT_ID" in body)
check("Has 'ready'",          "ready"          in body)
check("Model is ibm/granite", "ibm/granite" in body.get("model",""))

# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: /api/chat -- validation
# ══════════════════════════════════════════════════════════════════════════════
section("TEST 3 — POST /api/chat (validation)")

# Empty question should return 400
r = client.post("/api/chat", json={"question": ""})
check("Empty question -> 400", r.status_code == 400, f"got {r.status_code}")
body = json.loads(r.data)
check("Error field present", "error" in body)

# Question too long -> 400
r = client.post("/api/chat", json={"question": "x" * 1501})
check("Question > 1500 chars -> 400", r.status_code == 400, f"got {r.status_code}")

# Valid question -> 200 or 503 (503 = Granite not configured, which is valid in test env)
r = client.post("/api/chat", json={"question": "What crop grows well in red soil?"})
check(
    "Valid question -> 200 or 503",
    r.status_code in (200, 503, 504, 502),
    f"got {r.status_code}"
)
body = json.loads(r.data)
if r.status_code == 200:
    check("Response has 'answer'", "answer" in body)
    check("Response has 'model'",  "model"  in body)
else:
    check("Error has 'error' field", "error" in body)

# Language alias
r = client.post("/api/chat", json={"question": "Rice cultivation tips", "language": "hindi"})
check(
    "Language alias 'hindi' accepted -> not 400",
    r.status_code != 400,
    f"got {r.status_code}"
)

# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: /api/weather -- validation
# ══════════════════════════════════════════════════════════════════════════════
section("TEST 4 — GET /api/weather")

# Missing location -> 400
r = client.get("/api/weather")
check("Missing location -> 400", r.status_code == 400, f"got {r.status_code}")

# Valid location -> 200 (weather service never returns 503 -- always has fallback)
r = client.get("/api/weather?location=Warangal&language=en")
check("Valid location -> 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("Has 'location'",        "location"  in body)
check("Has 'season'",          "season"    in body)
check("Has 'tips'",            "tips"      in body)
check("Has 'notice'",          "notice"    in body)
check("Tips is a list",        isinstance(body.get("tips"), list))
check("Season is non-empty",   bool(body.get("season")))
check("No external data",      "IBM Granite" in body.get("advisory_source", ""))

# Telugu language
r = client.get("/api/weather?location=Guntur&language=te")
check("Telugu language accepted -> 200", r.status_code == 200, f"got {r.status_code}")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: /api/market -- validation
# ══════════════════════════════════════════════════════════════════════════════
section("TEST 5 — GET+POST /api/market")

# Missing crop -> 400
r = client.get("/api/market")
check("Missing crop -> 400", r.status_code == 400, f"got {r.status_code}")

# Valid crop GET -> 200
r = client.get("/api/market?crop=tomato")
check("GET tomato -> 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("Has 'success' field",   "success"   in body)
check("success is True",       body.get("success") is True)
check("Has 'notice'",          "notice"    in body)
check("Has 'data_source'",     "data_source" in body)
check("MSP: has_msp False (tomato)", body.get("has_msp") is False)

# Cereal with MSP -- POST
r = client.post("/api/market", json={"crop": "wheat", "language": "en"})
check("POST wheat -> 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("has_msp True (wheat)",  body.get("has_msp") is True)
check("msp_price present",     "msp_price" in body)
check("msp_price is int",      isinstance(body.get("msp_price"), int))

# Alias lookup (paddy -> rice)
r = client.get("/api/market?crop=paddy")
check("Alias 'paddy' -> rice -> 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("Alias resolves to 'rice'", body.get("product") == "rice")

# Unknown crop -> 200 with success=False
r = client.get("/api/market?crop=xyzunknowncrop999")
check("Unknown crop -> 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("success False for unknown", body.get("success") is False)
check("error_type = product_not_found", body.get("error_type") == "product_not_found")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: /api/market/catalog and /api/market/search
# ══════════════════════════════════════════════════════════════════════════════
section("TEST 6 — /api/market/catalog and /api/market/search")

r = client.get("/api/market/catalog")
check("GET /api/market/catalog -> 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("Catalog has 'vegetables'", "vegetables" in body)
check("Catalog has 'cereals'",    "cereals"    in body)
check("Catalog has 'fruits'",     "fruits"     in body)

r = client.get("/api/market/search?q=tom&limit=5")
check("GET /api/market/search -> 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("Has 'results' key", "results" in body)
check("Results is a list", isinstance(body.get("results"), list))
check("Results <= 5",      len(body.get("results",[])) <= 5)

# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: /api/crop-recommend
# ══════════════════════════════════════════════════════════════════════════════
section("TEST 7 — POST /api/crop-recommend")

# Missing fields -> 400
r = client.post("/api/crop-recommend", json={})
check("Missing fields -> 400", r.status_code == 400, f"got {r.status_code}")

# Valid request -> 200 or 503 (503 = Granite not configured)
r = client.post("/api/crop-recommend", json={
    "soil_type": "red soil",
    "season":    "kharif",
    "location":  "Telangana",
    "water":     "rainfed",
    "language":  "en",
})
check(
    "Valid crop-recommend -> 200 or 503",
    r.status_code in (200, 503, 504, 502),
    f"got {r.status_code}"
)

# ══════════════════════════════════════════════════════════════════════════════
# TEST 8: /api/pest-control
# ══════════════════════════════════════════════════════════════════════════════
section("TEST 8 — POST /api/pest-control")

# Missing fields -> 400
r = client.post("/api/pest-control", json={})
check("Missing fields -> 400", r.status_code == 400, f"got {r.status_code}")

# Valid request -> 200 or 503
r = client.post("/api/pest-control", json={
    "crop":     "cotton",
    "problem":  "white fly infestation",
    "language": "en",
    "location": "Gujarat",
})
check(
    "Valid pest-control -> 200 or 503",
    r.status_code in (200, 503, 504, 502),
    f"got {r.status_code}"
)

# ══════════════════════════════════════════════════════════════════════════════
# TEST 9: /api/v1/reload-config
# ══════════════════════════════════════════════════════════════════════════════
section("TEST 9 — POST /api/v1/reload-config")
r = client.post("/api/v1/reload-config")
check("Status 200", r.status_code == 200, f"got {r.status_code}")
body = json.loads(r.data)
check("Has 'success'", "success" in body)
check("success is True", body.get("success") is True)

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
total = _PASS + _FAIL
print()
print("=" * 60)
print(f"  RESULTS: {_PASS}/{total} passed, {_FAIL} failed")
print("=" * 60)

if _FAIL == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  {_FAIL} test(s) FAILED -- see above for details")

sys.exit(0 if _FAIL == 0 else 1)
