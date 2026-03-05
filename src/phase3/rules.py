from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .schemas import ParsedQuery


ATTRIBUTE_KEYWORDS: Dict[str, List[str]] = {
    "expense_ratio": [
        "expense ratio",
        "er ",
        "er?",
    ],
    "exit_load": [
        "exit load",
    ],
    "minimum_sip": [
        "min sip",
        "minimum sip",
        "sip amount",
        "min. for sip",
    ],
    "lock_in": [
        "lock in",
        "lock-in",
        "lockin",
    ],
    "riskometer": [
        "riskometer",
        "risk level",
        "risk rating",
    ],
    "benchmark": [
        "benchmark",
    ],
    "returns_3y": [
        "3 year return",
        "3-year return",
        "3y return",
        "3year return",
        "3 year % return",
        "3 year percentage return",
    ],
}


PROCEDURAL_KEYWORDS = [
    "how to download",
    "download statement",
    "get statement",
    "account statement",
    "portfolio statement",
    "view statement",
]


ADVICE_KEYWORDS = [
    "should i invest",
    "should i buy",
    "which is better",
    "which fund is better",
    "best fund",
    "recommend",
    "suggest",
    "good time to invest",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def detect_attributes(query: str) -> List[str]:
    q = _normalize(query)
    found: List[str] = []
    for attr, kws in ATTRIBUTE_KEYWORDS.items():
        if any(kw in q for kw in kws):
            found.append(attr)
    return found


def detect_question_type(query: str, attrs: List[str]) -> str:
    q = _normalize(query)

    if any(kw in q for kw in ADVICE_KEYWORDS):
        return "out_of_scope"

    if any(kw in q for kw in PROCEDURAL_KEYWORDS):
        return "procedural_query"

    if attrs:
        return "attribute_query"

    # Heuristics: mention of "statement" without advice → procedural.
    if "statement" in q:
        return "procedural_query"

    # Default to attribute-style for now; Phase 4 will still enforce no advice.
    return "attribute_query"


def match_funds_by_name_or_slug(
    query: str, known_funds: List[Tuple[str, str]]
) -> List[str]:
    """
    Simple fuzzy-ish match:
    - If the query contains the full slug or a large part of the name, we
      consider it a match.
    known_funds: list of (slug, name)
    """
    q = _normalize(query)
    matches: List[str] = []

    for slug, name in known_funds:
        slug_norm = _normalize(slug.replace("-", " "))
        name_norm = _normalize(name)
        if slug_norm and slug_norm in q:
            matches.append(slug)
            continue
        # Check by key words from the name (e.g. "bandhan large cap").
        main_tokens = " ".join(name_norm.split()[:3])
        if main_tokens and main_tokens in q:
            matches.append(slug)

    # Deduplicate while preserving order.
    seen = set()
    result: List[str] = []
    for s in matches:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result


def apply_rules(query: str, known_funds: List[Tuple[str, str]]) -> ParsedQuery:
    attrs = detect_attributes(query)
    qtype = detect_question_type(query, attrs)
    funds = match_funds_by_name_or_slug(query, known_funds)
    return ParsedQuery(
        raw_query=query,
        question_type=qtype,  # type: ignore[arg-type]
        fund_slugs=funds,
        attributes=attrs,
    )

