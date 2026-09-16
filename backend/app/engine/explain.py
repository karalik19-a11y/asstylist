"""Turns scoring output into human-readable Russian explanations."""

from __future__ import annotations

from typing import Any

from .colors import COLORS
from .options import SLOT_LABELS, mood_by_id, style_by_id
from .palette import CONTRAST_RU, METAL_RU, PaletteProfile
from .ranking import ScoredItem, describe_colors

FIT_RU = {
    "slim": "приталенный крой",
    "regular": "прямой крой",
    "relaxed": "свободный крой",
    "oversize": "оверсайз",
}

FORMALITY_RU = {0: "очень неформально", 1: "неформально", 2: "кэжуал", 3: "нарядно", 4: "формально"}


def item_reasons(scored: ScoredItem, ctx_info: dict[str, Any], limit: int = 4) -> list[str]:
    b = scored.breakdown
    item = scored.item
    reasons: list[tuple[float, str]] = []

    if b.get("style", 0) >= 0.9:
        reasons.append((b["style"], f"Точное попадание в стиль «{style_by_id(ctx_info['style'])['label']}»"))
    elif b.get("style", 0) >= 0.5:
        reasons.append((b["style"], "Перекликается с выбранным стилем"))

    if b.get("color", 0) >= 0.85:
        reasons.append(
            (b["color"], f"Оттенок ({describe_colors(item.colors)}) входит в вашу палитру «{ctx_info['palette_label']}»")
        )
    elif b.get("color", 0) >= 0.6:
        reasons.append((b["color"], "Цвет спокойно сочетается с остальными вещами образа"))

    if b.get("silhouette", 0) >= 0.9:
        fit = FIT_RU.get(item.fit, item.fit)
        reasons.append((b["silhouette"], f"{fit.capitalize()} подходит силуэту «{ctx_info['silhouette_ru']}»"))
    elif b.get("silhouette", 0) >= 0.6:
        reasons.append((b["silhouette"], "Нейтральная посадка — не конфликтует с силуэтом"))

    if b.get("mood", 0) >= 0.9:
        reasons.append((b["mood"], f"Работает на настроение «{mood_by_id(ctx_info['mood'])['label']}»"))
    elif b.get("mood", 0) >= 0.55:
        reasons.append((b["mood"], "Поддерживает общее настроение образа"))

    if b.get("formality", 0) >= 0.85:
        reasons.append((b["formality"], f"Уровень формальности совпадает с поводом ({FORMALITY_RU.get(item.formality, 'кэжуал')})"))

    if b.get("season", 0) >= 0.95:
        reasons.append((b["season"] * 0.9, "Сезон подходит — вещь будет в ходу"))

    if b.get("value", 0) >= 0.7:
        reasons.append(
            (b["value"], f"{item.rating:.1f}★ при {item.reviews_count} отзывах — честная цена за качество")
        )

    if b.get("verification", 0) >= 0.9:
        reasons.append((b["verification"] * 0.85, "Товар проверен: цена и ссылка подтверждены"))
    elif item.verification_status == "warning":
        reasons.append((0.4, "Товар помечен: часть данных не подтверждена"))

    reasons.sort(key=lambda pair: -pair[0])
    seen: set[str] = set()
    out: list[str] = []
    for _score, text in reasons:
        if text not in seen:
            seen.add(text)
            out.append(text)
    return out[:limit] if out else ["Подходит по базовым параметрам образа"]


def look_tips(
    body_tips: list[str],
    palette_info: dict[str, Any],
    style: str,
    picked: dict[str, ScoredItem],
) -> list[str]:
    tips: list[str] = list(body_tips[:2])

    colors_in_look: list[str] = []
    for scored in picked.values():
        colors_in_look.extend(scored.item.colors)
    neutrals = [c for c in colors_in_look if COLORS.get(c) and COLORS[c].neutral]
    accents = [c for c in colors_in_look if COLORS.get(c) and not COLORS[c].neutral]

    if len(set(accents)) > 2:
        tips.append("В образе больше двух акцентных цветов — оставьте один, остальное уведите в нейтральную гамму.")
    elif accents:
        tips.append(f"Акцент образа — {describe_colors(list(dict.fromkeys(accents))[:1])}; держите его в одной вещи.")
    elif neutrals:
        tips.append("Образ собран на нейтральной гамме — добавьте один аксессуар цветом, чтобы не выглядело плоско.")

    if "outerwear" in picked and "top" in picked:
        tips.append("Верхняя одежда расстёгнута — так вертикаль длины вытягивает силуэт.")

    style_label = style_by_id(style)["label"]
    tips.append(f"Чтобы усилить «{style_label.lower()}», держите минимум деталей и максимум качества ткани.")
    if "shoes" in picked and "bag" in picked:
        tips.append("Обувь и сумка в одной температуре (обе тёплые или обе холодные) — самый быстрый способ собрать образ.")
    return tips[:6]


def look_summary(
    style: str,
    mood: str,
    occasion: str,
    total_rub: float,
    budget_rub: float,
    picked: dict[str, ScoredItem],
    score: float,
) -> str:
    style_label = style_by_id(style)["label"]
    mood_label = mood_by_id(mood)["label"]
    key_item = ""
    if picked:
        hero = max(picked.values(), key=lambda s: s.score * min(1.0, s.item.price_rub / max(budget_rub, 1) + 0.4))
        key_item = f" Ключ образа — {hero.item.name.lower()} ({SLOT_LABELS.get(hero.item.category, hero.item.category).lower()})."
    left = max(0.0, budget_rub - total_rub)
    return (
        f"«{style_label}» в настроении «{mood_label.lower()}»: {len(picked)} вещей на "
        f"{total_rub:,.0f} ₽ из {budget_rub:,.0f} ₽ (остаток {left:,.0f} ₽).{key_item} "
        f"Оценка цельности образа — {score:.0f}/100."
    )


#: Повод по-русски для персонального объяснения (не дублируем OCCASION_OPTIONS,
#: чтобы explain оставался независимым от подписей UI).
OCCASION_RU = {
    "everyday": "на каждый день",
    "work": "на работу",
    "date": "на свидание",
    "party": "на вечеринку",
    "travel": "в поездку",
    "event": "на событие",
}


def personal_note(
    *,
    style: str,
    mood: str,
    occasion: str,
    palette: PaletteProfile,
    body: Any,
    picked: dict[str, Any],
    total_rub: float,
    budget_rub: float,
) -> str:
    """2–3 коротких предложения, почему образ собран именно для этого
    пользователя: цветотип по фото, силуэт, повод и бюджет."""
    parts: list[str] = []
    style_label = style_by_id(style)["label"]
    mood_label = mood_by_id(mood)["label"]

    look_colors: list[str] = []
    for scored in picked.values():
        item_colors = getattr(getattr(scored, "item", None), "colors", None) or []
        look_colors.extend(str(cid) for cid in item_colors)
    palette_hits = [cid for cid in dict.fromkeys(look_colors) if cid in set(palette.recommended)]
    hit_names = describe_colors(palette_hits[:3]) if palette_hits else ""

    if palette.source != "defaults":
        undertone_ru = {"warm": "тёплый", "cool": "холодный", "neutral": "нейтральный"}.get(
            palette.undertone, palette.undertone
        )
        contrast_ru = CONTRAST_RU.get(palette.contrast, palette.contrast)
        color_part = f"гамма из вашей палитры — {hit_names}" if hit_names else "гамма из вашей палитры"
        metal_ru = METAL_RU.get(palette.metal, palette.metal)
        parts.append(
            f"Под ваш цветотип «{palette.season_label}» ({undertone_ru} подтон, контраст {contrast_ru}) "
            f"собрана {color_part}; фурнитура и металл — {metal_ru}."
        )
    elif hit_names:
        parts.append(f"Оттенки ({hit_names}) взяты из ваших любимых и фирменных цветов стиля.")
    else:
        parts.append("Палитра собрана из фирменных оттенков стиля.")

    fits: list[str] = []
    for scored in picked.values():
        fit = getattr(getattr(scored, "item", None), "fit", None)
        if fit and fit not in fits:
            fits.append(str(fit))
    fit_ru = " и ".join(FIT_RU.get(fit, fit) for fit in fits[:2])
    silhouette_ru = getattr(body, "silhouette_ru", "") or "ваш силуэт"
    if fit_ru:
        parts.append(f"Крой — под силуэт «{silhouette_ru}» и параметры фигуры: {fit_ru}.")
    else:
        parts.append(f"Крой — под силуэт «{silhouette_ru}» и параметры фигуры.")

    occasion_ru = OCCASION_RU.get(occasion, "на каждый день")
    note = (
        f"Стиль «{style_label.lower()}» и настроение «{mood_label.lower()}» собраны {occasion_ru}: "
        + " ".join(parts)
    )
    if palette.source == "defaults":
        note += " Добавьте фото — тогда учтём цветотип и контраст внешности."
    return note
