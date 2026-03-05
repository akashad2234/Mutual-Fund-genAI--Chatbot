from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

QuestionType = Literal["attribute_query", "procedural_query", "out_of_scope"]


@dataclass
class ParsedQuery:
    """Normalized representation of a user query for downstream routing."""

    raw_query: str
    question_type: QuestionType
    fund_slugs: List[str]
    attributes: List[str]

