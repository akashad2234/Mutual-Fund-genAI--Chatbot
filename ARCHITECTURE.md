## System Architecture – Groww Mutual Fund RAG Chatbot

This document describes the end‑to‑end architecture for the Groww mutual fund RAG chatbot, with a focus on:

- Using **only official Groww public pages** as sources.
- Supporting questions on:
  - Return calculator, Holdings, Holdings analysis
  - Equity sector allocation, Advanced ratios
  - Minimum investments, Returns and rankings
  - Exit load, stamp duty and tax
  - Expense ratio, exit load, minimum SIP, lock‑in (ELSS), riskometer, benchmark
  - How to download statements
- Ensuring **every answer includes at least one Groww URL** and **no investment advice**.

---

## 1. High‑Level Overview

- **Phase 1 – Data acquisition & normalization**  
  Fetch Groww fund/help pages and extract structured fields and section text (already implemented for fund pages).

- **Phase 2 – Knowledge store & indexing**  
  Load Phase 1 output into a database and vector store for efficient retrieval.

- **Phase 3 – Query understanding & routing**  
  Classify questions (attribute vs. procedural vs. out‑of‑scope) and resolve fund names and attributes.

- **Phase 4 – Answer generation & safety**  
  Generate factual, sourced, non‑advisory answers using DB lookups and RAG over Groww content.

- **Phase 5 – Backend services**  
  Expose a `POST /chat` API and optional admin endpoints.

- **Phase 6 – Frontend chat application**  
  Web UI that calls the backend, renders answers and Groww links.

- **Phase 7 – Scheduler & refresh pipeline**  
  Periodically refresh Groww data, re‑run parsers/indexers so the chatbot always uses the latest information.

Tech stack suggestion:

- **Backend**: Python, FastAPI (or similar)
- **Ingestion**: `requests`, `beautifulsoup4`, `lxml`
- **Storage**: PostgreSQL (or SQLite initially), plus a vector DB (Chroma/Qdrant)
- **Frontend**: React/Next.js (or any SPA framework)
- **LLM**: Hosted API with strong system prompts and JSON output

---

## 2. Phase 1 – Data Acquisition & Normalization

Implemented in this repo under `src/phase1`.

- **Inputs**:
  - Fund detail URLs, for example:
    - `https://groww.in/mutual-funds/idfc-equity-fund-direct-growth`
    - `https://groww.in/mutual-funds/bandhan-large-mid-cap-fund-direct-growth`
    - `https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth`
    - `https://groww.in/mutual-funds/iti-elss-tax-saver-fund-direct-growth`
    - `https://groww.in/mutual-funds/iti-flexi-cap-fund-direct-growth`
  - Later: Groww help/FAQ URLs (for “how to download statements”, taxation details, etc.).

- **Components**:
  - `phase1.config`  
    - Defines a list of `FundSource` objects (name, URL, slug) and output paths.
  - `phase1.fetch`  
    - `fetch_html(url)` uses `requests` to download each page with retry‑friendly settings.
  - `phase1.parse`  
    - Extracts:
      - **Key attributes** (via regex on full page text):
        - `expense_ratio`, `minimum_sip`
        - `exit_load_summary`
        - `lock_in` (ELSS lock‑in where applicable)
        - `riskometer`
        - `benchmark`
      - **Section‑level text snippets**:
        - Return calculator
        - Holdings
        - Holdings analysis
        - Equity sector allocation
        - Advanced ratios
        - Minimum investments
        - Returns and rankings
        - Exit load, stamp duty and tax
      - A placeholder `statements_info` field (to be populated from help/FAQ pages).
  - `phase1.main`  
    - Orchestrates fetching and parsing for all configured funds.
    - Writes a consolidated JSON file: `data/funds_phase1.json`.

**Output format** (per fund, conceptual):

```json
{
  "name": "Bandhan Large Cap Fund Direct Growth",
  "url": "https://groww.in/mutual-funds/idfc-equity-fund-direct-growth",
  "slug": "idfc-equity-fund-direct-growth",
  "attributes": {
    "expense_ratio": "0.86%",
    "minimum_sip": "₹100",
    "exit_load_summary": "Exit load of 0.5%, if redeemed within 30 days.",
    "lock_in": null,
    "riskometer": "Very High",
    "benchmark": "NIFTY 100 Total Return Index",
    "statements_info": null
  },
  "sections": {
    "return_calculator": "...",
    "holdings": "...",
    "holdings_analysis": "...",
    "equity_sector_allocation": "...",
    "advanced_ratios": "...",
    "minimum_investments": "...",
    "returns_and_rankings": "...",
    "exit_load_stamp_duty_tax": "..."
  }
}
```

This JSON is the **canonical input** for later phases (DB load and indexing).

---

## 3. Phase 2 – Knowledge Store & Indexing

**Goal**: Turn Phase 1 output into query‑friendly storage layers.

- **Relational store (fund attributes)**:
  - Table `mutual_fund` (example fields):
    - `id`, `fund_slug`, `fund_name`
    - `expense_ratio`, `exit_load`, `minimum_sip`
    - `lock_in`, `riskometer`, `benchmark`
    - `source_url`, `last_scraped_at`
  - This is the source of truth for direct attribute queries.

- **Document store (section content & help articles)**:
  - `help_article` table for Groww help/FAQ pages:
    - `id`, `url`, `title`, `raw_html`, `raw_text`, `last_scraped_at`
  - For fund pages, the `sections` text from Phase 1 can either:
    - Stay in JSON, or
    - Be loaded into separate tables/JSONB columns for analysis.

- **Vector index (RAG corpus)**:
  - Chunked texts (200–400 tokens, with overlap) from:
    - `help_article.raw_text` (statements and tax how‑tos).
    - Optionally, explanatory parts of fund pages (not numeric attributes).
  - Stored in a vector DB (Chroma/Qdrant) with metadata:
    - `url`, `title`, `section_heading`, `doc_type`, `last_indexed_at`.

Indexing pipeline:

1. Detect new/updated rows in `help_article` or other sources.
2. Chunk text to passages.
3. Embed and upsert into vector DB with metadata.

---

## 4. Phase 3 – Query Understanding & Routing (Groq LLM)

**Goal**: Interpret user questions and decide which data path to use, using Groq LLM for classification where helpful.

- **Question types (via Groq LLM classifier + rules)**:
  - `attribute_query`  
    Questions about: expense ratio, exit load, min SIP, lock‑in, riskometer, benchmark, fund‑level returns, etc.
  - `procedural_query`  
    Questions like: “How do I download my mutual fund statement?”, “Where can I see my holdings?”.
  - `out_of_scope`  
    Investment advice, recommendations, comparisons (“which is better?”, “should I invest?”).

- **Entities (Groq‑assisted where needed)**:
  - Fund resolution:
    - Map user text to a known `fund_slug` via fuzzy matching on `mutual_fund.fund_name`.
  - Attribute mapping:
    - Map surface forms to canonical attributes (e.g. “ER” → `expense_ratio`, “min SIP” → `minimum_sip`).

- **Routing logic**:
  - If `attribute_query`:
    - Use fund + attribute list to pull data directly from `mutual_fund`.
  - If `procedural_query`:
    - Use semantic search over vector DB filtered to Groww help/FAQ content.
  - If `out_of_scope`:
    - Return a policy response explaining that no investment advice is provided.

Routing is implemented as a hybrid:

- Simple rules (regex/keyword) for obvious patterns.
- A **Groq LLM‑powered classifier** that takes the user query and returns:
  - `question_type` (`attribute_query`, `procedural_query`, or `out_of_scope`)
  - `fund_slugs` (resolved fund identifiers, if any)
  - `attributes` (normalized attribute names, if any).

---

## 5. Phase 4 – Answer Generation & Safety

**Goal**: Produce concise, factual answers with at least one Groww link, and no advice.

- **Attribute path**:
  - Prefer deterministic templates using DB values:
    - Example:  
      “The expense ratio of {fund_name} (Direct Growth) is {expense_ratio}% and the exit load is {exit_load}.  
      Source: {source_url}”
  - Optionally use a small LLM, with:
    - Strict system prompt (no advice, must include given `source_url`).
    - JSON output format for easy validation.

- **Procedural / RAG path**:
  - Provide LLM with:
    - User query.
    - Top‑k retrieved Groww help/FAQ chunks (with URLs).
  - System prompt:
    - Use only the provided context.
    - No investment advice or recommendations.
    - Always include at least one Groww URL from the context in the answer.

- **Safety & validation**:
  - Post‑generation filter to block advisory language (“you should invest”, “I recommend”, “best fund”, etc.).
  - Enforce:
    - `sources` not empty.
    - All URLs under `https://groww.in/`.
  - If checks fail, regenerate or return a safe fallback.

---

## 6. Phase 5 – Backend Services

**Goal**: Provide a simple, stable API over all logic.

- **Chat endpoint**:
  - `POST /chat`
  - Request:
    ```json
    { "message": "What is the expense ratio of IDFC Equity Fund direct growth?", "session_id": "optional" }
    ```
  - Steps:
    1. Query router (Phase 3).
    2. Retrieval (DB or vector DB).
    3. Answer generation + safety checks (Phase 4).
  - Response:
    ```json
    {
      "answer": "The expense ratio of ...",
      "sources": ["https://groww.in/mutual-funds/idfc-equity-fund-direct-growth"],
      "question_type": "attribute_query",
      "funds": ["idfc-equity-fund-direct-growth"]
    }
    ```

- **Admin endpoints (optional)**:
  - `GET /admin/funds` – list funds and last update times.
  - `POST /admin/reindex` – trigger reindexing.
  - `GET /admin/health` – check ingestion/indexer health.

---

## 7. Phase 6 – Frontend Chat Application

**Goal**: User‑facing interface for the chatbot.

- **Features**:
  - Chat style conversation view (user + bot messages).
  - Input box, send button, keyboard shortcuts.
  - Clear display of **source links** below each bot answer.
  - Disclaimer/banner: “No investment advice. Information sourced from Groww public pages only.”

- **Flow**:
  - User types a question.
  - Frontend sends `POST /chat`.
  - Renders `answer` and `sources` from the response.

- **Implementation options**:
  - React/Next.js frontend calling the backend via REST.
  - Simple local dev setup pointing to the same backend used by your Phase 1 scripts.

---

## 8. Phase 7 – Scheduler & Data Refresh

**Goal**: Keep all Groww data fresh and propagate updates through the pipeline.

- **Scheduler engine**:
  - Cron / Windows Task Scheduler, or
  - Orchestration tool (Airflow/Prefect), or
  - A simple long‑running process with timed jobs.

- **Core jobs**:
  - **Fetch & parse (Phase 1 refresh)**:
    - Periodically re‑run Phase 1 over all configured fund/help URLs.
    - Update `data/funds_phase1.json` and database tables.
  - **Reindex (Phase 2 refresh)**:
    - Detect changed texts and re‑chunk/re‑embed them into the vector DB.
  - **Health checks**:
    - Validate that required attributes exist for each tracked fund.
    - Alert/log on parser failures or sudden structural changes.

- **Effect on chatbot**:
  - The chat backend always reads from the **current DB and vector index**, so answers automatically reflect refreshed Groww data without code changes.

---

## 9. Next Steps

- Extend Phase 1 to:
  - Ingest Groww help/FAQ URLs for “how to download statements”.
  - Populate the `statements_info` attribute or a related help article table.
- Implement Phase 2 loaders:
  - Migrate `data/funds_phase1.json` into a relational DB.
  - Set up vector DB and build the initial index.
- Build minimal backend (`/chat`) and a simple web UI to start testing end‑to‑end.

