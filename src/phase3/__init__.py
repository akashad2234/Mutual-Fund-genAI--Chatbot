"""
Phase 3: query understanding and routing (Groq LLM + rules).

This phase:
- Interprets user queries.
- Classifies them into attribute / procedural / out_of_scope.
- Resolves fund references and attributes.
- Optionally calls Groq LLM to refine classification when a Groq API key is configured.
"""

