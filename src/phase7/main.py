from __future__ import annotations

import logging
from typing import Any, Dict

from src.phase1.main import run_phase1
from src.phase2.loader import run_phase2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("phase7")


def run_refresh() -> Dict[str, Any]:
  """
  Run a single refresh cycle:
  - Phase 1: scrape Groww pages and write structured JSON
  - Phase 2: load JSON into SQLite and build chunks

  Returns a summary dict.
  """
  funds = run_phase1()
  phase2_summary = run_phase2()

  summary: Dict[str, Any] = {
      "phase1_fund_count": len(funds),
      "phase2_fund_count": phase2_summary.get("fund_count"),
      "chunk_count": phase2_summary.get("chunk_count"),
      "db_path": phase2_summary.get("db_path"),
  }

  logger.info(
      "Phase 7 refresh complete: %s", summary
  )
  return summary


def main() -> None:
  run_refresh()


if __name__ == "__main__":
  main()

