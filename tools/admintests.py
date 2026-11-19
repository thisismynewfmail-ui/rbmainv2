#!/usr/bin/env python3
"""Headless tests for the Admin Tools (app/game/admin_tools.py).

    python3 tools/admintests.py

No server.  The rounds are built in process on a simulated clock, the same
way tools/geartests.py builds them, and the tests check four things:

  * who gets the kit: admin_system's ticket and nobody else's (not another
    admin, not a bot, not a client sending the message anyway), and that
    none of it is an item anybody can buy, own or trade
  * the kit coming out and going away again, as the holder and everyone
    else in the round see it, a world's own kit (an arena round's) included
  * each tool doing what it says: Smite kills through a shield and goes
    through a line; the Horde Horn calls the infected with no cooldown up to
    the safety cap (Last Light) or raises zombies on your side (elsewhere);
    the Titan Tonic's 10,000 health survives a medkit and lasts one life;
    the Blink Wand moves you; Purge clears the infected quietly
  * the server's own rate, whatever a client sends
"""
from __future__ import annotations

import math
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tools"))

import bottests                                    # noqa: E402
import geartests as G                              # noqa: E402

check = G.check


def admin(inst, name="Alice", team="red", items=("use_pistol",), pos=None, tools=True):
    """A player whose ticket did (or didn't) say ``tools``."""
    wire = G.Wire()
    hotbar = [G.hotbar_entry(i, n + 1) for n, i in enumerate(items)]
    while len(hotbar) < 5:
        hotbar.append(None)
    p = inst.add_player(900 + len(inst.players), name, {"hotbar": hotbar}, wire,
                        admin=tools, tools=tools)
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


def kit(inst, p):
    inst.handle(p, {"t": "admin", "op": "kit"})


def use(inst, clock, p, slot, direction, wait=True):
    """Draw tool ``slot`` and fire it once, past its rate."""
    p.slot = slot
    p.stowed = False
    if wait:
        clock.t += 1.0
    inst.handle(p, {"t": "fire", "d": direction})


def chat_lines(wire):
    return [m.get("m", "") for m in wire.of("chat")]


# ================================================================ who
def test_who():
    print("\n== who gets the kit ==")
    from app import config
    from app.game import admin_tools
    from app.models import catalog, market
    ok = admin_tools.allowed_user({"is_admin": 1, "username": "admin_system"})
    check("admin_system's ticket says tools", ok)
    check("...another admin's doesn't",
          not admin_tools.allowed_user({"is_admin": 1, "username": "admin_test"}))
    check("...nor a player who borrowed the name without the admin flag",
          not admin_tools.allowed_user({"is_admin": 0, "username": "admin_system"}))
    check("...nor nobody", not admin_tools.allowed_user(None))
    check("the list is config.ADMIN_TOOLS_USERS (BLOCKHAVEN_ADMIN_TOOLS)",
          "admin_system" in config.ADMIN_TOOLS_USERS)

    ids = sorted(admin_tools.KIT_IDS)
    check("five tools", len(ids) == 5, ids)
    check("none of them is in the catalogue", all(catalog.get(i) is None for i in ids),
          [i for i in ids if catalog.get(i) is not None])
    check("...or anywhere in the item list",
          not [it["id"] for it in catalog.ALL_ITEMS if it["id"] in admin_tools.KIT_IDS])
    refused = []
    for item_id in ids:
        try:
            market.purchase(1, item_id)
        except market.MarketError as exc:
            refused.append(str(exc))
    check("the market won't sell one", len(refused) == len(ids), refused)

    inst, clock = G.make_world()
    p, wire = admin(inst, "Mallory", tools=False)
    welcome = wire.of("welcome")[0]
    check("a normal player's welcome says nothing of it", "tools" not in welcome)
    kit(inst, p)
    check("...and asking for the kit by hand does nothing",
          not p.extra.get("admin_kit") and not wire.of("akit"))
    # even with a kit tool forced onto the hotbar, it does nothing for them
    from app.game.admin_tools import KIT
    bob, wb = admin(inst, "Bob", "blue", tools=False,
                    pos=[p.pos[0], p.pos[1], p.pos[2] + 14])
    p.avatar["hotbar"][0] = dict(KIT[0])
    p.reset_ammo()
    use(inst, clock, p, 0, G.aim_at(p, bob))
    check("...a Smite on a normal player's hotbar kills nobody", bob.alive and bob.health == 100,
          (bob.alive, bob.health))
    G.reset_players(inst)

    a, wa = admin(inst, "Alice")
    check("admin_system's welcome says tools", wa.of("welcome")[0].get("tools") is True)
    a.brain = object()              # a bot can't hold a ticket, but if it could
    kit(inst, a)
    check("a bot never gets the kit", not a.extra.get("admin_kit"))
    a.brain = None
    G.reset_players(inst)


# ================================================================ the kit
def test_kit():
    print("\n== taking it out and putting it away ==")
    from app.game import admin_tools
    inst, clock = G.make_world()
    a, wa, b, wb = G.pair(inst, clock, ["use_pistol"], gap=16)
    # make Alice the admin (G.pair builds two ordinary players)
    a.flags["tools"] = True
    kit(inst, a)
    mine = wa.of("akit")
    check("out: Alice is sent the kit", mine and mine[-1].get("you") and mine[-1]["on"]
          and [t["item_id"] for t in mine[-1]["hotbar"]] == [t["item_id"] for t in admin_tools.KIT],
          mine[-1:] if mine else None)
    check("out: ...and holds it on the server", a.weapon(0)["item_id"] == "admin_smite"
          and a.weapon(4)["item_id"] == "admin_purge")
    seen = [m for m in wb.of("akit") if m["id"] == a.pid]
    check("out: Bob sees it in her hands", seen and seen[-1]["on"] and seen[-1]["hotbar"])
    carl, wc = admin(inst, "Carl", "blue", tools=False)
    late = [m for m in wc.of("akit") if m["id"] == a.pid]
    check("out: someone joining later sees it too", late and late[-1]["on"], late)
    kit(inst, a)
    back = wa.of("akit")[-1]
    check("away: Alice is told, and nothing in the message means her own hotbar",
          back["on"] is False and back.get("hotbar") is None)
    check("away: ...and the server has her pistol back",
          a.weapon(0) and a.weapon(0)["item_id"] == "use_pistol")
    check("away: she's told both ways in chat",
          any("Admin tools out" in line for line in chat_lines(wa))
          and any("put away" in line for line in chat_lines(wa)))
    G.reset_players(inst)

    # an arena world's own kit: handed out while the tools are out, it's what
    # they get back when they put them away -- and no aload swaps the tools
    print("\n== ...in an arena world ==")
    inst, clock = G.make_world("rail_rivals")
    a, wa = admin(inst, "Alice", "red")
    kit(inst, a)
    wa.sent.clear()
    loadout = [inst.item("rr_test", "Test Rail", {"kind": "hitscan", "damage": 10, "rpm": 60,
                                                    "mag": 5, "reserve": 0}, [])]
    inst.set_loadout(a, loadout)
    check("arena: a round's kit doesn't knock the tools out of her hands",
          a.weapon(0)["item_id"] == "admin_smite" and not wa.of("aload"))
    kit(inst, a)
    back = wa.of("akit")[-1]
    check("arena: ...it's what she gets back when she puts them away",
          back["hotbar"] and back["hotbar"][0]["item_id"] == "rr_test"
          and a.weapon(0)["item_id"] == "rr_test", back.get("hotbar"))
    # a world's own rules about when anyone may fire -- this warm-up holds
    # every gun -- don't hold the tools
    kit(inst, a)
    held = not inst.can_fire(a)
    use(inst, clock, a, 2, [0.0, 0.0, 1.0])
    use(inst, clock, a, 1, [0.0, -0.3, 1.0])
    check("arena: the tools work through a warm-up that holds everyone's fire",
          held and a.health == admin_tools.TITAN_HP and inst.gear.minions,
          (held, a.health, len(inst.gear.minions)))
    G.reset_players(inst)


# ================================================================ the tools
def test_smite():
    print("\n== Smite ==")
    inst, clock = G.make_world()
    a, wa, b, wb = G.pair(inst, clock, ["use_pistol"], gap=16)
    a.flags["tools"] = True
    kit(inst, a)
    b.health = 5000
    inst.gear.apply(b, "shield", 10.0, 500, b)
    use(inst, clock, a, 0, G.aim_at(a, b))
    check("one shot kills a 5,000-health target through a shield", not b.alive, b.health)
    kills = [m for m in wb.of("kill") if m.get("vid") == b.pid]
    check("...credited to her, as Smite", kills and kills[-1]["w"] == "Smite"
          and kills[-1]["kid"] == a.pid, kills[-1:])
    check("...and she's told she hit", bool(wa.of("hit")))
    G.reset_players(inst)

    # a line of them
    a, wa, b, wb = G.pair(inst, clock, ["use_pistol"], gap=12)
    a.flags["tools"] = True
    kit(inst, a)
    d = a.extra["fwd"]
    carl, wc = admin(inst, "Carl", "blue", tools=False,
                     pos=[b.pos[0] + d[0] * 6, b.pos[1], b.pos[2] + d[2] * 6])
    use(inst, clock, a, 0, G.aim_at(a, b))
    check("it goes through a line of them", not b.alive and not carl.alive,
          (b.alive, carl.alive))

    # a minion
    from app.game import admin_tools
    inst.gear.raise_at(b, [b.pos[0], b.pos[1], b.pos[2]], admin_tools.ZOMBIE_MINION, 1, "test")
    m = next(iter(inst.gear.minions.values()))
    inst.admin_smite(m, a)
    check("it kills a minion outright", not m.alive or m.pid not in inst.gear.minions)
    G.reset_players(inst)


def test_tonic():
    print("\n== Titan Tonic ==")
    from app.game import admin_tools
    inst, clock = G.make_world()
    a, wa, b, wb = G.pair(inst, clock, ["use_pistol"], gap=16)
    a.flags["tools"] = True
    kit(inst, a)
    use(inst, clock, a, 2, [0.0, 0.0, 1.0])
    heals = wa.of("heal")
    check("10,000 health", a.health == admin_tools.TITAN_HP and heals
          and heals[-1]["hp"] == admin_tools.TITAN_HP, a.health)
    inst.heal(a, 50, a)
    check("...and a medkit doesn't pull it back down to 100", a.health == admin_tools.TITAN_HP,
          a.health)
    inst.apply_damage(a, b, 40, "Test")
    check("it takes a lot more than a few hits", a.alive and a.health == admin_tools.TITAN_HP - 40,
          a.health)
    inst.heal(a, 1000, a)
    check("...and heals back up to 10,000, no further", a.health == admin_tools.TITAN_HP, a.health)
    inst.kill(a, b, "Test")
    inst.spawn_player(a)
    check("it lasts one life", a.health == 100 and "max_hp" not in a.flags, (a.health, a.flags))
    G.reset_players(inst)


def test_blink():
    print("\n== Blink Wand ==")
    inst, clock = G.make_world()
    a, wa, b, wb = G.pair(inst, clock, ["use_pistol"], gap=40)
    a.flags["tools"] = True
    kit(inst, a)
    start = list(a.pos)
    d = a.extra["fwd"]
    wa.sent.clear()
    use(inst, clock, a, 3, d)
    moved = math.dist(start, a.pos)
    check("it moves her where she's looking", moved > 10, moved)
    check("...somewhere she fits", inst.body_fits(a.pos[0], a.pos[1], a.pos[2]))
    check("...and her client is put there", bool(wa.of("correct")))
    check("...and everyone else sees her arrive",
          any(m["id"] == a.pid for m in wb.of("respawned")))
    G.reset_players(inst)


def test_horde_last_light():
    print("\n== Horde Horn and Purge, Last Light ==")
    from app.game import admin_tools
    inst, clock = G.make_world("last_light")
    a, wa = admin(inst, "Alice", "survivors")
    kit(inst, a)
    zs = inst.horde.zombies
    inst.to_lobby(a)            # joining during setup drops you straight in the field
    use(inst, clock, a, 1, [0.0, -0.2, 1.0])
    check("in the lobby the horn says to deploy first", not zs and
          any("deploy first" in line for line in chat_lines(wa)))
    inst.deploy(a)
    a.spawn_protect_until = 0
    d = [math.sin(a.yaw), -0.25, math.cos(a.yaw)]
    for _ in range(12):
        clock.t += 0.13                 # 480 rpm, and not a moment's cooldown more
        a.slot, a.stowed = 1, False
        inst.handle(a, {"t": "fire", "d": d})
    count = len([z for z in zs.values() if z.alive])
    expected = 12 * admin_tools.HORDE_PACK + 12 // admin_tools.SPECIAL_EVERY
    check("twelve blasts in a second and a half: %d infected, no wave needed" % expected,
          count == expected, count)
    specials = [z for z in zs.values() if z.kind in admin_tools.SPECIALS]
    check("...a special every fourth blast", len(specials) == 12 // admin_tools.SPECIAL_EVERY,
          [z.kind for z in specials])

    before = len(zs)
    clock.t += 0.2
    a.slot = 1
    for _ in range(5):              # five in the same instant: one gets through
        inst.handle(a, {"t": "fire", "d": d})
    made = len(zs) - before
    check("the server keeps its own rate, whatever a client sends",
          admin_tools.HORDE_PACK <= made <= admin_tools.HORDE_PACK + 1, made)

    old_cap = admin_tools.HORDE_CAP
    try:
        admin_tools.HORDE_CAP = len(zs) + 3
        use(inst, clock, a, 1, d)
        check("the safety cap stops the horn", len(zs) == admin_tools.HORDE_CAP, len(zs))
        use(inst, clock, a, 1, d)
        check("...and says so", len(zs) == admin_tools.HORDE_CAP and
              any("safety cap" in line for line in chat_lines(wa)))
    finally:
        admin_tools.HORDE_CAP = old_cap

    # a bomber right beside her: purged, it takes nobody with it
    from app.game.worlds.infected import KINDS
    inst.horde.spawn("bomber", [a.pos[0] + 3, a.pos[1], a.pos[2]], KINDS["bomber"]["hp"],
                     KINDS["bomber"]["dmg"], 1)
    near = [z for z in zs.values() if z.alive and math.dist(z.pos, a.pos) <= admin_tools.PURGE_RADIUS]
    hp = a.health
    wa.sent.clear()
    use(inst, clock, a, 4, d)
    left = [z for z in zs.values() if z.alive and math.dist(z.pos, a.pos) <= admin_tools.PURGE_RADIUS]
    check("Purge clears the infected near her", near and not left, (len(near), len(left)))
    check("...quietly: the bomber beside her takes nobody with it", a.health == hp and a.alive,
          (hp, a.health))
    check("...and tells her how many", any(line.startswith("Purged ") for line in chat_lines(wa)))

    # Smite on one of the infected, out in the open
    eye = [a.pos[0], a.pos[1] + 5.05, a.pos[2]]
    _reach, yaw = max((inst.ray_world(eye, [math.sin(y), 0.0, math.cos(y)], 100.0), y)
                      for y in [k * math.pi / 8 for k in range(16)])
    way = [math.sin(yaw), 0.0, math.cos(yaw)]
    z = inst._spawn_common([a.pos[0] + way[0] * 14, a.pos[1], a.pos[2] + way[2] * 14])
    z.health = 99999
    z.state = "walk"
    use(inst, clock, a, 0, G._aim_pos(a, z.centre()))
    check("Smite drops one of the infected however tough", not z.alive, z.health)
    G.reset_players(inst)


def test_horde_elsewhere():
    print("\n== Horde Horn, any other world ==")
    from app.game import admin_tools, gear
    inst, clock = G.make_world()
    a, wa, b, wb = G.pair(inst, clock, ["use_pistol"], gap=24)
    a.flags["tools"] = True
    kit(inst, a)
    d = [a.extra["fwd"][0], -0.3, a.extra["fwd"][2]]
    use(inst, clock, a, 1, d)
    mine = [m for m in inst.gear.minions.values() if m.owner == a.pid]
    check("zombies rise on her side", len(mine) == admin_tools.ZOMBIE_MINION["count"], len(mine))
    for _ in range(10):
        use(inst, clock, a, 1, d, wait=False)
        clock.t += 0.13
    check("endless, but never past the round's limit",
          len(inst.gear.minions) == gear.MAX_MINIONS, len(inst.gear.minions))
    b.health = 1000
    G.run(inst, clock, 6.0)
    check("they go for the enemy", b.health < 1000, b.health)
    use(inst, clock, a, 4, d)
    check("Purge clears them away", not [m for m in inst.gear.minions.values()
                                         if math.dist(m.pos, a.pos) <= admin_tools.PURGE_RADIUS])
    G.reset_players(inst)


def test_off_record():
    print("\n== off the record ==")
    import threading
    from app.game.host import GameHost

    class Host:
        """Just the reporting half of GameHost."""
        world_id = "blackout_relay"

        def __init__(self):
            self.reports, self.badge_tally, self.report_lock = [], {}, threading.Lock()

        def queue_report(self, payload):
            self.reports.append(payload)

    inst, clock = G.make_world()
    a, wa, b, wb = G.pair(inst, clock, ["use_pistol"], gap=16)
    b.flags.pop("off_record", None)
    G.fire(inst, clock, b, G.aim_at(b, a), times=1)        # Bob's ordinary shot
    a.flags["tools"] = True
    kit(inst, a)
    kit(inst, a)                                            # out and straight away again
    use(inst, clock, a, 0, G.aim_at(a, b))                  # pistol, after all that
    a.pk, a.score = 3, 30                                   # whatever the session added up to
    b.pk, b.score = 2, 20
    host = Host()
    GameHost.report_player(host, inst, a, final=True)
    GameHost.report_player(host, inst, b, final=True)
    mine, his = host.reports
    check("a session with the kit in it books no kills or score",
          mine["kills"] == 0 and mine["score"] == 0 and mine["zkills"] == 0, mine)
    check("...but the time spent still counts", "playtime" in mine)
    check("...and everybody else's record is untouched", his["kills"] == 2 and his["score"] == 20, his)
    GameHost.report_badge(host, a, "kills", 5)
    GameHost.report_badge(host, b, "kills", 5)
    check("no badge progress for it either", list(host.badge_tally) == [(b.user_id, "kills", "add")],
          host.badge_tally)
    GameHost.report_round(host, inst, a, True)
    check("...nor a round won", len(host.reports) == 2, host.reports[2:])
    G.reset_players(inst)


def main() -> int:
    bottests.isolate()
    test_who()
    test_kit()
    test_smite()
    test_tonic()
    test_blink()
    test_horde_last_light()
    test_horde_elsewhere()
    test_off_record()
    print("\n%d passed, %d failed" % (len(G.PASSED), len(G.FAILED)))
    for name in G.FAILED:
        print("  failed: %s" % name)
    return 1 if G.FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
