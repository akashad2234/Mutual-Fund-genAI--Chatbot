from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

from src.phase3.router import route_query
from src.phase3.schemas import ParsedQuery

from . import config


@dataclass
class AnswerResult:
    answer: str
    sources: List[str]
    question_type: str
    funds: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


def _get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def _fetch_fund_row(
    fund_slug: str, db_path: Optional[Path] = None
) -> Optional[Dict]:
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT fund_slug, fund_name, url,
                   expense_ratio, minimum_sip, exit_load_summary,
                   lock_in, riskometer, benchmark,
                   attributes_json
            FROM mutual_fund
            WHERE fund_slug = ?;
            """,
            (fund_slug,),
        )
        row = cur.fetchone()
        if not row:
            return None
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
            attributes_json,
        ) = row
        attrs_extra = json.loads(attributes_json or "{}")
        return {
            "fund_slug": slug,
            "fund_name": name,
            "url": url,
            "expense_ratio": expense_ratio,
            "minimum_sip": minimum_sip,
            "exit_load_summary": exit_load_summary,
            "lock_in": lock_in,
            "riskometer": riskometer,
            "benchmark": benchmark,
            "attributes_extra": attrs_extra,
        }
    finally:
        conn.close()


def _format_attribute_value(attr: str, fund_row: Dict) -> Optional[str]:
    extra = fund_row.get("attributes_extra") or {}
    if attr == "expense_ratio":
        return fund_row.get("expense_ratio") or extra.get("expense_ratio")
    if attr == "minimum_sip":
        return fund_row.get("minimum_sip") or extra.get("minimum_sip")
    if attr == "exit_load":
        return fund_row.get("exit_load_summary") or extra.get("exit_load_summary")
    if attr == "lock_in":
        return fund_row.get("lock_in") or extra.get("lock_in")
    if attr == "riskometer":
        return fund_row.get("riskometer") or extra.get("riskometer")
    if attr == "benchmark":
        return fund_row.get("benchmark") or extra.get("benchmark")
    if attr == "returns_3y":
        # Stored only in attributes_json for now.
        return extra.get("returns_3y")
    return None


def _generate_attribute_answer(
    parsed: ParsedQuery, db_path: Optional[Path] = None
) -> AnswerResult:
    if not parsed.fund_slugs:
        answer = (
            "I could not identify which mutual fund you are asking about from the query."
        )
        return AnswerResult(
            answer=answer,
            sources=[],
            question_type=parsed.question_type,
            funds=[],
        )

    fund_slug = parsed.fund_slugs[0]
    fund_row = _fetch_fund_row(fund_slug, db_path=db_path)
    if not fund_row:
        answer = (
            "I could not find structured data for that fund in the knowledge store."
        )
        return AnswerResult(
            answer=answer,
            sources=[],
            question_type=parsed.question_type,
            funds=[fund_slug],
        )

    fund_name = fund_row["fund_name"]
    url = fund_row["url"]

    # Build a bullet list of available attributes.
    lines: List[str] = [f"For {fund_name}:"]
    for attr in parsed.attributes or []:
        label = config.ATTRIBUTE_LABELS.get(attr, attr)
        value = _format_attribute_value(attr, fund_row)
        if value is not None:
            lines.append(f"- {label}: {value}")

    # If no specific attributes requested or none found, fall back to expense ratio and exit load, if available.
    if len(lines) == 1:
        value_er = _format_attribute_value("expense_ratio", fund_row)
        value_ex = _format_attribute_value("exit_load", fund_row)
        if value_er:
            lines.append(f"- {config.ATTRIBUTE_LABELS['expense_ratio']}: {value_er}")
        if value_ex:
            lines.append(f"- {config.ATTRIBUTE_LABELS['exit_load']}: {value_ex}")

    if len(lines) == 1:
        lines.append("I could not find any of the requested attributes for this fund.")

    lines.append(f"Source: {url}")

    return AnswerResult(
        answer="\n".join(lines),
        sources=[url],
        question_type=parsed.question_type,
        funds=parsed.fund_slugs,
    )


def _generate_procedural_answer(parsed: ParsedQuery) -> AnswerResult:
    # Placeholder implementation for now.
    answer = (
        "This looks like a procedural question. The current Phase 4 implementation "
        "does not yet generate step-by-step instructions, but the RAG pipeline "
        "will eventually use Groww help pages to answer these."
    )
    return AnswerResult(
        answer=answer,
        sources=[],
        question_type=parsed.question_type,
        funds=parsed.fund_slugs,
    )


def _generate_out_of_scope_answer(parsed: ParsedQuery) -> AnswerResult:
    answer = (
        "I’m not allowed to provide investment advice, recommendations, or opinions. "
        "I can only share factual information from official Groww pages."
    )
    return AnswerResult(
        answer=answer,
        sources=[],
        question_type=parsed.question_type,
        funds=parsed.fund_slugs,
    )


def answer_message(
    message: str, use_groq: bool = True, db_path: Optional[Path] = None
) -> AnswerResult:
    """
    High-level Phase 4 entry point:
    - Uses Phase 3 router to interpret the message.
    - Dispatches to the appropriate path.
    """
    parsed = route_query(message, use_groq=use_groq)

    if parsed.question_type == "attribute_query":
        return _generate_attribute_answer(parsed, db_path=db_path)
    if parsed.question_type == "procedural_query":
        return _generate_procedural_answer(parsed)
    return _generate_out_of_scope_answer(parsed)

