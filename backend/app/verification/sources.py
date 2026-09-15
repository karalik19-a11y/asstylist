"""Source registry — where catalog products come from and how much we trust them."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    id: str
    label: str
    kind: str  # demo | marketplace | brand
    trust: float
    note: str


SOURCES: dict[str, Source] = {
    s.id: s
    for s in [
        Source("demo", "asStylist Select", "demo", 0.85, "Фирменная подборка asStylist"),
        Source("ozon", "Ozon", "marketplace", 0.9, "Маркетплейс"),
        Source("wildberries", "Wildberries", "marketplace", 0.9, "Маркетплейс"),
        Source("lamoda", "Lamoda", "marketplace", 0.9, "Fashion-маркетплейс"),
        Source("12storeez", "12 STOREEZ", "brand", 1.0, "Официальный бренд"),
        Source("uniqlo", "Uniqlo", "brand", 1.0, "Официальный бренд"),
        Source("sokolov", "SOKOLOV", "brand", 1.0, "Официальный бренд"),
    ]
}


def trust_for(source_id: str) -> float:
    return SOURCES.get(source_id, Source("unknown", source_id, "unknown", 0.5, "")).trust


def source_list() -> list[dict[str, object]]:
    return [
        {"id": s.id, "label": s.label, "kind": s.kind, "trust": s.trust, "note": s.note}
        for s in SOURCES.values()
    ]
