"""AI planner prototype for TekunoAI Event Management.

`suggest_plan` is deterministic and rule-based in this MVP: it uses only
the Python standard library and makes no external calls. Its return shape
is the contract a future LLM-backed planner will keep.
"""
from __future__ import annotations

import math
from typing import Optional


_TEMPLATES = {
    "corporate": {
        "vendors": ["venue", "catering", "av", "photography", "signage"],
        "timeline": [
            ("Setup and AV check", 60),
            ("Guest arrival and registration", 30),
            ("Welcome and keynote", 45),
            ("Main session / launch", 60),
            ("Networking and refreshments", 45),
            ("Closing remarks", 15),
            ("Teardown", 45),
        ],
        "budget": {"venue": 25, "catering": 30, "av": 15, "decor": 5,
                   "entertainment": 5, "contingency": 10, "other": 10},
        "tasks": ["Book venue", "Confirm AV requirements", "Order catering",
                  "Prepare registration list", "Brief speakers"],
    },
    "wedding": {
        "vendors": ["venue", "catering", "photography", "decor", "entertainment", "av"],
        "timeline": [
            ("Setup and decor", 120),
            ("Guest arrival", 30),
            ("Ceremony", 45),
            ("Photos and refreshments", 45),
            ("Reception and dinner", 90),
            ("Entertainment and dancing", 90),
            ("Send-off and teardown", 45),
        ],
        "budget": {"venue": 30, "catering": 30, "av": 5, "decor": 12,
                   "entertainment": 8, "contingency": 10, "other": 5},
        "tasks": ["Book venue", "Book photographer", "Order catering and cake",
                  "Arrange decor", "Confirm entertainment"],
    },
    "birthday": {
        "vendors": ["venue", "catering", "decor", "entertainment", "photography"],
        "timeline": [
            ("Setup and decor", 60),
            ("Guest arrival", 20),
            ("Welcome and activities", 60),
            ("Food and cake", 45),
            ("Games / entertainment", 45),
            ("Wrap-up and teardown", 30),
        ],
        "budget": {"venue": 20, "catering": 35, "av": 5, "decor": 15,
                   "entertainment": 10, "contingency": 10, "other": 5},
        "tasks": ["Book venue or confirm home setup", "Order food and cake",
                  "Arrange decor", "Plan activities"],
    },
    "conference": {
        "vendors": ["venue", "catering", "av", "photography", "signage", "printing"],
        "timeline": [
            ("Setup and AV check", 90),
            ("Registration", 45),
            ("Keynote", 60),
            ("Sessions block 1", 90),
            ("Lunch", 60),
            ("Sessions block 2", 90),
            ("Panel and closing", 45),
            ("Teardown", 45),
        ],
        "budget": {"venue": 30, "catering": 25, "av": 20, "decor": 3,
                   "entertainment": 2, "contingency": 10, "other": 10},
        "tasks": ["Book venue", "Confirm speakers", "Set up registration",
                  "Test AV and streaming", "Print badges and signage"],
    },
}

_GENERIC = {
    "vendors": ["venue", "catering", "av", "photography"],
    "timeline": [
        ("Setup", 60),
        ("Guest arrival", 30),
        ("Main programme", 90),
        ("Food and social time", 60),
        ("Wrap-up and teardown", 45),
    ],
    "budget": {"venue": 25, "catering": 30, "av": 10, "decor": 10,
               "entertainment": 5, "contingency": 10, "other": 10},
    "tasks": ["Book venue", "Order catering", "Confirm programme", "Arrange teardown help"],
}


def suggest_plan(event_type: str, guest_count: int,
                 budget_total: Optional[float] = None) -> dict:
    """Suggest an event plan from event type and guest count.

    Args:
        event_type: e.g. "corporate", "wedding", "birthday", "conference".
            Unknown types fall back to a generic template.
        guest_count: expected number of guests (must be >= 1).
        budget_total: optional total budget; if given, allocation amounts
            are included alongside percentages.

    Returns:
        A dictionary describing the suggested plan.
    """
    if guest_count < 1:
        raise ValueError("guest_count must be at least 1")
    key = (event_type or "generic").strip().lower()
    template = _TEMPLATES.get(key, _GENERIC)

    capacity = guest_count + int(math.ceil(guest_count * 0.1))  # 10% headroom
    coordinators = max(1, math.ceil(guest_count / 75))
    hosts = max(1, math.ceil(guest_count / 50))
    support = max(1, math.ceil(guest_count / 40))

    allocation_pct = dict(template["budget"])
    allocation_amounts = None
    if budget_total is not None:
        if budget_total < 0:
            raise ValueError("budget_total cannot be negative")
        allocation_amounts = {
            k: round(budget_total * pct / 100, 2)
            for k, pct in allocation_pct.items()
        }

    timeline = [
        {"block": name, "duration_minutes": minutes}
        for name, minutes in template["timeline"]
    ]
    total_minutes = sum(minutes for _, minutes in template["timeline"])

    tips = [
        "Confirm vendor arrival times at least 48 hours before the event.",
        "Keep a 10% contingency in the budget for last-minute costs.",
    ]
    if guest_count >= 200:
        tips.append("For 200+ guests, add a second registration / entry point.")
    if guest_count >= 100:
        tips.append("For 100+ guests, assign a dedicated coordinator for vendors.")
    if key == "conference":
        tips.append("Test AV and any live stream the day before, not on the day.")

    return {
        "event_type": key,
        "guest_count": guest_count,
        "venue_capacity_recommended": capacity,
        "staffing": {
            "coordinators": coordinators,
            "hosts": hosts,
            "support_staff": support,
        },
        "vendor_checklist": list(template["vendors"]),
        "timeline": timeline,
        "estimated_total_minutes": total_minutes,
        "starter_tasks": list(template["tasks"]),
        "budget_allocation_percent": allocation_pct,
        "budget_allocation_amounts": allocation_amounts,
        "catering_note": (
            f"Plan catering for {capacity} covers (guest count plus headroom); "
            "confirm dietary needs from RSVPs before finalising quantities."
        ),
        "risks_and_tips": tips,
        "planner": "rule-based prototype (LLM-backed planner on roadmap)",
    }
