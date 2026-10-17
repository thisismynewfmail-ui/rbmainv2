#!/usr/bin/env python3
"""Pets, checked offline against a throwaway database (no server):

    python3 tools/pettests.py

What can be bought and how often, adopting a pet makes her the one who
follows you, what Edit Pet may and may not save, the pet in the avatar
descriptor and back out of a game ticket, and the shop's shelves.
(The rig and the follower AI have their own checks: node tools/pettests.js.)
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config, db  # noqa: E402

# a database of its own, so the checks never touch data/blockhaven.sqlite3
config.DB_PATH = pathlib.Path(tempfile.mkdtemp(prefix="bh-pettests-")) / "pets.sqlite3"

from app import bootstrap  # noqa: E402
from app.models import avatars, catalog, market, pets, users  # noqa: E402

PASSED = FAILED = 0


def check(name: str, ok: bool, detail: object = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print("  PASS  " + name)
    else:
        FAILED += 1
        print("  FAIL  %s  %r" % (name, detail))


def raises(fn, *args, **kw) -> str:
    try:
        fn(*args, **kw)
    except Exception as exc:          # noqa: BLE001 - any refusal will do
        return str(exc) or exc.__class__.__name__
    return ""


def user(name: str, credits: int = 20000) -> int:
    users.create_user(name, "blockhaven1", credits=credits)
    return int(db.scalar("SELECT id FROM users WHERE username=?", (name,)))


def main() -> int:
    db.init_db()
    bootstrap.sync_catalog()

    print("== the catalogue ==")
    species = [it for it in pets.ITEMS if it["slot"] == "pet"]
    check("five pets", len(species) == 5, [s["id"] for s in species])
    wardrobe = [it for it in pets.ITEMS if it["slot"] in pets.COSMETIC_SLOTS]
    check("at least four things for every pet slot",
          all(sum(1 for w in wardrobe if w["slot"] == s) >= 4 for s in pets.COSMETIC_SLOTS))
    check("every pet item is in the catalogue", all(catalog.get(it["id"]) for it in pets.ITEMS))
    check("every pet has three persona tags out of the box",
          all(len(s["tags"]) == 3 and all(t in pets.TAGS for t in s["tags"])
              for s in pets.SPECIES.values()))
    check("every species has all six colours",
          all(set(s["colors"]) == set(pets.COLOR_KEYS) for s in pets.SPECIES.values()))
    parts_ok = all(isinstance(p.get("p"), list) and len(p["p"]) == 3 and len(p["s"]) == 3
                   for it in wardrobe for p in (it["data"].get("parts") or []))
    check("every modelled pet cosmetic has well-formed parts", parts_ok)
    check("the first pet is affordable on a new account's Noogets",
          pets.SPECIES["fern"]["price"] <= config.STARTING_CREDITS)

    print("\n== the everyday aisles leave pets to their own shelf ==")
    listed = {c["id"] for c in market.listing("all")}
    check("no pet item on the everyday shelf", not (listed & pets.ITEM_IDS),
          sorted(listed & pets.ITEM_IDS)[:4])
    found = {c["id"] for c in market.listing("all", search="Mochi")}
    check("a search still finds a pet", "pet_mochi" in found)

    print("\n== adopting ==")
    uid = user("petowner")
    check("no pet before buying one", not pets.owns_any(uid) and avatars.descriptor(uid)["pet"] is None)
    got = market.purchase(uid, "pet_fern")
    check("buying Fern works", got["item_id"] == "pet_fern")
    check("the first pet follows you at once", pets.active_id(uid) == got["inv_id"])
    check("owns_any now says so", pets.owns_any(uid))
    again = raises(market.purchase, uid, "pet_fern")
    check("one of each pet", "already" in again.lower(), again)
    second = market.purchase(uid, "pet_luna")
    check("a second pet does not take over", pets.active_id(uid) == got["inv_id"])
    desc = avatars.descriptor(uid)
    check("the descriptor carries the active pet",
          desc["pet"] and desc["pet"]["species"] == "fern", desc.get("pet"))
    check("...with her persona", len(desc["pet"]["tag_info"]) == 3)

    print("\n== the wardrobe ==")
    hat = market.purchase(uid, "pet_hat_beret")
    check("one of each pet cosmetic",
          "already" in raises(market.purchase, uid, "pet_hat_beret").lower())
    pin = market.purchase(uid, "pet_pin_star")

    print("\n== Edit Pet ==")
    fern = got["inv_id"]
    saved = pets.save(uid, fern, name="Sprout!!<script>", colors={"hair": "#ff98dc"},
                      tags=["shy", "dreamy"], equipped={"pet_hat": hat["inv_id"],
                                                        "pet_pin": pin["inv_id"]})
    check("names are cleaned", saved["name"] == "Sprout" + "script", saved["name"])
    check("a colour saves", saved["colors"]["hair"] == "#ff98dc")
    check("tags save", saved["tags"] == ["shy", "dreamy"])
    check("the outfit saves", saved["equipped"] == {"pet_hat": hat["inv_id"], "pet_pin": pin["inv_id"]})
    check("too many tags is refused",
          bool(raises(pets.save, uid, fern, tags=["shy", "dreamy", "loyal", "brave"])))
    check("an unknown tag is dropped",
          pets.save(uid, fern, tags=["shy", "nonsense"])["tags"] == ["shy"])
    check("a bad colour is refused", bool(raises(pets.save, uid, fern, colors={"eyes": "red"})))
    check("a hat cannot go in the pin slot",
          bool(raises(pets.save, uid, fern, equipped={"pet_pin": hat["inv_id"]})))
    other = user("someoneelse")
    theirs = market.purchase(other, "pet_hat_toque")
    check("you cannot dress her in somebody else's hat",
          bool(raises(pets.save, uid, fern, equipped={"pet_hat": theirs["inv_id"]})))
    check("you cannot edit somebody else's pet", bool(raises(pets.save, other, fern, name="Mine")))
    check("a partial outfit change keeps the rest",
          pets.save(uid, fern, equipped={"pet_hat": 0})["equipped"] == {"pet_pin": pin["inv_id"]})
    pets.save(uid, fern, equipped={"pet_hat": hat["inv_id"]})
    check("an avatar-slot item cannot be worn by a pet",
          bool(raises(pets.save, uid, fern, equipped={"hat": hat["inv_id"]})))

    print("\n== the active pet ==")
    check("you can switch which pet follows you", pets.set_active(uid, second["inv_id"]) == second["inv_id"])
    check("...and the descriptor follows", avatars.descriptor(uid)["pet"]["species"] == "luna")
    check("you cannot pick somebody else's pet", bool(raises(pets.set_active, other, fern)))
    pets.set_active(uid, 0)
    check("you can have none", avatars.descriptor(uid)["pet"] is None)
    pets.set_active(uid, fern)

    print("\n== the game ticket ==")
    whole = avatars.descriptor(uid, "petowner")
    small = avatars.compact(whole)
    check("the ticket carries the pet by reference",
          small["pet"]["items"] == {"pet_hat": "pet_hat_beret", "pet_pin": "pet_pin_star"},
          small.get("pet"))
    check("...in a few hundred bytes", len(json.dumps(small["pet"])) < 500, len(json.dumps(small["pet"])))
    back = avatars.expand(json.loads(json.dumps(small)))
    check("the host rebuilds her models", bool(back["pet"]["items"]["pet_hat"]["data"]["parts"]))
    check("...and her look", back["pet"]["colors"] == whole["pet"]["colors"]
          and back["pet"]["name"] == whole["pet"]["name"])
    forged = dict(small, pet=dict(small["pet"], species="dragon"))
    check("a forged species is dropped", avatars.expand(forged)["pet"] is None)
    forged = dict(small, pet=dict(small["pet"], items={"pet_hat": "hat_tophat"}))
    check("a forged item is dropped", avatars.expand(forged)["pet"]["items"] == {})

    print("\n== selling ==")
    market.sell_back(uid, fern)
    check("selling the active pet leaves no pet following", pets.active_id(uid) == 0)

    print("\n== the shop ==")
    shelf = pets.shelf(uid)
    check("five pets on the shelf", len(shelf["pets"]) == 5)
    check("owned pets are marked", [p["owned"] for p in shelf["pets"]].count(True) == 1)
    check("six wardrobe sections", [w["slot"] for w in shelf["wardrobe"]] == pets.COSMETIC_SLOTS)
    check("owned cosmetics are marked",
          any(c["owned"] for w in shelf["wardrobe"] for c in w["cards"] if c["id"] == "pet_hat_beret"))
    anon = pets.shelf(None)
    check("the shop works signed out", not anon["owns_pet"] and not anon["mine"])

    print("\n" + "=" * 20 + " %d passed, %d failed " % (PASSED, FAILED) + "=" * 20)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
