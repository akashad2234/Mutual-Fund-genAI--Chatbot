from __future__ import annotations

import logging

from .loader import run_phase2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("phase2")


def main() -> None:
    summary = run_phase2()
    logger.info(
        "Phase 2 completed. Loaded %d funds and created %d chunks into %s",
        summary["fund_count"],
        summary["chunk_count"],
        summary["db_path"],
    )


if __name__ == "__main__":
    main()

