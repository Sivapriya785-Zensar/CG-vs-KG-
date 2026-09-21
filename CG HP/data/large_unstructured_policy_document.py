"""
Large-scale unstructured retail source, built on the same 5 policy
categories as data/unstructured_policy_document.py -- no new policy facts,
just real retail scale added on top.

Two parts, deliberately kept separate:

1. POLICY_SECTION_TEXT -- the same return/exchange/loyalty/blackout/warranty
   rules as the original prose document, reworded independently. Small
   enough to fit in one KG-extraction LLM call (same one-time-extraction
   mechanism as graph/extract_kg_from_text.py, just pointed at this text).

2. CATALOG_SECTION_TEXT -- ~2000 named, described products
   (data/large_product_catalog.py), chunked into paragraphs. This is the
   part that gives CG's live chunk-retrieval a realistic large corpus to
   search -- KG's one-time extraction never sees this section at all,
   since a single LLM call can't reliably digest ~2000 catalog rows. That
   asymmetry is deliberate: it's the same "KG is limited to what a one-time
   pass can capture, CG can still search everything live" mechanism the
   original unstructured track tests, just stress-tested at real scale.

FULL_DOCUMENT_TEXT = both sections concatenated -- this is what CG's
chunk-retrieval searches over. Only POLICY_SECTION_TEXT is ever sent to the
KG extraction step.
"""
from kg_cg_experiment.data.large_product_catalog import generate_catalog

POLICY_SECTION_TEXT = """Return & Exchange Policy Overview

This page is maintained by the Customer Experience team and is the single source of truth for how we handle returns, exchanges, loyalty benefits, seasonal blackout windows, and the extended warranty program across our full catalog. Please read the whole page before answering a customer -- a lot of the nuance lives in the exceptions, not the headline numbers.

Section 1: Returns by category

Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to cover the cost of quality-checking returned devices before they go back on the shelf (or get refurbished, if they don't pass inspection).

Furniture works a little differently. You've got a shorter window here, just 14 days, and the restocking fee is steeper at $50 given the shipping and freight costs involved in moving large items back through the warehouse.

Apparel is the most forgiving category by a wide margin. You get a generous 45 days to send things back, and there's no fee at all for returns.

Groceries and Digital Goods are both non-returnable, full stop, no exceptions. Groceries can't come back due to spoilage and food-safety risk. Digital Goods can't be returned once downloaded or activated, and the same reasoning applies to exchanges too, so neither category supports exchanges at all either.

Section 2: Exchanges by category

If a customer would rather swap an Electronics item for something else instead of getting a refund, that's allowed -- the standard exchange fee is $10. Furniture exchanges follow that exact same Standard Exchange Rule as Electronics, so that's also a $10 fee, even though Furniture's return fee ($50) is much higher than Electronics' return fee ($15).

Apparel exchanges are free -- we call this the Free Exchange Rule internally.

As covered above, Groceries and Digital Goods support neither returns nor exchanges.

Section 3: Loyalty tiers and fee waivers

We've got four loyalty tiers: Bronze, Silver, Gold, and Platinum, in ascending order of benefits. Bronze and Silver come with no fee waivers at all.

Gold members get their exchange fee waived on Electronics and Furniture. Gold does NOT extend to the restocking fee -- a Gold member returning an Electronics or Furniture item still pays the full restocking fee.

Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver too, so Platinum is the full package on both Electronics and Furniture.

Section 4: Seasonal blackout windows

The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purchases made during that stretch are final sale for most customers. Gold and Platinum members are exempt from this one.

The Clearance Event Blackout runs January 2nd to January 15th and restricts Apparel returns during that window. Only Platinum members are exempt from this one -- Gold does not help here.

Section 5: Extended Warranty

Customers can add the Extended Warranty for $25 at checkout, as a one-time add-on tied to the order. It covers defect and damage claims beyond what the manufacturer's own warranty covers. Coverage is limited to Electronics and Furniture purchases only -- it does not apply to Apparel, Groceries, or Digital Goods.

Section 6: Catalog scope

Our full catalog spans five departments -- Electronics, Apparel, Furniture, Groceries, and Digital Goods -- with thousands of individual products across each. Every product's return, exchange, warranty, and loyalty treatment is governed entirely by which of these five departments it belongs to; there are no per-product exceptions to the rules above. The department listing for every current product is maintained in our product catalog system, a section of which follows this policy overview for reference."""


def _chunk_catalog_text(rows: list[dict], per_paragraph: int = 8) -> str:
    """Groups catalog rows into paragraphs of `per_paragraph` product
    descriptions each -- keeps individual chunks a manageable, realistic
    size for retrieval (similar in scale to the policy section's own
    paragraphs) rather than one line per chunk or the whole catalog as one
    giant chunk."""
    paragraphs = []
    for i in range(0, len(rows), per_paragraph):
        group = rows[i:i + per_paragraph]
        header = f"Catalog entries {group[0]['sku_id']}-{group[-1]['sku_id']} ({group[0]['category']}):"
        lines = [header] + [f"- {r['description']}" for r in group]
        paragraphs.append("\n".join(lines))
    return "\n\n".join(paragraphs)


_CATALOG_ROWS = generate_catalog(2000)
CATALOG_SECTION_TEXT = (
    "Product Catalog (reference listing -- department determines policy, "
    "individual products carry no separate rules)\n\n"
    + _chunk_catalog_text(_CATALOG_ROWS)
)

FULL_DOCUMENT_TEXT = POLICY_SECTION_TEXT + "\n\n" + CATALOG_SECTION_TEXT

# Convenience export for the question generator: sku_id -> row
CATALOG_BY_SKU = {r["sku_id"]: r for r in _CATALOG_ROWS}


if __name__ == "__main__":
    print(f"Policy section: {len(POLICY_SECTION_TEXT.split())} words")
    print(f"Catalog section: {len(CATALOG_SECTION_TEXT.split())} words, "
          f"{len(_CATALOG_ROWS)} products, "
          f"{len(CATALOG_SECTION_TEXT.split(chr(10)+chr(10)))} paragraphs")
    print(f"Full document: {len(FULL_DOCUMENT_TEXT.split())} words")
