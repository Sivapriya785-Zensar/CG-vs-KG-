# Raw log -- unstructured-data-source track

Generated: 2026-09-09T09:56:28.403747
Extracted KG: 22 nodes, 20 edges (see data/extracted_kg.json, produced by graph/extract_kg_from_text.py).

## D1 (direct, leak_free=True)
**Query:** hey so i wanna order some groceries online but idk what happens if i don't like it when it shows up... can i actually return that stuff or nah
**Expected:** No -- Groceries are non-returnable, no exceptions.
**Why (grounding):** rule:return_groceries refundable=False.

**KG-unstructured (170 tokens, 120+50):**
> According to our return policy, you can return or exchange items within 30 days of delivery. You'll need to provide the original packaging and any included accessories. A restocking fee of 10% of the item's price will be applied.

**CG-unstructured (384 tokens, 325+59, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, groceries are non-returnable, regardless of the reason. This means you won't be able to return them if you don't like them or if they arrive damaged. If you have issues with a damaged shipment, you should contact the shipping carrier to file a claim.
Context-extraction layer retrieved:
  - (sim=0.691) "Groceries and Digital Goods are both non-returnable, full stop, no exceptions, and support reps shou..."
  - (sim=0.654) ""Can I return groceries if they arrived damaged?" -- Groceries are non-returnable under this policy ..."
  - (sim=0.617) "Our return policies vary quite a bit depending on what you bought, and we get a lot of questions abo..."

## D2 (direct, leak_free=True)
**Query:** quick q before i buy this furniture piece -- if it doesn't work out and i gotta send it back, how much is that gonna cost me
**Expected:** $50 restocking fee.
**Why (grounding):** rule:return_furniture fee_usd=50.

**KG-unstructured (301 tokens, 260+41):**
> According to our return policy, if you need to return the furniture piece, you'll be charged a fee of $50. You'll also need to initiate the return within 14 days of purchase.

**CG-unstructured (556 tokens, 513+43, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our return policy, if you need to return the furniture piece, you'll be charged a restocking fee of $50. You'll also need to initiate the return within 14 days of delivery.
Context-extraction layer retrieved:
  - (sim=0.674) "Furniture works a little differently. You've got a shorter window here, just 14 days, and the restoc..."
  - (sim=0.643) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.604) "Apparel is the most forgiving category by a wide margin. You get a generous 45 days to send things b..."

## D3 (direct, leak_free=True)
**Query:** ok so i have this electronics item i need to return, how much is the fee and how long do i actually have to do it
**Expected:** $15 fee, 30-day window.
**Why (grounding):** rule:return_electronics fee_usd=15, window_days=30.

**KG-unstructured (366 tokens, 333+33):**
> According to our Return Policy, the fee for returning an Electronics item is $15. You have 30 days from the date of purchase to initiate the return.

**CG-unstructured (675 tokens, 642+33, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, the return fee for electronics is $15. You have 30 days from the delivery date on the shipping confirmation to initiate the return.
Context-extraction layer retrieved:
  - (sim=0.710) "Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to..."
  - (sim=0.703) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.648) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."

## D4 (direct, leak_free=True)
**Query:** bought some apparel, not sure it's gonna fit right tbh. if i return it is there a fee or what
**Expected:** $0, no fee.
**Why (grounding):** rule:return_apparel fee_usd=0.

**KG-unstructured (146 tokens, 113+33):**
> According to our return policy, there is a $7.99 restocking fee for all returns. Additionally, the original shipping cost is non-refundable.

**CG-unstructured (285 tokens, 264+21, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> No, there is no fee for returning apparel. You have 45 days to send it back.
Context-extraction layer retrieved:
  - (sim=0.722) "Apparel is the most forgiving category by a wide margin. You get a generous 45 days to send things b..."
  - (sim=0.630) "Our return policies vary quite a bit depending on what you bought, and we get a lot of questions abo..."
  - (sim=0.625) "Apparel exchanges are free -- we call this the Free Exchange Rule internally, and it applies specifi..."

## D5 (direct, leak_free=True)
**Query:** so i downloaded this digital goods thing and now i'm kinda regretting it lol, is there ANY way to get a refund
**Expected:** No, non-returnable once downloaded or activated.
**Why (grounding):** rule:return_digital_goods refundable=False.

**KG-unstructured (161 tokens, 113+48):**
> According to our policy, digital goods are non-refundable. However, if you purchased the digital goods within the last 30 days, you may be eligible for a store credit. Please contact our customer support team for further assistance.

**CG-unstructured (403 tokens, 355+48, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> Unfortunately, our policy states that Digital Goods are non-returnable and non-exchangeable. Once downloaded or activated, they cannot be returned or exchanged. This is due to the nature of digital products, which cannot be un-downloaded.
Context-extraction layer retrieved:
  - (sim=0.596) "Groceries and Digital Goods are both non-returnable, full stop, no exceptions, and support reps shou..."
  - (sim=0.519) "As covered above, Groceries and Digital Goods support neither returns nor exchanges. There is no exc..."
  - (sim=0.508) "Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to..."

## D6 (direct, leak_free=True)
**Query:** given my loyalty status rn, would the exchange fee actually get waived if i swap something out
**Expected:** Yes -- Gold waives the exchange fee.
**Why (grounding):** tier:gold -waives-> fee:exchange_fee_waiver -applies_to-> rule:exchange_standard.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (119 tokens, 106+13):**
> I don't have information on loyalty status or exchange fees.

**CG-unstructured (454 tokens, 415+39, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> To determine if the exchange fee would be waived, I need to know your current loyalty status. If you're a Gold member, the exchange fee would be waived for electronics and furniture exchanges.
Context-extraction layer retrieved:
  - (sim=0.703) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.702) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."
  - (sim=0.700) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."

## D7 (direct, leak_free=True)
**Query:** ok random question but which loyalty tier(s) actually get the restocking fee waived completely, like all the way
**Expected:** Platinum only.
**Why (grounding):** only tier:platinum -waives-> fee:restocking_fee_waiver.

**KG-unstructured (129 tokens, 110+19):**
> According to our loyalty program policy, only Platinum members have their restocking fee waived completely.

**CG-unstructured (310 tokens, 293+17, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, only Platinum members get the restocking fee waived completely.
Context-extraction layer retrieved:
  - (sim=0.820) ""Does my loyalty tier ever cover a restocking fee?" -- Only if you're Platinum. Gold covers exchange..."
  - (sim=0.778) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."
  - (sim=0.775) "We've got four loyalty tiers: Bronze, Silver, Gold, and Platinum, in ascending order of benefits. Br..."

## D8 (direct, leak_free=True)
**Query:** keep seeing this extended warranty thing pop up when i checkout -- how much is it and what does it even cover
**Expected:** $25; covers defect and damage claims beyond the manufacturer warranty period.
**Why (grounding):** product:extended_warranty cost_usd=25, attrs.covers.

**KG-unstructured (170 tokens, 110+60):**
> Our Extended Warranty program is available for purchase at checkout. The cost is $99.99 for a 2-year warranty and $149.99 for a 3-year warranty. 

The Extended Warranty covers repairs or replacements for defects in materials and workmanship for the duration of the warranty period.

**CG-unstructured (271 tokens, 225+46, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> The Extended Warranty is a one-time add-on that costs $25. It's available at checkout. According to our policy, it covers defect and damage claims for Electronics and Furniture, beyond what the manufacturer's own warranty covers.
Context-extraction layer retrieved:
  - (sim=0.779) "Customers can add the Extended Warranty for $25 at checkout, as a one-time add-on tied to the order...."
  - (sim=0.726) ""Does the warranty cover a pair of jeans?" -- No, the extended warranty only covers Electronics and ..."
  - (sim=0.720) "Section 5: Extended Warranty..."

## D9 (direct, leak_free=True)
**Query:** wait before this ships can u just confirm -- did i end up adding that extended warranty or not, i genuinely forget
**Expected:** No, you declined it.
**Why (grounding):** direct recall of the stored warranty.status=declined trace.
- Seed: "I already declined the extended warranty." -> Stored: warranty.status = declined

**KG-unstructured (139 tokens, 111+28):**
> I'd be happy to help you check on that. According to our records, you did not add the extended warranty to your order.

**CG-unstructured (539 tokens, 520+19):**
> I don't have information on whether you added the Extended Warranty to your order or not.
Context-extraction layer retrieved:
  - (sim=0.742) "Customers can add the Extended Warranty for $25 at checkout, as a one-time add-on tied to the order...."
  - (sim=0.673) "Section 5: Extended Warranty..."
  - (sim=0.671) ""Does the warranty cover a pair of jeans?" -- No, the extended warranty only covers Electronics and ..."

## D10 (direct, leak_free=True)
**Query:** i want to swap my electronics item for a different model, is that even allowed and how much would it cost me
**Expected:** Yes, $10 fee.
**Why (grounding):** rule:exchange_standard: allowed=True, fee_usd=10.

**KG-unstructured (357 tokens, 329+28):**
> According to our policy, you can exchange your electronics item under our Standard Exchange Rule. However, there is a fee of $10.

**CG-unstructured (662 tokens, 638+24, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> Yes, you can swap your electronics item for a different model. The standard exchange fee for electronics is $10.
Context-extraction layer retrieved:
  - (sim=0.684) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.592) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."
  - (sim=0.571) "Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to..."

## D11 (direct, leak_free=True)
**Query:** when's the holiday sale blackout thing exactly and what category does it mess with
**Expected:** Nov 25 - Dec 5, restricts Electronics.
**Why (grounding):** blackout:holiday_sale attrs.dates + restricts edge to product_category:electronics.

**KG-unstructured (135 tokens, 103+32):**
> According to our policy, the holiday sale blackout period is from November 20th to December 1st. It affects the Electronics and Home Appliances categories.

**CG-unstructured (342 tokens, 318+24, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> The Holiday Sale Blackout runs from November 25th through December 5th and applies to the Electronics category.
Context-extraction layer retrieved:
  - (sim=0.791) "The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purc..."
  - (sim=0.704) "Separately, there's the Clearance Event Blackout from January 2nd to January 15th, which restricts A..."
  - (sim=0.694) "We run two blackout windows a year where certain returns get more restrictive than the normal catego..."

## D12 (direct, leak_free=True)
**Query:** been a member here a long time now -- would my restocking fee get waived if i return an electronics item
**Expected:** Yes -- Platinum waives the restocking fee, which applies to Electronics.
**Why (grounding):** tier:platinum -waives-> fee:restocking_fee_waiver -applies_to-> rule:return_electronics.
- Seed: "I am a Platinum member." -> Stored: loyalty_tier.tier = Platinum

**KG-unstructured (376 tokens, 328+48):**
> As a Platinum member, you are exempt from the Holiday Sale Blackout, but that doesn't directly affect the restocking fee. However, I don't have information on whether your loyalty tier affects the restocking fee for electronics returns.

**CG-unstructured (689 tokens, 616+73, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> As a Gold member, you are exempt from the Holiday Sale Blackout, but that doesn't affect the restocking fee. According to our policy, Gold members get their exchange fee waived, but the restocking fee is not waived for returns. So, if you return an electronics item, you would still be responsible for paying the $15 restocking fee.
Context-extraction layer retrieved:
  - (sim=0.781) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."
  - (sim=0.739) "Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to..."
  - (sim=0.724) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."

## D13 (direct, leak_free=True)
**Query:** can i exchange a groceries order instead of just returning it or is that not a thing
**Expected:** No, exchanges aren't allowed for Groceries at all.
**Why (grounding):** rule:exchange_none for groceries: allowed=False.

**KG-unstructured (177 tokens, 105+72):**
> According to our policy, exchanges are only available for orders that are defective or damaged. If you'd like to exchange a grocery order, you'll need to contact our customer support team within 3 days of delivery and provide proof of the issue. We'll then assist you in returning the item and replacing it with a new one of equal or greater value.

**CG-unstructured (346 tokens, 317+29, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> No, exchanges are not an option for Groceries. According to our policy, Groceries are non-returnable and non-exchangeable.
Context-extraction layer retrieved:
  - (sim=0.721) "Groceries and Digital Goods are both non-returnable, full stop, no exceptions, and support reps shou..."
  - (sim=0.706) "As covered above, Groceries and Digital Goods support neither returns nor exchanges. There is no exc..."
  - (sim=0.694) ""Can I return groceries if they arrived damaged?" -- Groceries are non-returnable under this policy ..."

## D14 (direct, leak_free=True)
**Query:** whats the deal with the clearance event dates, like start and end exactly
**Expected:** Jan 2 - Jan 15.
**Why (grounding):** blackout:clearance_event attrs.dates.

**KG-unstructured (111 tokens, 103+8):**
> I don't have that information.

**CG-unstructured (343 tokens, 325+18, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> The Clearance Event Blackout dates are January 2nd to January 15th.
Context-extraction layer retrieved:
  - (sim=0.662) "Separately, there's the Clearance Event Blackout from January 2nd to January 15th, which restricts A..."
  - (sim=0.661) ""What about returning apparel bought during the January clearance sale?" -- Only Platinum members ke..."
  - (sim=0.618) "The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purc..."

## D15 (direct, leak_free=True)
**Query:** for whatever i ordered last time, what's the exchange fee gonna be if i wanna swap it
**Expected:** $10 -- Furniture uses the standard exchange rule.
**Why (grounding):** product_category:furniture -> rule:exchange_standard, fee_usd=10.
- Seed: "I bought Furniture on my last order." -> Stored: product.category = Furniture

**KG-unstructured (115 tokens, 107+8):**
> I don't have that information.

**CG-unstructured (498 tokens, 416+82, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> I'd need to know what type of item you're referring to and whether you're a Gold-tier member. If you're exchanging an electronics item and you're not a Gold-tier member, the exchange fee is $10. If you're a Gold-tier member, the exchange fee is waived. If you're exchanging a furniture item, the exchange fee is also $10, regardless of your tier status.
Context-extraction layer retrieved:
  - (sim=0.753) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.692) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."
  - (sim=0.686) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."

## D16 (direct, leak_free=True)
**Query:** out of all the tiers which ones dodge the holiday sale blackout
**Expected:** Gold and Platinum.
**Why (grounding):** tier:gold and tier:platinum both -exempt_from-> blackout:holiday_sale.

**KG-unstructured (108 tokens, 100+8):**
> I don't have that information.

**CG-unstructured (329 tokens, 315+14, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> Gold and Platinum members are exempt from the Holiday Sale Blackout.
Context-extraction layer retrieved:
  - (sim=0.730) "The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purc..."
  - (sim=0.692) "We run two blackout windows a year where certain returns get more restrictive than the normal catego..."
  - (sim=0.672) "Separately, there's the Clearance Event Blackout from January 2nd to January 15th, which restricts A..."

## D17 (direct, leak_free=True)
**Query:** so i think i paid extra for protection on this order -- if my furniture item shows up busted does that cover the return fee
**Expected:** Yes -- warranty covers Furniture returns for defect/damage.
**Why (grounding):** product:extended_warranty -covers-> rule:return_furniture; warranty=purchased trace.
- Seed: "I already purchased the extended warranty." -> Stored: warranty.status = purchased

**KG-unstructured (327 tokens, 256+71):**
> You paid extra for protection, which is the Extended Warranty. According to the policy, the Extended Warranty covers "defect and damage claims beyond manufacturer's warranty". If your furniture item shows up busted, you may be eligible for a return under the Return Furniture policy. However, I don't have information on whether the Extended Warranty covers the return fee.

**CG-unstructured (658 tokens, 622+36):**
> You have purchased the Extended Warranty, which covers defect and damage claims beyond the manufacturer's warranty. However, I don't have information on whether this warranty covers the return fee.
Context-extraction layer retrieved:
  - (sim=0.642) "Furniture works a little differently. You've got a shorter window here, just 14 days, and the restoc..."
  - (sim=0.635) ""Can I return groceries if they arrived damaged?" -- Groceries are non-returnable under this policy ..."
  - (sim=0.630) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."

## R1 (reasoning, leak_free=True)
**Query:** ok i keep hearing the top tier gets crazy perks on fees but honestly idk where i land tier-wise -- would my restocking fee actually be waived or is that only for ppl higher than me
**Expected:** No -- Gold only waives the exchange fee, not restocking. Restocking-fee waiver is Platinum-only.
**Why (grounding):** tier:gold has only one waives edge (exchange_fee_waiver); restocking_fee_waiver is waived only by tier:platinum.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (189 tokens, 127+62):**
> According to our policy, the top tier (Elite Tier) does receive waived restocking fees. However, I don't have information on the specific requirements or benefits for each tier. To determine your current tier and associated benefits, I recommend checking your account details or contacting our customer service team for more information.

**CG-unstructured (310 tokens, 283+27, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, your restocking fee will not be waived. You'll be responsible for paying the full restocking fee.
Context-extraction layer retrieved:
  - (sim=0.763) ""Does my loyalty tier ever cover a restocking fee?" -- Only if you're Platinum. Gold covers exchange..."
  - (sim=0.736) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."
  - (sim=0.720) ""I'm Silver tier, do I get any fee breaks?" -- No, Bronze and Silver have identical fee treatment: f..."

## R2 (reasoning, leak_free=True)
**Query:** so this is landing smack in the middle of the clearance period, does my status get me around that or is that exemption only for a different blackout
**Expected:** No -- Gold is exempt from Holiday Sale only, not Clearance Event. Only Platinum is exempt from Clearance Event.
**Why (grounding):** tier:gold -exempt_from-> holiday_sale only; tier:platinum -exempt_from-> both.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (142 tokens, 117+25):**
> I don't have information on whether your status affects the clearance period or if there's a different blackout period for exemptions.

**CG-unstructured (384 tokens, 332+52, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> You are a Platinum member. According to the policy, Platinum members are exempt from the Clearance Event Blackout, which restricts Apparel returns from January 2nd to January 15th. So, yes, your status will get you around that blackout.
Context-extraction layer retrieved:
  - (sim=0.693) "Separately, there's the Clearance Event Blackout from January 2nd to January 15th, which restricts A..."
  - (sim=0.657) "The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purc..."
  - (sim=0.642) "We run two blackout windows a year where certain returns get more restrictive than the normal catego..."

## R3 (reasoning, leak_free=True)
**Query:** not 100% sure if i have protection coverage on this order tbh -- if i do and i'm returning apparel does that even apply or is it only for certain stuff
**Expected:** No -- warranty covers only Electronics and Furniture returns, not Apparel (Apparel returns are already free anyway, but the coverage claim itself would be false).
**Why (grounding):** product:extended_warranty covers only rule:return_electronics and rule:return_furniture.
- Seed: "I already purchased the extended warranty." -> Stored: warranty.status = purchased

**KG-unstructured (156 tokens, 123+33):**
> According to our policy, Protection Coverage applies to eligible items, but it does not cover apparel. If you're returning apparel, the Protection Coverage would not apply.

**CG-unstructured (339 tokens, 290+49, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> Since you're returning apparel, our policy is that there's no fee for returns in this category, and you have 45 days to send it back. This applies to all apparel purchases, regardless of whether you have protection coverage or not.
Context-extraction layer retrieved:
  - (sim=0.670) "Coverage is limited to Electronics and Furniture purchases only. It doesn't apply to Apparel, Grocer..."
  - (sim=0.645) "Apparel is the most forgiving category by a wide margin. You get a generous 45 days to send things b..."
  - (sim=0.619) ""What about returning apparel bought during the January clearance sale?" -- Only Platinum members ke..."

## R4 (reasoning, leak_free=True)
**Query:** if someone's groceries order shows up and they want a refund, does ANYTHING help them out here -- status, protection, whatever -- or is it just a hard no
**Expected:** Nothing helps -- Groceries has no connection to any waiver or warranty; it's simply non-returnable regardless of tier or coverage.
**Why (grounding):** no tier or warranty edge touches rule:return_groceries anywhere in the schema.

**KG-unstructured (203 tokens, 122+81):**
> According to our policy, if a customer's groceries order shows up and they want a refund, they may be eligible for a refund or exchange under our "Order Protection" policy. This policy provides a 3-day window for customers to report any issues with their order, including damage or incorrect items. If the issue is reported within this timeframe, we will work with the customer to resolve the issue.

**CG-unstructured (401 tokens, 357+44, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> Unfortunately, it's a hard no. According to our policy, groceries are non-returnable, regardless of condition. If they arrived damaged, you should contact the shipping carrier to file a claim through their claims process.
Context-extraction layer retrieved:
  - (sim=0.726) ""Can I return groceries if they arrived damaged?" -- Groceries are non-returnable under this policy ..."
  - (sim=0.677) "Groceries and Digital Goods are both non-returnable, full stop, no exceptions, and support reps shou..."
  - (sim=0.619) "Apparel is the most forgiving category by a wide margin. You get a generous 45 days to send things b..."

## R5 (reasoning, leak_free=True)
**Query:** between my account status and any seasonal stuff, could i even order electronics during the holiday sale without it being a problem to return later
**Expected:** Yes -- Platinum is exempt from the Holiday Sale blackout, so the restriction doesn't apply.
**Why (grounding):** blackout:holiday_sale -restricts-> electronics; tier:platinum -exempt_from-> holiday_sale.
- Seed: "I am a Platinum member." -> Stored: loyalty_tier.tier = Platinum

**KG-unstructured (391 tokens, 332+59):**
> Based on the policy, as a Platinum loyalty tier member, you are exempt from the Holiday Sale Blackout, which means you can order electronics during the sale period. However, I don't have information on any additional seasonal return policies that might affect your ability to return electronics after the sale.

**CG-unstructured (577 tokens, 540+37, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> Based on the policy, as a Platinum member, you are exempt from the Holiday Sale Blackout, which means you can still make a purchase during that time and return it later.
Context-extraction layer retrieved:
  - (sim=0.749) "The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purc..."
  - (sim=0.734) ""If I bought electronics during the Black Friday sale, can I still return it?" -- Only if you're Gol..."
  - (sim=0.674) "Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to..."

## R6 (reasoning, leak_free=True)
**Query:** whatever tier i end up being, does that get me the exchange fee waiver or the restocking one or neither lol
**Expected:** No -- Bronze has zero waivers in this policy.
**Why (grounding):** tier:bronze has no waives edges anywhere.
- Seed: "I am a Bronze member." -> Stored: loyalty_tier.tier = Bronze

**KG-unstructured (317 tokens, 262+55):**
> Based on our policy, if you're a Platinum member, you'll get both the Exchange Fee Waiver and the Restocking Fee Waiver. If you're a Gold member, you'll get the Exchange Fee Waiver, but not the Restocking Fee Waiver.

**CG-unstructured (635 tokens, 570+65):**
> Based on our policy, if you're a Platinum member, you'll get both the exchange fee waiver and the restocking fee waiver. If you're a Gold member, you'll get the exchange fee waiver, but not the restocking fee waiver. If you're a Bronze member, you won't get either waiver.
Context-extraction layer retrieved:
  - (sim=0.767) ""Does my loyalty tier ever cover a restocking fee?" -- Only if you're Platinum. Gold covers exchange..."
  - (sim=0.751) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."
  - (sim=0.718) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."

## R7 (reasoning, leak_free=True)
**Query:** if someone buys furniture and wants to both return it AND separately maybe exchange it instead, is that literally the same fee or two diff things
**Expected:** Two different rules -- the Furniture Return Rule ($50) and the Standard Exchange Rule ($10) -- not one combined 'change your mind' fee.
**Why (grounding):** rule:return_furniture and rule:exchange_standard are distinct nodes with different fees.

**KG-unstructured (340 tokens, 258+82):**
> According to our return policy, if someone buys furniture and wants to return it, there is a $50 fee (ReturnRule 'Return Furniture').

If they also want to exchange it, there is a separate exchange fee of $10 (ExchangeRule 'Standard Exchange Rule').

So, in this case, there would be two separate fees: $50 for the return and $10 for the exchange.

**CG-unstructured (591 tokens, 517+74, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, if a customer wants to return furniture and then exchange it for a different item, they would be subject to two separate fees: the $50 return fee (as per the Return Furniture policy) and the $10 exchange fee (as per the Standard Exchange Rule, which applies to Furniture). These are two distinct fees, not the same fee.
Context-extraction layer retrieved:
  - (sim=0.801) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.720) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."
  - (sim=0.712) "Exchanges are handled separately from returns and don't always follow the same rule as the return po..."

## R8 (reasoning, leak_free=True)
**Query:** not sure if i added extra coverage to this electronics order or not -- if it breaks what am i actually paying, and would it be different either way
**Expected:** Since coverage was declined, the full $15 restocking fee applies if returned; if warranty had been purchased, it would have covered the defect claim on Electronics instead.
**Why (grounding):** warranty=declined trace; product:extended_warranty covers rule:return_electronics.
- Seed: "I already declined the extended warranty." -> Stored: warranty.status = declined

**KG-unstructured (451 tokens, 336+115):**
> According to our policy, if your electronics item breaks, you would be subject to our Standard Exchange Rule. This rule has a fee of $10 USD.

The Extended Warranty, which covers defect and damage claims beyond the manufacturer's warranty, is available for purchase for electronics items. However, if you didn't add this extra coverage to your order, the $10 USD fee from the Standard Exchange Rule would still apply.

So, in either case, you would be responsible for paying the $10 USD fee if you need to exchange the item due to a defect or damage.

**CG-unstructured (770 tokens, 607+163):**
> According to our policy, the Extended Warranty is a one-time add-on that can be purchased for $25 at checkout. If you did add the Extended Warranty to your order, it would cover defect and damage claims beyond the manufacturer's warranty.

If you didn't add the Extended Warranty, you would be covered by the manufacturer's warranty, and any claims would be handled according to their terms.

In either case, if the item breaks, you would need to contact our customer support to initiate a claim. If you added the Extended Warranty, you would be responsible for the $25 cost of the warranty, in addition to any other applicable fees. If you didn't add the Extended Warranty, you would not be responsible for the $25 fee, but you would still need to follow the manufacturer's warranty claims process.
Context-extraction layer retrieved:
  - (sim=0.687) "Coverage is limited to Electronics and Furniture purchases only. It doesn't apply to Apparel, Grocer..."
  - (sim=0.663) "Customers can add the Extended Warranty for $25 at checkout, as a one-time add-on tied to the order...."
  - (sim=0.602) ""Does the warranty cover a pair of jeans?" -- No, the extended warranty only covers Electronics and ..."

## R9 (reasoning, leak_free=True)
**Query:** thinking about exchanging an apparel item later, given my account status should i expect to pay anything or does tier not even matter here
**Expected:** No fee either way -- Apparel exchanges are already free regardless of tier, so Gold's waiver doesn't change anything here.
**Why (grounding):** rule:exchange_free (Apparel) is already fee_usd=0, independent of any tier waiver.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (143 tokens, 113+30):**
> According to our policy, tier does not affect the exchange process for apparel items. You will not be charged a fee for exchanging an apparel item.

**CG-unstructured (321 tokens, 266+55, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> As a Platinum loyalty tier member, you are eligible for free restocking fees on exchanges, but since you're exchanging an apparel item, the Free Exchange Rule applies. So, in this case, tier doesn't matter, and you won't pay anything for the exchange.
Context-extraction layer retrieved:
  - (sim=0.638) ""Does my loyalty tier ever cover a restocking fee?" -- Only if you're Platinum. Gold covers exchange..."
  - (sim=0.638) "Apparel is the most forgiving category by a wide margin. You get a generous 45 days to send things b..."
  - (sim=0.635) "Apparel exchanges are free -- we call this the Free Exchange Rule internally, and it applies specifi..."

## R10 (reasoning, leak_free=True)
**Query:** ok weird question but looking at both blackout periods, is there a tier that AINT fully exempt from at least one of em
**Expected:** Yes -- Bronze, Silver, and Gold are all not exempt from at least one blackout (Bronze/Silver from both, Gold specifically from Clearance Event); only Platinum is exempt from both.
**Why (grounding):** tier:bronze/silver: no exempt_from edges. tier:gold: holiday_sale only. tier:platinum: both.

**KG-unstructured (159 tokens, 113+46):**
> According to our policy, Tier 3 is not fully exempt from the winter blackout period (December 15 - January 15), but it is fully exempt from the summer blackout period (June 20 - August 20).

**CG-unstructured (317 tokens, 302+15, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> Yes, Bronze and Silver tiers are fully exempt from neither blackout period.
Context-extraction layer retrieved:
  - (sim=0.735) "We run two blackout windows a year where certain returns get more restrictive than the normal catego..."
  - (sim=0.678) ""I'm Silver tier, do I get any fee breaks?" -- No, Bronze and Silver have identical fee treatment: f..."
  - (sim=0.661) "Separately, there's the Clearance Event Blackout from January 2nd to January 15th, which restricts A..."

## R11 (reasoning, leak_free=True)
**Query:** wanna exchange a groceries item instead of returning it -- does my status open that up or is groceries just locked no matter what
**Expected:** No -- Groceries exchanges aren't allowed at all, unconditionally; no tier overrides this.
**Why (grounding):** rule:exchange_none for groceries: allowed=False; no tier edge touches it.
- Seed: "I am a Platinum member." -> Stored: loyalty_tier.tier = Platinum

**KG-unstructured (157 tokens, 113+44):**
> According to our policy, you can exchange a groceries item if you have a "Preferred" or "Elite" status. If you have a "Basic" status, you can only return the item for a refund.

**CG-unstructured (372 tokens, 325+47, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> Unfortunately, groceries are non-returnable and non-exchangeable, regardless of your status or the condition of the item. According to our policy, groceries can't be exchanged or returned, so this option isn't available for you.
Context-extraction layer retrieved:
  - (sim=0.727) "Groceries and Digital Goods are both non-returnable, full stop, no exceptions, and support reps shou..."
  - (sim=0.701) "As covered above, Groceries and Digital Goods support neither returns nor exchanges. There is no exc..."
  - (sim=0.690) ""Can I return groceries if they arrived damaged?" -- Groceries are non-returnable under this policy ..."

## R12 (reasoning, leak_free=True)
**Query:** if my electronics return also has a restocking fee attached does my status waive THAT too or just the exchange one
**Expected:** No -- the restocking fee CAN be waived, but only by Platinum, not Gold. You'd still pay the $15 fee.
**Why (grounding):** fee:restocking_fee_waiver applies_to rule:return_electronics, but only tier:platinum waives that fee.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (388 tokens, 328+60):**
> According to our policy, the Platinum loyalty tier only waives the exchange fee (which is $10) as per the Standard Exchange Rule. The restocking fee is a separate fee associated with the Return Electronics policy, which is $15. The Platinum tier does not exempt you from this fee.

**CG-unstructured (656 tokens, 601+55, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, being a Gold member only waives the exchange fee, not the restocking fee. So, if you're a Gold member and your electronics return also has a restocking fee attached, you would still be responsible for paying the restocking fee.
Context-extraction layer retrieved:
  - (sim=0.763) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."
  - (sim=0.735) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."
  - (sim=0.716) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."

## R13 (reasoning, leak_free=True)
**Query:** electronics vs furniture -- is it the same tiers that get the exchange fee waived or does that differ between them
**Expected:** Identical -- both use the Standard Exchange Rule, so the same Gold/Platinum waiver applies equally to both.
**Why (grounding):** both product_category:electronics and product_category:furniture -> rule:exchange_standard.

**KG-unstructured (447 tokens, 365+82):**
> According to the policy, the Exchange Rule 'Standard Exchange Rule' applies to both Electronics and Furniture. This rule states that the exchange fee is waived, as the 'allowed' field is set to True. The fee waiver is not tier-specific, so the same tiers (Gold and Platinum) that are exempt from the Holiday Sale Blackout would also be exempt from the exchange fee for both Electronics and Furniture.

**CG-unstructured (670 tokens, 626+44, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to the policy, the exchange fee waiver tiers differ between Electronics and Furniture. For Electronics, the exchange fee is waived for Platinum members. For Furniture, the exchange fee is waived for both Platinum and Gold members.
Context-extraction layer retrieved:
  - (sim=0.827) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.765) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."
  - (sim=0.739) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."

## R14 (reasoning, leak_free=False)
**Query:** so i mentioned i already swapped this electronics thing once before -- does that change anything if i wanna do it again
**Expected:** The graph itself has no 'one exchange per order' limit (it would simply say: allowed, $10 fee) -- but a prior exchange on record is worth flagging as a possible edge case rather than silently ignored.
**Why (grounding):** exchange.prior_count is an off-schema fact (no kg_node_id) -- tests honest handling of evidence the static graph doesn't have a rule for.
- Seed: "I already used my exchange on this order once before." -> Stored: exchange.prior_count = already_exchanged_once

**KG-unstructured (375 tokens, 328+47):**
> According to our Standard Exchange Rule, there is a $10 fee for exchanging an item. Since you've already exchanged this electronics item once before, the exchange is still allowed, but you will be charged the $10 fee again.

**CG-unstructured (684 tokens, 637+47, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, the standard exchange fee for electronics is a flat $10, regardless of the number of exchanges. So, if you want to exchange the item again, you would still be charged the $10 exchange fee.
Context-extraction layer retrieved:
  - (sim=0.559) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.548) "Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to..."
  - (sim=0.533) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."

## R15 (reasoning, leak_free=True)
**Query:** looking at a digital goods purchase, does my account status change anything about returning or exchanging it if i end up hating it
**Expected:** No -- Digital Goods can be neither returned nor exchanged at all, regardless of tier.
**Why (grounding):** rule:return_digital_goods refundable=False; rule:exchange_none for digital_goods allowed=False; neither has any tier connection.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (133 tokens, 113+20):**
> According to our policy, account status does not affect the return or exchange process for digital goods.

**CG-unstructured (352 tokens, 311+41, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> No, your account status does not change the return or exchange policy for Digital Goods. According to our policy, Digital Goods are non-returnable and non-exchangeable, regardless of your account status.
Context-extraction layer retrieved:
  - (sim=0.686) "Groceries and Digital Goods are both non-returnable, full stop, no exceptions, and support reps shou..."
  - (sim=0.636) ""If I bought electronics during the Black Friday sale, can I still return it?" -- Only if you're Gol..."
  - (sim=0.631) "Our return policies vary quite a bit depending on what you bought, and we get a lot of questions abo..."

## R16 (reasoning, leak_free=True)
**Query:** is there like a case where paying for the warranty is literally pointless bc you'd get the same protection for free anyway
**Expected:** Yes -- Apparel exchanges are already free and warranty doesn't even cover Apparel returns anyway, so it adds nothing there.
**Why (grounding):** rule:exchange_free fee_usd=0; product:extended_warranty's covers list excludes apparel entirely.

**KG-unstructured (164 tokens, 111+53):**
> According to our policy, if you purchase a product with a defect within 30 days of the original purchase date, you are eligible for a full refund or replacement, regardless of whether you have a warranty. This is covered under our 30-Day Satisfaction Guarantee.

**CG-unstructured (341 tokens, 272+69, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, the Extended Warranty covers defect and damage claims that go beyond what the manufacturer's own warranty covers. If a customer purchases an item with a manufacturer's warranty that already covers the item for its entire lifespan, then paying for the Extended Warranty would indeed be pointless, as the customer would already have the same protection for free.
Context-extraction layer retrieved:
  - (sim=0.626) "Customers can add the Extended Warranty for $25 at checkout, as a one-time add-on tied to the order...."
  - (sim=0.624) "Coverage is limited to Electronics and Furniture purchases only. It doesn't apply to Apparel, Grocer..."
  - (sim=0.619) ""Does the warranty cover a pair of jeans?" -- No, the extended warranty only covers Electronics and ..."

## R17 (reasoning, leak_free=True)
**Query:** trying to return a groceries order -- does my status get me a refund here or is that policy just a hard wall no matter the tier
**Expected:** Absolute -- Groceries' non-refundable rule has no tier connection at all. Gold doesn't help here.
**Why (grounding):** rule:return_groceries refundable=False; no tier edge touches it.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (133 tokens, 115+18):**
> I don't have information on whether your status affects the refund policy for groceries orders.

**CG-unstructured (354 tokens, 320+34, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> Unfortunately, our policy is a hard wall for groceries, regardless of your tier status. Groceries are non-returnable under this policy, and we cannot make exceptions.
Context-extraction layer retrieved:
  - (sim=0.735) ""Can I return groceries if they arrived damaged?" -- Groceries are non-returnable under this policy ..."
  - (sim=0.669) "Groceries and Digital Goods are both non-returnable, full stop, no exceptions, and support reps shou..."
  - (sim=0.632) "Our return policies vary quite a bit depending on what you bought, and we get a lot of questions abo..."

## M1 (mixed, leak_free=True)
**Query:** two things -- whats the standard exchange fee on electronics, and given my status would i actually have to pay it
**Expected:** $10 standard fee; waived to $0 for Gold.
**Why (grounding):** rule:exchange_standard fee_usd=10; tier:gold waives fee:exchange_fee_waiver which applies_to it.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (390 tokens, 328+62):**
> Based on our policy, the standard exchange fee on electronics is $10.

However, since you are a Platinum loyalty tier member, you are exempt from the Holiday Sale Blackout, which means you can exchange electronics during this period without any restrictions. Therefore, you would not have to pay the exchange fee.

**CG-unstructured (691 tokens, 622+69, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, the standard exchange fee for electronics is $10.

As for your status, I don't have information on your specific loyalty tier. However, I can tell you that if you're a Gold member, you would not have to pay the exchange fee, as Gold members are exempt from paying the exchange fee for exchanges.
Context-extraction layer retrieved:
  - (sim=0.762) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.672) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."
  - (sim=0.664) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."

## M2 (mixed, leak_free=True)
**Query:** whats the restocking fee on a furniture return, and does the warranty cover that if u have it
**Expected:** $50 fee; yes, warranty covers Furniture returns.
**Why (grounding):** rule:return_furniture fee_usd=50; product:extended_warranty covers rule:return_furniture.

**KG-unstructured (323 tokens, 252+71):**
> According to our return policy, the restocking fee for a furniture return is $50.

As for the warranty, the Extended Warranty policy covers defect and damage claims beyond the manufacturer's warranty. However, it does not specifically mention covering restocking fees. Therefore, I don't have information on whether the warranty covers the restocking fee in this case.

**CG-unstructured (530 tokens, 488+42, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our return policy, the restocking fee for a furniture return is $50. 

The Extended Warranty does not cover restocking fees. It covers defect and damage claims beyond the manufacturer's warranty.
Context-extraction layer retrieved:
  - (sim=0.776) "Furniture works a little differently. You've got a shorter window here, just 14 days, and the restoc..."
  - (sim=0.727) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."
  - (sim=0.680) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."

## M3 (mixed, leak_free=True)
**Query:** can u tell me the holiday sale dates and also does my status get me around that restriction
**Expected:** Nov 25 - Dec 5; yes, Platinum is exempt.
**Why (grounding):** blackout:holiday_sale dates; tier:platinum exempt_from holiday_sale.
- Seed: "I am a Platinum member." -> Stored: loyalty_tier.tier = Platinum

**KG-unstructured (180 tokens, 106+74):**
> According to our policy, our holiday sale dates are from November 25th to December 1st.

As for your status, our loyalty program has a "VIP" tier that excludes sale restrictions for VIP members. However, I need to verify your current tier status to confirm. Can you please provide your loyalty program membership number or email address associated with your account?

**CG-unstructured (308 tokens, 276+32, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> The Holiday Sale Blackout dates are November 25th through December 5th. As a customer, I don't have information on your specific status.
Context-extraction layer retrieved:
  - (sim=0.716) "The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purc..."
  - (sim=0.662) ""If I bought electronics during the Black Friday sale, can I still return it?" -- Only if you're Gol..."
  - (sim=0.646) ""What about returning apparel bought during the January clearance sale?" -- Only Platinum members ke..."

## M4 (mixed, leak_free=True)
**Query:** how much is the warranty even, and would it cover an apparel return
**Expected:** $25; no -- warranty doesn't cover Apparel (and Apparel returns are already free anyway).
**Why (grounding):** product:extended_warranty cost_usd=25; covers list excludes apparel.

**KG-unstructured (182 tokens, 102+80):**
> According to our policy, the warranty is a 2-year protection plan that costs $19.99 for purchases made between January 1st and June 30th, and $24.99 for purchases made between July 1st and December 31st.

As for coverage, the warranty covers defects in materials and workmanship for eligible products, but it does not cover apparel or accessories.

**CG-unstructured (288 tokens, 249+39, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> The warranty is an extended warranty that covers Electronics and Furniture, but not Apparel. It does not cover Digital Goods or Groceries. I don't have information on the cost of the warranty.
Context-extraction layer retrieved:
  - (sim=0.696) "Apparel is the most forgiving category by a wide margin. You get a generous 45 days to send things b..."
  - (sim=0.663) ""Does the warranty cover a pair of jeans?" -- No, the extended warranty only covers Electronics and ..."
  - (sim=0.643) ""What about returning apparel bought during the January clearance sale?" -- Only Platinum members ke..."

## M5 (mixed, leak_free=True)
**Query:** whats the exchange fee for furniture, and also totally unrelated but did i end up adding that protection plan to my order
**Expected:** $10 (unrelated first part); no, you declined it.
**Why (grounding):** tests whether the model keeps two unrelated facts straight without conflating them.
- Seed: "I already declined the extended warranty." -> Stored: warranty.status = declined

**KG-unstructured (292 tokens, 255+37):**
> According to our policy, the exchange fee for furniture is $10.

As for the protection plan, I don't have information on whether you added the Extended Warranty to your order.

**CG-unstructured (698 tokens, 661+37):**
> According to our policy, the exchange fee for furniture is $10.

As for the protection plan, I don't have information on whether you added it to your order or not.
Context-extraction layer retrieved:
  - (sim=0.762) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.702) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."
  - (sim=0.697) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."

## M6 (mixed, leak_free=True)
**Query:** which tiers waive the restocking fee and does my status put me in that group
**Expected:** Only Platinum; no, Gold is not in that group.
**Why (grounding):** only tier:platinum -waives-> fee:restocking_fee_waiver.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (157 tokens, 104+53):**
> According to our policy, the following tiers waive the restocking fee:

* Platinum Members
* Gold Members with 5+ years of loyalty

Please note that your status is not mentioned in your query, so I don't have information about your current status.

**CG-unstructured (298 tokens, 260+38, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, the Platinum tier is the only one that waives the restocking fee. Since you didn't mention your tier, I don't have information on your status.
Context-extraction layer retrieved:
  - (sim=0.760) ""Does my loyalty tier ever cover a restocking fee?" -- Only if you're Platinum. Gold covers exchange..."
  - (sim=0.719) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."
  - (sim=0.704) ""I'm Silver tier, do I get any fee breaks?" -- No, Bronze and Silver have identical fee treatment: f..."

## M7 (mixed, leak_free=True)
**Query:** clearance event dates pls, and is any tier exempt from that one
**Expected:** Jan 2 - Jan 15; Platinum only.
**Why (grounding):** blackout:clearance_event dates; only tier:platinum exempt_from it.

**KG-unstructured (110 tokens, 102+8):**
> I don't have that information.

**CG-unstructured (359 tokens, 324+35, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> The Clearance Event Blackout dates are January 2nd to January 15th. During this time, only Platinum members are exempt from the return restrictions on Apparel purchases.
Context-extraction layer retrieved:
  - (sim=0.700) "Separately, there's the Clearance Event Blackout from January 2nd to January 15th, which restricts A..."
  - (sim=0.656) ""What about returning apparel bought during the January clearance sale?" -- Only Platinum members ke..."
  - (sim=0.618) "The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purc..."

## M8 (mixed, leak_free=True)
**Query:** whats the exchange fee for whatever i ordered last time, and separately is that category even exchangeable or is it locked like groceries
**Expected:** $10 (Furniture, standard exchange rule); yes, allowed -- unlike Groceries, which cannot be exchanged at all.
**Why (grounding):** product_category:furniture -> rule:exchange_standard (allowed=True, fee=10) vs rule:exchange_none for groceries.
- Seed: "I bought Furniture on my last order." -> Stored: product.category = Furniture

**KG-unstructured (122 tokens, 114+8):**
> I don't have that information.

**CG-unstructured (370 tokens, 296+74, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> I'd be happy to help you with that.

To determine the exchange fee, I would need to know what category your last order falls under. If it's Groceries or Digital Goods, exchanges are not allowed, so there is no exchange fee to consider.

If it's an Electronics or Furniture item, the exchange fee is $10, as per our policy.
Context-extraction layer retrieved:
  - (sim=0.738) "As covered above, Groceries and Digital Goods support neither returns nor exchanges. There is no exc..."
  - (sim=0.705) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.703) "Exchanges are handled separately from returns and don't always follow the same rule as the return po..."

## M9 (mixed, leak_free=True)
**Query:** does warranty cover an electronics return, and can u even exchange electronics for a different model instead of refunding
**Expected:** Yes, warranty covers it; yes, exchange is allowed ($10 fee).
**Why (grounding):** product:extended_warranty covers rule:return_electronics; rule:exchange_standard allowed=True.

**KG-unstructured (416 tokens, 327+89):**
> According to our policy:

* The Extended Warranty applies to Electronics, which means it covers defect and damage claims beyond the manufacturer's warranty.
* The Standard Exchange Rule applies to Electronics, which means you can exchange an electronics product for a different model, but there is a $10 exchange fee.

So, to answer your questions: yes, the warranty covers an electronics return, and yes, you can exchange an electronics product for a different model.

**CG-unstructured (723 tokens, 636+87, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to the policy:

* The Extended Warranty applies to Electronics, and it covers "defect and damage claims beyond manufacturer's warranty". However, it does not explicitly state that it covers returns, so I don't have information on whether the warranty covers an electronics return.
* Yes, you can exchange electronics for a different model instead of refunding. The Standard Exchange Rule allows exchanges for electronics, with a $10 exchange fee.
Context-extraction layer retrieved:
  - (sim=0.690) "Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to..."
  - (sim=0.687) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.674) "A Gold-tier member buys a $300 television (Electronics) in October, outside any blackout window, and..."

## M10 (mixed, leak_free=True)
**Query:** whats the restocking fee for electronics normally and would my status change that number at all
**Expected:** $15 normally; waived to $0 for Platinum.
**Why (grounding):** rule:return_electronics fee_usd=15; tier:platinum waives fee:restocking_fee_waiver which applies_to it.
- Seed: "I am a Platinum member." -> Stored: loyalty_tier.tier = Platinum

**KG-unstructured (355 tokens, 324+31):**
> According to our policy, the standard restocking fee for electronics is $10. 

Your loyalty status does not affect the restocking fee for electronics.

**CG-unstructured (562 tokens, 531+31, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, the normal restocking fee for Electronics is $15. 

Your loyalty status does not affect the restocking fee for Electronics.
Context-extraction layer retrieved:
  - (sim=0.724) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."
  - (sim=0.707) "Electronics can be sent back within 30 days of delivery, though we do charge a $15 restocking fee to..."
  - (sim=0.702) ""Does my loyalty tier ever cover a restocking fee?" -- Only if you're Platinum. Gold covers exchange..."

## M11 (mixed, leak_free=True)
**Query:** are the exchange fees the same for electronics and furniture, and does warranty help with either one
**Expected:** Yes, both $10; no -- the warranty covers RETURNS for those categories, not the exchange fee itself, so it doesn't apply here.
**Why (grounding):** both -> rule:exchange_standard (fee=10); product:extended_warranty's covers edges point only to return rules, never exchange rules.

**KG-unstructured (433 tokens, 362+71):**
> According to our policy, the exchange fee for both Electronics and Furniture is $10, as stated in the Standard Exchange Rule.

As for the warranty, it does not directly help with exchanges, but it does apply to both Electronics and Furniture. The Extended Warranty covers defect and damage claims beyond the manufacturer's warranty, but it does not affect exchange fees.

**CG-unstructured (688 tokens, 623+65, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to our policy, yes, the exchange fees are the same for both electronics and furniture, which is $10. 

As for the warranty, it does not cover exchange fees. The warranty, specifically the Extended Warranty, covers defect and damage claims beyond the manufacturer's warranty, but it does not include exchange fees.
Context-extraction layer retrieved:
  - (sim=0.823) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.727) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."
  - (sim=0.715) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."

## M12 (mixed, leak_free=True)
**Query:** holiday sale dates again pls, and does my status specifically get me around THAT one
**Expected:** Nov 25 - Dec 5; yes, Gold is exempt from Holiday Sale specifically.
**Why (grounding):** blackout:holiday_sale dates; tier:gold exempt_from holiday_sale.
- Seed: "I am a Gold tier member." -> Stored: loyalty_tier.tier = Gold

**KG-unstructured (157 tokens, 104+53):**
> According to our policy, our holiday sale dates are from November 25th to December 1st.

As for your status, our loyalty program offers exclusive benefits to our Premium Members. However, the holiday sale dates mentioned above are not excluded for Premium Members.

**CG-unstructured (319 tokens, 274+45, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> The Holiday Sale Blackout dates are November 25th through December 5th. As a customer, I don't have information on your specific status, so I don't know if you're exempt from this blackout.
Context-extraction layer retrieved:
  - (sim=0.678) "The Holiday Sale Blackout runs November 25th through December 5th and applies to Electronics -- purc..."
  - (sim=0.654) ""If I bought electronics during the Black Friday sale, can I still return it?" -- Only if you're Gol..."
  - (sim=0.622) ""What about returning apparel bought during the January clearance sale?" -- Only Platinum members ke..."

## M13 (mixed, leak_free=True)
**Query:** whats the fee difference between exchanging groceries vs furniture, in actual dollars
**Expected:** Groceries exchanges aren't permitted at all -- there's no fee because there's no option. Furniture is $10.
**Why (grounding):** rule:exchange_none (groceries) allowed=False vs rule:exchange_standard (furniture) fee_usd=10.

**KG-unstructured (255 tokens, 245+10):**
> I don't have information about exchanging groceries.

**CG-unstructured (498 tokens, 479+19, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> There is no exchange fee for Groceries. The exchange fee for Furniture is $10.
Context-extraction layer retrieved:
  - (sim=0.774) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.684) "As covered above, Groceries and Digital Goods support neither returns nor exchanges. There is no exc..."
  - (sim=0.669) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."

## M14 (mixed, leak_free=True)
**Query:** if i do have protection coverage, walk me thru the cost if i return electronics vs furniture
**Expected:** Both covered by warranty -- the $15 Electronics fee and the $50 Furniture fee are both waived by the coverage.
**Why (grounding):** product:extended_warranty covers both rule:return_electronics and rule:return_furniture.
- Seed: "I already purchased the extended warranty." -> Stored: warranty.status = purchased

**KG-unstructured (474 tokens, 362+112):**
> If you have protection coverage, here are the costs for returning Electronics and Furniture:

**Returning Electronics:**

* Return window: 30 days (from Return Electronics policy)
* Refundable: Yes
* Fee: $15 (from Return Electronics policy)

**Returning Furniture:**

* Return window: 14 days (from Return Furniture policy)
* Refundable: Yes
* Fee: $50 (from Return Furniture policy)

Note that protection coverage does not affect the return window or refundability, but it may provide additional benefits or coverage.

**CG-unstructured (867 tokens, 680+187):**
> If you have protection coverage, here's what you can expect:

**Returning Electronics:**

* Return fee: $15 (as per the Return Electronics policy)
* Exchange fee (if you choose to exchange instead of getting a refund): $10 (as per the Standard Exchange Rule)
* If you're a Gold member, the exchange fee is waived, so you only pay the return fee of $15.

**Returning Furniture:**

* Return fee: $50 (as per the Return Furniture policy)
* Exchange fee (if you choose to exchange instead of getting a refund): $10 (as per the Standard Exchange Rule)
* If you're a Gold member, the exchange fee is waived, but you still pay the full return fee of $50.

Note that protection coverage doesn't affect the return or exchange fees, but it does provide additional benefits, such as coverage for defect and damage claims beyond the manufacturer's warranty.
Context-extraction layer retrieved:
  - (sim=0.732) "Coverage is limited to Electronics and Furniture purchases only. It doesn't apply to Apparel, Grocer..."
  - (sim=0.674) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.627) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."

## M15 (mixed, leak_free=True)
**Query:** which category has the lowest return fee, and is that the same one with the lowest exchange fee too
**Expected:** Lowest return fee ($0): Apparel (Groceries/Digital Goods aren't $0 -- they're simply not returnable at all, a different thing). Lowest exchange fee ($0): also Apparel. Same category.
**Why (grounding):** rule:return_apparel fee_usd=0 vs return_groceries/digital_goods refundable=False (not comparable as a '$' figure); rule:exchange_free (apparel) fee_usd=0 vs exchange_none (groceries/digital) allowed=False.

**KG-unstructured (145 tokens, 108+37):**
> According to our return and exchange policy, the lowest return fee is $5.99 for all categories. 

The lowest exchange fee is also $5.99 for all categories.

**CG-unstructured (378 tokens, 317+61, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> According to the policy, the Electronics category has the lowest return fee, which is $15. However, the lowest exchange fee is actually $10, which applies to both Electronics and Furniture categories. So, the exchange fee is the same for both categories, but the return fee is lower in Electronics.
Context-extraction layer retrieved:
  - (sim=0.709) "If a customer would rather swap an electronics item for something else instead of getting a refund, ..."
  - (sim=0.702) "Exchanges are handled separately from returns and don't always follow the same rule as the return po..."
  - (sim=0.688) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."

## M16 (mixed, leak_free=True)
**Query:** given my status would either fee get waived on an electronics order or am i paying both fees straight up
**Expected:** Pay both in full -- Bronze has no waivers of any kind.
**Why (grounding):** tier:bronze has no waives edges at all.
- Seed: "I am a Bronze member." -> Stored: loyalty_tier.tier = Bronze

**KG-unstructured (372 tokens, 326+46):**
> As a Gold loyalty tier member, you are exempt from the Holiday Sale Blackout, but that doesn't directly affect the exchange fees. However, I don't have information on whether your loyalty tier status affects the exchange fees.

**CG-unstructured (586 tokens, 531+55, FELL BACK: no stored decision trace matched this question, structurally or by similarity):**
> You are a Gold member. According to the policy, Gold members get their exchange fee waived, but they still pay the full restocking fee. So, on an electronics order, you would pay the restocking fee ($15) but the exchange fee would be waived.
Context-extraction layer retrieved:
  - (sim=0.639) "Only Platinum members get the restocking fee waived. Platinum also covers the exchange fee waiver to..."
  - (sim=0.619) ""I'm Silver tier, do I get any fee breaks?" -- No, Bronze and Silver have identical fee treatment: f..."
  - (sim=0.606) "Gold members get their exchange fee waived -- that's the $10 fee mentioned above for both Electronic..."
