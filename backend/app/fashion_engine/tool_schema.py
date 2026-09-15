"""Схема инструмента для function-calling агентов (порт ``TOOL_SCHEMA``)."""

from __future__ import annotations

TOOL_SCHEMA: dict = {
    "name": "asystylist_create_outfit",
    "description": (
        "Fashion Discovery & Outfit Intelligence Engine. "
        "Understands aesthetic intent, discovers real designer / archive / niche pieces, "
        "and builds a coherent outfit around a styling thesis. "
        "Use when the user asks for outfit recommendations, styling, fashion looks, "
        "or wants clothes matching a specific aesthetic (industrial, romantic, gothic, minimal, archive, etc.)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language description of the desired look / aesthetic / garments. Can be in any language.",
            },
            "nicheLevel": {
                "type": "number",
                "description": "0 = mainstream, 50 = contemporary, 80 = niche, 100 = extremely experimental. Default 60.",
                "minimum": 0,
                "maximum": 100,
            },
            "budgetMax": {
                "type": "number",
                "description": "Maximum total budget for the outfit (optional).",
            },
            "currency": {
                "type": "string",
                "description": "Currency code, e.g. RUB, EUR, USD. Default RUB.",
            },
            "aesthetics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Preferred aesthetics, e.g. ['industrial','dark','romantic']",
            },
            "occasion": {
                "type": "string",
                "description": "e.g. everyday, editorial, night, work",
            },
            "fitPreference": {
                "type": "string",
                "description": "e.g. relaxed, slim, oversized, regular",
            },
        },
        "required": ["query"],
    },
    "returns": (
        "JSON: {aesthetic, stylingThesis, outfitScore, items[], stylingLogic, "
        "references[], alternatives[], criticFeedback[], meta{engineVersion, queriesUsed}}"
    ),
}
