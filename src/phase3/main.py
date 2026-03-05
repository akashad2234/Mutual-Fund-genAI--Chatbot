from __future__ import annotations

import logging
import sys

from .router import route_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("phase3")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m src.phase3.main \"your question here\"")
        sys.exit(1)
    query = sys.argv[1]
    parsed = route_query(query)
    logger.info("Parsed query: %s", parsed)
    print(parsed)


if __name__ == "__main__":
    main()

