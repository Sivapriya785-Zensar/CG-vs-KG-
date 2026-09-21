"""
Generates a ~2000-row realistic retail product catalog on top of the SAME
category-level policy rules used everywhere else in this project (returns,
exchanges, loyalty waivers, blackouts, warranty). Nothing about the actual
POLICY changes here -- this only adds many named, described products under
each category, the way a real retailer's catalog would, so the unstructured
document has real scale and real retail flavor (not just a policy page) to
test chunk-retrieval against.

Deliberately additive: does not touch data/policy_dataset.py or
data/unstructured_policy_document.py, so the existing 50-question experiment
stays reproducible exactly as before.

Each SKU inherits its policy purely from its category -- there is no
per-SKU exception -- so grading a question about any SKU only requires
knowing which category it belongs to, same mechanism as the original
5-category dataset, just with many more named, described entry points.
"""
import random

random.seed(42)  # deterministic catalog, reproducible across runs

CATEGORY_SUBLINES = {
    "Electronics": [
        "TV", "Laptop", "Smartphone", "Tablet", "Headphones", "Speaker",
        "Smartwatch", "Camera", "Gaming Console", "Router", "Monitor",
        "Printer", "External Hard Drive", "Webcam", "Drone", "E-Reader",
        "Projector", "Soundbar", "Fitness Tracker", "Power Bank",
    ],
    "Apparel": [
        "T-Shirt", "Jeans", "Jacket", "Dress", "Sweater", "Shorts",
        "Sneakers", "Boots", "Hat", "Scarf", "Gloves", "Socks",
        "Pajamas", "Swimsuit", "Coat", "Skirt", "Blouse", "Hoodie",
        "Belt", "Sandals",
    ],
    "Furniture": [
        "Sofa", "Dining Table", "Office Chair", "Bookshelf", "Bed Frame",
        "Coffee Table", "Wardrobe", "TV Stand", "Recliner", "Nightstand",
        "Desk", "Bar Stool", "Ottoman", "Dresser", "Bench", "Bunk Bed",
        "Patio Set", "Filing Cabinet", "Shoe Rack", "Console Table",
    ],
    "Groceries": [
        "Coffee Beans", "Pasta", "Olive Oil", "Cereal", "Rice", "Spice Set",
        "Snack Box", "Tea Sampler", "Honey Jar", "Granola", "Peanut Butter",
        "Chocolate Box", "Canned Soup", "Dried Fruit Mix", "Baking Kit",
        "Sauce Bundle", "Juice Pack", "Cookie Tin", "Cheese Selection",
        "Frozen Meal Kit",
    ],
    "Digital Goods": [
        "eBook", "Movie Download", "Software License", "Game Key",
        "Music Album", "Online Course", "Audiobook", "Stock Photo Pack",
        "Font Bundle", "App Subscription", "Cloud Storage Plan",
        "Antivirus License", "VPN Subscription", "Digital Gift Card",
        "Streaming Pass",
    ],
}

BRANDS = [
    "Northline", "Cascade", "Ember", "Voyager", "Alderwood", "Solace",
    "Highmark", "Pinegrove", "Vantage", "Meridian", "Brightside", "Kestrel",
    "Fernbrook", "Ironclad", "Lucent", "Rosemont", "Driftwood", "Anchorpoint",
    "Windward", "Sablefield",
]

# Short, generic-but-real selling-point phrases per category, combined with
# the subline to produce a one-line description -- real retail catalog
# flavor, not just a bare product name. No policy facts embedded here (those
# only ever come from the category, never per-SKU) so grading stays clean.
DESCRIPTORS = {
    "Electronics": [
        "with fast charging and a 2-year manufacturer warranty",
        "featuring wireless connectivity and voice control support",
        "built for everyday use with a durable aluminum housing",
        "with an upgraded processor for smoother multitasking",
        "designed for home and office use with quiet operation",
    ],
    "Apparel": [
        "made from breathable, machine-washable fabric",
        "available in multiple colors, true to size",
        "designed for year-round comfort and easy layering",
        "with a relaxed fit and reinforced stitching",
        "part of this season's everyday essentials line",
    ],
    "Furniture": [
        "with a solid wood frame and stain-resistant finish",
        "flat-packed for easy home assembly",
        "designed to fit compact living spaces",
        "upholstered in easy-clean fabric",
        "built for daily use with a 5-year structural warranty from the manufacturer",
    ],
    "Groceries": [
        "sourced from small-batch suppliers",
        "a pantry staple, sold in a resealable package",
        "naturally gluten-free and non-GMO",
        "a customer favorite for weekday meals",
        "packaged in eco-friendly, recyclable materials",
    ],
    "Digital Goods": [
        "delivered instantly via email after purchase",
        "compatible with most major devices and platforms",
        "includes lifetime access to future minor updates",
        "downloadable immediately, no physical shipping required",
        "activated with a one-time code sent to your account",
    ],
}


def generate_catalog(target_rows: int = 2000) -> list[dict]:
    """Returns a list of {sku_id, name, category, brand, price_usd,
    description} rows, evenly spread across the 5 policy categories."""
    rows = []
    per_category = target_rows // len(CATEGORY_SUBLINES)
    sku_counter = 1

    for category, sublines in CATEGORY_SUBLINES.items():
        descriptors = DESCRIPTORS[category]
        for i in range(per_category):
            subline = sublines[i % len(sublines)]
            brand = BRANDS[(i * 7 + len(category)) % len(BRANDS)]
            model_num = 100 + (i % 900)
            name = f"{brand} {subline} {model_num}"
            price = round(random.uniform(8, 1800), 2)
            descriptor = descriptors[i % len(descriptors)]
            rows.append({
                "sku_id": f"SKU-{sku_counter:05d}",
                "name": name,
                "category": category,
                "brand": brand,
                "price_usd": price,
                "description": f"{name} ({category}) -- {descriptor}. Priced at ${price:.2f}.",
            })
            sku_counter += 1

    return rows


if __name__ == "__main__":
    catalog = generate_catalog()
    print(f"Generated {len(catalog)} SKUs across {len(CATEGORY_SUBLINES)} categories")
    print("\nSample entries:")
    for row in catalog[:3] + catalog[400:403]:
        print(" ", row["description"])
