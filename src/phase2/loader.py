from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from . import config
from .db import get_connection, init_schema, upsert_mutual_funds
from .indexing import build_doc_chunks


def load_phase1_json(path: Path | None = None) -> List[Dict]:
    """Load the Phase 1 JSON output into memory."""
    p = path or config.PHASE1_JSON_PATH
    data = json.loads(Path(p).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Phase 1 JSON must be a list of fund records")
    return data


def run_phase2(db_path: Path | None = None, phase1_json_path: Path | None = None) -> dict:
    """
    Orchestrate Phase 2:
    - Ensure schema exists
    - Load Phase 1 JSON
    - Upsert mutual funds
    - Build document chunks with deterministic embeddings

    Returns a small summary dict useful for tests and diagnostics.
    """
    funds = load_phase1_json(phase1_json_path)

    from . import config as phase2_config

    # Override global paths if arguments are provided (used by tests).
    if db_path is not None:
        phase2_config.DB_PATH = Path(db_path)
    if phase1_json_path is not None:
        phase2_config.PHASE1_JSON_PATH = Path(phase1_json_path)

    from . import config as cfg

    with get_connection(cfg.DB_PATH) as conn:
        init_schema(conn)
        fund_count = upsert_mutual_funds(conn, funds)
        chunk_count = build_doc_chunks(conn)

        return {
            "fund_count": fund_count,
            "chunk_count": chunk_count,
            "db_path": str(cfg.DB_PATH),
        }

