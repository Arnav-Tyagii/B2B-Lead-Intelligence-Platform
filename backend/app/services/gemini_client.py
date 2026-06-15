"""Rate-limit-aware Gemini client.

Bakes in every free-tier guardrail:
  - **Concurrency cap** via a semaphore (free tier allows only a few req/min).
  - **Exponential backoff on HTTP 429** (ResourceExhausted), capped retries.
  - **Single-flight**: concurrent identical prompts share one in-flight call.
  - **Fail-fast disable**: on a fatal auth/model error we disable Gemini for the
    rest of the process and log ONCE — we never retry it per record. Callers then
    fall back to the deterministic enricher.
  - **Defensive JSON parsing**: strips code fences and extracts the JSON object.

All failures surface as `GeminiUnavailable`, so the orchestrator has a single
exception type to catch before falling back.
"""

import asyncio
import hashlib
import json

import google.generativeai as genai

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Free tier is ~10-15 req/min; keep live concurrency tiny.
_MAX_CONCURRENCY = 2
_MAX_RETRIES = 4
_INITIAL_BACKOFF_SECONDS = 2.0

_semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)
_inflight: dict[str, "asyncio.Task[dict]"] = {}

# Process-wide kill switch flipped on a fatal error (bad key / bad model).
_disabled = False
_configured = False


class GeminiUnavailable(Exception):
    """Raised for any condition where the caller should use the fallback."""


def is_disabled() -> bool:
    return _disabled


def _disable(reason: str) -> None:
    """Flip the kill switch and log exactly once."""
    global _disabled
    if not _disabled:
        _disabled = True
        logger.error("Gemini disabled for the rest of this process: %s", reason)


def _ensure_configured() -> None:
    global _configured
    if not _configured:
        genai.configure(api_key=get_settings().gemini_api_key)
        _configured = True


def _classify(exc: Exception) -> str:
    """Map an SDK/transport exception to 'rate_limit' | 'fatal' | 'transient'
    by inspecting the type/message — avoids hard imports of google.api_core."""
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if "resourceexhausted" in name or "429" in msg or "quota" in msg or "rate" in msg:
        return "rate_limit"
    if any(
        k in name for k in ("permissiondenied", "unauthenticated", "invalidargument", "notfound")
    ) or any(k in msg for k in ("api key", "permission", "unauthenticated", "not found", "401", "403")):
        return "fatal"
    return "transient"


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a model response that may be fenced,
    chatty, or contain trailing content after the object.

    We seek the first '{' (which also skips a ```json fence prefix) and use
    `raw_decode`, which parses one complete JSON value and ignores anything after
    it — so a response like `{...}\\n{...}` or `{...}\\nNote: ...` still works."""
    start = text.find("{")
    if start == -1:
        raise GeminiUnavailable("No JSON object found in Gemini response")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as exc:
        raise GeminiUnavailable(f"Malformed JSON from Gemini: {exc}") from exc
    if not isinstance(obj, dict):
        raise GeminiUnavailable("Gemini response was not a JSON object")
    return obj


async def _do_generate(prompt: str) -> dict:
    settings = get_settings()
    _ensure_configured()
    model = genai.GenerativeModel(settings.gemini_model)

    backoff = _INITIAL_BACKOFF_SECONDS
    async with _semaphore:  # concurrency cap
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await model.generate_content_async(prompt)
                return _extract_json(response.text)
            except GeminiUnavailable:
                raise  # parsing error — don't retry, just fall back
            except Exception as exc:  # noqa: BLE001 - we classify below
                kind = _classify(exc)
                if kind == "fatal":
                    _disable(str(exc))
                    raise GeminiUnavailable(f"fatal error: {exc}") from exc
                if attempt == _MAX_RETRIES:
                    raise GeminiUnavailable(f"{kind} after {attempt} attempts: {exc}") from exc
                logger.warning(
                    "Gemini %s (attempt %d/%d), backing off %.1fs",
                    kind, attempt, _MAX_RETRIES, backoff,
                )
                await asyncio.sleep(backoff)
                backoff *= 2  # exponential backoff
    raise GeminiUnavailable("exhausted retries")  # unreachable, satisfies type checker


async def generate_json(prompt: str) -> dict:
    """Generate and parse a JSON object from Gemini, with single-flight dedupe.

    Raises GeminiUnavailable on any failure (incl. when disabled / no key)."""
    if _disabled:
        raise GeminiUnavailable("Gemini is disabled")
    if not get_settings().gemini_enabled:
        raise GeminiUnavailable("No Gemini API key configured")

    # Single-flight: identical concurrent prompts share ONE in-flight Task.
    # Using a Task (vs a bare Future) means every caller awaits the same object,
    # so a failure is always retrieved by an awaiter — no "exception never
    # retrieved" warnings.
    key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    existing = _inflight.get(key)
    if existing is not None:
        return await existing

    task: asyncio.Task[dict] = asyncio.ensure_future(_do_generate(prompt))
    _inflight[key] = task
    try:
        return await task
    finally:
        _inflight.pop(key, None)
