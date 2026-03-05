from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.phase2.db import init_schema
from src.phase4.service import answer_message
from src.phase4 import config as phase4_config


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


def test_answer_message_returns_3y_return_and_source(tmp_path, monkeypatch):
    """
    Integration-style test across Phases 2–4 that mimics the desired behaviour:

    User query:
      "what is the % of return in 3year for
       https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth MF"

    Expected behaviour:
    - Classified as attribute_query.
    - Fund slug resolved.
    - 3-year return (22.21%) present in the answer.
    - Source URL included in the sources list.
    """
    temp_db = tmp_path / "phase2.db"
    _create_temp_db_with_icici_fund(temp_db)

    # Point Phase 4 (and thus Phase 3's DB-backed fund loading) to our temp DB.
    monkeypatch.setattr(phase4_config, "DB_PATH", temp_db)

    query = (
        "what is the % of return in 3year for "
        "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth MF"
    )

    result = answer_message(query, use_groq=False, db_path=temp_db)

    assert result.question_type == "attribute_query"
    assert "icici-prudential-top-100-fund-direct-growth" in result.funds
    assert "22.21%" in result.answer
    assert any(
        "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth"
        in src
        for src in result.sources
    )

