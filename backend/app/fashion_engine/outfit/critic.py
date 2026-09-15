"""FashionCritic — порт ``src/outfit/FashionCritic.js``.

Намеренно придирчивая проверка готового образа: слабый силуэт, отсутствие
героя, нет контраста, «замусоренность» масс-маркетом, разъехавшийся цвет.
Может одобрить (APPROVE) или потребовать пересборку (REBUILD).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..types import OutfitCandidate, ProductItem


@dataclass
class CriticVerdict:
    decision: str
    feedback: list[str] = field(default_factory=list)
    issues: int = 0
    score_adjustment: float = 0.0


class FashionCritic:
    def critique(self, outfit: OutfitCandidate, score_breakdown: dict[str, float] | None = None) -> CriticVerdict:
        feedback: list[str] = []
        issues = 0
        items: list[ProductItem] = outfit.items or []

        silhouettes = [
            entry
            for item in items
            for entry in (getattr(item.fashion_attributes, "silhouette", []) or [])
        ]
        if not silhouettes or all(entry == "regular" for entry in silhouettes):
            feedback.append("Silhouette is too predictable / safe. Needs stronger shape language.")
            issues += 2

        fashion_scores = [float(item.fashion_score or 50) for item in items]
        max_score = max(fashion_scores) if fashion_scores else 0.0
        # Отличие порта: «герой» определяется ещё и относительно самого образа.
        # В каталоге asStylist вещи масс-маркета дают fashion score ниже 72, и
        # абсолютный порог оригинала ругался даже на образ с явным акцентом;
        # теперь вещь-акцент (выше среднего на 8+) считается героем.
        average_score = sum(fashion_scores) / len(fashion_scores) if fashion_scores else 0.0
        if max_score < 72 and (max_score - average_score) < 8:
            feedback.append("No clear hero piece. The outfit lacks a strong focal point.")
            issues += 2

        has_sheer = any(
            getattr(item.fashion_attributes, "material", "") == "sheer" or "sheer" in (item.tags or [])
            for item in items
        )
        has_structure = any(
            {"structured", "oversized", "deconstructed"}
            & set(getattr(item.fashion_attributes, "silhouette", []) or [])
            for item in items
        )
        if not has_sheer and not has_structure and len(items) > 2:
            feedback.append("Insufficient contrast in texture or volume.")
            issues += 1

        generic_count = len([item for item in items if item.taste_category == "generic" or (item.generic_score or 0) > 65])
        if generic_count >= 2:
            feedback.append("Too many generic items. Dilutes the fashion strength of the look.")
            issues += 2

        if not outfit.styling_thesis or outfit.styling_thesis == "Contemporary Editorial":
            feedback.append("Styling thesis is weak or generic. Needs a sharper cultural idea.")
            issues += 1

        colors = {
            item.fashion_attributes.color
            for item in items
            if item.fashion_attributes and item.fashion_attributes.color not in (None, "", "unknown")
        }
        if len(colors) > 4:
            feedback.append("Color story is fragmented.")
            issues += 1

        if fashion_scores:
            average = sum(fashion_scores) / len(fashion_scores)
            if average < 68:
                feedback.append("Overall item quality is not high enough for a strong editorial-feeling look.")
                issues += 2

        if issues >= 5:
            decision, adjustment = "REBUILD", -15.0
            feedback.append("CRITICAL: Outfit needs full rebuild.")
        elif issues >= 3:
            decision, adjustment = "REBUILD", -8.0
            feedback.append("Several issues detected — recommend refinement.")
        elif issues == 0:
            decision, adjustment = "APPROVE", 5.0
            feedback.append("Strong, coherent, fashion-forward look. Approved.")
        else:
            decision, adjustment = "APPROVE", 0.0
            feedback.append("Minor notes only. Acceptable.")

        return CriticVerdict(decision=decision, feedback=feedback, issues=issues, score_adjustment=adjustment)
