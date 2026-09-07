"""
Maps KG nodes to decision-trace "slots" (entity_key, attribute), and defines
every known slot -- whether or not it has a KG node -- plus a lightweight
topic-keyword guard used as a precision filter on direct embedding recall.

This is what lets Condition B's structural relevance check work: when a
query's KG traversal reaches a node that has a slot mapping (e.g. any
tier:* node), we know "the user's loyalty tier" is a slot worth checking the
persistent trace store for -- even though the query text itself may share no
vocabulary with a stored statement about it (see README.md "Trace matching"
for why raw text similarity alone misses this).

Not every entity a user might state something about has a KG node (e.g.
shipping preference or complaint history isn't modeled in the policy graph
at all) -- those slots are still valid, they just never get picked up by the
KG-structural path, only by direct embedding recall against the stored
statement text.
"""
from kg_cg_experiment.data.policy_dataset import NODES

KG_NODE_TO_SLOT = {
    "tier:bronze": ("loyalty_tier", "tier"),
    "tier:silver": ("loyalty_tier", "tier"),
    "tier:gold": ("loyalty_tier", "tier"),
    "tier:platinum": ("loyalty_tier", "tier"),
    "product_category:electronics": ("product", "category"),
    "product_category:apparel": ("product", "category"),
    "product_category:furniture": ("product", "category"),
    "product_category:groceries": ("product", "category"),
    "product_category:digital_goods": ("product", "category"),
    "product:extended_warranty": ("warranty", "status"),
}

# Every known (entity_key, attribute) slot, whether or not it has a KG node
# -- used to validate that statement extraction only ever produces a slot
# that's actually recognized somewhere in this list. Broadened beyond the
# original 4 (tier, category, warranty, one off-schema example) to 7, so
# CG's demonstrated advantage isn't resting on a handful of fact types:
# shipping preference, complaint history, and payment method are all
# realistic customer-support facts with no KG node at all (same pattern as
# the original car-rental-insurance example -- direct embedding recall is
# the only path that can ever surface them), and prior-exchange-count is a
# KG-adjacent fact (relevant to exchange decisions) that also has no node.
KNOWN_SLOTS = {
    ("loyalty_tier", "tier"),
    ("product", "category"),
    ("warranty", "status"),
    ("shipping", "preference"),
    ("complaint", "history"),
    ("payment", "method"),
    ("exchange", "prior_count"),
}


def _aliases_for_type(node_type: str) -> list[str]:
    return [a for n in NODES if n["type"] == node_type for a in n.get("aliases", [])]


# Lightweight topic-keyword guard for the direct-embedding recall path
# (graph/context_graph.py). Embedding similarity alone can produce a
# high-scoring but topically implausible match (e.g. two sentences about
# "insurance" in different senses); before accepting a direct hit, the slot
# it belongs to must have at least one of its topic keywords actually
# present in the query text. KG-linked slots reuse the same alias lists the
# KG traversal itself uses (so this can't drift out of sync with the
# schema); off-schema slots get an explicit, hand-picked list.
SLOT_TOPIC_KEYWORDS: dict[tuple[str, str], list[str]] = {
    ("loyalty_tier", "tier"): _aliases_for_type("LoyaltyTier") + ["tier", "loyalty", "membership", "status"],
    ("product", "category"): _aliases_for_type("ProductCategory"),
    ("warranty", "status"): _aliases_for_type("WarrantyProduct") + ["warranty"],
    ("shipping", "preference"): ["shipping", "delivery", "ship", "expedited", "standard shipping"],
    ("complaint", "history"): ["complain", "complaint", "escalat", "issue before", "previous problem", "reported"],
    ("payment", "method"): ["paid with", "payment", "gift card", "credit card", "store credit"],
    ("exchange", "prior_count"): ["already exchanged", "exchanged before", "previous exchange", "exchange again"],
}
