from __future__ import annotations

import hashlib
from typing import Iterable, Tuple

import sqlite3

from . import config


def _fake_embed(text: str, dim: int = 8) -> str:
    """
    Deterministic, local-only "embedding" used for Phase 2 plumbing tests.

    It hashes the text and produces a comma-separated list of integers
    that behave like a tiny embedding vector. In production this should
    be replaced with a real embedding model.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Take the first `dim` bytes and normalise them into small ints.
    vals = [str(b) for b in h[:dim]]
    return ",".join(vals)


def build_doc_chunks(
    conn: sqlite3.Connection,
) -> int:
    """
    Build simple text chunks for each fund section and store them with
    a deterministic embedding. Returns the number of chunks created.
    """
    cursor = conn.cursor()

    # Delete existing chunks to simplify idempotency during development.
    cursor.execute(f"DELETE FROM {config.DOC_CHUNK_TABLE};")

    cursor.execute(
        f"SELECT fund_slug, sections_json FROM {config.MUTUAL_FUND_TABLE};"
    )

    total_chunks = 0
    for fund_slug, sections_json in cursor.fetchall():
        # sections_json is a JSON string mapping section_key -> text
        import json

        sections = json.loads(sections_json)
        for key, text in sections.items():
            if not text:
                continue
            emb = _fake_embed(text)
            cursor.execute(
                f"""
                INSERT INTO {config.DOC_CHUNK_TABLE} (
                    fund_slug, section_key, text, embedding
                )
                VALUES (?, ?, ?, ?);
                """,
                (fund_slug, key, text, emb),
            )
            total_chunks += 1

    return total_chunks

