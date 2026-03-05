from __future__ import annotations

from pathlib import Path

from src.phase1 import config as phase1_config

# Path to the Phase 1 JSON output listing all funds and their sections.
PHASE1_JSON_PATH: Path = Path(phase1_config.OUTPUT_JSON)

# SQLite database used as the local relational knowledge store.
DB_PATH: Path = Path(phase1_config.STRUCTURED_DIR) / "phase2.db"

# Table names.
MUTUAL_FUND_TABLE = "mutual_fund"
DOC_CHUNK_TABLE = "doc_chunk"

