"""Трендовые стили, фото каталога и персональное объяснение образа."""

from __future__ import annotations

from app.catalog.products import seed_products, valid_products

TREND_STYLES = {"office_siren", "gorpcore", "y2k", "indie_sleaze", "dark_academia", "balletcore"}


def test_local_catalog_has_no_static_photos():
    """Локальный каталог — «пустышка» без файлов фото: живые изображения
    подтягивает только движок в реальном времени (web-search)."""
    for row in valid_products():
        assert row["image_url"] == "", row["sku"]


def test_mock_archetypes_have_no_broken_hotlinks():
    """Mock-архетипы либо имеют прямую ссылку на фото вещи, либо плейсхолдер —
    никакого мусора вместо изображения."""
    from app.fashion_engine.search.providers.mock_real_product_provider import MOCK_IMAGES

    for name, url in MOCK_IMAGES.items():
        assert url.startswith("https://"), name


def test_engine_search_items_carry_live_image_field():
    """У позиций выдачи движка есть поле image_url (заполняется в реальном
    времени от web-search / mock-архетипов)."""
    from app.fashion_engine.search.providers.mock_real_product_provider import MockRealProductProvider
    from app.fashion_engine.search.provider import SearchContext

    provider = MockRealProductProvider()
    items = provider.search("leather black boots", SearchContext(limit=5))
    assert items
    for item in items:
        data = item.to_dict() if hasattr(item, "to_dict") else {"image": item.image}
        assert "image" in data
        # релевантность провайдера нужна смешанной сортировке в общей выдаче
        assert float((item.meta or {}).get("query_match") or 0) > 0


def test_engine_search_mixes_external_archetypes(client):
    """Выдача движка смешивает каталог приложения и внешних находок/архетипов."""
    response = client.post("/api/engine/search", json={"query": "black leather boots", "limit": 12})
    assert response.status_code == 200, response.text
    body = response.json()
    assert "mock-real-catalog" in body["engine"]["providers"]
    sources = {item["source"] for item in body["items"]}
    assert "mock-real-catalog" in sources
    for item in body["items"]:
        assert "image_url" in item


def test_trend_styles_present_in_options():
    from app.engine.options import STYLE_OPTIONS, style_by_id

    ids = {option["id"] for option in STYLE_OPTIONS}
    assert TREND_STYLES <= ids
    assert style_by_id("office_siren")["label"] == "Офис-сирена"
    # старые стили никуда не делись
    assert {"minimal", "old_money", "streetwear"} <= ids


def test_trend_styles_ranking_links():
    from app.engine.ranking import STYLE_AFFINITY

    for style in TREND_STYLES:
        assert style in STYLE_AFFINITY
        assert STYLE_AFFINITY[style], f"у стиля {style} нет соседей"


def test_catalog_carries_trend_styles():
    by_sku = {row["sku"]: row for row in valid_products()}
    assert "office_siren" in by_sku["BT-016"]["styles"]
    assert "gorpcore" in by_sku["OW-014"]["styles"]
    assert "y2k" in by_sku["BT-018"]["styles"]
    # ретеггинг базовых позиций
    assert "office_siren" in by_sku["BT-001"]["styles"]
    assert "indie_sleaze" in by_sku["OW-004"]["styles"]
    assert "balletcore" in by_sku["SH-006"]["styles"]


def test_seed_rows_verifiable():
    from app.services import catalog_service
    from app.db import SessionLocal

    session = SessionLocal()
    try:
        stats = catalog_service.seed_catalog(session, force=True)
        assert stats["total"] == len(seed_products())
        second = catalog_service.seed_catalog(session)
        assert second["seeded"] == 0  # синхронизация идемпотентна
        for row in valid_products():
            for style in TREND_STYLES:
                if style in row["styles"]:
                    break
            else:
                continue
            break
        # и каждый стиль имеет хотя бы несколько вещей в каталоге
        from collections import Counter

        counts: Counter[str] = Counter()
        for row in valid_products():
            for style in TREND_STYLES & set(row["styles"]):
                counts[style] += 1
        assert all(counts.get(style, 0) >= 3 for style in TREND_STYLES)
    finally:
        session.close()


def test_personal_note_in_look(client):
    response = client.post(
        "/api/looks/generate",
        json={
            "style": "office_siren",
            "mood": "confident",
            "occasion": "work",
            "season": "all",
            "presentation": "unisex",
            "height_cm": 170,
            "weight_kg": 62,
            "budget_rub": 60_000,
            "demo_user_id": "trend-user",
            "save": False,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["personal_note"]
    assert "Офис-сирена" in body["personal_note"] or "офис-сирена" in body["personal_note"].lower()
    assert "фото" in body["personal_note"].lower()  # без снимка честно предлагаем добавить
    assert body["items"]


def test_personal_note_mentions_color_type_with_photo(client):
    import io

    from PIL import Image, ImageDraw

    img = Image.new("RGB", (200, 260), (90, 110, 140))
    d = ImageDraw.Draw(img)
    d.ellipse((70, 30, 130, 100), fill=(224, 186, 158))
    d.rectangle((60, 100, 140, 170), fill=(222, 182, 155))
    d.ellipse((64, 18, 136, 60), fill=(60, 45, 35))
    d.rectangle((60, 170, 140, 260), fill=(30, 30, 32))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/looks/generate",
        data={
            "style": "minimal",
            "mood": "calm",
            "occasion": "everyday",
            "season": "all",
            "presentation": "unisex",
            "height_cm": 172,
            "weight_kg": 68,
            "budget_rub": 50000,
            "demo_user_id": "photo-note-user",
            "save": "false",
        },
        files={"photo": ("me.png", buf, "image/png")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["personal_note"]
    assert "цветотип" in body["personal_note"].lower()
    assert body["palette"]["color_type_ru"]
    assert body["palette"]["source"] != "defaults"
