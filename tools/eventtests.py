#!/usr/bin/env python3
"""Headless tests for the event worlds (app/models/event_worlds/).

Needs no server.  For every event world (or the ones named)::

    python3 tools/eventtests.py                 # every event world
    python3 tools/eventtests.py rail_rivals     # just one
    python3 tools/eventtests.py --seconds 400   # longer rounds of play

it checks, in order:

``catalogue``  the registry entry, its areas and their thumbnails, the
               badges (every level of every one builds a model, and every
               emblem is painted in static/js/engine/world_emblems.js),
               the speech events (each reads from every side and has
               stock lines), the Bots Zone subtab and the persona tag;
``client``     the world's scripts exist and register an arrival scene and
               a thumbnail for every area (and a card for the world);
``map``        the geometry audit tools/mapcheck.py runs, routes included;
``play``       a round of bots and one stand-in person on a simulated
               clock: rounds start, go live, end and move on to a new
               area, no tick stage ever throws, no bot is inside the map
               or needs rescuing from the void, bots move, and the world's
               own ``selftest`` (if it has one) is happy with what it saw;
``sleep``      the sleeping-round model advances for an hour, survives a
               snapshot, wakes into a live round of the world, and the
               live round goes back to sleep.
"""
from __future__ import annotations

import argparse
import math
import os
import random
import re
import sys
import time
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASSED: List[str] = []
FAILED: List[str] = []


def check(name: str, ok: bool, detail: Any = "") -> bool:
    (PASSED if ok else FAILED).append(name)
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name,
                          ("  (%s)" % detail) if detail not in ("", None) else ""))
    return ok


def isolate() -> None:
    """A throwaway data directory, the way tools/bottests.py runs."""
    sys.argv = [sys.argv[0]]
    import tools.bottests as bottests
    bottests.isolate()


# ================================================================ catalogue
def test_catalogue(module) -> None:
    from app.models import badges, worlds
    from app.bots import config as bot_config, personas, speech
    world = module.WORLD
    wid = world["id"]
    entry = worlds.get(wid)
    check("%s: in the world registry and open" % wid, entry is not None)
    if entry is None:
        return
    areas = entry.get("areas") or []
    check("%s: at least four areas" % wid, len(areas) >= 4, len(areas))
    check("%s: every area has a name, a blurb and a thumbnail" % wid,
          all(a.get("name") and a.get("blurb") and a.get("thumb") for a in areas))
    check("%s: how-to-play steps" % wid, len(entry.get("howto") or []) >= 3)
    mine = [b for b in badges.BADGES_LIST if b["game"] == wid]
    check("%s: at least six badges" % wid, len(mine) >= 6, len(mine))
    built = True
    for badge in mine:
        for level in range(1, len(badge["thresholds"]) + 1):
            try:
                badges.model(badge["id"], level)
            except Exception as exc:          # noqa: BLE001
                built = False
                print("      %s level %d: %s" % (badge["id"], level, exc))
    check("%s: every badge builds at every level" % wid, built)
    emblems = open(os.path.join(ROOT, "static/js/engine/world_emblems.js")).read()
    missing = [b["emblem"] for b in mine if "'%s'" % b["emblem"] not in emblems]
    check("%s: every emblem is painted" % wid, not missing, ", ".join(missing))
    kinds = [k for k in speech.KINDS if k.group == wid]
    check("%s: speech events of its own" % wid, len(kinds) >= 4, len(kinds))
    sides_ok, stock_ok = True, True
    for kind in kinds:
        event = {"kind": kind.id, "by": "Fox", "by_team": "red", "team": "red",
                 "what": "something", "n": 2, "world": wid}
        for name, team in (("Fox", "red"), ("Owl", "red"), ("Owl", "blue"), ("Owl", "ffa")):
            text, relation = speech.describe(event, name, team)
            if not text:
                sides_ok = False
                print("      %s from %s/%s says nothing" % (kind.id, name, team))
        if not any(key[0] == kind.id for key in speech.CANNED):
            stock_ok = False
            print("      %s has no stock lines" % kind.id)
    check("%s: every speech event reads from every side" % wid, sides_ok)
    check("%s: every speech event has stock lines" % wid, stock_ok)
    section = module.BOT_SECTION[0]
    fields = [f for f in bot_config.FIELDS if f.section == section]
    check("%s: a Bots Zone subtab with its own settings" % wid,
          len(fields) >= 6 and any(f.toggle for f in fields), len(fields))
    check("%s: persona ties for the subtab" % wid, len(module.PERSONA_TIES) >= 6)
    tag = getattr(module, "PERSONA_TAG", {}).get("id")
    check("%s: a favourite-world persona tag" % wid, tag in personas.TAGS_BY_ID, tag)
    check("%s: bots weigh the world" % wid, ("w_" + wid) in personas.PACK_ORDER)


def test_client(module) -> None:
    from app.models import worlds
    world = worlds.get(module.WORLD["id"])
    wid = world["id"]
    scripts = [world.get("thumb_script")] + list(world.get("game_scripts") or [])
    texts = {}
    for url in scripts:
        path = os.path.join(ROOT, url.lstrip("/"))
        ok = os.path.exists(path)
        check("%s: %s exists" % (wid, url), ok)
        if ok:
            texts[url] = open(path).read()
    game = "".join(texts.get(u, "") for u in world.get("game_scripts") or [])
    thumbs = texts.get(world.get("thumb_script"), "")
    scenes = set(re.findall(r"""register\(\s*['"]([a-z0-9_]+)['"]""", game))
    cards = set(re.findall(r"""registerWorld\(\s*['"]([a-z0-9_]+)['"]""", thumbs))
    for area in world.get("areas") or []:
        check("%s: an arrival scene for %s" % (wid, area["name"]), area["thumb"] in scenes)
        check("%s: a thumbnail for %s" % (wid, area["name"]), area["thumb"] in cards)
    check("%s: a card for the world" % wid, world["thumb"] in cards)
    check("%s: a client plugin" % wid, "Arena.register('%s'" % wid in game)


# ===================================================================== map
def test_map(module, routes: bool) -> None:
    import importlib
    sys.argv = [sys.argv[0]] + ([] if routes else ["--fast"])
    mapcheck = importlib.import_module("tools.mapcheck")
    wid = module.WORLD["id"]
    problems = mapcheck.audit(wid, mapcheck.MAPS[wid])
    check("%s: the map passes its geometry audit" % wid, problems == 0, problems)


# ==================================================================== play
class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _patch(clock):
    import app.game.instance as engine
    import app.game.bots.brain as brain_module
    import app.game.bots.runner as runner_module
    import app.game.bots.survival as mind_module
    import app.game.gear as gear_module
    patched = [engine, brain_module, runner_module, mind_module, gear_module]
    originals = [(m, m.now) for m in patched if hasattr(m, "now")]
    for m, _ in originals:
        m.now = clock
    return originals


def run_world(world_id: str, seconds: float, bots: int = 14, seed: int = 5,
              watcher: bool = True) -> Dict[str, Any]:
    sys.argv = [sys.argv[0]]
    import tools.bottests as bottests
    import app.game.instance as engine
    from app.game.bots.runner import BotRunner
    clock = Clock()
    originals = _patch(clock)
    try:
        host = bottests.FakeHost(world_id)
        inst = host.cls(host, host.world, 7, host.map)
        rng = random.Random(seed)
        inst.bots = BotRunner(inst)
        teams = inst.team_names()
        specs = [bottests._spec(500 + i, rng, teams[i % len(teams)]) for i in range(bots)]
        inst.bots.wake({"mode": inst.mode, "round": 1, "between": True}, specs)
        person = None
        if watcher:
            person = inst.add_player(1, "watcher", {"hotbar": []}, None)
            inst.bots.bot_cfg = host.bot_cfg
            host.bot_cfg["near_radius"] = 5000
        ticks = int(seconds / engine.TICK_DT)
        areas_seen = [inst.area_id]
        phases = {}
        inside = 0
        moved = {}
        started = {p.pid: list(p.pos) for p in inst.players.values()}
        worst = 0.0
        observations: List[Dict[str, Any]] = []
        for n in range(ticks):
            clock.t += engine.TICK_DT
            if person is not None:
                person.last_message = clock.t
            began = time.perf_counter()
            inst.tick()
            worst = max(worst, time.perf_counter() - began)
            phases[inst.phase] = phases.get(inst.phase, 0) + 1
            if inst.area_id != areas_seen[-1]:
                areas_seen.append(inst.area_id)
            if n % 10 == 0:
                for brain in inst.bots.brains.values():
                    p = brain.p
                    if p.alive and bottests._inside_solid(inst, p.pos):
                        inside += 1
                    if p.alive:
                        first = started.get(p.pid) or p.pos
                        moved[p.pid] = max(moved.get(p.pid, 0.0), math.dist(first, p.pos))
                if hasattr(inst, "observe"):
                    observations.append(inst.observe())
        errors = dict(getattr(inst, "_stage_errors", {}) or {})
        return {"inst": inst, "host": host, "areas": areas_seen, "phases": phases,
                "inside": inside, "moved": moved, "errors": errors,
                "rescues": sum(b.rescues for b in inst.bots.brains.values()),
                "rounds": inst.round_number, "worst_ms": worst * 1000.0,
                "observations": observations, "seconds": seconds}
    finally:
        for m, orig in originals:
            m.now = orig


def test_play(module, seconds: float) -> None:
    wid = module.WORLD["id"]
    r = run_world(wid, seconds)
    inst = r["inst"]
    check("%s: no tick stage ever throws" % wid, not r["errors"], r["errors"])
    check("%s: rounds go live" % wid, r["phases"].get("active", 0) > 0, r["phases"])
    check("%s: rounds end and start again" % wid, r["rounds"] >= 3, "%d rounds" % r["rounds"])
    check("%s: the server moves on to a new area" % wid, len(set(r["areas"])) >= 2,
          " -> ".join(r["areas"]))
    check("%s: no bot is ever inside the map's geometry" % wid, r["inside"] == 0,
          "%d samples" % r["inside"])
    check("%s: no bot falls out of the world" % wid, r["rescues"] <= 2, r["rescues"])
    still = [pid for pid, d in r["moved"].items() if d < 8.0]
    check("%s: bots get about (all but a couple move)" % wid,
          len(still) <= max(1, len(r["moved"]) // 6), "%d of %d stayed put" %
          (len(still), len(r["moved"])))
    check("%s: tick cost stays low" % wid, r["worst_ms"] < 250, "%.1f ms worst" % r["worst_ms"])
    selftest = getattr(inst, "selftest", None)
    if selftest is not None:
        for name, ok, detail in selftest(r):
            check("%s: %s" % (wid, name), ok, detail)


# =================================================================== sleep
def test_sleep(module) -> None:
    sys.argv = [sys.argv[0]]
    import tools.bottests as bottests
    from app.bots import dormant
    from app.models import worlds
    from app.game.bots.runner import BotRunner
    world = worlds.get(module.WORLD["id"])
    wid = world["id"]
    rng = random.Random(3)
    dorm = dormant.Dormant(world, 9, 1000.0, rng)
    for uid in range(40, 52):
        dorm.add(uid, 1000.0, rng.random(), rng.random())
    before = dorm.round
    dorm.advance(1000.0 + 3600.0)
    check("%s: a sleeping round moves on in an hour" % wid, dorm.round > before,
          "round %d, %s" % (dorm.round, dorm.summary()))
    again = dormant.Dormant.load(world, dorm.dump())
    check("%s: a sleeping round survives a snapshot" % wid,
          again.area == dorm.area and again.round == dorm.round and
          len(again.members) == len(dorm.members))
    state = dorm.wake_state(1000.0 + 3600.0)
    check("%s: it wakes with a state" % wid, state.get("area") in [a["id"] for a in world["areas"]])
    clock = Clock()
    originals = _patch(clock)
    try:
        host = bottests.FakeHost(wid)
        inst = host.cls(host, host.world, 9, host.map)
        inst.bots = BotRunner(inst)
        teams = inst.team_names()
        specs = [bottests._spec(700 + i, rng, teams[i % len(teams)]) for i in range(8)]
        state["between"] = False
        state["phase"] = "active"
        inst.bots.wake(state, specs)
        check("%s: a woken round is under way in the right area" % wid,
              inst.phase == "active" and inst.area_id == state["area"],
              "%s in %s" % (inst.phase, inst.area_id))
        snap = inst.bots.sleep_snapshot()
        live = snap.get("live") or {}
        check("%s: and goes back to sleep with its area" % wid, live.get("area") == inst.area_id)
        dorm2 = dormant.Dormant(world, 9, clock.t, rng)
        for row in snap["bots"]:
            dorm2.members[row["uid"]] = dormant.Member(row["team"], clock.t, 0.5, 0.5)
        dorm2.from_live(live, clock.t)
        check("%s: the sleeping round adopts it" % wid, dorm2.area == inst.area_id)
    finally:
        for m, orig in originals:
            m.now = orig


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("worlds", nargs="*")
    parser.add_argument("--seconds", type=float, default=420.0)
    parser.add_argument("--fast", action="store_true", help="skip the route walk")
    parser.add_argument("--only", default="catalogue,client,map,play,sleep")
    args = parser.parse_args(argv[1:])
    isolate()
    from app.models import event_worlds
    wanted = args.worlds or event_worlds.ids()
    groups = set(args.only.split(","))
    for wid in wanted:
        module = event_worlds.by_id(wid)
        if module is None:
            print("unknown event world %r (have: %s)" % (wid, ", ".join(event_worlds.ids())))
            return 2
        print("=" * 74)
        print(module.WORLD["name"])
        if "catalogue" in groups:
            test_catalogue(module)
        if "client" in groups:
            test_client(module)
        if "map" in groups:
            test_map(module, routes=not args.fast)
        if "play" in groups:
            test_play(module, args.seconds)
        if "sleep" in groups:
            test_sleep(module)
    print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
    for name in FAILED:
        print("  failed: %s" % name)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
