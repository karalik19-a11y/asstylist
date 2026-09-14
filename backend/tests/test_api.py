"""HTTP API tests (TestClient, real DB, real engine)."""

from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw

REQUEST = {
    "style": "minimal",
    "mood": "calm",
    "occasion": "everyday",
    "season": "all",
    "presentation": "unisex",
    "height_cm": 176,
    "weight_kg": 72,
    "budget_rub": 50_000,
    "demo_user_id": "api-tester",
}


def photo_bytes() -> bytes:
    image = Image.new("RGB", (120, 160), (210, 212, 220))
    draw = ImageDraw.Draw(image)
    draw.ellipse([45, 20, 80, 60], fill=(224, 176, 146))
    draw.polygon([(40, 65), (85, 65), (95, 140), (30, 140)], fill=(220, 170, 140))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True
    assert body["db"]["products"] >= 100
    assert body["db"]["eligible_products"] >= 100
    assert body["budget_max_rub"] == 100_000


def test_meta_exposes_taxonomy(client):
    body = client.get("/api/meta").json()
    assert len(body["styles"]) >= 10
    assert len(body["moods"]) >= 8
    assert body["budget"]["max_rub"] == 100_000
    assert body["colors"]
    assert abs(sum(body["ranking_weights"].values()) - 1.0) < 1e-6


def test_demo_auth(client):
    response = client.post("/api/telegram/auth", json={"demo_user_id": "auth-tester"})
    assert response.status_code == 200
    body = response.json()
    assert body["demo"] is True
    assert body["user"]["telegram_id"].startswith("demo-")


def test_generate_with_json(client):
    response = client.post("/api/looks/generate", json=REQUEST)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"]
    assert body["total_rub"] <= body["budget_rub"]
    assert len(body["items"]) >= 3
    assert body["body"]["silhouette"]
    assert body["palette"]["recommended"]
    assert body["verdict"]["grade"]
    assert body["diagnostics"]["candidates_total"] > 0


def test_generate_with_photo_multipart(client):
    response = client.post(
        "/api/looks/generate",
        data={**REQUEST, "demo_user_id": "photo-tester"},
        files={"photo": ("look.jpg", photo_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ai_provider"] == "local"
    assert body["photo_digest"]
    assert len(body["photo_digest"]) == 64


def test_generate_rejects_oversized_budget(client):
    response = client.post("/api/looks/generate", json={**REQUEST, "budget_rub": 5_000_000})
    assert response.status_code == 422


def test_generate_rejects_absurd_height(client):
    response = client.post("/api/looks/generate", json={**REQUEST, "height_cm": 40})
    assert response.status_code == 422


def test_generate_rejects_bad_image(client):
    response = client.post(
        "/api/looks/generate",
        data=REQUEST,
        files={"photo": ("bad.jpg", b"definitely not a jpeg", "image/jpeg")},
    )
    assert response.status_code == 422


def test_history_and_detail(client):
    created = client.post("/api/looks/generate", json={**REQUEST, "demo_user_id": "history-tester"}).json()
    history = client.get("/api/looks", params={"demo_user_id": "history-tester"}).json()
    assert any(row["id"] == created["id"] for row in history["items"])

    detail = client.get(f"/api/looks/{created['id']}", params={"demo_user_id": "history-tester"}).json()
    assert detail["id"] == created["id"]
    assert len(detail["items"]) == len(created["items"])


def test_look_is_isolated_between_users(client):
    created = client.post("/api/looks/generate", json={**REQUEST, "demo_user_id": "owner"}).json()
    response = client.get(f"/api/looks/{created['id']}", params={"demo_user_id": "someone-else"})
    assert response.status_code == 404


def test_swap_replaces_the_slot_and_keeps_budget(client):
    created = client.post("/api/looks/generate", json={**REQUEST, "demo_user_id": "swap-tester"}).json()
    target = next(item for item in created["items"] if item["slot"] == "shoes")

    response = client.post(
        f"/api/looks/{created['id']}/swap",
        params={"demo_user_id": "swap-tester"},
        json={"slot": "shoes"},
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    swapped = next(item for item in updated["items"] if item["slot"] == "shoes")
    assert swapped["sku"] != target["sku"]
    assert updated["version"] == created["version"] + 1
    assert updated["total_rub"] <= updated["budget_rub"]
    # other slots untouched
    untouched = {i["slot"]: i["sku"] for i in created["items"] if i["slot"] != "shoes"}
    assert all(i["sku"] == untouched[i["slot"]] for i in updated["items"] if i["slot"] != "shoes")


def test_swap_unknown_slot_returns_422(client):
    created = client.post("/api/looks/generate", json={**REQUEST, "demo_user_id": "swap-bad"}).json()
    response = client.post(
        f"/api/looks/{created['id']}/swap", params={"demo_user_id": "swap-bad"}, json={"slot": "helicopter"}
    )
    assert response.status_code == 422


def test_favorite_toggle(client):
    created = client.post("/api/looks/generate", json={**REQUEST, "demo_user_id": "fav-tester"}).json()
    first = client.post(f"/api/looks/{created['id']}/favorite", params={"demo_user_id": "fav-tester"}).json()
    second = client.post(f"/api/looks/{created['id']}/favorite", params={"demo_user_id": "fav-tester"}).json()
    assert first["is_favorite"] is True
    assert second["is_favorite"] is False


def test_catalog_items_filters(client):
    body = client.get("/api/catalog/items", params={"category": "shoes", "max_price": 10_000}).json()
    assert body["total"] > 0
    assert all(item["category"] == "shoes" for item in body["items"])
    assert all(item["price_rub"] <= 10_000 for item in body["items"])


def test_verification_report_endpoint(client):
    body = client.get("/api/catalog/verification").json()
    assert body["failed"] >= 4
    assert body["verified"] >= 100
    assert any(row["sku"] == "BAD-001" for row in body["items"])


def test_import_accepts_good_and_rejects_bad(client):
    good = {
        "sku": "API-001",
        "category": "top",
        "name": "Импортная футболка",
        "brand": "Test Brand",
        "price_rub": 4990,
        "currency": "RUB",
        "url": "https://www.lamoda.ru/p/api-001",
        "source": "lamoda",
        "sizes": ["S", "M"],
        "colors": ["black"],
        "styles": ["minimal"],
        "moods": ["calm"],
        "seasons": ["all"],
    }
    bad = {**good, "sku": "API-002", "url": "https://evil.example/x"}
    body = client.post("/api/catalog/import", json={"products": [good, bad]}).json()
    assert body["accepted"] == 1
    assert body["rejected"] == 1

    listed = client.get("/api/catalog/items", params={"category": "top"}).json()
    assert any(item["sku"] == "API-001" for item in listed["items"])


def test_reverify_endpoint(client):
    body = client.post("/api/catalog/reverify").json()
    assert body["total"] >= 100
    assert body["failed"] >= 4
    assert body["verified"] >= 100


def test_generated_items_have_real_scores(client):
    """Regression guard for the empty-weights bug (all scores 0.0)."""
    body = client.post(
        "/api/looks/generate",
        json={**REQUEST, "style": "old_money", "mood": "elegant", "budget_rub": 80_000, "demo_user_id": "score-check"},
    ).json()
    assert all(item["score"] > 0 for item in body["items"]), body["items"]
    assert body["budget_utilization"] > 0.5
