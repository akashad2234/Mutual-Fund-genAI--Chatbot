from __future__ import annotations

import logging
import sys

from .service import answer_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("phase4")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m src.phase4.main \"your question here\"")
        sys.exit(1)
    query = sys.argv[1]
    result = answer_message(query)
    logger.info("Answer: %s", result.answer)
    logger.info("Sources: %s", result.sources)
    print(result.answer)
    if result.sources:
        print("Sources:")
        for src in result.sources:
            print(f"- {src}")


if __name__ == "__main__":
    main()

