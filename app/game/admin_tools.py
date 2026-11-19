"""Admin Tools: a kit only the admin_system account can pick up in a game.

None of it is an item.  It isn't in the catalogue (app/models/catalog.py), so
it can't turn up in the market, a crate, an inventory, a trade, an outfit, a
bot's hotbar or a world's own kit.  A player gets the kit only when their
signed join ticket says ``tools``.  app/views/worlds_view.py writes that for
the accounts in config.ADMIN_TOOLS_USERS (admin_system, unless
BLOCKHAVEN_ADMIN_TOOLS names others), and the host checks it again on every
use, so a changed client can't reach any of it.

Press ` (the key under Esc) in any world to swap your hotbar for the kit,
and again to put it away:

  1 Smite        kills whatever it hits outright: players, bots, the
                 infected, minions -- through shields, armour and a death
                 refused.  Goes through a line of them.  Hold to keep firing.
  2 Horde Horn   calls the infected where you aim, as fast as you can click
                 or hold: no cooldown and no wave needed (Last Light, up to a
                 safety cap so the server keeps up).  In any other world it
                 raises zombies to fight on your side, the oldest making way.
  3 Titan Tonic  10,000 health, as often as you like (until you next die).
  4 Blink Wand   teleports you to where you're looking.
  5 Purge        clears every infected and minion near you.

A session in which the kit came out is off the record: its play time is
booked, but none of its kills, score, wins or badge progress
(app/game/host.py), so the tools never put anybody on a leaderboard.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Sequence

from .. import config

TITAN_HP = 10000
HORDE_CAP = 300            # infected alive at once, however fast the horn is blown
HORDE_PACK = 6             # infected per blast
SPECIAL_EVERY = 4          # every this many blasts, one special comes too
SPECIALS = ("brute", "spitter", "bomber", "leaper", "screamer", "bloater")
PURGE_RADIUS = 60.0
SMITE_RANGE = 400.0
SMITE_PIERCE = 12          # targets one shot goes through
BLINK_RANGE = 250.0
HORN_RANGE = 160.0
ZOMBIE_MINION = {"name": "Admin's Zombie", "model": "zombie", "count": 4, "hp": 60,
                 "speed": 15, "damage": 12, "reach": 4.5, "rate": 1.0, "secs": 45,
                 "glow": "#6bff9a"}


def _tool(item_id: str, name: str, op: str, stats: Dict[str, Any],
          parts: Sequence[Dict[str, Any]], blurb: str) -> Dict[str, Any]:
    body = {"stats": dict(stats, kind="admin", admin=op, custom=True, reserve=0),
            "parts": [dict(p) for p in parts], "admin": op, "blurb": blurb}
    return {"inv_id": 0, "item_id": item_id, "name": name, "slot": "usable",
            "tier": "normal", "data": body}


R = 1.5708        # a quarter turn: the held models point down the barrel axis
KIT: List[Dict[str, Any]] = [
    _tool("admin_smite", "Smite", "smite",
          {"rpm": 300, "mag": 999, "range": SMITE_RANGE, "auto": True,
           "tracer": "#ffd23f", "sound": "bolt"},
          [{"t": "cyl", "p": [0, 0, -0.25], "s": [0.17, 0.8, 0.17], "c": "#3a2a5e", "r": [R, 0, 0]},
           {"t": "cyl", "p": [0, 0, 0.55], "s": [0.12, 1.0, 0.12], "c": "#ffcf3a", "m": "metal", "r": [R, 0, 0]},
           {"t": "torus", "p": [0, 0, 1.08], "s": [0.46, 0.1, 0.46], "c": "#ffcf3a", "m": "metal", "r": [R, 0, 0]},
           {"t": "sph", "p": [0, 0, 1.12], "s": [0.3, 0.3, 0.3], "c": "#fff3a0", "m": "neon"},
           {"t": "star", "p": [0, 0, 1.12], "s": [0.56, 0.56, 0.08], "c": "#ffe066", "m": "neon"}],
          "Kills whatever it hits, outright."),
    _tool("admin_horn", "Horde Horn", "horde",
          {"rpm": 480, "mag": 999, "range": HORN_RANGE, "auto": True, "sound": "horn"},
          [{"t": "cyl", "p": [0, 0, -0.15], "s": [0.18, 0.7, 0.18], "c": "#5a3a24", "r": [R, 0, 0]},
           {"t": "cone", "p": [0, 0, 0.55], "s": [0.6, 1.0, 0.6], "c": "#6bff9a", "m": "glass", "r": [-R, 0, 0]},
           {"t": "torus", "p": [0, 0, 1.02], "s": [0.6, 0.1, 0.6], "c": "#2f8f46", "r": [R, 0, 0]},
           {"t": "torus", "p": [0, 0, 0.25], "s": [0.28, 0.08, 0.28], "c": "#2f8f46", "r": [R, 0, 0]}],
          "Calls the infected where you aim. No cooldown."),
    _tool("admin_tonic", "Titan Tonic", "tonic",
          {"rpm": 60, "mag": 999, "sound": "heal"},
          [{"t": "sph", "p": [0, 0, 0.25], "s": [0.66, 0.66, 0.66], "c": "#ff3b5c", "m": "glass"},
           {"t": "cyl", "p": [0, 0.4, 0.25], "s": [0.22, 0.3, 0.22], "c": "#ffd6e0", "m": "glass"},
           {"t": "box", "p": [0, 0.6, 0.25], "s": [0.24, 0.14, 0.24], "c": "#8b5a2b"},
           {"t": "star", "p": [0, 0.04, 0.6], "s": [0.3, 0.3, 0.05], "c": "#ffd23f", "m": "neon"}],
          "10,000 health."),
    _tool("admin_blink", "Blink Wand", "blink",
          {"rpm": 150, "mag": 999, "range": BLINK_RANGE, "sound": "whoosh"},
          [{"t": "cyl", "p": [0, 0, 0.3], "s": [0.09, 1.4, 0.09], "c": "#2b1d3d", "r": [R, 0, 0]},
           {"t": "star", "p": [0, 0, 1.06], "s": [0.46, 0.46, 0.08], "c": "#c4a5ff", "m": "neon"},
           {"t": "sph", "p": [0, 0, 1.06], "s": [0.16, 0.16, 0.16], "c": "#ffffff", "m": "neon"}],
          "Teleports you to where you look."),
    _tool("admin_purge", "Purge", "purge",
          {"rpm": 40, "mag": 999, "sound": "explode"},
          [{"t": "box", "p": [0, -0.1, 0.1], "s": [0.52, 0.3, 0.62], "c": "#2b2f3a", "m": "metal"},
           {"t": "cyl", "p": [0, 0.12, 0.1], "s": [0.36, 0.14, 0.36], "c": "#ff3b30", "m": "neon"},
           {"t": "torus", "p": [0, 0.07, 0.1], "s": [0.46, 0.08, 0.46], "c": "#ffd23f", "m": "metal"}],
          "Clears the infected and minions near you."),
]
KIT_IDS = frozenset(tool["item_id"] for tool in KIT)


# ---------------------------------------------------------------- who
def allowed_user(user: Optional[Dict[str, Any]]) -> bool:
    """The web side: does this account get the kit in its join ticket?"""
    if not user or not user.get("is_admin"):
        return False
    return str(user.get("username") or "").lower() in config.ADMIN_TOOLS_USERS


def allowed(player) -> bool:
    """The game side: a person (never a bot) whose signed ticket said so."""
    return bool(getattr(player, "flags", {}).get("tools")) and player.brain is None


def tell(player, text: str) -> None:
    player.send({"t": "chat", "kind": "system", "from": "", "id": 0, "m": text,
                 "at": time.time()})


# ------------------------------------------------------------ messages
def handle(world, player, message: Dict[str, Any]) -> None:
    """{"t": "admin", "op": "kit"} -- take the kit out, or put it away."""
    if not allowed(player):
        return
    if message.get("op") == "kit":
        with world.lock:
            toggle(world, player, not player.extra.get("admin_kit"))


def toggle(world, player, on: bool) -> None:
    if on:
        player.extra["admin_kit"] = [dict(tool) for tool in KIT]
        # a session with the kit in it is off the record: play time counts,
        # but no kills, score, wins or badge progress (app/game/host.py), so
        # a Smite spree never tops a leaderboard
        player.flags["off_record"] = True
    else:
        player.extra.pop("admin_kit", None)
    first = next((i for i in range(len(KIT)) if player.weapon(i)), 0)
    player.slot = first
    player.stowed = player.weapon(first) is None
    player.reset_ammo()
    player.reload_until = 0.0
    player.next_fire = 0.0
    kit = player.extra.get("admin_kit")
    # put away: back to whatever the world has handed them (a round's kit),
    # or, with nothing in the message, their own hotbar
    world_kit = player.extra.get("loadout")
    player.send({"t": "akit", "id": player.pid, "you": 1, "on": bool(on),
                 "hotbar": kit if on else world_kit, "slot": player.slot})
    shown = kit if on else player.extra.get("public_loadout", world_kit)
    world.broadcast({"t": "akit", "id": player.pid, "on": bool(on), "hotbar": shown},
                    exclude=player.pid)
    world.broadcast({"t": "slot", "id": player.pid, "i": -1 if player.stowed else player.slot},
                    exclude=player.pid)
    tell(player, "Admin tools out: Smite, Horde Horn, Titan Tonic, Blink Wand, Purge. "
                 "Press ` to put them away." if on else "Admin tools put away.")


# --------------------------------------------------------------- using
def fire(world, player, stats: Dict[str, Any], direction: List[float],
         origin: List[float]) -> None:
    if not allowed(player):
        return
    op = stats.get("admin")
    if op == "smite":
        smite(world, player, origin, direction)
    elif op == "horde":
        horde(world, player, origin, direction)
    elif op == "tonic":
        tonic(world, player)
    elif op == "blink":
        blink(world, player, origin, direction)
    elif op == "purge":
        purge(world, player)
    # a bottomless magazine
    slot = player.slot
    player.ammo[slot] = int(stats.get("mag", 999) or 999)


def smite(world, player, origin, direction) -> int:
    wall = world.ray_world(origin, direction, SMITE_RANGE)
    start, gone, killed = list(origin), 0.0, 0
    for _ in range(SMITE_PIERCE):
        victim, distance, headshot = world.nearest_player_hit(player, start, direction,
                                                              wall - gone)
        if victim is None:
            break
        world.admin_smite(victim, player, headshot)
        killed += 1
        step = distance + 1.6
        gone += step
        start = [start[0] + direction[0] * step, start[1] + direction[1] * step,
                 start[2] + direction[2] * step]
    world.broadcast({"t": "fx", "k": "shot", "id": player.pid, "o": origin, "d": direction,
                     "w": "admin_smite", "c": "#ffd23f"}, exclude=player.pid)
    if killed:
        player.send({"t": "hit", "n": killed})
    return killed


def aim_point(world, origin, direction, reach: float) -> List[float]:
    dist = world.ray_world(origin, direction, reach)
    d = max(3.0, dist - 2.0)
    return [origin[0] + direction[0] * d, origin[1] + direction[1] * d,
            origin[2] + direction[2] * d]


def ground_below(world, point) -> List[float]:
    drop = world.ray_world(point, [0.0, -1.0, 0.0], 400.0)
    if drop >= 400.0:
        return list(point)
    return [point[0], point[1] - drop + 0.05, point[2]]


def horde(world, player, origin, direction):
    point = ground_below(world, aim_point(world, origin, direction, HORN_RANGE))
    result = world.admin_horde(player, point)
    if isinstance(result, str):
        # say why, but not ten times a second while the trigger is held
        moment = time.monotonic()
        said_at, said = player.extra.get("horn_said", (0.0, ""))
        if result != said or moment - said_at > 3.0:
            player.extra["horn_said"] = (moment, result)
            tell(player, result)
    return result


def tonic(world, player) -> None:
    before = int(player.health)
    player.flags["max_hp"] = TITAN_HP
    player.health = TITAN_HP
    player.send({"t": "heal", "hp": TITAN_HP, "amt": max(0, TITAN_HP - before),
                 "by": "Titan Tonic"})


def blink(world, player, origin, direction) -> bool:
    from .instance import now
    dist = world.ray_world(origin, direction, BLINK_RANGE)
    for back in (1.5, 3.0, 5.0, 8.0, 12.0):
        d = max(0.0, dist - back)
        spot = [origin[0] + direction[0] * d, origin[1] + direction[1] * d - 2.0,
                origin[2] + direction[2] * d]
        feet = ground_below(world, spot)
        if world.body_fits(feet[0], feet[1], feet[2]):
            player.pos = feet
            player.vel = [0.0, 0.0, 0.0]
            player.last_ground_pos = list(feet)
            player.airborne_since = 0.0
            player.last_pos_time = now()
            # the old position is still in flight from the client
            player.extra["tp_grace"] = now() + 0.8
            world.correct(player)
            world.broadcast({"t": "respawned", "id": player.pid, "p": player.pos,
                             "hp": int(player.health)}, exclude=player.pid)
            return True
    tell(player, "Nowhere to land there.")
    return False


def purge(world, player) -> int:
    count = world.admin_purge(player, PURGE_RADIUS)
    tell(player, ("Purged %d." % count) if count else
         "Nothing to purge within %d studs." % int(PURGE_RADIUS))
    return count


def distance(a, b) -> float:
    return math.dist(a, b)
