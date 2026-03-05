from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Mapping

from . import config


@contextmanager
def get_connection(db_path: Path | None = None):
    """Context manager that yields a SQLite connection."""
    path = db_path or config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    """
    Create core Phase 2 tables if they do not already exist.
    - mutual_fund: structured attributes for each fund
    - doc_chunk: text chunks derived from sections, for RAG-style retrieval
    """
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {config.MUTUAL_FUND_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_slug TEXT UNIQUE NOT NULL,
            fund_name TEXT NOT NULL,
            url TEXT NOT NULL,
            expense_ratio TEXT,
            minimum_sip TEXT,
            exit_load_summary TEXT,
            lock_in TEXT,
            riskometer TEXT,
            benchmark TEXT,
            attributes_json TEXT NOT NULL,
            sections_json TEXT NOT NULL
        );
        """
    )

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {config.DOC_CHUNK_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_slug TEXT NOT NULL,
            section_key TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            FOREIGN KEY (fund_slug) REFERENCES {config.MUTUAL_FUND_TABLE}(fund_slug)
        );
        """
    )


def upsert_mutual_funds(
    conn: sqlite3.Connection, funds: Iterable[Mapping]
) -> int:
    """
    Insert or update mutual fund records from Phase 1 JSON.

    Returns the number of funds upserted.
    """
    cursor = conn.cursor()
    count = 0
    for fund in funds:
        slug = fund["slug"]
        name = fund.get("name") or slug
        url = fund["url"]
        attrs = fund.get("attributes") or {}
        sections = fund.get("sections") or {}

        expense_ratio = attrs.get("expense_ratio")
        minimum_sip = attrs.get("minimum_sip")
        exit_load_summary = attrs.get("exit_load_summary")
        lock_in = attrs.get("lock_in")
        riskometer = attrs.get("riskometer")
        benchmark = attrs.get("benchmark")

        cursor.execute(
            f"""
            INSERT INTO {config.MUTUAL_FUND_TABLE} (
                fund_slug, fund_name, url,
                expense_ratio, minimum_sip, exit_load_summary,
                lock_in, riskometer, benchmark,
                attributes_json, sections_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fund_slug) DO UPDATE SET
                fund_name=excluded.fund_name,
                url=excluded.url,
                expense_ratio=excluded.expense_ratio,
                minimum_sip=excluded.minimum_sip,
                exit_load_summary=excluded.exit_load_summary,
                lock_in=excluded.lock_in,
                riskometer=excluded.riskometer,
                benchmark=excluded.benchmark,
                attributes_json=excluded.attributes_json,
                sections_json=excluded.sections_json
            ;
            """,
            (
                slug,
                name,
                url,
                expense_ratio,
                minimum_sip,
                exit_load_summary,
                lock_in,
                riskometer,
                benchmark,
                json.dumps(attrs, ensure_ascii=False),
                json.dumps(sections, ensure_ascii=False),
            ),
        )
        count += 1
    return count

