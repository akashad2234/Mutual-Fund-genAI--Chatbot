from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from . import config as phase1_config
from .fetch import fetch_html
from .parse import parse_fund_page_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("phase1")


def ensure_data_dir() -> Path:
    """
    Ensure that both the base data directory and the structured
    subdirectory exist.
    """
    data_path = Path(phase1_config.DATA_DIR)
    structured_path = Path(phase1_config.STRUCTURED_DIR)
    data_path.mkdir(parents=True, exist_ok=True)
    structured_path.mkdir(parents=True, exist_ok=True)
    return structured_path


def run_phase1() -> List[Dict]:
    ensure_data_dir()

    results: List[Dict] = []

    for fund in phase1_config.FUND_SOURCES:
        logger.info("Processing fund: %s (%s)", fund.name, fund.url)
        fetch_result = fetch_html(fund.url)
        if not fetch_result.ok or not fetch_result.content:
            logger.error(
                "Failed to fetch %s: %s", fund.url, fetch_result.error or fetch_result.status_code
            )
            continue

        parsed = parse_fund_page_html(fetch_result.content, fund.url, fund.slug)
        fund_dict = parsed.to_dict()
        results.append(fund_dict)

    # Stamp all records with a common last_updated timestamp.
    timestamp = datetime.now(timezone.utc).isoformat()
    for fund_dict in results:
        fund_dict["last_updated"] = timestamp

    # Persist to JSON for inspection and for later phases.
    output_path = Path(phase1_config.OUTPUT_JSON)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("Saved Phase 1 data for %d funds to %s", len(results), output_path)

    return results


if __name__ == "__main__":
    run_phase1()

