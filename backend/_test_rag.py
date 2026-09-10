"""
_test_rag.py — RAG retrieval verification test
================================================
Proves that:
1. Keywords are correctly extracted from farmer questions
2. The right KB sections are retrieved for each query
3. The retrieved context contains the expected agricultural terms
4. RAG context is actually passed to IBM Granite (shown in debug output)

Run from the backend directory:
    cd AI-Agent-for-Smart-Farming-Advice-main/backend
    python _test_rag.py
"""
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag import retrieve, retrieve_for_display, extract_keywords, build_prompt, build_crop_prompt, build_pest_prompt

_PASS = 0
_FAIL = 0

def check(label, condition, detail=""):
    global _PASS, _FAIL
    if condition:
        _PASS += 1
        print(f"  [PASS] {label}")
    else:
        _FAIL += 1
        print(f"  [FAIL] {label}" + (f" -- {detail}" if detail else ""))


print("=" * 70)
print("  RAG RETRIEVAL VERIFICATION TEST")
print("=" * 70)

# ── Test 1: What crop is best for this season? ────────────────────────────
print("\nQuery 1: 'What crop is best for this season?'")
result = retrieve_for_display("What crop is best for this season?")
context = result["context"].lower()
kws     = result["keywords"]
check("Keywords extracted",       len(kws) > 0,         f"got: {kws}")
check("Context is non-empty",     len(context) > 100)
check("Context has 'season'",     "season" in context)
check("Context has 'kharif' or 'rabi'", "kharif" in context or "rabi" in context)
check("Context has crop names",   "rice" in context or "wheat" in context or "maize" in context)

# ── Test 2: Which crop is suitable for black soil? ────────────────────────
print("\nQuery 2: 'Which crop is suitable for black soil?'")
result = retrieve_for_display("Which crop is suitable for black soil?")
context = result["context"].lower()
check("Keywords extracted",       len(result["keywords"]) > 0)
check("Context has 'black' soil", "black" in context)
check("Context has cotton",       "cotton" in context)
check("Context has vertisol or regur", "vertisol" in context or "regur" in context)
check("Top match is soil section",
      any("soil" in m["section"].lower() for m in result["matches"]))

# ── Test 3: How can I control tomato pests? ───────────────────────────────
print("\nQuery 3: 'How can I control tomato pests?'")
result = retrieve_for_display("How can I control tomato pests?")
context = result["context"].lower()
check("Context has 'tomato'",     "tomato" in context)
check("Context has pest info",    "borer" in context or "whitefly" in context or "mites" in context)
check("Context has control info", "spinosad" in context or "buprofezin" in context or "hanpv" in context or "trichogramma" in context)

# ── Test 4: Which crop needs less water? ─────────────────────────────────
print("\nQuery 4: 'Which crop needs less water?'")
result = retrieve_for_display("Which crop needs less water?")
context = result["context"].lower()
check("Context has drought info",    "drought" in context or "water" in context)
check("Context has drought crops",   "bajra" in context or "jowar" in context or "sorghum" in context or "ragi" in context)
check("Context has water figures",   "mm" in context)

# ── Test 5: Rice cultivation ───────────────────────────────────────────────
print("\nQuery 5: 'Rice cultivation tips'")
result = retrieve_for_display("Rice cultivation tips")
context = result["context"].lower()
check("Context has rice/paddy",   "rice" in context or "paddy" in context)
check("Context has fertilizer",   "npk" in context or "urea" in context or "fertilizer" in context)
check("Context has water info",   "water" in context or "irrigation" in context)

# ── Test 6: Fall Armyworm ──────────────────────────────────────────────────
print("\nQuery 6: 'Fall armyworm in maize'")
result = retrieve_for_display("Fall armyworm in maize")
context = result["context"].lower()
check("Context has FAW",          "armyworm" in context or "faw" in context)
check("Context has maize",        "maize" in context or "makka" in context)
check("Context has management",   "emamectin" in context or "trichogramma" in context or "chlorantraniliprole" in context)

# ── Test 7: Government schemes ─────────────────────────────────────────────
print("\nQuery 7: 'Government schemes for farmers'")
result = retrieve_for_display("Government schemes for farmers")
context = result["context"].lower()
check("Context has PM-KISAN",     "pm-kisan" in context or "kisan" in context)
check("Context has scheme info",  "scheme" in context or "subsidy" in context or "insurance" in context)

# ── Test 8: Keyword expansion (synonyms) ──────────────────────────────────
print("\nQuery 8: Keyword synonym expansion test")
kws = extract_keywords("pest control for my tomato plants")
check("Synonym expansion works",  "borer" in kws or "hopper" in kws or "insect" in kws,
      f"keywords: {kws}")
kws2 = extract_keywords("black soil crop")
check("Black soil synonyms",      "vertisol" in kws2 or "regur" in kws2 or "cotton soil" in kws2,
      f"keywords: {kws2}")

# ── Test 9: Prompt builder includes context ────────────────────────────────
print("\nQuery 9: Prompt builder passes context to Granite")
q = "What crop is best for red soil?"
ctx = retrieve(q)
prompt = build_prompt(q, language="en", location="Telangana", context=ctx)
check("Prompt contains 'Retrieved Agricultural Context'",
      "Retrieved Agricultural Context" in prompt)
check("Prompt contains actual KB text",
      "laterite" in prompt.lower() or "groundnut" in prompt.lower() or "red soil" in prompt.lower())
check("Prompt has grounding rules",
      "ONLY on the Retrieved Agricultural Context" in prompt)
check("Prompt includes question",  q in prompt)

# ── Test 10: Crop prompt builder ───────────────────────────────────────────
print("\nQuery 10: build_crop_prompt passes context")
cp = build_crop_prompt("black cotton soil", "kharif", "Telangana", "rainfed", "en")
check("Crop prompt has soil type",  "black cotton soil" in cp)
check("Crop prompt has season",     "kharif" in cp.lower())
check("Crop prompt has context",    "Retrieved Agricultural Context" in cp)
check("Crop prompt has KB content", len(cp) > 500)

# ── Test 11: Pest prompt builder ───────────────────────────────────────────
print("\nQuery 11: build_pest_prompt passes context")
pp = build_pest_prompt("tomato", "holes in fruit", "Andhra Pradesh", "te")
check("Pest prompt has crop",     "tomato" in pp.lower())
check("Pest prompt has problem",  "holes" in pp.lower())
check("Pest prompt has context",  "Retrieved Agricultural Context" in pp)
check("Pest prompt has language instruction", "Telugu" in pp)

# ── Test 12: KB size and coverage ─────────────────────────────────────────
print("\nQuery 12: KB coverage check")
from rag import _load_kb
chunks, headers = _load_kb()
check("KB loaded",            len(chunks) > 0,  f"chunks: {len(chunks)}")
check("KB has 30+ chunks",    len(chunks) >= 30, f"chunks: {len(chunks)}")
check("KB has section headers", len([h for h in headers if h]) > 5)
print(f"  INFO: KB has {len(chunks)} chunks, {len([h for h in headers if h])} with section headers")

# ── Summary ────────────────────────────────────────────────────────────────
total = _PASS + _FAIL
print()
print("=" * 70)
print(f"  RESULTS: {_PASS}/{total} passed, {_FAIL} failed")
print("=" * 70)
if _FAIL == 0:
    print("  ALL RAG TESTS PASSED")
    print()
    print("  Demonstration: RAG flow for 'black soil crop'")
    r = retrieve_for_display("Which crop is suitable for black soil?")
    for i, m in enumerate(r["matches"][:3], 1):
        print(f"  [{i}] Section: {m['section']}, Score: {m['score']}")
        print(f"       Preview: {m['preview'][:100]}...")
    print()
    print("  This context ^ is what gets sent to IBM Granite inside the prompt.")
else:
    print(f"  {_FAIL} test(s) FAILED")

sys.exit(0 if _FAIL == 0 else 1)
