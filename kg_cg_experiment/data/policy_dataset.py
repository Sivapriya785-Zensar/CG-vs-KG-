

NODES = [
    # Product categories
    {"id": "product_category:electronics", "type": "ProductCategory", "label": "Electronics",
     "aliases": ["electronics", "electronic item", "gadget", "tech product"]},
    {"id": "product_category:apparel", "type": "ProductCategory", "label": "Apparel",
     "aliases": ["apparel", "clothing", "clothes", "garment"]},
    {"id": "product_category:furniture", "type": "ProductCategory", "label": "Furniture",
     "aliases": ["furniture", "sofa", "table", "chair"]},
    {"id": "product_category:groceries", "type": "ProductCategory", "label": "Groceries",
     "aliases": ["groceries", "grocery", "food item", "perishable"]},
    {"id": "product_category:digital_goods", "type": "ProductCategory", "label": "Digital Goods",
     "aliases": ["digital goods", "digital product", "downloadable item", "digital download"]},

    # Return policies
    {"id": "rule:return_electronics", "type": "ReturnRule", "label": "Electronics Return Rule",
     "aliases": ["return electronics", "returning electronics", "electronics return", "electronics refund"],
     "attrs": {"refundable": True, "fee_usd": 15, "window_days": 30}},
    {"id": "rule:return_apparel", "type": "ReturnRule", "label": "Apparel Return Rule",
     "aliases": ["return apparel", "returning apparel", "apparel return", "clothing return", "clothing refund"],
     "attrs": {"refundable": True, "fee_usd": 0, "window_days": 45}},
    {"id": "rule:return_furniture", "type": "ReturnRule", "label": "Furniture Return Rule",
     "aliases": ["return furniture", "returning furniture", "furniture return", "furniture refund"],
     "attrs": {"refundable": True, "fee_usd": 50, "window_days": 14}},
    {"id": "rule:return_groceries", "type": "ReturnRule", "label": "Groceries Return Rule",
     "aliases": ["return groceries", "returning groceries", "grocery return", "grocery refund"],
     "attrs": {"refundable": False, "fee_usd": None, "note": "Non-returnable due to perishability, no exceptions."}},
    {"id": "rule:return_digital_goods", "type": "ReturnRule", "label": "Digital Goods Return Rule",
     "aliases": ["return digital goods", "digital goods return", "digital product refund"],
     "attrs": {"refundable": False, "fee_usd": None, "note": "Non-returnable once downloaded or activated."}},

    # Exchange policies
    {"id": "rule:exchange_none", "type": "ExchangeRule", "label": "No Exchange Rule",
     "aliases": ["exchange groceries", "exchange digital goods", "exchange digital product"],
     "attrs": {"allowed": False, "fee_usd": None}},
    {"id": "rule:exchange_standard", "type": "ExchangeRule", "label": "Standard Exchange Rule",
     "aliases": ["exchange electronics", "exchange furniture", "exchange fee",
                 "exchange my item", "exchange my order", "product exchange"],
     "attrs": {"allowed": True, "fee_usd": 10}},
    {"id": "rule:exchange_free", "type": "ExchangeRule", "label": "Free Exchange Rule",
     "aliases": ["exchange apparel", "exchange clothing", "size exchange", "clothing exchange"],
     "attrs": {"allowed": True, "fee_usd": 0}},

    # Loyalty tiers
    {"id": "tier:bronze", "type": "LoyaltyTier", "label": "Bronze",
     "aliases": ["bronze tier", "bronze member", "bronze status", "no status", "base tier"]},
    {"id": "tier:silver", "type": "LoyaltyTier", "label": "Silver",
     "aliases": ["silver tier", "silver member", "silver status"]},
    {"id": "tier:gold", "type": "LoyaltyTier", "label": "Gold",
     "aliases": ["gold tier", "gold member", "gold status"]},
    {"id": "tier:platinum", "type": "LoyaltyTier", "label": "Platinum",
     "aliases": ["platinum tier", "platinum member", "platinum status"]},

    # Promo blackouts
    {"id": "blackout:holiday_sale", "type": "PromoBlackout", "label": "Holiday Sale Blackout",
     "aliases": ["holiday sale blackout", "black friday blackout", "holiday sale period", "black friday", "holiday sale"],
     "attrs": {"dates": "Nov 25 - Dec 5"}},
    {"id": "blackout:clearance_event", "type": "PromoBlackout", "label": "Clearance Event Blackout",
     "aliases": ["clearance event blackout", "clearance sale blackout", "post-holiday clearance", "clearance period", "clearance event"],
     "attrs": {"dates": "Jan 2 - Jan 15"}},

    # Fees / waivers
    {"id": "fee:exchange_fee_waiver", "type": "Fee", "label": "Exchange Fee Waiver",
     "aliases": ["exchange fee waiver", "waived exchange fee"]},
    {"id": "fee:restocking_fee_waiver", "type": "Fee", "label": "Restocking Fee Waiver",
     "aliases": ["restocking fee waiver", "waived restocking fee", "restocking fee"]},

    # Extended warranty
    {"id": "product:extended_warranty", "type": "WarrantyProduct", "label": "Extended Warranty",
     "aliases": ["extended warranty", "warranty plan", "protection plan", "warranty"],
     "attrs": {"cost_usd": 25, "covers": "defect and damage claims beyond the manufacturer warranty period"}},
]

EDGES = [
    ("product_category:electronics", "rule:return_electronics", "has_return_policy"),
    ("product_category:apparel", "rule:return_apparel", "has_return_policy"),
    ("product_category:furniture", "rule:return_furniture", "has_return_policy"),
    ("product_category:groceries", "rule:return_groceries", "has_return_policy"),
    ("product_category:digital_goods", "rule:return_digital_goods", "has_return_policy"),

    ("product_category:electronics", "rule:exchange_standard", "has_exchange_policy"),
    ("product_category:furniture", "rule:exchange_standard", "has_exchange_policy"),
    ("product_category:apparel", "rule:exchange_free", "has_exchange_policy"),
    ("product_category:groceries", "rule:exchange_none", "has_exchange_policy"),
    ("product_category:digital_goods", "rule:exchange_none", "has_exchange_policy"),

    ("tier:gold", "fee:exchange_fee_waiver", "waives"),
    ("tier:platinum", "fee:exchange_fee_waiver", "waives"),
    ("tier:platinum", "fee:restocking_fee_waiver", "waives"),

    ("fee:exchange_fee_waiver", "rule:exchange_standard", "applies_to"),
    ("fee:restocking_fee_waiver", "rule:return_electronics", "applies_to"),
    ("fee:restocking_fee_waiver", "rule:return_furniture", "applies_to"),

    ("blackout:holiday_sale", "product_category:electronics", "restricts"),
    ("blackout:clearance_event", "product_category:apparel", "restricts"),

    ("tier:gold", "blackout:holiday_sale", "exempt_from"),
    ("tier:platinum", "blackout:holiday_sale", "exempt_from"),
    ("tier:platinum", "blackout:clearance_event", "exempt_from"),

    ("product:extended_warranty", "rule:return_electronics", "covers"),
    ("product:extended_warranty", "rule:return_furniture", "covers"),
]
