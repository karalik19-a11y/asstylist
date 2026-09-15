"""Budget optimiser: fills the look's slots with the best items under budget.

Deterministic two-phase search (repair down, then upgrade up) — no randomness,
so the same input always produces the same look.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ranking import ScoredItem

MAX_REPAIR_ITERATIONS = 400
MAX_UPGRADE_ITERATIONS = 200


@dataclass
class LookDraft:
    picked: dict[str, ScoredItem] = field(default_factory=dict)
    total_rub: float = 0.0
    budget_rub: float = 0.0
    over_budget: bool = False
    dropped_slots: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rub": self.total_rub,
            "budget_rub": self.budget_rub,
            "over_budget": self.over_budget,
            "dropped_slots": self.dropped_slots,
            "warnings": self.warnings,
            "budget_utilization": round(self.total_rub / self.budget_rub, 3) if self.budget_rub else 0.0,
        }


def _best(pool: list[ScoredItem]) -> ScoredItem:
    ordered = sorted(pool, key=lambda c: (-c.score, c.item.price_rub, c.item.sku))
    return ordered[0]


def build_look(
    candidates_by_slot: dict[str, list[ScoredItem]],
    slot_specs: dict[str, dict[str, Any]],
    budget_rub: float,
    flex: float = 1.35,
) -> LookDraft:
    slots = sorted(slot_specs, key=lambda s: slot_specs[s].get("order", 0))
    weights = {s: float(slot_specs[s].get("weight", 1.0)) for s in slots}
    weight_sum = sum(weights.values()) or 1.0
    allocation = {s: budget_rub * weights[s] / weight_sum for s in slots}

    picked: dict[str, ScoredItem] = {}
    warnings: list[str] = []
    for slot in slots:
        cands = candidates_by_slot.get(slot) or []
        if not cands:
            if slot_specs[slot].get("required"):
                warnings.append(f"Нет доступных позиций в категории «{slot}»")
            continue
        affordable = [c for c in cands if c.item.price_rub <= allocation[slot] * flex]
        pool = affordable or [min(cands, key=lambda c: (c.item.price_rub, c.item.sku))]
        picked[slot] = _best(pool)

    draft = LookDraft(picked=picked, budget_rub=budget_rub, warnings=warnings)

    def total() -> float:
        return round(sum(p.item.price_rub for p in picked.values()), 2)

    # --- phase 1: repair down until we fit the budget -------------------
    for _ in range(MAX_REPAIR_ITERATIONS):
        if total() <= budget_rub:
            break
        best: tuple[float, str, ScoredItem] | None = None  # (loss per ruble, slot, next)
        for slot, current in list(picked.items()):
            cheaper = [c for c in (candidates_by_slot.get(slot) or []) if c.item.price_rub < current.item.price_rub - 0.01]
            if not cheaper:
                continue
            nxt = _best(cheaper)
            loss = current.score - nxt.score
            saved = current.item.price_rub - nxt.item.price_rub
            ratio = loss / max(saved, 1.0)
            if best is None or ratio < best[0]:
                best = (ratio, slot, nxt)
        if best is not None:
            picked[best[1]] = best[2]
            continue
        droppable = [s for s in picked if not slot_specs.get(s, {}).get("required", True)]
        if not droppable:
            break
        droppable.sort(key=lambda s: (picked[s].score, -picked[s].item.price_rub, s))
        dropped = droppable[0]
        del picked[dropped]
        draft.dropped_slots.append(dropped)

    # --- phase 2: fill optional slots we don't have yet -----------------
    for slot in slots:
        if slot in picked:
            continue
        cands = candidates_by_slot.get(slot) or []
        headroom = budget_rub - total()
        affordable = [c for c in cands if c.item.price_rub <= headroom and c.score >= 0.3]
        if affordable:
            picked[slot] = _best(affordable)
            if slot in draft.dropped_slots:
                draft.dropped_slots.remove(slot)

    # --- phase 3: spend the remainder on the best upgrades --------------
    for _ in range(MAX_UPGRADE_ITERATIONS):
        current_total = total()
        best_upgrade: tuple[float, str, ScoredItem] | None = None  # (gain per ruble, slot, next)
        for slot, current in picked.items():
            upgrades = [
                c
                for c in (candidates_by_slot.get(slot) or [])
                if c.item.price_rub > current.item.price_rub + 0.01
                and current_total - current.item.price_rub + c.item.price_rub <= budget_rub
            ]
            if not upgrades:
                continue
            nxt = _best(upgrades)
            gain = nxt.score - current.score
            if gain <= 0:
                continue
            cost = nxt.item.price_rub - current.item.price_rub
            ratio = gain / max(cost, 1.0)
            if best_upgrade is None or ratio > best_upgrade[0]:
                best_upgrade = (ratio, slot, nxt)
        if best_upgrade is None:
            break
        picked[best_upgrade[1]] = best_upgrade[2]

    draft.total_rub = total()
    draft.over_budget = draft.total_rub > budget_rub + 0.01
    if draft.over_budget:
        draft.warnings.append("Бюджет превышен: в каталоге не хватило более дешёвых позиций")
    if draft.dropped_slots:
        draft.warnings.append("Часть необязательных вещей убрана, чтобы уложиться в бюджет")
    return draft
