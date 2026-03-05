from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.env_loader import load as load_env  # ensures .env is loaded
from src.phase2 import config as phase2_config
from src.phase4.service import answer_message


def get_last_updated() -> str | None:
    path: Path = phase2_config.PHASE1_JSON_PATH
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, list) or not data:
        return None
    timestamps: list[str] = []
    for item in data:
        if isinstance(item, dict):
            ts = item.get("last_updated")
            if isinstance(ts, str):
                timestamps.append(ts)
    return max(timestamps) if timestamps else None


def main() -> None:
    load_env()

    st.set_page_config(
        page_title="Groww Mutual Fund RAG Chatbot",
        page_icon="💹",
        layout="wide",
    )

    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.25rem;">
            <div style="
                width:34px;height:34px;border-radius:999px;
                background:linear-gradient(135deg,#04ad83,#17a5f5);
                display:flex;align-items:center;justify-content:center;
                color:white;font-weight:700;font-size:18px;
            ">
                G
            </div>
            <div>
                <div style="font-size:20px;font-weight:600;">
                    Groww Mutual Fund RAG Chatbot
                </div>
                <div style="font-size:12px;color:#6b7280;">
                    MF Facts · Powered by RAG
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            margin:0.4rem 0 0.9rem;
            padding:0.6rem 0.8rem;
            border-radius:0.5rem;
            background:#fef9c3;
            color:#854d0e;
            font-size:13px;
        ">
          <strong>Note:</strong> Ask factual questions about supported Groww mutual funds.
          Every answer comes from official Groww pages. No investment advice.
        </div>
        """,
        unsafe_allow_html=True,
    )

    last_updated = get_last_updated()
    if last_updated:
        st.markdown(
            f"**Last updated:** {last_updated}",
        )

    st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                st.markdown(
                    "Sources:\n" + "\n".join(f"- {src}" for src in msg["sources"])
                )

    prompt = st.chat_input(
        "Ask a question about a Groww mutual fund (expense ratio, exit load, SIP, 3-year return, etc.)"
    )
    if prompt:
        st.session_state.messages.append(
            {"role": "user", "content": prompt, "sources": []}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = answer_message(prompt)
            st.markdown(result.answer)
            if result.sources:
                st.markdown(
                    "Sources:\n" + "\n".join(f"- {src}" for src in result.sources)
                )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result.answer,
                "sources": result.sources,
            }
        )


if __name__ == "__main__":
    main()

