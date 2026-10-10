#!/usr/bin/env python3
"""Put items on a (development) account's hotbar, granting them first.

    python3 tools/gearkit.py builderman_x use_ny24_roman_candle use_ny25_glowstick

For trying event weapons in a world (and for tools/gameshot.js): up to five
usable items, in slot order.  Writes to the configured database -- run it
against a development server, never a live one.
"""
from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    from app import db
    from app.models import avatars, catalog, inventory, users
    db.init_db()
    user = users.get_by_username(argv[0])
    if user is None:
        print("no such user: %s" % argv[0])
        return 1
    uid = int(user["id"])
    for index, item_id in enumerate(argv[1:6]):
        item = catalog.get(item_id)
        if item is None or item["slot"] != "usable":
            print("not a usable item: %s" % item_id)
            return 1
        row = inventory.first_of(uid, item_id)
        if row is None:
            inventory.grant(uid, item_id, source="admin")
            row = inventory.first_of(uid, item_id)
        avatars.set_hotbar_slot(uid, index, int(row["id"]))
        print("slot %d: %s" % (index + 1, item["name"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
