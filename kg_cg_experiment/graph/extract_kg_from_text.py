"""
Builds the "unstructured data source" KG: a ONE-TIME LLM extraction pass
over data/unstructured_policy_document.py's prose, producing the same
node/edge shape as data/policy_dataset.py, saved to data/extracted_kg.json.

This is the "necessary steps for KG" a design-time-only structured graph
requires when its knowledge doesn't start out structured: a real KG-from-docs
pipeline needs an extraction step somewhere, and this is a real (if simple)
one -- one live LLM call, not a per-query call, not hand-typed by us. Once
extracted, the result is cached to disk and treated exactly like the
hand-authored graph from then on: static, traversed as-is, never touched at
query time. This mirrors how build_static_kg() works -- built once, reused
forever -- except the "once" here is an LLM call instead of a Python literal.

Node `type` strings are pinned to the exact vocabulary
graph/context_graph.py's structural-relevance logic checks for
(ProductCategory, ReturnRule, ExchangeRule, LoyaltyTier, PromoBlackout, Fee,
WarrantyProduct) -- get those wrong and CG's structural path silently stops
working for the extracted graph, so the prompt is explicit about them, the
same way you'd document an ontology for a real extraction pipeline. Node IDs
are similarly pinned to policy_dataset.py's exact naming convention (e.g.
"tier:gold") so that decision-trace evidence (extracted from user statements
against the SAME id scheme, see graph/statement_extraction.py) can still
link into this graph's nodes -- entity-resolution/canonicalization is a
normal, honest part of building a KG from text, not a shortcut around the
extraction itself. Everything else (attrs, aliases, edges -- the actual
facts) is for the model to determine from the document, not hardcoded here.

Run once:  python -m kg_cg_experiment.graph.extract_kg_from_text
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kg_cg_experiment.agent.llm_client import OllamaUnavailableError, chat, is_available
from kg_cg_experiment.data.unstructured_policy_document import POLICY_DOCUMENT_TEXT

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "extracted_kg.json"

EXTRACTION_PROMPT = f"""You are extracting a structured knowledge graph from a retail policy document.

Read the document below and output ONLY a JSON object (no other text, no markdown fences) with this exact shape:

{{
  "nodes": [
    {{"id": "<id>", "type": "<type>", "label": "<display name>", "aliases": ["<lowercase phrase>", ...], "attrs": {{...}}}}
  ],
  "edges": [
    {{"source": "<node id>", "target": "<node id>", "relation": "<relation>"}}
  ]
}}

Use ONLY these node types, exactly spelled: ProductCategory, ReturnRule, ExchangeRule, LoyaltyTier, PromoBlackout, Fee, WarrantyProduct.

Use ONLY these node ids (one node per id, do not invent others):
product_category:electronics, product_category:apparel, product_category:furniture, product_category:groceries, product_category:digital_goods,
rule:return_electronics, rule:return_apparel, rule:return_furniture, rule:return_groceries, rule:return_digital_goods,
rule:exchange_standard, rule:exchange_free, rule:exchange_none,
tier:bronze, tier:silver, tier:gold, tier:platinum,
blackout:holiday_sale, blackout:clearance_event,
fee:exchange_fee_waiver, fee:restocking_fee_waiver,
product:extended_warranty

For each ReturnRule node, include attrs: refundable (true/false), fee_usd (number or null), and window_days if stated.
For each ExchangeRule node, include attrs: allowed (true/false), fee_usd (number or null).
For each PromoBlackout node, include attrs: dates (string).
For the WarrantyProduct node, include attrs: cost_usd (number) and covers (string).
For each node, include a realistic `aliases` list: lowercase phrases a customer might actually use to refer to it, based on how the document itself phrases things.

For edges, use relations: has_return_policy, has_exchange_policy, waives, applies_to, restricts, exempt_from, covers -- connecting nodes exactly as the document describes (e.g. which tier waives which fee, which fee applies to which rule, which blackout restricts which category, which tier is exempt from which blackout, what the warranty covers).

Determine every attribute value and every edge from what the document actually says -- do not assume anything not stated or implied by the text.

DOCUMENT:
{POLICY_DOCUMENT_TEXT}
"""


def _extract_json(text: str) -> str:
    """Models routinely ignore "output ONLY JSON" and add a preamble or
    trailing note anyway -- rather than depend on perfect compliance, pull
    the JSON out of whatever surrounds it: prefer a fenced ```json block if
    present anywhere in the text, otherwise fall back to the span from the
    first '{' to the last '}'."""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


def extract():
    if not is_available():
        print("ERROR: Ollama is not reachable. Nothing extracted.")
        sys.exit(1)

    print("Calling the LLM once to extract a KG from the unstructured policy document...")
    try:
        result = chat([{"role": "user", "content": EXTRACTION_PROMPT}])
    except OllamaUnavailableError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    raw = _extract_json(result["text"])
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        print("ERROR: model output wasn't valid JSON. Raw output below -- fix the prompt or retry.\n")
        print(raw)
        print(f"\nJSON error: {e}")
        sys.exit(1)

    if "nodes" not in parsed or "edges" not in parsed:
        print("ERROR: extracted JSON is missing 'nodes' or 'edges'. Raw output:\n")
        print(json.dumps(parsed, indent=2))
        sys.exit(1)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(parsed, indent=2), encoding="utf-8")

    print(f"\nExtracted {len(parsed['nodes'])} nodes, {len(parsed['edges'])} edges "
          f"({result['prompt_tokens']}+{result['completion_tokens']}={result['total_tokens']} tokens).")
    print(f"Wrote {OUT_PATH}")
    print("\nSpot-check this file before trusting it -- extraction can miss or misread a fact, "
          "same risk any real KG-from-docs pipeline has.")


if __name__ == "__main__":
    extract()
