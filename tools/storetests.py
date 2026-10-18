#!/usr/bin/env python3
"""The Crate Vault's rules, checked offline against a throwaway database
(no server):

    python3 tools/storetests.py

What the market lists and what it will sell must be the same thing: the live
event's crate and key, everyday gear, and -- once an event is over -- its
collection in the archive, bar its hats.  Nothing upcoming, no hat ever.  A
past event's weapons and held items are in the Event Armory at one premium
price, the same on every shelf, at the till and in the sell-back.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop("BLOCKHAVEN_EVENTS", None)

from app import config, db  # noqa: E402

# a database of its own, so the till checks never touch data/blockhaven.sqlite3
config.DB_PATH = pathlib.Path(tempfile.mkdtemp(prefix="bh-storetests-")) / "store.sqlite3"

from app import bootstrap  # noqa: E402
from app.bots import factory  # noqa: E402
from app.models import catalog, crates, inventory, market, store, users  # noqa: E402

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

    armory(now, past, live)

    print("\n" + "=" * 20 + " %d passed, %d failed " % (PASSED, FAILED) + "=" * 20)
    return 1 if FAILED else 0


def armory(now: int, past: list, live: list) -> None:
    """The Event Armory: past events' weapons and held items, on the Gear
    aisle and an aisle of their own, at ARMORY_PREMIUM everywhere."""
    print("\n== the Event Armory ==")
    stock = [it for it in catalog.ALL_ITEMS if crates.in_armory(it, now)]
    ids = {it["id"] for it in stock}
    old_use = {it["id"] for it in catalog.ALL_ITEMS if it["slot"] == "usable"
               and it.get("event") in past and int(it.get("price", 0)) > 0}
    check("every past event's weapons and held items are in the Armory",
          bool(past) and bool(ids) and ids == old_use, sorted(old_use ^ ids)[:5])
    check("the Armory is weapons and held items only -- no hat, no cosmetic",
          all(it["slot"] == "usable" for it in stock))
    aisle = market.listing("armory")
    check("the armory aisle lists exactly the Armory", {c["id"] for c in aisle} == ids,
          len(aisle))
    starts = [crates.EVENTS[c["event"]]["starts"] for c in aisle]
    check("the armory aisle is newest event first", starts == sorted(starts, reverse=True))
    check("every Armory card names its event",
          all(c["armory"] and c["ed_name"] and c["ed_short"]
              for c in store.decorate(aisle, now)))
    gear = market.listing("usable", archive=True)
    gear_ids = [c["id"] for c in gear]
    check("the Gear aisle shelves the Armory", ids <= set(gear_ids), len(ids - set(gear_ids)))
    first = next((n for n, c in enumerate(gear) if c["armory"]), len(gear))
    check("on the Gear aisle the everyday weapons come first, then the Armory",
          all(c["armory"] for c in gear[first:]) and not any(c["armory"] for c in gear[:first]))
    check("Everything still leaves the archive to the Crate Hall",
          not [c for c in market.listing("all") if c["armory"]])
    check("archive_count and armory_count split the archive",
          market.armory_count(now) == len(ids) and market.archive_count(now) > 0)

    print("\n== the Armory's price ==")
    over = [(it["id"], crates.price_of(it, now), int(it["price"])) for it in stock]
    check("an Armory piece costs more than it did during its event",
          all(p > base for _i, p, base in over), [o for o in over if o[1] <= o[2]][:3])
    check("the premium is modest (about a quarter) and a tidy number",
          all(p % 50 == 0 and 1.15 <= p / float(base) <= 1.35 for _i, p, base in over),
          [o for o in over if o[1] % 50 or not 1.15 <= o[1] / float(o[2]) <= 1.35][:3])
    sample = stock[0] if stock else catalog.get("use_pistol")
    price = crates.price_of(sample, now)
    check("the shelf card shows the Armory price",
          all(c["price"] == crates.price_of(catalog.get(c["id"]), now) for c in gear))
    found = market.listing("all", search=sample["name"])
    check("a search shows the Armory price",
          any(c["id"] == sample["id"] and c["price"] == price for c in found), sample["name"])
    api = {c["id"]: c["price"] for c in market.catalog_listing()}
    check("/api/catalog carries the Armory price", api.get(sample["id"]) == price,
          api.get(sample["id"]))
    hall = {p["id"]: p for w in store.wings(now, {}, {}) for sh in w["shelves"]
            for p in sh["pieces"]}
    check("the Crate Hall's collections show the Armory price",
          all(hall[i]["price"] == crates.price_of(catalog.get(i), now) and hall[i]["buy"]
              for i in ids if i in hall) and any(i in hall for i in ids))
    check("a bot pays the Armory price", factory._cost(sample) == price, factory._cost(sample))
    # the same weapon while its event ran sold at its catalogue price
    ev = crates.EVENTS[sample["event"]]
    during = ev["starts"] + 3600
    check("while its event runs, a weapon is not marked up",
          not crates.in_armory(sample, during)
          and crates.price_of(sample, during) == int(sample["price"]))
    live_use = [it for it in catalog.ALL_ITEMS if it["slot"] == "usable"
                and it.get("event") in live]
    check("the live event's own weapons keep their catalogue price",
          all(crates.price_of(it, now) == int(it["price"]) and not crates.in_armory(it, now)
              for it in live_use))
    hats = [it for it in catalog.ALL_ITEMS if it["slot"] == "hat"]
    check("hats are still not for sale, Armory or not",
          not any(crates.for_sale(h, now) or crates.in_armory(h, now) for h in hats))

    print("\n== the till ==")
    db.init_db()
    bootstrap.sync_catalog()
    users.create_user("armory_buyer", "blockhaven1", credits=10000)
    uid = int(db.scalar("SELECT id FROM users WHERE username=?", ("armory_buyer",)))
    bought = market.purchase(uid, sample["id"])
    check("the till charges the Armory price",
          bought["price"] == price and bought["total"] == price
          and bought["balance"] == 10000 - price, bought.get("price"))
    ledger = db.scalar("SELECT delta FROM credit_ledger WHERE user_id=? ORDER BY id DESC LIMIT 1",
                       (uid,))
    check("the ledger books the Armory price", int(ledger) == -price, ledger)
    row = inventory.get_row(uid, bought["inv_id"])
    check("the inventory shows the Armory price (what a sell-back pays 40% of)",
          inventory.decorate(row)["price"] == price)
    sold = market.sell_back(uid, bought["inv_id"])
    check("the sell-back pays 40% of the Armory price", sold["refund"] == int(price * 0.4),
          sold["refund"])
    for it in live_use[:1]:
        paid = market.purchase(uid, it["id"])
        check("a live event's weapon rings up at its catalogue price",
              paid["price"] == int(it["price"]), paid["price"])
    hat = next((h for h in hats if h.get("event") in past), hats[0])
    try:
        market.purchase(uid, hat["id"])
        refused = False
    except market.MarketError:
        refused = True
    check("the till still refuses an old event's hat", refused, hat["id"])


if __name__ == "__main__":
    sys.exit(main())
