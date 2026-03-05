from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    url: str
    status_code: int
    ok: bool
    content: Optional[str]
    error: Optional[str]


DEFAULT_HEADERS = {
    # A realistic UA string helps avoid being blocked by some sites.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def fetch_html(url: str, timeout: int = 20) -> FetchResult:
    """Fetch a single URL and return HTML as text."""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        logger.info("Fetched %s (%s)", url, resp.status_code)
        if not resp.ok:
            return FetchResult(
                url=url,
                status_code=resp.status_code,
                ok=False,
                content=None,
                error=f"HTTP error {resp.status_code}",
            )
        return FetchResult(
            url=url,
            status_code=resp.status_code,
            ok=True,
            content=resp.text,
            error=None,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error fetching %s", url)
        return FetchResult(
            url=url,
            status_code=0,
            ok=False,
            content=None,
            error=str(exc),
        )

