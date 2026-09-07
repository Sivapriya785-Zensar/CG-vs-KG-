"""
Decision-based test scenarios -- the agentic upgrade from Q&A to action.

Every scenario grades whether the agent's ACTION (one of agent.decision.
ACTIONS, parsed structurally) is correct, not whether its prose sounds
right. Expected actions are grounded against data/policy_dataset.py's real
edges wherever the graph settles the question outright (documented in
`why`). A few scenarios (marked `judgment_call=True`) encode a reasonable
support-agent policy choice I'm making as the test author rather than a
fact the graph states directly -- e.g. whether a second exchange request
should escalate. Those are flagged explicitly rather than presented as
graph-derived truth, per the same anti-fabrication discipline as the rest
of this experiment: I'm not certain there's one "correct" real-world answer
for those, so don't read them as harshly as the graph-grounded ones.

Three groups:
  - SINGLE_FACT (15): one seeded fact (or none), one decision.
  - CHAINING (5): two facts stored in SEPARATE sessions for the same
    customer, one decision in a third session -- tests whether CG's
    evidence layer composes two independently-recalled facts into one
    correct action, not just recalls one fact in isolation.
  - INTERFERENCE (4): 10-11 stored facts for one customer, most irrelevant
    or deliberately conflicting in unrelated slots -- tests retrieval
    precision as the trace store grows, and specifically whether a
    conflict in an IRRELEVANT slot wrongly blocks a decision that only
    needed a different, clean slot.
"""

SINGLE_FACT = [
    {"id": "DEC1", "seed_statements": [],
     "query": "I want to return my Groceries order, it's just something I changed my mind about.",
     "expected_action": "deny_request",
     "why": "rule:return_groceries refundable=False, 'no exceptions'."},
    {"id": "DEC2", "seed_statements": [],
     "query": "I'd like to exchange my Apparel purchase for a different size.",
     "expected_action": "approve_refund",
     "why": "rule:exchange_free: allowed=True, fee_usd=0 -- standard grant, nothing to waive."},
    {"id": "DEC3", "seed_statements": ["I am a Platinum member."],
     "query": "I want to return my Furniture order -- can I get the restocking fee waived?",
     "expected_action": "apply_waiver",
     "why": "tier:platinum waives fee:restocking_fee_waiver, which applies_to rule:return_furniture."},
    {"id": "DEC4", "seed_statements": ["I am a Bronze member."],
     "query": "Can I get my restocking fee waived on this Furniture return?",
     "expected_action": "approve_refund",
     "why": "tier:bronze has no waives edges -- return proceeds, $50 fee stands, nothing waived."},
    {"id": "DEC5", "seed_statements": ["I already bought the extended warranty."],
     "query": "My Electronics item arrived damaged -- can you process my return without the restocking fee since I have the warranty?",
     "expected_action": "apply_waiver",
     "why": "product:extended_warranty -covers-> rule:return_electronics (defect/damage claims)."},
    {"id": "DEC6", "seed_statements": [],
     "query": "I want to return an Electronics item outside the standard 30-day window -- is that fine?",
     "expected_action": "deny_request",
     "why": "rule:return_electronics window_days=30; nothing in the schema overrides an exceeded window for any tier."},
    {"id": "DEC7", "seed_statements": ["I already complained about a damaged item last month."],
     "query": "This is now my second complaint about damaged furniture -- should this be handled by a person instead of continuing with a bot?",
     "expected_action": "escalate_to_human",
     "why": "repeat-complaint evidence plus an explicit ask to escalate.",
     "judgment_call": True},
    {"id": "DEC8", "seed_statements": [],
     "query": "I received the wrong item in my Electronics order -- what should happen?",
     "expected_action": "escalate_to_human",
     "why": "a shipping error isn't modeled anywhere in this return/exchange policy schema -- honest escalation, not a guessed return/exchange action.",
     "judgment_call": True},
    {"id": "DEC9", "seed_statements": ["I paid with a gift card."],
     "query": "I want a refund for my Apparel return -- will I get cash back since I used a gift card?",
     "expected_action": "approve_refund",
     "why": "the return itself is clear-cut (Apparel, free exchange/return); cash-vs-store-credit mechanics for gift-card payments aren't modeled, so the ACTION is still a grant -- the reasoning text, not the action, is where honesty about that gap should show up."},
    {"id": "DEC10", "seed_statements": ["I am a Gold tier member."],
     "query": "I'd like to exchange my Electronics purchase for a different model -- will there be a fee?",
     "expected_action": "apply_waiver",
     "why": "tier:gold waives fee:exchange_fee_waiver, which applies_to rule:exchange_standard (Electronics' exchange rule)."},
    {"id": "DEC11", "seed_statements": ["I am a Gold tier member."],
     "query": "Can I return this Furniture item and get the restocking fee waived, given my tier?",
     "expected_action": "approve_refund",
     "why": "tier:gold does NOT waive fee:restocking_fee_waiver (only Platinum does) -- return proceeds, $50 fee stands. The trap: asked directly about a waiver Gold doesn't actually have."},
    {"id": "DEC12", "seed_statements": ["I am a Platinum member."],
     "query": "I want to return Apparel I bought during the clearance event -- is that a problem given my status?",
     "expected_action": "approve_refund",
     "why": "blackout:clearance_event restricts apparel; tier:platinum -exempt_from-> clearance_event -- restriction doesn't apply."},
    {"id": "DEC13", "seed_statements": ["I am a Gold tier member."],
     "query": "I bought Apparel during the clearance sale and want to return it -- my Gold status should cover this, right?",
     "expected_action": "deny_request",
     "why": "tier:gold is exempt from winter/holiday-sale blackout ONLY, not clearance_event -- the trap: asked to confirm a benefit Gold doesn't have for this specific blackout."},
    {"id": "DEC14", "seed_statements": [],
     "query": "Can I exchange my Digital Goods purchase for a different item?",
     "expected_action": "deny_request",
     "why": "rule:exchange_none for digital_goods: allowed=False."},
    {"id": "DEC15", "seed_statements": ["I already exchanged this item once."],
     "query": "I'd like to exchange my Electronics item again for a different color -- is that possible?",
     "expected_action": "escalate_to_human",
     "why": "the graph itself has no 'one exchange per order' rule (it would say: allowed, $10 fee), but a stored prior-exchange flag is exactly the kind of thing a real agent shouldn't silently ignore or silently enforce without a real policy behind it -- escalate rather than either extreme.",
     "judgment_call": True},
]

CHAINING = [
    {"id": "CHAIN1",
     "session1_statement": "I am a Gold tier member.",
     "session2_statement": "I bought Electronics.",
     "query": "I want to exchange my order -- will there be a fee?",
     "expected_action": "apply_waiver",
     "why": "category (session 2) determines the exchange rule is rule:exchange_standard (fee-waivable); tier (session 1) determines gold waives it. Needs BOTH facts, from two different sessions."},
    {"id": "CHAIN2",
     "session1_statement": "I am a Gold tier member.",
     "session2_statement": "I bought Apparel.",
     "query": "Will I be charged if I exchange this?",
     "expected_action": "approve_refund",
     "why": "Apparel's exchange rule is already $0 regardless of tier -- Gold's waiver is moot here. Tests whether the agent over-applies the tier narrative when it doesn't actually change anything."},
    {"id": "CHAIN3",
     "session1_statement": "I am a Platinum member.",
     "session2_statement": "I bought Furniture.",
     "query": "I need to return this -- what will it cost me?",
     "expected_action": "apply_waiver",
     "why": "tier:platinum waives fee:restocking_fee_waiver, which applies_to rule:return_furniture (session 2's category)."},
    {"id": "CHAIN4",
     "session1_statement": "I am a Bronze member.",
     "session2_statement": "I bought Electronics.",
     "query": "I want to return this -- any fees?",
     "expected_action": "approve_refund",
     "why": "Bronze has no waivers; the $15 restocking fee stands, return still proceeds."},
    {"id": "CHAIN5",
     "session1_statement": "I bought Furniture.",
     "session2_statement": "I already bought the extended warranty.",
     "query": "This item arrived defective -- what happens if I return it?",
     "expected_action": "apply_waiver",
     "why": "product:extended_warranty covers rule:return_furniture for defect claims (session 1's category + session 2's warranty fact, combined)."},
]

# Each interference scenario stores every statement for ONE customer (same
# user_id), most irrelevant to the eventual query -- some deliberately
# conflicting with each other in slots that have NOTHING to do with the
# decision being asked, to test that an unrelated conflict never blocks an
# otherwise-clean decision.
INTERFERENCE = [
    {"id": "STRESS1",
     "statements": [
         "I am a Gold tier member.",
         "I prefer expedited shipping.",
         "I paid with a credit card.",
         "I already complained about a late delivery.",
         "I bought Electronics.",
         "I already exchanged a different item once.",
         "I already declined the extended warranty.",
         "I prefer overnight shipping.",          # conflicts stmt #2 (shipping slot) -- irrelevant to this decision
         "I paid with a gift card.",                # conflicts stmt #3 (payment slot) -- irrelevant to this decision
         "I already filed a complaint before.",      # redundant with #4, no new conflict
     ],
     "query": "I want to exchange my Electronics purchase -- will I be charged a fee?",
     "expected_action": "apply_waiver",
     "why": "Gold + Electronics -> exchange fee waived (same logic as DEC10/CHAIN1). The shipping and payment conflicts are in unrelated slots and must not force a fallback -- only a conflict in loyalty_tier or product would legitimately block this decision."},
    {"id": "STRESS2",
     "statements": [
         "I am a Gold tier member.",
         "I prefer expedited shipping.",
         "I paid with a credit card.",
         "I already complained about a late delivery.",
         "I bought Electronics.",
         "I already exchanged a different item once.",
         "I already declined the extended warranty.",
         "I prefer overnight shipping.",
         "I paid with a gift card.",
         "I already filed a complaint before.",
         "Actually, I just checked, I'm Silver.",     # genuine tier conflict, buried 10 statements deep
     ],
     "query": "I want to exchange my Electronics purchase -- will I be charged a fee?",
     "expected_action": None,
     "why": "Same as STRESS1 but with a genuine loyalty_tier conflict (Gold vs Silver) added at the end. Unlike STRESS1's irrelevant-slot conflicts, THIS one is directly relevant and must trigger a fallback -- expected_action is deliberately None; grade this on whether CG's fallback banner correctly names the tier conflict despite 10 other stored facts, not on which action gets picked afterward (that's whatever the fallback KG-equivalent context produces)."},
    {"id": "STRESS3",
     "statements": [
         "I prefer expedited shipping.",
         "I paid with a credit card.",
         "I already complained about a late delivery.",
         "I already exchanged a different item once.",
     ],
     "query": "Can I return my Furniture item and have the restocking fee waived?",
     "expected_action": None,
     "why": "Only off-schema decoys on record (shipping/payment/complaint/exchange-count) -- no tier, category, or warranty fact at all. CG should fall back (nothing relevant stored), exactly like KG. expected_action is deliberately None here too: grade on whether CG correctly finds nothing, not on which specific fallback action the model picks."},
    {"id": "STRESS4",
     "statements": [
         "I am a Platinum member.",
         "I bought Apparel.",
         "I already declined the extended warranty.",
         "I prefer expedited shipping.",
         "I paid with a gift card.",
         "I already complained about a late delivery.",
     ],
     "query": "I bought this during the clearance event -- can I return it given my status?",
     "expected_action": "approve_refund",
     "why": "Platinum (relevant) + Apparel (relevant, determines clearance_event is the applicable blackout) -exempt_from-> clearance blackout. Three more irrelevant decoys (warranty decline, shipping, payment, complaint) must not distract from correctly combining the two relevant facts."},
]

ALL_DECISION_SCENARIOS = {
    "single_fact": SINGLE_FACT,
    "chaining": CHAINING,
    "interference": INTERFERENCE,
}
