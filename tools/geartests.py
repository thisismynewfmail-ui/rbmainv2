#!/usr/bin/env python3
"""Headless tests for the event weapons' mechanics (app/game/gear.py).

    python3 tools/geartests.py            # every check
    python3 tools/geartests.py -v         # ...and what each weapon did

No server: a Blackout Relay round and a Last Light round are built in
process on a simulated clock, two players are put in them with any item on
the hotbar, and the tests fire, swing, throw and summon and look at what the
round does -- damage, statuses, minions, turrets, strikes, sticky bombs,
boomerangs -- and at what the players were told.  Every event weapon in the
catalogue is also fired once each way it can be, to be sure none of them
throws.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Any, Dict, List

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tools"))

VERBOSE = "-v" in sys.argv
PASSED: List[str] = []
FAILED: List[str] = []


def check(name: str, ok: bool, detail: Any = "") -> bool:
    (PASSED if ok else FAILED).append(name)
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  %s" % (detail,)))
    return ok


class Clock:
    def __init__(self):
        self.t = 5000.0

    def __call__(self):
        return self.t


class Wire:
    """A websocket that keeps what it is sent."""

    def __init__(self):
        self.sent: List[Dict[str, Any]] = []

    def send_json(self, payload):
        self.sent.append(payload)

    def close(self, *a):
        pass

    def of(self, kind: str) -> List[Dict[str, Any]]:
        return [m for m in self.sent if m.get("t") == kind]


def hotbar_entry(item_id: str, inv: int = 1) -> Dict[str, Any]:
    from app.models import catalog
    item = catalog.get(item_id)
    return {"inv_id": inv, "item_id": item["id"], "name": item["name"], "slot": "usable",
            "tier": "normal", "data": item["data"]}


def make_world(world_id: str = "blackout_relay"):
    import bottests
    import app.game.instance as engine
    import app.game.gear as gear_module
    clock = Clock()
    patched = [engine]
    for name in ("app.game.worlds.blackout_relay", "app.game.worlds.last_light",
                 "app.game.worlds.infected", "app.game.worlds.capture_the_flag"):
        __import__(name)
        patched.append(sys.modules[name])
    for module in patched:
        if hasattr(module, "now"):
            module.now = clock
    gear_module._now = clock
    host = bottests.FakeHost(world_id)
    inst = host.cls(host, host.world, 3, host.map)
    return inst, clock


def add(inst, name: str, team: str, items: List[str], pos=None):
    from app.game.instance import Player
    wire = Wire()
    hotbar = [hotbar_entry(i, n + 1) for n, i in enumerate(items)]
    while len(hotbar) < 5:
        hotbar.append(None)
    p = inst.add_player(100 + len(inst.players), name, {"hotbar": hotbar}, wire)
    if p is None:
        raise RuntimeError("could not add %s" % name)
    p.ws = wire
    p.team = team
    p.alive = True
    p.health = 100
    p.spawn_protect_until = 0.0
    p.reset_ammo()
    if pos is not None:
        p.pos = list(pos)
    p.grounded = True
    return p, wire


def aim_at(a, b) -> List[float]:
    d = [b.pos[0] - a.pos[0], (b.pos[1] + 2.6) - (a.pos[1] + 5.05), b.pos[2] - a.pos[2]]
    n = math.sqrt(sum(v * v for v in d))
    return [v / n for v in d]


def run(inst, clock, seconds: float) -> None:
    import app.game.instance as engine
    for _ in range(int(seconds / engine.TICK_DT)):
        clock.t += engine.TICK_DT
        for p in inst.players.values():
            p.last_message = clock.t
        inst.tick()


def fire(inst, clock, p, direction, times: int = 1, gap: float = 0.0) -> None:
    for _ in range(times):
        p.next_fire = 0.0
        p.reload_until = 0.0
        inst.handle_fire(p, {"d": direction})
        if gap:
            run(inst, clock, gap)


def flat_spot(inst):
    """A clear, flat stretch of the map to test on: a spawn point."""
    sp = inst.spawn_points("red")[0]["p"]
    return [float(sp[0]), float(sp[1]), float(sp[2])]


def pair(inst, clock, items: List[str], gap: float = 14.0):
    """Alice (red, holding ``items``) and Bob (blue) ``gap`` apart on open
    ground, facing each other."""
    best = None
    for sp in inst.spawn_points("red") + inst.spawn_points("blue"):
        spot = [float(sp["p"][0]), float(sp["p"][1]), float(sp["p"][2])]
        eye = [spot[0], spot[1] + 3.0, spot[2]]
        for yaw in (0.0, math.pi / 2, math.pi, -math.pi / 2):
            d = [math.sin(yaw), 0.0, math.cos(yaw)]
            clear = inst.ray_world(eye, d, gap * 2.5 + 10)
            if clear >= gap * 2.5 + 10:
                best = (spot, yaw, d)
                break
        if best:
            break
    spot, yaw, d = best or (flat_spot(inst), 0.0, [0.0, 0.0, 1.0])
    a, wa = add(inst, "Alice", "red", items, spot)
    b, wb = add(inst, "Bob", "blue", ["use_pistol"],
                [spot[0] + d[0] * gap, spot[1], spot[2] + d[2] * gap])
    a.yaw = yaw
    b.yaw = yaw + math.pi
    a.extra["fwd"] = d
    return a, wa, b, wb


def reset_players(inst):
    for pid in list(inst.players):
        inst.remove_player(pid)
    inst.gear.reset()


# ================================================================ tests
def test_statuses():
    print("\n== statuses ==")
    inst, clock = make_world()
    a, wa, b, wb = pair(inst, clock, ["use_pistol"])
    g = inst.gear
    g.apply(b, "burn", 2.0, 10.0, a, "Test Flame")
    before = b.health
    run(inst, clock, 2.2)
    check("burn: damage over time, credited and then gone", 15 <= before - b.health <= 25
          and not g.has(b, "burn"), before - b.health)
    g.apply(b, "slow", 3.0, 0.4, a)
    check("slow: 40%% slower", abs(g.move_scale(b) - 0.6) < 1e-6, g.move_scale(b))
    g.apply(b, "root", 1.0, 1, a)
    check("root: cannot move, the host corrects a move", not g.can_move(b))
    old = list(b.pos)
    wb.sent.clear()
    clock.t += 0.1
    inst.handle_input(b, {"p": [old[0] + 6, old[1], old[2]], "v": [0, 0, 0], "g": 1})
    check("root: ...and a move while rooted is put back", b.pos == old and wb.of("correct"),
          b.pos)
    g.apply(b, "mark", 4.0, 0.5, a)
    b.health = 100
    inst.apply_damage(b, a, 20, "Test", False)
    check("mark: +50% damage taken", abs(b.health - 70) < 0.01, b.health)
    g.apply(b, "shield", 4.0, 15, b)
    b.health = 100
    g.remove(b, "mark")
    inst.apply_damage(b, a, 20, "Test", False)
    check("shield: soaks damage until it is used up", abs(b.health - 95) < 0.01 and not g.has(b, "shield"),
          b.health)
    g.apply(b, "cheat", 10.0, 1, b)
    b.health = 10
    inst.apply_damage(b, a, 50, "Test", False)
    check("cheat: a killing blow leaves 1 hp once", b.alive and b.health == 1 and not g.has(b, "cheat"),
          (b.alive, b.health))
    run(inst, clock, 0.1)
    st = wb.of("st")
    check("statuses are sent to the player they are on", st and isinstance(st[-1].get("s"), dict), st[-1:] )
    snap = inst.snapshot()
    row = next(r for r in snap["ps"] if r[0] == b.pid)
    check("statuses ride in the snapshot as bits", len(row) >= 11 and isinstance(row[10], int))
    g.apply(b, "stun", 1.0, 1, a)
    b.next_fire = 0
    shots = len(inst.projectiles)
    inst.handle_fire(b, {"d": [0, 0, -1]})
    check("stun: no firing", b.ammo[0] == int(b.weapon_stats().get("mag", 0)), b.ammo[0])
    reset_players(inst)


def test_weapons():
    print("\n== the New Year weapons ==")
    inst, clock = make_world()
    g = inst.gear

    # Countdown Crackler: sticks, then goes off on its fuse
    a, wa, b, wb = pair(inst, clock, ["use_ny22_countdown_crackler"], gap=20)
    fire(inst, clock, a, aim_at(a, b))
    run(inst, clock, 0.6)
    stuck = [p for p in inst.projectiles if "stuck" in p.data]
    check("crackler: the clockbomb sticks to what it hits", stuck, [p.data for p in inst.projectiles])
    hp = b.health
    run(inst, clock, 3.2)
    check("crackler: ...and goes off on its fuse", not inst.projectiles and b.health < hp,
          (len(inst.projectiles), b.health))
    reset_players(inst)

    # Sequin Saber: three cuts dazzle into a mark
    a, wa, b, wb = pair(inst, clock, ["use_ny23_sequin_saber"], gap=5)
    b.health = 1000
    fire(inst, clock, a, aim_at(a, b), times=3, gap=0.5)
    check("sequin saber: three hits dazzle into a mark", g.has(b, "mark"),
          {n: (h.stacks, round(h.value, 2)) for n, h in (g.status.get(b.pid) or {}).items()})
    reset_players(inst)

    # Gold Rush: a kill refills and loads ricochets
    a, wa, b, wb = pair(inst, clock, ["use_ny23_gold_rush"], gap=20)
    fwd = a.extra["fwd"]
    c, wc = add(inst, "Cara", "blue", ["use_pistol"],
                [b.pos[0] + fwd[0] * 7, b.pos[1], b.pos[2] + fwd[2] * 7])
    a.ammo[0] = 2
    b.health = 25
    fire(inst, clock, a, aim_at(a, b))
    st = g._wstate(a, "use_ny23_gold_rush")
    check("gold rush: a kill refills the cylinder", not b.alive and a.ammo[0] == 6, (b.alive, a.ammo[0]))
    check("gold rush: ...and loads ricochets", st.get("ricochets") == 3, st)
    c.health = 100
    inst.spawn_player(b)           # back in, and back where he was
    b.pos = [c.pos[0] - fwd[0] * 7, c.pos[1], c.pos[2] - fwd[2] * 7]
    b.health = 100
    b.spawn_protect_until = 0
    fire(inst, clock, a, aim_at(a, b))
    check("gold rush: a ricochet jumps to the next enemy", c.health < 100 and b.health < 100,
          (b.health, c.health))
    reset_players(inst)

    # Roman Candle: a volley of eight fireballs that set alight
    a, wa, b, wb = pair(inst, clock, ["use_ny24_roman_candle"], gap=18)
    b.health = 1000
    fire(inst, clock, a, aim_at(a, b))
    launched = len([m for m in wa.sent if m.get("t") == "proj"]) + \
        len([m for m in wb.sent if m.get("t") == "proj"])
    run(inst, clock, 1.5)
    launched = len(wb.of("proj"))
    check("roman candle: one pull fires the whole volley", launched >= 8, launched)
    check("roman candle: ...and they set alight", g.has(b, "burn") or b.health < 1000, b.health)
    reset_players(inst)

    # Sky Bloom: the shell bursts into bomblets
    a, wa, b, wb = pair(inst, clock, ["use_ny24_sky_bloom"], gap=26)
    fire(inst, clock, a, aim_at(a, b))
    run(inst, clock, 1.2)
    kinds = [m.get("k") for m in wb.of("proj")]
    check("sky bloom: the shell breaks into bomblets", kinds.count("bomblet") >= 4, kinds)
    reset_players(inst)

    # Midnight Mallet: every 12 hits the clock strikes
    a, wa, b, wb = pair(inst, clock, ["use_ny22_midnight_mallet"], gap=5)
    b.health = 5000
    fire(inst, clock, a, aim_at(a, b), times=12, gap=0.8)
    blasts = [m for m in wb.sent if m.get("t") == "fx" and m.get("k") == "explode"]
    check("midnight mallet: the twelfth hit chimes", blasts, [m.get("k") for m in wb.sent[-20:]])
    reset_players(inst)

    # Synth Laser: ramps and overheats
    a, wa, b, wb = pair(inst, clock, ["use_ny25_synth_laser"], gap=20)
    b.health = 5000
    first = None
    for k in range(120):
        before = b.health
        fire(inst, clock, a, aim_at(a, b))
        if first is None:
            first = before - b.health
        run(inst, clock, 0.1)
    last = [m for m in wa.of("dealt")][-1]["a"] if wa.of("dealt") else 0
    check("synth laser: damage ramps up on a held beam", last > first * 1.5, (first, last))
    check("synth laser: ...until it overheats", any(m.get("m") == "Overheated!" for m in wa.of("notice")))
    reset_players(inst)

    # Vinyl: out, back, through
    a, wa, b, wb = pair(inst, clock, ["use_ny25_vinyl_disc"], gap=16)
    fwd = a.extra["fwd"]
    c, wc = add(inst, "Cara", "blue", ["use_pistol"],
                [b.pos[0] + fwd[0] * 8, b.pos[1], b.pos[2] + fwd[2] * 8])
    fire(inst, clock, a, aim_at(a, b))
    run(inst, clock, 3.0)
    check("vinyl disc: it passes through and comes home", b.health < 100 and not inst.projectiles
          and a.ammo[0] == 1, (b.health, len(inst.projectiles), a.ammo[0]))
    reset_players(inst)

    # Disco grenade: a turret that shoots
    a, wa, b, wb = pair(inst, clock, ["use_ny25_disco_grenade"], gap=14)
    b.health = 1000
    fire(inst, clock, a, aim_at(a, b))
    run(inst, clock, 3.0)
    check("disco grenade: a turret goes down and fires", g.deployables and b.health < 1000,
          (len(g.deployables), b.health))
    check("disco grenade: ...and the item goes on cooldown", g.cooldown_left(a, "use_ny25_disco_grenade") > 0)
    reset_players(inst)

    # Glowstick: a healing zone
    a, wa, b, wb = pair(inst, clock, ["use_ny25_glowstick"], gap=30)
    a.health = 40
    fire(inst, clock, a, [a.extra["fwd"][0], -0.2, a.extra["fwd"][2]])
    run(inst, clock, 3.0)
    check("glowstick: the zone heals", a.health > 40, a.health)
    reset_players(inst)

    # Ball Drop: a strike lands where you point
    a, wa, b, wb = pair(inst, clock, ["use_ny26_ball_drop"], gap=20)
    fire(inst, clock, a, aim_at(a, b))
    hp = b.health
    run(inst, clock, 0.5)
    check("ball drop: the warning goes up first", wb.of("gfx") and b.health == hp)
    run(inst, clock, 2.0)
    check("ball drop: ...then it lands", b.health < hp or not b.alive, b.health)
    reset_players(inst)

    # Party horn: a cone that pushes and stuns
    a, wa, b, wb = pair(inst, clock, ["use_ny26_party_horn"], gap=8)
    fire(inst, clock, a, aim_at(a, b))
    check("party horn: the cone hits, shoves and stuns", b.health < 100 and wb.of("knock")
          and g.has(b, "stun"), (b.health, len(wb.of("knock"))))
    reset_players(inst)

    # Cider and grapes: consume
    a, wa, b, wb = pair(inst, clock, ["use_ny23_cider", "use_ny26_grapes"], gap=30)
    a.health = 40
    fire(inst, clock, a, [0, 0, 1])
    run(inst, clock, 3.2)
    check("cider: heals over time and hastes", a.health > 55 and wa.of("cd"), a.health)
    a.slot = 1
    fire(inst, clock, a, [0, 0, 1])
    check("grapes: a crit buff", g.has(a, "crit"))
    reset_players(inst)

    # Noisemaker and bottle rocket: abilities
    a, wa, b, wb = pair(inst, clock, ["use_ny22_noisemaker", "use_ny24_bottle_rocket"], gap=30)
    fire(inst, clock, a, [0, 0, 1])
    check("noisemaker: rallies its holder", g.has(a, "haste"))
    a.slot = 1
    fire(inst, clock, a, [0, 0, 1])
    check("bottle rocket: launches", any(m.get("v", [0, 0])[1] > 40 for m in wa.of("knock")))
    reset_players(inst)


def test_minions():
    print("\n== summons ==")
    inst, clock = make_world()
    g = inst.gear
    a, wa, b, wb = pair(inst, clock, ["use_pistol"], gap=24)
    staff = {"kind": "summon", "cooldown": 60, "cost_hp": 25,
             "minion": {"name": "Restless Dead", "model": "zombie", "count": 4, "hp": 60,
                        "speed": 15, "damage": 12, "reach": 4.5, "rate": 1.0, "secs": 30}}
    a.avatar["hotbar"][0]["data"] = {"stats": staff, "parts": []}
    a.avatar["hotbar"][0]["item_id"] = "use_test_staff"
    b.health = 1000
    fire(inst, clock, a, [0, 0, 1])
    check("summon: four of them rise", len(g.minions) == 4, len(g.minions))
    check("summon: ...at a cost in health", a.health == 75, a.health)
    check("summon: ...and the staff goes on a minute's cooldown",
          59 < g.cooldown_left(a, "use_test_staff") <= 60)
    run(inst, clock, 6.0)
    check("summon: they go for the enemy and bite", b.health < 1000, b.health)
    snap = inst.snapshot()
    check("summon: they ride in the snapshot", len(snap.get("mn") or []) == 4)
    m = next(iter(g.minions.values()))
    hp = m.health
    b.next_fire = 0
    inst.handle_fire(b, {"d": _aim_pos(b, m.centre())})
    check("summon: an enemy can shoot them down", m.health < hp or not m.alive, (hp, m.health))
    run(inst, clock, 30.0)
    check("summon: they crumble when their time is up", not g.minions, len(g.minions))
    reset_players(inst)

    # in Last Light they fight the infected
    inst, clock = make_world("last_light")
    g = inst.gear
    spot = None
    a, wa = add(inst, "Alice", "survivors", ["use_pistol"])
    inst.deploy(a)
    a.avatar["hotbar"][0]["data"] = {"stats": staff, "parts": []}
    a.avatar["hotbar"][0]["item_id"] = "use_test_staff"
    a.spawn_protect_until = 0
    z = inst._spawn_common([a.pos[0] + 12, a.pos[1], a.pos[2]])
    z.state = "walk"
    fire(inst, clock, a, [0, 0, 1])
    hp = z.health
    run(inst, clock, 4.0)
    check("last light: the risen go for the infected", z.health < hp or not z.alive, (hp, z.health))
    bitten = [m for m in wa.of("dmg") if m.get("by") == "Alice's Restless Dead"]
    check("last light: ...and leave the survivors alone", not bitten, bitten[:2])


def test_circus():
    """Halloween 2025's set: balloon dogs that pop, pins that hit harder off
    every wall, a whip that drags."""
    print("\n== the big top ==")
    from app.game.instance import Projectile
    inst, clock = make_world()
    g = inst.gear
    a, wa, b, wb = pair(inst, clock, ["use_hw25_balloon_animals"], gap=22)
    b.health = 1000
    fire(inst, clock, a, aim_at(a, b))
    check("balloons: three dogs are twisted", len(g.minions) == 3, len(g.minions))
    run(inst, clock, 6.0)
    check("balloons: they run at the enemy and pop", b.health < 1000 and not g.minions,
          (b.health, len(g.minions)))
    pops = [m for m in wb.sent if m.get("k") == "explode" and m.get("kind") == "confetti"]
    check("balloons: ...in confetti", bool(pops), len(pops))
    reset_players(inst)

    # bounce_ramp: the same blast, once fresh and once off two walls
    a, wa, b, wb = pair(inst, clock, ["use_pistol"], gap=22)
    taken = []
    for ramp in (1.0, 2.0):
        b.health = 1000
        proj = Projectile.__new__(Projectile)
        proj.pid_owner, proj.team = a.pid, a.team
        proj.pos = [b.pos[0], b.pos[1] + 2.6, b.pos[2]]
        proj.vel = [0.0, 0.0, 0.0]
        proj.stats = {"splash": 3.0, "splash_damage": 14, "damage": 14, "knockback": 0,
                      "self_damage": 0.0}
        proj.born, proj.kind, proj.weapon, proj.ident = clock.t, "pin", "Juggler's Pins", 0
        proj.data = {"ramp": ramp}
        inst.explode(proj)
        taken.append(1000 - b.health)
    check("pins: a pin that has come off walls hits harder", taken[1] > taken[0] * 1.8, taken)
    reset_players(inst)

    a, wa, b, wb = pair(inst, clock, ["use_hw25_ringmaster_whip"], gap=12)
    b.health = 1000
    fire(inst, clock, a, aim_at(a, b))
    check("whip: it reaches 12 studs and cracks", b.health < 1000, b.health)
    check("whip: ...marks whoever it catches", g.has(b, "mark"))
    pulls = wb.of("knock")
    toward = pulls and (pulls[-1]["v"][0] * (a.pos[0] - b.pos[0]) +
                        pulls[-1]["v"][2] * (a.pos[2] - b.pos[2])) > 0
    check("whip: ...and drags them in", bool(toward), pulls[-1:] if pulls else None)
    reset_players(inst)


def _aim_pos(p, point):
    d = [point[0] - p.pos[0], point[1] - (p.pos[1] + 5.05), point[2] - p.pos[2]]
    n = math.sqrt(sum(v * v for v in d))
    return [v / n for v in d]


def test_every_weapon():
    """Fire every event weapon and held item a few ways; nothing may throw."""
    print("\n== every event weapon, fired ==")
    from app.models import catalog
    usable = [it["id"] for it in catalog.ALL_ITEMS if it["slot"] == "usable" and it.get("event")]
    errors = []
    for world in ("blackout_relay", "last_light"):
        inst, clock = make_world(world)
        for item_id in usable:
            try:
                if world == "last_light":
                    a, wa = add(inst, "Alice", "survivors", [item_id])
                    inst.deploy(a)
                    a.spawn_protect_until = 0
                    target = inst._spawn_common([a.pos[0], a.pos[1], a.pos[2] + 12])
                    target.state = "walk"
                    d = _aim_pos(a, target.centre())
                else:
                    a, wa, b, wb = pair(inst, clock, [item_id], gap=12)
                    b.health = 2000
                    d = aim_at(a, b)
                for _ in range(3):
                    fire(inst, clock, a, d)
                    run(inst, clock, 0.6)
                run(inst, clock, 4.0)
                errs = getattr(inst, "_stage_errors", {})
                if errs:
                    errors.append((world, item_id, dict(errs)))
                    inst.__dict__["_stage_errors"] = {}
            except Exception as exc:          # pragma: no cover - reported
                import traceback
                traceback.print_exc()
                errors.append((world, item_id, repr(exc)))
            reset_players(inst)
    check("all %d event weapons fire in both worlds without an error" % len(usable),
          not errors, errors[:6])


def main() -> int:
    test_statuses()
    test_weapons()
    test_minions()
    test_circus()
    test_every_weapon()
    print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
    for name in FAILED:
        print("  failed: %s" % name)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
