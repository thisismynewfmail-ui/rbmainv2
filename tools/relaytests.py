#!/usr/bin/env python3
"""Headless tests for Blackout Relay's map rotation.

Needs no server::

    python3 tools/relaytests.py                 # everything, every map
    python3 tools/relaytests.py substation      # one map's play test
    python3 tools/relaytests.py --only catalogue,map

``catalogue``  the world page's list of maps matches the maps package, and
               every map has a thumbnail and an arrival scene registered in
               the client scripts;
``map``        the whole rotation passes tools/mapcheck.py (mirror symmetry
               included -- every map is fair to the last hundredth);
``play``       on every map, a round of bots on a simulated clock: nobody is
               ever inside the geometry or needs rescuing from the void, no
               tick stage throws, the bots get about, and somebody takes the
               other team's flag off its pedestal;
``walk``       on every map, a person (not a bot: bots move server-side and
               never send a position) walks away from every muster pad and
               outpost -- the client's own physics in node
               (tools/walkcheck.js), then that walk replayed to the server
               as the inputs a client sends, every one of which it accepts;
``rotate``     a round ending rolls a different map, says so (``brnext``),
               and the next round starts there (``brarea`` with its map);
``sleep``      a sleeping round keeps its map, moves on to another between
               rounds, and wakes on it.
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


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _patch(clock):
    import app.game.instance as engine
    import app.game.bots.brain as brain_module
    import app.game.bots.runner as runner_module
    import app.game.worlds.capture_the_flag as ctf_module
    import app.game.worlds.blackout_relay as relay_module
    import app.game.gear as gear_module
    mods = [engine, brain_module, runner_module, ctf_module, relay_module, gear_module]
    originals = [(m, m.now) for m in mods if hasattr(m, "now")]
    for m, _ in originals:
        m.now = clock
    return originals


# ================================================================ catalogue
def test_catalogue() -> None:
    from app.models import worlds
    from app.game.maps.relay import areas as order
    world = worlds.get("blackout_relay")
    listed = [a["id"] for a in world.get("areas") or []]
    built = ["ironvale"] + [a for a, _ in order.ORDER]
    check("catalogue: the world page lists every map in the rotation, in order",
          listed == built, "%s vs %s" % (listed, built))
    names = {a: n for a, n in order.ORDER}
    check("catalogue: the names agree",
          all(names.get(a["id"], a["name"]) == a["name"] for a in world["areas"]))
    check("catalogue: every map has a blurb, a target and a length",
          all(a.get("blurb") and a.get("captures") and a.get("minutes") for a in world["areas"]))
    game = open(os.path.join(ROOT, "static/js/worlds/blackout_relay.js")).read()
    thumbs = open(os.path.join(ROOT, "static/js/worlds/blackout_relay_thumbs.js")).read()
    scenes = set(re.findall(r"""register\(\s*['"]([a-z0-9_]+)['"]""", game))
    cards = set(re.findall(r"""registerWorld\(\s*['"]([a-z0-9_]+)['"]""", thumbs))
    for area in world["areas"]:
        check("catalogue: an arrival scene for %s" % area["name"], "br_" + area["id"] in scenes)
        if area["id"] != "ironvale":
            check("catalogue: a thumbnail for %s" % area["name"], area["thumb"] in cards)


# ===================================================================== map
def test_map(routes: bool) -> None:
    import importlib
    sys.argv = [sys.argv[0]] + ([] if routes else ["--fast"])
    mapcheck = importlib.import_module("tools.mapcheck")
    problems = mapcheck.audit("relay", mapcheck.MAPS["relay"])
    check("map: the rotation passes its geometry audit", problems == 0, problems)


# ==================================================================== play
_HOST = {}


def _host():
    import tools.bottests as bottests
    if "host" not in _HOST:
        _HOST["host"] = bottests.FakeHost("blackout_relay")
    return _HOST["host"]


def run_map(area: str, seconds: float, bots: int = 14, seed: int = 5) -> Dict[str, Any]:
    import tools.bottests as bottests
    import app.game.instance as engine
    from app.game.bots.runner import BotRunner
    clock = Clock()
    originals = _patch(clock)
    os.environ["BLOCKHAVEN_RELAY_MAP"] = area
    try:
        host = _host()
        inst = host.cls(host, host.world, 7, host.map)
        rng = random.Random(seed)
        inst.bots = BotRunner(inst)
        specs = [bottests._spec(500 + i, rng, ("red", "blue")[i % 2]) for i in range(bots)]
        inst.bots.wake({"mode": inst.mode, "round": 1}, specs)
        person = inst.add_player(1, "watcher", {"hotbar": []}, None)
        inst.bots.bot_cfg = host.bot_cfg
        host.bot_cfg["near_radius"] = 5000
        taken: Dict[str, int] = {}
        captures = 0
        inside = 0
        moved: Dict[int, float] = {}
        started = {p.pid: list(p.pos) for p in inst.players.values()}
        worst = 0.0
        real_event = inst.push_event

        def spy(kind, **data):
            if kind == "flag_take":
                taken[data.get("team", "")] = taken.get(data.get("team", ""), 0) + 1
            return real_event(kind, **data)
        inst.push_event = spy
        for n in range(int(seconds / engine.TICK_DT)):
            clock.t += engine.TICK_DT
            person.last_message = clock.t
            began = time.perf_counter()
            inst.tick()
            worst = max(worst, time.perf_counter() - began)
            if n % 10 == 0:
                for brain in inst.bots.brains.values():
                    p = brain.p
                    if p.alive and bottests._inside_solid(inst, p.pos):
                        inside += 1
                    if p.alive:
                        first = started.get(p.pid) or p.pos
                        moved[p.pid] = max(moved.get(p.pid, 0.0), math.dist(first, p.pos))
        captures = sum(inst.captures.values())
        return {"inst": inst, "taken": taken, "captures": captures, "inside": inside,
                "moved": moved, "worst_ms": worst * 1000.0,
                "errors": dict(getattr(inst, "_stage_errors", {}) or {}),
                "rescues": sum(b.rescues for b in inst.bots.brains.values()),
                "area": inst.area_id}
    finally:
        os.environ.pop("BLOCKHAVEN_RELAY_MAP", None)
        for m, orig in originals:
            m.now = orig


def test_play(areas: List[str], seconds: float) -> None:
    for area in areas:
        r = run_map(area, seconds)
        tag = "play %s" % area
        check("%s: the round is on this map" % tag, r["area"] == area, r["area"])
        check("%s: no tick stage ever throws" % tag, not r["errors"], r["errors"])
        check("%s: no bot is ever inside the map's geometry" % tag, r["inside"] == 0,
              "%d samples" % r["inside"])
        check("%s: no bot falls out of the world" % tag, r["rescues"] <= 2, r["rescues"])
        still = [pid for pid, d in r["moved"].items() if d < 8.0]
        check("%s: bots get about" % tag, len(still) <= max(1, len(r["moved"]) // 6),
              "%d of %d stayed put" % (len(still), len(r["moved"])))
        check("%s: somebody takes a flag off its pedestal" % tag, sum(r["taken"].values()) > 0,
              "taken %s, captures %d" % (r["taken"], r["captures"]))
        check("%s: tick cost stays low" % tag, r["worst_ms"] < 250, "%.1f ms" % r["worst_ms"])
        print("      (%s: flags taken %s, %d captured)" % (area, r["taken"], r["captures"]))


# ==================================================================== walk
def _spawn_list(inst) -> List[Dict[str, Any]]:
    out = []
    spawns = inst.area.get("spawns") or {}
    for team in ("red", "blue"):
        for k, point in enumerate(spawns.get(team) or []):
            out.append({"p": list(point["p"]), "yaw": float(point.get("yaw", 0.0)),
                        "label": "%s muster %d" % (team, k), "team": team})
        for k, point in enumerate(inst.outposts.get(team) or []):
            out.append({"p": list(point["p"]), "yaw": float(point.get("yaw", 0.0)),
                        "label": "%s outpost %d" % (team, k), "team": team})
    return out


def walk_map(area: str, seconds: float = 4.0) -> Dict[str, Any]:
    """Every spawn on ``area``: walked with the client's physics, then the
    walk sent to the server the way a client sends it."""
    import json
    import subprocess
    import tempfile
    clock = Clock()
    originals = _patch(clock)
    os.environ["BLOCKHAVEN_RELAY_MAP"] = area
    try:
        host = _host()
        inst = host.cls(host, host.world, 11, host.map)
        payload = inst.map_payload()
        spawns = _spawn_list(inst)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"parts": payload["parts"], "kill_y": payload.get("kill_y", -60),
                       "seconds": seconds, "spawns": spawns}, fh)
            name = fh.name
        try:
            run = subprocess.run(["node", os.path.join(ROOT, "tools", "walkcheck.js"), name],
                                 capture_output=True, text=True, timeout=300)
        finally:
            os.unlink(name)
        if run.returncode != 0:
            return {"error": run.stderr.strip()[-400:], "area": inst.area_id}
        walks = json.loads(run.stdout)
        sent: List[Dict[str, Any]] = []

        class WS:
            def send_json(self, msg):
                sent.append(msg)

            def close(self):
                pass
        person = inst.add_player(1, "walker", {"hotbar": []}, WS())
        refused: List[str] = []
        for spawn, result in zip(spawns, walks):
            person.team = spawn["team"]
            person.alive = True
            person.pos = list(spawn["p"])
            person.last_ground_pos = list(spawn["p"])
            person.vel = [0.0, 0.0, 0.0]
            person.corrections = 0
            person.airborne_since = 0.0
            clock.t += 5.0
            person.last_pos_time = clock.t
            before = sum(1 for m in sent if m.get("t") == "correct")
            for x, y, z, grounded, yaw in result["path"]:
                clock.t += 0.05
                inst.handle_input(person, {"t": "in", "p": [x, y, z], "g": bool(grounded),
                                           "v": [0.0, 0.0, 0.0], "y": yaw, "pi": 0.0})
            after = sum(1 for m in sent if m.get("t") == "correct")
            last = result["path"][-1] if result["path"] else None
            if after > before or (last and math.dist(person.pos, last[:3]) > 0.5):
                refused.append(spawn["label"])
        return {"area": inst.area_id, "walks": walks, "refused": refused,
                "fits": [s["label"] for s in spawns if not inst.body_fits(*s["p"])]}
    finally:
        os.environ.pop("BLOCKHAVEN_RELAY_MAP", None)
        for m, orig in originals:
            m.now = orig


def test_walk(areas: List[str]) -> None:
    for area in areas:
        r = walk_map(area)
        tag = "walk %s" % area
        if not check("%s: the client physics ran" % tag, "error" not in r, r.get("error")):
            continue
        walks = r["walks"]
        check("%s: the round is on this map" % tag, r["area"] == area, r["area"])
        bad = [w["label"] for w in walks if w["embedded"]] + r["fits"]
        check("%s: nobody is put down inside anything" % tag, not bad, bad[:6])
        bad = [w["label"] for w in walks if not w["grounded"]]
        check("%s: every spawn stands on a floor" % tag, not bad, bad[:6])
        bad = ["%s %.1f" % (w["label"], w["reach"]) for w in walks if w["reach"] < 8.0]
        check("%s: a person can walk away from every spawn" % tag, not bad, bad[:6])
        bad = ["%s %.1f" % (w["label"], w["drop"]) for w in walks if w["drop"] > 30.0]
        check("%s: and does not fall through the floor doing it" % tag, not bad, bad[:6])
        check("%s: the server accepts every step of it" % tag, not r["refused"],
              r["refused"][:6])
        print("      (%s: %d spawns, reach %.0f..%.0f)" % (
            area, len(walks), min(w["reach"] for w in walks), max(w["reach"] for w in walks)))


# ================================================================== rotate
def test_rotate() -> None:
    import tools.bottests as bottests
    clock = Clock()
    originals = _patch(clock)
    try:
        host = _host()
        inst = host.cls(host, host.world, 8, host.map)
        sent: List[Dict[str, Any]] = []

        class WS:
            def send_json(self, msg):
                sent.append(msg)

            def close(self):
                pass
        person = inst.add_player(1, "watcher", {"hotbar": []}, WS())
        first = inst.area_id
        inst.end_round("red", "test")
        nxt = [m for m in sent if m.get("t") == "brnext"]
        check("rotate: the end of a round rolls the next map and says so",
              bool(nxt) and nxt[-1].get("next") != first and nxt[-1].get("next") in inst.areas,
              nxt[-1].get("next") if nxt else None)
        target = inst.next_area_id
        inst.restart_round()
        moved = [m for m in sent if m.get("t") == "brarea"]
        check("rotate: the next round is on the map it rolled", inst.area_id == target,
              "%s -> %s" % (first, inst.area_id))
        check("rotate: everybody is sent the new map", bool(moved) and moved[-1].get("map") and
              moved[-1]["map"]["markers"].get("area") == target)
        markers = moved[-1]["map"]["markers"] if moved else {}
        check("rotate: the new map ships its flags, musters and outposts",
              all(k in markers for k in ("flag_red", "flag_blue", "muster_red", "muster_blue",
                                         "outpost_red", "outpost_blue")))
        check("rotate: the flags stand on the new map's pedestals",
              all(f.home == markers["flag_%s" % t]["p"] for t, f in inst.flags.items()))
        spawn = person.pos
        rect = inst.area["rect"]
        check("rotate: and the round starts in it",
              rect[0] <= spawn[0] <= rect[1] and rect[2] <= spawn[2] <= rect[3], spawn)
        seen = {first, inst.area_id}
        for _ in range(60):
            inst.end_round("blue", "test")
            inst.restart_round()
            seen.add(inst.area_id)
        check("rotate: the roll gets round the whole rotation in time",
              len(seen) == len(inst.areas), "%d of %d" % (len(seen), len(inst.areas)))
        del bottests
    finally:
        for m, orig in originals:
            m.now = orig


# =================================================================== sleep
def test_sleep() -> None:
    from app.bots import dormant
    from app.models import worlds
    world = worlds.get("blackout_relay")
    rng = random.Random(3)
    dorm = dormant.Dormant(world, 9, 1000.0, rng)
    check("sleep: a sleeping round is on a map of the rotation",
          dorm.area in [a["id"] for a in world["areas"]], dorm.area)
    for uid in range(40, 56):
        dorm.add(uid, 1000.0, rng.random(), rng.random())
    seen = {dorm.area}
    t = 1000.0
    for _ in range(12):
        t += 3600.0
        dorm.advance(t)
        seen.add(dorm.area)
    check("sleep: it moves on to other maps between rounds",
          len(seen) >= min(3, len(world["areas"])), sorted(seen))
    again = dormant.Dormant.load(world, dorm.dump())
    check("sleep: and keeps its map through a snapshot", again.area == dorm.area)
    state = dorm.wake_state(t)
    check("sleep: it wakes with its map", state.get("area") == dorm.area, state.get("area"))
    clock = Clock()
    originals = _patch(clock)
    try:
        import tools.bottests as bottests
        from app.game.bots.runner import BotRunner
        host = _host()
        inst = host.cls(host, host.world, 9, host.map)
        inst.bots = BotRunner(inst)
        specs = [bottests._spec(700 + i, rng, ("red", "blue")[i % 2]) for i in range(8)]
        inst.bots.wake(state, specs)
        check("sleep: a woken round is on the map it slept on", inst.area_id == state["area"],
              inst.area_id)
        rect = inst.area["rect"]
        inside = [p for p in inst.players.values()
                  if rect[0] <= p.pos[0] <= rect[1] and rect[2] <= p.pos[2] <= rect[3]]
        check("sleep: with its bots on it", len(inside) == len(inst.players),
              "%d of %d" % (len(inside), len(inst.players)))
        snap = inst.bots.sleep_snapshot()
        check("sleep: and goes back to sleep with its map",
              (snap.get("live") or {}).get("area") == inst.area_id)
    finally:
        for m, orig in originals:
            m.now = orig


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("maps", nargs="*")
    parser.add_argument("--seconds", type=float, default=150.0)
    parser.add_argument("--fast", action="store_true", help="skip the route walk")
    parser.add_argument("--only", default="catalogue,map,walk,play,rotate,sleep")
    args = parser.parse_args(argv[1:])
    sys.argv = [sys.argv[0]]
    import tools.bottests as bottests
    bottests.isolate()
    from app.game.maps.relay import areas as order
    groups = set(args.only.split(","))
    maps = args.maps or ["ironvale"] + [a for a, _ in order.ORDER]
    print("=" * 74)
    print("Blackout Relay")
    if "catalogue" in groups:
        test_catalogue()
    if "map" in groups:
        test_map(routes=not args.fast)
    if "walk" in groups:
        test_walk(maps)
    if "play" in groups:
        test_play(maps, args.seconds)
    if "rotate" in groups:
        test_rotate()
    if "sleep" in groups:
        test_sleep()
    print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
    for name in FAILED:
        print("  failed: %s" % name)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
