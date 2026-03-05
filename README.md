## Groww Mutual Fund RAG – Phase 1

This repository implements **Phase 1 (data acquisition & normalization)** for a RAG-based chatbot focused on Groww mutual funds.

### What Phase 1 does

- Fetches official, public fund pages from `https://groww.in/` (currently a fixed list of funds).
- Extracts:
  - **Key attributes**: expense ratio, exit load summary, minimum SIP, lock-in (ELSS), riskometer, benchmark.
  - **Section text snippets** for:
    - Return calculator
    - Holdings
    - Holdings analysis
    - Equity sector allocation
    - Advanced ratios
    - Minimum investments
    - Returns and rankings
    - Exit load, stamp duty and tax
  - Placeholder for **“how to download statements”** (to be wired to help/FAQ URLs later).
- Writes all data into a single JSON file under `data/funds_phase1.json`.

### Tech stack

- Python 3.10+
- `requests`, `beautifulsoup4`, `lxml`

### Setup

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running Phase 1 extraction

From the project root:

```bash
python -m src.phase1.main
```

This will:

- Fetch each configured Groww mutual fund page.
- Parse out key attributes and section text.
- Save results to `data/structured/funds_phase1.json`.

You can then use this JSON as the input for later phases (database loading, vector indexing, RAG, etc.).

