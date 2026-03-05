from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load() -> None:
    """
    Load environment variables from:
    - A standard .env in the project root (if present).
    - data/.env (if present), overriding previous values.
    """
    # Default .env in current working directory / project root.
    load_dotenv()

    data_env = Path("data") / ".env"
    if data_env.exists():
        load_dotenv(dotenv_path=data_env, override=True)


# Automatically load when this module is imported.
load()

