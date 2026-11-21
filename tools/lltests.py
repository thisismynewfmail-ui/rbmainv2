#!/usr/bin/env python3
"""Headless tests for Last Light's places.

Needs no server::

    python3 tools/lltests.py                    # everything, every new place
    python3 tools/lltests.py drivein            # one place
    python3 tools/lltests.py --only catalogue,map

``catalogue``  the world page's list of places matches the maps package; every
               place has an arrival scene, a thumbnail, its infected's
               clothes and the bots' notes on its landmarks; every rig it
               uses is one the client draws; and it has what a stand needs
               -- sixteen pads in a safe room, ammunition, first aid, fuel
               barrels, a lure that makes a sound the client knows, plenty
               of places for the infected to come from and named places;
``map``        the whole map passes tools/mapcheck.py;
``walk``       a person walks away from every pad in the safe room with the
               client's own physics (tools/walkcheck.js), and the server
               accepts every step of it;
``play``       bots hold the place for a few waves on a simulated clock: the
               waves come, the infected spawn away from everybody, reach the
               survivors and die; nobody is ever inside the geometry, needs
               rescuing from the void or gets stuck; the bots get about the
               place's landmarks; nothing in the tick throws.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASSED: List[str] = []
FAILED: List[str] = []
BUILT_IN = ("town", "hospital", "docks", "camp")
SOUNDS_BUILT_IN = ("bell", "dinner", "siren", "horn")


def check(name: str, ok: bool, detail: Any = "") -> bool:
    (PASSED if ok else FAILED).append(name)
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name,
                          ("  (%s)" % (detail,)) if detail not in ("", None) else ""))
    return ok


def read(rel: str) -> str:
    with open(os.path.join(ROOT, rel)) as fh:
        return fh.read()


_MAP: Dict[str, Any] = {}


def map_data() -> Dict[str, Any]:
    if "map" not in _MAP:
        from app.game.maps import lastlight
        _MAP["map"] = lastlight.build()
    return _MAP["map"]


def area_record(area_id: str) -> Dict[str, Any]:
    return next(a for a in map_data()["markers"]["areas"] if a["id"] == area_id)


# ================================================================ catalogue
def test_catalogue(areas: List[str]) -> None:
    from app.models import worlds
    from app.game.maps import lastlight
    from app.game.bots import survival
    world = worlds.get("last_light")
    lastlight.all_areas()
    listed = [a["id"] for a in world.get("areas") or []]
    check("catalogue: the world page lists every place, in order",
          listed == list(lastlight.AREA_IDS), "%s vs %s" % (listed, lastlight.AREA_IDS))
    names = {entry[0]: entry[2] for entry in lastlight.AREAS}
    check("catalogue: the names agree",
          all(names.get(a["id"]) == a["name"] for a in world["areas"]))
    check("catalogue: every place has a blurb", all(a.get("blurb") for a in world["areas"]))
    game = read("static/js/worlds/last_light.js")
    thumbs = read("static/js/worlds/last_light_thumbs.js")
    rigs_js = read("static/js/worlds/last_light_rigs.js")
    zombies = read("static/js/engine/zombies.js")
    scenes = set(re.findall(r"""Intro\.register\(\s*['"]([a-z0-9_]+)['"]""", game))
    cards = set(re.findall(r"""registerWorld\(\s*['"]([a-z0-9_]+)['"]""", thumbs))
    kinds = set(re.findall(r"""Rigs\.register\(\s*['"]([a-z0-9_]+)['"]""", rigs_js))
    sounds = set(re.findall(r"""GA\.register\(\s*['"]([a-z0-9_]+)['"]""", game + rigs_js))
    wardrobe = zombies[zombies.index("var WARDROBE"):zombies.index("var SPECIAL")]
    for area_id in areas:
        record = area_record(area_id)
        name = record["name"]
        check("catalogue %s: an arrival scene" % area_id, area_id in scenes)
        check("catalogue %s: a thumbnail on the world page" % area_id, "ll_" + area_id in cards)
        outfits = re.search(r"\n    %s: \[(.*?)\n    \]" % re.escape(area_id), wardrobe, re.S)
        count = len(re.findall(r"\{ shirt:", outfits.group(1))) + \
            outfits.group(1).count("CLASSIC") if outfits else 0
        check("catalogue %s: the infected wear the place's own clothes (eight looks)" % area_id,
              count >= 8, count)
        spots = survival.AREA_SPOTS.get(area_id) or {}
        marks = [m["name"] for m in record["landmarks"]]
        check("catalogue %s: the bots know what every landmark is for" % area_id,
              bool(spots) and set(marks) == set(spots),
              sorted(set(marks) ^ set(spots)))
        check("catalogue %s: a dozen named places or more" % area_id, len(marks) >= 12, len(marks))
        used = sorted({r["kind"] for r in (record.get("extra") or {}).get("rigs") or []})
        missing = [k for k in used if k not in kinds]
        check("catalogue %s: every rig it uses is one the client draws" % area_id, not missing,
              missing)
        check("catalogue %s: something in it moves" % area_id, len(used) >= 4, used)
        pts = record["points"]
        check("catalogue %s: sixteen pads in the safe room" % area_id, len(record["safe"]) == 16,
              len(record["safe"]))
        check("catalogue %s: ammunition, first aid and fuel barrels" % area_id,
              len(pts.get("ammo", [])) >= 6 and len(pts.get("med", [])) >= 4
              and len(pts.get("barrel", [])) >= 8,
              {k: len(v) for k, v in pts.items()})
        check("catalogue %s: plenty of places for the infected to come from" % area_id,
              len(record["zspawn"]) >= 26, len(record["zspawn"]))
        lure = record.get("lure") or {}
        check("catalogue %s: a lure, and a sound the client can make for it" % area_id,
              bool(lure.get("name")) and (lure.get("sound") in SOUNDS_BUILT_IN
                                         or lure.get("sound") in sounds), lure.get("sound"))
        print("      (%s: %s -- %d parts, %d rigs)" % (area_id, name,
                                                     record["parts"][1] - record["parts"][0],
                                                     len((record.get("extra") or {}).get("rigs") or [])))


# ===================================================================== map
def test_map() -> None:
    import importlib
    sys.argv = [sys.argv[0]]
    mapcheck = importlib.import_module("tools.mapcheck")
    problems = mapcheck.audit("lastlight", mapcheck.MAPS["lastlight"])
    check("map: every place passes its geometry audit", problems == 0, problems)


# ==================================================================== host
class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _patch(clock):
    import app.game.instance as engine
    import app.game.bots.brain as brain_module
    import app.game.bots.runner as runner_module
    import app.game.worlds.last_light as survival_module
    import app.game.worlds.infected as infected_module
    import app.game.bots.survival as mind_module
    import app.game.gear as gear_module
    mods = [engine, brain_module, runner_module, survival_module, infected_module,
            mind_module, gear_module]
    originals = [(m, m.now) for m in mods if hasattr(m, "now")]
    for m, _ in originals:
        m.now = clock
    return originals


_HOST: Dict[str, Any] = {}


def _host():
    import tools.bottests as bottests
    if "host" not in _HOST:
        _HOST["host"] = bottests.FakeHost("last_light")
    return _HOST["host"]


# ==================================================================== walk
def walk_area(area: str, seconds: float = 4.0) -> Dict[str, Any]:
    clock = Clock()
    originals = _patch(clock)
    os.environ["BLOCKHAVEN_LL_AREA"] = area
    try:
        host = _host()
        inst = host.cls(host, host.world, 11, host.map)
        payload = inst.map_payload()
        spawns = [{"p": list(s["p"]), "yaw": float(s.get("yaw", 0.0)),
                   "label": "pad %d" % k} for k, s in enumerate(inst.area["safe"])]
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
        os.environ.pop("BLOCKHAVEN_LL_AREA", None)
        for m, orig in originals:
            m.now = orig


def test_walk(areas: List[str]) -> None:
    for area in areas:
        r = walk_area(area)
        tag = "walk %s" % area
        if not check("%s: the client physics ran" % tag, "error" not in r, r.get("error")):
            continue
        walks = r["walks"]
        check("%s: the round is in this place" % tag, r["area"] == area, r["area"])
        bad = [w["label"] for w in walks if w["embedded"]] + r["fits"]
        check("%s: nobody is put down inside anything" % tag, not bad, bad[:6])
        bad = [w["label"] for w in walks if not w["grounded"]]
        check("%s: every pad is a floor" % tag, not bad, bad[:6])
        bad = ["%s %.1f" % (w["label"], w["reach"]) for w in walks if w["reach"] < 8.0]
        check("%s: a person can walk away from every pad" % tag, not bad, bad[:6])
        bad = ["%s %.1f" % (w["label"], w["drop"]) for w in walks if w["drop"] > 30.0]
        check("%s: and does not fall through the floor doing it" % tag, not bad, bad[:6])
        check("%s: the server accepts every step of it" % tag, not r["refused"], r["refused"][:6])
        print("      (%s: %d pads, reach %.0f..%.0f)" % (
            area, len(walks), min(w["reach"] for w in walks), max(w["reach"] for w in walks)))


# ==================================================================== play
def play_area(area: str, seconds: float, bots: int = 10, seed: int = 7) -> Dict[str, Any]:
    import tools.bottests as bottests
    import app.game.instance as engine
    from app.game.bots.runner import BotRunner
    clock = Clock()
    originals = _patch(clock)
    os.environ["BLOCKHAVEN_LL_AREA"] = area
    try:
        host = _host()
        inst = host.cls(host, host.world, 7, host.map)
        rng = random.Random(seed)
        inst.bots = BotRunner(inst)
        specs = [bottests._spec(300 + i, rng, inst.team_names()[0]) for i in range(bots)]
        # waking the bots resumes the round, in the place it names
        inst.bots.wake({"mode": inst.mode, "round": 1, "area": area}, specs)
        person = inst.add_player(1, "watcher", {"hotbar": []}, None)
        person.alive = True
        inst.bots.bot_cfg = host.bot_cfg
        host.bot_cfg["near_radius"] = 5000
        spawned: List[float] = []
        hurt = {"n": 0}
        horde = inst.horde
        real_spawn = horde.spawn

        def spawn(kind, pos, hp, dmg, wave, variant=None, rise=False):
            if kind != "mite" and not rise:
                near = [math.dist(s.pos, pos) for s in inst.survivors()]
                if near:
                    spawned.append(min(near))
            return real_spawn(kind, pos, hp, dmg, wave, variant, rise)
        horde.spawn = spawn
        real_damage = inst.damage_player if hasattr(inst, "damage_player") else None
        inside = 0
        places: Dict[str, set] = {}
        moved: Dict[int, float] = {}
        started = {p.pid: list(p.pos) for p in inst.players.values()}
        worst = 0.0
        health0 = {}
        for n in range(int(seconds / engine.TICK_DT)):
            clock.t += engine.TICK_DT
            person.last_message = clock.t
            began = time.perf_counter()
            inst.tick()
            worst = max(worst, time.perf_counter() - began)
            if n % 10:
                continue
            intel = inst.bots.survival.intel() if inst.bots.survival else None
            for brain in inst.bots.brains.values():
                p = brain.p
                if not p.alive or inst.where(p) != "field":
                    continue
                if bottests._inside_solid(inst, p.pos):
                    inside += 1
                first = started.get(p.pid) or p.pos
                moved[p.pid] = max(moved.get(p.pid, 0.0), math.dist(first, p.pos))
                if p.health < health0.get(p.pid, p.health):
                    hurt["n"] += 1
                health0[p.pid] = p.health
                if intel is not None:
                    name = intel.name_of(p.pos)
                    if name:
                        places.setdefault(p.username, set()).add(name)
        stuck = 0
        for brain in inst.bots.brains.values():
            p = brain.p
            if p.alive and brain.waypoints and math.dist(brain.last_progress[0], p.pos) < 0.5 \
                    and clock.t - brain.last_progress[1] > 8:
                stuck += 1
        return {"inst": inst, "area": inst.area_id, "spawned": spawned, "inside": inside,
                "places": places, "moved": moved, "worst_ms": worst * 1000.0, "stuck": stuck,
                "hurt": hurt["n"], "errors": dict(getattr(inst, "_stage_errors", {}) or {}),
                "rescues": sum(b.rescues for b in inst.bots.brains.values()),
                "kills": inst.round_kills + inst.wave_kills, "wave": inst.wave,
                "rounds": inst.round_number}
    finally:
        os.environ.pop("BLOCKHAVEN_LL_AREA", None)
        for m, orig in originals:
            m.now = orig


def test_play(areas: List[str], seconds: float) -> None:
    for area in areas:
        r = play_area(area, seconds)
        tag = "play %s" % area
        check("%s: the round is in this place" % tag, r["area"] == area, r["area"])
        check("%s: no tick stage ever throws" % tag, not r["errors"], r["errors"])
        check("%s: the waves come and the infected die" % tag,
              r["wave"] >= 1 and r["kills"] > 10, (r["wave"], r["kills"]))
        near = sorted(r["spawned"])
        check("%s: the infected spawn well away from everybody" % tag,
              bool(near) and near[0] >= 40.0, near[:4])
        check("%s: and they reach the survivors" % tag, r["hurt"] > 0, r["hurt"])
        check("%s: no bot is ever inside the geometry" % tag, r["inside"] == 0,
              "%d samples" % r["inside"])
        check("%s: no bot falls out of the world or gets stuck" % tag,
              r["rescues"] <= 1 and r["stuck"] <= 1, (r["rescues"], r["stuck"]))
        visited = sorted(len(v) for v in r["places"].values())
        check("%s: the bots get about its places" % tag,
              bool(visited) and visited[len(visited) // 2] >= 2, visited)
        check("%s: tick cost stays low" % tag, r["worst_ms"] < 300, "%.1f ms" % r["worst_ms"])
        print("      (%s: wave %d, %d killed, nearest spawn %.0f, places per bot %s)" % (
            area, r["wave"], r["kills"], near[0] if near else -1, visited))


def main(argv: List[str]) -> int:
    from app.game.maps import lastlight
    AREA_IDS = [entry[0] for entry in lastlight.all_areas()]
    parser = argparse.ArgumentParser()
    parser.add_argument("areas", nargs="*")
    parser.add_argument("--only", default="catalogue,map,walk,play")
    parser.add_argument("--seconds", type=float, default=200.0)
    args = parser.parse_args(argv[1:])
    new = [a for a in AREA_IDS if a not in BUILT_IN]
    areas = args.areas or new
    groups = set(args.only.split(","))
    if "catalogue" in groups:
        print("== catalogue ==")
        test_catalogue(areas)
    if "map" in groups:
        print("== map ==")
        test_map()
    if "walk" in groups:
        print("== walk ==")
        test_walk(areas)
    if "play" in groups:
        print("== play (%.0f simulated seconds each) ==" % args.seconds)
        test_play(areas, args.seconds)
    print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
