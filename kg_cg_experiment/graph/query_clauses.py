"""
Splits a query into clauses for direct embedding recall.

Root-cause fix for a real failure found in the 50-question reasoning set
(M5): a question bundling an unrelated clause with an evidence-relevant one
("What's the standard change fee for Economy tickets, and by the way, did I
end up getting insurance for my rental car?") diluted the whole-query
embedding enough that a real, stored, directly-relevant trace fell below the
similarity threshold and was missed entirely.

Splitting into clauses and embedding each separately (context_graph.py takes
the max similarity per trace across all clauses) fixes this without loosening
the threshold globally: an irrelevant clause can no longer drag down the
score of a clause that IS relevant on its own. This can only increase recall
relative to whole-query embedding (more candidate embeddings checked per
trace), never decrease it -- the precision cost of that is intentionally
carried by the topic-keyword filter in context_graph.py, not by narrowing
this splitter's aggressiveness.
"""
import re

_SPLIT_PATTERN = re.compile(
    r"(?<=[.?!])\s+"                       # sentence boundaries
    r"|\s*,?\s*\bby the way\b\s*,?\s*"
    r"|\s*,?\s*\bseparately\b\s*,?\s*"
    r"|\s*,?\s*\balso\b\s*,?\s*"
    r"|\s*;\s*",
    re.IGNORECASE,
)

_MAX_CLAUSES = 5


def split_into_clauses(query: str) -> list[str]:
    """Always includes the whole query as one candidate (so a single-clause
    question isn't penalized), plus each split fragment if there's more than
    one. Deduplicated, capped to keep the embed() call count bounded."""
    fragments = [f.strip() for f in _SPLIT_PATTERN.split(query) if f.strip()]

    clauses = [query.strip()]
    if len(fragments) > 1:
        clauses.extend(fragments)

    seen = set()
    unique = []
    for c in clauses:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique[:_MAX_CLAUSES]
