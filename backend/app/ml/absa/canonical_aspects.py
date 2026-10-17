"""
ml/absa/canonical_aspects.py — Enterprise Canonical Aspect Definitions
----------------------------------------------------------------------
Enforces Enterpret-style 8 fixed product dimensions + General + Miscellaneous:
  - Quality: Durability, craftsmanship, defects, material integrity
  - Price: Cost, value for money, subscription pricing, discounts
  - Service: Customer support, warranty response, refund handling
  - Delivery: Logistics, shipping speed, delivery condition, transit delays
  - Battery: Battery life, charging speed, battery drain, capacity degradation
  - Performance: Speed, responsiveness, latency, overheating, crashes/bugs
  - Design: Ergonomics, aesthetics, weight, size, color, build form factor
  - Packaging: Unboxing experience, package damage, protective wrap, seal integrity
  - General: Overall sentiment/praise without attribute specificity ("Love this product")
  - Miscellaneous: Specific complaints with no current taxonomy match (HDBSCAN nursery bucket)
"""
from typing import Dict, List, Set

CANONICAL_ASPECTS: List[str] = [
    "Quality",
    "Price",
    "Service",
    "Delivery",
    "Battery",
    "Performance",
    "Design",
    "Packaging",
]

SPECIAL_NODES: List[str] = [
    "General",
    "Miscellaneous",
]

ALL_ASPECTS: List[str] = CANONICAL_ASPECTS + SPECIAL_NODES

# Calibrated classification routing threshold:
# Sentences with max aspect probability below this route to Miscellaneous
MISCELLANEOUS_THRESHOLD: float = 0.45

# Explicit domain keyword vocabulary for fast lexical matching and token span extraction
ASPECT_KEYWORDS: Dict[str, List[str]] = {
    "Quality": [
        "quality", "durability", "material", "build", "craftsmanship", "broke",
        "broken", "durable", "sturdy", "flimsy", "cheap", "plastic", "defective",
        "defect", "scratched", "scratch", "crack", "cracked", "faulty", "solid",
        "well-made", "premium", "reliable", "reliability", "tear", "wear",
    ],
    "Price": [
        "price", "cost", "value", "worth", "expensive", "cheap", "overpriced",
        "affordable", "deal", "discount", "penny", "money", "bargain", "rip-off",
        "ripoff", "pricing", "rate", "charge", "economic", "budget", "economical",
    ],
    "Service": [
        "service", "support", "customer support", "representative", "help",
        "warranty", "refund", "return", "replacement", "agent", "email", "call",
        "reps", "assistance", "response", "ticket", "staff", "desk", "chat",
    ],
    "Delivery": [
        "delivery", "shipping", "shipped", "arrived", "arrival", "package",
        "transit", "courier", "tracking", "fedex", "ups", "usps", "dhl",
        "bluedart", "delay", "delayed", "late", "fast", "on-time", "dispatch",
    ],
    "Battery": [
        "battery", "charge", "charging", "charger", "mah", "drain", "power",
        "cable", "port", "usb-c", "plug", "recharge", "life", "hours",
        "runtime", "drainage", "standby", "recharging",
    ],
    "Performance": [
        "performance", "speed", "fast", "slow", "lag", "laggy", "latency",
        "smooth", "fluid", "responsive", "unresponsive", "crash", "crashed",
        "crashes", "freeze", "freezes", "bug", "glitch", "hot", "overheat",
        "overheating", "warm", "fan", "audio", "sound", "volume", "connection",
        "bluetooth", "wifi", "sync",
    ],
    "Design": [
        "design", "look", "looks", "appearance", "aesthetic", "style", "color",
        "size", "weight", "heavy", "light", "compact", "bulky", "ergonomic",
        "ergonomics", "grip", "fit", "comfortable", "comfort", "button",
        "buttons", "display", "screen", "finish",
    ],
    "Packaging": [
        "packaging", "box", "package", "unbox", "unboxing", "wrap", "wrapped",
        "bubble wrap", "seal", "sealed", "tape", "dented", "dented box", "crushed box",
        "container", "pack",
    ],
    "General": [
        "product", "item", "purchase", "buy", "everything", "overall", "experience",
        "recommend", "worth it", "good", "bad", "great", "terrible", "awesome",
        "horrible", "best", "worst", "satisfied", "disappointed",
    ],
}

# Semantic patterns capturing implicit functional statements (zero explicit noun mentions)
IMPLICIT_PATTERNS: Dict[str, List[str]] = {
    "Battery": [
        "shut off after", "shuts off after", "stopped holding a charge",
        "won't hold a charge", "wont hold a charge", "dead after 20 minutes",
        "dies in minutes", "dies after", "drains quickly", "drains so fast",
        "loses charge", "runs out of juice", "takes forever to juice up",
        "died within an hour", "lasted only two hours", "lasts all week",
        "all day runtime", "won't turn on unless plugged in",
    ],
    "Delivery": [
        "took three weeks", "took 3 weeks", "took a month", "never arrived",
        "still waiting after", "showed up two weeks late", "tracking was stuck",
        "tracking never updated", "left out in the rain", "arrived broken at doorstep",
        "delivered to the wrong address",
    ],
    "Quality": [
        "fell apart", "snapped in half", "fell off on day two", "came loose",
        "peeling off", "stopped working suddenly", "buttons jammed",
        "feels like cheap junk", "creaking sound", "feels flimsy in hand",
        "rattling inside", "looks like it will break any minute",
    ],
    "Packaging": [
        "looked like it was run over by a truck", "box was completely crushed",
        "no protective padding inside", "seal was already broken",
        "arrived with tape ripped open", "box had a gaping hole", "arrived dented",
    ],
    "Price": [
        "not worth a single penny", "absolute waste of money", "feels like daylight robbery",
        "paid way too much for this", "punch above its weight for the price",
        "unbeatable for this price point", "bang for the buck",
    ],
    "Service": [
        "hung up on me", "never replied to my emails", "refused to honor their promise",
        "no one picked up", "gave me the runaround", "automated bot was useless",
        "helped me immediately without hassle", "agent was polite and resolved it",
    ],
    "Performance": [
        "stutters constantly", "freezes every few minutes", "takes forever to load",
        "gets uncomfortably warm", "burned my lap", "sound cuts out randomly",
        "keeps dropping connection", "delayed input", "glitches out",
    ],
    "Design": [
        "too bulky for my pockets", "hurts my ears after 10 minutes",
        "uncomfortable to hold", "awkward to carry around", "fingerprint magnet",
        "looks sleek on my desk", "fits like a glove",
    ],
}
