"""
One-time KG extraction for the large-scale unstructured track -- identical
mechanism to graph/extract_kg_from_text.py, pointed at
data/large_unstructured_policy_document.py's POLICY_SECTION_TEXT (NOT the
2000-row catalog appendix -- that section is deliberately never sent to
extraction; see that module's docstring for why).

Run once:  python -m kg_cg_experiment.graph.extract_large_kg_from_text
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kg_cg_experiment.agent.llm_client import OllamaUnavailableError, chat, is_available
from kg_cg_experiment.data.large_unstructured_policy_document import POLICY_SECTION_TEXT

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "large_extracted_kg.json"

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

For edges, use relations: has_return_policy, has_exchange_policy, waives, applies_to, restricts, exempt_from, covers -- connecting nodes exactly as the document describes.

Determine every attribute value and every edge from what the document actually says -- do not assume anything not stated or implied by the text. Ignore any mention of a product catalog or individual products -- those are out of scope for this graph.

DOCUMENT:
{POLICY_SECTION_TEXT}
"""


def _extract_json(text: str) -> str:
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

    print("Calling the LLM once to extract a KG from the large-scale policy section...")
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


if __name__ == "__main__":
    extract()
