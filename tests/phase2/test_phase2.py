import json
from pathlib import Path

import sqlite3

from src.phase2.loader import run_phase2
from src.phase2 import config as phase2_config


def test_run_phase2_loads_funds_and_builds_chunks(tmp_path, monkeypatch):
    """
    End-to-end style test for Phase 2:
    - Creates a small Phase 1-style JSON file.
    - Points Phase 2 at that JSON and at a temporary SQLite DB.
    - Runs Phase 2 and verifies that:
      - At least one fund is loaded into the DB.
      - At least one chunk is created.
    """
    # Create a fake Phase 1 JSON file.
    phase1_data = [
        {
            "name": "Sample Fund Direct Growth",
            "url": "https://groww.in/mutual-funds/sample-fund-direct-growth",
            "slug": "sample-fund-direct-growth",
            "attributes": {
                "expense_ratio": "0.86%",
                "minimum_sip": "₹100",
                "exit_load_summary": "Exit load of 0.5%, if redeemed within 30 days.",
                "lock_in": None,
                "riskometer": "Very High",
                "benchmark": "Sample Index",
            },
            "sections": {
                "return_calculator": "Return calculator content.",
                "holdings": "Holdings content.",
                "minimum_investments": "Minimum investments content.",
            },
        }
    ]

    temp_phase1_json = tmp_path / "funds_phase1.json"
    temp_phase1_json.write_text(json.dumps(phase1_data, ensure_ascii=False), encoding="utf-8")

    # Point Phase 2 config to a temporary DB and JSON file.
    temp_db = tmp_path / "phase2.db"
    monkeypatch.setattr(phase2_config, "DB_PATH", temp_db)
    monkeypatch.setattr(phase2_config, "PHASE1_JSON_PATH", temp_phase1_json)

    summary = run_phase2(db_path=temp_db, phase1_json_path=temp_phase1_json)

    assert summary["fund_count"] == 1
    assert summary["chunk_count"] >= 1
    assert Path(summary["db_path"]).exists()

    # Inspect DB contents directly to ensure data landed correctly.
    conn = sqlite3.connect(temp_db)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {phase2_config.MUTUAL_FUND_TABLE};")
        (fund_rows,) = cur.fetchone()
        assert fund_rows == 1

        cur.execute(f"SELECT COUNT(*) FROM {phase2_config.DOC_CHUNK_TABLE};")
        (chunk_rows,) = cur.fetchone()
        assert chunk_rows == summary["chunk_count"]
    finally:
        conn.close()

