from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Tuple

from . import config
from .groq_client import classify_with_groq
from .rules import apply_rules
from .schemas import ParsedQuery


def _load_known_funds_from_db(db_path: Path) -> List[Tuple[str, str]]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT fund_slug, fund_name FROM mutual_fund;"
        )
        return [(slug, name) for slug, name in cur.fetchall()]
    finally:
        conn.close()


def _load_known_funds_from_phase1_json(json_path: Path) -> List[Tuple[str, str]]:
    if not json_path.exists():
        return []
    data = json.loads(json_path.read_text(encoding="utf-8"))
    funds: List[Tuple[str, str]] = []
    for item in data:
        slug = item.get("slug")
        name = item.get("name") or slug
        if slug and name:
            funds.append((slug, name))
    return funds


def load_known_funds() -> List[Tuple[str, str]]:
    """
    Load the catalog of known funds from Phase 2 DB if available,
    otherwise fall back to Phase 1 JSON.
    Returns a list of (slug, name) pairs.
    """
    funds = _load_known_funds_from_db(config.PHASE2_DB_PATH)
    if funds:
        return funds
    return _load_known_funds_from_phase1_json(config.PHASE1_JSON_PATH)


def route_query(query: str, use_groq: bool = True) -> ParsedQuery:
    """
    Main entry point for Phase 3.

    - Loads known funds from previous phases.
    - Applies rule-based routing to get a baseline ParsedQuery.
    - Optionally calls Groq LLM (if API key is configured) to refine the
      classification; falls back to the rule-based result on any error.
    """
    known_funds = load_known_funds()
    baseline = apply_rules(query, known_funds)

    if not use_groq:
        return baseline

    groq_result = classify_with_groq(
        query=query,
        known_funds=known_funds,
        attributes=baseline.attributes,
    )
    return groq_result or baseline

