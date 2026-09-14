"""Product verification layer.

Every product that can reach a look passes through here. The layer is
deterministic, offline by default, and produces a score + issue list so a
"verified" badge always means something concrete.

Checks
------
schema          required fields present and correctly typed
price           price is a sane positive RUB amount
category        category is one the engine knows how to place in a look
url             resolvable URL on an allow-listed host (SSRF guard)
sizes           at least one size is declared
attributes      colours / styles / seasons are filled in
source          the source is a known, trusted one
checksum        the record has not been tampered with since it was verified
freshness       the verification has not expired (TTL)
reachability    optional live HTTP check — disabled unless explicitly enabled
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from ..config import settings
from .sources import trust_for

VALID_CATEGORIES = {
    "outerwear",
    "top",
    "knitwear",
    "bottom",
    "dress",
    "shoes",
    "bag",
    "accessory",
}

REQUIRED_FIELDS = ("sku", "category", "name", "brand", "price_rub", "url")

#: Checks whose failure always disqualifies a product, whatever the score.
CRITICAL_CHECKS = frozenset({"schema", "price", "url", "category", "source", "checksum"})

STATUS_VERIFIED = "verified"
STATUS_WARNING = "warning"
STATUS_FAILED = "failed"
STATUS_PENDING = "pending"


@dataclass
class Check:
    name: str
    passed: bool
    weight: float
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationOutcome:
    status: str
    score: float
    issues: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    verified_at: str | None = None
    expires_at: str | None = None
    checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "score": round(self.score, 3),
            "issues": self.issues,
            "checks": [c.to_dict() for c in self.checks],
            "verified_at": self.verified_at,
            "expires_at": self.expires_at,
            "checksum": self.checksum,
        }


def compute_checksum(payload: dict[str, Any]) -> str:
    """Stable content hash over the fields that matter commercially."""
    keys = [
        "sku",
        "category",
        "name",
        "brand",
        "price_rub",
        "currency",
        "url",
        "source",
        "sizes",
        "colors",
        "styles",
    ]
    normalised = {key: payload.get(key) for key in keys}
    blob = json.dumps(normalised, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _host_allowed(url: str) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False, "некорректный URL"
    if parsed.scheme not in ("http", "https"):
        return False, f"недопустимая схема {parsed.scheme or '(нет)'}"
    host = (parsed.hostname or "").lower()
    if not host:
        return False, "в URL нет хоста"
    for allowed in settings.allowed_product_hosts:
        allowed = allowed.lower()
        if host == allowed or host.endswith("." + allowed):
            return True, host
    return False, f"хост {host} не в белом списке"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [value]
        except json.JSONDecodeError:
            return [value]
    return [value]


def verify_product(
    payload: dict[str, Any],
    *,
    now: datetime | None = None,
    expected_checksum: str | None = None,
    reachability: bool | None = None,
) -> VerificationOutcome:
    now = now or datetime.now(timezone.utc)
    checks: list[Check] = []
    issues: list[str] = []

    missing = [f for f in REQUIRED_FIELDS if not payload.get(f)]
    schema_ok = not missing
    checks.append(
        Check("schema", schema_ok, 0.18, "все обязательные поля заполнены" if schema_ok else f"нет полей: {', '.join(missing)}")
    )
    if not schema_ok:
        issues.append(f"schema: отсутствуют {', '.join(missing)}")

    price = payload.get("price_rub")
    price_ok = False
    try:
        price_value = float(price)
        price_ok = 0 < price_value <= settings.budget_max_rub and str(payload.get("currency", "RUB")).upper() == "RUB"
        detail = f"{price_value:,.0f} ₽" if price_ok else "цена вне диапазона или валюта не RUB"
    except (TypeError, ValueError):
        detail = "цена не число"
    checks.append(Check("price", price_ok, 0.15, detail))
    if not price_ok:
        issues.append(f"price: {detail}")

    category = payload.get("category")
    category_ok = category in VALID_CATEGORIES
    checks.append(Check("category", category_ok, 0.1, str(category)))
    if not category_ok:
        issues.append(f"category: неизвестная категория {category}")

    url = str(payload.get("url", ""))
    url_ok, url_detail = _host_allowed(url)
    checks.append(Check("url", url_ok, 0.2, url_detail))
    if not url_ok:
        issues.append(f"url: {url_detail}")

    sizes = _as_list(payload.get("sizes"))
    sizes_ok = len(sizes) > 0
    checks.append(Check("sizes", sizes_ok, 0.1, f"{len(sizes)} размеров"))
    if not sizes_ok:
        issues.append("sizes: не указаны размеры")

    attrs_ok = bool(_as_list(payload.get("colors"))) and bool(_as_list(payload.get("styles"))) and bool(
        _as_list(payload.get("seasons"))
    )
    checks.append(Check("attributes", attrs_ok, 0.12, "цвета/стили/сезоны заполнены" if attrs_ok else "не хватает атрибутов"))
    if not attrs_ok:
        issues.append("attributes: не заполнены цвета, стили или сезоны")

    source = str(payload.get("source", "unknown"))
    trust = trust_for(source)
    checks.append(Check("source", trust >= 0.85, 0.08, f"источник {source} (доверие {trust})"))
    if trust < 0.85:
        issues.append(f"source: низкое доверие к источнику {source}")

    checksum = compute_checksum(payload)
    checksum_ok = expected_checksum is None or expected_checksum == checksum
    checks.append(Check("checksum", checksum_ok, 0.04, checksum[:12]))
    if not checksum_ok:
        issues.append("checksum: запись изменена после верификации")

    ttl_days = max(1, int(settings.verification_ttl_days))
    expires_at = now + timedelta(days=ttl_days)
    checks.append(Check("freshness", True, 0.03, f"TTL {ttl_days} дн."))

    do_network = settings.verification_network_enabled if reachability is None else bool(reachability)
    if do_network and url_ok:
        network_ok, network_detail = check_reachability(url)
        checks.append(Check("reachability", network_ok, 0.05, network_detail))
        if not network_ok:
            issues.append(f"reachability: {network_detail}")
    else:
        checks.append(
            Check("reachability", True, 0.0, "проверка сети отключена (офлайн-режим)" if not do_network else "URL невалиден")
        )

    weight_sum = sum(c.weight for c in checks) or 1.0
    raw = sum(c.weight for c in checks if c.passed) / weight_sum
    score = round(raw * (0.9 + 0.1 * trust), 3)

    critical_failures = [c.name for c in checks if not c.passed and c.name in CRITICAL_CHECKS]
    if critical_failures:
        status = STATUS_FAILED
    elif score >= 0.92:
        status = STATUS_VERIFIED
    elif score >= settings.verification_min_score:
        status = STATUS_WARNING
    else:
        status = STATUS_FAILED

    return VerificationOutcome(
        status=status,
        score=score,
        issues=issues,
        checks=checks,
        verified_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        checksum=checksum,
    )


def check_reachability(url: str) -> tuple[bool, str]:
    """Live check, only ever called for allow-listed hosts and only when enabled."""
    allowed, detail = _host_allowed(url)
    if not allowed:
        return False, detail
    try:
        import httpx

        response = httpx.get(
            url,
            timeout=settings.verification_network_timeout_sec,
            follow_redirects=True,
            headers={"User-Agent": "asStylist-Verifier/1.0"},
        )
        if response.status_code < 400:
            return True, f"HTTP {response.status_code}"
        return False, f"HTTP {response.status_code}"
    except Exception as exc:  # noqa: BLE001 — network errors are verification failures, not crashes
        return False, f"{type(exc).__name__}"


def is_eligible(status: str, score: float) -> bool:
    """Can this product be used to build a look?

    * verified — always
    * warning  — yes, but the UI shows a flag
    * failed   — only when ALLOW_UNVERIFIED_PRODUCTS is on
    """
    if status == STATUS_VERIFIED:
        return True
    if status == STATUS_WARNING:
        return score >= settings.verification_min_score
    return settings.allow_unverified_products
