"""
Static catalog of shopping/booking platforms, plus a deterministic
"fallback" recommendation generator used when Gemini is not configured
or fails.
"""
from urllib.parse import quote_plus

PLATFORMS = {
    "Amazon": "https://www.amazon.in/s?k={}",
    "Flipkart": "https://www.flipkart.com/search?q={}",
    "IKEA": "https://www.ikea.com/in/en/search/?q={}",
    "Swiggy": "https://www.swiggy.com/search?query={}",
    "Zomato": "https://www.zomato.com/search?query={}",
    "OYO": "https://www.oyorooms.com/search?location={}",
}


def search_url(platform: str, query: str) -> str:
    template = PLATFORMS.get(platform, PLATFORMS["Amazon"])
    return template.format(quote_plus(query))


def fallback(planner: str, data: dict) -> dict:
    """Deterministic, budget-proportional recommendations (no AI required)."""
    budget = float(data["budget"])

    if planner == "home":
        specs = [
            ("Lighting", "Warm LED ceiling light", "IKEA", budget * 0.10),
            ("Furniture", "Compact multipurpose table", "Amazon", budget * 0.30),
            ("Seating", "Accent chair", "Flipkart", budget * 0.25),
            ("Decor", "Wall art / decor set", "IKEA", budget * 0.15),
        ]
        allocation = {
            "furniture": budget * 0.45,
            "lighting": budget * 0.15,
            "decor": budget * 0.20,
            "reserve": budget * 0.20,
        }
    elif planner == "party":
        specs = [
            ("Catering", "Catering package", "Swiggy", budget * 0.40),
            ("Food", "Restaurant / event food options", "Zomato", budget * 0.15),
            ("Decoration", "Theme decoration supplies", "Amazon", budget * 0.15),
            ("Venue", "Venue / accommodation search", "OYO", budget * 0.20),
        ]
        allocation = {
            "catering": budget * 0.55,
            "decoration": budget * 0.15,
            "entertainment": budget * 0.10,
            "venue": budget * 0.20,
        }
    else:  # jewelry
        specs = [
            ("Necklace", "Occasion-appropriate necklace", "Amazon", budget * 0.35),
            ("Earrings", "Matching earrings", "Flipkart", budget * 0.20),
            ("Bangles", "Complementary bangles", "Amazon", budget * 0.15),
            ("Set", "Coordinated jewellery set", "Flipkart", budget * 0.25),
        ]
        allocation = {
            "necklace": budget * 0.35,
            "earrings": budget * 0.20,
            "bangles": budget * 0.15,
            "reserve": budget * 0.30,
        }

    recommendations = [
        {
            "name": name,
            "category": category,
            "platform": platform,
            "estimated_price": round(price, 2),
            "reason": "Fallback estimate; verify live price and availability before purchasing.",
            "search_url": search_url(platform, name),
        }
        for category, name, platform, price in specs
    ]

    return {
        "planner": planner,
        "budget": budget,
        "allocation": {key: round(value, 2) for key, value in allocation.items()},
        "recommendations": recommendations,
        "tips": [
            "Compare listings across platforms before buying.",
            "Prices and availability can change at any time.",
            "Keep a small reserve for unexpected costs.",
        ],
        "disclaimer": "Prices are estimates unless a live commerce API is connected.",
        "ai_used": False,
    }
