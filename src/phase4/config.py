from __future__ import annotations

from pathlib import Path

from src.phase2 import config as phase2_config

# Use the same SQLite DB as Phase 2 for attribute lookups.
DB_PATH: Path = phase2_config.DB_PATH

# Mapping from canonical attribute identifiers to human-readable labels.
ATTRIBUTE_LABELS = {
    "expense_ratio": "Expense ratio",
    "exit_load": "Exit load",
    "minimum_sip": "Minimum SIP",
    "lock_in": "Lock-in period",
    "riskometer": "Riskometer",
    "benchmark": "Benchmark",
    "returns_3y": "3-year return",
}

