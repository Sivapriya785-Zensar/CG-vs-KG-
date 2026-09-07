"""
The SAME retail policy facts as data/policy_dataset.py, but written as an
unstructured prose document -- the way a real internal policy wiki page
reads, not a clean fact-per-line list. This is the source-of-truth for the
"unstructured data source" comparison track (see README.md): instead of
starting from a hand-authored graph, both KG and CG here have to work from
this messy text.

Deliberately unstructured on purpose: facts are embedded mid-sentence,
categories and rules are mixed together in flowing paragraphs, restated in
different words in more than one place (the way a real wiki page accretes
over time, with an FAQ section that repeats what the body already said),
and there's a little natural editorializing ("which surprises people
sometimes") the way a person would actually write this, not a bot
outputting a clean list.

This version is deliberately LONGER than a minimal restatement of
policy_dataset.py would need to be -- more paragraphs, more section
headers, a support-team FAQ block, a worked example, and some genuinely
irrelevant filler (store hours, shipping carriers, a general goodwill
blurb) mixed in among the load-bearing facts. That's intentional: a real
internal policy page is never just the facts in the cleanest possible
order, and an extraction pipeline that only works on a tidy paragraph
isn't really being tested. The added length restates existing facts in new
phrasing rather than introducing new ones, so the ground truth stays
identical.

Every fact in here was cross-checked against policy_dataset.py's NODES/EDGES
before writing this -- same numbers, same asymmetries, same coverage gaps --
so a "correct" answer from either pipeline is independently verifiable
against the other's ground truth, not just internally consistent with itself.
"""

POLICY_DOCUMENT_TEXT = """Return & Exchange Policy Overview

This page is maintained by the Customer Experience team and is the single source of truth for how we handle returns, exchanges, loyalty benefits, seasonal blackout windows, and the extended warranty program. Please read the whole page before answering a customer -- a lot of the nuance lives in the exceptions, not the headline numbers.

Store hours are 9am-9pm local time, seven days a week, and support tickets are typically answered within one business day. None of that affects the policy details below, but it comes up often enough in the same conversations that we're noting it here.

Section 1: Returns by category

Our return policies vary quite a bit depending on what you bought, and we get a lot of questions about the differences, so let's go category by category.

Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to cover the cost of quality-checking returned devices before they go back on the shelf (or get refurbished, if they don't pass inspection). That 30-day window starts from the delivery date on the shipping confirmation, not the order date, which matters for anything that shipped with a delay.

Furniture works a little differently. You've got a shorter window here, just 14 days, and the restocking fee is steeper at $50 given the shipping and freight costs involved in moving large items back through the warehouse. We know 14 days feels tight compared to electronics, but large-item return logistics are a lot more expensive for us, hence the shorter window and higher fee.

Apparel is the most forgiving category by a wide margin. You get a generous 45 days to send things back, and there's no fee at all for returns -- we absorb that cost as part of keeping the clothing category low-friction, since sizing issues are so common and mostly not the customer's fault.

Groceries and Digital Goods are both non-returnable, full stop, no exceptions, and support reps should not make case-by-case exceptions here even for sympathetic situations. Groceries obviously can't come back once they've left our warehouse, due to spoilage and food-safety risk -- once it's out the door, it's out the door. Digital Goods can't be returned once downloaded or activated, for the obvious reason that a digital copy can't be un-downloaded; the same reasoning applies to exchanges too, so neither category supports exchanges at all either.

Section 2: Exchanges by category

Exchanges are handled separately from returns and don't always follow the same rule as the return policy for that category, which is a common point of confusion.

If a customer would rather swap an electronics item for something else instead of getting a refund, that's allowed -- the standard exchange fee for electronics is $10. Furniture exchanges follow that exact same Standard Exchange Rule as electronics, so that's also a $10 fee, even though furniture's return fee ($50) is much higher than electronics' return fee ($15). Don't let a customer assume the exchange fee scales with the return fee -- it doesn't, both categories share the same flat $10 exchange fee.

Apparel exchanges are free -- we call this the Free Exchange Rule internally, and it applies specifically to clothing. So to be clear: apparel returns are free AND apparel exchanges are free, apparel is the only category with zero friction on both sides.

As covered above, Groceries and Digital Goods support neither returns nor exchanges. There is no exchange fee to waive for either category because the exchange option doesn't exist for them in the first place.

Section 3: Loyalty tiers and fee waivers

We've got four loyalty tiers: Bronze, Silver, Gold, and Platinum, in ascending order of benefits. Bronze is the default tier every account starts at, and Silver is the first step up, but neither Bronze nor Silver come with any fee waivers at all -- members at those tiers pay the standard exchange and restocking fees listed above just like a non-member would.

Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronics and Furniture exchanges. Gold does NOT extend to the restocking fee, though -- this is a common misconception, so it's worth stating plainly: a Gold member returning a $15 electronics item or a $50 furniture item still pays the full restocking fee, Gold only helps if they're exchanging, not returning.

Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver too, so Platinum is really the full package -- no exchange fee, no restocking fee, on either Electronics or Furniture. If you're ever unsure which tier covers which fee, remember: Gold = exchange fee only, Platinum = both fees.

Section 4: Seasonal blackout windows

We run two blackout windows a year where certain returns get more restrictive than the normal category policy, and loyalty tier can exempt a member from a blackout even when it applies to everyone else.

The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purchases made during that stretch are locked in as final sale for most customers, overriding the normal 30-day electronics return window entirely. Gold and Platinum members are exempt from this one though, meaning they keep their normal return rights even on purchases made during the blackout window.

Separately, there's the Clearance Event Blackout from January 2nd to January 15th, which restricts Apparel returns during that window, overriding the normal 45-day apparel window. But this time only Platinum members are exempt -- Gold doesn't help you here, which surprises people sometimes since Gold does help with the Holiday Sale blackout. To spell out the asymmetry directly: Gold is exempt from the Electronics blackout but NOT the Apparel blackout; Platinum is exempt from both.

Section 5: Extended Warranty

Customers can add the Extended Warranty for $25 at checkout, as a one-time add-on tied to the order. It covers defect and damage claims that go beyond what the manufacturer's own warranty covers -- so once the manufacturer's coverage window has lapsed, or for a type of damage the manufacturer excludes, the extended warranty can still apply.

Coverage is limited to Electronics and Furniture purchases only. It doesn't apply to Apparel, Groceries, or Digital Goods -- those categories aren't eligible for the warranty add-on at checkout at all, so don't offer it to a customer buying in those categories.

Section 6: Worked example

A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and later decides to exchange it for a different model rather than return it. They pay the $10 standard exchange fee -- wait, no, Gold waives the exchange fee, so they pay nothing. Now compare: if that same Gold member instead returned the television for a refund, they would owe the $15 restocking fee, because Gold's waiver only covers exchanges, not returns. Same customer, same item, different fee outcome depending on whether they return or exchange.

Section 7: Frequently asked questions

"Does my loyalty tier ever cover a restocking fee?" -- Only if you're Platinum. Gold covers exchange fees only, never restocking fees, on any category.

"If I bought electronics during the Black Friday sale, can I still return it?" -- Only if you're Gold or Platinum tier; everyone else is final-sale during that window (Nov 25 - Dec 5).

"What about returning apparel bought during the January clearance sale?" -- Only Platinum members keep return rights during that window (Jan 2 - Jan 15); Gold members do not, even though Gold covers the November blackout.

"Can I return groceries if they arrived damaged?" -- Groceries are non-returnable under this policy regardless of condition; damaged-on-arrival cases should be routed to the shipping-carrier claims process instead, which is a separate workflow from this return policy.

"Does the warranty cover a pair of jeans?" -- No, the extended warranty only covers Electronics and Furniture, never Apparel, Groceries, or Digital Goods.

"I'm Silver tier, do I get any fee breaks?" -- No, Bronze and Silver have identical fee treatment: full exchange fees, full restocking fees, no blackout exemptions. Fee waivers and blackout exemptions only start at Gold.

We ship via a mix of regional carriers depending on the destination, and delivery timing is unrelated to any of the policy terms above -- the return/exchange windows are always measured from delivery date regardless of which carrier handled the shipment. We're always working to make these policies clearer and friendlier for customers, and this page gets revisited whenever support tickets show a pattern of confusion, so if a rule above still isn't clear after reading this, flag it to the policy team rather than guessing."""
