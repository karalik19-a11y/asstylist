"""Tests for the product verification layer."""

from __future__ import annotations

from app.catalog.products import seed_products, valid_products
from app.services import catalog_service
from app.verification.verifier import (
    STATUS_FAILED,
    STATUS_VERIFIED,
    compute_checksum,
    is_eligible,
    verify_product,
)


def good_payload() -> dict:
    return valid_products()[0]


def test_valid_product_is_verified():
    outcome = verify_product(good_payload())
    assert outcome.status == STATUS_VERIFIED
    assert outcome.score >= 0.92
    assert outcome.issues == []
    assert outcome.checksum


def test_all_seed_products_pass_verification():
    outcomes = [verify_product(payload) for payload in valid_products()]
    assert outcomes
    assert all(o.status == STATUS_VERIFIED for o in outcomes), [o.issues for o in outcomes if o.status != STATUS_VERIFIED][:3]


def test_all_broken_products_are_rejected():
    broken = [p for p in seed_products() if p["sku"].startswith("BAD")]
    assert len(broken) == 4
    for payload in broken:
        outcome = verify_product(payload)
        assert outcome.status == STATUS_FAILED, payload["sku"]
        assert not is_eligible(outcome.status, outcome.score)


def test_host_allowlist_blocks_unknown_hosts():
    payload = good_payload()
    payload["url"] = "https://totally-not-a-shop.ru/item"
    outcome = verify_product(payload)
    assert outcome.status == STATUS_FAILED
    assert any(issue.startswith("url:") for issue in outcome.issues)


def test_non_http_scheme_is_blocked():
    payload = good_payload()
    payload["url"] = "file:///etc/passwd"
    assert verify_product(payload).status == STATUS_FAILED


def test_bad_price_is_a_critical_failure():
    payload = good_payload()
    payload["price_rub"] = -5
    outcome = verify_product(payload)
    assert outcome.status == STATUS_FAILED


def test_price_above_ceiling_is_rejected():
    payload = good_payload()
    payload["price_rub"] = 500_000
    assert verify_product(payload).status == STATUS_FAILED


def test_checksum_detects_tampering():
    payload = good_payload()
    outcome = verify_product(payload)
    tampered = dict(payload)
    tampered["price_rub"] = payload["price_rub"] + 1000
    rechecked = verify_product(tampered, expected_checksum=outcome.checksum)
    assert rechecked.status != STATUS_VERIFIED
    assert any(issue.startswith("checksum:") for issue in rechecked.issues)


def test_checksum_is_stable():
    assert compute_checksum(good_payload()) == compute_checksum(good_payload())


def test_missing_attributes_only_downgrade_to_warning():
    payload = good_payload()
    payload["styles"] = []
    outcome = verify_product(payload)
    assert outcome.status == STATUS_VERIFIED or outcome.status == "warning"
    assert any(issue.startswith("attributes:") for issue in outcome.issues)


def test_unknown_source_is_critical():
    payload = good_payload()
    payload["source"] = "unknown"
    assert verify_product(payload).status == STATUS_FAILED


def test_network_check_refuses_non_allowlisted_hosts():
    from app.verification.verifier import check_reachability

    ok, detail = check_reachability("https://evil.example/x")
    assert ok is False
    assert "белом списке" in detail


def test_catalog_rows_are_persisted_with_status(session):
    from app.models import Product

    rows = session.query(Product).all()
    assert rows
    by_sku = {p.sku: p for p in rows}
    for sku in ("BAD-001", "BAD-002", "BAD-003", "BAD-004"):
        assert by_sku[sku].verification_status == STATUS_FAILED
        assert by_sku[sku].active is False
    verified = [p for p in rows if p.verification_status == STATUS_VERIFIED]
    assert len(verified) >= 100
    assert all(p.active for p in verified)
    assert not any(p.active for p in rows if p.verification_status == STATUS_FAILED)


def test_verification_report_shape(session):
    report = catalog_service.verification_report(session)
    assert report["total"] == report["verified"] + report["warning"] + report["failed"]
    assert report["failed"] >= 4
    assert report["eligible"] == report["verified"] + report["warning"]
    assert report["network_enabled"] is False
    assert len(report["items"]) == report["total"]


def test_reverify_is_idempotent(session):
    first = catalog_service.reverify_catalog(session)
    second = catalog_service.reverify_catalog(session)
    assert first == second


def test_import_rejects_bad_rows(session):
    payload = good_payload()
    payload["sku"] = "IMP-001"
    bad = dict(payload)
    bad["sku"] = "IMP-002"
    bad["url"] = "https://nope.example/x"

    accepted = catalog_service.verify_and_persist(session, payload)
    rejected = catalog_service.verify_and_persist(session, bad)
    assert accepted.verification_status == STATUS_VERIFIED
    assert accepted.active is True
    assert rejected.verification_status == STATUS_FAILED
    assert rejected.active is False
