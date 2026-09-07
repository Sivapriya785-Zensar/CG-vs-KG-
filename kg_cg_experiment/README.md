# KG vs CG experiment

Compares a static Knowledge Graph (Condition A) against a per-query
constructed Context Graph (Condition B) on the same customer-support agent.
Built with `networkx` (in-memory, no server/credentials) plus a local SQLite
file for persistent decision traces. LLM backend is local Ollama (default
`llama3` for chat, `nomic-embed-text` for embeddings) -- no API keys, no
OpenAI/Neo4j dependency.

**Domain: retail customer support** (return/exchange/warranty policy). This
replaced an earlier airline-policy domain -- same graph shape and mechanics
throughout (product category ~ booking type, return rule ~ cancellation
rule, exchange rule ~ change rule, promo blackout ~ travel blackout,
extended warranty ~ travel insurance), just more immediately legible
content. **`results/` and `results_reasoning/` are historical artifacts from
the old airline schema and were not re-run against retail** -- read them for
their methodology and findings, not their specific facts, which no longer
exist in `data/policy_dataset.py`.

## Layout

- `data/policy_dataset.py` -- the design-time retail policy schema (product
  categories, return/exchange rules, promo blackouts, loyalty tiers,
  extended warranty). See its docstring for the intentional asymmetries
  (Gold vs Platinum, which categories warranty covers, etc.) that make
  reasoning questions non-trivial to guess.
- `data/slot_mapping.py` -- maps KG nodes to decision-trace "slots" (e.g.
  any `tier:*` node -> the `loyalty_tier` slot), used for structural
  relevance; also the topic-keyword guard used by the precision fix below.
  Seven slots total (three KG-linked: tier, category, warranty; four
  off-schema: shipping preference, complaint history, payment method,
  prior-exchange count) -- broadened from the original four so CG's
  demonstrated advantage doesn't rest on only a couple of fact types.
- `data/trace_store.py` -- persistent, user-scoped SQLite store for decision
  traces and the opt-in answer cache. Traces survive across sessions for the
  same `user_id`; never pooled across different users.
- `graph/knowledge_graph.py` -- builds the static KG once.
- `graph/seed_matching.py` -- deterministic query -> seed-node matching and
  hop expansion, shared by both conditions.
- `graph/query_clauses.py` -- splits a query into clauses for direct
  embedding recall (the recall fix below).
- `graph/statement_extraction.py` -- deterministic (regex-based) fail-fast
  extraction of a Statement into decision-trace facts across all seven
  slots. This is the *storing* half.
- `graph/context_graph.py` -- Condition B: KG base + trace-store evidence,
  with the fail-fast/fail-safe fallback contract, plus the two precision/
  recall fixes described below. This is the *matching* half.
- `agent/llm_client.py` -- thin client over Ollama's chat and embeddings
  endpoints; token counts come straight from Ollama's response, never
  estimated.
- `agent/cache.py` -- opt-in answer-cache policy for Condition B.
- `agent/runner.py` -- runs one free-text query against a condition
  (`run_kg`, `run_cg`) or stores a Statement (`run_statement`).
- `agent/decision.py` -- **action-based** decision mode: both conditions
  choose exactly one structured action (`ACTIONS`) instead of free text.
  See "Decision testing" below.
- `server.py` + `static/index.html` -- FastAPI backend + single-file chat UI
  with a Statement/Question mode toggle and Apply-KG/Apply-CG switches.
- `tests/test_queries.py`, `tests/test_queries_reasoning.py` -- the two
  earlier 50-question free-text sets (airline domain, see the note above).
- `tests/test_decisions.py` -- 24 decision scenarios (retail domain): 15
  single-fact, 5 cross-session chaining, 4 memory-interference stress tests.
- `tests/run_decision_tests.py` -- runs the decision scenarios live and
  writes `results_decisions/`, including the fabrication-vs-action analysis.

## Two fixes, found by reading real failures (not speculative hardening)

Both came out of manually grading the 50-question reasoning set (see
`results_reasoning/quality_review.md`, item M5 and the general false-positive
risk noted there) and are applied in `graph/context_graph.py`:

1. **Recall fix -- clause splitting.** Direct embedding recall used to embed
   the whole query as one vector. A question bundling an unrelated clause
   with an evidence-relevant one ("What's the return fee for Apparel, and by
   the way, did I get the extended warranty?") diluted the relevant clause's
   similarity below threshold and missed a trace that was genuinely on
   file. Measured concretely: whole-query similarity 0.54 (below the 0.65
   threshold) vs. the isolated clause alone at 0.68 (above it). Now every
   clause (`graph/query_clauses.py`) is embedded separately and the max
   similarity per trace across clauses is used -- this can only increase
   recall, never decrease it.
2. **Precision fix -- topic-keyword guard.** To keep (1) from also
   increasing false positives, a direct-embedding hit is no longer accepted
   on similarity score alone: its slot's topic keywords
   (`data/slot_mapping.py` `SLOT_TOPIC_KEYWORDS`) must actually appear in
   the query text. KG-linked slots reuse the same alias lists the KG
   traversal itself uses (can't drift out of sync); off-schema slots
   (shipping, complaints, payment, exchange count) get an explicit list.

## Trace matching: why it's two mechanisms, not one

Pure embedding similarity between a stored statement and a new question is
good at paraphrase recall but structurally blind: "I'm a Gold tier member"
and "will my exchange fee be waived?" score only ~0.35, even though the KG
says tier *does* determine that fee -- the connection is graph-structural
(tier -waives-> fee -applies_to-> exchange rule), not textual. `context_graph.py`
therefore combines:

1. **KG-structural relevance** -- the query's own KG traversal reaches a
   node mapped to a known slot -> check the trace store for that slot,
   regardless of text similarity.
2. **Direct embedding recall** (clause-split, topic-filtered as above) --
   the query embedding vs. every stored trace's own statement embedding,
   real cosine similarity (`config.TRACE_SIMILARITY_THRESHOLD`, 0.65 --
   picked after empirically measuring true-paraphrase pairs at 0.79-0.89 and
   unrelated pairs at 0.35-0.48 on this embedding model, not guessed).

A trace only contributes if every candidate for its slot agrees on the
value (fail-fast); a genuine conflict falls the whole answer back to
KG-static rather than guessing (fail-safe).

**User-scoping matters in practice, not just in theory.** An early version
of the trace store pooled every session's traces globally regardless of
`user_id`, which silently broke the first 50-question test suite by letting
unrelated hypothetical customers' conflicting tier claims collide. Fixed by
scoping every trace to `user_id`; see `results/summary.md` for the numbers.

## Decision testing -- the agentic upgrade from Q&A to action

Every free-text test so far graded whether the answer *read* correctly. An
agent's memory only matters if it changes what the agent *does*, not just
what it says -- so `agent/decision.py` constrains both conditions to emit
exactly one action from a fixed set, parsed structurally:

```
approve_refund      grant the request under standard policy (no waiver)
apply_waiver        grant the request AND waive the fee that would apply
deny_request        the request cannot be granted under policy
escalate_to_human   not enough confidence, or the policy doesn't cover this
request_more_info   need one more fact from the customer before deciding
```

`tests/test_decisions.py` has three groups:

- **Single-fact (15)** -- one seeded fact (or none), one decision. Includes
  direct traps mirroring the free-text set's asymmetries as ACTIONS instead
  of prose: DEC11 asks about a waiver Gold doesn't actually have (should
  `approve_refund`, not `apply_waiver`); DEC13 asks about blackout exemption
  Gold doesn't have for that specific blackout (should `deny_request`).
- **Cross-session chaining (5)** -- tier stored in session 1, product
  category stored in session 2, decision asked in session 3. Tests whether
  CG composes two independently-recalled facts into one correct action, not
  just recalls one fact in isolation.
- **Memory interference (4)** -- 10-11 stored facts for one customer, most
  irrelevant or deliberately conflicting in slots that have nothing to do
  with the decision being asked (STRESS1: a shipping-preference conflict and
  a payment-method conflict, buried among the noise, must NOT block a
  decision that only needed the clean tier+category slots; STRESS2 adds a
  *genuinely* relevant tier conflict and checks it's still caught despite
  the volume of other stored facts).

**The centerpiece finding to look for, not a footnote:** across both earlier
50-question free-text runs, the model's most reliable failure mode wasn't
"no evidence, so it declines" -- it was **confidently fabricating a specific
personal fact it was never given, and reasoning fluently from there** (see
`results_reasoning/quality_review.md`, R3 and R8 in particular: CG had the
*correct* facts on the table and still talked itself into a wrong,
self-contradictory conclusion; more context gave the model more surface
area to elaborate, not more caution). `run_decision_tests.py` makes this
concrete instead of anecdotal: `fabrication_analysis.md` flags every KG
response that names a specific tier or category with zero evidence access,
and reports whether that fabrication was harmless (lucky match) or actually
**changed the action taken** -- e.g. approving a waiver that shouldn't have
been granted. That's the real-world risk this pattern represents in any
agentic system: a fabricated intermediate claim silently becoming a wrong
downstream action, not just a wrong sentence.

## Opt-in answer cache (reduces tokens, never used for measurement runs)

`agent/cache.py` lets a real, non-fallback CG answer be reused for a close
paraphrase (`config.CACHE_SIMILARITY_THRESHOLD`, 0.85) *only* when the KG
context and the exact trace values used are byte-identical to what produced
the cached answer. Strictly opt-in (UI switch, `use_cache=False` everywhere
in every `run_*_tests.py` script) -- no graded measurement run uses it, per
the "no token-usage optimization" rule for the actual A/B comparison.

## Requirements

- Ollama running locally with a chat model and an embedding model pulled:
  `ollama pull llama3` and `ollama pull nomic-embed-text`.
- Python deps already in this repo's environment: `fastapi`, `uvicorn`,
  `networkx`, `requests`.

Config is env-driven (see `config.py`): `OLLAMA_URL`, `OLLAMA_MODEL`,
`EMBED_MODEL`, `TRACE_SIMILARITY_THRESHOLD`, `CACHE_SIMILARITY_THRESHOLD`,
`TRACE_DB_PATH`.

## Run the chat UI

```bash
python -m uvicorn kg_cg_experiment.server:app --host 127.0.0.1 --port 8710
```

Then open http://127.0.0.1:8710. Every submit hits the real local model
live; nothing is precomputed.

## Run the decision-scenario suite (24 scenarios, retail domain)

Not run as part of building this -- it costs real Ollama tokens on your
machine. Run it yourself when ready:

```bash
python -m kg_cg_experiment.tests.run_decision_tests
```

Clears the trace store first (reproducible run), then writes under
`kg_cg_experiment/results_decisions/`: `raw_log.md` (every statement, every
KG/CG decision with full reasoning and real token counts),
`decision_table.md` (expected vs. actual action, correctness, fallback,
tokens), and `fabrication_analysis.md` (the centerpiece analysis described
above).

## Run the retail Direct/Reasoning/Mixed suite (50Q, methodology-fixed)

Not run as part of building this -- real Ollama tokens. A fix on the
airline reasoning set's methodology: that set often let a question restate
the personalizing fact directly in its own text ("since I'm Gold tier..."),
which lets KG answer correctly with zero memory -- not a fair test of
whether CG's recall actually helps. Every personalized question in this set
keeps the fact generic ("given my loyalty status") so KG genuinely can't
know it; 49/50 questions are `leak_free=True` for that reason (one,
`R14`, unavoidably references a just-stated recent action and is flagged as
such, not passed off as clean). See `tests/test_queries_retail.py`'s
docstring for the full audit.

```bash
python -m kg_cg_experiment.tests.run_queries_retail_tests
```

Writes `kg_cg_experiment/results_retail/raw_log.md` and `index.md` (token
counts, fallback flags, per-question `leak_free` status). No auto-grading --
read the transcript and grade by hand, same discipline as
`results_reasoning/quality_review.md`.

## Run the unstructured-data-source track (same 50Q, different knowledge source)

A second, independent comparison: instead of KG/CG both drawing on the
hand-authored graph (`data/policy_dataset.py`), this track sources
everything from `data/unstructured_policy_document.py` -- a prose policy
document, the way a real internal wiki page reads, not a clean
fact-per-line list. Same 50 questions (`test_queries_retail.py`, unchanged),
same trace-store evidence mechanism for personalization; only the base
knowledge source and how each condition gets it from that source differ:

- **KG-unstructured** (`graph/knowledge_graph_unstructured.py`): a
  **one-time** LLM extraction pass (`graph/extract_kg_from_text.py`) turns
  the prose into a graph once, cached to `data/extracted_kg.json`, then
  traversed exactly like the hand-authored KG forever after -- static,
  never touches the source text again. If the extraction missed or
  flattened a nuance, KG has no way to recover it, ever.
- **CG-unstructured** (`graph/context_extraction.py`): gets the same
  extracted-graph evidence CG normally gets, **plus** a live retrieval pass
  straight from the original prose on every query (real embeddings,
  paragraph-level chunks, cosine similarity -- see the module docstring for
  why `top_k=3` and the threshold were picked empirically, not guessed).
  This is the asymmetry actually being tested: does having another live
  shot at the real source text -- not just the one-time extraction -- catch
  something the extraction lost?

Run the one-time extraction first (single LLM call, ~a few seconds), then
the comparison itself:

```bash
python -m kg_cg_experiment.graph.extract_kg_from_text
python -m kg_cg_experiment.tests.run_queries_unstructured_source_tests
```

Writes `kg_cg_experiment/results_retail_unstructured/raw_log.md` and
`index.md`, including which document chunks CG's context-extraction layer
actually retrieved (with similarity scores) for every question. Compare
directly against `results_retail/` -- same 50 questions, same grading
discipline, different knowledge source.

## Run the older free-text suites (airline domain, historical)

```bash
python -m kg_cg_experiment.tests.run_tests              # 50Q, KG/CG isolation + fallback
python -m kg_cg_experiment.tests.run_reasoning_tests     # 50Q, Direct/Reasoning/Mixed quality
```

These reference the pre-retail schema and are kept for their methodology,
not as something to re-run expecting current facts.
