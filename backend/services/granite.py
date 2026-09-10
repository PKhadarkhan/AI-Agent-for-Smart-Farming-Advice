"""
services/granite.py — Centralized IBM Granite Service
=======================================================
Single module responsible for ALL communication with IBM watsonx.ai.

Environment variables (all read at call time — hot-reload safe):
    IBM_API_KEY       Required. IBM Cloud API key used to obtain IAM tokens.
    IBM_PROJECT_ID    Required. watsonx.ai project ID.
    IBM_WATSONX_URL   Optional. Defaults to the Frankfurt (eu-de) endpoint.
                      Override for us-south or other regions:
                        https://us-south.ml.cloud.ibm.com

Design:
    • IAM Bearer token is obtained server-side only; never sent to the browser.
    • Token is cached in memory and refreshed 5 minutes before expiry.
    • Cache is protected by a threading.Lock — safe for multi-threaded WSGI.
    • On 401 the cache is invalidated and one automatic retry is performed.
    • Timeout, network, and API errors are converted to typed exceptions with
      user-friendly messages for each supported language (en / hi / te).
    • No secrets are ever logged.

Public API:
    call_granite(prompt, *, max_new_tokens, language) -> str
        Raises GraniteConfigError   – missing IBM_API_KEY or IBM_PROJECT_ID
        Raises GraniteAuthError     – invalid / expired API key
        Raises GraniteTimeoutError  – request timed out
        Raises GraniteServiceError  – HTTP error from watsonx.ai
        Raises GraniteError         – base class for all above
    get_granite_status() -> dict
        Returns a safe (no secrets) status dictionary.
"""

import os
import time
import threading

import requests

# ── Model configuration ────────────────────────────────────────────────────────
GRANITE_MODEL_ID    = "ibm/granite-4-h-small"
WATSONX_API_VERSION = "2023-05-29"
DEFAULT_WATSONX_URL = "https://eu-de.ml.cloud.ibm.com"
IBM_IAM_URL         = "https://iam.cloud.ibm.com/identity/token"

MAX_NEW_TOKENS_DEFAULT = 700
IAM_TOKEN_TIMEOUT      = 20   # seconds
GRANITE_CALL_TIMEOUT   = 60   # seconds
TOKEN_REFRESH_BUFFER   = 300  # refresh 5 min before expiry

# ── User-facing error strings (en / hi / te) ───────────────────────────────────
_ERRORS = {
    "config": {
        "en": "The AI service is not configured on the server. Please contact the administrator.",
        "hi": "सर्वर पर AI सेवा कॉन्फ़िगर नहीं है। कृपया व्यवस्थापक से संपर्क करें।",
        "te": "సర్వర్‌లో AI సేవ కాన్ఫిగర్ కాలేదు. దయచేసి నిర్వాహకులను సంప్రదించండి.",
    },
    "auth": {
        "en": "AI service authentication failed. Please check your IBM API key.",
        "hi": "AI सेवा प्रमाणीकरण विफल हुआ। कृपया अपनी IBM API key जांचें।",
        "te": "AI సేవ ప్రమాణీకరణ విఫలమైంది. దయచేసి మీ IBM API కీని తనిఖీ చేయండి.",
    },
    "timeout": {
        "en": "The AI service took too long to respond. Please try again.",
        "hi": "AI सेवा की प्रतिक्रिया में बहुत समय लगा। कृपया पुनः प्रयास करें।",
        "te": "AI సేవ స్పందించడానికి చాలా సమయం పట్టింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    },
    "service": {
        "en": "The AI service returned an error. Please try again later.",
        "hi": "AI सेवा ने एक त्रुटि लौटाई। कृपया बाद में पुनः प्रयास करें।",
        "te": "AI సేవ ఒక లోపాన్ని తిరిగి ఇచ్చింది. దయచేసి తర్వాత మళ్ళీ ప్రయత్నించండి.",
    },
    "unavailable": {
        "en": "Unable to connect to the AI service. Please try again later.",
        "hi": "AI सेवा से कनेक्ट नहीं हो सका। कृपया बाद में पुनः प्रयास करें।",
        "te": "AI సేవకు కనెక్ట్ కాలేకపోయాము. దయచేసి తర్వాత మళ్ళీ ప్రయత్నించండి.",
    },
}


def _user_msg(error_key: str, language: str = "en") -> str:
    """Return a translated user-facing error string."""
    lang = language if language in ("en", "hi", "te") else "en"
    return _ERRORS.get(error_key, _ERRORS["unavailable"]).get(lang, _ERRORS[error_key]["en"])


# ── Typed exceptions ──────────────────────────────────────────────────────────

class GraniteError(Exception):
    """Base class for all Granite service errors."""
    def __init__(self, message: str, user_message: str = "", language: str = "en"):
        super().__init__(message)
        self.user_message = user_message or message
        self.language = language


class GraniteConfigError(GraniteError):
    """IBM_API_KEY or IBM_PROJECT_ID is missing."""


class GraniteAuthError(GraniteError):
    """IBM IAM authentication failed (bad/expired API key)."""


class GraniteTimeoutError(GraniteError):
    """Request to watsonx.ai timed out."""


class GraniteServiceError(GraniteError):
    """HTTP error returned by watsonx.ai (4xx/5xx other than 401)."""


# ── IAM token cache ────────────────────────────────────────────────────────────
_token_cache: dict = {
    "access_token": None,
    "expires_at":   0,
    "lock":         threading.Lock(),
}


def _read_config() -> tuple[str, str, str]:
    """
    Read IBM credentials from environment at call time.
    Returns (api_key, project_id, watsonx_base_url).
    Raises GraniteConfigError if required vars are absent.
    """
    api_key    = os.environ.get("IBM_API_KEY", "").strip()
    project_id = (
        os.environ.get("IBM_PROJECT_ID", "")
        or os.environ.get("GRANITE_PROJECT_ID", "")   # backward-compat alias
    ).strip()
    base_url   = (
        os.environ.get("IBM_WATSONX_URL", "").rstrip("/")
        or DEFAULT_WATSONX_URL
    )

    missing = []
    if not api_key:
        missing.append("IBM_API_KEY")
    if not project_id:
        missing.append("IBM_PROJECT_ID")

    if missing:
        raise GraniteConfigError(
            f"Missing environment variables: {', '.join(missing)}. "
            "Set them in backend/.env and restart.",
            user_message=_user_msg("config"),
        )

    return api_key, project_id, base_url


def _fetch_fresh_token(api_key: str) -> tuple[str, int]:
    """
    Exchange an IBM Cloud API key for a fresh IAM Bearer token.
    Returns (access_token, expires_in_seconds).
    Raises GraniteAuthError or GraniteServiceError on failure.
    """
    try:
        resp = requests.post(
            IBM_IAM_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey":     api_key,
            },
            timeout=IAM_TOKEN_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        raise GraniteTimeoutError(
            "IAM token request timed out.",
            user_message=_user_msg("timeout"),
        )
    except requests.exceptions.RequestException as exc:
        raise GraniteServiceError(
            f"IAM network error: {exc}",
            user_message=_user_msg("unavailable"),
        )

    if resp.status_code in (400, 401, 403):
        raise GraniteAuthError(
            f"IAM rejected API key (HTTP {resp.status_code}): {resp.text[:200]}",
            user_message=_user_msg("auth"),
        )

    if not resp.ok:
        raise GraniteServiceError(
            f"IAM endpoint returned HTTP {resp.status_code}: {resp.text[:200]}",
            user_message=_user_msg("service"),
        )

    data       = resp.json()
    token      = data.get("access_token", "").strip()
    expires_in = int(data.get("expires_in", 3600))

    if not token:
        raise GraniteServiceError(
            f"IAM returned empty access_token. Keys in response: {list(data.keys())}",
            user_message=_user_msg("service"),
        )

    return token, expires_in


def _get_iam_token(api_key: str) -> str:
    """
    Return a valid IAM Bearer token, fetching or refreshing as needed.
    Thread-safe. Never logs or returns the API key.
    """
    with _token_cache["lock"]:
        now = time.time()
        if (
            _token_cache["access_token"]
            and now < _token_cache["expires_at"] - TOKEN_REFRESH_BUFFER
        ):
            return _token_cache["access_token"]

        token, expires_in = _fetch_fresh_token(api_key)
        _token_cache["access_token"] = token
        _token_cache["expires_at"]   = now + expires_in
        return token


def invalidate_token_cache() -> None:
    """Force the next call_granite() to fetch a fresh IAM token."""
    with _token_cache["lock"]:
        _token_cache["access_token"] = None
        _token_cache["expires_at"]   = 0


def call_granite(
    prompt: str,
    *,
    max_new_tokens: int = MAX_NEW_TOKENS_DEFAULT,
    language: str = "en",
) -> str:
    """
    Send a prompt to IBM Granite and return the generated text.

    Args:
        prompt:         The full prompt string (RAG context already embedded).
        max_new_tokens: Maximum tokens to generate (default 700).
        language:       Language code for user-facing error messages.

    Returns:
        The generated text string (stripped).

    Raises:
        GraniteConfigError   – IBM_API_KEY or IBM_PROJECT_ID not set.
        GraniteAuthError     – API key rejected by IAM.
        GraniteTimeoutError  – Request timed out.
        GraniteServiceError  – HTTP error from watsonx.ai.
        GraniteError         – Other/unexpected error.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt must not be empty.")

    api_key, project_id, base_url = _read_config()
    endpoint = f"{base_url}/ml/v1/text/generation?version={WATSONX_API_VERSION}"

    payload = {
        "model_id":   GRANITE_MODEL_ID,
        "project_id": project_id,
        "input":      prompt,
        "parameters": {
            "decoding_method":    "greedy",
            "max_new_tokens":     max_new_tokens,
            "min_new_tokens":     10,
            "stop_sequences":     [],
            "repetition_penalty": 1.1,
        },
    }

    for attempt in range(2):   # attempt 0 → retry once on 401
        token = _get_iam_token(api_key)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        }

        try:
            resp = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=GRANITE_CALL_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            raise GraniteTimeoutError(
                f"Granite API timed out after {GRANITE_CALL_TIMEOUT}s.",
                user_message=_user_msg("timeout", language),
                language=language,
            )
        except requests.exceptions.RequestException as exc:
            raise GraniteServiceError(
                f"Granite network error: {exc}",
                user_message=_user_msg("unavailable", language),
                language=language,
            )

        # 401 → invalidate cache and retry once with a fresh token
        if resp.status_code == 401 and attempt == 0:
            invalidate_token_cache()
            continue

        # 400/403 → bad request or forbidden (misconfigured project_id / model_id)
        if resp.status_code in (400, 403):
            body = resp.text[:400]
            raise GraniteServiceError(
                f"Granite rejected request (HTTP {resp.status_code}): {body}",
                user_message=_user_msg("service", language),
                language=language,
            )

        # Other 4xx/5xx
        if not resp.ok:
            body = resp.text[:400]
            raise GraniteServiceError(
                f"Granite API error (HTTP {resp.status_code}): {body}",
                user_message=_user_msg("service", language),
                language=language,
            )

        # Parse successful response
        data    = resp.json()
        results = data.get("results", [])
        if results:
            return results[0].get("generated_text", "").strip()

        raise GraniteServiceError(
            f"Granite returned no results. Response keys: {list(data.keys())}",
            user_message=_user_msg("service", language),
            language=language,
        )

    # Should never be reached
    raise GraniteAuthError(
        "Granite authentication failed after token refresh retry.",
        user_message=_user_msg("auth", language),
        language=language,
    )


def get_granite_status() -> dict:
    """
    Return a safe status dictionary — no secrets included.
    Suitable for the /api/v1/granite-status endpoint.
    """
    api_key    = os.environ.get("IBM_API_KEY", "").strip()
    project_id = (
        os.environ.get("IBM_PROJECT_ID", "")
        or os.environ.get("GRANITE_PROJECT_ID", "")
    ).strip()
    base_url   = os.environ.get("IBM_WATSONX_URL", "").rstrip("/") or DEFAULT_WATSONX_URL

    token_cached = bool(
        _token_cache["access_token"]
        and time.time() < _token_cache["expires_at"] - TOKEN_REFRESH_BUFFER
    )
    token_expires_in = max(0, int(_token_cache["expires_at"] - time.time())) if token_cached else 0

    return {
        "model":           GRANITE_MODEL_ID,
        "endpoint":        f"{base_url}/ml/v1/text/generation?version={WATSONX_API_VERSION}",
        "iam_url":         IBM_IAM_URL,
        "IBM_API_KEY":     "configured" if api_key     else "MISSING",
        "IBM_PROJECT_ID":  "configured" if project_id  else "MISSING",
        "IBM_WATSONX_URL": base_url,
        "token_cached":    token_cached,
        "token_expires_in_seconds": token_expires_in if token_cached else None,
        "ready":           bool(api_key and project_id),
    }
