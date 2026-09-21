# CG HP — CG-only large-scale hyperparameter test

Large-scale (2000-product catalog, 500-question) extension of the original
50-question KG vs CG experiment, run CG-only against a real-retail-scale
unstructured document (`kg_cg_experiment/`'s existing 8-paragraph document,
scaled up).

## Contents

- `data/large_product_catalog.py` — generates 2000 SKUs (400 per category
  across Electronics, Apparel, Furniture, Groceries, Digital Goods),
  deterministic (`random.seed(42)`), each with a brand/model name and a
  realistic one-line description.
- `data/large_unstructured_policy_document.py` — the source document, split
  into `POLICY_SECTION_TEXT` (607 words, the actual return/exchange/loyalty/
  blackout/warranty rules — the only part sent to KG extraction) and
  `CATALOG_SECTION_TEXT` (2000 products chunked into 251 paragraphs,
  chunk-retrieval-only).
- `data/large_extracted_kg.json` — one-time LLM-extracted KG from
  `POLICY_SECTION_TEXT` (22 nodes, 17 edges).
- `graph/extract_large_kg_from_text.py` — the extraction script that produced
  the JSON above.
- `tests/test_queries_large.py` — 500 programmatically-generated questions
  (170 direct, 170 reasoning, 160 mixed), every `expected_answer` computed
  from a small `CATEGORY_RULES` dict, never hand-typed.
- `tests/run_large_cg_only_test.py` — the CG-only runner (KG calls never
  made). Configurable via `LARGE_CHUNK_THRESHOLD` / `LARGE_CHUNK_TOP_K` /
  `OLLAMA_TEMPERATURE`.
- `tests/grade_large_run.py` — automated fact-level grading against the
  computed expected answers (dollar amounts / yes-no matching).
- `results_large/` — output of the one run executed so far:
  `chunk_threshold=0.45, temperature=0.4`.

## Result of this run: chunk=0.45, temp=0.4 (500/500 questions)

Automated grading: **4.4% PASS** (8.1% excluding UNCLEAR).

**This number is not a meaningful measurement of CG's retrieval quality** —
it reflects two structural bugs in this test's design, not the
threshold/temperature setting:

1. **Graph traversal never fires for most questions.** The KG-traversal step
   matches query text against node labels/aliases in the extracted policy
   graph. These 500 questions reference products by name only
   ("Kestrel TV 100"), never by category ("Electronics") — so for most
   questions the traversal subgraph comes back empty and the model gets zero
   policy facts from the graph.
2. **Chunk retrieval can't compensate.** `run_large_cg_only_test.py` builds
   its chunk-retrieval pool from `CATALOG_SECTION_TEXT` only, not
   `FULL_DOCUMENT_TEXT` — so the policy prose paragraphs (which do contain
   the actual fee/window/waiver facts) are never in the searchable pool
   either. Chunk retrieval only ever returns catalog rows (price/description),
   which don't carry policy facts.

Net effect: for a large majority of these questions, the policy facts needed
to answer correctly are structurally unreachable by either of CG's two
retrieval paths, independent of what chunk-similarity threshold or
temperature is set. Fixing this requires either (a) bridging product → 
category in the traversal step (e.g. seed the traversal with the category
tag found in a retrieved catalog chunk), and/or (b) including
`FULL_DOCUMENT_TEXT` (policy + catalog) in the chunk-retrieval pool instead
of the catalog section alone. Neither fix has been applied or re-tested yet.
