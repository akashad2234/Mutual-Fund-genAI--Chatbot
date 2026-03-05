from __future__ import annotations

import logging
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


SECTION_TITLES = {
    "return_calculator": "Return calculator",
    "holdings": "Holdings",
    "holdings_analysis": "Holdings analysis",
    "equity_sector_allocation": "Equity sector allocation",
    "advanced_ratios": "Advanced ratios",
    "minimum_investments": "Minimum investments",
    "returns_and_rankings": "Returns and rankings",
    "exit_load_stamp_duty_tax": "Exit load, stamp duty and tax",
}


@dataclass
class FundAttributes:
    expense_ratio: Optional[str] = None
    minimum_sip: Optional[str] = None
    exit_load_summary: Optional[str] = None
    lock_in: Optional[str] = None
    riskometer: Optional[str] = None
    benchmark: Optional[str] = None
    statements_info: Optional[str] = None


@dataclass
class FundPageData:
    name: Optional[str]
    url: str
    slug: str
    attributes: FundAttributes
    sections: Dict[str, Optional[str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "slug": self.slug,
            "attributes": asdict(self.attributes),
            "sections": self.sections,
        }


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_page_title(soup: BeautifulSoup) -> Optional[str]:
    if soup.title and soup.title.string:
        return _clean_text(soup.title.string)
    h1 = soup.find("h1")
    return _clean_text(h1.get_text()) if h1 else None


def _extract_expense_ratio(text: str) -> Optional[str]:
    # Look for patterns like "Expense ratio 0.86%"
    m = re.search(r"Expense\s*ratio[^0-9%]*([\d.,]+\s*%)", text, flags=re.IGNORECASE)
    return _clean_text(m.group(1)) if m else None


def _extract_minimum_sip(text: str) -> Optional[str]:
    # Pattern around "Min. for SIP ₹100"
    m = re.search(
        r"Min\.?\s*for\s*SIP[^₹0-9]*([₹\s\d,]+)",
        text,
        flags=re.IGNORECASE,
    )
    return _clean_text(m.group(1)) if m else None


def _extract_exit_load_summary(text: str) -> Optional[str]:
    # Use first concise sentence under "Exit load" or "Exit load, stamp duty and tax"
    m = re.search(
        r"Exit\s*load[^.:]*[:\-]?\s*([^.]+?\.)",
        text,
        flags=re.IGNORECASE,
    )
    return _clean_text(m.group(1)) if m else None


def _extract_lock_in(text: str) -> Optional[str]:
    # ELSS funds usually mention 3 year lock-in
    m = re.search(
        r"lock[-\s]*in[^0-9]*([\d]+\s*year[s]?)",
        text,
        flags=re.IGNORECASE,
    )
    return _clean_text(m.group(1)) if m else None


def _extract_riskometer(text: str) -> Optional[str]:
    # Look for "Riskometer" or "Risk" plus a label like "Very High"
    m = re.search(
        r"(Riskometer|Risk level)[^A-Za-z]*(Low to moderate|Low|Moderate|Moderately high|High|Very high)",
        text,
        flags=re.IGNORECASE,
    )
    return _clean_text(m.group(2)) if m else None


def _extract_benchmark(text: str) -> Optional[str]:
    m = re.search(
        r"Benchmark[^:]*[:\-]\s*([^\n]+)",
        text,
        flags=re.IGNORECASE,
    )
    return _clean_text(m.group(1)) if m else None


def _find_section_text(soup: BeautifulSoup, title_snippet: str) -> Optional[str]:
    """
    Find a section by heading text and return a plain-text snippet of the
    content that follows it until the next heading at similar level.
    """
    # Consider h1–h4 as headings.
    heading = soup.find(
        lambda tag: tag.name in ("h1", "h2", "h3", "h4")
        and title_snippet.lower() in tag.get_text(strip=True).lower()
    )
    if not heading:
        return None

    texts = []
    for sibling in heading.find_all_next():
        if sibling.name in ("h1", "h2", "h3", "h4"):
            break
        # Skip scripts/styles
        if sibling.name in ("script", "style"):
            continue
        # Capture table rows as text, otherwise generic text.
        texts.append(sibling.get_text(separator=" ", strip=True))

    joined = " ".join(filter(None, texts))
    return _clean_text(joined) if joined else None


def parse_fund_page_html(html: str, url: str, slug: str) -> FundPageData:
    """
    Parse a Groww mutual fund HTML page into structured attributes and
    section-level text.
    """
    soup = BeautifulSoup(html, "lxml")
    full_text = _clean_text(soup.get_text(separator=" "))

    attributes = FundAttributes(
        expense_ratio=_extract_expense_ratio(full_text),
        minimum_sip=_extract_minimum_sip(full_text),
        exit_load_summary=_extract_exit_load_summary(full_text),
        lock_in=_extract_lock_in(full_text),
        riskometer=_extract_riskometer(full_text),
        benchmark=_extract_benchmark(full_text),
        # Phase 1: placeholder – will wire to help/FAQ pages later.
        statements_info=None,
    )

    sections: Dict[str, Optional[str]] = {}
    for key, title in SECTION_TITLES.items():
        section_text = _find_section_text(soup, title)
        sections[key] = section_text
        logger.debug("Section %s found=%s", key, bool(section_text))

    name = _extract_page_title(soup)

    return FundPageData(
        name=name,
        url=url,
        slug=slug,
        attributes=attributes,
        sections=sections,
    )

