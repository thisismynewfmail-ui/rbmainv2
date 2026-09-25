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
``chat``     the Dynamic Modifiers (DM momentum and its decay, in-game chat
             heat, bots answering each other within limits), Speech Events
             from each side of the round, the game state the host reports and
             the chat relay end to end with the language model stubbed out
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
              state: Dict[str, Any] = None, seed: int = 11,
              setup=None) -> Dict[str, Any]:
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
        if setup is not None:
            setup(inst)
        start = time.perf_counter()
        ticks = int(seconds / engine.TICK_DT)
        worst = 0.0
        inside = 0
        at_flag = 0
        checked = 0.0
        for n in range(ticks):
            clock.t += engine.TICK_DT
            if person is not None:
                person.last_message = clock.t
            began = time.perf_counter()
            inst.tick()
            worst = max(worst, time.perf_counter() - began)
            check_start = time.perf_counter()
            flags = getattr(inst, "flags", None)
            for brain in inst.bots.brains.values():
                if brain.p.alive and _inside_solid(inst, brain.p.pos):
                    inside += 1
                if flags and brain.p.alive and brain.p.team in flags:
                    enemy = flags["blue" if brain.p.team == "red" else "red"]
                    if math.dist(brain.p.pos, enemy.home) < 20:
                        at_flag += 1
            checked += time.perf_counter() - check_start
        elapsed = time.perf_counter() - start - checked
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
                  "inside": inside,
                  "at_flag": at_flag,
                  "rescues": sum(b.rescues for b in inst.bots.brains.values()),
                  "climbs": sum(b.climbs for b in inst.bots.brains.values()),
                  "short_climbs": sum(b.short_climbs for b in inst.bots.brains.values()),
                  "kills": sum(p.kills for p in inst.players.values()),
                  "alive": sum(1 for p in inst.players.values() if p.alive)}
        return result
    finally:
        for module, original in originals:
            module.now = original


def _inside_solid(inst, pos) -> bool:
    """Is a bot's body overlapping the map anywhere (beyond rounding)?"""
    from app.game.bots import body
    inset = 0.05
    x0, x1 = pos[0] - body.HALF_W + inset, pos[0] + body.HALF_W - inset
    z0, z1 = pos[2] - body.HALF_D + inset, pos[2] + body.HALF_D - inset
    y0, y1 = pos[1] + 0.1, pos[1] + body.HEIGHT - inset
    for lo, hi in inst._colliders_near([x0, y0, z0], [x1, y1, z1]):
        if hi[0] > x0 and lo[0] < x1 and hi[1] > y0 and lo[1] < y1 and hi[2] > z0 and lo[2] < z1:
            return True
    return False


def _carrier_run() -> int:
    """One bot on the enemy flag with the road home clear: it must pick the
    flag up and carry it all the way, whatever mood it was in."""
    def put_on_flag(inst):
        bot = next(p for p in inst.players.values() if p.brain is not None)
        if not bot.alive:
            # a round woken mid-game can start a bot on its respawn timer
            inst.spawn_player(bot)
        enemy = inst.flags[inst.enemy_of(bot.team)]
        bot.pos = list(enemy.home)
        bot.brain.ground = list(bot.pos)
        bot.brain.goal = "afk"            # the worst mood to be caught in
        bot.brain.afk_until = 1e12
        bot.brain.goal_until = 1e12
    r = run_world("capture_the_flag", 60.0, 1, setup=put_on_flag, seed=3)
    return sum(r["inst"].captures.values())


def test_live(seconds: float) -> None:
    print("\n== live (headless, %.0f simulated seconds each) ==" % seconds)
    for world_id in ("capture_the_flag", "blackout_relay", "fortress_team_2", "burger_tycoon"):
        host = FakeHost(world_id)
        inst = host.cls(host, host.world, 7, host.map)
        points = [sp for team in (inst.team_names() or [""]) for sp in inst.spawn_points(team)]
        for extra in (getattr(inst, "forward_spawns", None) or {}).values():
            points.extend(extra)
        stuck = [sp["p"] for sp in points if not inst.body_fits(*sp["p"])]
        check("%s: every spawn point has room for a body (%d points)" % (world_id, len(points)),
              not stuck, stuck)
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
        check("%s: no bot is ever inside the map's geometry" % label, r["inside"] == 0,
              "%d frames" % r["inside"])
        check("%s: no bot falls through the world and needs rescuing" % label,
              r["rescues"] == 0, r["rescues"])
        check("%s: ledge jumps land on the ledge (%d of %d fell short)"
              % (label, r["short_climbs"], r["climbs"]),
              r["short_climbs"] <= max(3, r["climbs"] // 10), r["short_climbs"])
        check("%s: tick cost stays low" % label, r["ms_per_tick"] < 12.0,
              "%.2f ms" % r["ms_per_tick"])
        if inst.mode == "captures":
            taken = sum(1 for m in r["system"] if "picked up" in m)
            # a round can go a couple of minutes without a grab, as real ones
            # do; bots standing at the enemy flag shows they went for it
            check("%s: bots go for the enemy flag (%d taken, %d bot-seconds at it)"
                  % (label, taken, r["at_flag"] // 20), taken > 0 or r["at_flag"] >= 40,
                  r["system"][-5:])
            if world_id == "capture_the_flag":
                caps = _carrier_run()
                check("%s: a bot holding the flag runs it home and scores" % label,
                      caps > 0, "captures %d" % caps)
        elif inst.mode == "payload":
            check("%s: the cart moves" % label,
                  inst.cart_distance > 5 or inst.checkpoints_reached or inst.round_number > 1,
                  "distance %.1f" % inst.cart_distance)
        else:
            built = sum(len(p.built) for p in inst.plots)
            check("%s: restaurants get built" % label, built >= 3, built)


# ====================================================================== chat
class _StubDirector:
    """What the chat relay and the chatter engine ask of the director."""

    def __init__(self, names: Dict[int, str]):
        import threading
        self.names = names
        self.lock = threading.RLock()
        self.ops = {w: [] for w in ("burger_tycoon", "capture_the_flag",
                                    "fortress_team_2", "blackout_relay")}
        self.chatter = None

    def enabled(self) -> bool:
        return True

    def card(self, uid: int) -> Dict[str, Any]:
        return {"id": uid, "name": self.names.get(uid, "bot%d" % uid), "tags": ["friendly"],
                "traits": {"chatty": 0.7}, "joined": 1700000000, "blurb": ""}

    def index_of(self, uid: int) -> int:
        return 0 if uid in self.names else -1


class _StubLLM:
    """Answers every chat request at once, and remembers the prompts."""

    def __init__(self, reply: str = "no way", up: bool = True):
        self.prompts: List[Dict[str, Any]] = []
        self.reply = reply
        self.up = up

    def context_limit(self) -> int:
        return 16000

    def estimate_tokens(self, text: str) -> int:
        return len(text or "") // 4 + 1

    def submit(self, kind, priority, build, done, ttl=600.0, bot=0) -> bool:
        if not self.up:
            return False
        request = build()
        self.prompts.append({"kind": kind, "bot": bot, "request": request})
        done(self.reply + " %d" % len(self.prompts), None)
        return True


def test_chat() -> None:
    print("\n== chat: dynamic modifiers and speech events ==")
    from app import bootstrap
    with contextlib.redirect_stdout(io.StringIO()):
        bootstrap.seed()
    from app.bots import config as bot_config, gamechat, llm, modifiers, speech
    bot_config.save({"llm.enabled": True})

    # ---- DM momentum
    m = modifiers.Momentum()
    t = 1000.0
    m.heard(7, 1, t)                          # they write
    m.replied(7, 1, t + 40)                   # the bot answers
    m.heard(7, 1, t + 45)                     # they answer back: 1 turn
    check("momentum: one back-and-forth is not enough (needs 2)",
          m.speedup(7, 1, t + 45) == 0.0, m.speedup(7, 1, t + 45))
    m.replied(7, 1, t + 60)
    m.heard(7, 1, t + 60)                     # straight back: 2 turns
    check("momentum: two back-and-forths make the bot 30% quicker",
          abs(m.speedup(7, 1, t + 60) - 0.30) < 1e-6, m.speedup(7, 1, t + 60))
    m.replied(7, 1, t + 70)
    m.heard(7, 1, t + 70)                     # third turn, straight back
    check("momentum: each further turn adds 10%",
          abs(m.speedup(7, 1, t + 70) - 0.40) < 1e-6, m.speedup(7, 1, t + 70))
    m.replied(7, 1, t + 80)
    m.heard(7, 1, t + 110)                    # 30 s to answer: half the boost left
    check("momentum: a 30 s pause leaves half of it (decay 60 s)",
          abs(m.speedup(7, 1, t + 110) - 0.25) < 1e-6, m.speedup(7, 1, t + 110))
    check("momentum: a bot mid-conversation counts as talking", m.talking(7, t + 120))
    m.replied(7, 1, t + 120)
    m.heard(7, 1, t + 190)                    # over a minute: gone, start again
    check("momentum: after the decay time it is gone and the count restarts",
          m.speedup(7, 1, t + 190) == 0.0 and m.pairs[(7, 1)]["turns"] == 0)
    check("momentum: nobody talking once it has faded", not m.talking(7, t + 400))
    for _ in range(12):
        m.replied(9, 2, t)
        m.heard(9, 2, t)
    check("momentum: never more than the ceiling (70%)",
          abs(m.speedup(9, 2, t) - 0.70) < 1e-6, m.speedup(9, 2, t))
    bot_config.save({"modifiers.dm_enabled": False})
    check("momentum: switched off, replies are never quicker", m.speedup(9, 2, t) == 0.0)
    bot_config.save({"modifiers.dm_enabled": True})

    # ---- the chatter engine uses it for the reply delay
    from app.bots import chatter
    stub = _StubDirector({50: "botty"})
    engine = chatter.Engine(stub)
    bot_config.save({"messages.dm_delay_seconds": [100, 100]})
    delays = []
    for turn in range(3):
        before = chatter._now()
        engine.on_dm(50, 3, "someone", "hey %d" % turn)
        delays.append(round(engine.pending_dm[50][3] - before))
        engine._clear_dm(50, 3)
        engine.momentum.replied(50, 3, chatter._now())
    check("momentum: the DM reply delay shrinks once it is a conversation",
          delays[0] >= 99 and delays[2] <= 71, delays)
    bot_config.save({"messages.dm_delay_seconds": [20, 180]})

    # ---- chat heat
    heat = modifiers.Heat()
    check("heat: one line is no boost", heat.multiplier(0.0) == 1.0 or not heat.lines)
    heat.heard(1, 0.0)
    heat.heard(1, 5.0)
    heat.heard(1, 10.0)
    hot = heat.multiplier(10.0, 1)
    check("heat: a player who keeps talking is likelier to get an answer", hot > 1.5, hot)
    check("heat: it fades back to normal once they stop", heat.multiplier(75.0, 1) == 1.0,
          heat.multiplier(75.0, 1))
    heat.answered(1, 99, 10.0)
    partner, warmth = heat.partner_of(1, 40.0)
    check("heat: the bot they were talking with stays their partner, fading",
          partner == 99 and 0.4 < warmth < 0.6, (partner, warmth))

    # ---- speech: every event reads from both sides
    red = speech.describe({"kind": "flag_take", "team": "red", "by": "Fox", "by_team": "blue"}, "ann", "red")
    blue = speech.describe({"kind": "flag_take", "team": "red", "by": "Fox", "by_team": "blue"}, "bob", "blue")
    check("speech: a stolen flag is bad news for its team", red[1] == "victim" and "YOUR team's flag" in red[0], red)
    check("speech: ...and good news for the thief's team", blue[1] == "ally" and "teammate Fox" in blue[0], blue)
    missing = [k.id for k in speech.KINDS
               if not speech.describe(dict(kind=k.id, by="x", by_team="red", team="red", winner="red",
                                           attackers="red", n=3, victim="y", plot="P"), "me", "red")[0]]
    check("speech: every event has something to say", not missing, missing)
    check("speech: events only happen in their own worlds",
          speech.applies("flag_take", "capture_the_flag") and not speech.applies("flag_take", "burger_tycoon")
          and speech.applies("tycoon_build", "burger_tycoon") and speech.applies("killstreak", "fortress_team_2"))

    # ---- the host reports events, the round's state and each bot's view
    def give_flag(inst):
        bot = next(p for p in inst.players.values() if p.brain is not None)
        if not bot.alive:
            inst.spawn_player(bot)
        enemy = inst.flags[inst.enemy_of(bot.team)]
        bot.pos = list(enemy.home)
        bot.brain.ground = list(bot.pos)
    r = run_world("capture_the_flag", 40.0, 1, setup=give_flag, seed=3)
    report = r["inst"].bots.chat_report() or {}
    kinds = [e.get("kind") for e in report.get("speech", [])]
    state = report.get("state") or {}
    me = ((report.get("bots") or [{}])[0]).get("me") or {}
    check("host: taking and capturing the flag are reported as speech events",
          "flag_take" in kinds and "flag_capture" in kinds, kinds)
    check("host: the report carries the score and the flags",
          sum((state.get("score") or {}).values()) >= 1 and set(state.get("flags") or {}) == {"red", "blue"},
          state)
    check("host: and the bot's own view (kills, job)", "kills" in me and "role" in me, me)

    # ---- the relay, end to end with the model stubbed out
    bots = {11: "ann", 12: "bob", 13: "cara"}
    stub = _StubDirector(bots)
    relay = gamechat.Relay(stub)
    sent: List[Any] = []
    relay._send = lambda room, uid, text, delay: sent.append((uid, text, delay))
    fake = _StubLLM()
    real_client = llm.client
    llm.client = lambda: fake
    try:
        bot_config.save({"speech.chances": dict(speech.DEFAULT_CHANCES, flag_take=100),
                         "speech.max_voices": 2, "speech.follow_chance": 100,
                         "messages.chat_per_minute": 30})
        roster = [{"uid": 11, "name": "ann", "team": "red", "traits": {"chatty": 0.6},
                   "me": {"alive": True, "kills": 2, "deaths": 1, "role": "defend"}},
                  {"uid": 12, "name": "bob", "team": "blue", "traits": {"chatty": 0.6}, "me": {}},
                  {"uid": 13, "name": "cara", "team": "red", "traits": {"chatty": 0.6}, "me": {}}]
        base = {"inst": 4, "bots": roster, "humans": [{"uid": 1, "name": "Fox", "team": "blue"}],
                "state": {"mode": "captures", "phase": "active", "score": {"red": 0, "blue": 1},
                          "target": 3, "time_left": 200,
                          "flags": {"red": {"state": "carried", "by": "Fox", "by_team": "blue"},
                                    "blue": {"state": "home"}}}}
        relay.on_report("capture_the_flag", dict(base, lines=[], speech=[
            {"kind": "flag_take", "team": "red", "by": "Fox", "by_team": "blue"}]))
        check("relay: a stolen flag gets reactions (chance 100%, two voices)", len(sent) == 2, sent)
        text = " ".join(m["content"] for p in fake.prompts for m in p["request"]["messages"])
        check("relay: the bot is told what happened, from its side",
              "Just now:" in text and ("YOUR team's flag" in text or "teammate Fox" in text), text[-400:])
        check("relay: ...with the round's state as background",
              "Score: your team" in text and "background only" in text)
        sent.clear()
        fake.prompts.clear()
        relay.on_report("capture_the_flag", dict(base, lines=[], speech=[
            {"kind": "flag_take", "team": "red", "by": "Fox", "by_team": "blue"}]))
        check("relay: the same kind of event waits out its cooldown", not sent, sent)

        # chat heat: a player who keeps talking gets answered more often
        bot_config.save({"messages.chat_reply_chance": 20, "speech.enabled": False})

        def answered(lines_said: int, trials: int = 200) -> float:
            hits = 0
            for trial in range(trials):
                relay.rooms.clear()
                sent.clear()
                for n in range(lines_said):
                    relay.on_report("capture_the_flag", dict(base, lines=[
                        {"who": "Fox", "uid": 1, "text": "this map is wild", "team": "blue",
                         "at": time.time(), "bot": False}], speech=[]))
                    got = bool(sent)
                    sent.clear()
                hits += got
            return hits / float(trials)
        cold, warm = answered(1), answered(4)
        check("heat: the fourth line in a row is likelier to get an answer than the first",
              warm > cold * 1.4, "%.2f vs %.2f" % (warm, cold))

        # bots answering bots stops at the limit
        bot_config.save({"modifiers.bot_reply_chance": 100, "modifiers.bot_chain_fade": 0,
                         "modifiers.bot_chain_max": 3, "messages.chat_per_minute": 100})
        relay.rooms.clear()
        sent.clear()
        per_line = []
        for n in range(8):
            before = len(sent)
            relay.on_report("capture_the_flag", dict(base, lines=[
                {"who": "ann", "uid": 11, "text": "anyone on d", "team": "red",
                 "at": time.time(), "bot": True}], speech=[]))
            per_line.append(len(sent) - before)
        check("bots: bots answer each other, but never past the limit (3 lines)",
              1 <= sum(per_line[:3]) <= 3 and sum(per_line[3:]) == 0, per_line)
        relay.on_report("capture_the_flag", dict(base, lines=[
            {"who": "Fox", "uid": 1, "text": "lol", "team": "blue", "at": time.time(), "bot": False}],
            speech=[]))
        check("bots: a real player speaking resets the limit",
              relay.rooms[("capture_the_flag", 4)].chain == 0)

        # the model down: speech events still get a stock line
        bot_config.save({"speech.enabled": True, "speech.cooldown_seconds": 0})
        fake.up = False
        relay.rooms.clear()
        sent.clear()
        relay.on_report("capture_the_flag", dict(base, lines=[], speech=[
            {"kind": "flag_take", "team": "red", "by": "Fox", "by_team": "blue"}]))
        check("relay: with the model down a stolen flag still gets a stock line",
              sent and all(isinstance(s_[1], str) and s_[1] for s_ in sent), sent)
    finally:
        llm.client = real_client
        bot_config.reset("modifiers")
        bot_config.reset("speech")
        bot_config.save({"messages.chat_reply_chance": 60, "messages.chat_per_minute": 8})


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
        for i in fresh._due(tt, 800):
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
    import resource
    from app import config as site_config
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    size = sum(p.stat().st_size
               for p in site_config.DB_PATH.parent.glob(site_config.DB_PATH.name + "*"))
    folders = sum(1 for _ in (site_config.DATA_DIR / "bots" / "accounts").glob("*/*"))
    print("  info  peak memory %.0f MB for the whole process; database %.1f MB (%.1f KB per bot);"
          " %d bot folders" % (rss, size / 1e6, size / 1024.0 / max(1, count), folders))


def main(argv: List[str]) -> int:
    global VERBOSE
    parser = argparse.ArgumentParser()
    parser.add_argument("groups", nargs="*", default=["unit", "chat", "live", "scale"])
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--bots", type=int, default=20000)
    parser.add_argument("--seconds", type=float, default=150.0)
    args = parser.parse_args(argv[1:])
    VERBOSE = args.verbose
    isolate()
    if "unit" in args.groups:
        test_unit()
    if "chat" in args.groups:
        test_chat()
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
