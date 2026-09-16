"""ASSTYLIST Fashion Radar v2.

A curated, freshness-aware menswear trend layer. The radar deliberately separates
"popular" from "fashion-interesting": virality is not treated as taste.

The signal model is designed for periodic refreshes from TikTok, Pinterest,
Instagram and Reddit exports/API adapters. The committed seed is a September
2026 editorial snapshot and must be refreshed rather than treated as timeless.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
import re


@dataclass(frozen=True)
class TrendSignal:
    slug: str
    label: str
    aliases: tuple[str, ...]
    score: float
    niche: float
    sources: tuple[str, ...]
    hero_items: tuple[str, ...]
    avoid_as_generic: bool = False


RADAR_VERSION = "2026-09-16"

# Seeded from current platform/editorial signals. Pinterest's 2026 men's report
# explicitly shows strong movement around modern craftsman/workwear, leather,
# accessory-first styling and pink accents; current menswear coverage also points
# toward broken-down prep/surf tailoring, romantic drape and military references.
CURRENT_SIGNALS: tuple[TrendSignal, ...] = (
    TrendSignal(
        "modern-craftsman", "Modern Craftsman",
        ("vintage workwear", "american workwear", "chore coat", "field jacket", "m-65", "barn jacket", "utility"),
        0.91, 0.78, ("pinterest", "instagram", "reddit"),
        ("chore coat", "field jacket", "washed denim", "rugged knit", "silver chain"),
    ),
    TrendSignal(
        "leather-weather", "Leather Weather",
        ("leather jacket", "motorcycle jacket", "moto", "washed leather", "leather tote", "leather loafers"),
        0.88, 0.82, ("pinterest", "instagram", "reddit"),
        ("weathered leather jacket", "leather boot", "leather bag", "leather cap"),
    ),
    TrendSignal(
        "broken-down-prep", "Broken-down Prep",
        ("broken down tailoring", "surf prep", "surfer prep", "ivy surf", "beach tailoring", "relaxed ivy"),
        0.87, 0.90, ("instagram", "reddit", "pinterest"),
        ("soft blazer", "silk board short", "oxford", "rugby knit", "boat shoe"),
    ),
    TrendSignal(
        "romantic-menswear", "Romantic Menswear",
        ("romantic menswear", "soft tailoring", "drape", "sheer", "lace menswear", "fluid tailoring", "victorian"),
        0.84, 0.91, ("instagram", "pinterest", "reddit"),
        ("draped shirt", "sheer layer", "soft trouser", "long coat"),
    ),
    TrendSignal(
        "military-romance", "Military Romance",
        ("military tailoring", "british military", "victorian military", "military floral", "military romantic"),
        0.82, 0.94, ("instagram", "pinterest", "reddit"),
        ("military jacket", "ornamental shirt", "floral accent", "polished boot"),
    ),
    TrendSignal(
        "archive-reconstruction", "Archive Reconstruction",
        ("archive", "deadstock", "reconstruction", "deconstructed", "reworked", "upcycled archive"),
        0.86, 0.96, ("instagram", "reddit", "pinterest"),
        ("reworked jacket", "archive denim", "deconstructed shirt", "deadstock knit"),
    ),
    TrendSignal(
        "technical-romantic", "Technical Romantic",
        ("technical utility", "techwear", "technical nylon", "mesh utility", "gorp tailoring", "utility tailoring"),
        0.79, 0.88, ("tiktok", "instagram", "reddit"),
        ("technical shell", "wide cargo", "mesh layer", "trail shoe"),
    ),
    TrendSignal(
        "americana-90s", "90s Americana Recut",
        ("90s americana", "americana", "90s sportswear", "straight leg jeans", "plaid", "frontier knit"),
        0.80, 0.74, ("pinterest", "instagram", "reddit"),
        ("straight denim", "plaid overshirt", "frontier knit", "baseball cap"),
    ),
    TrendSignal(
        "accessory-first", "Accessory-first Styling",
        ("accessory first", "chain necklace", "silver cuff", "bag charm", "statement belt", "pins charms"),
        0.83, 0.89, ("pinterest", "tiktok", "instagram"),
        ("silver chain", "cuff", "charm", "statement belt"),
    ),
    TrendSignal(
        "pink-accent", "Dusty Pink Accent",
        ("dusty pink", "pink shirt", "pink beanie", "pink scarf", "rose tie", "pink accent"),
        0.77, 0.86, ("pinterest", "instagram", "tiktok"),
        ("dusty pink shirt", "rose tie", "pink knit"),
    ),
    TrendSignal(
        "sport-couture", "Sport Couture",
        ("sport couture", "track tailoring", "football tailoring", "racket tailoring", "retro sport"),
        0.75, 0.84, ("tiktok", "instagram", "pinterest"),
        ("track jacket", "pleated trouser", "retro trainer", "sport scarf"),
    ),
    # These are still searchable, but should not dominate a niche recommendation.
    TrendSignal(
        "quiet-luxury", "Quiet Luxury",
        ("quiet luxury", "old money", "stealth wealth", "minimal luxury"),
        0.52, 0.35, ("pinterest", "instagram", "reddit"),
        ("unbranded knit", "tailored trouser", "loafer"), True,
    ),
    TrendSignal(
        "generic-gorpcore", "Generic Gorpcore",
        ("gorpcore", "gorp"),
        0.48, 0.42, ("tiktok", "instagram", "reddit"),
        ("shell", "cargo", "trail shoe"), True,
    ),
)


STALE_GENERIC = frozenset({
    "old money", "clean girl", "clean boy", "blokette", "basic bastard",
    "drip", "hypebeast", "logo streetwear", "generic gorpcore",
})


def _tokens(text: str) -> str:
    return re.sub(r"[^a-zа-я0-9]+", " ", (text or "").lower().replace("ё", "е")).strip()


def signal_matches(text: str, signal: TrendSignal) -> int:
    haystack = f" {_tokens(text)} "
    return sum(1 for alias in signal.aliases if f" {_tokens(alias)} " in haystack)


def radar_for(text: str, *, niche_level: int = 70) -> list[dict]:
    """Return current signals sorted by fashion relevance, not raw popularity."""
    results: list[dict] = []
    for signal in CURRENT_SIGNALS:
        hits = signal_matches(text, signal)
        if not hits:
            continue
        niche_bonus = (niche_level / 100.0) * signal.niche * 0.18
        generic_penalty = 0.16 if signal.avoid_as_generic and niche_level >= 60 else 0.0
        relevance = max(0.0, signal.score + niche_bonus - generic_penalty)
        results.append({
            "slug": signal.slug,
            "label": signal.label,
            "score": round(min(1.0, relevance), 3),
            "niche": signal.niche,
            "hits": hits,
            "sources": signal.sources,
            "heroItems": signal.hero_items,
            "avoidAsGeneric": signal.avoid_as_generic,
        })
    return sorted(results, key=lambda row: (-row["score"], -row["niche"], row["slug"]))


def freshness_weight(published_at: date | None, half_life_days: float = 45.0) -> float:
    """Exponential freshness decay for externally ingested social signals."""
    if published_at is None:
        return 0.55
    age = max(0, (date.today() - published_at).days)
    return round(math.exp(-math.log(2) * age / half_life_days), 4)


def source_diversity_score(sources: list[str] | tuple[str, ...]) -> float:
    """Reward corroboration across independent social surfaces."""
    unique = {str(source).lower() for source in sources if source}
    return round(min(1.0, 0.45 + 0.14 * max(0, len(unique) - 1)), 3)


__all__ = ["CURRENT_SIGNALS", "RADAR_VERSION", "STALE_GENERIC", "TrendSignal", "freshness_weight", "radar_for", "source_diversity_score"]
