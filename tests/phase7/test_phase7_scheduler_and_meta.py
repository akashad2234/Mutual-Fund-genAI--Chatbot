from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.phase5.app import app, _compute_last_updated
from src.phase7.main import run_refresh
from src.phase2 import config as phase2_config


def test_run_refresh_calls_phase1_and_phase2(monkeypatch):
    """
    Verifies that the Phase 7 refresh orchestrator calls Phase 1 and Phase 2
    and returns a merged summary.
    """
    called = {"phase1": False, "phase2": False}

    def fake_run_phase1():
        called["phase1"] = True
        return [{"slug": "test-fund"}]

    def fake_run_phase2():
        called["phase2"] = True
        return {"fund_count": 1, "chunk_count": 2, "db_path": "/tmp/db.sqlite"}

    from src.phase7 import main as phase7_main

    monkeypatch.setattr(phase7_main, "run_phase1", fake_run_phase1)
    monkeypatch.setattr(phase7_main, "run_phase2", fake_run_phase2)

    summary = run_refresh()

    assert called["phase1"] is True
    assert called["phase2"] is True
    assert summary["phase1_fund_count"] == 1
    assert summary["phase2_fund_count"] == 1
    assert summary["chunk_count"] == 2


def test_meta_endpoint_returns_last_updated_from_phase1_json(tmp_path, monkeypatch):
    """
    Integration-style test for the /meta endpoint that checks it derives the
    last_updated timestamp from the Phase 1 JSON file.
    """
    # Create a temporary Phase 1 JSON file with per-fund last_updated values.
    data = [
        {"slug": "fund-a", "last_updated": "2026-03-03T10:00:00Z"},
        {"slug": "fund-b", "last_updated": "2026-03-04T12:30:00Z"},
    ]
    temp_json = tmp_path / "funds_phase1.json"
    temp_json.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(phase2_config, "PHASE1_JSON_PATH", temp_json)

    # Direct function check
    last_updated = _compute_last_updated()
    assert last_updated == "2026-03-04T12:30:00Z"

    # API-level check
    client = TestClient(app)
    resp = client.get("/meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_updated"] == "2026-03-04T12:30:00Z"

