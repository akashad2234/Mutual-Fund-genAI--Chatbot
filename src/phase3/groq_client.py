from __future__ import annotations

import json
import os
from typing import List, Optional, Tuple

import requests

from src import env_loader  # noqa: F401  - ensures .env is loaded

from . import config
from .schemas import ParsedQuery


def _get_api_key() -> Optional[str]:
    return os.getenv(config.GROQ_API_KEY_ENV)


def classify_with_groq(
    query: str, known_funds: List[Tuple[str, str]], attributes: List[str]
) -> Optional[ParsedQuery]:
    """
    Optional Groq-powered classifier. If no API key is configured or an
    error occurs, returns None so callers can fall back to rule-based logic.
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    funds_hint = [{"slug": slug, "name": name} for slug, name in known_funds]

    system_prompt = (
        "You are a classifier for a mutual fund Q&A chatbot that only uses "
        "official Groww pages.\n"
        "Your task is to classify the user's question and extract:\n"
        "- question_type: 'attribute_query', 'procedural_query', or 'out_of_scope'\n"
        "- fund_slugs: list of slugs from the provided fund catalog (may be empty)\n"
        "- attributes: list of attribute identifiers such as "
        "'expense_ratio', 'exit_load', 'minimum_sip', 'lock_in', "
        "'riskometer', 'benchmark'.\n"
        "Return strictly valid JSON matching this schema and do not add explanations."
    )

    user_payload = {
        "query": query,
        "known_funds": funds_hint,
        "attribute_hints": attributes,
    }

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.GROQ_MODEL,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, ensure_ascii=False),
                    },
                ],
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        obj = json.loads(content)
        question_type = obj.get("question_type", "attribute_query")
        fund_slugs = obj.get("fund_slugs") or []
        attrs = obj.get("attributes") or []
        return ParsedQuery(
            raw_query=query,
            question_type=question_type,  # type: ignore[arg-type]
            fund_slugs=list(fund_slugs),
            attributes=list(attrs),
        )
    except Exception:
        # Silent fallback: the caller will use rule-based routing.
        return None

