#!/usr/bin/env python3
"""The Crate Vault's rules, checked offline (no server):

    python3 tools/storetests.py

What the market lists and what it will sell must be the same thing: the live
event's crate and key, everyday gear, and -- once an event is over -- its
collection in the archive, bar its hats.  Nothing upcoming, no hat ever.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop("BLOCKHAVEN_EVENTS", None)

from app.models import catalog, crates, market, store  # noqa: E402

PASSED = FAILED = 0


def check(name: str, ok: bool, detail: object = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print("  PASS  " + name)
    else:
        FAILED += 1
        print("  FAIL  %s  %r" % (name, detail))


def main() -> int:
    now = int(time.time())
    states = {eid: crates.event_state(eid, now) for eid in crates.EVENTS}
    past = sorted((e for e, s in states.items() if s == "past"), key=lambda e: crates.EVENTS[e]["starts"])
    upcoming = [e for e, s in states.items() if s == "upcoming"]
    live = [e for e, s in states.items() if s == "live"]

    print("== the shelf and the till agree ==")
    sellable = [it for it in catalog.ALL_ITEMS if crates.for_sale(it, now)]
    check("no hat is ever for sale", not [it["id"] for it in sellable if it["slot"] == "hat"],
          [it["id"] for it in sellable if it["slot"] == "hat"][:5])
    up_items = [it["id"] for it in sellable if it.get("event") in upcoming]
    check("nothing from an upcoming event is for sale", not up_items, up_items[:5])
    if past:
        old = crates.EVENTS[past[0]]
        series = crates.SERIES.get(old.get("series", ""), {})
        crate_item = catalog.get(series.get("crate", ""))
        check("an archive crate is for sale", bool(crate_item) and crates.for_sale(crate_item, now),
              series.get("crate"))
        old_hats = [it for it in catalog.ALL_ITEMS if it.get("event") == past[0] and it["slot"] == "hat"]
        check("an archive hat is still crate-only",
              bool(old_hats) and not any(crates.for_sale(h, now) for h in old_hats))
    if live:
        live_hats = [it for it in catalog.ALL_ITEMS if it.get("event") in live and it["slot"] == "hat"]
        check("a live event's hats are crate-only", not any(crates.for_sale(h, now) for h in live_hats))

    print("\n== what the aisles show ==")
    plain = market.listing("all")
    check("the plain aisles leave the archive to the Crate Hall",
          not [c for c in plain if states.get((catalog.get(c["id"]) or {}).get("event", ""), "") == "past"])
    if past:
        name = catalog.get(crates.SERIES[crates.EVENTS[past[0]]["series"]]["crate"])["name"]
        found = market.listing("all", search=name.split()[0])
        check("a search reaches into the archive", any(c["name"] == name for c in found), name)
    event_aisle = market.listing("event")
    check("the event aisle is the live event's things only",
          all(states.get((catalog.get(c["id"]) or {}).get("event", ""), "") == "live" for c in event_aisle),
          [c["id"] for c in event_aisle][:5])
    check("archive_count counts the archive", market.archive_count(now) > 0 if past else True)

    print("\n== the Crate Hall ==")
    wings = store.wings(now, {}, {})
    check("one wing per holiday plus Classic", len(wings) >= 7, [w.get("id") for w in wings])
    check("exactly one wing is selected", sum(1 for w in wings if w.get("selected")) == 1)
    if live:
        first = wings[0]
        check("the live event's holiday is the first wing",
              first.get("id") == crates.EVENTS[live[0]].get("holiday"), first.get("id"))

    print("\n" + "=" * 20 + " %d passed, %d failed " % (PASSED, FAILED) + "=" * 20)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
