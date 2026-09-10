"""
rag.py — Retrieval-Augmented Generation Module
================================================
Loads the agricultural knowledge base, retrieves the most relevant
chunks for a query using keyword + section-header matching, and builds
the exact prompt format required by IBM Granite.

RAG workflow:
  Farmer question
  → extract keywords
  → score every KB chunk against keywords + query terms
  → retrieve top-k chunks (with section headings prioritised)
  → build grounded prompt
  → send to IBM Granite → answer

The KB is loaded once and cached in-process for efficiency.
"""

import os
import re

# ── Knowledge-base path ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH  = os.path.join(BASE_DIR, "..", "data", "agricultural_knowledge.txt")

# Chunk settings
CHUNK_SIZE    = 25   # lines per chunk — larger chunks carry more context
OVERLAP_LINES = 3    # line overlap between adjacent chunks (sliding window)

# ── Language name map ──────────────────────────────────────────────────────────
_LANG_NAMES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "te": "Telugu (తెలుగు)",
}

# ── Module-level KB cache ──────────────────────────────────────────────────────
_kb_chunks:  list[str] = []
_kb_headers: list[str] = []   # normalised section heading for each chunk


def _load_kb(path: str = KB_PATH) -> tuple[list[str], list[str]]:
    """
    Read the KB file once and split into overlapping chunks.
    Returns (chunks, headers) — parallel lists.
    """
    global _kb_chunks, _kb_headers
    if _kb_chunks:
        return _kb_chunks, _kb_headers

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return [], []

    # Build chunks with sliding window (overlap = OVERLAP_LINES)
    chunks:  list[str] = []
    headers: list[str] = []
    current_header = ""
    step = max(1, CHUNK_SIZE - OVERLAP_LINES)

    # Track the current section header for each line
    line_headers: list[str] = []
    hdr = ""
    for line in lines:
        stripped = line.strip()
        if re.match(r"^={6,}$", stripped):
            pass  # separator row
        elif re.match(r"^[A-Z][A-Z /&-]{3,}:?$", stripped) and len(stripped) < 60:
            hdr = stripped.rstrip(":")
        line_headers.append(hdr)

    for start in range(0, len(lines), step):
        end   = min(start + CHUNK_SIZE, len(lines))
        chunk = "".join(lines[start:end]).strip()
        if not chunk:
            continue
        # Dominant header in this chunk
        h = line_headers[start] if start < len(line_headers) else ""
        chunks.append(chunk)
        headers.append(h)

    _kb_chunks  = chunks
    _kb_headers = headers
    return chunks, headers


# ── Stopwords for keyword extraction ──────────────────────────────────────────
_STOPWORDS = {
    "what", "how", "when", "where", "which", "why", "is", "are", "was",
    "the", "a", "an", "of", "to", "in", "for", "and", "or", "with",
    "me", "my", "i", "can", "do", "does", "tell", "give", "about",
    "please", "want", "need", "know", "should", "will", "be", "has",
    "have", "on", "at", "from", "that", "this", "it", "its", "am",
    "good", "better", "crop", "farm", "farmer", "grow", "growing",
    "best", "using", "use", "get", "any", "some", "more", "also",
    "if", "then", "but", "so", "not", "no", "yes", "ok", "very",
    "much", "many", "here", "there", "now", "today",
}

# Domain-specific synonyms that expand keyword search
_SYNONYMS: dict[str, list[str]] = {
    "black soil":    ["vertisol", "regur", "cotton soil", "black cotton"],
    "red soil":      ["laterite", "alfisol", "red loam"],
    "alluvial":      ["gangetic", "delta", "river soil"],
    "sandy":         ["sandy loam", "light soil"],
    "water":         ["irrigation", "rainfall", "moisture", "drip", "waterlogging"],
    "pest":          ["insect", "borer", "hopper", "caterpillar", "worm", "bug", "fly"],
    "disease":       ["blight", "wilt", "rust", "rot", "blast", "mildew", "virus", "mosaic"],
    "fertilizer":    ["npk", "urea", "dap", "manure", "fym", "compost", "nutrient"],
    "kharif":        ["rainy season", "monsoon", "june", "july", "august"],
    "rabi":          ["winter season", "october", "november", "wheat season"],
    "season":        ["kharif", "rabi", "zaid", "monsoon", "summer", "winter"],
    "tomato":        ["tamata", "tamatar", "fruit borer", "tlcv"],
    "rice":          ["paddy", "dhaan", "vari", "bph", "stem borer"],
    "wheat":         ["gehun", "godhuma", "rust", "crown root"],
    "maize":         ["makka", "corn", "faw", "fall armyworm"],
    "cotton":        ["kapas", "patti", "bollworm", "bt cotton"],
    "groundnut":     ["peanut", "verusenaga", "moongphali"],
    "low water":     ["drought", "water scarce", "less water", "dryland", "arid"],
    "market":        ["mandi", "msp", "price", "apmc", "enam"],
    "government":    ["scheme", "pm-kisan", "subsidy", "kcc", "pmfby"],
}


def extract_keywords(query: str) -> list[str]:
    """
    Extract meaningful keywords from the query, expanding with synonyms.
    Returns a deduplicated list of lowercase keyword strings.
    """
    tokens = re.split(r"[\s,?.!;:()/]+", query.lower())
    keywords = [t for t in tokens if len(t) > 2 and t not in _STOPWORDS]

    # Expand with synonym terms
    query_lower = query.lower()
    for trigger, synonyms in _SYNONYMS.items():
        if trigger in query_lower or any(s in query_lower for s in synonyms):
            keywords.extend(synonyms[:2])   # add up to 2 synonyms
            keywords.append(trigger)

    # Deduplicate, preserving order
    seen = set()
    result = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
    return result


def _score_chunk(chunk: str, header: str, keywords: list[str], query: str) -> float:
    """
    Score a chunk against the query keywords.

    Scoring rules:
    - Each keyword found in chunk body: +1 point
    - Keyword in section header: +2 points (headers are more specific)
    - Long chunk bonus: small bonus for longer chunks (more context)
    - Section header in query: +3 bonus (direct match)
    """
    chunk_lower  = chunk.lower()
    header_lower = header.lower()
    query_lower  = query.lower()

    score = 0.0
    for kw in keywords:
        if kw in chunk_lower:
            score += 1.0
        if kw in header_lower:
            score += 2.0       # extra weight for section-header match

    # Bonus: if the section header appears in the query
    if header_lower and header_lower in query_lower:
        score += 3.0

    # Small length bonus (max 0.5) — rewards richer chunks
    score += min(len(chunk) / 3000, 0.5)

    return score


def retrieve(query: str, top_k: int = 4) -> str:
    """
    Retrieve the top_k most relevant knowledge-base chunks for the query.

    Returns:
        A single string with chunks separated by '---'.
        Always returns a non-empty string (falls back to first 3 chunks).

    The retrieved text is passed verbatim into the IBM Granite prompt so
    Granite can ground its answer in the knowledge base.
    """
    chunks, headers = _load_kb()

    if not chunks:
        return "Agricultural knowledge base is not available. Please check the data directory."

    keywords = extract_keywords(query)
    if not keywords:
        return "\n\n---\n\n".join(chunks[:3])

    # Score every chunk
    scored = [
        (_score_chunk(chunk, headers[i], keywords, query), i, chunk)
        for i, chunk in enumerate(chunks)
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Take top_k chunks with score > 0; fallback to first 3 if none scored
    top = [chunk for score, _, chunk in scored[:top_k] if score > 0]
    if not top:
        top = chunks[:3]

    # Deduplicate (overlapping chunks can be near-identical)
    seen_starts = set()
    deduped = []
    for chunk in top:
        key = chunk[:80]    # first 80 chars as a fingerprint
        if key not in seen_starts:
            seen_starts.add(key)
            deduped.append(chunk)

    return "\n\n---\n\n".join(deduped[:top_k])


def retrieve_for_display(query: str, top_k: int = 4) -> dict:
    """
    Like retrieve(), but returns a dict with the context string AND
    the score/header metadata — useful for debugging and demonstration.
    """
    chunks, headers = _load_kb()
    if not chunks:
        return {"context": "KB not found.", "matches": []}

    keywords = extract_keywords(query)
    scored = [
        (_score_chunk(chunks[i], headers[i], keywords, query), headers[i], chunks[i])
        for i in range(len(chunks))
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    top = [(score, hdr, chunk)
           for score, hdr, chunk in scored[:top_k] if score > 0]
    if not top:
        top = [(0, headers[0], chunks[0])]

    context = "\n\n---\n\n".join(chunk for _, _, chunk in top[:top_k])
    matches = [
        {"score": round(score, 2), "section": hdr, "preview": chunk[:120] + "..."}
        for score, hdr, chunk in top[:top_k]
    ]
    return {"context": context, "keywords": keywords, "matches": matches}


# ── Prompt builders ────────────────────────────────────────────────────────────

def build_prompt(
    question:  str,
    language:  str = "en",
    location:  str = "India",
    context:   str = "",
) -> str:
    """
    Build the IBM Granite prompt for the general farming chatbot.

    Args:
        question: Farmer's question (original language is fine).
        language: ISO code — 'en', 'hi', or 'te'.
        location: Farm location / state.
        context:  RAG-retrieved agricultural knowledge (auto-retrieved if empty).

    Returns:
        Complete prompt string ready to send to IBM Granite.

    The prompt explicitly instructs Granite to:
    - Respond in the selected language
    - Use only information from the provided context
    - Not invent live weather, live prices, or unsupported chemical doses
    - Say "this information is not available" when context is insufficient
    """
    if not context:
        context = retrieve(question)

    lang_code = language.lower().strip()
    if lang_code not in _LANG_NAMES:
        lang_code = "en"
    lang_name = _LANG_NAMES[lang_code]

    return (
        "You are an AI Smart Farming Advisor for Indian farmers.\n"
        f"Respond completely in {lang_name} only.\n\n"
        "STRICT RULES — follow these always:\n"
        "1. Base your answer ONLY on the Retrieved Agricultural Context provided below.\n"
        "2. If the context does not contain sufficient information to answer confidently, "
        "say clearly that this information is not available in the knowledge base.\n"
        "3. Do NOT invent live weather conditions, live mandi prices, or specific "
        "pesticide doses not mentioned in the context.\n"
        "4. If recommending chemicals, always include basic safety precautions.\n"
        "5. Be practical and concise — small/medium Indian farmers are your audience.\n"
        "6. Do NOT fabricate crop yields, temperatures, or facts not in the context.\n\n"
        f"Farmer's Question: {question}\n"
        f"Farm Location: {location}\n\n"
        "Retrieved Agricultural Context (use this to answer):\n"
        f"{context}\n\n"
        "ANSWER:"
    )


def build_crop_prompt(
    soil_type:   str,
    season:      str,
    location:    str,
    water:       str,
    language:    str = "en",
    extra_info:  str = "",
    context:     str = "",
) -> str:
    """
    Build a crop recommendation prompt using soil, season, and location context.
    """
    if not context:
        query = f"{soil_type} soil {season} season {location} crop recommendation"
        context = retrieve(query)

    lang_code = language.lower().strip()
    lang_name = _LANG_NAMES.get(lang_code, "English")

    extra_block = f"\nAdditional details: {extra_info}" if extra_info else ""

    return (
        "You are an AI Smart Farming Advisor for Indian farmers.\n"
        f"Respond completely in {lang_name} only.\n\n"
        "STRICT RULES:\n"
        "1. Recommend crops ONLY based on the Retrieved Context below.\n"
        "2. For each recommended crop, provide: season suitability, soil compatibility, "
        "water requirement, expected yield, and one key risk.\n"
        "3. Do NOT guarantee yields or prices — always say 'under good management'.\n"
        "4. Do NOT invent crop facts not in the context.\n"
        "5. If information is not available, clearly say so.\n\n"
        "Farmer Input:\n"
        f"  Soil Type: {soil_type}\n"
        f"  Season: {season}\n"
        f"  Location: {location}\n"
        f"  Water Availability: {water}\n"
        f"{extra_block}\n\n"
        "Retrieved Agricultural Context:\n"
        f"{context}\n\n"
        "Please recommend 3-5 suitable crops with:\n"
        "- Why this crop suits the soil and season\n"
        "- Water requirement\n"
        "- Expected yield (under good management)\n"
        "- One main risk to watch for\n\n"
        "ANSWER:"
    )


def build_pest_prompt(
    crop:       str,
    problem:    str,
    location:   str,
    language:   str = "en",
    context:    str = "",
) -> str:
    """
    Build a pest/disease control prompt grounded in the KB.
    """
    if not context:
        query = f"{crop} pest disease {problem} control management"
        context = retrieve(query)

    lang_code = language.lower().strip()
    lang_name = _LANG_NAMES.get(lang_code, "English")

    return (
        "You are an AI Smart Farming Advisor for Indian farmers.\n"
        f"Respond completely in {lang_name} only.\n\n"
        "STRICT RULES:\n"
        "1. Provide pest/disease advice ONLY based on the Retrieved Context.\n"
        "2. Structure your answer as: Identification → Prevention → Biological Control → "
        "Chemical Control → Safety Precautions.\n"
        "3. Only mention chemical doses that are EXPLICITLY stated in the context.\n"
        "4. If a specific chemical is not in the context, do NOT invent one — say 'consult "
        "your local agricultural extension officer'.\n"
        "5. Always emphasise protective equipment (gloves, mask) when mentioning chemicals.\n\n"
        f"Affected Crop: {crop}\n"
        f"Problem Description: {problem}\n"
        f"Location: {location}\n\n"
        "Retrieved Agricultural Context:\n"
        f"{context}\n\n"
        "Please provide:\n"
        "1. Possible identification of the pest/disease based on the description\n"
        "2. Prevention methods (cultural/biological)\n"
        "3. Chemical control options (with safety precautions)\n\n"
        "ANSWER:"
    )
