"""
Phase 4: answer generation & safety.

This phase:
- Takes a user message and uses Phase 3 router to interpret it.
- For attribute queries, looks up structured data from Phase 2 DB.
- Generates concise, factual answers that always include at least one source URL.
- Provides a simple placeholder path for procedural and out_of_scope queries.
"""

