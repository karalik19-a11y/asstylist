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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
