"""Память о пользователе: рост и вес вводятся один раз.

Проверяем, что сервис хранит ровно то, о чём просили (рост и вес), не пускает
мусор, умеет «забыть» данные и запоминает рост/вес после удачной сборки образа —
именно из этого вырастает выбор «сохранённые данные или новые» при следующем входе.
"""

from __future__ import annotations

LOOK_REQUEST = {
    "style": "minimal",
    "mood": "calm",
    "occasion": "everyday",
    "season": "all",
    "presentation": "unisex",
    "height_cm": 181,
    "weight_kg": 77,
    "budget_rub": 50_000,
    "demo_user_id": "memory-tester",
}


def test_profile_empty_at_first_visit(client):
    body = client.get("/api/profile?demo_user_id=memory-newcomer").json()
    assert body["saved"] is False
    assert body["profile"] == {}
    assert body["used_count"] == 0


def test_profile_keeps_only_height_and_weight(client):
    response = client.put(
        "/api/profile?demo_user_id=memory-keeper",
        json={"height_cm": 174, "weight_kg": 64, "style": "grunge", "budget_rub": 90_000},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["saved"] is True
    assert body["profile"] == {"height_cm": 174.0, "weight_kg": 64.0}
    assert body["problems"] == []

    again = client.get("/api/profile?demo_user_id=memory-keeper").json()
    assert again["profile"] == {"height_cm": 174.0, "weight_kg": 64.0}
    assert again["updated_at"]


def test_profile_rejects_impossible_values_without_losing_previous(client):
    client.put("/api/profile?demo_user_id=memory-strict", json={"height_cm": 168, "weight_kg": 58})
    body = client.put("/api/profile?demo_user_id=memory-strict", json={"height_cm": 999}).json()
    assert body["problems"], "некорректный рост должен вернуть пояснение"
    assert "999" not in str(body["profile"].get("height_cm"))
    assert body["profile"]["height_cm"] == 168.0
    assert body["profile"]["weight_kg"] == 58.0


def test_profile_partial_update_keeps_other_field(client):
    client.put("/api/profile?demo_user_id=memory-partial", json={"height_cm": 170, "weight_kg": 60})
    body = client.put("/api/profile?demo_user_id=memory-partial", json={"weight_kg": 63}).json()
    assert body["profile"] == {"height_cm": 170.0, "weight_kg": 63.0}


def test_profile_used_and_forgotten(client):
    client.put("/api/profile?demo_user_id=memory-cycle", json={"height_cm": 176, "weight_kg": 70})

    assert client.post("/api/profile/used?demo_user_id=memory-cycle").json()["used_count"] == 1
    assert client.post("/api/profile/used?demo_user_id=memory-cycle").json()["used_count"] == 2

    cleared = client.post("/api/profile/reset?demo_user_id=memory-cycle").json()
    assert cleared["saved"] is False
    assert cleared["profile"] == {}
    assert client.get("/api/profile?demo_user_id=memory-cycle").json()["saved"] is False


def test_generate_look_remembers_body(client):
    """Рост и вес уходят в память сразу после сборки образа — их не спросят заново."""
    response = client.post("/api/looks/generate", json=LOOK_REQUEST)
    assert response.status_code == 200
    assert response.json()["profile"]["profile"] == {"height_cm": 181.0, "weight_kg": 77.0}

    saved = client.get("/api/profile?demo_user_id=memory-tester").json()
    assert saved["saved"] is True
    assert saved["profile"] == {"height_cm": 181.0, "weight_kg": 77.0}
