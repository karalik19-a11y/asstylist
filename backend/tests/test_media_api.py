"""Фотографии объявлений через наш сервер.

CDN Авито отдаёт картинки браузеру не всегда (hotlink-защита, регион,
Referer) — из-за этого в карточке вещи оставался чёрный прямоугольник.
Эндпоинт ``/api/media/photo`` ходит за фото сам и отдаёт его со своего домена.
Тесты работают без сети: подменяем HTTP-клиент.
"""

from __future__ import annotations

import httpx
import pytest

from app.api import media
from app.config import settings

PHOTO_URL = "https://90.img.avito.st/image/1/1.example.jpg"

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"photo" * 40


class _FakeResponse:
    def __init__(self, payload: bytes, *, status: int = 200, content_type: str = "image/jpeg") -> None:
        self.content = payload
        self.status_code = status
        self.headers = {"content-type": content_type}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", PHOTO_URL)
            raise httpx.HTTPStatusError(
                "error", request=request, response=httpx.Response(self.status_code, request=request)
            )


class _FakeClient:
    """Мини-двойник httpx.AsyncClient: считает запросы, отдаёт заданный ответ."""

    calls: list[str] = []
    response: _FakeResponse = _FakeResponse(JPEG_BYTES)

    def __init__(self, *args, **kwargs) -> None:  # noqa: ARG002 — интерфейс httpx
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def get(self, url: str) -> _FakeResponse:
        type(self).calls.append(url)
        if isinstance(type(self).response, Exception):
            raise type(self).response
        return type(self).response


@pytest.fixture()
def fake_http(monkeypatch, tmp_path):
    """Подменяем httpx и складываем кэш фото в tmp-каталог."""
    _FakeClient.calls = []
    _FakeClient.response = _FakeResponse(JPEG_BYTES)
    monkeypatch.setattr(media.httpx, "AsyncClient", _FakeClient)
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    return _FakeClient


def test_host_allowlist():
    assert media.host_allowed("https://90.img.avito.st/image/1/x.jpg")
    assert media.host_allowed("https://img.avito.st/x.jpg")
    assert media.host_allowed("https://www.avito.ru/photo.jpg")
    # подделка хоста и чужие сайты — мимо
    assert not media.host_allowed("https://img.avito.st.evil.com/x.jpg")
    assert not media.host_allowed("https://evil.com/avito.st/x.jpg")
    assert not media.host_allowed("file:///etc/passwd")
    assert not media.host_allowed("")


def test_photo_proxy_returns_image_and_caches(client, fake_http):
    first = client.get("/api/media/photo", params={"u": PHOTO_URL})
    assert first.status_code == 200
    assert first.headers["content-type"].startswith("image/jpeg")
    assert first.content == JPEG_BYTES
    assert "max-age" in first.headers["cache-control"]

    second = client.get("/api/media/photo", params={"u": PHOTO_URL})
    assert second.status_code == 200
    assert second.content == JPEG_BYTES
    # Второй показ образа не дёргает CDN: файл уже лежит у нас.
    assert fake_http.calls == [PHOTO_URL]


def test_photo_proxy_rejects_foreign_hosts(client, fake_http):
    response = client.get("/api/media/photo", params={"u": "https://evil.com/photo.jpg"})
    assert response.status_code == 400
    assert fake_http.calls == []


def test_photo_proxy_reports_upstream_failure(client, fake_http):
    fake_http.response = _FakeResponse(b"", status=404)
    response = client.get("/api/media/photo", params={"u": PHOTO_URL})
    assert response.status_code == 502
    assert "Авито" in response.json()["detail"]


def test_photo_proxy_refuses_non_images(client, fake_http):
    fake_http.response = _FakeResponse(b"<html>captcha</html>", content_type="text/html")
    response = client.get("/api/media/photo", params={"u": PHOTO_URL})
    assert response.status_code == 502


def test_photo_proxy_survives_network_error(client, fake_http):
    fake_http.response = httpx.ConnectError("нет сети")
    response = client.get("/api/media/photo", params={"u": PHOTO_URL})
    assert response.status_code == 502
    assert "ConnectError" in response.json()["detail"]


def test_photo_proxy_validates_url(client):
    assert client.get("/api/media/photo").status_code == 422
    assert client.get("/api/media/photo", params={"u": "short"}).status_code == 422


def test_photo_served_from_local_snapshot_without_network(client, fake_http, tmp_path, monkeypatch):
    """Фото, скачанное рядом со снимком выдачи, отдаётся без выхода в сеть."""
    import json

    photos = tmp_path / "photos"
    photos.mkdir()
    (photos / "1234567890.jpg").write_bytes(JPEG_BYTES)
    snapshot = tmp_path / "avito_listings.json"
    snapshot.write_text(
        json.dumps(
            {
                "captured_at": "2026-09-16",
                "listings": [
                    {"id": "1234567890", "image": PHOTO_URL, "photo_path": "photos/1234567890.jpg"}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "avito_snapshot_path", str(snapshot))

    response = client.get("/api/media/photo", params={"u": PHOTO_URL})
    assert response.status_code == 200
    assert response.content == JPEG_BYTES
    assert fake_http.calls == [], "локальное фото не должно дёргать сеть"
