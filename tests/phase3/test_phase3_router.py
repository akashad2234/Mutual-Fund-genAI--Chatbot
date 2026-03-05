from __future__ import annotations

import json
from pathlib import Path

from src.phase3 import config as phase3_config
from src.phase3.router import route_query, load_known_funds
from src.phase3.schemas import ParsedQuery


def test_route_query_identifies_3y_return_and_fund_slug(tmp_path, monkeypatch):
    """
    Integration-style test for Phase 3 routing without calling Groq.

    It simulates a minimal Phase 1 output containing the
    ICICI Prudential Large & Mid Cap Fund Direct Plan Growth fund, and
    verifies that:
    - The query is classified as an attribute_query.
    - The correct fund slug is detected from the URL in the query.
    - The 'returns_3y' attribute is detected.
    """
    # Minimal Phase 1-style JSON with just the ICICI Prudential fund.
    phase1_data = [
        {
            "name": "ICICI Prudential Large & Mid Cap Fund Direct Plan Growth",
            "url": "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth",
            "slug": "icici-prudential-top-100-fund-direct-growth",
            "attributes": {},
            "sections": {},
        }
    ]

    temp_phase1_json = tmp_path / "funds_phase1.json"
    temp_phase1_json.write_text(json.dumps(phase1_data, ensure_ascii=False), encoding="utf-8")

    # Point Phase 3 config to our temporary Phase 1 JSON and a non-existent DB,
    # so load_known_funds() will fall back to this JSON file.
    temp_db = tmp_path / "phase2.db"
    monkeypatch.setattr(phase3_config, "PHASE1_JSON_PATH", temp_phase1_json)
    monkeypatch.setattr(phase3_config, "PHASE2_DB_PATH", temp_db)

    query = (
        "what is the % of return in 3year for "
        "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth MF"
    )

    parsed = route_query(query, use_groq=False)

    assert isinstance(parsed, ParsedQuery)
    assert parsed.question_type == "attribute_query"
    assert "icici-prudential-top-100-fund-direct-growth" in parsed.fund_slugs
    assert "returns_3y" in parsed.attributes


def test_route_query_can_use_groq_if_available(monkeypatch):
    """
    High-level test for Groq integration path: we stub the Groq classifier
    to ensure that route_query() prefers its result when provided.
    No real API calls are made.
    """
    from src.phase3 import router as phase3_router
    from src.phase3.schemas import ParsedQuery

    query = "what is the % of return in 3year for ICICI Prudential Large & Mid Cap Fund Direct Plan Growth"

    # Stub known funds.
    monkeypatch.setattr(
        phase3_router,
        "load_known_funds",
        lambda: [("icici-prudential-top-100-fund-direct-growth", "ICICI Prudential Large & Mid Cap Fund Direct Plan Growth")],
    )

    # Stub Groq classifier to return a specific ParsedQuery.
    def fake_classify_with_groq(q, known_funds, attributes):
        return ParsedQuery(
            raw_query=q,
            question_type="attribute_query",
            fund_slugs=["icici-prudential-top-100-fund-direct-growth"],
            attributes=["returns_3y"],
        )

    monkeypatch.setattr(phase3_router, "classify_with_groq", fake_classify_with_groq)

    parsed = phase3_router.route_query(query, use_groq=True)

    assert parsed.question_type == "attribute_query"
    assert parsed.fund_slugs == ["icici-prudential-top-100-fund-direct-growth"]
    assert "returns_3y" in parsed.attributes

