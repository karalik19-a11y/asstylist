"""Optional remote multimodal analysis.

Kept behind a provider switch. If the network call fails for any reason we
silently fall back to the local Pillow analyser — the product must never break
because an external API is down or unconfigured.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from ..config import settings
from .analyzer import analyze_photo

PROMPT = (
    "Ты fashion-аналитик. По фото определи: person_detected (bool), "
    "temperature (warm|cool|neutral), depth (light|medium|deep), chroma (soft|clear), "
    "dominant_colors (до 5 цветов из списка: black, charcoal, grey, light_grey, white, ivory, "
    "beige, sand, camel, brown, chocolate, terracotta, burgundy, red, coral, pink, blush, lavender, "
    "violet, blue, navy, sky, teal, emerald, olive, khaki, green, mustard, yellow, orange, silver, gold). "
    "Ответь строго JSON без пояснений."
)


def _merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        if value is None:
            continue
        merged[key] = value
    merged["source"] = extra.get("source", base.get("source", "local"))
    if extra.get("ok"):
        merged["palette_confidence"] = min(0.95, float(extra.get("palette_confidence", 0.75)))
    return merged


def _call_openai(data: bytes) -> dict[str, Any] | None:
    payload = {
        "model": settings.openai_model,
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(data).decode()}"},
                    },
                ],
            }
        ],
    }
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json=payload,
        timeout=20.0,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    parsed = json.loads(text[text.find("{") : text.rfind("}") + 1])
    parsed["source"] = f"openai:{settings.openai_model}"
    parsed["ok"] = True
    return parsed


def _call_gemini(data: bytes) -> dict[str, Any] | None:
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT},
                    {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(data).decode()}},
                ]
            }
        ]
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    response = httpx.post(url, params={"key": settings.gemini_api_key}, json=payload, timeout=20.0)
    response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(text[text.find("{") : text.rfind("}") + 1])
    parsed["source"] = f"gemini:{settings.gemini_model}"
    parsed["ok"] = True
    return parsed


def analyze(data: bytes) -> dict[str, Any]:
    """Analyse a photo, preferring the configured remote provider when available."""
    local = analyze_photo(data, provider_label="local")
    provider = settings.effective_ai_provider
    if provider == "local":
        return local
    try:
        remote = _call_openai(data) if provider == "openai" else _call_gemini(data)
    except Exception:  # noqa: BLE001 — any remote failure must degrade gracefully
        local["remote_fallback"] = True
        return local
    if not remote:
        local["remote_fallback"] = True
        return local
    return _merge(local, remote)
