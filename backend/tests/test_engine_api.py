"""HTTP-контракт движка ASSTYLIST: /api/engine/* и генерация образа через него."""

from __future__ import annotations

from app.services.fashion_engine_service import PIPELINE

GENERATE = {
    "style": "grunge",
    "mood": "bold",
    "occasion": "everyday",
    "season": "autumn",
    "presentation": "feminine",
    "height_cm": 172,
    "weight_kg": 62,
    "budget_rub": 55_000,
    "query": "грязный индустриальный образ с прозрачным верхом",
    "niche_level": 78,
    "demo_user_id": "engine-api-tester",
}


def test_engine_health(client):
    body = client.get("/api/engine/health").json()
    assert body["status"] == "ok"
    assert body["engine_version"]
    assert body["pipeline"] == PIPELINE
    assert body["enabled"] is True
    assert body["catalog"]["eligible_items"] >= 100
    assert body["catalog"]["currency"] == "RUB"
    assert "karalik19-a11y/-" in body["source"]


def test_engine_schema_and_taxonomy(client):
    schema = client.get("/api/engine/schema").json()
    assert schema["name"] == "asystylist_create_outfit"
    assert schema["parameters"]["required"] == ["query"]

    taxonomy = client.get("/api/engine/taxonomy").json()
    assert len(taxonomy["style_profiles"]) >= 10
    assert set(taxonomy["style_profiles"]) >= {"minimal", "grunge", "old_money"}
    taste_ids = {entry["id"] for entry in taxonomy["taste_categories"]}
    assert taste_ids
    role_ids = {entry["id"] for entry in taxonomy["roles"]}
    assert {"hero", "base", "footwear"} <= role_ids
    assert all(entry["label"] for entry in taxonomy["taste_categories"])


def test_engine_search_endpoint(client):
    response = client.post(
        "/api/engine/search",
        json={
            "query": "индустриальный образ с прозрачным верхом",
            "style": "grunge",
            "budget_rub": 60_000,
            "presentation": "feminine",
            "season": "autumn",
            "limit": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    engine = body["engine"]
    assert engine["pipeline"] == PIPELINE
    assert engine["styling_thesis"] and engine["styling_thesis_ru"]
    assert engine["outfit_score"] > 0
    assert engine["queries_used"]
    assert body["thesis_options"]

    assert 0 < len(body["items"]) <= 5
    first = body["items"][0]
    assert first["engine"]["taste_category"]
    assert first["engine"]["role"]
    assert first["reasons"]
    assert first["sku"]
    assert body["budget_rub"] == 60_000
    assert body["suggested_request"]["query"] == "индустриальный образ с прозрачным верхом"


def test_engine_search_validates_query(client):
    short = client.post("/api/engine/search", json={"query": "я"})
    assert short.status_code == 422
    empty = client.post("/api/engine/search", json={})
    assert empty.status_code == 422


def test_engine_outfit_endpoint_returns_the_original_contract(client):
    response = client.post(
        "/api/engine/outfit",
        json={
            "query": "industrial romantic look with sheer top and leather jacket",
            "nicheLevel": 80,
            "aesthetics": ["industrial", "romantic"],
            "budgetMax": 90_000,
            "currency": "RUB",
            "occasion": "editorial",
            "fitPreference": "oversized",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {
        "aesthetic",
        "stylingThesis",
        "outfitScore",
        "items",
        "stylingLogic",
        "criticFeedback",
        "criticDecision",
        "meta",
    }
    assert body["outfitScore"] > 0
    assert len(body["items"]) >= 3
    first = body["items"][0]
    assert first["currency"] == "RUB"
    assert first["price"] > 0
    assert first["role"] in {"hero", "base", "layer", "footwear", "accessory"}
    assert first["fashionScore"] >= 0
    assert first["sourceUrl"].startswith("http")
    assert body["meta"]["catalog"]["provider"] == "app-catalog"
    assert body["meta"]["catalog"]["currency"] == "RUB"


def test_generated_look_is_driven_by_the_engine_and_persisted(client):
    response = client.post("/api/looks/generate", json=GENERATE)
    assert response.status_code == 200
    look = response.json()

    engine = look["engine"]
    assert engine["pipeline"] == PIPELINE
    assert engine["styling_thesis"] == look["diagnostics"]["engine"]["styling_thesis"]
    assert engine["niche_level"] == 78
    assert look["summary"].startswith("Тезис движка")
    assert look["score"] == engine["final_score"]
    assert look["total_rub"] <= look["budget_rub"]

    assert len(look["items"]) >= 3
    assert all(item["engine"]["role"] for item in look["items"])
    assert any(item["engine"]["in_engine_outfit"] for item in look["items"])
    assert all(item["reasons"][0].startswith("Движок:") for item in look["items"])
    assert look["diagnostics"]["engine"]["candidates"]["validated"] > 0

    # Образ читается из истории вместе с блоком движка (он лежит в ranking_json).
    stored = client.get(f"/api/looks/{look['id']}?demo_user_id=engine-api-tester").json()
    assert stored["engine"]["pipeline"] == PIPELINE
    assert stored["engine"]["styling_thesis"] == engine["styling_thesis"]
    assert stored["items"][0]["engine"]["fashion_score"] == look["items"][0]["engine"]["fashion_score"]


def test_swap_keeps_engine_metadata(client):
    look = client.post("/api/looks/generate", json={**GENERATE, "demo_user_id": "engine-swap-tester"}).json()
    slot = look["items"][0]["slot"]
    response = client.post(
        f"/api/looks/{look['id']}/swap?demo_user_id=engine-swap-tester",
        json={"slot": slot, "exclude_skus": []},
    )
    assert response.status_code == 200
    swapped = response.json()
    assert swapped["engine"]["pipeline"] == PIPELINE
    assert len(swapped["items"]) == len(look["items"])
    replaced = next(item for item in swapped["items"] if item["slot"] == slot)
    assert replaced["sku"] != look["items"][0]["sku"]
    assert replaced["engine"]["role"]
    assert replaced["reasons"][0].startswith("Движок:")
    assert swapped["total_rub"] <= swapped["budget_rub"]


def test_engine_metadata_reaches_meta_endpoint(client):
    meta = client.get("/api/meta").json()
    assert meta["version"]
    assert meta["colors"] and meta["styles"]
