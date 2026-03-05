from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.phase2 import config as phase2_config
from src.phase4.service import answer_message


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    question_type: str
    funds: List[str]


class MetaResponse(BaseModel):
    last_updated: Optional[str] = None


app = FastAPI(
    title="Groww Mutual Fund RAG Chatbot API",
    version="0.1.0",
    description="Backend service for the Groww mutual fund RAG chatbot.",
)

# Allow frontend (Vite dev server) to call the API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Deployed Netlify frontend
        "https://jazzy-selkie-0ac22f.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    """
    Simple health/info endpoint so hitting the Render root URL
    (e.g. https://mutual-fund-genai-chatbot.onrender.com/) does not 404.
    """
    return {
        "status": "ok",
        "message": "Groww Mutual Fund RAG backend",
        "endpoints": ["/chat", "/meta"],
    }


def _compute_last_updated() -> Optional[str]:
    path: Path = phase2_config.PHASE1_JSON_PATH
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, list) or not data:
        return None
    timestamps = []
    for item in data:
        if isinstance(item, dict):
            ts = item.get("last_updated")
            if isinstance(ts, str):
                timestamps.append(ts)
    if not timestamps:
        return None
    # Use the max timestamp string (ISO 8601 timestamps are lexicographically sortable).
    return max(timestamps)


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.
    - Delegates to Phase 4 answer_message() for routing and answer generation.
    - Always returns at least an answer string and possibly one or more sources.
    """
    result = answer_message(request.message)
    return ChatResponse(
        answer=result.answer,
        sources=result.sources,
        question_type=result.question_type,
        funds=result.funds,
    )


@app.get("/meta", response_model=MetaResponse)
def meta_endpoint() -> MetaResponse:
    """
    Returns simple metadata such as the last_updated timestamp derived from
    the Phase 1 JSON file. This is used by the frontend to display when
    the data was last refreshed by the scheduler.
    """
    return MetaResponse(last_updated=_compute_last_updated())

