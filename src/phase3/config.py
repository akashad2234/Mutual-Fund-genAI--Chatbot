from __future__ import annotations

import os
from pathlib import Path

from src.phase2 import config as phase2_config

# Environment variable name that should hold the Groq API key.
GROQ_API_KEY_ENV = "GROQ_API_KEY"

# Default Groq model for classification / routing.
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

# Locations for existing knowledge from earlier phases.
PHASE1_JSON_PATH: Path = phase2_config.PHASE1_JSON_PATH
PHASE2_DB_PATH: Path = phase2_config.DB_PATH

