"""Every event Blockhaven has run, in the order it ran them.

Blockhaven opened on New Year's Day 2022 and has kept the calendar ever
since: New Year, St. Patrick's Day, Easter, the Fourth of July, Halloween
and Christmas, every year.  Each holiday has a module of its own with one
``kit.Event`` per year:

=========  ===========================================================
newyear     2022 (the launch) ... 2026, each from New Year's Eve
stpatricks  2022 ... 2026, the week either side of March 17th
easter      2022 ... 2026, nine days either side of Easter Sunday
july4       2022 ... 2026, the week before and after the Fourth
halloween   2022 ... 2026 -- 2026 is the Hallowed Harvest, running now
christmas   2022 ... 2025, and 2026 waiting for December
=========  ===========================================================

``EVENTS`` is all of them in date order, which is also the order of their
crates' series numbers (Series #1 is the Blockhaven Hat Crate, which was
there on opening day).  Nothing outside this package needs to know how an
event is put together: app/models/crates.py turns each one into a series,
an event, offers and a badge, and app/models/catalog.py takes its items.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .kit import Event
from . import christmas, easter, halloween, july4, newyear, stpatricks

HOLIDAYS = [
    {"id": "newyear", "name": "New Year", "icon": "clock",
     "blurb": "Midnight, every year since the very first one."},
    {"id": "stpatricks", "name": "St. Patrick's Day", "icon": "shamrock",
     "blurb": "A leprechaun, a pot of gold and whatever he left behind."},
    {"id": "easter", "name": "Easter", "icon": "egg",
     "blurb": "Eggs, bunnies, and chocolate in quantities nobody should eat."},
    {"id": "july4", "name": "Fourth of July", "icon": "firework",
     "blurb": "Fireworks, flags and the cookout that gets out of hand."},
    {"id": "halloween", "name": "Halloween", "icon": "pumpkin",
     "blurb": "The lamps go out across the server, one October at a time."},
    {"id": "christmas", "name": "Christmas", "icon": "snowflake",
     "blurb": "Snow on everything, and a crate under every tree."},
]
HOLIDAY_IDS = [h["id"] for h in HOLIDAYS]

EVENTS: List[Event] = sorted(
    newyear.EVENTS + stpatricks.EVENTS + easter.EVENTS + july4.EVENTS
    + halloween.EVENTS + christmas.EVENTS,
    key=lambda e: (e.starts, e.id))
BY_ID: Dict[str, Event] = {e.id: e for e in EVENTS}

# Each holiday's editions numbered from the first (Halloween 2022 is the
# 1st Halloween), so a card can say "5th annual".
for _holiday in HOLIDAY_IDS:
    for _n, _event in enumerate([e for e in EVENTS if e.holiday == _holiday], 1):
        _event.edition = _n


def all_items() -> List[Dict[str, Any]]:
    """Every catalogue item the events brought, crates and keys first."""
    out: List[Dict[str, Any]] = []
    for event in EVENTS:
        if event.key:
            out.append(event.key)
        if event.crate:
            out.append(event.crate)
    for event in EVENTS:
        out.extend(event.items)
    return out


def all_effects() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for event in EVENTS:
        out.update(event.effects)
    return out


def ordinal(n: int) -> str:
    return "%d%s" % (n, "th" if 10 <= n % 100 <= 20 else
                     {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))
