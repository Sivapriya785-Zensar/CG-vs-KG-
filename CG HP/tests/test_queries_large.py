"""
500 questions for the large-scale (2000-product) unstructured track.
Same Direct/Reasoning/Mixed structure and anti-fabrication discipline as
tests/test_queries_retail.py: every expected_answer is computed directly
from the category-level policy rules (never guessed), and every question
references a real, named product from the large catalog so answering it
correctly requires actually finding that product's department.

Personalizing facts (loyalty tier, warranty status) are seeded the same way
as the original 50-question set -- via seed_statements, kept out of the
question text itself, so a memory-less baseline can't cheat.

Generated programmatically (not hand-written per item) given the volume,
but every expected_answer traces to the exact same category rules used
throughout this project -- nothing here is invented or approximate.
"""
import random

from kg_cg_experiment.data.large_unstructured_policy_document import CATALOG_BY_SKU

random.seed(7)

CATEGORY_RULES = {
    "Electronics": {"return_fee": 15, "return_window": 30, "exchange_fee": 10,
                     "exchange_allowed": True, "warranty_eligible": True,
                     "blackout": "Holiday Sale Blackout (Nov 25 - Dec 5)"},
    "Apparel": {"return_fee": 0, "return_window": 45, "exchange_fee": 0,
                "exchange_allowed": True, "warranty_eligible": False,
                "blackout": "Clearance Event Blackout (Jan 2 - Jan 15)"},
    "Furniture": {"return_fee": 50, "return_window": 14, "exchange_fee": 10,
                  "exchange_allowed": True, "warranty_eligible": True,
                  "blackout": None},
    "Groceries": {"return_fee": None, "return_window": None, "exchange_fee": None,
                  "exchange_allowed": False, "warranty_eligible": False,
                  "blackout": None},
    "Digital Goods": {"return_fee": None, "return_window": None, "exchange_fee": None,
                       "exchange_allowed": False, "warranty_eligible": False,
                       "blackout": None},
}

_all_skus = list(CATALOG_BY_SKU.keys())


def _pick_sku(category: str, offset: int) -> dict:
    """Deterministic pick of one product from the given category, spread
    across the catalog rather than always the first entry."""
    cat_skus = [s for s in _all_skus if CATALOG_BY_SKU[s]["category"] == category]
    return CATALOG_BY_SKU[cat_skus[offset % len(cat_skus)]]


CATEGORIES = list(CATEGORY_RULES.keys())


def _build_direct(n: int) -> list[dict]:
    items = []
    for i in range(n):
        category = CATEGORIES[i % len(CATEGORIES)]
        rule = CATEGORY_RULES[category]
        product = _pick_sku(category, i // len(CATEGORIES))
        qid = f"D{i+1}"

        variant = i % 4
        if variant == 0:
            q = f"I bought a {product['name']}, can I return it, and if so what's the fee?"
            if rule["return_fee"] is None:
                exp = f"No -- {category} items are non-returnable, no exceptions."
            else:
                exp = f"Yes -- ${rule['return_fee']} fee, {rule['return_window']}-day window."
            why = f"{product['sku_id']} is {category}; rule:return_{category.lower().replace(' ', '_')}"
        elif variant == 1:
            q = f"Can I exchange my {product['name']} for a different one, and what would it cost?"
            if not rule["exchange_allowed"]:
                exp = f"No -- exchanges aren't allowed for {category} at all."
            else:
                exp = f"Yes -- ${rule['exchange_fee']} fee." if rule["exchange_fee"] else "Yes -- no fee."
            why = f"{product['sku_id']} is {category}; exchange policy for that department"
        elif variant == 2:
            q = f"Does the extended warranty cover my {product['name']} if it's defective?"
            exp = ("Yes -- warranty covers defect/damage claims for this department."
                   if rule["warranty_eligible"] else
                   f"No -- warranty doesn't cover {category}.")
            why = f"{product['sku_id']} is {category}; warranty covers only Electronics/Furniture"
        else:
            q = f"What department is the {product['name']} in, and what's its return window?"
            exp = (f"{category}; {rule['return_window']}-day window."
                   if rule["return_window"] else f"{category}; not returnable, no window applies.")
            why = f"{product['sku_id']} catalog entry -> {category} department"

        items.append({"id": qid, "category": "direct", "leak_free": True, "seed_statements": [],
                      "query": q, "expected_answer": exp, "why": why})
    return items


def _build_reasoning(n: int) -> list[dict]:
    items = []
    tiers = ["Gold", "Platinum", "Bronze"]
    for i in range(n):
        category = CATEGORIES[i % len(CATEGORIES)] if i % 3 != 0 else "Electronics"
        rule = CATEGORY_RULES[category]
        product = _pick_sku(category, i // len(CATEGORIES) + 50)
        tier = tiers[i % len(tiers)]
        qid = f"R{i+1}"

        variant = i % 3
        if variant == 0:
            q = (f"I have a {product['name']} I want to return, but I'm not sure my loyalty tier "
                 f"gets me a fee break. Would my restocking fee be waived?")
            if category in ("Groceries", "Digital Goods"):
                exp = f"No -- {category} is non-returnable regardless of tier; the question doesn't apply."
            elif tier == "Platinum":
                exp = f"Yes -- Platinum waives the ${rule['return_fee']} restocking fee for {category}."
            elif tier == "Gold":
                exp = f"No -- Gold only waives the exchange fee, not restocking. You'd still pay ${rule['return_fee']}."
            else:
                exp = f"No -- Bronze has no waivers; you'd pay the full ${rule['return_fee']}."
            why = f"{product['sku_id']} is {category}; tier:{tier.lower()} waiver rules"
            seed = [f"I am a {tier} tier member."]
        elif variant == 1:
            q = (f"If I bought my {product['name']} during a blackout period, would my loyalty status "
                 f"get me around that restriction?")
            if rule["blackout"] is None:
                exp = f"There's no blackout window for {category}, so this doesn't apply."
            elif "Holiday" in rule["blackout"]:
                exp = ("Yes -- Gold and Platinum are both exempt from the Holiday Sale Blackout."
                       if tier in ("Gold", "Platinum") else
                       "No -- only Gold and Platinum are exempt; Bronze is not.")
            else:
                exp = ("Yes -- Platinum is exempt from the Clearance Event Blackout."
                       if tier == "Platinum" else
                       "No -- only Platinum is exempt from the Clearance Event Blackout; Gold does not help here.")
            why = f"{product['sku_id']} is {category}; blackout exemption depends on tier"
            seed = [f"I am a {tier} tier member."]
        else:
            q = (f"I already declined the extended warranty on my {product['name']}. If it breaks, "
                 f"what would I actually pay to return it?")
            if not rule["warranty_eligible"]:
                exp = f"Warranty wasn't relevant anyway -- {category} isn't warranty-eligible."
            elif rule["return_fee"] is None:
                exp = f"{category} isn't returnable regardless of warranty status."
            else:
                exp = f"Since you declined coverage, the full ${rule['return_fee']} restocking fee applies."
            why = f"{product['sku_id']} is {category}; warranty.status=declined trace"
            seed = ["I already declined the extended warranty."]

        items.append({"id": qid, "category": "reasoning", "leak_free": True, "seed_statements": seed,
                      "query": q, "expected_answer": exp, "why": why})
    return items


def _build_mixed(n: int) -> list[dict]:
    items = []
    tiers = ["Gold", "Platinum", "Bronze"]
    for i in range(n):
        cat_a = CATEGORIES[i % len(CATEGORIES)]
        cat_b = CATEGORIES[(i + 2) % len(CATEGORIES)]
        rule_a = CATEGORY_RULES[cat_a]
        rule_b = CATEGORY_RULES[cat_b]
        product_a = _pick_sku(cat_a, i // len(CATEGORIES) + 100)
        product_b = _pick_sku(cat_b, i // len(CATEGORIES) + 150)
        tier = tiers[i % len(tiers)]
        qid = f"M{i+1}"

        q = (f"Two things -- what's the return fee on my {product_a['name']}, and separately, "
             f"is my {product_b['name']} even eligible for exchange?")
        part_a = (f"${rule_a['return_fee']} fee for {cat_a}." if rule_a["return_fee"] is not None
                  else f"{cat_a} isn't returnable at all.")
        part_b = (f"Yes, {cat_b} exchanges are allowed." if rule_b["exchange_allowed"]
                  else f"No, {cat_b} exchanges aren't allowed at all.")
        exp = f"{part_a} {part_b}"
        why = f"{product_a['sku_id']}={cat_a}, {product_b['sku_id']}={cat_b}, independent department rules"

        items.append({"id": qid, "category": "mixed", "leak_free": True, "seed_statements": [],
                      "query": q, "expected_answer": exp, "why": why})
    return items


DIRECT = _build_direct(170)
REASONING = _build_reasoning(170)
MIXED = _build_mixed(160)

ALL_LARGE_QUERIES = DIRECT + REASONING + MIXED
LEAK_FREE_COUNT = sum(1 for q in ALL_LARGE_QUERIES if q["leak_free"])

if __name__ == "__main__":
    print(f"{len(ALL_LARGE_QUERIES)} questions: {len(DIRECT)} direct, "
          f"{len(REASONING)} reasoning, {len(MIXED)} mixed")
    for item in ALL_LARGE_QUERIES[:3] + ALL_LARGE_QUERIES[170:173] + ALL_LARGE_QUERIES[340:343]:
        print(f"\n{item['id']}: {item['query']}\n  -> {item['expected_answer']}")
