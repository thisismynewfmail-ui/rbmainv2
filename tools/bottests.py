#!/usr/bin/env python3
"""Tests for the bot system that need no running server.

    python3 tools/bottests.py            # everything
    python3 tools/bottests.py live       # only the in-game simulations
    python3 tools/bottests.py -v live    # ... and say what the bots did

Three groups:

``unit``     personas, usernames, the chat-template renderer, the sleeping
             instance models, prompt culling, trait packing
``live``     each world run headless on a simulated clock with a round of
             bots woken into it, a pretend person watching, and the result
             checked: flags taken and captured, the cart pushed, restaurants
             built, nobody stuck in a wall or lost in the void, and the time a
             tick costs
``scale``    the director carrying a large population (``--bots N``,
             default 20000) on a throwaway database, timed per tick

Nothing here touches ``data/``: every database is a temporary file.
"""
from __future__ import annotations

import argparse
import io
import contextlib
import math
import os
import random
import sys
import tempfile
import time
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASSED: List[str] = []
FAILED: List[str] = []
VERBOSE = False


def check(name: str, ok: bool, detail: Any = "") -> bool:
    (PASSED if ok else FAILED).append(name)
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name,
                          "" if ok or not detail else "  -- %s" % str(detail)[:240]))
    return ok


def isolate() -> str:
    """Point the platform at a throwaway data directory."""
    from app import config
    tmp = tempfile.mkdtemp(prefix="bh-bottests-")
    config.DATA_DIR = config.Path(tmp)
    config.DB_PATH = config.DATA_DIR / "t.sqlite3"
    from app.bots import storage
    storage.ROOT = config.DATA_DIR / "bots"
    storage.ACCOUNTS = storage.ROOT / "accounts"
    from app.game.bots import nav
    nav.CACHE_DIR = config.DATA_DIR / "navcache"
    return tmp


# ====================================================================== unit
def test_unit() -> None:
    print("\n== unit ==")
    from app.bots import names, personas, dormant, template
    rng = random.Random(1)
    made = names.generate_unique(rng, set(), 400)
    check("names: generator makes valid, unique names",
          len(made) == 400 and all(names.acceptable(n) for n in made)
          and len({n.lower() for n in made}) == 400)
    check("names: spaces become an underscore or vanish",
          names.normalise("teto gaming", random.Random(2)) in ("teto_gaming", "tetogaming"))
    check("names: banned fragments are refused",
          not names.acceptable("robotman") and not names.acceptable("xX_admin"))
    check("names: model lists parse from JSON or lines",
          names.parse_model_list('sure! ["a1b", "keigo"]') == ["a1b", "keigo"]
          and names.parse_model_list("1. keigo\n2. banjo53") == ["1. keigo", "2. banjo53"])
    tags = personas.draw_tags(rng, 8)
    groups = [personas.tag_info(t)["group"] for t in tags]
    check("personas: every core group is present",
          all(g in groups for g, _e, core, _c in personas.GROUPS if core), tags)
    check("personas: exclusive groups hold one tag",
          all(groups.count(g) <= 1 for g, excl, _c, _m in personas.GROUPS if excl))
    traits = personas.derive_traits(tags, rng)
    back = personas.unpack_traits(personas.pack_traits(traits))
    check("personas: packed traits round-trip",
          all(abs(back[k] - traits[k]) < 0.006 for k in personas.PACK_ORDER))
    a = personas.mask_of(["night_owl", "ctf_main", "friendly"])
    b = personas.mask_of(["night_owl", "ctf_main", "loner"])
    check("personas: shared-tag count", personas.shared(a, b) == 2)
    chatml = ("{% for m in messages %}{{'<|im_start|>' + m['role'] + '\\n' + m['content']"
              " + '<|im_end|>\\n'}}{% endfor %}{% if add_generation_prompt %}"
              "{{ '<|im_start|>assistant\\n' }}{% endif %}")
    out = template.render_chat(chatml, [{"role": "user", "content": "hi"}])
    check("template: ChatML renders", out == "<|im_start|>user\nhi<|im_end|>\n<|im_start|>assistant\n", out)
    try:
        template.render_chat("{{ raise_exception('nope') }}", [])
        raised = False
    except template.RaisedError:
        raised = True
    check("template: raise_exception surfaces", raised)
    check("template: no attribute escapes",
          template.render_chat("{{ ''.__class__ }}{{ messages.__len__ }}", []) == "")
    from app.models import worlds
    for world in worlds.WORLDS:
        inst = dormant.Dormant(world, 5, 1000.0, random.Random(3))
        for uid in range(1, 13):
            inst.add(uid, 1000.0, rng.random(), rng.random())
        inst.advance(1000.0 + 3600)
        state = inst.wake_state(1000.0 + 3600)
        moved = (inst.round > 1 if inst.mode != "endless"
                 else sum(len(p["built"]) for p in inst.plots) > 0)
        check("dormant: %s moves on in an hour asleep" % world["id"], moved,
              inst.summary())
        again = dormant.Dormant.load(world, inst.dump())
        check("dormant: %s survives a snapshot" % world["id"],
              again.count == inst.count and again.round == inst.round)
        check("dormant: %s wakes with a state" % world["id"], state.get("mode") == inst.mode)


# ====================================================================== live
class FakeHost:
    """Just enough of app.game.host.GameHost for an instance to run."""

    def __init__(self, world_id: str):
        from app.game.host import load_world_class
        from app.models import worlds
        from app.game.instance import GameInstance
        from app.game.bots import nav
        self.world_id = world_id
        self.world = worlds.get(world_id)
        self.cls = load_world_class(world_id)
        self.map = self.cls.build_map()
        self.nav = nav.NavGrid(world_id, self.map, GameInstance._build_colliders(self.map))
        if not self.nav._load_cache():
            self.nav.build()
            self.nav._save_cache()
        self.nav.ready = True
        self.bot_cfg = {"system_enabled": True, "think_hz": 6, "far_think_hz": 1.2,
                        "near_radius": 170, "anything_floor": 3, "tangent_per_minute": 9,
                        "afk_per_minute": 3, "tilt_deaths": 4, "revenge": 40,
                        "greet": 35, "messages_quick_reactions": True,
                        "messages_ingame_chat": True, "messages_chat_per_minute": 8}
        self.reports: List[Dict[str, Any]] = []

    def report_player(self, instance, player, final=False):
        kills, deaths, score = player.kills, player.deaths, player.score
        if player.brain is not None:
            kills, deaths, score = player.brain.stats_delta()
        self.reports.append({"kind": "stats", "uid": player.user_id, "kills": kills})

    def report_round(self, instance, player, won):
        self.reports.append({"kind": "round", "uid": player.user_id, "won": won})

    def report_visit(self, instance, player):
        self.reports.append({"kind": "visit", "uid": player.user_id})

    def wake_heartbeat(self):
        pass


class Clock:
    """A simulated monotonic clock shared by the engine and the bots."""

    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _spec(uid: int, rng: random.Random, team: str = "") -> Dict[str, Any]:
    from app.bots import personas
    from app.models import catalog
    tags = personas.draw_tags(rng, 7)
    traits = personas.derive_traits(tags, rng)
    hotbar = []
    for item_id in ("use_pistol", "use_shotgun", "use_stick",
                    rng.choice(["use_smg", "use_rifle", "use_sniper", ""]), ""):
        item = catalog.get(item_id) if item_id else None
        hotbar.append({"inv_id": uid * 10 + len(hotbar), "item_id": item["id"],
                       "name": item["name"], "slot": "usable", "tier": "normal",
                       "data": item["data"]} if item else None)
    return {"uid": uid, "name": "bot%d" % uid, "team": team,
            "avatar": {"user_id": uid, "username": "bot%d" % uid, "colors": {},
                       "items": {}, "hotbar": hotbar},
            "stats": [0, 0, 0], "tags": tags, "traits": traits,
            "bias": {"skill": 0.55, "reaction": 380, "aim": 3.5,
                     "objective": min(1.0, 0.72 * (0.5 + traits["objective"]))}}


def run_world(world_id: str, seconds: float, bots: int = 16, watcher: bool = True,
              state: Dict[str, Any] = None, seed: int = 11) -> Dict[str, Any]:
    import app.game.instance as engine
    import app.game.bots.brain as brain_module
    import app.game.bots.runner as runner_module
    import app.game.worlds.capture_the_flag as ctf_module
    import app.game.worlds.fortress_team2 as payload_module
    import app.game.worlds.burger_tycoon as tycoon_module
    import app.game.worlds.blackout_relay as relay_module
    clock = Clock()
    patched = [engine, brain_module, runner_module, ctf_module, payload_module,
               tycoon_module, relay_module]
    originals = [(m, m.now) for m in patched if hasattr(m, "now")]
    for module, _orig in originals:
        module.now = clock
    try:
        host = FakeHost(world_id)
        inst = host.cls(host, host.world, 7, host.map)
        from app.game.bots.runner import BotRunner
        rng = random.Random(seed)
        inst.bots = BotRunner(inst)
        teams = inst.team_names()
        specs = [_spec(100 + i, rng, teams[i % len(teams)] if world_id != "burger_tycoon" else "")
                 for i in range(bots)]
        inst.bots.wake(state or {"mode": inst.mode, "round": 1}, specs)
        # a pretend person standing about, so the bots run at full detail
        person = None
        if watcher:
            person = inst.add_player(1, "watcher", {"hotbar": []}, None)
            person.alive = True
            inst.bots.bot_cfg = host.bot_cfg
            host.bot_cfg["near_radius"] = 5000
        start = time.perf_counter()
        ticks = int(seconds / engine.TICK_DT)
        worst = 0.0
        for n in range(ticks):
            clock.t += engine.TICK_DT
            if person is not None:
                person.last_message = clock.t
            began = time.perf_counter()
            inst.tick()
            worst = max(worst, time.perf_counter() - began)
        elapsed = time.perf_counter() - start
        stuck = 0
        for brain in inst.bots.brains.values():
            p = brain.p
            if p.alive and brain.waypoints and math.dist(brain.last_progress[0], p.pos) < 0.5 \
                    and clock.t - brain.last_progress[1] > 8:
                stuck += 1
        chat = [e for e in inst.chat_log if e.get("kind") != "system"]
        system = [e.get("m", "") for e in inst.chat_log if e.get("kind") == "system"]
        result = {"inst": inst, "host": host, "ticks": ticks,
                  "ms_per_tick": elapsed / ticks * 1000.0, "worst_ms": worst * 1000.0,
                  "chat": chat, "system": system, "stuck": stuck,
                  "void": sum(1 for m in system if "the void" in m),
                  "kills": sum(p.kills for p in inst.players.values()),
                  "alive": sum(1 for p in inst.players.values() if p.alive)}
        return result
    finally:
        for module, original in originals:
            module.now = original


def test_live(seconds: float) -> None:
    print("\n== live (headless, %.0f simulated seconds each) ==" % seconds)
    for world_id, bots in (("capture_the_flag", 14), ("blackout_relay", 18),
                           ("fortress_team_2", 16), ("burger_tycoon", 14)):
        r = run_world(world_id, seconds, bots)
        inst = r["inst"]
        label = world_id
        if VERBOSE:
            print("   %s: %.2f ms/tick (worst %.1f), kills %d, chat %d, stuck %d"
                  % (world_id, r["ms_per_tick"], r["worst_ms"], r["kills"],
                     len(r["chat"]), r["stuck"]))
            for line in r["system"][-6:]:
                print("      sys:", line)
            for line in r["chat"][-6:]:
                print("      chat: %s: %s" % (line.get("from"), line.get("m")))
        check("%s: bots fight (kills happen)" % label, r["kills"] > 0, r["kills"])
        check("%s: nobody stuck for long" % label, r["stuck"] <= max(1, bots // 8), r["stuck"])
        check("%s: tick cost stays low" % label, r["ms_per_tick"] < 12.0,
              "%.2f ms" % r["ms_per_tick"])
        if inst.mode == "captures":
            taken = sum(1 for m in r["system"] if "picked up" in m)
            check("%s: flags get taken" % label, taken > 0, r["system"][-5:])
            if world_id == "capture_the_flag":
                caps = sum(inst.captures.values())
                check("%s: flags get captured" % label, caps > 0 or inst.round_number > 1,
                      inst.captures)
        elif inst.mode == "payload":
            check("%s: the cart moves" % label,
                  inst.cart_distance > 5 or inst.checkpoints_reached or inst.round_number > 1,
                  "distance %.1f" % inst.cart_distance)
        else:
            built = sum(len(p.built) for p in inst.plots)
            check("%s: restaurants get built" % label, built >= 3, built)


# ===================================================================== scale
def test_scale(count: int) -> None:
    print("\n== scale (%d bots) ==" % count)
    from app import bootstrap
    with contextlib.redirect_stdout(io.StringIO()):
        bootstrap.seed()
    from app.bots import config as bot_config, director as dm, factory
    bot_config.save({"llm.enabled": False, "creation.username_source": "procedural",
                     "creation.profile_source": "procedural"})
    d = dm.get()
    d.load()
    rng = random.Random(5)
    started = time.time()
    made = 0
    while made < count:
        made += len(factory.create_batch(min(250, count - made), rng, None))
    rate = made / max(0.001, time.time() - started)
    check("scale: created %d bots (%.0f/s)" % (made, rate), made == count)
    import app.game.registry as registry
    registry.STALE_AFTER = 1e9
    for world in dm.WORLD_IDS:
        registry.heartbeat(world, {"world": world, "players": 0, "instances": []})
    fresh = dm.Director()
    t = time.time()
    fresh.load()
    check("scale: director loads in under 5s", time.time() - t < 5, "%.2fs" % (time.time() - t))
    now = int(time.time())
    cost = 0.0
    for s in range(600):
        tt = now + s
        t0 = time.perf_counter()
        want = fresh.targets(tt)
        for i in fresh._due(tt, 4000):
            fresh._event(i, tt, *want)
        if s % 5 == 0:
            fresh._control(tt)
        fresh._summarise(tt)
        cost += time.perf_counter() - t0
    per_tick = cost / 600 * 1000.0
    want_online, want_playing = fresh.targets(now + 600)
    check("scale: online tracks the curve (within 5%)",
          abs(fresh.online - want_online) <= max(5, want_online * 0.05),
          "%d vs %d" % (fresh.online, want_online))
    check("scale: director tick %.2f ms" % per_tick, per_tick < 25.0)


def main(argv: List[str]) -> int:
    global VERBOSE
    parser = argparse.ArgumentParser()
    parser.add_argument("groups", nargs="*", default=["unit", "live", "scale"])
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--bots", type=int, default=20000)
    parser.add_argument("--seconds", type=float, default=150.0)
    args = parser.parse_args(argv[1:])
    VERBOSE = args.verbose
    isolate()
    if "unit" in args.groups:
        test_unit()
    if "live" in args.groups:
        test_live(args.seconds)
    if "scale" in args.groups:
        test_scale(args.bots)
    print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
    for name in FAILED:
        print("  failed: %s" % name)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
