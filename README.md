# 🌾 AI Agent for Smart Farming Advice

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![IBM Granite](https://img.shields.io/badge/IBM_watsonx.ai-ibm%2Fgranite--4--h--small-052FAD?logo=ibm)](https://www.ibm.com/watsonx)
[![Flask](https://img.shields.io/badge/Backend-Flask_3.0-000000?logo=flask)](https://flask.palletsprojects.com/)
[![Frontend](https://img.shields.io/badge/Frontend-HTML5%20%2F%20CSS3%20%2F%20JS-E34F26?logo=html5)](frontend/index.html)
[![Tests](https://img.shields.io/badge/Tests-116%20passing-brightgreen)](#-testing)

> **IBM watsonx.ai Hackathon — Problem Statement No. 9: AI Agent for Smart Farming Advice**
> Powered entirely by **IBM Granite (`ibm/granite-4-h-small`) via watsonx.ai** and RAG (Retrieval-Augmented Generation).
> **No external APIs are used.**

---

## 📌 Overview

**Smart Farming AI Advisor** is a full-stack web application that gives Indian farmers intelligent, context-aware agricultural guidance in **English, Hindi (हिंदी), and Telugu (తెలుగు)**. It features a premium dark-mode glassmorphism design for an exceptional user experience.

The system uses a **Retrieval-Augmented Generation (RAG)** pipeline backed by an 870-line ICAR/KVK agricultural knowledge base combined with the **IBM Granite LLM** on **watsonx.ai**. Every AI response is grounded in retrieved knowledge — Granite cannot invent live weather data, live market prices, or unsupported pesticide doses.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   Farmer (Web Browser)                         │
│   Chat | Weather | Market | Crop Advice | Pest Control         │
└────────────────────────────┬───────────────────────────────────┘
                             │  HTTP (JSON)
                             ▼
┌────────────────────────────────────────────────────────────────┐
│              Flask REST API Backend (app.py)                   │
│  ┌──────────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │  RAG Pipeline    │  │  Weather Svc  │  │  Market Svc    │  │
│  │  (rag.py)        │  │  (weather.py) │  │  (market.py)   │  │
│  │  870-line KB     │  │  Stored data  │  │  MSP + Mandi   │  │
│  │  40 chunks       │  │  10 cities    │  │  sample data   │  │
│  │  Keyword score   │  │  × 12 months  │  │  15 crops      │  │
│  │  Synonym expand  │  └───────┬───────┘  └───────┬────────┘  │
│  └────────┬─────────┘          │                  │           │
│           │                    └──────────┬────────┘           │
│           ▼                               ▼                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           services/granite.py                           │   │
│  │  IAM token exchange → IBM watsonx.ai inference          │   │
│  │  Model: ibm/granite-4-h-small                           │   │
│  │  Token cache · 401 retry · Thread-safe · No secrets     │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    IBM watsonx.ai (Frankfurt)
              https://eu-de.ml.cloud.ibm.com

        All AI powered by IBM Granite only. Zero external APIs.
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **AI Advisory Chatbot** | Ask any farming question in English, Hindi, or Telugu. RAG retrieves the most relevant KB chunks; IBM Granite answers using only that context. |
| 🌾 **Crop Recommendation** | Enter soil type, season, water source, and location → IBM Granite recommends 3–5 crops with yield, risk, and care info grounded in the KB. |
| 🐛 **Pest & Disease Control** | Describe symptoms for any crop → structured IPM advice: identification → prevention → biological → chemical control (with doses from KB only). |
| ⛅ **Weather Advisory** | Stored typical monthly climate for 10 cities (temp, humidity, rainfall, condition) + IBM Granite seasonal farming advice. Clearly labelled as stored data, not live. |
| 📊 **Market / Mandi Prices** | Government MSP 2024-25 for 22 commodities + stored sample mandi prices (min/max/modal) for 15 crops × 30 markets + IBM Granite market commentary. Clearly labelled as stored sample data, not live. |
| 🌐 **Multilingual** | Full English, Hindi, and Telugu support across all 5 features including error messages and UI labels. |
| 🔍 **RAG Debug Endpoint** | `GET /api/v1/rag-debug?q=...` shows exactly which KB chunks were retrieved and passed to Granite — proves grounding in action. |

---

## 📁 Repository Structure

```
AI-Agent-for-Smart-Farming-Advice/
│
├── backend/
│   ├── app.py                  # Flask REST API — all routes, error handling,
│   │                           # /api/v1/rag-debug endpoint
│   ├── rag.py                  # RAG pipeline — overlapping chunks, keyword +
│   │                           # section-header scoring, synonym expansion,
│   │                           # build_prompt / build_crop_prompt / build_pest_prompt
│   ├── requirements.txt        # Python deps: flask, flask-cors, python-dotenv, requests
│   ├── .env.example            # Credential template (IBM_API_KEY, IBM_PROJECT_ID)
│   ├── _test_routes.py         # 58-check route integration test suite (Windows-safe)
│   ├── _test_rag.py            # 41-check RAG verification test suite
│   ├── _test_market.py         # 17-check market service unit tests
│   └── services/
│       ├── granite.py          # Centralized IBM Granite service — IAM token cache,
│       │                       # typed exceptions, thread-safe, 401 retry
│       ├── weather.py          # Stored climate data (10 cities × 12 months) +
│       │                       # IBM Granite seasonal advisory
│       ├── market.py           # Govt. MSP 2024-25 + stored sample mandi data
│       │                       # (15 crops × 30 markets, min/max/modal) +
│       │                       # IBM Granite market commentary
│       └── __init__.py
│
├── frontend/
│   ├── index.html              # Landing page with cinematic hero background
│   ├── app.html                # Main single-page app — 5 tabs, language selector
│   ├── style.css               # Responsive dark-mode glassmorphism CSS design system
│   └── script.js               # Tab logic, API calls, mandi table, weather grid,
│                               # autocomplete, en/hi/te i18n
│
├── data/
│   └── agricultural_knowledge.txt   # ICAR/KVK knowledge base (870+ lines)
│                                    # 14 sections, 40 chunks, 33 with headers
│
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/PKhadarkhan/AI-Agent-for-Smart-Farming-Advice.git
cd AI-Agent-for-Smart-Farming-Advice
```

### 2. Install dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `backend/.env`:

```dotenv
# Required — IBM Cloud API key (used to obtain IAM Bearer tokens server-side)
IBM_API_KEY=your_ibm_cloud_api_key_here

# Required — watsonx.ai project ID
# cloud.ibm.com → watsonx.ai → Projects → <project> → Manage → General
IBM_PROJECT_ID=your_watsonx_project_id_here

# Optional — override watsonx.ai region (default: Frankfurt eu-de)
# IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com

PORT=5000
FLASK_DEBUG=false
```

> 🔒 **Security:** The API key is exchanged server-side for a short-lived IAM Bearer token. The token is cached in-memory and refreshed 5 minutes before expiry. No secrets are ever sent to the browser or logged.

### 4. Start the backend

```bash
python app.py
```

The server starts on `http://localhost:5000`. The startup banner shows IBM credential status.

### 5. Open the frontend

Open `frontend/index.html` in any browser, or serve it:

```bash
cd ../frontend
python -m http.server 8080
# Visit http://localhost:8080/index.html
```

---

## 🤖 IBM Granite Integration

| Setting | Value |
|---|---|
| Model | `ibm/granite-4-h-small` |
| Provider | IBM watsonx.ai |
| Default endpoint | `https://eu-de.ml.cloud.ibm.com/ml/v1/text/generation` |
| IAM token URL | `https://iam.cloud.ibm.com/identity/token` |
| Token cache | In-memory, thread-safe, refreshed 5 min before expiry |
| 401 retry | Automatic once on token expiry |
| Timeout | 60 s (generation), 20 s (IAM) |

All calls go through [`services/granite.py`](backend/services/granite.py) which raises typed exceptions (`GraniteConfigError`, `GraniteAuthError`, `GraniteTimeoutError`, `GraniteServiceError`) — never exposes stack traces to the browser.

---

## 🔍 RAG Pipeline

The RAG pipeline in [`backend/rag.py`](backend/rag.py) ensures every AI response is grounded in the knowledge base.

### Flow

```
Farmer question
 → extract_keywords()         ← stopword removal
 → synonym expansion          ← "black soil" → vertisol, regur, cotton soil
 → score 40 KB chunks         ← keyword hits + section-header bonus
 → retrieve top-4 chunks      ← deduplicated overlapping windows
 → build_prompt()             ← context injected with strict grounding rules
 → IBM Granite                ← responds in selected language
 → answer to frontend
```

### Grounding Rules (in every prompt)

> 1. Base your answer **only** on the Retrieved Agricultural Context provided.
> 2. If the context does not contain sufficient information, say clearly that it is not available in the knowledge base.
> 3. Do **not** invent live weather conditions, live mandi prices, or pesticide doses not mentioned in the context.
> 4. If recommending chemicals, always include safety precautions.
> 5. Do **not** fabricate crop yields, temperatures, or facts not in the context.

### Prove RAG is working

```
GET http://localhost:5000/api/v1/rag-debug?q=Which+crop+is+suitable+for+black+soil
```

Response shows the exact keywords extracted, each KB chunk's score and section header, and the context string that is passed verbatim into the Granite prompt.

### Knowledge Base — 14 sections, 870+ lines

| Section | Content |
|---|---|
| Crops — Cereals | Rice, Wheat, Maize, Sorghum, Bajra, Ragi, Barley |
| Crops — Pulses | Arhar, Gram, Moong, Urad, Masoor |
| Crops — Oilseeds | Groundnut, Soybean, Mustard, Sunflower, Castor, Sesame |
| Crops — Vegetables | Tomato, Chilli, Onion, Potato, Brinjal, Cucumber, Watermelon |
| Crops — Cash | Cotton, Sugarcane, Turmeric, Jute |
| Soil types | Black cotton (Vertisol), Red (Laterite), Alluvial, Sandy loam, Clay, Loamy, Saline-sodic — best/good/poor crops for each |
| Seasonal calendar | Kharif/Rabi/Zaid dates, crops, month-by-month activity guide |
| IPM | ETL values, biological controls, neem products, pest-specific ID & management |
| Disease management | Fungal, bacterial, viral — prevention, treatment |
| Fertilizers & nutrients | N/P/K deficiency signs, micronutrients, organic options, biofertilizers |
| Water management | Drip, sprinkler, critical irrigation stages, low-water crop list with mm figures |
| Crop rotation | Beneficial sequences, intercropping systems |
| Weather guidance | Heat stress, frost, drought, waterlogging management |
| Market | MSP explanation, 22-crop MSP table, major mandis, market tips |

---

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | GET | Health check — shows IBM credential status |
| `GET /api/v1/granite-status` | GET | Granite config, endpoint, token cache state (no secrets) |
| `GET /api/v1/rag-debug` | GET/POST | RAG transparency — keywords, scored chunks, exact context |
| `POST /api/v1/reload-config` | POST | Hot-reload `.env` without restarting |
| `POST /api/chat` | POST | AI chatbot — RAG + IBM Granite — en/hi/te |
| `GET /api/weather` | GET | Weather advisory — stored data + Granite AI |
| `GET\|POST /api/market` | GET/POST | MSP + sample mandi data + Granite AI |
| `GET /api/market/catalog` | GET | Product catalog grouped by category (130+ products) |
| `GET /api/market/search?q=` | GET | Autocomplete product search |
| `GET /api/market/crops` | GET | All product keys + aliases |
| `POST /api/crop-recommend` | POST | Crop recommendation — targeted RAG + Granite |
| `POST /api/pest-control` | POST | Pest/disease advice — targeted RAG + Granite |

### Request / Response examples

**Chat**
```json
POST /api/chat
{ "question": "Which crop is best for black cotton soil in Kharif?",
  "language": "te", "location": "Telangana" }

→ { "answer": "...(Telugu)...", "context": "...", "model": "ibm/granite-4-h-small" }
```

**Crop recommendation**
```json
POST /api/crop-recommend
{ "soil_type": "black cotton soil", "season": "kharif",
  "location": "Vidarbha", "water": "rainfed", "language": "hi" }

→ { "recommendation": "...(Hindi)...", "context": "...", "rag_query": "..." }
```

**Market**
```json
POST /api/market
{ "crop": "tomato", "state": "Andhra Pradesh", "language": "en" }

→ { "success": true, "msp_price": null, "has_msp": false,
    "mandi_data": [{"market":"Kurnool","min_price":400,"max_price":1800,"modal_price":900,...}],
    "ai_advisory": "...", "notice": "Showing stored sample data — not live prices" }
```

**RAG debug**
```
GET /api/v1/rag-debug?q=How+to+control+tomato+fruit+borer

→ {
    "query": "How to control tomato fruit borer",
    "keywords": ["control", "tomato", "fruit", "borer", "whitefly", "tlcv"],
    "matches": [
      {"score": 8.5, "section": "TOMATO", "preview": "- Pests: Fruit Borer (Helicoverpa armigera)..."},
      {"score": 6.0, "section": "INTEGRATED PEST MANAGEMENT", "preview": "..."}
    ],
    "context": "...(exact text passed to Granite)...",
    "note": "This exact 'context' text is inserted into the Granite prompt."
  }
```

---

## 📊 Data Layers

### Weather — Stored Typical Climate Data
- **10 cities with full monthly data:** Warangal, Hyderabad, Nizamabad, Guntur, Kurnool, Nagpur, Pune, Ludhiana, Jaipur, Lucknow
- **Fields per month:** Min temp, max temp, humidity %, typical rainfall mm, weather condition
- **30+ regions** covered via state/region aliases
- **Clearly labelled** in UI: "Stored typical climate — NOT live data"
- **Modular:** Live IBM Environmental Intelligence data can be plugged in via `_find_location()` without changing any other code

### Market — Stored Sample Mandi Data
- **15 key crops** with sample records: Rice, Wheat, Maize, Tomato, Potato, Onion, Arhar, Gram, Groundnut, Soybean, Cotton, Chilli, Turmeric, Sugarcane
- **Fields per record:** Market name, state, min price ₹, max price ₹, modal price ₹, unit, season, date label
- **30 mandis** including Warangal, Nizamabad, Guntur, Kurnool, Amritsar, Indore, Nagpur, Lasalgaon, Erode
- **Clearly labelled** in UI: "Stored sample data — NOT live prices"

### Government MSP 2024-25
- 22 crops with official CCEA floor prices (₹/quintal)
- MSP vs mandi price difference clearly explained to farmers

---

## 🧪 Testing

```bash
cd backend

# Route integration tests (all 12 endpoints)
python _test_routes.py     # 58/58 pass

# RAG verification tests (4 required queries + 8 more)
python _test_rag.py        # 41/41 pass

# Market service unit tests
python _test_market.py     # 17/17 pass
```

All tests run without IBM credentials — Granite calls return a clean 503 (service not configured) which the tests accept as a valid response. The route structure, validation, data service, and RAG pipeline are fully tested offline.

### Required query coverage verified by `_test_rag.py`

| Query | Sections retrieved | Result |
|---|---|---|
| "What crop is best for this season?" | SEASONAL CALENDAR, KHARIF/RABI/ZAID, crop lists | ✅ PASS |
| "Which crop is suitable for black soil?" | SOIL TYPES AND CROP SUITABILITY (vertisol/regur), FAQ | ✅ PASS |
| "How can I control tomato pests?" | TOMATO (Helicoverpa, Spinosad, HaNPV), IPM | ✅ PASS |
| "Which crop needs less water?" | LOW-WATER CROPS section (Bajra 300-500mm, Jowar 400-600mm) | ✅ PASS |

---

## 🌐 Multilingual Support

| Language | Code | Coverage |
|---|---|---|
| English | `en` | Full — all features, error messages, UI labels |
| Hindi (हिंदी) | `hi` | Full — all features, error messages, UI labels |
| Telugu (తెలుగు) | `te` | Full — all features, error messages, UI labels |

Language is selected in the frontend header. Every API call passes `"language"` to the backend which:
1. Instructs IBM Granite to respond entirely in the selected language
2. Returns error messages (`GraniteError.user_message`) in the selected language
3. Accepts language aliases: `"english"` → `"en"`, `"hindi"` → `"hi"`, `"telugu"` → `"te"`

**No translation API is used.** IBM Granite handles multilingual generation natively.

---

## 🛡️ Security

| Concern | Implementation |
|---|---|
| IBM API key exposure | Never sent to browser; exchanged server-side for short-lived IAM token |
| Token storage | In-memory only; never logged; refreshed 5 min before expiry |
| Stack traces | All exceptions caught and converted to friendly user messages; no tracebacks to client |
| Secret management | `.env` file excluded from git via `.gitignore`; `.env.example` contains no real values |
| Input validation | Question length capped at 1500 chars; required fields enforced before Granite call |
| Thread safety | IAM token cache protected by `threading.Lock` |

---

## 🎯 Problem Statement No. 9 — Compliance Checklist

- [x] **IBM Cloud / IBM Granite mandatory requirement met:** `ibm/granite-4-h-small` via watsonx.ai — only AI system used
- [x] **No external APIs:** Open-Meteo, data.gov.in, Agmarknet, OpenAI, Gemini, Claude, HuggingFace, Google Translate, Microsoft Translator — all excluded; confirmed by automated grep scan
- [x] **RAG advisory system:** Grounded responses using 870-line ICAR/KVK knowledge base; `/api/v1/rag-debug` proves context is passed to Granite
- [x] **Weather guidance:** IBM Granite + stored monthly climate data; live data clearly labelled unavailable
- [x] **Soil & crop guidance:** Soil type, season, water, location → RAG-grounded crop recommendations
- [x] **Pest & disease control:** IPM-structured advice grounded in KB — identification, prevention, biological, chemical, safety
- [x] **Market / mandi information:** Govt. MSP + stored sample mandi prices (min/max/modal) + IBM Granite commentary; live prices clearly labelled unavailable
- [x] **English, Hindi, and Telugu:** Full support — Granite responds in the farmer's language; no translation API used
- [x] **No API key required (other than IBM):** Only `IBM_API_KEY` + `IBM_PROJECT_ID` needed

---

## 📜 License & Acknowledgments

- Developed for the **IBM watsonx.ai Hackathon — Problem Statement No. 9**.
- Agricultural guidance derived from public ICAR (Indian Council of Agricultural Research) and KVK guidelines.
- Government MSP data: Cabinet Committee on Economic Affairs (CCEA), Government of India, 2024-25.
- Weather climate normals: India Meteorological Department (IMD) climatological data.
- Mandi sample data: APMC annual reports and agricultural extension bulletins.
- Repository: [https://github.com/PKhadarkhan/AI-Agent-for-Smart-Farming-Advice](https://github.com/PKhadarkhan/AI-Agent-for-Smart-Farming-Advice)
