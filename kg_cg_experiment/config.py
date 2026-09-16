"""Config for the KG vs CG experiment. Everything read from env vars, nothing hardcoded."""
import os
from pathlib import Path

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:8b")
OLLAMA_TIMEOUT_S = int(os.environ.get("OLLAMA_TIMEOUT_S", "120"))

# Local embedding model for genuine similarity-based trace matching (not a
# keyword list). Already pulled locally: `ollama pull nomic-embed-text`.
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")

# Cosine-similarity threshold for direct question<->stored-statement recall.
# Empirically measured on this embedding model before picking this number
# (see kg_cg_experiment/README.md "Trace matching" section): true paraphrase
# pairs scored 0.79-0.89, unrelated pairs scored 0.35-0.48. 0.65 sits in the
# gap between them with margin on both sides.
TRACE_SIMILARITY_THRESHOLD = float(os.environ.get("TRACE_SIMILARITY_THRESHOLD", "0.65"))

# Separate (higher, stricter) threshold for the opt-in answer-cache reuse
# feature -- reusing a cached answer is a stronger claim than "this trace is
# relevant," so it requires a tighter paraphrase match.
CACHE_SIMILARITY_THRESHOLD = float(os.environ.get("CACHE_SIMILARITY_THRESHOLD", "0.85"))

# Cosine-similarity threshold for the unstructured track's live document-chunk
# retrieval (graph/context_extraction.py). Looser than TRACE_SIMILARITY_THRESHOLD
# because a multi-sentence paragraph dilutes similarity compared to a single
# declarative statement: relevant chunks measured 0.53-0.74, irrelevant ones
# 0.33-0.37 on this embedding model.
CHUNK_SIMILARITY_THRESHOLD = float(os.environ.get("CHUNK_SIMILARITY_THRESHOLD", "0.45"))

TRACE_DB_PATH = os.environ.get(
    "TRACE_DB_PATH",
    str(Path(__file__).resolve().parent / "data" / "traces.db"),
)

# Deterministic generation: temperature 0 to minimize LLM-stochasticity noise
# in a measurement experiment (not a tuning exercise).
OLLAMA_OPTIONS = {"temperature": float(os.environ.get("OLLAMA_TEMPERATURE", "0")), "seed": 42}

# Recent conversation turns included as literal evidence for Condition B (CG).
CG_RECENT_TURNS_WINDOW = int(os.environ.get("CG_RECENT_TURNS_WINDOW", "8"))

# Hop radius for KG/CG graph traversal from matched seed nodes. 2 hops is
# needed to reach e.g. BookingType -> ChangeRule -> Fee -> LoyaltyTier.
GRAPH_TRAVERSAL_HOPS = int(os.environ.get("GRAPH_TRAVERSAL_HOPS", "2"))
