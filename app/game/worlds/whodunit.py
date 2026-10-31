"""Whodunit: a murder mystery (app/models/event_worlds/whodunit.py).

Everyone arrives as a guest, and at the start of each round the roles are
dealt in secret: one **murderer** (two in a big party) with a knife, one
**detective** (or two) with a revolver, and everybody else **innocent**.
Nobody is told who anybody else is.

**The murderer** wins by leaving nobody else standing.  The knife is kept
out of sight until it is drawn -- a guest holding a knife is a murderer --
and kills with one stab, or thrown (R) from a distance on a cooldown.

**The detective** wins (with every innocent) by shooting the murderer.  The
revolver kills with one shot and takes a while to reload; shoot an innocent
and the detective is disgraced on the spot -- out, the revolver on the floor
for any innocent brave enough to pick it up and finish the job as the
**hero**.

**The innocents** win by surviving the clock (or seeing the murderer shot).
Clues turn up round the place, and every one an innocent or the detective
picks up goes in the shared case file; enough clues and the file gives up a
hint, four in all, each sharper than the last:

1. *seen* -- where the murderer was a moment ago;
2. *trail* -- the murderer's footprints glow for a while;
3. *suspects* -- three names, one of them the murderer's;
4. *glimpse* -- the murderer stands out for a few seconds.

A murderer who picks a clue up burns it.

**The dead** are out until the next round, and talk only to each other.
The kill feed names the detective's shots but never the murderer's.

**Each place has a twist** (``extra["twist"]``): the manor's thunderstorm
puts the lights out, the express goes through tunnels (dark, and anybody
on the roof is swept off), the hotel holds a masquerade (every guest in the
same mask, no names), and the liner sails into fog banks.
"""
from __future__ import annotations

import math
import re
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import instance as engine
from ...models import catalog
from ..instance import EYE_HEIGHT, JUMP_SPEED, MAX_HEALTH, STOW_SLOT, Player, normalise, ray_aabb
from ..maps.events import whodunit as wd_map
from .arena import NEVER, ArenaWorld

KNIFE_REACH = 6.5
KNIFE_ARC = 0.42
KNIFE_COOL = 0.9
THROW_SPEED = 78.0
THROW_GRAVITY = 14.0
THROW_COOL = 7.0
THROW_LIFE = 1.4
REVOLVER_RANGE = 170.0
REVOLVER_RELOAD = 2.6
CLUE_REACH = 3.2
GUN_REACH = 3.6
CLUE_EVERY = (3.5, 6.5)
CLUE_POINTS = 3
SURVIVE_POINTS = 15
MURDER_POINTS = 12
CATCH_POINTS = 40
TRAIL_SECONDS = 14.0
GLIMPSE_SECONDS = 6.0
SIGHT = 70.0
SIGHT_DIM = 24.0
HINTS = ("seen", "trail", "suspects", "glimpse")
DEFAULTS: Dict[str, Any] = {}
# what a witness says, and what a bot that has worked it out says
SEEN_LINES = ["its {name}!", "{name} has a knife", "{name} is the murderer", "RUN its {name}",
              "{name} did it"]
MURDER_WORDS = ("murder", "killer", "knife", "its ", "it's", "did it", "sus", "stabbed")


def _defaults() -> Dict[str, Any]:
    if not DEFAULTS:
        from ...models.event_worlds import whodunit as meta
        for spec in meta.BOT_FIELDS:
            DEFAULTS[spec[0]] = spec[3]
    return DEFAULTS


def _item(item_id: str, name: str, kind: str, parts: List[Dict[str, Any]],
          **stats: Any) -> Dict[str, Any]:
    body = {"kind": kind, "rpm": stats.pop("rpm", 120), "mag": stats.pop("mag", 99),
            "reserve": 0, "range": stats.pop("range", 60), "custom": True}
    body.update(stats)
    return ArenaWorld.item(item_id, name, body, parts)


KNIFE = _item("wd_knife", "Knife", "wd_knife", [
    {"t": "box", "p": [0, 0, -0.1], "s": [0.22, 0.34, 0.9], "c": "#3a2418"},
    {"t": "box", "p": [0, 0.02, 0.4], "s": [0.5, 0.14, 0.14], "c": "#a8a8a8", "m": "metal"},
    {"t": "box", "p": [0, 0.04, 1.1], "s": [0.08, 0.32, 1.3], "c": "#d8dce4", "m": "metal"},
    {"t": "wedge", "p": [0, 0.04, 1.9], "s": [0.08, 0.32, 0.4], "c": "#d8dce4", "m": "metal"}],
    rpm=70, range=KNIFE_REACH, melee=True, sound="wd_stab")
REVOLVER = _item("wd_revolver", "Revolver", "wd_revolver", [
    {"t": "box", "p": [0, -0.35, -0.2], "s": [0.3, 0.8, 0.45], "c": "#5a3a24"},
    {"t": "cyl", "p": [0, 0.08, 0.15], "s": [0.5, 0.42, 0.5], "c": "#6a6e76", "m": "metal",
     "r": [1.5708, 0, 0]},
    {"t": "cyl", "p": [0, 0.12, 0.85], "s": [0.18, 1.2, 0.18], "c": "#4a4e56", "m": "metal",
     "r": [1.5708, 0, 0]},
    {"t": "box", "p": [0, 0.3, 1.38], "s": [0.06, 0.12, 0.06], "c": "#c8a040"}],
    rpm=40, range=REVOLVER_RANGE, mag=1, sound="wd_bang", tracer="#ffe2a0")


class WhodunitWorld(ArenaWorld):
    MAP = wd_map
    FFA = True
    ROUNDS_PER_AREA = 2
    SETUP_SECONDS = 12.0
    ROUND_SECONDS = 180.0
    RESULTS_SECONDS = 16.0
    ELIMINATION = True
    LOGO = "Whodunit"
    FREEZE_COUNTDOWN = True
    CUSTOM_KINDS = ("wd_knife", "wd_revolver")
    respawn_seconds = 6.0
    BOT_CHATTER = ["who is it", "sus", "stick together", "where is everyone", "gg", "not me",
                   "i saw nothing", "trust no one", "where's the detective", "lol"]

    # ------------------------------------------------------------ settings
    def setting(self, key: str) -> Any:
        cfg = getattr(self.bots, "cfg", None) if self.bots is not None else None
        value = (cfg or {}).get("whodunit_" + key)
        return _defaults().get(key) if value is None else value

    def pct(self, key: str) -> float:
        try:
            return max(0.0, min(1.0, float(self.setting(key)) / 100.0))
        except (TypeError, ValueError):
            return 0.5

    # ================================================================ setup
    def world_setup(self) -> None:
        self.roles: Dict[int, str] = {}
        self.clues: Dict[int, Dict[str, Any]] = {}
        self.bodies: List[Dict[str, Any]] = []
        self.knives: Dict[int, Dict[str, Any]] = {}
        self.gun: Optional[Dict[str, Any]] = None
        self.case = 0
        self.hints: List[str] = []
        self.hint_at: List[int] = []
        self.trail_until = 0.0
        self.glimpse_until = 0.0
        self.suspects: List[str] = []
        self.twist: Dict[str, Any] = {"kind": "", "on": False, "until": 0.0, "next": NEVER,
                                      "warn": 0.0}
        self.next_clue = NEVER
        self.live_at = NEVER
        self.next_id = 1
        self.round_stats: Dict[int, Dict[str, float]] = {}
        self.counts: Dict[str, int] = {"murders": 0, "caught": 0, "misfires": 0, "clues": 0,
                                       "burned": 0, "hints": 0, "throws": 0, "rounds": 0,
                                       "gun_drops": 0, "heroes": 0, "twists": 0, "falls": 0}
        self.events_said: Dict[str, float] = {}
        self.landmarks: List[Tuple[List[float], str]] = []
        self.marks: Dict[str, List[Dict[str, Any]]] = {}
        self.caught_by = ""
        self.step_at: Dict[int, float] = {}

    def round_setup(self) -> None:
        area = self.area
        extra = area.get("extra") or {}
        self.marks = {k: list(v) for k, v in (area.get("points") or {}).items()}
        self.landmarks = [(list(m["p"]), m["name"]) for m in area.get("landmarks") or []]
        self.ROUND_SECONDS = float(extra.get("round_seconds") or WhodunitWorld.ROUND_SECONDS)
        self.roles = {}
        self.clues = {}
        self.bodies = []
        self.knives = {}
        self.gun = None
        self.case = 0
        self.hints = []
        self.trail_until = 0.0
        self.glimpse_until = 0.0
        self.suspects = []
        self.round_stats = {}
        self.events_said = {}
        self.caught_by = ""
        self.step_at = {}
        kind = str(extra.get("twist") or "")
        self.twist = {"kind": kind, "on": False, "until": 0.0, "next": NEVER, "warn": 0.0}
        self.next_clue = NEVER
        for player in self.players.values():
            self.reset_player(player)
        self._deal()

    def reset_player(self, player: Player) -> None:
        for key in ("wd_mind", "wd_stab_at", "wd_throw_at", "wd_clues", "wd_knife_out"):
            player.extra.pop(key, None)

    # ============================================================== roles
    def role(self, player: Player) -> str:
        return self.roles.get(player.pid, "innocent")

    def is_murderer(self, player: Player) -> bool:
        return self.roles.get(player.pid) == "murderer"

    def armed(self, player: Player) -> bool:
        return self.roles.get(player.pid) in ("detective", "hero")

    def _deal(self) -> None:
        """Deal the roles in secret, and hand everybody their kit."""
        guests = [p for p in self.players.values() if p.team in self.team_names() or p.team == "ffa"]
        guests = [p for p in guests if not p.extra.get("spectator")]
        self.rng.shuffle(guests)
        n = len(guests)
        killers = 0 if n < 2 else (2 if n >= 10 else 1)
        sleuths = 0 if n < 2 else (2 if n >= 10 else 1)
        for i, player in enumerate(guests):
            if i < killers:
                self.roles[player.pid] = "murderer"
            elif i < killers + sleuths:
                self.roles[player.pid] = "detective"
            else:
                self.roles[player.pid] = "innocent"
        for player in guests:
            self._kit(player)
            self._tell_role(player)

    def _kit(self, player: Player) -> None:
        role = self.role(player)
        if role == "murderer":
            # the knife is a secret until it is drawn: everybody else is
            # told the murderer's hands are empty
            self.set_loadout(player, [KNIFE], public=[], quiet=True)
            self.handle_slot(player, {"i": STOW_SLOT})
        elif role in ("detective", "hero"):
            # the revolver is on show to the guests -- but not to a murderer,
            # who has to work out who carries it (from a shot, say)
            self.set_loadout(player, [REVOLVER], public=[], quiet=True)
            for other in self.players.values():
                if other is not player and not self.is_murderer(other):
                    self._show_revolver(player, other)
        else:
            self.set_loadout(player, [], public=[], quiet=True)

    def _show_revolver(self, armed: Player, viewer: Player) -> None:
        """Tell ``viewer`` (anybody but a murderer) what ``armed`` really
        carries, and which slot is in their hand."""
        viewer.send({"t": "aload", "id": armed.pid, "hotbar": armed.extra.get("loadout")})
        viewer.send({"t": "slot", "id": armed.pid,
                     "i": STOW_SLOT if armed.stowed else armed.slot})

    def _tell_role(self, player: Player) -> None:
        role = self.role(player)
        partners = [p.username for p in self.players.values()
                    if p is not player and self.role(p) == role and role == "murderer"]
        player.send({"t": "wdx", "k": "role", "role": role, "partners": partners})
        self._send_me(player, force=True)

    def handle_slot(self, player: Player, message: Dict[str, Any]) -> None:
        super().handle_slot(player, message)
        if not self.is_murderer(player):
            return
        out = not player.stowed and player.weapon(player.slot) is not None
        if out == bool(player.extra.get("wd_knife_out")):
            return
        player.extra["wd_knife_out"] = out
        # what everybody else sees in the murderer's hand
        shown: List[Any] = [KNIFE] if out else []
        player.extra["public_loadout"] = shown + [None] * (catalog.HOTBAR_SIZE - len(shown))
        self.broadcast({"t": "aload", "id": player.pid, "hotbar": player.extra["public_loadout"]},
                       exclude=player.pid)
        self.broadcast({"t": "slot", "id": player.pid,
                        "i": STOW_SLOT if player.stowed else player.slot}, exclude=player.pid)

    def knife_out(self, player: Player) -> bool:
        return bool(player.extra.get("wd_knife_out")) and self.is_murderer(player)

    # ============================================================ spawning
    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        spawns = self.area.get("spawns") or {}
        return list(spawns.get("start") or spawns.get(team) or []) or super().spawn_points(team)

    def on_spawned(self, player: Player) -> None:
        if self.phase in ("setup", "active") and player.pid in self.roles:
            self._kit(player)

    def on_player_join(self, player: Player) -> None:
        super().on_player_join(player)
        if self.phase == "setup" and player.pid not in self.roles:
            # in before the lights go down: a guest like everybody else
            self.roles[player.pid] = "innocent"
            self._kit(player)
            self._tell_role(player)
        elif player.pid not in self.roles:
            # watching until the next case: empty-handed, not in their own
            # kit (nobody here carries anything the case did not hand out)
            self.set_loadout(player, [], public=[], quiet=True)

    def on_player_ready(self, player: Player) -> None:
        super().on_player_ready(player)
        if self.is_murderer(player):
            return
        for other in self.players.values():
            if other is not player and self.armed(other) and other.extra.get("loadout"):
                self._show_revolver(other, player)
        if self.gun is not None:
            player.send({"t": "wdx", "k": "gun", "p": self.gun["p"], "late": 1})

    def welcome_lines(self, player: Player) -> List[str]:
        lines = super().welcome_lines(player)
        lines.append("Somebody here is a murderer. Your role is dealt in secret each round.")
        lines.append("Innocents: pick up clues for the case file and stay alive. Detective: "
                     "shoot the murderer -- and only the murderer.")
        return lines

    def can_fire(self, player: Player) -> bool:
        return self.phase == "active" and self.in_play(player)

    def can_hurt(self, attacker: Player, victim: Player) -> bool:
        return attacker is not victim

    # ============================================================ weapons
    def custom_fire(self, player: Player, stats: Dict[str, Any], direction: List[float],
                    origin: List[float]) -> None:
        kind = stats.get("kind")
        if kind == "wd_knife" and self.is_murderer(player):
            self.stab(player, direction)
        elif kind == "wd_revolver" and self.armed(player):
            self.shoot(player, direction, origin)

    def world_action(self, player: Player, kind: str, message: Dict[str, Any]) -> None:
        if kind == "throw":
            direction = message.get("d")
            if isinstance(direction, list) and len(direction) == 3:
                try:
                    self.throw(player, normalise([float(v) for v in direction]))
                except (TypeError, ValueError):
                    return

    def stab(self, player: Player, direction: Sequence[float]) -> bool:
        moment = engine.now()
        if not self.knife_out(player) or moment < player.extra.get("wd_stab_at", 0.0):
            return False
        player.extra["wd_stab_at"] = moment + KNIFE_COOL
        origin = [player.pos[0], player.pos[1] + 3.4, player.pos[2]]
        best, best_d = None, KNIFE_REACH
        for other in self.playing():
            if other is player or self.is_murderer(other):
                continue
            target = [other.pos[0], other.pos[1] + 2.6, other.pos[2]]
            delta = [target[i] - origin[i] for i in range(3)]
            d = math.sqrt(sum(v * v for v in delta))
            if d > best_d or d < 1e-6:
                continue
            unit = [v / d for v in delta]
            if sum(unit[i] * direction[i] for i in range(3)) < 1.0 - KNIFE_ARC:
                continue
            if not self.line_of_sight(origin, target):
                continue
            best, best_d = other, d
        self.broadcast({"t": "wdx", "k": "swing", "id": player.pid}, exclude=player.pid)
        if best is None:
            return False
        self._murder(player, best, "Knife")
        return True

    def throw(self, player: Player, direction: Sequence[float]) -> bool:
        moment = engine.now()
        if not self.knife_out(player) or not self.in_play(player) or self.phase != "active":
            return False
        if moment < player.extra.get("wd_throw_at", 0.0):
            return False
        player.extra["wd_throw_at"] = moment + THROW_COOL
        kid = self.next_id
        self.next_id += 1
        origin = [player.pos[0] + direction[0] * 1.2, player.pos[1] + EYE_HEIGHT - 0.4,
                  player.pos[2] + direction[2] * 1.2]
        self.knives[kid] = {"id": kid, "p": origin, "v": [d * THROW_SPEED for d in direction],
                            "by": player.pid, "until": moment + THROW_LIFE}
        self.counts["throws"] += 1
        self.broadcast({"t": "wdx", "k": "throw", "id": kid, "p": [round(v, 2) for v in origin],
                        "v": [round(d * THROW_SPEED, 2) for d in direction], "by": player.pid})
        player.send({"t": "wdx", "k": "cool", "throw": THROW_COOL})
        return True

    def _step_knives(self, dt: float, moment: float) -> None:
        for kid, knife in list(self.knives.items()):
            thrower = self.players.get(knife["by"])
            p, v = knife["p"], knife["v"]
            v[1] -= THROW_GRAVITY * dt
            step = [v[i] * dt for i in range(3)]
            length = math.sqrt(sum(s * s for s in step)) or 1e-6
            unit = [s / length for s in step]
            wall = self.ray_world(p, unit, length)
            hit, hit_t = None, min(wall, length)
            for other in self.playing():
                if thrower is not None and (other is thrower or self.is_murderer(other)):
                    continue
                lo, hi = other.hitbox()
                t = ray_aabb(p, unit, lo, hi)
                if t is not None and 0.0 <= t <= hit_t:
                    hit, hit_t = other, t
            end = [p[i] + unit[i] * hit_t for i in range(3)]
            if hit is not None:
                self.knives.pop(kid)
                self.broadcast({"t": "wdx", "k": "stick", "id": kid, "p": [round(c, 2) for c in end],
                                "hit": hit.pid})
                if thrower is not None and self.in_play(thrower):
                    self._stat(thrower, "throw_kills")
                    self.badge(thrower, "wd_throws")
                    self._murder(thrower, hit, "Thrown Knife")
                continue
            if wall < length or moment >= knife["until"]:
                self.knives.pop(kid)
                self.broadcast({"t": "wdx", "k": "stick", "id": kid, "p": [round(c, 2) for c in end]})
                continue
            knife["p"] = end

    def shoot(self, player: Player, direction: Sequence[float], origin: Sequence[float]) -> bool:
        moment = engine.now()
        if moment < player.reload_until or not self.in_play(player):
            return False
        player.reload_until = moment + REVOLVER_RELOAD
        wall = self.ray_world(origin, direction, REVOLVER_RANGE)
        best, best_t = None, wall
        for other in self.playing():
            if other is player:
                continue
            lo, hi = other.hitbox()
            t = ray_aabb(origin, direction, lo, hi)
            if t is not None and 0.0 <= t < best_t:
                best, best_t = other, t
        end = [origin[i] + direction[i] * best_t for i in range(3)]
        self.broadcast({"t": "wdx", "k": "shot", "id": player.pid,
                        "a": [round(v, 2) for v in origin], "b": [round(v, 2) for v in end]})
        player.send({"t": "wdx", "k": "cool", "reload": REVOLVER_RELOAD})
        self._bot_saw_shot(player, origin, end)
        if best is None:
            return False
        if self.is_murderer(best):
            self._caught(player, best)
        else:
            self._misfire(player, best)
        return True

    # ============================================================== deaths
    def _murder(self, murderer: Player, victim: Player, weapon: str) -> None:
        moment = engine.now()
        witnesses = self._witnesses(murderer, victim)
        self.apply_damage(victim, None, MAX_HEALTH * 3, weapon)
        if victim.alive:
            return
        self.counts["murders"] += 1
        # the murderer's kills and points are booked at the end of the round:
        # a score that jumped would give them away
        self._stat(murderer, "kills")
        self.badge(murderer, "wd_kills")
        if self.twist["on"]:
            self.badge(murderer, "wd_shadow")
        self._bot_witness(murderer, victim, witnesses, moment)
        self._event("wd_body", None, "", victim=victim.username, where=self._place(victim.pos))

    def _witnesses(self, murderer: Player, victim: Player) -> List[Player]:
        """Who saw it: anybody close enough with a clear view of the
        murderer -- not in the dark, the fog or behind a mask."""
        out = []
        sight = self.sight()
        eye_m = [murderer.pos[0], murderer.pos[1] + 4.0, murderer.pos[2]]
        for other in self.playing():
            if other is murderer or other is victim or self.is_murderer(other):
                continue
            if math.dist(other.pos, murderer.pos) > sight:
                continue
            if self.line_of_sight([other.pos[0], other.pos[1] + EYE_HEIGHT, other.pos[2]], eye_m):
                out.append(other)
        return out

    def _caught(self, shooter: Player, murderer: Player) -> None:
        self.caught_by = shooter.username
        self.apply_damage(murderer, shooter, MAX_HEALTH * 3, "Revolver")
        if murderer.alive:
            return
        self.counts["caught"] += 1
        shooter.score += CATCH_POINTS
        self._stat(shooter, "caught")
        self.badge(shooter, "wd_solved")
        if self.role(shooter) == "hero":
            self.counts["heroes"] += 1
            self.badge(shooter, "wd_hero")
        if self.round_ends and self.round_ends - engine.now() < 10.0:
            self.badge(shooter, "wd_close")
        self.broadcast({"t": "wdx", "k": "caught", "by": shooter.username, "who": murderer.username,
                        "hero": self.role(shooter) == "hero"})
        self._event("wd_caught", shooter, "", who=murderer.username)
        for brain_player in self.players.values():
            mind = brain_player.extra.get("wd_mind")
            if mind is not None:
                mind.get("sus", {}).pop(murderer.pid, None)

    def _misfire(self, shooter: Player, victim: Player) -> None:
        """The detective shot an innocent: the innocent dies, and so does the
        detective's career -- and the revolver goes on the floor."""
        self.apply_damage(victim, shooter, MAX_HEALTH * 3, "Revolver")
        self.counts["misfires"] += 1
        self._stat(shooter, "misfires")
        self.badge(shooter, "wd_wrong_man")
        shooter.send({"t": "wdx", "k": "misfire", "who": victim.username})
        self.broadcast({"t": "wdx", "k": "disgraced", "who": shooter.username,
                        "victim": victim.username}, exclude=shooter.pid)
        self._event("wd_misfire", shooter, "", victim=victim.username)
        self.apply_damage(shooter, None, MAX_HEALTH * 3, "Disgrace")

    def kill(self, victim, killer, weapon_name: str, headshot: bool = False) -> None:
        if not isinstance(victim, Player) or not victim.alive:
            return
        pos = list(victim.pos)
        super().kill(victim, killer, weapon_name, headshot)
        if victim.alive:
            return
        if self.phase in ("active", "setup"):
            bid = self.next_id
            self.next_id += 1
            body = {"id": bid, "p": [round(pos[0], 2), round(pos[1], 2), round(pos[2], 2)],
                    "yaw": round(victim.yaw, 2), "name": victim.username, "at": engine.now()}
            self.bodies.append(body)
            self.broadcast({"t": "wdx", "k": "body", "id": bid, "p": body["p"], "yaw": body["yaw"],
                            "name": victim.username, "pid": victim.pid,
                            "w": weapon_name if weapon_name not in ("Knife", "Thrown Knife") else "knife"})
        # the detective's revolver goes on the floor where they fell
        if self.armed(victim) and self.phase == "active":
            self.gun = {"p": self._ground([pos[0], pos[1] + 1.0, pos[2]]), "at": engine.now()}
            self.counts["gun_drops"] += 1
            # where it lies is for the guests' eyes: a murderer hears it
            # clatter down, and no more
            for other in self.players.values():
                other.send({"t": "wdx", "k": "gun"} if self.is_murderer(other) else
                           {"t": "wdx", "k": "gun", "p": self.gun["p"]})
            self._event("wd_gun", None, "", where=self._place(pos), dropped=True)
        self._check_end()

    def after_kill(self, killer: Optional[Player], victim: Player, weapon: str) -> None:
        if victim.brain is not None:
            victim.brain.target = None

    def _ground(self, pos: Sequence[float]) -> List[float]:
        top = [pos[0], pos[1] + 2.0, pos[2]]
        d = self.ray_world(top, [0.0, -1.0, 0.0], 60.0)
        return [round(pos[0], 2), round(top[1] - d, 2), round(pos[2], 2)]

    # ======================================================== the round
    def on_live(self) -> None:
        moment = engine.now()
        self.live_at = moment
        self.next_clue = moment + 2.0
        for _ in range(min(3, len(self.marks.get("clue", [])))):
            self._spawn_clue()
        kind = self.twist["kind"]
        if kind:
            lo, hi = (self.area.get("extra") or {}).get("twist_every") or [35.0, 50.0]
            self.twist["next"] = moment + self.rng.uniform(lo, hi) * 0.7
        self.counts["rounds"] += 1
        self._broadcast_state()

    def round_tick(self, dt: float, moment: float) -> None:
        if self.phase != "active":
            return
        playing = self.playing()
        self._step_knives(dt, moment)
        self._pickups(playing, moment)
        self._twist_tick(playing, moment)
        if moment >= self.next_clue:
            self.next_clue = moment + self.rng.uniform(*CLUE_EVERY) * (1.3 if len(playing) < 5 else 1.0)
            self._spawn_clue()
        fall = (self.area.get("extra") or {}).get("fall_y")
        if fall is not None:
            for player in playing:
                if player.pos[1] < float(fall):
                    self.counts["falls"] += 1
                    self.apply_damage(player, None, MAX_HEALTH * 3,
                                      str((self.area.get("extra") or {}).get("fall_what") or "a fall"))
        if moment < self.trail_until:
            for m in [p for p in playing if self.is_murderer(p)]:
                if moment - self.step_at.get(m.pid, 0.0) > 0.55 and \
                        math.hypot(m.vel[0], m.vel[2]) > 2.0:
                    self.step_at[m.pid] = moment
                    step = {"t": "wdx", "k": "step", "p": [round(m.pos[0], 2), round(m.pos[1], 2),
                                                           round(m.pos[2], 2)],
                            "yaw": round(m.yaw, 2)}
                    for other in self.players.values():
                        if not self.is_murderer(other):
                            other.send(step)
        self._check_end()

    def _check_end(self) -> None:
        if self.phase != "active":
            return
        alive = self.playing()
        killers = [p for p in alive if self.is_murderer(p)]
        others = [p for p in alive if not self.is_murderer(p)]
        had_killer = any(r == "murderer" for r in self.roles.values())
        if had_killer and not killers:
            self.finish_round("innocents", "caught")
        elif had_killer and not others:
            self.finish_round("murderer", "everyone")

    def finish_round(self, winner: str, reason: str = "", headline: str = "",
                     winner_name: str = "") -> None:
        if self.phase != "active":
            return
        for player in self.players.values():
            murders = int(self.round_stats.get(player.pid, {}).get("kills", 0))
            if murders and self.is_murderer(player):
                player.kills += murders
                player.score += murders * MURDER_POINTS
        super().finish_round(winner, reason, headline, winner_name)

    def time_up(self) -> None:
        for player in self.playing():
            if not self.is_murderer(player):
                player.score += SURVIVE_POINTS
                self._stat(player, "survived")
                self.badge(player, "wd_survived")
        self.finish_round("innocents", "time")

    def leader(self) -> str:
        return ""

    def player_won(self, player: Player, winner: str) -> bool:
        if player.pid not in self.roles:
            return False
        if winner == "murderer":
            return self.is_murderer(player)
        if winner == "innocents":
            return not self.is_murderer(player)
        return False

    def headline(self, winner: str, reason: str) -> str:
        killers = [p.username for p in self.players.values() if self.is_murderer(p)]
        who = " and ".join(killers) or "the murderer"
        if winner == "murderer":
            return "%s got away with it" % who
        if reason == "caught":
            return "%s caught %s" % (self.caught_by or "the detective", who)
        return "the guests survived the night -- it was %s" % who

    def on_round_over(self, winner: str, reason: str, winners: List[Player]) -> None:
        for player in winners:
            self.badge(player, "wd_wins")
            self.badge(player, "wd_area_" + self.area_id, 1, "max")
        if winner == "murderer":
            for player in winners:
                if self.round_stats.get(player.pid, {}).get("kills", 0) >= 4:
                    self.badge(player, "wd_spotless")
        self.broadcast({"t": "wdx", "k": "reveal",
                        "roles": {str(pid): role for pid, role in self.roles.items()}})
        if winner == "murderer":
            self._event("wd_escape", None, "", who=" and ".join(
                p.username for p in self.players.values() if self.is_murderer(p)))

    def result_columns(self) -> List[List[str]]:
        return [["role", "Role"], ["score", "Points"], ["clues", "Clues"], ["kills", "Kills"]]

    def results_rows(self) -> List[Dict[str, Any]]:
        names = {"murderer": "Murderer", "detective": "Detective", "hero": "Hero",
                 "innocent": "Innocent"}
        rows = []
        for p in self.players.values():
            if p.pid not in self.roles:
                continue
            stats = self.round_stats.get(p.pid, {})
            rows.append({"id": p.pid, "name": p.username, "team": "ffa", "score": p.score,
                         "role": names.get(self.role(p), "Guest"),
                         "clues": int(stats.get("clues", 0)),
                         "kills": int(stats.get("kills", 0) + stats.get("caught", 0))})
        rows.sort(key=lambda r: (-r["score"], r["name"]))
        return rows

    def awards(self, winner: str) -> List[str]:
        out = []
        best = max(self.players.values(), default=None,
                   key=lambda p: self.round_stats.get(p.pid, {}).get("clues", 0))
        if best is not None and self.round_stats.get(best.pid, {}).get("clues", 0) >= 3:
            out.append("Sharpest eyes: %s (%d clues)" % (best.username,
                                                         self.round_stats[best.pid]["clues"]))
        if self.caught_by:
            out.append("Case closed by %s" % self.caught_by)
        return out

    def result_extra(self, winner: str) -> Dict[str, Any]:
        return {"roles": {str(pid): role for pid, role in self.roles.items()},
                "side": winner}

    # ======================================================== clues & hints
    def _spawn_clue(self) -> None:
        spots = self.marks.get("clue", [])
        if not spots:
            return
        live = 3 + len(self.playing()) // 2
        if len(self.clues) >= live:
            return
        taken = [c["p"] for c in self.clues.values()]
        options = [m for m in spots if all(math.dist(m["p"], t) > 10.0 for t in taken)]
        if not options:
            return
        mark = self.rng.choice(options)
        cid = self.next_id
        self.next_id += 1
        self.clues[cid] = {"id": cid, "p": list(mark["p"]), "kind": self.rng.randrange(5)}

    def _pickups(self, playing: List[Player], moment: float) -> None:
        for cid, clue in list(self.clues.items()):
            for player in playing:
                if math.dist(player.pos, clue["p"]) < CLUE_REACH:
                    self.clues.pop(cid)
                    self._take_clue(player, clue)
                    break
        if self.gun is not None and moment - self.gun["at"] > 1.0:
            for player in playing:
                if self.is_murderer(player) or self.armed(player):
                    continue
                if math.dist(player.pos, self.gun["p"]) < GUN_REACH:
                    self.gun = None
                    self.roles[player.pid] = "hero"
                    self._kit(player)
                    player.send({"t": "wdx", "k": "armed"})
                    self.broadcast({"t": "wdx", "k": "gun_taken"}, exclude=player.pid)
                    self._event("wd_gun", player, "", dropped=False)
                    self._send_me(player, force=True)
                    break

    def _take_clue(self, player: Player, clue: Dict[str, Any]) -> None:
        if player.brain is not None:
            mind = self._mind(player)
            mind.pop("clue", None)
            mind["pause_until"] = engine.now() + player.brain.rng.uniform(0.3, 2.2)
        if self.is_murderer(player):
            self.counts["burned"] += 1
            self._stat(player, "burned")
            player.send({"t": "wdx", "k": "burned"})
            self.broadcast({"t": "wdx", "k": "clue", "id": clue["id"], "burn": 1}, exclude=player.pid)
            return
        self.case += 1
        self.counts["clues"] += 1
        player.score += CLUE_POINTS
        self._stat(player, "clues")
        self.badge(player, "wd_clues")
        self.broadcast({"t": "wdx", "k": "clue", "id": clue["id"], "by": player.pid,
                        "case": self.case})
        if len(self.hints) < len(HINTS) and self.case >= self._hint_goal(len(self.hints)):
            self._hint(HINTS[len(self.hints)])
        self._broadcast_state()

    def _hint_goal(self, n: int) -> int:
        per = 3 + len(self.roles) // 5
        return per * (n + 1)

    def _hint(self, kind: str) -> None:
        moment = engine.now()
        self.hints.append(kind)
        self.counts["hints"] += 1
        killers = [p for p in self.playing() if self.is_murderer(p)]
        if not killers:
            return
        msg: Dict[str, Any] = {"t": "wdx", "k": "hint", "hint": kind}
        if kind == "seen":
            where = self._place(killers[0].pos) or "somewhere in the house"
            msg["where"] = where
            msg["p"] = [round(v, 1) for v in killers[0].pos]
        elif kind == "trail":
            self.trail_until = moment + TRAIL_SECONDS
            msg["for"] = TRAIL_SECONDS
        elif kind == "suspects":
            others = [p for p in self.playing() if not self.is_murderer(p) and not self.armed(p)]
            self.rng.shuffle(others)
            names = [k.username for k in killers] + [p.username for p in others[:2]]
            self.rng.shuffle(names)
            self.suspects = names
            msg["names"] = names
        elif kind == "glimpse":
            self.glimpse_until = moment + GLIMPSE_SECONDS
            msg["ids"] = [k.pid for k in killers]
            msg["for"] = GLIMPSE_SECONDS
        for player in self.players.values():
            if self.is_murderer(player):
                player.send({"t": "wdx", "k": "hint_m", "hint": kind})
            else:
                player.send(msg)
        self._bot_hint(kind, killers)
        self._event("wd_hint", None, "", hint=kind)

    # ============================================================== twists
    def _twist_tick(self, playing: List[Player], moment: float) -> None:
        tw = self.twist
        kind = tw["kind"]
        if not kind:
            return
        extra = self.area.get("extra") or {}
        if not tw["on"]:
            warn = float(extra.get("twist_warn", 0.0) or 0.0)
            if warn and not tw["warn"] and moment >= tw["next"] - warn:
                tw["warn"] = moment
                self.broadcast({"t": "wdx", "k": "twist_warn", "twist": kind, "in": warn})
            if moment >= tw["next"]:
                length = float(extra.get("twist_for") or 6.0)
                tw.update({"on": True, "until": moment + length, "warn": 0.0})
                self.counts["twists"] += 1
                self.broadcast({"t": "wdx", "k": "twist", "twist": kind, "on": True, "for": length})
                self._broadcast_state()
        else:
            if kind == "tunnel":
                roof = float(extra.get("roof_y", 99.0))
                for player in playing:
                    if player.pos[1] > roof:
                        self.apply_damage(player, None, MAX_HEALTH * 3, "a tunnel")
            if moment >= tw["until"]:
                lo, hi = extra.get("twist_every") or [35.0, 50.0]
                tw.update({"on": False, "next": moment + self.rng.uniform(lo, hi)})
                self.broadcast({"t": "wdx", "k": "twist", "twist": kind, "on": False})
                self._broadcast_state()

    def sight(self) -> float:
        """How far anybody can see right now (the lights, the fog)."""
        if self.twist["on"] and self.twist["kind"] in ("storm", "tunnel", "fog"):
            return SIGHT_DIM
        return SIGHT

    def masked(self) -> bool:
        return self.twist["on"] and self.twist["kind"] == "masks"

    # ================================================================ chat
    def handle_chat(self, player: Player, message: Dict[str, Any]) -> None:
        if self.phase == "active" and (player.extra.get("out") or not player.alive) and \
                player.team in ("ffa",) and player.pid in self.roles:
            # the dead talk only to the dead
            text = message.get("m")
            if not isinstance(text, str):
                return
            text = " ".join(text.split())[:200]
            if not text:
                return
            entry = {"t": "chat", "from": player.username, "id": player.pid,
                     "uid": player.user_id, "team": player.team, "m": "[dead] " + text,
                     "kind": "team", "at": time.time(), "admin": player.admin}
            for other in self.players.values():
                if other.extra.get("out") or not other.alive or other.pid not in self.roles:
                    other.send(entry)
            return
        super().handle_chat(player, message)
        if self.phase == "active" and player.brain is None and player.alive:
            self._heard(player, message.get("m"))

    def _heard(self, speaker: Player, text: Any) -> None:
        """A real player named somebody: the bots take it into account."""
        if not isinstance(text, str):
            return
        low = text.lower()
        if not any(w in low for w in MURDER_WORDS):
            return
        for other in self.playing():
            if other is speaker or len(other.username) < 3:
                continue
            if re.search(r"\b%s\b" % re.escape(other.username.lower()), low):
                for bot in self.players.values():
                    if bot.brain is not None and bot is not other:
                        self._suspect(bot, other, 0.45, engine.now())

    # ============================================================== helpers
    def _stat(self, player: Player, key: str, amount: float = 1.0) -> None:
        stats = self.round_stats.setdefault(player.pid, {})
        stats[key] = stats.get(key, 0.0) + amount

    def _place(self, pos: Sequence[float]) -> str:
        best, best_d = "", 1e9
        for p, name in self.landmarks:
            d = math.hypot(p[0] - pos[0], p[2] - pos[2]) + abs(p[1] - pos[1]) * 2.0
            if d < best_d:
                best, best_d = name, d
        return best if best_d < 70 else ""

    def _event(self, kind: str, player: Optional[Player], team: str, **extra: Any) -> None:
        moment = engine.now()
        if moment - self.events_said.get(kind, -99.0) < 5.0:
            return
        self.events_said[kind] = moment
        data = {"world": "whodunit", "by": player.username if player else "",
                "by_team": "", "team": team}
        data.update(extra)
        if self.bots is not None:
            self.bots.on_game_event(kind, data)

    def _broadcast_state(self) -> None:
        self.broadcast({"t": "wds", "s": self.hud_state()})

    # ============================================================== state
    def hud_state(self) -> Dict[str, Any]:
        alive = len([p for p in self.playing()])
        goal = self._hint_goal(len(self.hints)) if len(self.hints) < len(HINTS) else self.case
        prev = self._hint_goal(len(self.hints) - 1) if self.hints else 0
        tw = self.twist
        return {"wd": {"case": self.case, "goal": goal, "prev": prev, "hints": list(self.hints),
                       "alive": alive, "guests": len(self.roles),
                       "twist": tw["kind"], "on": bool(tw["on"]),
                       "left": round(max(0.0, tw["until"] - engine.now()), 1) if tw["on"] else 0,
                       "gun": bool(self.gun)}}

    def snapshot_extra(self) -> Any:
        if self.phase not in ("active", "setup"):
            return None
        out: Dict[str, Any] = {}
        if self.clues:
            out["cl"] = [[c["id"], c["p"][0], c["p"][1], c["p"][2], c["kind"]]
                         for c in self.clues.values()]
        if self.bodies:
            out["bd"] = [[b["id"], b["p"][0], b["p"][1], b["p"][2], b["yaw"]] for b in self.bodies]
        if self.knives:
            out["kn"] = [[k["id"], round(k["p"][0], 2), round(k["p"][1], 2), round(k["p"][2], 2)]
                         for k in self.knives.values()]
        if self.masked():
            out["mk"] = 1
        return out

    def me_state(self, player: Player) -> Dict[str, Any]:
        moment = engine.now()
        role = self.roles.get(player.pid, "")
        out = {"role": role, "clues": int(self.round_stats.get(player.pid, {}).get("clues", 0))}
        if role == "murderer":
            out["throw"] = round(max(0.0, player.extra.get("wd_throw_at", 0.0) - moment), 1)
            # (not "out": the arena client reads that as out of the round)
            out["drawn"] = bool(player.extra.get("wd_knife_out"))
            out["partners"] = [p.username for p in self.players.values()
                               if p is not player and self.is_murderer(p)]
        elif role in ("detective", "hero"):
            out["reload"] = round(max(0.0, player.reload_until - moment), 1)
        return out

    def score_row(self, player: Player, row: Dict[str, Any]) -> None:
        # nothing on the board may give a murderer away while the round is on
        row["role"] = ""
        row["clues"] = int(self.round_stats.get(player.pid, {}).get("clues", 0))
        if self.phase == "active":
            row["kills"] = 0
            row["score"] = 0
            row["deaths"] = 0

    def describe(self) -> Dict[str, Any]:
        info = super().describe()
        info.update({"case": self.case, "hints": list(self.hints)})
        return info

    def sleep_extra(self) -> Dict[str, Any]:
        return {}

    def resume_progress(self, progress: float, state: Dict[str, Any]) -> None:
        """Woken mid-round: the roles are dealt afresh for whoever is here."""

    # ================================================================ bots
    def _mind(self, player: Player) -> Dict[str, Any]:
        return player.extra.setdefault("wd_mind", {"sus": {}})

    def _suspect(self, bot: Player, who: Player, amount: float, moment: float,
                 sure: bool = False) -> None:
        if bot is who or self.is_murderer(bot) and self.is_murderer(who):
            return
        sus = self._mind(bot)["sus"]
        old = sus.get(who.pid, (0.0, moment))[0]
        sus[who.pid] = (1.0 if sure else min(0.95, old + amount), moment)

    def suspicion(self, bot: Player, who: Player) -> float:
        entry = self._mind(bot)["sus"].get(who.pid)
        if entry is None:
            return 0.0
        score, at = entry
        # an old hunch fades
        return max(0.0, score - max(0.0, engine.now() - at - 30.0) * 0.01)

    def prime_suspect(self, bot: Player) -> Tuple[Optional[Player], float]:
        best, best_s = None, 0.0
        for pid in list(self._mind(bot)["sus"].keys()):
            other = self.players.get(pid)
            if other is None or not self.in_play(other):
                continue
            s = self.suspicion(bot, other)
            if s > best_s:
                best, best_s = other, s
        return best, best_s

    def _bot_witness(self, murderer: Player, victim: Player, witnesses: List[Player],
                     moment: float) -> None:
        masked = self.masked()
        eyes = self.sight() * (0.4 + 0.6 * self.pct("eyes"))
        for w in witnesses:
            if w.brain is None or math.dist(w.pos, murderer.pos) > eyes:
                continue
            mind = self._mind(w)
            mind["fled_from"] = list(murderer.pos)
            mind["scared"] = moment
            if masked:
                # somebody in a mask: no telling who, only that it happened
                self.callout(w.brain, ["someone in a mask did it", "a MASK stabbed them",
                                       "RUN its a mask", "murder!! cant see who"], "masked",
                             chance=0.7, every=40.0)
                continue
            self._suspect(w, murderer, 1.0, moment, sure=True)
            if not self.armed(w):
                lines = [line.format(name=murderer.username) for line in SEEN_LINES]
                if self.callout(w.brain, lines, "seen%d" % murderer.pid, chance=0.9, every=60.0):
                    # everybody heard it: the other bots believe it, mostly
                    # (hearsay alone is not quite enough for a careful
                    # detective to shoot on)
                    for other in self.players.values():
                        if other.brain is not None and other is not w and other is not murderer:
                            self._suspect(other, murderer, 0.4 + 0.3 * self.pct("trust"), moment)

    def _bot_hint(self, kind: str, killers: List[Player]) -> None:
        moment = engine.now()
        for bot in self.players.values():
            if bot.brain is None or self.is_murderer(bot) or not self.in_play(bot):
                continue
            mind = self._mind(bot)
            if kind == "seen":
                mind["lead"] = (list(killers[0].pos), moment)
            elif kind == "trail":
                for k in killers:
                    if math.dist(k.pos, bot.pos) < 60.0:
                        self._suspect(bot, k, 0.45, moment)
                mind["trail"] = moment + TRAIL_SECONDS
            elif kind == "suspects":
                for name in self.suspects:
                    other = next((p for p in self.players.values() if p.username == name), None)
                    if other is not None and other is not bot:
                        self._suspect(bot, other, 0.26, moment)
            elif kind == "glimpse":
                for k in killers:
                    self._suspect(bot, k, 1.0, moment, sure=True)

    def _bot_saw_shot(self, shooter: Player, origin: Sequence[float], end: Sequence[float]) -> None:
        """A murderer is never shown the revolver: a bot one learns who carries
        it the way a player would -- by seeing the flash (and feeling a round
        go past)."""
        moment = engine.now()
        for m in self.playing():
            if m.brain is None or not self.is_murderer(m):
                continue
            mind = self._mind(m)
            eye = [m.pos[0], m.pos[1] + EYE_HEIGHT, m.pos[2]]
            if math.dist(m.pos, shooter.pos) < self.sight() and self.line_of_sight(eye, origin):
                mind.setdefault("armed_seen", {})[shooter.pid] = moment
            # the shot's path past them: close enough to feel it
            ab = [end[i] - origin[i] for i in range(3)]
            span = sum(v * v for v in ab) or 1e-6
            t = max(0.0, min(1.0, sum((eye[i] - origin[i]) * ab[i] for i in range(3)) / span))
            if math.dist(eye, [origin[i] + ab[i] * t for i in range(3)]) < 6.0:
                mind["shot_at"] = (list(shooter.pos), moment)

    def _known_armed(self, murderer: Player, other: Player) -> bool:
        """Whether a murderer bot knows ``other`` carries the revolver: it has
        seen them fire it (the dead keep no secrets: a misfire disgraces the
        detective in front of everybody)."""
        return self.armed(other) and other.pid in self._mind(murderer).get("armed_seen", {})

    def bot_tick(self, moment: float) -> None:
        for player in self.players.values():
            if player.brain is not None:
                player.brain.target = None
        if self.phase != "active":
            return
        for player in self.playing():
            mind = player.extra.get("wd_mind") or {}
            if mind.get("stow_at") and moment >= mind["stow_at"]:
                mind.pop("stow_at", None)
                self._stow(player)
        # a guest seen holding a knife is a murderer
        if moment < getattr(self, "_look_at", 0.0):
            return
        self._look_at = moment + 0.5
        sight = self.sight()
        for m in self.playing():
            if not self.knife_out(m) or self.masked():
                continue
            eye_m = [m.pos[0], m.pos[1] + 4.0, m.pos[2]]
            for bot in self.playing():
                if bot.brain is None or bot is m or self.is_murderer(bot):
                    continue
                if math.dist(bot.pos, m.pos) > sight * (0.4 + 0.6 * self.pct("eyes")):
                    continue
                if self.line_of_sight([bot.pos[0], bot.pos[1] + EYE_HEIGHT, bot.pos[2]], eye_m):
                    self._suspect(bot, m, 0.9, moment)

    def bot_role(self, brain) -> str:
        return "guest"

    def hostiles_for(self, player: Player):
        """Nobody here is an enemy on sight: the knife and the revolver are
        used by the role brains below, never by the generic fight (which would
        draw a murderer's knife at the first guest it saw)."""
        yield from ()

    def bot_goal_weights(self, brain, weights: Dict[str, float]) -> Dict[str, float]:
        weights = dict(weights)
        weights["objective"] = weights.get("objective", 1.0) * 6.0
        weights["fight"] = 0.0
        return weights

    def bot_urgent(self, brain) -> bool:
        return self.phase == "active" and bool(self.setting("enabled"))

    def bot_objective(self, brain) -> None:
        if not self.setting("enabled") or self.phase != "active":
            return
        p = brain.p
        if not self.in_play(p):
            return
        if self._unperch(brain):
            return
        role = self.role(p)
        if role == "murderer":
            self._bot_murderer(brain)
        elif role in ("detective", "hero"):
            self._bot_detective(brain)
        else:
            self._bot_innocent(brain)

    # ---- shared
    def _go(self, brain, point: Sequence[float], key: str) -> None:
        if math.hypot(brain.p.pos[0] - point[0], brain.p.pos[2] - point[2]) < 2.0 and \
                abs(brain.p.pos[1] - point[1]) < 2.5:
            brain.waypoints = []
            return
        hop = self._via(brain.p, point)
        if hop is not None:
            point, key = hop, "via%d_%d" % (int(hop[0] * 3), int(hop[2] * 3))
        brain.go(list(point), key)

    def _levels(self) -> List[float]:
        """The heights of the place's floors: wherever a room, a clue, a
        staircase's end or a spawn is."""
        cached = getattr(self, "_levels_for", None)
        if cached is not None and cached[0] == self.area_id:
            return cached[1]
        ys = set()
        for kind in ("roam", "clue", "stair"):
            for m in self.marks.get(kind) or ():
                ys.add(round(m["p"][1], 1))
        for spawn in (self.area.get("spawns") or {}).get("start") or ():
            ys.add(round(spawn["p"][1], 1))
        levels = sorted(ys)
        self._levels_for = (self.area_id, levels)
        return levels

    def _reachable(self, q: Sequence[float]) -> bool:
        """Can the bots find floor at ``q`` -- a clue, a room, a staircase's
        end?  A corner or two of a house has none on their map (the strip of
        the crypt between its wall and the tombs, the bottom of the crypt
        stair): a bot sent there walks to the spot over it and stands."""
        nav = getattr(self.host, "nav", None)
        if nav is None or not nav.ready:
            return True
        cache = getattr(self, "_reach_for", None)
        if cache is None or cache[0] != self.area_id:
            cache = (self.area_id, {})
            self._reach_for = cache
        key = (round(q[0], 1), round(q[1], 1), round(q[2], 1))
        found = cache[1].get(key)
        if found is None:
            node = nav.nearest(q, 2)
            found = node >= 0 and abs(nav.py[node] - q[1]) < 2.5 and \
                math.hypot(nav.px[node] - q[0], nav.pz[node] - q[2]) < 4.5
            cache[1][key] = found
        return found

    def _unperch(self, brain) -> bool:
        """A bot that has jumped up onto something with no way on from it in
        its graph -- a rail, a lifeboat, a roof -- and stalled there: walk it
        off the edge, towards the nearest room below."""
        p = brain.p
        mind = self._mind(p)
        moment = engine.now()
        if mind.get("unperch_until", 0.0) > moment:
            if p.pos[1] < mind.get("perch_y", 1e9) - 1.0:
                mind.pop("unperch_until", None)
                mind.pop("perch_since", None)
                return False
            brain.waypoints = [list(mind["perch_to"])]
            return True
        if getattr(brain, "airborne", False) or brain.waypoints:
            mind.pop("perch_since", None)
            return False
        levels = self._levels()
        if not levels or min(abs(y - p.pos[1]) for y in levels) <= 2.5:
            mind.pop("perch_since", None)
            return False
        since = mind.setdefault("perch_since", moment)
        if moment - since < 2.0:
            return False
        below = [m["p"] for kind in ("roam", "stair") for m in self.marks.get(kind) or ()
                 if m["p"][1] < p.pos[1] - 2.5 and
                 math.hypot(m["p"][0] - p.pos[0], m["p"][2] - p.pos[2]) > 6.0]
        if not below:
            return False
        q = min(below, key=lambda q: math.hypot(q[0] - p.pos[0], q[2] - p.pos[2]) +
                abs(q[1] - p.pos[1]))
        to = [q[0], p.pos[1], q[2]]
        mind.update({"unperch_until": moment + 3.0, "perch_y": p.pos[1], "perch_to": to})
        brain.waypoints = [to]
        self.doing(brain, "climbing down")
        return True

    def _via(self, p: Player, point: Sequence[float]) -> Optional[List[float]]:
        """Bound for another floor: the staircase to take first (the maps
        mark both ends of every one).  A long search across four decks runs
        out of budget, and a search that runs out leaves a bot on the spot
        right over where it was going -- on a lifeboat, say."""
        mind = self._mind(p)
        moment = engine.now()
        held = mind.get("via")
        if held is not None:
            # on a staircase: see it through to the other end
            to, until = held
            # (a step's height off counts: coming down, a body stops on the
            # lip of the bottom step right over the mark at its foot)
            there = abs(to[1] - p.pos[1]) <= 3.0 and math.hypot(to[0] - p.pos[0], to[2] - p.pos[2]) < 3.0
            if moment < until and not there:
                return list(to)
            mind.pop("via", None)
        if abs(point[1] - p.pos[1]) < 4.0:
            return None
        best, best_s = None, 1e9
        for st in self.marks.get("stair") or ():
            a, to = st["p"], st.get("to")
            if to is None or abs(a[1] - p.pos[1]) > 1.5:
                continue                    # not on this floor (or half way up it)
            if not self._reachable(to):
                continue                    # a way down the bots cannot see the end of
            if abs(to[1] - point[1]) >= abs(a[1] - point[1]):
                continue                    # it goes the wrong way
            near = math.hypot(a[0] - p.pos[0], a[2] - p.pos[2])
            if near < 4.0:
                mind["via"] = (list(to), moment + 14.0)
                return list(to)             # at its foot (or its head): take it
            s = near + math.hypot(to[0] - point[0], to[2] - point[2]) + abs(to[1] - point[1]) * 3.0
            if s < best_s:
                best, best_s = list(a), s
        return best

    def _face(self, brain, target: Sequence[float]) -> List[float]:
        p = brain.p
        dx, dy, dz = target[0] - p.pos[0], target[1] - (p.pos[1] + EYE_HEIGHT), target[2] - p.pos[2]
        flat = math.hypot(dx, dz) or 1e-6
        p.yaw = math.atan2(dx, dz)
        p.pitch = math.atan2(dy, flat)
        brain.aim_yaw = p.yaw
        return normalise([dx, dy, dz])

    @staticmethod
    def _looking_at(a: Player, b: Player, cone: float = 0.6) -> bool:
        """``a`` faces ``b`` (within about 35 degrees either way)."""
        dx, dz = b.pos[0] - a.pos[0], b.pos[2] - a.pos[2]
        off = math.atan2(dx, dz) - a.yaw
        return abs(math.atan2(math.sin(off), math.cos(off))) < cone

    def _sees(self, a: Player, b: Player, reach: Optional[float] = None) -> bool:
        if math.dist(a.pos, b.pos) > (reach or self.sight()):
            return False
        return self.line_of_sight([a.pos[0], a.pos[1] + EYE_HEIGHT, a.pos[2]],
                                  [b.pos[0], b.pos[1] + 3.0, b.pos[2]])

    # ---- getting about the way a guest does
    def _style(self, brain, mind: Dict[str, Any]) -> str:
        """How this guest spends a case when nothing is chasing it, from its
        persona: a sleuth after every clue in the house, a collector, a buddy
        who sticks with somebody, a wallflower who keeps to a corner, a
        wanderer who cannot keep still.  Dealt afresh each case."""
        style = mind.get("style")
        if style is None:
            weights = {
                "sleuth": 0.3 + brain.t("explore", 0.2) * 1.4 + brain.t("aggression", 0.5) * 0.5,
                "collector": 0.75,
                "buddy": 0.2 + brain.t("support", 0.2) * 1.2 + brain.t("social", 0.5) * 0.5,
                "wallflower": 0.15 + (1.0 - brain.t("aggression", 0.5)) * 0.4 +
                (1.0 - brain.t("social", 0.5)) * 0.3,
                "wanderer": 0.12 + brain.t("chaos", 0.08) * 1.5 + brain.t("jumpy", 0.2) * 0.7,
            }
            style = brain.rng.choices(list(weights), list(weights.values()))[0]
            mind["style"] = style
        return style

    def _offset(self, point: Sequence[float], p: Player, radius: float) -> List[float]:
        """Somewhere by ``point`` of this bot's own, so two of them sent to the
        same place do not stand on the same spot (and never through a wall)."""
        nav = getattr(self.host, "nav", None)
        if nav is None or not nav.ready:
            return list(point)
        eye = [point[0], point[1] + 1.5, point[2]]
        base = (p.pid * 2.399) % (2.0 * math.pi)
        for r in (radius, radius * 0.6):
            for turn in (0.0, 1.9, -1.9, 3.1, 0.9, -0.9):
                a = base + turn
                x, z = point[0] + math.sin(a) * r, point[2] + math.cos(a) * r
                if nav.walkable(x, point[1], z) and self.line_of_sight(eye, [x, point[1] + 1.5, z]):
                    return [x, point[1], z]
        # a corridor, say: short of it, on the way in
        d = math.hypot(p.pos[0] - point[0], p.pos[2] - point[2])
        if d > radius:
            x = point[0] + (p.pos[0] - point[0]) / d * radius
            z = point[2] + (p.pos[2] - point[2]) / d * radius
            if nav.walkable(x, point[1], z):
                return [x, point[1], z]
        return list(point)

    def _look_round(self, brain, mind: Dict[str, Any], moment: float, at: Optional[Player] = None) -> None:
        """Standing about: turn the view the way a person does at a party --
        to the faces in the room (the one it has a hunch about, most of all),
        a doorway, back again."""
        p = brain.p
        if at is not None:
            brain.look_yaw = math.atan2(at.pos[0] - p.pos[0], at.pos[2] - p.pos[2])
            return
        if moment < mind.get("glance_at", 0.0):
            return
        mind["glance_at"] = moment + brain.rng.uniform(0.7, 2.2)
        faces = [o for o in self.playing() if o is not p and math.dist(o.pos, p.pos) < 32.0 and
                 abs(o.pos[1] - p.pos[1]) < 6.0]
        if faces and brain.rng.random() < 0.6:
            hunch, sure = self.prime_suspect(p)
            face = hunch if hunch in faces and sure > 0.25 else brain.rng.choice(faces)
            brain.look_yaw = math.atan2(face.pos[0] - p.pos[0], face.pos[2] - p.pos[2])
        else:
            brain.look_yaw = p.yaw + brain.rng.uniform(-1.7, 1.7)

    def _fidget(self, brain, mind: Dict[str, Any], moment: float) -> None:
        """Nobody stands stock still: a hop now and then (the restless more),
        and a few steps up and down the room."""
        p = brain.p
        restless = brain.t("jumpy", 0.2) + brain.t("chaos", 0.08) + \
            (0.35 if mind.get("style") == "wanderer" else 0.0)
        if not brain.airborne and brain.rng.random() < 0.012 * restless:
            brain.airborne = True
            brain.vy = JUMP_SPEED
        if brain.waypoints or moment < mind.get("pace_at", 0.0):
            return
        mind["pace_at"] = moment + brain.rng.uniform(2.5, 7.0) / (0.6 + restless)
        if brain.rng.random() < 0.45:
            a = brain.rng.uniform(0.0, 2.0 * math.pi)
            r = brain.rng.uniform(1.5, 4.5)
            step = [p.pos[0] + math.sin(a) * r, p.pos[1], p.pos[2] + math.cos(a) * r]
            nav = getattr(self.host, "nav", None)
            if nav is not None and nav.ready and nav.walkable(step[0], step[1], step[2]) and \
                    self.line_of_sight([p.pos[0], p.pos[1] + 1.5, p.pos[2]], [step[0], step[1] + 1.5, step[2]]):
                brain.waypoints = [step]

    def _roam(self, brain, mind: Dict[str, Any], key: str = "wander") -> Tuple[str, str]:
        """Room to room the way a guest goes about a house: somewhere it has
        not been lately and everybody else is not, and a while there looking
        round before moving on.  Says whether it is on its way or there, and
        where."""
        p = brain.p
        moment = engine.now()
        spot = mind.get("spot")
        if spot is not None:
            here = math.hypot(p.pos[0] - spot[0], p.pos[2] - spot[2]) < 3.2 and abs(p.pos[1] - spot[1]) < 3.0
            if here:
                if "linger_until" not in mind:
                    mind["linger_until"] = moment + self._linger(brain, mind)
                if moment < mind["linger_until"]:
                    if not mind.get("pacing"):
                        brain.waypoints = []
                    self._look_round(brain, mind, moment)
                    self._fidget(brain, mind, moment)
                    return "here", self._place(spot)
                spot = None
            elif moment > mind.get("spot_until", 0.0):
                spot = None                 # a long way round: somewhere else, then
        if spot is None:
            spot = self._next_spot(brain, mind)
            if spot is None:
                super().bot_objective(brain)
                return "going", ""
            mind["spot"] = spot
            mind.pop("linger_until", None)
            mind["spot_until"] = moment + 40.0
        self._go(brain, spot, key + "%d" % int(spot[0] * 3 + spot[2]))
        return "going", self._place(spot)

    def _linger(self, brain, mind: Dict[str, Any]) -> float:
        lo, hi = {"sleuth": (2.0, 6.0), "collector": (3.0, 9.0), "buddy": (3.0, 7.0),
                  "wallflower": (9.0, 22.0), "wanderer": (1.0, 4.0),
                  "detective": (3.0, 8.0), "murderer": (3.0, 10.0)}.get(mind.get("style", ""), (3.0, 8.0))
        return brain.rng.uniform(lo, hi)

    def _next_spot(self, brain, mind: Dict[str, Any]) -> Optional[List[float]]:
        p = brain.p
        moment = engine.now()
        options = self.marks.get("roam") or [{"p": q} for q, _ in self.landmarks]
        if not options:
            return None
        style = mind.get("style", "")
        reach = {"sleuth": 150.0, "wanderer": 190.0, "wallflower": 60.0, "detective": 130.0}.get(style, 100.0)
        seen = mind.setdefault("seen", {})
        others = [o for o in self.playing() if o is not p]
        heading = [self._mind(o).get("spot") for o in others if o.brain is not None]
        fresh = [b["p"] for b in self.bodies if moment - b["at"] < 45.0]
        best, best_s, best_key = None, -1e9, ""
        for m in options:
            q = m["p"]
            d = math.dist(q, p.pos)
            if d < 8.0 or not self._reachable(q):
                continue                    # here already (or nowhere a bot can stand)
            key = "%d_%d_%d" % (int(q[0]), int(q[1]), int(q[2]))
            s = -abs(d - reach * 0.5) * 0.25 - max(0.0, d - reach) * 0.6
            s += min(70.0, moment - seen.get(key, -1e9)) * 0.5
            s -= 22.0 * sum(1 for o in others if math.dist(o.pos, q) < 12.0)
            s -= 26.0 * sum(1 for h in heading if h is not None and math.dist(h, q) < 10.0)
            if not self.is_murderer(p):
                # nobody innocent goes back to look at a body for long
                s -= 30.0 * sum(1 for b in fresh if math.dist(b, q) < 18.0)
            if abs(q[1] - p.pos[1]) > 4.0:
                s -= 6.0 if style in ("sleuth", "wanderer", "detective") else 18.0
            s += brain.rng.uniform(0.0, 18.0)
            if s > best_s:
                best, best_s, best_key = q, s, key
        if best is None:
            return None
        seen[best_key] = moment
        return self._offset(best, p, brain.rng.uniform(0.8, 3.2))

    def _pick_clue(self, brain, mind: Dict[str, Any], reach: float,
                   avoid: Optional[Sequence[float]] = None) -> Optional[Dict[str, Any]]:
        """A clue of its own to go for: never one somebody nearer is already
        after (the way a person sees another get there first and turns for the
        next), and one a little out of the way over the one everybody sees."""
        p = brain.p
        claims: Dict[int, Player] = {}
        for other in self.playing():
            if other is not p and other.brain is not None:
                cid = self._mind(other).get("clue")
                if cid is not None:
                    claims[cid] = other
        playing = [o for o in self.playing() if o is not p]
        best, best_s = None, 1e9
        for cid, clue in self.clues.items():
            q = clue["p"]
            d = math.dist(q, p.pos)
            if d > reach or not self._reachable(q):
                continue
            rival = claims.get(cid)
            if rival is not None and math.dist(rival.pos, q) < d + 4.0:
                continue
            s = d + ((cid * 37 + p.pid * 11) % 17)
            if abs(q[1] - p.pos[1]) > 6.0:
                s += 25.0
            if avoid is not None and math.dist(q, avoid) < 25.0:
                s += 200.0
            if any(math.dist(o.pos, q) < min(d - 3.0, 12.0) for o in playing):
                s += 60.0                   # somebody is standing right by it
            if s < best_s:
                best, best_s = clue, s
        if best is None:
            mind.pop("clue", None)
            return None
        mind["clue"] = best["id"]
        return best

    def _tail(self, brain, target: Player, standoff: float, key: str) -> None:
        """Keep ``target`` in view from across the room -- not at its elbow."""
        p = brain.p
        d = math.dist(target.pos, p.pos)
        if d > standoff + 5.0 or not self._sees(p, target, standoff + 25.0):
            # from its own side: two of them on one guest do not end up
            # shoulder to shoulder
            a = math.atan2(p.pos[0] - target.pos[0], p.pos[2] - target.pos[2]) + \
                ((p.pid * 0.618) % 1.0 - 0.5) * 1.2
            q = [target.pos[0] + math.sin(a) * standoff, target.pos[1],
                 target.pos[2] + math.cos(a) * standoff]
            nav = getattr(self.host, "nav", None)
            if nav is None or not nav.ready or not nav.walkable(q[0], q[1], q[2]) or \
                    not self.line_of_sight([target.pos[0], target.pos[1] + 1.5, target.pos[2]],
                                           [q[0], q[1] + 1.5, q[2]]):
                q = self._offset(target.pos, p, standoff * 0.7)
            self._go(brain, q, key + "%d" % target.pid)
        elif d < standoff - 6.0:
            away = math.atan2(p.pos[0] - target.pos[0], p.pos[2] - target.pos[2])
            self._go(brain, [p.pos[0] + math.sin(away) * 4.0, p.pos[1], p.pos[2] + math.cos(away) * 4.0],
                     key + "back%d" % target.pid)
        else:
            brain.waypoints = []
            self._fidget(brain, self._mind(p), engine.now())
        self._look_round(brain, self._mind(p), engine.now(), at=target)

    def _buddy(self, brain, mind: Dict[str, Any], moment: float) -> Optional[Player]:
        """Somebody to stick with for a while: one guest each (two to a pair,
        not a crowd), never a follower itself, and never one it has a hunch
        about."""
        p = brain.p
        friend = self.players.get(mind.get("buddy", 0))
        if friend is not None and self.in_play(friend) and moment < mind.get("buddy_until", 0.0) and \
                self.suspicion(p, friend) < 0.4:
            return friend
        mind.pop("buddy", None)
        if moment < mind.get("buddy_next", 0.0):
            return None
        mind["buddy_next"] = moment + brain.rng.uniform(6.0, 16.0)
        taken = {self._mind(o).get("buddy") for o in self.playing() if o is not p and o.brain is not None}
        best, best_s = None, -1e9
        for other in self.playing():
            if other is p or other.pid in taken or self.suspicion(p, other) >= 0.3:
                continue
            if other.brain is not None and self._mind(other).get("buddy"):
                continue                    # no trains of followers
            d = math.dist(other.pos, p.pos)
            if d > 70.0:
                continue
            s = -d + (20.0 if other.brain is None else 0.0) + (15.0 if self.armed(other) else 0.0)
            s += brain.rng.uniform(0.0, 15.0)
            if s > best_s:
                best, best_s = other, s
        if best is not None:
            mind["buddy"] = best.pid
            mind["buddy_until"] = moment + brain.rng.uniform(20.0, 50.0)
            mind["side"] = brain.rng.choice((-1.0, 1.0))
        return best

    def _keep_with(self, brain, mind: Dict[str, Any], friend: Player, moment: float) -> None:
        """At a friend's shoulder -- a step behind and to one side -- watching
        the room while they do whatever they are doing."""
        p = brain.p
        a = friend.yaw + math.pi + mind.get("side", 1.0) * 0.8
        spot = [friend.pos[0] + math.sin(a) * 5.5, friend.pos[1], friend.pos[2] + math.cos(a) * 5.5]
        nav = getattr(self.host, "nav", None)
        if nav is None or not nav.ready or not nav.walkable(spot[0], spot[1], spot[2]):
            spot = self._offset(friend.pos, p, 5.5)
        d = math.dist(friend.pos, p.pos)
        busy = sum(1 for o in self.playing() if o is not p and o is not friend and
                   math.dist(o.pos, friend.pos) < 8.0)
        if busy >= 1:
            # company enough round them already: keep them in sight from
            # across the room instead
            self._tail(brain, friend, 11.0, "buddy")
        elif d > 10.0 or d < 3.0:
            self._go(brain, spot, "buddy%d" % friend.pid)
        else:
            brain.waypoints = []
            self._look_round(brain, mind, moment)
            self._fidget(brain, mind, moment)

    def _bot_view_body(self, brain, mind: Dict[str, Any], style: str, moment: float) -> bool:
        """A fresh body: the curious go and look -- from a few steps off, two
        at most, a few seconds -- and then want to be anywhere else."""
        if not self.bodies:
            return False
        p = brain.p
        body = self.bodies[-1]
        if moment - body["at"] > 22.0 or math.dist(body["p"], p.pos) > 80.0:
            mind.pop("view", None)
            return False
        bid = body["id"]
        rolls = mind.setdefault("body_roll", {})
        if bid not in rolls:
            chance = {"sleuth": 0.7, "collector": 0.3, "buddy": 0.2, "wallflower": 0.05,
                      "wanderer": 0.45}.get(style, 0.3) * (0.6 + self.pct("bravery") * 0.8)
            viewers = sum(1 for o in self.playing() if o is not p and o.brain is not None and
                          self._mind(o).get("view") == bid)
            rolls[bid] = viewers < 2 and brain.rng.random() < chance
        if not rolls[bid]:
            return False
        mind["view"] = bid
        spot = mind.get("view_at")
        if spot is None or mind.get("view_id") != bid:
            spot = self._offset(body["p"], p, brain.rng.uniform(4.5, 7.0))
            if not self._reachable(spot):
                rolls[bid] = False
                mind.pop("view", None)
                return False
            mind.update({"view_at": spot, "view_id": bid, "view_until": None})
        if math.hypot(p.pos[0] - spot[0], p.pos[2] - spot[2]) > 2.5:
            self._go(brain, spot, "body%d" % bid)
            self.doing(brain, "going to see the body")
            return True
        if mind.get("view_until") is None:
            mind["view_until"] = moment + brain.rng.uniform(2.5, 5.0)
            where = self._place(body["p"])
            self.callout(brain, ["rip %s" % body["name"], "who did this", "%s is dead" % body["name"],
                                 "omg" + (" in the " + where if where and not where.startswith("the ")
                                          else (" in " + where if where else "")),
                                 "anyone see who did it?"], "viewbody", chance=0.4, every=40.0)
        if moment < mind["view_until"]:
            brain.waypoints = []
            brain.look_yaw = math.atan2(body["p"][0] - p.pos[0], body["p"][2] - p.pos[2])
            self.doing(brain, "looking at the body of %s" % body["name"])
            return True
        rolls[bid] = False
        mind.pop("view", None)
        mind.pop("spot", None)              # and then away from it
        return False

    # ---- innocents
    def _bot_innocent(self, brain) -> None:
        p = brain.p
        moment = engine.now()
        mind = self._mind(p)
        style = self._style(brain, mind)
        threat, sure = self.prime_suspect(p)
        if threat is not None and sure >= 0.7 and math.dist(threat.pos, p.pos) < 45.0:
            self._flee(brain, threat.pos, "from %s" % threat.username)
            return
        scared = mind.get("scared", -99.0)
        if moment - scared < 6.0 and mind.get("fled_from"):
            self._flee(brain, mind["fled_from"], "from a body")
            where = self._place(mind["fled_from"])
            self.callout(brain, ["RUN", "body!!", "someones dead" + (" in " + where if where else ""),
                                 "get out of " + (where or "here")], "body", chance=0.5, every=40.0)
            return
        mind.pop("flee_to", None)
        # the revolver on the floor: the brave go for it (one at a time --
        # whoever is nearest; the rest leave it to them)
        if self.gun is not None and not mind.get("for_gun") and self._reachable(self.gun["p"]) and \
                brain.rng.random() < 0.15 + self.pct("bravery") * 0.5:
            d = math.dist(self.gun["p"], p.pos)
            if d < 90.0 and mind.get("gun_try", 0.0) < moment:
                mind["gun_try"] = moment + 20.0
                mind["for_gun"] = True
        if mind.get("for_gun") and self.gun is not None:
            d = math.dist(self.gun["p"], p.pos)
            if any(o is not p and o.brain is not None and self._mind(o).get("for_gun") and
                   math.dist(o.pos, self.gun["p"]) < d for o in self.playing()):
                mind["for_gun"] = False     # somebody nearer is on their way to it
        if mind.get("for_gun") and self.gun is not None:
            self._go(brain, self.gun["p"], "gun")
            self.doing(brain, "going for the detective's revolver")
            self.callout(brain, ["getting the gun", "ill get the gun", "gun's here"], "gun",
                         chance=0.4, every=60.0)
            return
        mind.pop("for_gun", None)
        if moment < mind.get("pause_until", 0.0):
            # just picked something up: a look at it, and round the room
            brain.waypoints = []
            self._look_round(brain, mind, moment)
            return
        if self._bot_view_body(brain, mind, style, moment):
            return
        # a hunch about somebody: the bold keep an eye on them from across
        # the room, and say so
        watched = threat is not None and any(
            o is not p and o.brain is not None and not self.armed(o) and
            self._mind(o).get("watching") == threat.pid for o in self.playing())
        if threat is not None and 0.45 <= sure < 0.7 and style in ("sleuth", "buddy") and \
                not watched and brain.t("aggression", 0.5) > 0.35 and math.dist(threat.pos, p.pos) < 50.0:
            mind["watching"] = threat.pid
            self._tail(brain, threat, 14.0, "watch")
            self.doing(brain, "keeping an eye on %s" % threat.username)
            self.callout(brain, ["im watching you %s" % threat.username, "%s is sus" % threat.username,
                                 "why is %s following people" % threat.username], "watch%d" % threat.pid,
                         chance=0.3, every=60.0)
            return
        mind.pop("watching", None)
        # in the mood for clues, or for a look round (each guest its own way)
        if moment >= mind.get("mood_until", 0.0):
            keen = {"sleuth": 0.85, "collector": 0.7, "buddy": 0.3, "wallflower": 0.25,
                    "wanderer": 0.35}.get(style, 0.6)
            mind["mood"] = "clues" if brain.rng.random() < keen else "roam"
            mind["mood_until"] = moment + brain.rng.uniform(15.0, 35.0)
        reach = {"sleuth": 240.0, "collector": 150.0}.get(style, 60.0) if mind["mood"] == "clues" else 16.0
        clue = self._pick_clue(brain, mind, reach, avoid=threat.pos if threat is not None else None)
        if clue is not None:
            self._go(brain, clue["p"], "clue%d" % clue["id"])
            self.doing(brain, "picking up a clue%s" % (
                " near " + self._place(clue["p"]) if self._place(clue["p"]) else ""))
            return
        # safety in numbers: a buddy sticks with somebody, and anybody may
        # once there is a body
        if style == "buddy" or (self.bodies and style != "wallflower" and brain.t("social", 0.5) > 0.5):
            friend = self._buddy(brain, mind, moment)
            if friend is not None:
                self._keep_with(brain, mind, friend, moment)
                self.doing(brain, "keeping with %s" % friend.username)
                if self.bodies:
                    self.callout(brain, ["stick together", "stay with me", "dont go off alone",
                                         "wait for me " + friend.username], "crowd",
                                 chance=0.2, every=90.0)
                return
        state, where = self._roam(brain, mind)
        if state == "here":
            self.doing(brain, "hanging about %s" % where if where else "looking round the place")
        else:
            self.doing(brain, "heading to %s" % where if where else "looking round the place")

    def _flee(self, brain, danger: Sequence[float], why: str) -> None:
        """Away from ``danger`` -- never past it -- to somewhere the others are
        not all running too."""
        p = brain.p
        mind = self._mind(p)
        moment = engine.now()
        held = mind.get("flee_to")
        if held is not None and moment < held[1] and math.dist(held[0], danger) > 25.0 and \
                math.dist(held[0], p.pos) > 3.0:
            self._go(brain, held[0], "flee")
            self.doing(brain, "running %s" % why)
            return
        options = self.marks.get("roam") or [{"p": pt} for pt, _ in self.landmarks]
        others = [o for o in self.playing() if o is not p]
        runs = [self._mind(o).get("flee_to") for o in others if o.brain is not None]
        away = [p.pos[0] - danger[0], p.pos[2] - danger[2]]
        away_len = math.hypot(away[0], away[1]) or 1e-6
        best, best_s = None, -1e9
        for m in options:
            q = m["p"]
            if not self._reachable(q):
                continue
            # far enough is far enough: a long way off is a long way to run
            s = min(math.dist(q, danger), 70.0) - math.dist(q, p.pos) * 0.5
            to = [q[0] - p.pos[0], q[2] - p.pos[2]]
            to_len = math.hypot(to[0], to[1]) or 1e-6
            if (to[0] * away[0] + to[1] * away[1]) / (to_len * away_len) < -0.3 and \
                    math.dist(q, danger) < to_len + 10.0:
                s -= 40.0                   # that way is past whoever it is
            s -= 16.0 * sum(1 for r in runs if r is not None and math.dist(r[0], q) < 10.0)
            for other in others:
                if self.is_murderer(p):
                    # a murderer runs from the gun it knows of, not towards one
                    if self._known_armed(p, other):
                        s -= max(0.0, 40.0 - math.dist(other.pos, q)) * 0.8
                elif self.armed(other):
                    s += max(0.0, 30.0 - math.dist(other.pos, q)) * 0.8
            s += brain.rng.uniform(0.0, 12.0)
            if s > best_s:
                best, best_s = q, s
        if best is not None:
            to = self._offset(best, p, brain.rng.uniform(1.0, 3.5))
            mind["flee_to"] = (to, moment + 5.0)
            mind.pop("spot", None)
            self._go(brain, to, "flee")
        self.doing(brain, "running %s" % why)

    # ---- the detective (and the hero)
    def _bot_detective(self, brain) -> None:
        p = brain.p
        moment = engine.now()
        mind = self._mind(p)
        mind["style"] = "detective"
        trigger = self.pct("trigger")
        need = 0.85 - trigger * 0.45
        target, sure = self.prime_suspect(p)
        if target is not None and sure >= need:
            d = math.dist(target.pos, p.pos)
            if self._sees(p, target) and d < 60.0:
                blocked = self._in_the_way(p, target)
                if blocked or (d > 14.0 and brain.rng.random() < 0.3):
                    # somebody is in the line of fire: get round them
                    self._go(brain, target.pos, "chase")
                else:
                    brain.waypoints = []
                if moment >= p.reload_until and not blocked:
                    self._bot_fire(brain, target)
                self.callout(brain, ["dont move %s" % target.username, "its you", "i know it was you",
                                     "hands where i can see them"], "aim%d" % target.pid,
                             chance=0.35, every=60.0)
                self.doing(brain, "taking aim at %s" % target.username)
                return
            self._go(brain, target.pos, "chase")
            self.doing(brain, "after %s" % target.username)
            return
        if target is not None and sure >= 0.35 and math.dist(target.pos, p.pos) < 70.0:
            # not sure enough to shoot: shadow them, and wait for them to slip
            self._tail(brain, target, 16.0, "shadow")
            self.doing(brain, "shadowing %s" % target.username)
            return
        lead = mind.get("lead")
        if lead is not None and moment - lead[1] < 25.0 and self._reachable(lead[0]):
            if math.dist(lead[0], p.pos) > 6.0:
                self._go(brain, lead[0], "lead")
                self.doing(brain, "checking %s" % (self._place(lead[0]) or "a lead"))
                return
            mind.pop("lead", None)
        # the scene of the crime: a look at the body, then the rooms round it
        if self.bodies:
            body = self.bodies[-1]
            if moment - body["at"] < 14.0 and math.dist(body["p"], p.pos) < 120.0 and \
                    mind.get("examined") != body["id"]:
                spot = self._offset(body["p"], p, 3.5)
                if not self._reachable(spot):
                    mind["examined"] = body["id"]       # nowhere to stand by it
                elif math.hypot(spot[0] - p.pos[0], spot[2] - p.pos[2]) > 2.5:
                    self._go(brain, spot, "body%d" % body["id"])
                    self.doing(brain, "going to the body")
                    return
                else:
                    until = mind.setdefault("examine_until", moment + brain.rng.uniform(2.0, 4.0))
                    if moment < until:
                        brain.waypoints = []
                        brain.look_yaw = math.atan2(body["p"][0] - p.pos[0], body["p"][2] - p.pos[2])
                        self.doing(brain, "examining the body")
                        return
                    mind.pop("examine_until", None)
                    mind["examined"] = body["id"]
                    near = sorted((m["p"] for m in self.marks.get("roam") or ()
                                   if 10.0 < math.dist(m["p"], body["p"]) < 60.0 and self._reachable(m["p"])),
                                  key=lambda q: math.dist(q, body["p"]))
                    mind["sweep"] = [list(q) for q in near[:3]]
                    brain.rng.shuffle(mind["sweep"])
        sweep = mind.get("sweep")
        if sweep:
            q = sweep[0]
            if math.hypot(q[0] - p.pos[0], q[2] - p.pos[2]) > 4.0:
                self._go(brain, q, "sweep%d" % int(q[0] * 3 + q[2]))
                self.doing(brain, "searching %s" % (self._place(q) or "round the body"))
                return
            sweep.pop(0)
        clue = self._pick_clue(brain, mind, 40.0)
        if clue is not None:
            self._go(brain, clue["p"], "clue%d" % clue["id"])
            self.doing(brain, "picking up a clue")
            return
        state, where = self._roam(brain, mind, "patrol")
        self.doing(brain, ("watching %s" % where if state == "here" else "on patrol to %s" % where)
                   if where else "on patrol")

    def _in_the_way(self, p: Player, target: Player, margin: float = 2.6) -> Optional[Player]:
        """Somebody standing between ``p`` and ``target``, near enough the line
        that a shot (or a thrown knife) could find them instead."""
        a = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        b = [target.pos[0], target.pos[1] + 2.8, target.pos[2]]
        ab = [b[i] - a[i] for i in range(3)]
        length = math.sqrt(sum(v * v for v in ab)) or 1e-6
        for other in self.playing():
            if other is p or other is target:
                continue
            c = [other.pos[0], other.pos[1] + 2.8, other.pos[2]]
            t = sum((c[i] - a[i]) * ab[i] for i in range(3)) / (length * length)
            if t <= 0.0 or t >= 1.0:
                continue
            closest = [a[i] + ab[i] * t for i in range(3)]
            if math.dist(closest, c) < margin:
                return other
        return None

    def _bot_fire(self, brain, target: Player) -> None:
        p = brain.p
        aim = [target.pos[0], target.pos[1] + 2.8, target.pos[2]]
        direction = self._face(brain, aim)
        # a steady hand, by skill
        wobble = (1.0 - brain.skill) * 0.06 + 0.012
        direction = normalise([direction[0] + brain.rng.gauss(0, wobble),
                               direction[1] + brain.rng.gauss(0, wobble * 0.6),
                               direction[2] + brain.rng.gauss(0, wobble)])
        if p.stowed or p.slot != 0:
            self.handle_slot(p, {"i": 0})
        origin = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        self.shoot(p, direction, origin)

    # ---- the murderer
    def _bot_murderer(self, brain) -> None:
        p = brain.p
        moment = engine.now()
        mind = self._mind(p)
        stealth = self.pct("stealth")
        # hunted: shot at lately, or a known gun close by and looking this way
        shot_at = mind.get("shot_at")
        sleuth = next((o for o in self.playing() if o is not p and self._known_armed(p, o) and
                       self._sees(o, p, 40.0) and self._looking_at(o, p)), None)
        hunted = sleuth is not None or (shot_at is not None and moment - shot_at[1] < 10.0)
        victim = self.players.get(mind.get("victim", 0))
        # named in front of everybody: deny it (a murderer who says nothing
        # looks guilty)
        accused = sum(1 for o in self.playing()
                      if o.brain is not None and o is not p and self.suspicion(o, p) >= 0.6)
        if accused >= 2:
            self.callout(brain, ["not me", "it wasnt me", "why me??", "theyre lying",
                                 "i was with you the whole time"], "notme", chance=0.6, every=45.0)
        if victim is not None and (not self.in_play(victim) or moment > mind.get("victim_until", 0)):
            victim = None
            mind.pop("victim", None)
        if victim is None and moment >= mind.get("next_hunt", 0.0):
            victim = self._pick_victim(brain, hunted)
            if victim is not None:
                mind["victim"] = victim.pid
                mind["victim_until"] = moment + 25.0
                # whether this one is worth doing with somebody watching is
                # decided once, when the victim is picked -- not every think
                # (and bolder the longer the night goes on: the murderer has
                # to leave nobody standing before the clock runs out)
                late = max(0.0, min(1.0, (moment - self.live_at) / max(1.0, self.ROUND_SECONDS)))
                mind["bold"] = brain.rng.random() < \
                    brain.t("aggression", 0.5) * (1.2 - stealth) * 0.35 + late * 0.55
            mind["next_hunt"] = moment + brain.rng.uniform(3.0, 9.0) * (0.5 + stealth)
        if victim is not None:
            d = math.dist(victim.pos, p.pos)
            onlookers = self._onlookers(p, victim)
            # the party's first minutes nobody strikes in front of anybody; a
            # bold murderer goes ahead with a witness or two about after
            # that, and with the clock running out anybody does
            calm = moment < self.live_at + 15.0 + 25.0 * stealth
            desperate = self.round_ends - moment < 25.0
            if onlookers and (calm or not mind.get("bold")) and not hunted and not desperate:
                # people about: hang back, the knife away, and wait for the
                # victim to wander off on its own
                self._stow(p)
                self._tail(brain, victim, 9.0 + 5.0 * stealth, "stalk")
                self.doing(brain, "keeping close to %s" % victim.username)
                return
            if d < KNIFE_REACH - 0.6:
                self._draw(p)
                direction = self._face(brain, [victim.pos[0], victim.pos[1] + 2.6, victim.pos[2]])
                brain.waypoints = []
                if self.stab(p, direction):
                    mind.pop("victim", None)
                    mind["next_hunt"] = moment + brain.rng.uniform(4.0, 10.0) * (0.6 + stealth)
                    mind["fled_from"] = list(p.pos)
                    self._stow_later(p)
                return
            if 12.0 < d < 42.0 and moment >= p.extra.get("wd_throw_at", 0.0) and \
                    brain.rng.random() < self.pct("throw") * 0.08 * (0.4 + brain.skill) and \
                    self._sees(p, victim, 45.0) and not self._in_the_way(p, victim):
                self._draw(p)
                aim = [victim.pos[0] + victim.vel[0] * d / THROW_SPEED,
                       victim.pos[1] + 2.6 + THROW_GRAVITY * (d / THROW_SPEED) ** 2 * 0.5,
                       victim.pos[2] + victim.vel[2] * d / THROW_SPEED]
                direction = self._face(brain, aim)
                self.throw(p, direction)
                return
            # the knife comes out only for the last step, and only with
            # nobody to see it
            if d < KNIFE_REACH + 3.0 and not onlookers:
                self._draw(p)
            else:
                self._stow(p)
            self._go(brain, victim.pos, "hunt%d" % victim.pid)
            self.doing(brain, "following %s" % victim.username)
            return
        self._stow(p)
        if hunted:
            self._flee(brain, sleuth.pos if sleuth is not None else shot_at[0],
                       "from the detective" if sleuth is not None else "from the gunfire")
            return
        # blend in: pick clues up (and burn them), drift round the rooms the
        # way a guest does
        mind["style"] = "murderer"
        if moment >= mind.get("mood_until", 0.0):
            mind["mood"] = "clues" if brain.rng.random() < 0.55 else "roam"
            mind["mood_until"] = moment + brain.rng.uniform(10.0, 25.0)
        clue = self._pick_clue(brain, mind, 120.0 if mind["mood"] == "clues" else 18.0)
        if clue is not None:
            self._go(brain, clue["p"], "clue%d" % clue["id"])
            self.doing(brain, "picking up a clue")
            return
        state, where = self._roam(brain, mind)
        self.doing(brain, "mingling%s" % (" in " + where if where and state == "here" else ""))

    def _pick_victim(self, brain, hunted: bool) -> Optional[Player]:
        p = brain.p
        best, best_s = None, -1e9
        near = sorted((math.dist(other.pos, p.pos), other.pid, other) for other in self.playing()
                      if other is not p and not self.is_murderer(other))
        for rank, (d, _pid, other) in enumerate(near):
            if d > 140.0:
                break
            # only the nearest few are worth looking round for witnesses
            alone = 1.0 if rank < 6 and self._alone(other, p) else 0.0
            s = -d + alone * 60.0 * (0.5 + self.pct("stealth"))
            if self._known_armed(p, other):
                # the revolver is the one thing that can stop a murderer: take
                # it out of the game while it is not pointed this way (or when
                # it is coming for us anyway); otherwise keep clear of it
                watching = self._looking_at(other, p) and self._sees(other, p, 50.0)
                s += 40.0 if hunted else (35.0 if alone and not watching else -30.0)
            s += brain.rng.uniform(0.0, 20.0)
            if s > best_s:
                best, best_s = other, s
        return best

    def _alone(self, victim: Player, murderer: Player, reach: float = 40.0) -> bool:
        """Nobody but the murderer within sight of ``victim`` (on its floor,
        in the room with it): somebody to follow."""
        for other in self.playing():
            if other is murderer or other is victim or self.is_murderer(other):
                continue
            if abs(other.pos[1] - victim.pos[1]) < 8.0 and \
                    math.dist(other.pos, victim.pos) < reach and self._sees(other, victim, reach):
                return False
        return True

    def _onlookers(self, murderer: Player, victim: Player) -> List[Player]:
        """Who would see it done: anybody with an eye on the murderer from
        about as far as a witness could tell who it was."""
        out = []
        reach = min(58.0, self.sight())
        for other in self.playing():
            if other is murderer or other is victim or self.is_murderer(other):
                continue
            if math.dist(other.pos, murderer.pos) < reach and self._sees(other, murderer, reach):
                out.append(other)
        return out

    def _draw(self, p: Player) -> None:
        if p.stowed or p.slot != 0:
            self.handle_slot(p, {"i": 0})

    def _stow(self, p: Player) -> None:
        if not p.stowed:
            self.handle_slot(p, {"i": STOW_SLOT})

    def _stow_later(self, p: Player) -> None:
        p.extra.setdefault("wd_mind", {"sus": {}})["stow_at"] = engine.now() + 0.8

    def bot_context(self) -> List[str]:
        lines = ["You are playing Whodunit, a murder mystery: one guest is secretly the murderer, "
                 "one the detective; innocents pick up clues and try to survive."]
        lines.append("Case file: %d clues, hints so far: %s." % (self.case, ", ".join(self.hints) or "none"))
        return lines

    def bot_me(self, brain) -> Dict[str, Any]:
        p = brain.p
        target, sure = self.prime_suspect(p)
        return {"role": self.role(p), "suspect": target.username if target and sure > 0.5 else "",
                "doing": p.extra.get("bot_doing", "")}

    def bot_spread(self, players: List[Player]) -> None:
        """The roles are dealt by the rules, not the bots."""

    def observe(self) -> Dict[str, Any]:
        return {"roles": dict(self.roles), "case": self.case}

    def selftest(self, result: Dict[str, Any]) -> List[Tuple[str, bool, Any]]:
        c = self.counts
        return [
            ("murders happen", c["murders"] >= 2, dict(c)),
            ("murderers get caught", c["caught"] >= 1, c["caught"]),
            ("clues fill the case file", c["clues"] >= 6, c["clues"]),
            ("the case file gives hints", c["hints"] >= 1, c["hints"]),
        ]


WORLD_CLASS = WhodunitWorld
