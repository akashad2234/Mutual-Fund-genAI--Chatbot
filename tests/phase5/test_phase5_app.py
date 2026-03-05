from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from src.phase2.db import init_schema
from src.phase4 import config as phase4_config
from src.phase5.app import app


def _create_temp_db_with_icici_fund(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        init_schema(conn)
        cur = conn.cursor()
        attributes = {
            "expense_ratio": "0.78%",
            "minimum_sip": "₹100",
            "returns_3y": "22.21%",
        }
        sections = {}
        cur.execute(
            """
            INSERT INTO mutual_fund (
                fund_slug, fund_name, url,
                expense_ratio, minimum_sip, exit_load_summary,
                lock_in, riskometer, benchmark,
                attributes_json, sections_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "icici-prudential-top-100-fund-direct-growth",
                "ICICI Prudential Large & Mid Cap Fund Direct Plan Growth",
                "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth",
                attributes["expense_ratio"],
                attributes["minimum_sip"],
                "Exit load of 1% if redeemed within 1 month.",
                None,
                "Very High",
                "NIFTY Large Midcap 250 Total Return Index",
                json.dumps(attributes, ensure_ascii=False),
                json.dumps(sections, ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_chat_endpoint_returns_expected_3y_answer(tmp_path, monkeypatch):
    """
    End-to-end style test for Phase 5 backend service, integrating
    Phases 2–4 underneath.

    It verifies that a POST /chat call for the ICICI fund 3-year return
    produces an answer containing '22.21%' and the correct Groww URL,
    along with metadata fields.
    """
    temp_db = tmp_path / "phase2.db"
    _create_temp_db_with_icici_fund(temp_db)

    # Point Phase 4 (and thus routing/lookup) to our temp DB.
    monkeypatch.setattr(phase4_config, "DB_PATH", temp_db)

    client = TestClient(app)

    query = (
        "what is the % of return in 3year for "
        "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth MF"
    )

    resp = client.post("/chat", json={"message": query})
    assert resp.status_code == 200

    data = resp.json()

    assert data["question_type"] == "attribute_query"
    assert "icici-prudential-top-100-fund-direct-growth" in data["funds"]
    assert "22.21%" in data["answer"]
    assert any(
        "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth"
        in src
        for src in data["sources"]
    )

