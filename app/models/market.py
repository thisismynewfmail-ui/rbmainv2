"""The item market.

Prices are read from the server side catalogue only.  The client sends an item
id (and, for crates and keys, how many) and nothing else, so a modified request
cannot change a price, grant a free item, or force an outcome.

Hats are not on the shelf any more: they come out of crates (crates.py), and
so does anything else a crate holds exclusively.  The market sells the keys
and crates that open them, the bundles, everything wearable that is not a
crate exclusive, and the event items while their event runs.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .. import db
from . import catalog, crates, inventory

# Things you can hold several of and buy several of at once.
STACKABLE = set(catalog.STASH_SLOTS)

# The market's own aisle order.  Keys lead: they are the first thing on the
# shelf, because a crate is useless without one.
AISLE_ORDER = {"key": 0, "crate": 1, "usable": 2, "hair": 3, "face": 4,
               "shirt": 5, "pants": 6, "belt": 7, "back": 8, "hat": 9}

# How long an item counts as new, from the day it shipped.
NEW_IDS = frozenset(it["id"] for it in catalog.ALL_ITEMS
                    if it.get("event") or it["slot"] in ("crate", "key")
                    or it["id"] in ("hair_quiff", "hair_afro", "hair_buns", "hair_waves"))


class MarketError(Exception):
    pass


def listing(slot: Optional[str] = None, sort: str = "featured",
            search: str = "") -> List[Dict[str, Any]]:
    """What is on the shelf right now."""
    now = int(time.time())
    items = [it for it in catalog.ALL_ITEMS if crates.for_sale(it, now)]
    if slot and slot not in ("all", "featured"):
        if slot == "stash":
            items = [it for it in items if it["slot"] in STACKABLE]
        elif slot == "event":
            items = [it for it in items if it.get("event")]
        else:
            items = [it for it in items if it["slot"] == slot]
    term = (search or "").strip().lower()
    if term:
        items = [it for it in items
                 if term in it["name"].lower() or term in it["id"].lower()
                 or term in it.get("description", "").lower()]
    if sort == "price_asc":
        items.sort(key=lambda i: (i.get("price", 0), i["name"]))
    elif sort == "price_desc":
        items.sort(key=lambda i: (-i.get("price", 0), i["name"]))
    elif sort == "name":
        items.sort(key=lambda i: i["name"].lower())
    else:
        items.sort(key=lambda i: (AISLE_ORDER.get(i["slot"], 9),
                                  0 if i.get("event") else 1,
                                  i.get("sort_order", 0), i["name"]))
    return [_card(it, now) for it in items]


def catalog_listing() -> List[Dict[str, Any]]:
    """Every item the renderer may be asked to draw -- including the ones the
    shelf does not sell, because somebody's inventory, a crate's contents or a
    random look on the welcome screen can still show them."""
    now = int(time.time())
    return [_card(it, now) for it in catalog.ALL_ITEMS if not it.get("hidden")]


def _card(item: Dict[str, Any], now: Optional[int] = None) -> Dict[str, Any]:
    grade = crates.GRADES.get(item.get("rarity", "common"), crates.GRADES["common"])
    series = (crates.CRATE_SERIES.get(item["id"])
              or crates.KEY_SERIES.get(item["id"]))
    return db.AttrDict({
        "id": item["id"],
        "name": item["name"],
        "slot": item["slot"],
        "slot_label": catalog.SLOT_LABELS.get(item["slot"], item["slot"]),
        "price": item.get("price", 0),
        "rarity": item.get("rarity", "common"),
        "rarity_color": grade["color"],
        "description": item.get("description", ""),
        "data": item.get("data", {}),
        "free": item.get("price", 0) <= 0,
        "for_sale": crates.for_sale(item, now),
        "crate_only": item["id"] in crates.CRATE_EXCLUSIVE,
        "event": item.get("event", ""),
        "series": series["id"] if series else "",
        "stackable": item["slot"] in STACKABLE,
        "is_new": item["id"] in NEW_IDS,
        # Unusuals only ever come out of a crate now
        "unusual_capable": item["slot"] == "hat",
    })


def purchase(user_id: int, item_id: str, qty: int = 1) -> Dict[str, Any]:
    """Buy copies of an item. Atomic: charge + grant happen together."""
    item = catalog.get(item_id)
    if item is None:
        raise MarketError("That item is not in the catalogue.")
    if item["id"] in crates.CRATE_EXCLUSIVE:
        raise MarketError("%s only comes out of a crate now -- grab a crate and a key!"
                          % item["name"])
    if item.get("event") and not crates.event_active(item["event"]):
        raise MarketError("%s went away with the event." % item["name"])
    price = int(item.get("price", 0))
    if price < 0:
        raise MarketError("That item is not for sale.")
    if price == 0 and inventory.owns_item(user_id, item_id):
        raise MarketError("You already own %s." % item["name"])
    try:
        qty = int(qty or 1)
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, min(crates.MAX_QTY if item["slot"] in STACKABLE else 1, qty))
    total = price * qty
    now = int(time.time())

    with db.transaction() as conn:
        row = conn.execute("SELECT credits, username FROM users WHERE id=?",
                           (user_id,)).fetchone()
        if row is None:
            raise MarketError("No such account.")
        credits = int(row["credits"])
        if credits < total:
            raise MarketError("You need %s more Noogets for %s."
                              % (f"{total - credits:,}", item["name"]))
        new_balance = credits - total
        conn.execute("UPDATE users SET credits=? WHERE id=?",
                     (new_balance, user_id))
        conn.execute(
            "INSERT INTO credit_ledger(user_id,delta,balance_after,reason,"
            "actor_id,created_at) VALUES(?,?,?,?,?,?)",
            (user_id, -total, new_balance,
             ("Bought %s" % item["name"]) if qty == 1
             else "Bought %d x %s" % (qty, item["name"]), None, now))
        inv_ids = []
        serial = 0
        for _ in range(qty):
            serial = int(conn.execute(
                "SELECT COALESCE(MAX(serial),0) FROM inventory WHERE item_id=?",
                (item_id,)).fetchone()[0]) + 1
            cur = conn.execute(
                "INSERT INTO inventory(user_id,item_id,tier,effect,serial,"
                "acquired_at,source) VALUES(?,?,?,?,?,?,?)",
                (user_id, item_id, "normal", "", serial, now, "market"))
            inv_ids.append(int(cur.lastrowid))

    db.audit(user_id, "market.purchase", item_id,
             {"price": price, "qty": qty, "inv_ids": inv_ids})
    return {
        "inv_id": inv_ids[-1], "inv_ids": inv_ids, "item_id": item_id,
        "name": item["name"], "slot": item["slot"], "price": price, "qty": qty,
        "total": total, "tier": "normal", "effect": "", "effect_name": "",
        "balance": new_balance, "serial": serial,
        # authoritative copy count, so the card's "Owned xN" is right even when
        # the same account bought one somewhere else a moment ago
        "owned": inventory.count_of(user_id, item_id),
        "stash": crates.stash_counts(user_id) if item["slot"] in STACKABLE else None,
    }


def sell_back(user_id: int, inv_id: int) -> Dict[str, Any]:
    """Refund an owned copy for 40% of its catalogue price."""
    row = inventory.get_row(user_id, inv_id)
    if row is None:
        raise MarketError("You do not own that item.")
    item = catalog.get(row["item_id"])
    if item is None:
        raise MarketError("Unknown item.")
    if item.get("is_default"):
        raise MarketError("Starter equipment cannot be sold.")
    refund = int(item.get("price", 0) * 0.4)
    now = int(time.time())
    with db.transaction() as conn:
        owned = conn.execute("SELECT 1 FROM inventory WHERE id=? AND user_id=?",
                             (inv_id, user_id)).fetchone()
        if owned is None:
            raise MarketError("You do not own that item.")
        conn.execute("DELETE FROM inventory WHERE id=? AND user_id=?",
                     (inv_id, user_id))
        if refund > 0:
            from .. import config
            credits = int(conn.execute("SELECT credits FROM users WHERE id=?",
                                       (user_id,)).fetchone()["credits"])
            new_balance = min(config.MAX_CREDITS, credits + refund)
            conn.execute("UPDATE users SET credits=? WHERE id=?",
                         (new_balance, user_id))
            conn.execute(
                "INSERT INTO credit_ledger(user_id,delta,balance_after,reason,"
                "actor_id,created_at) VALUES(?,?,?,?,?,?)",
                (user_id, refund, new_balance, "Sold %s" % item["name"], None, now))
    from . import avatars
    avatars.unequip_missing(user_id)
    db.audit(user_id, "market.sell", row["item_id"], {"refund": refund})
    return {"refund": refund, "item_id": row["item_id"],
            "owned": inventory.count_of(user_id, row["item_id"])}
