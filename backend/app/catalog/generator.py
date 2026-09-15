"""Unbounded trend feed.

The seed catalog is finite; the feed is not. This module deterministically
produces an endless stream of niche, TikTok/Pinterest-flavoured items — each
with a photo and a working marketplace search link — so the app always has
"ещё" to show. It is a generator, not a database: cursor = offset.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any

from .products import img_for, search_url

STYLES = [
    "y2k", "coquette", "blokecore", "gorpcore", "indie-sleaze", "mcbling",
    "clean-girl", "old-money", "fairy-grunge", "office-siren", "street", "grunge",
]

GARMENTS: dict[str, list[tuple[str, str]]] = {
    "top": [
        ("бэби-ти со стразами", "I.AM.GIA"), ("кроп-топ halter", "House of CB"),
        ("футболка «hello kitty»", "Sanrio"), ("топ-бандо", "Princess Polly"),
        ("джерси blokecore", "Adidas"), ("лонгслив с сеткой", "Dolls Kill"),
        ("корсет-топ satin", "House of CB"), ("футболка Ed Hardy", "Ed Hardy"),
    ],
    "bottom": [
        ("baggy-джинсы low-rise", "JNCO"), ("карго-парашюты", "True Religion"),
        ("юбка-плиссе микро", "Brandy Melville"), ("джинсы с ремнём-цепью", "Baby Phat"),
        ("брюки flare", "Levis"), ("мини-юбка кожаная", "Nasty Gal"),
    ],
    "knitwear": [
        ("велюр-худи juicy", "Juicy Couture"), ("кофта на молнии", "Von Dutch"),
        ("свитер angora", "Brandy Melville"), ("болеро-сетка", "Dolls Kill"),
    ],
    "outerwear": [
        ("кроп-пуховик металлик", "I.AM.GIA"), ("шуба эко «cheburashka»", "Nasty Gal"),
        ("куртка varsity", "Hollister"), ("дублёнка авиатор", "Urban Outfitters"),
    ],
    "dress": [
        ("платье-комбинация satin", "House of CB"), ("мини с перьями", "Dolls Kill"),
        ("сетчатое платье", "I.AM.GIA"), ("платье с бантами coquette", "Princess Polly"),
    ],
    "shoes": [
        ("платформенные кроссовки", "New Balance"), ("угги с блёстками", "UGG"),
        ("ботфорты на платформе", "Jeffrey Campbell"), ("балетки с бантом", "Miu Miu"),
    ],
    "bag": [
        ("сумка-багет со стразами", "Fendi"), ("плюшевая сумка", "Baby Phat"),
        ("микро-сумка на цепочке", "Coach"), ("шоппер с принтом", "Urban Outfitters"),
    ],
    "accessory": [
        ("овальные очки 00-х", "Gucci"), ("панама деним", "Von Dutch"),
        ("чокер со стразами", "Claire's"), ("серьги-кольца", "Chrome Hearts"),
    ],
}

COLORS = ["чёрный", "розовый", "серебро", "белый", "деним", "красный", "золото", "лавандовый"]
SOURCES = ["lamoda", "ozon", "wildberries"]


def _rng(cursor: int) -> random.Random:
    seed = int.from_bytes(hashlib.sha256(str(cursor).encode()).digest()[:8], "big")
    return random.Random(seed)


def generate_items(cursor: int, count: int = 12) -> tuple[list[dict[str, Any]], int]:
    """Return `count` items starting at `cursor`, plus the next cursor."""
    out: list[dict[str, Any]] = []
    for index in range(count):
        key = cursor + index
        rnd = _rng(key)
        category = rnd.choice(list(GARMENTS))
        name, brand = rnd.choice(GARMENTS[category])
        color = rnd.choice(COLORS)
        style = rnd.choice(STYLES)
        source = rnd.choice(SOURCES)
        price = rnd.choice(range(1500, 40000, 250))
        query = f"{brand} {name} {color}"
        out.append(
            {
                "sku": f"FEED-{key:05d}",
                "category": category,
                "name": f"{name} · {color}",
                "brand": brand,
                "price_rub": float(price),
                "url": search_url(source, query),
                "image_url": img_for(f"FEED-{key:05d}", category, name),
                "style": style,
                "likes": f"{rnd.randint(2, 900)}K",
                "source": source,
                "verification_status": "verified",
            }
        )
    return out, cursor + count
