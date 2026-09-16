"""Application configuration.

Everything is driven by environment variables so the service can run in
"demo/local mode" with zero secrets, or in production with a real Telegram bot
token and (optionally) a remote vision model.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"

#: Hard product ceiling defined in the spec: 100 000 RUB.
BUDGET_CEILING_RUB = 100_000

DEFAULT_RANKING_WEIGHTS: dict[str, float] = {
    "style": 0.28,
    "mood": 0.15,
    "silhouette": 0.16,
    "color": 0.15,
    "formality": 0.08,
    "season": 0.05,
    "value": 0.08,
    "verification": 0.05,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- runtime -------------------------------------------------------
    app_name: str = "asStylist"
    app_env: str = "development"
    debug: bool = True
    version: str = APP_VERSION

    #: Demo mode requires no Telegram token and no network at all.
    demo_mode: bool = True

    # --- storage -------------------------------------------------------
    database_url: str = "sqlite:///./data/asstylist.db"
    data_dir: str = "./data"
    static_dir: str = "./frontend/dist"
    store_photos: bool = False
    upload_max_bytes: int = 10 * 1024 * 1024
    allowed_upload_types: tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")

    # --- telegram ------------------------------------------------------
    telegram_bot_token: str | None = None
    telegram_web_app_url: str | None = None
    telegram_auth_max_age_sec: int = 86_400
    #: On boot, when a bot token is configured, attach the Mini App to the bot
    #: automatically (menu button + commands + webhook) in a background thread.
    #: Lets a Render deploy "just work" after setting TELEGRAM_BOT_TOKEN.
    telegram_autoconfigure: bool = True

    # --- security ------------------------------------------------------
    cors_origins: tuple[str, ...] = ("*",)
    admin_token: str = "asstylist-local-admin"

    # --- budget --------------------------------------------------------
    budget_max_rub: int = BUDGET_CEILING_RUB
    budget_min_rub: int = 10_000

    # --- vision / AI ---------------------------------------------------
    #: "local" = offline Pillow heuristics (default, free).
    #: "openai" / "gemini" = remote multimodal model, requires API key.
    ai_provider: str = "local"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    # --- verification layer -------------------------------------------
    verification_min_score: float = 0.6
    verification_ttl_days: int = 30
    #: Network reachability checks are disabled by default: the demo must work
    #: offline and must never be tricked into calling arbitrary hosts.
    verification_network_enabled: bool = False
    verification_network_timeout_sec: float = 3.0
    allowed_product_hosts: tuple[str, ...] = (
        "asstylist.local",
        "avito.ru",
        "ozon.ru",
        "wildberries.ru",
        "lamoda.ru",
        "yandex-market.ru",
        "sokolov.ru",
        "12storeez.com",
        "uniqlo.com",
    )
    #: When false, products that failed verification never reach a look.
    allow_unverified_products: bool = False

    # --- ASSTYLIST Fashion Engine (поиск и подбор вещей) ---------------
    #: Движок из github.com/karalik19-a11y/- управляет поиском и подбором:
    #: расширение запроса → Fashion Intelligence → Taste/anti-generic →
    #: архитектура образа → оценка → критик.
    fashion_engine_enabled: bool = True
    #: ``hybrid`` — движок собирает образ, приложение страхует бюджет/слоты;
    #: ``engine`` — только движок (без отката на прежний ранжировщик);
    #: ``legacy`` — прежний ранжировщик приложения.
    fashion_engine_mode: str = "hybrid"
    #: Разрешить откат на прежний ранжировщик, если движок не собрал образ.
    fashion_engine_allow_fallback: bool = True
    #: Потолки пайплайна движка. Для каталога asStylist (~100 позиций) они не
    #: срабатывают — как и в оригинале, где mock-каталог был меньше лимитов.
    fashion_engine_max_products: int = 120
    #: Сколько позиций локального каталога забирать на один расширенный
    #: запрос. Каталог asStylist небольшой, поэтому провайдер отдаёт весь
    #: ассортимент (сначала совпадения, затем остальное) — отбор делает
    #: интеллектуальный слой движка, как в оригинале с mock-каталогом.
    fashion_engine_limit_per_query: int = 130
    #: Предохранитель по размеру пула, который уходит в движок.
    fashion_engine_max_cards: int = 160
    fashion_engine_min_confidence: float = 0.6
    #: Подключать справочный каталог дизайнерских архетипов (Rick Owens,
    #: Margiela, Yohji…): ссылки ведут на поиск по ритейлеру, позиции помечены
    #: как «архетип движка» и проходят тот же интеллектуальный отбор.
    fashion_engine_enable_mock: bool = True
    #: Вес оценки образа движка в итоговом индексе (0…1).
    fashion_engine_score_weight: float = 0.3

    # --- Авито: единственный источник товаров ---------------------------
    #: Поиск и подбор вещей идут только по объявлениям Авито: каждая позиция
    #: выдачи — живое объявление со ссылкой, фото и ценой в рублях. Если Авито
    #: временно недоступен, движок всё равно подбирает вещи, а ссылки ведут на
    #: соответствующие подборки Авито (резервный режим, без пустых выдач).
    avito_enabled: bool = True
    #: Город/регион поиска (слаг Авито): rossiya — вся страна, moskva,
    #: sankt-peterburg и т.д.
    avito_city: str = "rossiya"
    avito_timeout_sec: float = 6.0
    #: Сколько объявлений забирать на один запрос.
    avito_max_results: int = 10
    #: Сколько расширенных запросов движка уходят в живой поиск (каждый —
    #: HTTP-запрос; остальные расширения обслуживаются из кэша/пула).
    avito_max_queries: int = 5
    #: TTL кэша выдачи Авито (секунды) и негативных ответов.
    avito_cache_ttl_sec: int = 900
    avito_negative_ttl_sec: int = 180

    # --- живой поиск вещей (WebSearchProvider) ------------------------
    #: Мастер-переключатель: без ключей провайдер тихо отдаёт пустой список,
    #: пайплайн при этом работает по каталогу приложения.
    web_search_enabled: bool = True
    web_search_timeout_sec: float = 6.0
    web_search_max_results: int = 8
    #: SerpAPI (engine=google_shopping) — основной живой источник.
    serpapi_api_key: str | None = None
    #: Google Custom Search — запасной живой источник (нужны key + cx).
    google_cse_api_key: str | None = None
    google_cse_cx: str | None = None
    #: Партнёрский фид магазина: URL JSON-массива товаров
    #: [{name, brand, price, currency, category, image, url, tags?}, …].
    product_feed_url: str | None = None
    #: Курсы для пересчёта цен источников в рубли (отображение и бюджет).
    fx_rates: dict[str, float] = Field(
        default_factory=lambda: {"RUB": 1.0, "EUR": 100.0, "USD": 90.0, "GBP": 115.0, "CNY": 12.5}
    )

    # --- ranking -------------------------------------------------------
    ranking_weights: dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_RANKING_WEIGHTS))
    ranking_weights_json: str | None = None

    @field_validator("ranking_weights_json")
    @classmethod
    def _parse_weights(cls, value: str | None) -> str | None:  # pragma: no cover - trivial
        if value:
            parsed = json.loads(value)
            if not isinstance(parsed, dict):
                raise ValueError("RANKING_WEIGHTS_JSON must be a JSON object")
        return value

    def resolved_ranking_weights(self) -> dict[str, float]:
        """Ranking weights, normalised so they sum to 1.0."""
        raw: dict[str, Any] = dict(DEFAULT_RANKING_WEIGHTS)
        if self.ranking_weights:
            raw.update({k: float(v) for k, v in self.ranking_weights.items()})
        if self.ranking_weights_json:
            raw.update({k: float(v) for k, v in json.loads(self.ranking_weights_json).items()})
        total = sum(max(0.0, float(v)) for v in raw.values()) or 1.0
        return {k: max(0.0, float(v)) / total for k, v in raw.items()}

    @property
    def effective_ai_provider(self) -> str:
        provider = (self.ai_provider or "local").lower()
        if provider == "openai" and not self.openai_api_key:
            return "local"
        if provider == "gemini" and not self.gemini_api_key:
            return "local"
        return provider

    @property
    def web_search_available(self) -> bool:
        """Есть ли хотя бы один сконфигурированный живой источник."""
        if not self.web_search_enabled:
            return False
        return bool(self.serpapi_api_key or self.product_feed_url or (self.google_cse_api_key and self.google_cse_cx))

    def to_rub(self, amount: float, currency: str) -> float | None:
        """Пересчитать цену источника в рубли; None, если валюта неизвестна."""
        rate = (self.fx_rates or {}).get((currency or "RUB").upper())
        if rate is None:
            return None
        return round(float(amount) * float(rate), 2)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def persist_env(updates: dict[str, str | bool | None], env_file: str = ".env") -> list[str]:
    """Write the given keys into `.env`, preserving every other line.

    Used by the in-app "connect my bot" flow so the token survives a restart.
    `.env` is git-ignored; values are never logged.
    """
    from pathlib import Path

    normalised = {key.upper(): ("" if value is None else str(value)) for key, value in updates.items()}
    path = Path(env_file)
    lines: list[str] = []
    written: set[str] = set()

    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip().upper()
                if key in normalised:
                    lines.append(f"{key}={normalised[key]}")
                    written.add(key)
                    continue
            lines.append(raw)

    for key, value in normalised.items():
        if key not in written:
            lines.append(f"{key}={value}")

    if lines and lines[-1] != "":
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return sorted(normalised)
