"""
Turns a user-declared Statement (see server.py POST /api/statement) into zero
or more decision-trace facts to store persistently.

This is the "storing" half of the trace system and stays deterministic
regex, same fail-fast philosophy throughout: a rule only fires on an
unambiguous pattern, and if a single statement expresses two contradictory
things for the same slot, nothing is stored for that slot -- callers must
report that plainly rather than pick one arbitrarily.

The "matching" half -- finding which *already-stored* traces are relevant to
a brand new question, including ones from other sessions -- is a different
problem (paraphrase recall) and is handled with real embeddings in
graph/context_graph.py, not here.

Seven slots total (data/slot_mapping.py), three KG-linked (loyalty tier,
product category, warranty status) and four off-schema (shipping
preference, complaint history, payment method, prior-exchange count) --
the off-schema ones exist specifically so CG's advantage isn't demonstrated
on only a couple of fact types.
"""
import re
from dataclasses import dataclass

from kg_cg_experiment.data.policy_dataset import NODES

_TIER_NODES = [n for n in NODES if n["type"] == "LoyaltyTier"]
_CATEGORY_NODES = [n for n in NODES if n["type"] == "ProductCategory"]

_SELF_REF = (
    r"(?:i'?m|i am|i've|i have|i bought|i purchased|i ordered|it'?s|this is|"
    r"my order is|my item is|just upgraded to|confirmed i'?m|checked,?\s*i'?m|checked,?\s*i am)"
)

_DECLINE_WORDS = (
    r"(?:don'?t want|not interested|no thanks?|not buying|decided not to buy|"
    r"declin(?:ed|e)|won'?t (?:be )?(?:buying|getting)|already told you.{0,20}no|"
    r"do not want|didn'?t (?:buy|get|purchase|add))"
)
_ACCEPT_WORDS = (
    r"(?:bought|purchased|opted for|decided to buy|decided to get|added|"
    r"already (?:have|bought|purchased|got|added)|i got)"
)


@dataclass
class ExtractedStatement:
    entity_key: str
    attribute: str
    value: str
    kg_node_id: str | None


def _leftmost_longest_self_ref_match(text: str, candidate_nodes: list[dict]) -> dict[str, None]:
    """Resolves "I bought Electronics" to product_category:electronics only,
    disambiguating overlapping aliases by taking the longest match starting
    earliest, same approach as the KG's own seed matching."""
    occurrences = []
    for node in candidate_nodes:
        for alias in node["aliases"]:
            pattern = rf"{_SELF_REF}\b[^.]{{0,25}}\b{re.escape(alias)}\b"
            for m in re.finditer(pattern, text):
                alias_start = m.end() - len(alias)
                occurrences.append((alias_start, m.end(), node["id"]))

    occurrences.sort(key=lambda o: (o[0], -(o[1] - o[0])))
    next_free = 0
    winners = {}
    for start, end, node_id in occurrences:
        if start < next_free:
            continue
        next_free = end
        winners[node_id] = None
    return winners


def _extract_tier(text: str) -> ExtractedStatement | None:
    hits = _leftmost_longest_self_ref_match(text, _TIER_NODES)
    if len(hits) != 1:
        return None  # none, or internally contradictory -- fail-fast either way
    (node_id,) = hits.keys()
    node = next(n for n in _TIER_NODES if n["id"] == node_id)
    return ExtractedStatement("loyalty_tier", "tier", node["label"], node_id)


def _extract_product_category(text: str) -> ExtractedStatement | None:
    hits = _leftmost_longest_self_ref_match(text, _CATEGORY_NODES)
    if len(hits) != 1:
        return None
    (node_id,) = hits.keys()
    node = next(n for n in _CATEGORY_NODES if n["id"] == node_id)
    return ExtractedStatement("product", "category", node["label"], node_id)


def _extract_warranty(text: str) -> ExtractedStatement | None:
    decline = re.search(rf"\b{_DECLINE_WORDS}\b[^.]{{0,40}}\bwarranty\b", text) or \
        re.search(rf"\bwarranty\b[^.]{{0,40}}\b{_DECLINE_WORDS}\b", text)
    accept = re.search(rf"\b{_ACCEPT_WORDS}\b[^.]{{0,40}}\bwarranty\b", text) or \
        re.search(rf"\bwarranty\b[^.]{{0,40}}\b{_ACCEPT_WORDS}\b", text)
    if decline and accept:
        return None  # contradictory within one statement -- fail-fast
    if decline:
        return ExtractedStatement("warranty", "status", "declined", "product:extended_warranty")
    if accept:
        return ExtractedStatement("warranty", "status", "purchased", "product:extended_warranty")
    return None


_SHIPPING_PATTERN = re.compile(
    r"\b(expedited|overnight|express|standard|two[- ]day|next[- ]day)\b[^.]{0,25}\b(shipping|delivery)\b"
    r"|\b(shipping|delivery)\b[^.]{0,25}\b(expedited|overnight|express|standard|two[- ]day|next[- ]day)\b"
)


def _extract_shipping_preference(text: str) -> ExtractedStatement | None:
    m = _SHIPPING_PATTERN.search(text)
    if not m:
        return None
    value = next(g for g in m.groups() if g and g not in ("shipping", "delivery"))
    return ExtractedStatement("shipping", "preference", value.replace(" ", "-"), None)


_COMPLAINT_PATTERN = re.compile(
    r"\b(already (?:complained|filed a complaint|reported|escalated)|"
    r"complained (?:before|last|previously)|filed a complaint (?:before|previously)|"
    r"had (?:an? )?issue (?:before|previously|last time))\b"
)


def _extract_complaint_history(text: str) -> ExtractedStatement | None:
    if not _COMPLAINT_PATTERN.search(text):
        return None
    return ExtractedStatement("complaint", "history", "prior_complaint_on_record", None)


_PAYMENT_PATTERN = re.compile(
    r"\bpaid (?:with|using|via)\s+(?:a |an |my )?(gift card|credit card|debit card|store credit|paypal)\b"
)


def _extract_payment_method(text: str) -> ExtractedStatement | None:
    m = _PAYMENT_PATTERN.search(text)
    if not m:
        return None
    return ExtractedStatement("payment", "method", m.group(1).replace(" ", "_"), None)


_EXCHANGE_COUNT_PATTERN = re.compile(
    r"\b(already exchanged (?:this|it|the item)(?: once)?|"
    r"exchanged (?:this|it) (?:before|already|once)|"
    r"this is my (?:second|2nd) exchange|already used my exchange)\b"
)


def _extract_prior_exchange(text: str) -> ExtractedStatement | None:
    if not _EXCHANGE_COUNT_PATTERN.search(text):
        return None
    return ExtractedStatement("exchange", "prior_count", "already_exchanged_once", None)


_RULES = [
    _extract_tier, _extract_product_category, _extract_warranty,
    _extract_shipping_preference, _extract_complaint_history,
    _extract_payment_method, _extract_prior_exchange,
]


def extract_statements(text: str) -> list[ExtractedStatement]:
    """A single statement can express more than one fact (e.g. "I'm a Gold
    member and I already exchanged this item once") -- each rule fires
    independently. Returns [] if nothing unambiguous was found."""
    lowered = text.lower()
    results = []
    for rule in _RULES:
        item = rule(lowered)
        if item is not None:
            results.append(item)
    return results
