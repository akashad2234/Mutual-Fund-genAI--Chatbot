"""
Phase 7: scheduler & data refresh orchestration.

This phase is responsible for:
- Re-running Phase 1 scraping on a schedule.
- Re-running Phase 2 loading and indexing.
- Ensuring the structured JSON and DB stay fresh, including the
  `last_updated` timestamps used by the frontend.
"""

