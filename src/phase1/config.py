from __future__ import annotations

from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass(frozen=True)
class FundSource:
    """Configuration for a single Groww mutual fund page."""

    name: str
    url: str
    slug: str


# Initial list of funds in scope for Phase 1.
FUND_SOURCES: List[FundSource] = [
    FundSource(
        name="Bandhan Large Cap Fund Direct Growth",
        url="https://groww.in/mutual-funds/idfc-equity-fund-direct-growth",
        slug="idfc-equity-fund-direct-growth",
    ),
    FundSource(
        name="Bandhan Large & Mid Cap Fund Direct Growth",
        url="https://groww.in/mutual-funds/bandhan-large-mid-cap-fund-direct-growth",
        slug="bandhan-large-mid-cap-fund-direct-growth",
    ),
    FundSource(
        name="ICICI Prudential Top 100 Fund Direct Growth",
        url="https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth",
        slug="icici-prudential-top-100-fund-direct-growth",
    ),
    FundSource(
        name="ITI ELSS Tax Saver Fund Direct Growth",
        url="https://groww.in/mutual-funds/iti-elss-tax-saver-fund-direct-growth",
        slug="iti-elss-tax-saver-fund-direct-growth",
    ),
    FundSource(
        name="ITI Flexi Cap Fund Direct Growth",
        url="https://groww.in/mutual-funds/iti-flexi-cap-fund-direct-growth",
        slug="iti-flexi-cap-fund-direct-growth",
    ),
]


DATA_DIR = "data"
STRUCTURED_DIR = str(Path(DATA_DIR) / "structured")
OUTPUT_JSON = str(Path(STRUCTURED_DIR) / "funds_phase1.json")

