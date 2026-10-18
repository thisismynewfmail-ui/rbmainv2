#!/usr/bin/env python3
"""Pets, checked offline against a throwaway database (no server):

    python3 tools/pettests.py

What can be bought and how often, adopting a pet makes her the one who
follows you, what Edit Pet may and may not save, the pet in the avatar
descriptor and back out of a game ticket, the shop's shelves, and the Pet
Zone's care: needs that run down lazily, naps and waking, cooldowns, what is
refused and why, persona, the bond, its daily cap and milestones, the daily
greeting, and the Pet Zone tab.
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
from app.http.router import Request  # noqa: E402
from app.models import avatars, catalog, market, pet_care, pets, users  # noqa: E402
from app.views import base as base_view  # noqa: E402

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


def refused(fn, *args, **kw):
    """The CareError an action is refused with, or None if it happened."""
    try:
        fn(*args, **kw)
    except pet_care.CareError as exc:
        return exc
    return None


def nav_pet(uid: int) -> bool:
    """What the page context says about the Pet Zone tab for this account."""
    req = Request("GET", "/", "", {}, b"", "127.0.0.1")
    req.user = users.get_by_id(uid)
    return base_view.context(req)["nav_pet"]


def poke(inv_id: int, at: int, **needs: float) -> None:
    """Set some of her needs as they stand at ``at``."""
    sets = ", ".join("%s=?" % k for k in needs)
    db.execute("UPDATE pet_care SET %s, settled_at=? WHERE inv_id=?" % sets,
               list(needs.values()) + [at, inv_id])


def care_checks() -> None:
    print("\n== the Pet Zone: her needs ==")
    carer = user("carer")
    check("no pet, no Pet Zone tab", nav_pet(carer) is False)
    fern = market.purchase(carer, "pet_fern")["inv_id"]
    check("a pet of your own brings the Pet Zone tab", nav_pet(carer) is True)
    check("the page context has no tab for a signed-out visitor",
          base_view.context(Request("GET", "/", "", {}, b"", "127.0.0.1"))["nav_pet"] is False)
    day = 20000
    T = day * 86400 + 10 * 3600            # ten in the morning, UTC
    st = pet_care.state(carer, fern, now=T)
    check("she arrives fed, happy and brushed", st["needs"] == pet_care.START, st["needs"])
    check("...happy, awake and ready for a hello",
          st["mood"]["id"] == "happy" and not st["napping"] and st["greet_ready"])
    tags = ["cheerful", "loyal", "curious"]
    per_hour = pet_care.rates(tags)
    check("a cheerful pet's happiness runs down slower",
          per_hour["happiness"] == pet_care.DECAY["happiness"] * 0.75)
    check("an energetic one gets tired and hungry faster",
          pet_care.rates(["energetic"])["energy"] > pet_care.DECAY["energy"]
          and pet_care.rates(["energetic"])["fullness"] > pet_care.DECAY["fullness"])
    later = pet_care.state(carer, fern, now=T + 10 * 3600)
    want = {k: pet_care.START[k] - per_hour[k] * 10 for k in pet_care.NEEDS}
    check("ten hours on, every need has run down at its own rate",
          all(abs(later["needs"][k] - want[k]) < 0.01 for k in pet_care.NEEDS), later["needs"])
    row = db.query_one("SELECT settled_at, fullness FROM pet_care WHERE inv_id=?", (fern,))
    check("...worked out on reading: nothing was written", row["settled_at"] == T and row["fullness"] == 75)
    week = pet_care.state(carer, fern, now=T + 7 * 86400)
    check("a week alone empties her and no further",
          all(v == 0 for v in week["needs"].values()), week["needs"])
    check("...and she is starving", week["mood"]["id"] == "starving" and week["mood"]["needy"])
    check("the page is given her rates per second, to run the meters itself",
          abs(st["rates"]["fullness"] - pet_care.DECAY["fullness"] / 3600) < 1e-6)

    print("\n== the Pet Zone: moods ==")
    full = {"fullness": 80, "happiness": 70, "energy": 80, "cleanliness": 80}
    def mood(tags_=(), **kw):
        return pet_care.mood_of(dict(full, **kw), False, list(tags_))
    check("asleep comes first", pet_care.mood_of(dict(full, fullness=1), True, []) == "asleep")
    check("then starving, exhausted and sad",
          (mood(fullness=10), mood(energy=10), mood(happiness=10)) == ("starving", "exhausted", "sad"))
    check("then hungry, sleepy and grubby",
          (mood(fullness=30), mood(energy=25), mood(cleanliness=20)) == ("hungry", "sleepy", "grubby"))
    check("a clingy pet is lonely where another is bored",
          mood(("clingy",), happiness=30) == "lonely" and mood(happiness=30) == "bored")
    check("over the moon, happy, content",
          (mood(happiness=90), mood(), mood(happiness=50)) == ("ecstatic", "happy", "content"))

    print("\n== the Pet Zone: looking after her ==")
    t = T + 60
    pat = pet_care.act(carer, fern, "pat", now=t)
    check("a pat makes her happier", pat["result"]["deltas"]["happiness"] > 0, pat["result"])
    check("a loyal pet loves pats (half as much happiness again)",
          pat["result"]["loved"] and abs(pat["result"]["deltas"]["happiness"] - 7.5) < 0.05)
    check("...and bonds faster: (1 + 1 for love) x 1.5 = 3", pat["result"]["bond"] == 3, pat["result"])
    again = refused(pet_care.act, carer, fern, "pat", now=t + 1)
    check("the answer shows her cooldown started and the pat counted",
          pat["care"]["cooldowns"]["pat"] == pet_care.ACTIONS["pat"]["cooldown"]
          and pat["care"]["counts"]["pat"] == 1, (pat["care"]["cooldowns"], pat["care"]["counts"]))
    check("a pat has a cooldown", again is not None and again.code == "cooldown" and again.status == 429)
    check("...that says how long to wait and comes with her state",
          again is not None and 0 < again.retry_in <= 2 and again.care and again.care["inv_id"] == fern)
    check("after the cooldown she can be patted again",
          refused(pet_care.act, carer, fern, "pat", now=t + 3) is None)
    t += 60
    poke(fern, t, happiness=50)
    fed = pet_care.act(carer, fern, "feed", "berries", now=t)
    check("Fern's favourite treat is the berry bowl",
          fed["result"]["favourite"] and fed["result"]["loved"])
    check("...worth half as much happiness again",
          abs(fed["result"]["deltas"]["happiness"] - pet_care.TREATS["berries"]["happiness"] * 1.5) < 0.05,
          fed["result"]["deltas"])
    check("a treat fills her up", fed["result"]["deltas"]["fullness"] > 0)
    other = pet_care.act(carer, fern, "feed", "cookie", now=t + 10)
    check("another treat is just a treat", not other["result"]["favourite"])
    poke(fern, t + 20, fullness=96)
    stuffed = refused(pet_care.act, carer, fern, "feed", "cookie", now=t + 30)
    check("a stuffed pet refuses food", stuffed is not None and stuffed.code == "full" and stuffed.status == 409)
    poke(fern, t + 40, cleanliness=99)
    check("a spotless pet needs no brushing",
          getattr(refused(pet_care.act, carer, fern, "brush", now=t + 50), "code", "") == "spotless")
    poke(fern, t + 60, cleanliness=40)
    brushed = pet_care.act(carer, fern, "brush", now=t + 70)
    check("a brush cleans her up", brushed["result"]["deltas"]["cleanliness"] == 30)
    poke(fern, t + 80, energy=5)
    check("a worn-out pet is too tired to play",
          getattr(refused(pet_care.act, carer, fern, "play", "ball", now=t + 90), "code", "") == "tired")
    poke(fern, t + 100, energy=80, happiness=40)
    played = pet_care.act(carer, fern, "play", "wand", now=t + 110)
    check("a curious pet's favourite toy is the feather wand",
          played["result"]["favourite"] and played["care"]["favourite_toy"] == "wand")
    check("...a quarter as much happiness again, on top of loving play",
          abs(played["result"]["deltas"]["happiness"] - 13 * 1.25 * 1.5) < 0.05, played["result"]["deltas"])
    check("playing tires her out", played["result"]["deltas"]["energy"] < 0)

    print("\n== the Pet Zone: what is refused ==")
    for action, item, why in (("dance", None, "an unknown action"), ("feed", None, "food without a treat"),
                              ("feed", "steak", "an unknown treat"), ("play", "bone", "an unknown toy"),
                              ("play", None, "play without a toy")):
        e = refused(pet_care.act, carer, fern, action, item, now=t + 200)
        check("%s is refused" % why, e is not None and e.code == "invalid" and e.status == 400, e and e.code)
    e = refused(pet_care.act, carer, "abc", "pat", now=t + 200)
    check("a pet that is not a number is refused", e is not None and e.code == "invalid")
    e = refused(pet_care.act, carer, 999999, "pat", now=t + 200)
    check("a pet you do not own is refused", e is not None and e.code == "not_owned" and e.status == 404)
    stranger = user("stranger")
    e = refused(pet_care.act, stranger, fern, "pat", now=t + 200)
    check("you cannot look after somebody else's pet", e is not None and e.code == "not_owned")
    check("...or read how she is", isinstance(refused(pet_care.state, stranger, fern, now=t + 200),
                                              pet_care.CareError))
    check("a wake for a pet who is awake is refused",
          getattr(refused(pet_care.act, carer, fern, "wake", now=t + 200), "code", "") == "awake")

    print("\n== the Pet Zone: naps ==")
    t += 400
    poke(fern, t, energy=90)
    check("she is not sleepy with plenty of energy",
          getattr(refused(pet_care.act, carer, fern, "nap", now=t + 1), "code", "") == "not_sleepy")
    poke(fern, t + 3, energy=40, fullness=60)
    nap = pet_care.act(carer, fern, "nap", now=t + 3)
    check("a tired pet naps", nap["care"]["napping"] and nap["care"]["mood"]["id"] == "asleep")
    check("...and says when she will wake by herself",
          nap["care"]["nap_left"] == int(-(-(100 - 40) // (pet_care.NAP_GAIN / 60))), nap["care"]["nap_left"])
    e = refused(pet_care.act, carer, fern, "pat", now=t + 10)
    check("nothing but waking her while she sleeps", e is not None and e.code == "asleep")
    asleep = pet_care.state(carer, fern, now=t + 63)
    check("asleep, her energy comes back fast",
          abs(asleep["needs"]["energy"] - (40 + pet_care.NAP_GAIN)) < 0.01, asleep["needs"]["energy"])
    check("...and her tummy empties at half speed",
          abs(asleep["needs"]["fullness"] - (60 - per_hour["fullness"] / 60 * pet_care.NAP_SLOW)) < 0.01)
    woken = pet_care.act(carer, fern, "wake", now=t + 63)
    check("woken early, she is up -- and a little cross about it",
          not woken["care"]["napping"] and woken["result"]["deltas"]["happiness"] < 0)
    poke(fern, t + 100, energy=70)
    pet_care.act(carer, fern, "nap", now=t + 101)
    rested = pet_care.state(carer, fern, now=t + 101 + 600)
    check("left alone she wakes up by herself, rested",
          not rested["napping"] and rested["needs"]["energy"] > 99, rested["needs"]["energy"])
    settled = pet_care.settle(dict(db.query_one("SELECT * FROM pet_care WHERE inv_id=?", (fern,))),
                              tags, t + 101 + 600)
    check("...at the exact second she was rested", settled["woke_at"] == t + 101 + 150, settled["woke_at"])

    print("\n== the Pet Zone: the bond ==")
    check("milestones start at Just Met", pet_care.milestone(0)["name"] == "Just Met")
    m = pet_care.milestone(40)
    check("and climb", m["level"] == 1 and m["next"]["name"] == "Pals" and abs(m["progress"] - 0.5) < 1e-6, m)
    check("the last has nothing after it",
          pet_care.milestone(5000)["next"] is None and pet_care.milestone(5000)["progress"] == 1.0)
    d2 = (day + 1) * 86400 + 9 * 3600
    poke(fern, d2, energy=80, happiness=50, fullness=60, cleanliness=60, napping_since=0)
    before = pet_care.state(carer, fern, now=d2)["bond"]["points"]
    gained, crossed, capped = 0, [], False
    for i in range(30):
        r = pet_care.act(carer, fern, "pat", now=d2 + i * 4)["result"]
        gained += r["bond"]
        capped = capped or r["capped"]
        if r["milestone"]:
            crossed.append(r["milestone"]["name"])
    after = pet_care.state(carer, fern, now=d2 + 200)["bond"]
    check("care grows the bond up to the daily cap and no further",
          gained == pet_care.DAILY_BOND and after["today"] == pet_care.DAILY_BOND, (gained, after["today"]))
    check("...and says so once it is reached", capped)
    reached = pet_care.milestone(after["points"])
    check("a milestone passed on the way is announced",
          crossed == [reached["name"]] and before < reached["floor"], (crossed, before, after["points"]))
    nxt = pet_care.act(carer, fern, "pat", now=d2 + 86400)
    check("tomorrow the bond grows again", nxt["result"]["bond"] > 0 and nxt["care"]["bond"]["today"] == nxt["result"]["bond"])
    check("the bond only ever grows", after["points"] == before + gained)

    print("\n== the Pet Zone: the daily hello ==")
    g1 = pet_care.act(carer, fern, "greet", now=d2 + 100)
    check("a hello once a day", g1["result"]["streak"] == 1 and not g1["care"]["greet_ready"])
    check("...worth a little bond on top of the cap", g1["result"]["bond"] == 5, g1["result"])
    e = refused(pet_care.act, carer, fern, "greet", now=d2 + 200)
    check("a second hello the same day is refused", e is not None and e.code == "greeted")
    g2 = pet_care.act(carer, fern, "greet", now=d2 + 86400 + 300)
    check("the next day's hello makes a streak", g2["result"]["streak"] == 2 and g2["result"]["bond"] == 6)
    g3 = pet_care.act(carer, fern, "greet", now=d2 + 3 * 86400)
    check("a day missed starts it again", g3["result"]["streak"] == 1)
    counts = g3["care"]["counts"]
    check("she remembers what you have done together", counts["pat"] >= 30 and counts["greet"] == 3, counts)

    print("\n== the Pet Zone: persona ==")
    ember = market.purchase(carer, "pet_ember")["inv_id"]
    pets.save(carer, ember, tags=["feisty"])
    e0 = ember and pet_care.state(carer, ember, now=d2 + 4 * 86400)
    check("a feisty pet would rather not be brushed", "brush" in e0["dislikes"] and "play" in e0["loves"])
    poke(ember, d2 + 4 * 86400, cleanliness=40)
    b = pet_care.act(carer, ember, "brush", now=d2 + 4 * 86400 + 1)
    check("...and gets half the happiness from it", b["result"]["disliked"]
          and abs(b["result"]["deltas"]["happiness"] - 1.5) < 0.05, b["result"])
    pets.save(carer, ember, tags=["feisty", "showoff"])
    check("a tag that loves something outweighs one that dislikes it",
          "brush" not in pet_care.state(carer, ember, now=d2 + 4 * 86400 + 2)["dislikes"])
    summary = pet_care.summary(carer, now=d2 + 4 * 86400 + 2)
    check("the switcher gets every pet's mood", set(summary) == {fern, ember}
          and all("label" in v and "needy" in v for v in summary.values()))
    cat = pet_care.catalogue()
    check("the page's catalogue has the bar's actions and their effects",
          [a["id"] for a in cat["actions"]] == pet_care.ACTION_ORDER and "wake" in cat["effects"])
    check("every species has a favourite treat on the tray",
          all(pet_care.FAVOURITE.get(s) in pet_care.TREATS for s in pets.SPECIES))


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

    care_checks()

    print("\n" + "=" * 20 + " %d passed, %d failed " % (PASSED, FAILED) + "=" * 20)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
