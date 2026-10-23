"""Calamity Coast: survive the disaster (app/models/event_worlds/calamity_coast.py).

Two teams of rescuers -- the **Lifeguards** and the **Rangers** -- in a
town about to have a very bad day.  A round is three disasters, one after
another; each one is announced in a short calm, the siren sounds, and then
it hits for most of a minute.  Everybody still standing when it passes
scores for their team, and the team with the most points over the three
wins the round.  Nobody can hurt anybody: the town does all the hurting.

**Between disasters** (the calm) the next one is named, so there is time to
think: supply crates turn up (a life ring, a hard hat, a raincoat or a pair
of running shoes), and townsfolk are stranded in the worst places.  Hold E
by one to pick them up and carry them to the evacuation point for points of
your own -- slower, and in the open, but worth it.  The fallen come back at
the next calm.

**The disasters** are written into each area (``extra["disasters"]``), each
a few *parts* from the same small kit, so a tsunami in one town and a lava
flood in another are one piece of code:

``level``      water (or lava) rising to a height and going down again;
               below it you drown (a life ring floats you).
``strikes``    things falling out of the sky on warning circles: meteors,
               lightning, lava bombs, hail, debris, coconuts.  They land
               on the first thing they hit, so a roof is cover.
``wind``       gusts that push anyone in the open and not in the lee of
               something.
``tornado``    a funnel walking a path through the town: it drags you in,
               lifts you and drops you.
``cold``       a cold meter that fills in the open and empties by a fire or
               indoors; full, it hurts.
``rain``       hail or acid that hurts anyone not under a roof.
``quake``      the ground shakes and parts of the town give way (switchable
               solids switched off), with debris (a strikes part).
``front``      an avalanche or a rockslide coming down a lane; anything in
               its way and not behind something is swept off.
``fire``       a blaze that spreads from house to house.
``sinkholes``  patches of ground that crack and drop.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import instance as engine
from ..instance import MAX_HEALTH, Player
from ..maps.events import calamity_coast as cc_map
from .arena import NEVER, ArenaWorld

CALM_SECONDS = 16.0
WARN_SECONDS = 7.0
DISASTERS = 3
SURVIVE_POINTS = 10
RESCUE_POINTS = 15
CRATE_POINTS = 2
CARRY_SCALE = 0.82
PICKUP_REACH = 5.5
CRATE_REACH = 3.2
CRATES = 3
STRANDED = 2
SHOES_SECONDS = 25.0
SHOES_SCALE = 1.25
COVER_UP = 60.0            # a roof is anything solid this far over your head
LEE = 7.0                  # something upwind this close keeps the wind off
PUSH_EVERY = 0.4
POWERS = ("ring", "hat", "coat", "shoes")
POWER_NAMES = {"ring": "a life ring", "hat": "a hard hat", "coat": "a raincoat",
               "shoes": "running shoes"}
# which disasters a power-up is good for (crates lean towards the next one)
POWER_FOR = {"level": "ring", "strikes": "hat", "quake": "hat", "rain": "coat",
             "cold": "coat", "front": "shoes", "fire": "shoes", "wind": "shoes",
             "tornado": "shoes", "sinkholes": "shoes"}
# what a bot shouts when it knows where it is going for the next disaster
PLAN_LINES = {"high": ["high ground!", "get up high", "climb!", "up the hill", "find a roof"],
              "shelter": ["get inside", "inside now", "find a roof", "take cover"],
              "open": ["out of the buildings", "open ground", "away from the walls",
                       "get outside"],
              "heat": ["find a fire", "stay warm", "by the fire"]}
# badge stats booked for surviving a disaster with a part of these kinds
SURVIVED_STAT = {"level": "cc_floods", "wind": "cc_storms", "tornado": "cc_storms",
                 "cold": "cc_cold", "front": "cc_cold", "quake": "cc_quakes",
                 "sinkholes": "cc_quakes", "fire": "cc_fires", "strikes": "",
                 "rain": ""}
DEFAULTS: Dict[str, Any] = {}


def _defaults() -> Dict[str, Any]:
    if not DEFAULTS:
        from ...models.event_worlds import calamity_coast as meta
        for spec in meta.BOT_FIELDS:
            DEFAULTS[spec[0]] = spec[3]
    return DEFAULTS


def _smooth(f: float) -> float:
    f = max(0.0, min(1.0, f))
    return f * f * (3.0 - 2.0 * f)


class Path:
    """A polyline on the ground (x, z), walked by distance."""

    def __init__(self, points: Sequence[Sequence[float]]):
        self.points = [(float(p[0]), float(p[-1])) for p in points]
        self.cum = [0.0]
        for a, b in zip(self.points, self.points[1:]):
            self.cum.append(self.cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.length = self.cum[-1] or 1.0

    def at(self, d: float) -> Tuple[float, float, float, float]:
        """(x, z, dx, dz) at distance ``d``: the point and the way along."""
        d = max(0.0, min(self.length, d))
        for i in range(len(self.points) - 1):
            if d <= self.cum[i + 1] or i == len(self.points) - 2:
                a, b = self.points[i], self.points[i + 1]
                seg = (self.cum[i + 1] - self.cum[i]) or 1.0
                f = (d - self.cum[i]) / seg
                ux, uz = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
                return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, ux, uz
        x, z = self.points[0]
        return x, z, 1.0, 0.0

    def project(self, x: float, z: float) -> Tuple[float, float]:
        """(distance along, distance off) of the nearest point to (x, z)."""
        best = (0.0, 1e9)
        for i, (a, b) in enumerate(zip(self.points, self.points[1:])):
            vx, vz = b[0] - a[0], b[1] - a[1]
            seg2 = vx * vx + vz * vz or 1.0
            f = max(0.0, min(1.0, ((x - a[0]) * vx + (z - a[1]) * vz) / seg2))
            px, pz = a[0] + vx * f, a[1] + vz * f
            off = math.hypot(x - px, z - pz)
            if off < best[1]:
                best = (self.cum[i] + f * math.sqrt(seg2), off)
        return best


class CalamityCoastWorld(ArenaWorld):
    MAP = cc_map
    TEAMS = ("red", "blue")
    TEAM_NAMES = {"red": "Lifeguards", "blue": "Rangers"}
    ROUNDS_PER_AREA = 2
    SETUP_SECONDS = 10.0
    ROUND_SECONDS = 0.0            # three disasters, however long they take
    RESULTS_SECONDS = 15.0
    ELIMINATION = True             # the fallen watch until the next calm
    LOGO = "Calamity Coast"
    respawn_seconds = 6.0
    BOT_CHATTER = ["high ground", "get inside", "run", "here it comes", "help", "gg",
                   "close one", "anyone hurt", "evac", "crate", "ok we survived"]

    # ------------------------------------------------------------ settings
    def setting(self, key: str) -> Any:
        cfg = getattr(self.bots, "cfg", None) if self.bots is not None else None
        value = (cfg or {}).get("calamity_coast_" + key)
        return _defaults().get(key) if value is None else value

    def pct(self, key: str) -> float:
        try:
            return max(0.0, min(1.0, float(self.setting(key)) / 100.0))
        except (TypeError, ValueError):
            return 0.5

    # ================================================================ setup
    def world_setup(self) -> None:
        self.specs: List[Dict[str, Any]] = []
        self.order: List[int] = []
        self.stage = "calm"
        self.stage_until = 0.0
        self.stage_started = 0.0
        self.index = -1
        self.current: Optional[Dict[str, Any]] = None
        self.parts: List[Dict[str, Any]] = []
        self.points: Dict[str, int] = {"red": 0, "blue": 0}
        self.strandees: Dict[int, Dict[str, Any]] = {}
        self.crates: Dict[int, Dict[str, Any]] = {}
        self.strikes: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1
        self.round_stats: Dict[int, Dict[str, float]] = {}
        self.counts: Dict[str, int] = {"disasters": 0, "survived": 0, "rescued": 0,
                                       "lost": 0, "crates": 0, "strikes": 0, "pushed": 0,
                                       "deaths": 0, "collapsed": 0, "cold": 0, "fires": 0}
        self.events_said: Dict[str, float] = {}
        self.marks: Dict[str, List[Dict[str, Any]]] = {}
        self.landmarks: List[Tuple[List[float], str]] = []

    def round_setup(self) -> None:
        area = self.area
        extra = area.get("extra") or {}
        self.marks = {k: list(v) for k, v in (area.get("points") or {}).items()}
        self.landmarks = [(list(m["p"]), m["name"]) for m in area.get("landmarks") or []]
        self.specs = [dict(d) for d in extra.get("disasters") or []]
        if len(self.specs) < DISASTERS:
            raise ValueError("Calamity Coast area %s has too few disasters" % self.area_id)
        # three of the area's disasters, never the same one twice in a row
        # across the area's two rounds; the third is the big one
        last = getattr(self, "_last_spec", None)
        order = list(range(len(self.specs)))
        self.rng.shuffle(order)
        if last is not None and order[0] == last:
            order.append(order.pop(0))
        self.order = order[:DISASTERS]
        self._last_spec = self.order[-1]
        self.index = -1
        self.current = None
        self.parts = []
        self.stage = "calm"
        self.stage_until = NEVER
        self.points = {"red": 0, "blue": 0}
        self.strandees = {}
        self.crates = {}
        self.strikes = {}
        self.round_stats = {}
        self.events_said = {}
        self.cover_cache: Dict[int, Tuple[float, bool]] = {}
        for player in self.players.values():
            self.reset_player(player)
        # whatever the last round knocked down stands again
        for key, d in (area.get("dynamic") or {}).items():
            self.set_dynamic(key, bool(d.get("on", True)))

    def reset_player(self, player: Player) -> None:
        for key in ("cc_pw", "cc_carry", "cc_cold", "cc_shoes", "cc_mind", "cc_hurt"):
            player.extra.pop(key, None)

    def rival(self, team: str) -> str:
        return "blue" if team == "red" else "red"

    # ============================================================ spawning
    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        spawns = self.area.get("spawns") or {}
        return list(spawns.get(team) or spawns.get("start") or []) or super().spawn_points(team)

    def on_spawned(self, player: Player) -> None:
        player.extra.pop("cc_carry", None)
        player.extra["cc_cold"] = 0.0

    def welcome_lines(self, player: Player) -> List[str]:
        lines = super().welcome_lines(player)
        lines.append("Survive the disasters: when the siren sounds, get somewhere safe. "
                     "Everyone still standing scores for their team.")
        lines.append("Hold E by a stranded townsperson to carry them to the evacuation "
                     "point. Walk over a supply crate to open it.")
        return lines

    # ============================================================ movement
    def move_scale(self, player: Player) -> float:
        scale = 1.0
        if player.extra.get("cc_carry"):
            scale *= CARRY_SCALE
        if player.extra.get("cc_shoes", 0.0) > engine.now():
            scale *= SHOES_SCALE
        return scale

    def can_fire(self, player: Player) -> bool:
        return False

    def can_hurt(self, attacker: Player, victim: Player) -> bool:
        return False

    # ============================================================== rounds
    def on_live(self) -> None:
        self._calm(engine.now())

    def round_tick(self, dt: float, moment: float) -> None:
        playing = self.playing()
        self._pickups(playing, moment)
        if self.stage == "calm":
            if moment >= self.stage_until - WARN_SECONDS and not self.stage_warned:
                self.stage_warned = True
                spec = self.current or {}
                self.broadcast({"t": "ccx", "k": "siren", "id": spec.get("id", ""),
                                "name": spec.get("name", ""), "in": WARN_SECONDS})
                self._event("cc_siren", None, "", what=spec.get("name", "the disaster"))
            if moment >= self.stage_until:
                self._strike_up(moment)
        elif self.stage == "active":
            t = moment - self.stage_started
            for part in self.parts:
                handler = getattr(self, "_tick_" + part["kind"], None)
                if handler is not None:
                    handler(part, playing, dt, t, moment)
            self._land_strikes(playing, moment)
            if moment >= self.stage_until:
                self._passed(moment)
        self._carry_tick(playing, moment)

    def _calm(self, moment: float) -> None:
        """The calm before the next one: crates, the stranded, the fallen back."""
        self.index += 1
        if self.index >= len(self.order):
            return
        self.current = dict(self.specs[self.order[self.index]])
        self.current["big"] = self.index == DISASTERS - 1
        self.stage = "calm"
        self.stage_started = moment
        self.stage_until = moment + CALM_SECONDS
        self.stage_warned = False
        self.parts = []
        self.strikes = {}
        # what the last one knocked down is back, and so are the fallen
        if self.index > 0:
            for key, d in (self.area.get("dynamic") or {}).items():
                self.set_dynamic(key, bool(d.get("on", True)))
            for player in list(self.players.values()):
                if player.extra.get("out") and player.team in self.TEAMS:
                    self.respawn_for_round(player)
        for player in self.players.values():
            player.extra["cc_cold"] = 0.0
        self._drop_crates()
        self._strand()
        spec = self.current
        self.broadcast({"t": "ccx", "k": "next", "id": spec.get("id", ""),
                        "name": spec.get("name", ""), "line": spec.get("line", ""),
                        "n": self.index + 1, "of": DISASTERS, "in": CALM_SECONDS,
                        "big": spec["big"]})
        self.system_message("Disaster %d of %d: %s in %d seconds. %s" % (
            self.index + 1, DISASTERS, spec.get("name", "?"), int(CALM_SECONDS),
            spec.get("line", "")))
        self._broadcast_state()

    def _strike_up(self, moment: float) -> None:
        """The disaster hits."""
        spec = self.current or {}
        scale = 1.25 if spec.get("big") else 1.0
        self.stage = "active"
        self.stage_started = moment
        seconds = float(spec.get("seconds", 45.0)) * (1.1 if spec.get("big") else 1.0)
        self.stage_until = moment + seconds
        self.parts = []
        for raw in spec.get("parts") or []:
            part = dict(raw)
            part["scale"] = scale
            part["seconds"] = seconds
            part["state"] = {}
            self.parts.append(part)
        self.counts["disasters"] += 1
        self.in_disaster = {p.pid for p in self.playing()}
        self.unhurt = {p.pid for p in self.playing()}
        self.broadcast({"t": "ccx", "k": "hit", "id": spec.get("id", ""),
                        "name": spec.get("name", ""), "for": round(seconds, 1),
                        "big": bool(spec.get("big"))})
        self._event("cc_hit", None, "", what=spec.get("name", "the disaster"))
        self._broadcast_state()

    def _passed(self, moment: float) -> None:
        """It is over: everybody standing scores, and the next calm begins."""
        spec = self.current or {}
        kinds = {p["kind"] for p in self.parts}
        standing = [p for p in self.playing() if p.pid in self.in_disaster]
        for player in standing:
            self.points[player.team] = self.points.get(player.team, 0) + SURVIVE_POINTS
            player.score += SURVIVE_POINTS
            self._stat(player, "survived")
            self.badge(player, "cc_survived")
            for kind in kinds:
                stat = SURVIVED_STAT.get(kind)
                if stat:
                    self.badge(player, stat)
            if player.pid in self.unhurt and player.health >= MAX_HEALTH - 0.5:
                self.badge(player, "cc_unscathed")
                self._stat(player, "unscathed")
        self.counts["survived"] += len(standing)
        alive_all = [p for p in self.playing()]
        if len(alive_all) == 1 and len(self.in_disaster) >= 4:
            self.badge(alive_all[0], "cc_last_one")
            self.system_message("%s is the only one left standing!" % alive_all[0].username)
        # the stranded left out there are taken off by the coastguard
        for s in self.strandees.values():
            if s["state"] == "wait":
                s["state"] = "gone"
        self.broadcast({"t": "ccx", "k": "passed", "id": spec.get("id", ""),
                        "name": spec.get("name", ""),
                        "standing": {t: sum(1 for p in standing if p.team == t)
                                     for t in self.TEAMS},
                        "points": dict(self.points)})
        self._event("cc_passed", None, "", what=spec.get("name", "it"),
                    red=sum(1 for p in standing if p.team == "red"),
                    blue=sum(1 for p in standing if p.team == "blue"))
        self.parts = []
        self.strikes = {}
        if self.index >= DISASTERS - 1:
            self._finish()
            return
        self._calm(moment)

    def _finish(self) -> None:
        red, blue = self.points.get("red", 0), self.points.get("blue", 0)
        if red == blue:
            rr = sum(1 for s in self.strandees.values() if s["state"] == "safe" and s.get("team") == "red")
            rb = sum(1 for s in self.strandees.values() if s["state"] == "safe" and s.get("team") == "blue")
            winner = "" if rr == rb else ("red" if rr > rb else "blue")
        else:
            winner = "red" if red > blue else "blue"
        self.finish_round(winner, "survived")

    def time_up(self) -> None:
        self._finish()

    def leader(self) -> str:
        red, blue = self.points.get("red", 0), self.points.get("blue", 0)
        return "" if red == blue else ("red" if red > blue else "blue")

    def headline(self, winner: str, reason: str) -> str:
        if not winner:
            return "dead level -- the town owes you all a drink"
        return "%s ride out the storm, %d points to %d" % (
            self.team_name(winner), self.points.get(winner, 0),
            self.points.get(self.rival(winner), 0))

    def after_kill(self, killer: Optional[Player], victim: Player, weapon: str) -> None:
        self.counts["deaths"] += 1
        carried = victim.extra.pop("cc_carry", None)
        if carried and carried in self.strandees:
            s = self.strandees[carried]
            s["state"] = "wait"
            s["by"] = 0
            s["p"] = self._ground(victim.pos)
            self.broadcast({"t": "ccx", "k": "dropped", "id": carried, "p": s["p"]})
        if self.stage == "active":
            self._event("cc_down", victim, victim.team, what=weapon)

    # ======================================================== the hazards
    def _ground(self, pos: Sequence[float]) -> List[float]:
        top = [pos[0], pos[1] + 2.0, pos[2]]
        d = self.ray_world(top, [0.0, -1.0, 0.0], 80.0)
        return [round(pos[0], 2), round(top[1] - d, 2), round(pos[2], 2)]

    def covered(self, player: Player) -> bool:
        """Is there a roof over this player's head?"""
        moment = engine.now()
        hit = self.cover_cache.get(player.pid)
        if hit and moment - hit[0] < 0.3:
            return hit[1]
        head = [player.pos[0], player.pos[1] + 5.6, player.pos[2]]
        roof = self.ray_world(head, [0.0, 1.0, 0.0], COVER_UP) < COVER_UP - 0.01
        self.cover_cache[player.pid] = (moment, roof)
        return roof

    def _lee(self, player: Player, ux: float, uz: float) -> bool:
        """Is something solid between this player and the wind (ux, uz)?"""
        chest = [player.pos[0], player.pos[1] + 2.6, player.pos[2]]
        return self.ray_world(chest, [-ux, 0.0, -uz], LEE) < LEE - 0.01

    def _hurt(self, player: Player, amount: float, what: str) -> None:
        if amount <= 0 or not player.alive:
            return
        self.unhurt.discard(player.pid)
        self.apply_damage(player, None, amount, what)

    def _push(self, player: Player, vx: float, vy: float, vz: float) -> None:
        """Wind and water at work: a person gets a shove, a bot a drift."""
        if not player.alive:
            return
        moment = engine.now()
        player.extra["launch_until"] = moment + 1.2
        if player.brain is not None:
            player.extra["cc_push"] = (vx, vz, moment + PUSH_EVERY + 0.1)
            if vy > 4.0:
                player.brain.airborne = True
                player.brain.vy = max(player.brain.vy, vy)
            return
        player.send({"t": "knock", "v": [round(vx, 2), round(vy, 2), round(vz, 2)]})

    def bot_push(self, player: Player) -> Optional[Tuple[float, float]]:
        push = player.extra.get("cc_push")
        if not push or push[2] < engine.now():
            return None
        # a person's knock fades under their feet within a quarter second;
        # a steady drift at this share covers the same ground
        return push[0] * 0.6, push[1] * 0.6

    # ---- level: water or lava rising and falling
    def level_at(self, part: Dict[str, Any], t: float) -> float:
        lo, hi = float(part.get("from", 0.0)), float(part.get("to", 10.0))
        hi = lo + (hi - lo) * (1.0 + (part["scale"] - 1.0) * 0.5)
        rise, fall = float(part.get("rise", 20.0)), float(part.get("fall", 8.0))
        seconds = part["seconds"]
        if t < rise:
            return lo + (hi - lo) * _smooth(t / rise)
        if t > seconds - fall:
            return hi - (hi - lo) * _smooth((t - (seconds - fall)) / fall)
        return hi

    def _in_rect(self, part: Dict[str, Any], pos: Sequence[float]) -> bool:
        r = part.get("rect")
        if not r:
            return True
        ox, _, oz = self.area["centre"]
        x, z = pos[0] - ox, pos[2] - oz
        return r[0] <= x <= r[1] and r[2] <= z <= r[3]

    def _tick_level(self, part, playing, dt, t, moment) -> None:
        y = self.level_at(part, t)
        part["state"]["y"] = y
        medium = part.get("medium", "water")
        dps = float(part.get("dps", 30.0)) * part["scale"]
        for player in playing:
            if not self._in_rect(part, player.pos) or player.pos[1] + 1.4 >= y:
                continue
            if medium == "water" and "ring" in player.extra.get("cc_pw", ()):
                # a life ring floats you: up you come, to the surface
                if player.pos[1] + 1.4 < y - 0.5:
                    self._push(player, 0.0, 14.0, 0.0)
                continue
            self._hurt(player, dps * dt, "the lava" if medium == "lava" else "the water")
            if medium == "water" and part.get("flow"):
                fx, fz = part["flow"]
                if moment - player.extra.get("cc_swept", 0.0) > PUSH_EVERY:
                    player.extra["cc_swept"] = moment
                    self._push(player, fx * 10.0, 2.0, fz * 10.0)
        for s in self.strandees.values():
            if s["state"] == "wait" and s["p"][1] + 1.0 < y and self._in_rect(part, s["p"]):
                self._lose(s, "swept away" if medium == "water" else "lost to the lava")

    # ---- strikes: from the sky, on warning circles
    def _tick_strikes(self, part, playing, dt, t, moment) -> None:
        state = part["state"]
        lo, hi = part.get("every", [1.0, 2.0])
        if "next" not in state:
            state["next"] = moment + self.rng.uniform(0.5, 1.5)
        if moment < state["next"] or t > part["seconds"] - 2.0:
            return
        state["next"] = moment + self.rng.uniform(lo, hi) / part["scale"]
        target = self._strike_target(part, playing)
        if target is None:
            return
        r = float(part.get("r", 6.0))
        sid = self.next_id
        self.next_id += 1
        warn = float(part.get("warn", 1.6))
        self.strikes[sid] = {"id": sid, "p": target, "r": r, "at": moment + warn,
                             "what": part.get("what", "meteor"),
                             "damage": float(part.get("damage", 60.0)) * part["scale"]}
        self.counts["strikes"] += 1
        self.broadcast({"t": "ccx", "k": "warn", "id": sid, "p": target, "r": r,
                        "what": part.get("what", "meteor"), "in": warn})

    def _strike_target(self, part, playing) -> Optional[List[float]]:
        """Where the next one comes down: often on somebody in the open, else
        anywhere in the area -- and it lands on the first thing it hits."""
        ox, _, oz = self.area["centre"]
        aim = part.get("aim", "players")
        x = z = None
        if aim == "marks":
            spots = self.marks.get(part.get("marks", "debris"), [])
            if spots:
                m = self.rng.choice(spots)["p"]
                x, z = m[0] + self.rng.uniform(-4.0, 4.0), m[2] + self.rng.uniform(-4.0, 4.0)
        if x is None and aim != "anywhere" and playing and self.rng.random() < 0.65:
            pool = [p for p in playing if not part.get("open") or not self.covered(p)] or playing
            victim = self.rng.choice(pool)
            x = victim.pos[0] + self.rng.uniform(-5.0, 5.0)
            z = victim.pos[2] + self.rng.uniform(-5.0, 5.0)
        if x is None:
            hx, hz = self.area.get("half") or [150.0, 150.0]
            r = part.get("rect")
            if r:
                x, z = ox + self.rng.uniform(r[0], r[1]), oz + self.rng.uniform(r[2], r[3])
            else:
                x = ox + self.rng.uniform(-hx * 0.85, hx * 0.85)
                z = oz + self.rng.uniform(-hz * 0.85, hz * 0.85)
        sky = [x, 160.0, z]
        d = self.ray_world(sky, [0.0, -1.0, 0.0], 220.0)
        if d >= 219.0:
            return None
        return [round(x, 2), round(160.0 - d, 2), round(z, 2)]

    def _land_strikes(self, playing, moment) -> None:
        for sid, strike in list(self.strikes.items()):
            if moment < strike["at"]:
                continue
            self.strikes.pop(sid)
            p, r = strike["p"], strike["r"]
            self.broadcast({"t": "ccx", "k": "land", "id": sid, "p": p, "r": r,
                            "what": strike["what"]})
            for player in playing:
                d = math.hypot(player.pos[0] - p[0], player.pos[2] - p[2])
                if d > r or abs(player.pos[1] - p[1]) > 4.5:
                    continue
                pw = player.extra.setdefault("cc_pw", [])
                if "hat" in pw:
                    pw.remove("hat")
                    player.send({"t": "ccx", "k": "saved", "by": "hat"})
                    self._send_me(player, force=True)
                    if strike["what"] == "lightning":
                        self.badge(player, "cc_lightning")
                    continue
                hurt = strike["damage"] * (1.0 - 0.55 * d / r)
                self._hurt(player, hurt, {"meteor": "a meteor", "lightning": "lightning",
                                          "lava_bomb": "a lava bomb", "hail": "hail",
                                          "debris": "falling debris", "coconut": "a coconut",
                                          "boulder": "a boulder"}.get(strike["what"], "the sky"))
                if player.alive and d < r * 0.6:
                    ux, uz = (player.pos[0] - p[0]) / max(d, 0.5), (player.pos[2] - p[2]) / max(d, 0.5)
                    self._push(player, ux * 18.0, 9.0, uz * 18.0)
            for s in self.strandees.values():
                if s["state"] == "wait" and math.hypot(s["p"][0] - p[0], s["p"][2] - p[2]) < r * 0.7 \
                        and abs(s["p"][1] - p[1]) < 4.5:
                    self._lose(s, "hurt")

    # ---- wind: gusts from one quarter
    def _tick_wind(self, part, playing, dt, t, moment) -> None:
        state = part["state"]
        on, off = part.get("gust", [6.0, 4.0])
        if "until" not in state:
            state.update({"gust": False, "until": moment + 1.5})
        if moment >= state["until"]:
            state["gust"] = not state["gust"]
            state["until"] = moment + (on if state["gust"] else off) * self.rng.uniform(0.8, 1.2)
            if state["gust"]:
                self.broadcast({"t": "ccx", "k": "gust", "for": round(state["until"] - moment, 1),
                                "dir": part.get("dir", [1.0, 0.0])})
        if not state["gust"]:
            return
        ux, uz = part.get("dir", [1.0, 0.0])
        strength = float(part.get("strength", 16.0)) * part["scale"]
        for player in playing:
            if moment - player.extra.get("cc_gusted", 0.0) < PUSH_EVERY:
                continue
            if self.covered(player) or self._lee(player, ux, uz):
                continue
            player.extra["cc_gusted"] = moment
            self.counts["pushed"] += 1
            self._push(player, ux * strength, 3.0, uz * strength)

    # ---- tornado: a funnel walking a path
    def _tick_tornado(self, part, playing, dt, t, moment) -> None:
        state = part["state"]
        path = state.get("path")
        if path is None:
            ox, _, oz = self.area["centre"]
            path = state["path"] = Path([(x + ox, z + oz) for x, z in part.get("path", [[0, 0], [10, 0]])])
            state["d"] = 0.0
            state["dir"] = 1.0
        speed = float(part.get("speed", 9.0)) * part["scale"]
        state["d"] += state["dir"] * speed * dt
        if state["d"] >= path.length:
            state["d"], state["dir"] = path.length, -1.0
        elif state["d"] <= 0.0:
            state["d"], state["dir"] = 0.0, 1.0
        x, z, _, _ = path.at(state["d"])
        ground = self._ground([x, 80.0, z])
        state["p"] = [round(x, 2), ground[1], round(z, 2)]
        outer, core = float(part.get("r", 26.0)), float(part.get("core", 8.0))
        dps = float(part.get("dps", 22.0)) * part["scale"]
        for player in playing:
            dx, dz = player.pos[0] - x, player.pos[2] - z
            d = math.hypot(dx, dz)
            if d > outer or player.pos[1] > ground[1] + 60.0:
                continue
            if d < core:
                self._hurt(player, dps * dt, "the tornado")
            if moment - player.extra.get("cc_twisted", 0.0) < PUSH_EVERY:
                continue
            player.extra["cc_twisted"] = moment
            if self.covered(player) and d > core:
                continue
            ux, uz = dx / max(d, 0.5), dz / max(d, 0.5)
            pull = 9.0 * (1.0 - d / outer) + 3.0
            spin = 14.0 * (1.0 - d / outer) + 4.0
            lift = 22.0 if d < core else 0.0
            self.counts["pushed"] += 1
            self._push(player, -ux * pull - uz * spin, lift, -uz * pull + ux * spin)
        for s in self.strandees.values():
            if s["state"] == "wait" and math.hypot(s["p"][0] - x, s["p"][2] - z) < core:
                self._lose(s, "blown away")

    # ---- cold: a meter that fills in the open
    def _tick_cold(self, part, playing, dt, t, moment) -> None:
        heat = self.marks.get("heat", [])
        rate = float(part.get("rate", 0.05)) * part["scale"]
        dps = float(part.get("dps", 8.0))
        for player in playing:
            warm = self.covered(player) or any(
                math.dist(player.pos, h["p"]) < float(h.get("r", 9.0)) for h in heat)
            cold = float(player.extra.get("cc_cold", 0.0))
            if warm:
                cold = max(0.0, cold - 0.2 * dt)
            else:
                coat = "coat" in player.extra.get("cc_pw", ())
                cold = min(1.0, cold + rate * dt * (0.45 if coat else 1.0))
            player.extra["cc_cold"] = cold
            if cold >= 1.0:
                self._hurt(player, dps * dt, "the cold")
                self.counts["cold"] += 1

    # ---- rain: hail or acid on anyone in the open
    def _tick_rain(self, part, playing, dt, t, moment) -> None:
        dps = float(part.get("dps", 6.0)) * part["scale"]
        for player in playing:
            if self.covered(player):
                continue
            coat = "coat" in player.extra.get("cc_pw", ())
            self._hurt(player, dps * dt * (0.25 if coat else 1.0),
                       "acid rain" if part.get("what") == "acid" else "the hail")

    # ---- quake: shaking, and parts of the town giving way
    def _tick_quake(self, part, playing, dt, t, moment) -> None:
        state = part["state"]
        done = state.setdefault("done", set())
        for i, (at, group) in enumerate(part.get("collapse") or []):
            if i in done or t < float(at):
                continue
            done.add(i)
            self.set_dynamic_group(group, False)
            self.counts["collapsed"] += 1
            self.broadcast({"t": "ccx", "k": "collapse", "group": group,
                            "name": (part.get("names") or {}).get(group, "")})
        if not state.get("shaking"):
            state["shaking"] = True
            self.broadcast({"t": "ccx", "k": "shake", "for": round(part["seconds"], 1),
                            "power": float(part.get("power", 1.0)) * part["scale"]})

    # ---- front: an avalanche or a rockslide down a lane
    def _tick_front(self, part, playing, dt, t, moment) -> None:
        state = part["state"]
        lanes = state.get("lanes")
        if lanes is None:
            ox, _, oz = self.area["centre"]
            lanes = state["lanes"] = [
                (Path([(x + ox, z + oz) for x, z in lane["pts"]]), float(lane.get("w", 20.0)),
                 float(lane.get("delay", 0.0)))
                for lane in part.get("lanes") or []]
        speed = float(part.get("speed", 14.0)) * part["scale"]
        depth = float(part.get("depth", 14.0))
        dps = float(part.get("dps", 70.0)) * part["scale"]
        fronts = []
        for path, width, delay in lanes:
            s = (t - delay) * speed
            fronts.append(round(s, 1))
            if s <= 0.0 or s - depth > path.length:
                continue
            _, _, ux, uz = path.at(min(s, path.length))
            for player in playing:
                along, off = path.project(player.pos[0], player.pos[2])
                if off > width / 2.0 or not (s - depth <= along <= s):
                    continue
                if self._lee(player, ux, uz):
                    continue
                self._hurt(player, dps * dt, part.get("weapon", "the avalanche"))
                if moment - player.extra.get("cc_swept", 0.0) > PUSH_EVERY:
                    player.extra["cc_swept"] = moment
                    self._push(player, ux * 16.0, 4.0, uz * 16.0)
            for st in self.strandees.values():
                if st["state"] != "wait":
                    continue
                along, off = path.project(st["p"][0], st["p"][2])
                if off <= width / 2.0 and s - depth <= along <= s:
                    self._lose(st, "swept away")
        state["s"] = fronts

    # ---- fire: a blaze spreading from house to house
    def _tick_fire(self, part, playing, dt, t, moment) -> None:
        state = part["state"]
        cells = self.marks.get(part.get("marks", "fire"), [])
        if not cells:
            return
        burning = state.setdefault("burning", {})
        burnt = state.setdefault("burnt", set())
        if not burning and not burnt:
            for i in self.rng.sample(range(len(cells)), min(len(cells), int(part.get("start", 2)))):
                burning[i] = moment
        spread, burn = float(part.get("spread", 7.0)) / part["scale"], float(part.get("burn", 26.0))
        reach = float(part.get("reach", 22.0))
        changed = False
        for i, since in list(burning.items()):
            if moment - since > burn:
                burning.pop(i)
                burnt.add(i)
                changed = True
                continue
            if moment - since > spread and not state.get(("spread", i)):
                state[("spread", i)] = True
                near = [j for j in range(len(cells)) if j not in burning and j not in burnt and
                        math.dist(cells[j]["p"], cells[i]["p"]) < reach]
                for j in self.rng.sample(near, min(len(near), 2)):
                    burning[j] = moment
                    changed = True
        if changed or "sent" not in state:
            state["sent"] = True
            self.counts["fires"] = len(burning) + len(burnt)
        r = float(part.get("r", 7.0))
        dps = float(part.get("dps", 20.0))
        for player in playing:
            for i in burning:
                c = cells[i]["p"]
                if math.hypot(player.pos[0] - c[0], player.pos[2] - c[2]) < r and \
                        abs(player.pos[1] - c[1]) < 8.0:
                    self._hurt(player, dps * dt, "the fire")
                    break
        for s in self.strandees.values():
            if s["state"] == "wait" and any(
                    math.dist(s["p"], cells[i]["p"]) < r for i in burning):
                self._lose(s, "lost in the smoke")

    def burning_cells(self) -> List[int]:
        for part in self.parts:
            if part["kind"] == "fire":
                return sorted(part["state"].get("burning", {}).keys())
        return []

    # ---- sinkholes: ground that cracks and drops
    def _tick_sinkholes(self, part, playing, dt, t, moment) -> None:
        state = part["state"]
        holes = part.get("holes") or []
        if not holes:
            return
        queue = state.setdefault("queue", [])
        gone = state.setdefault("gone", set())
        if "next" not in state:
            state["next"] = moment + 2.0
        lo, hi = part.get("every", [4.0, 7.0])
        if moment >= state["next"] and t < part["seconds"] - 4.0:
            state["next"] = moment + self.rng.uniform(lo, hi) / part["scale"]
            waiting = {q["i"] for q in queue}
            options = [i for i in range(len(holes)) if i not in gone and i not in waiting]
            if options:
                # the ground gives way where people are standing
                def crowd(i):
                    hx, _, hz = self._abs(holes[i]["p"])
                    return sum(1 for p in playing if math.hypot(p.pos[0] - hx, p.pos[2] - hz) < 30.0)
                options.sort(key=lambda i: -crowd(i) + self.rng.random() * 2.0)
                i = options[0]
                warn = float(part.get("warn", 3.0))
                queue.append({"i": i, "at": moment + warn})
                self.broadcast({"t": "ccx", "k": "crack", "i": i, "p": self._abs(holes[i]["p"]),
                                "r": float(holes[i].get("r", 8.0)), "in": warn})
        for q in list(queue):
            if moment >= q["at"]:
                queue.remove(q)
                gone.add(q["i"])
                self.set_dynamic(holes[q["i"]]["key"], False)
                self.counts["collapsed"] += 1
                self.broadcast({"t": "ccx", "k": "sink", "i": q["i"]})
        floor = part.get("floor")
        if floor is not None:
            for player in playing:
                if player.pos[1] < float(floor):
                    self._hurt(player, 40.0 * dt, "a sinkhole")

    def _abs(self, p: Sequence[float]) -> List[float]:
        """An area-local point (as the maps write them) in world space."""
        ox, _, oz = self.area["centre"]
        return [round(float(p[0]) + ox, 2), round(float(p[1]), 2), round(float(p[2]) + oz, 2)]

    # ======================================================== the stranded
    def _strand(self) -> None:
        spots = list(self.marks.get("stranded", []))
        if not spots:
            return
        taken = [s["p"] for s in self.strandees.values() if s["state"] in ("wait", "carried")]
        self.rng.shuffle(spots)
        count = STRANDED + (1 if (self.current or {}).get("big") else 0)
        for mark in spots:
            if count <= 0:
                break
            if any(math.dist(mark["p"], t) < 20.0 for t in taken):
                continue
            sid = self.next_id
            self.next_id += 1
            self.strandees[sid] = {"id": sid, "p": list(mark["p"]), "state": "wait", "by": 0,
                                   "name": mark.get("name", ""), "look": self.rng.randrange(6)}
            taken.append(mark["p"])
            count -= 1
        self.broadcast({"t": "ccx", "k": "stranded",
                        "n": sum(1 for s in self.strandees.values() if s["state"] == "wait")})

    def _lose(self, s: Dict[str, Any], why: str) -> None:
        s["state"] = "lost"
        self.counts["lost"] += 1
        self.broadcast({"t": "ccx", "k": "lost", "id": s["id"], "p": s["p"], "why": why})

    def _evac(self) -> List[Dict[str, Any]]:
        return self.marks.get("evac", [])

    def _carry_tick(self, playing: List[Player], moment: float) -> None:
        for player in playing:
            sid = player.extra.get("cc_carry")
            if not sid:
                continue
            s = self.strandees.get(sid)
            if s is None or s["state"] != "carried":
                player.extra.pop("cc_carry", None)
                continue
            s["p"] = [round(player.pos[0], 2), round(player.pos[1], 2), round(player.pos[2], 2)]
            for mark in self._evac():
                if math.dist(player.pos, mark["p"]) < float(mark.get("r", 10.0)):
                    self._rescued(player, s)
                    break

    def _rescued(self, player: Player, s: Dict[str, Any]) -> None:
        s["state"] = "safe"
        s["team"] = player.team
        player.extra.pop("cc_carry", None)
        self.points[player.team] = self.points.get(player.team, 0) + RESCUE_POINTS
        player.score += RESCUE_POINTS
        self.counts["rescued"] += 1
        self._stat(player, "rescues")
        self.badge(player, "cc_rescues")
        if self.round_stats.get(player.pid, {}).get("rescues", 0) >= 3:
            self.badge(player, "cc_hero")
        self.broadcast({"t": "ccx", "k": "rescued", "id": s["id"], "by": player.username,
                        "team": player.team, "points": dict(self.points)})
        self._event("cc_rescue", player, player.team)
        self._send_me(player, force=True)
        self._broadcast_state()

    def pick_up(self, player: Player) -> bool:
        """Pick up the nearest stranded townsperson in reach."""
        if player.extra.get("cc_carry") or not self.in_play(player):
            return False
        best, best_d = None, PICKUP_REACH
        for s in self.strandees.values():
            if s["state"] != "wait":
                continue
            d = math.dist(s["p"], player.pos)
            if d < best_d:
                best, best_d = s, d
        if best is None:
            return False
        best["state"] = "carried"
        best["by"] = player.pid
        player.extra["cc_carry"] = best["id"]
        self.broadcast({"t": "ccx", "k": "carry", "id": best["id"], "by": player.pid})
        self._send_me(player, force=True)
        return True

    def use(self, player: Player, message: Dict[str, Any]) -> None:
        self.pick_up(player)

    # ======================================================== the crates
    def _drop_crates(self) -> None:
        spots = list(self.marks.get("crate", []))
        if not spots:
            return
        live = [c for c in self.crates.values() if not c.get("taken")]
        self.rng.shuffle(spots)
        for mark in spots:
            if len(live) >= CRATES:
                break
            if any(math.dist(mark["p"], c["p"]) < 12.0 for c in live):
                continue
            cid = self.next_id
            self.next_id += 1
            crate = {"id": cid, "p": list(mark["p"]), "taken": False}
            self.crates[cid] = crate
            live.append(crate)

    def _pickups(self, playing: List[Player], moment: float) -> None:
        for crate in self.crates.values():
            if crate["taken"]:
                continue
            for player in playing:
                if math.dist(player.pos, crate["p"]) < CRATE_REACH:
                    self._open_crate(player, crate, moment)
                    break

    def _open_crate(self, player: Player, crate: Dict[str, Any], moment: float) -> None:
        crate["taken"] = True
        pw = player.extra.setdefault("cc_pw", [])
        upcoming = {p["kind"] for p in (self.current or {}).get("parts") or []}
        leaning = [POWER_FOR[k] for k in upcoming if k in POWER_FOR]
        options = [k for k in POWERS if k not in pw] or list(POWERS)
        pick = self.rng.choice([k for k in leaning if k in options] or options) \
            if self.rng.random() < 0.6 else self.rng.choice(options)
        if pick == "shoes":
            player.extra["cc_shoes"] = moment + SHOES_SECONDS
        elif pick not in pw:
            pw.append(pick)
        self.points[player.team] = self.points.get(player.team, 0) + CRATE_POINTS
        player.score += CRATE_POINTS
        self.counts["crates"] += 1
        self._stat(player, "crates")
        self.badge(player, "cc_crates")
        self.broadcast({"t": "ccx", "k": "crate", "id": crate["id"], "by": player.pid,
                        "what": pick})
        player.send({"t": "ccx", "k": "power", "what": pick, "name": POWER_NAMES[pick]})
        self._send_me(player, force=True)

    # ============================================================ helpers
    def _stat(self, player: Player, key: str, amount: float = 1.0) -> None:
        stats = self.round_stats.setdefault(player.pid, {})
        stats[key] = stats.get(key, 0.0) + amount

    def _place(self, pos: Sequence[float]) -> str:
        best, best_d = "", 1e9
        for p, name in self.landmarks:
            d = math.hypot(p[0] - pos[0], p[2] - pos[2])
            if d < best_d:
                best, best_d = name, d
        return best if best_d < 90 else ""

    def _event(self, kind: str, player: Optional[Player], team: str, **extra: Any) -> None:
        moment = engine.now()
        key = kind + (team or "")
        if moment - self.events_said.get(key, -99.0) < 6.0:
            return
        self.events_said[key] = moment
        data = {"world": "calamity_coast", "by": player.username if player else "",
                "by_team": player.team if player else "", "team": team}
        data.update(extra)
        if self.bots is not None:
            self.bots.on_game_event(kind, data)

    def _broadcast_state(self) -> None:
        self.broadcast({"t": "ccs", "s": self.hud_state()})

    # ============================================================== state
    def hud_state(self) -> Dict[str, Any]:
        moment = engine.now()
        spec = self.current or {}
        alive = {t: sum(1 for p in self.playing() if p.team == t) for t in self.TEAMS}
        return {"cc": {"stage": self.stage if self.phase == "active" else self.phase,
                       "n": self.index + 1, "of": DISASTERS, "id": spec.get("id", ""),
                       "name": spec.get("name", ""), "line": spec.get("line", ""),
                       "big": bool(spec.get("big")),
                       "left": round(max(0.0, self.stage_until - moment), 1)
                       if self.stage_until < NEVER else 0,
                       "points": dict(self.points), "alive": alive,
                       "stranded": sum(1 for s in self.strandees.values() if s["state"] == "wait")}}

    def snapshot_extra(self) -> Any:
        if self.phase != "active":
            return None
        out: Dict[str, Any] = {}
        t = engine.now() - self.stage_started
        for part in self.parts:
            kind, state = part["kind"], part["state"]
            if kind == "level" and "y" in state:
                out.setdefault("lv", []).append([round(state["y"], 2), part.get("medium", "water"),
                                                 part.get("rect")])
            elif kind == "tornado" and "p" in state:
                out["tw"] = state["p"] + [float(part.get("r", 26.0)), float(part.get("core", 8.0))]
            elif kind == "front" and "s" in state:
                out["fr"] = state["s"]
            elif kind == "fire":
                out["fi"] = self.burning_cells()
            elif kind == "wind":
                out["wd"] = 1 if state.get("gust") else 0
        if self.stage == "active":
            out["t"] = round(t, 1)
        out["st"] = [[s["id"], s["p"][0], s["p"][1], s["p"][2], s["state"], s["by"], s["look"]]
                     for s in self.strandees.values() if s["state"] in ("wait", "carried")]
        out["cr"] = [[c["id"], c["p"][0], c["p"][1], c["p"][2]]
                     for c in self.crates.values() if not c["taken"]]
        return out

    def me_state(self, player: Player) -> Dict[str, Any]:
        moment = engine.now()
        return {"pw": list(player.extra.get("cc_pw", ())),
                "shoes": round(max(0.0, player.extra.get("cc_shoes", 0.0) - moment), 1),
                "carry": int(player.extra.get("cc_carry") or 0),
                "cold": round(float(player.extra.get("cc_cold", 0.0)), 2)}

    def score_row(self, player: Player, row: Dict[str, Any]) -> None:
        stats = self.round_stats.get(player.pid, {})
        row["sv"] = int(stats.get("survived", 0))
        row["rs"] = int(stats.get("rescues", 0))

    def results_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for p in self.players.values():
            if p.team not in self.TEAMS:
                continue
            stats = self.round_stats.get(p.pid, {})
            rows.append({"name": p.username, "team": p.team, "score": p.score,
                         "survived": int(stats.get("survived", 0)),
                         "rescues": int(stats.get("rescues", 0)),
                         "crates": int(stats.get("crates", 0))})
        rows.sort(key=lambda r: (-r["score"], r["name"]))
        return rows

    def result_columns(self) -> List[List[str]]:
        return [["score", "Points"], ["survived", "Survived"], ["rescues", "Rescues"],
                ["crates", "Crates"]]

    def awards(self, winner: str) -> List[str]:
        out = []
        best = max(self.players.values(), default=None,
                   key=lambda p: self.round_stats.get(p.pid, {}).get("rescues", 0))
        if best is not None and self.round_stats.get(best.pid, {}).get("rescues", 0) >= 1:
            out.append("Hero of the hour: %s (%d rescued)" % (
                best.username, self.round_stats[best.pid]["rescues"]))
        sv = [p for p in self.players.values()
              if self.round_stats.get(p.pid, {}).get("survived", 0) >= DISASTERS]
        if sv:
            out.append("Rode out all three: %s" % ", ".join(p.username for p in sv[:6]))
        return out

    def result_extra(self, winner: str) -> Dict[str, Any]:
        return {"points": dict(self.points)}

    def on_round_over(self, winner: str, reason: str, winners: List[Player]) -> None:
        for player in winners:
            self.badge(player, "cc_wins")
            self.badge(player, "cc_area_" + self.area_id, 1, "max")

    def describe(self) -> Dict[str, Any]:
        info = super().describe()
        spec = self.current or {}
        info.update({"disaster": spec.get("name", ""), "stage": self.stage,
                     "points": dict(self.points)})
        return info

    def sleep_extra(self) -> Dict[str, Any]:
        return {"points": dict(self.points)}

    def resume_progress(self, progress: float, state: Dict[str, Any]) -> None:
        points = state.get("points") or {}
        self.points = {t: int(points.get(t, 0)) for t in self.TEAMS}

    # ============================================================== bots
    def bot_role(self, brain) -> str:
        rescue = self.pct("rescuers") * (0.6 + brain.t("support", 0.2) + brain.t("objective", 0.5) * 0.5)
        loot = self.pct("scavengers") * (0.5 + brain.t("explore", 0.2) + brain.t("chaos", 0.1) * 0.5)
        roll = brain.rng.random()
        if roll < rescue * 0.6:
            return "rescuer"
        if roll < rescue * 0.6 + loot * 0.4:
            return "scavenger"
        return "survivor"

    def bot_goal_weights(self, brain, weights: Dict[str, float]) -> Dict[str, float]:
        weights = dict(weights)
        weights["objective"] = weights.get("objective", 1.0) * 6.0
        weights["fight"] = 0.0
        return weights

    def bot_urgent(self, brain) -> bool:
        return self.phase == "active" and bool(self.setting("enabled"))

    def bot_tick(self, moment: float) -> None:
        for player in self.players.values():
            if player.brain is not None:
                player.brain.target = None

    def bot_objective(self, brain) -> None:
        if not self.setting("enabled") or self.phase != "active":
            return
        p = brain.p
        if not p.alive or not self.in_play(p):
            return
        moment = engine.now()
        mind = p.extra.setdefault("cc_mind", {})
        if self._bot_dodge(brain, mind, moment):
            return
        if p.extra.get("cc_carry"):
            self._bot_carry(brain, mind)
            return
        if self.stage == "calm" and moment < self.stage_until - WARN_SECONDS * 0.6:
            if brain.role == "rescuer" and self._bot_rescue(brain, mind):
                return
            if brain.role in ("scavenger", "rescuer") and self._bot_crate(brain, mind):
                return
        elif self.stage == "active" and brain.role == "rescuer" and \
                brain.rng.random() < self.pct("bravery") * 0.02 and self._bot_rescue(brain, mind):
            return
        self._bot_safety(brain, mind, moment)

    def _go(self, brain, point: Sequence[float], key: str) -> None:
        if math.hypot(brain.p.pos[0] - point[0], brain.p.pos[2] - point[2]) < 2.2 and \
                abs(brain.p.pos[1] - point[1]) < 2.5:
            brain.waypoints = []
            return
        brain.go(list(point), key)

    def _bot_dodge(self, brain, mind, moment) -> bool:
        """Out from under a warning circle, away from a funnel."""
        p = brain.p
        dodge = self.pct("dodge") * (0.5 + brain.skill * 0.7)
        for strike in self.strikes.values():
            c, r = strike["p"], strike["r"]
            d = math.hypot(p.pos[0] - c[0], p.pos[2] - c[2])
            if d < r + 1.6 and abs(p.pos[1] - c[1]) < 4.5:
                if mind.get("dodged") == strike["id"] or brain.rng.random() > dodge:
                    mind["dodged"] = strike["id"]
                    continue
                mind["dodged"] = strike["id"]
                ux, uz = (p.pos[0] - c[0]) / max(d, 0.5), (p.pos[2] - c[2]) / max(d, 0.5)
                if d < 0.5:
                    a = brain.rng.uniform(0, 2 * math.pi)
                    ux, uz = math.cos(a), math.sin(a)
                brain.waypoints = [[c[0] + ux * (r + 4.0), p.pos[1], c[2] + uz * (r + 4.0)]]
                self.doing(brain, "diving out of the way")
                self.callout(brain, ["incoming", "move!", "watch out", "look up", "MOVE"],
                             "dodge", chance=0.35)
                return True
        for part in self.parts:
            if part["kind"] == "tornado" and "p" in part["state"]:
                tx, _, tz = part["state"]["p"]
                d = math.hypot(p.pos[0] - tx, p.pos[2] - tz)
                if d < float(part.get("r", 26.0)) + 10.0:
                    ux, uz = (p.pos[0] - tx) / max(d, 0.5), (p.pos[2] - tz) / max(d, 0.5)
                    brain.go([p.pos[0] + ux * 30.0, p.pos[1], p.pos[2] + uz * 30.0], "flee-twister")
                    self.doing(brain, "running from the tornado")
                    self.callout(brain, ["TORNADO", "its coming this way", "run run run",
                                         "get away from the twister"], "twister", chance=0.6)
                    return True
        return False

    def _bot_carry(self, brain, mind) -> None:
        evac = self._evac()
        if not evac:
            return
        p = brain.p
        best = min(evac, key=lambda m: math.dist(m["p"], p.pos))
        self._go(brain, best["p"], "evac")
        self.doing(brain, "carrying somebody to the evacuation point")
        self.callout(brain, ["got one", "taking them to evac", "carrying one, cover me",
                             "evac incoming"], "carry", chance=0.45, every=40.0)

    def _bot_rescue(self, brain, mind) -> bool:
        p = brain.p
        waiting = [s for s in self.strandees.values() if s["state"] == "wait"]
        if not waiting:
            return False
        claimed = {o.extra.get("cc_mind", {}).get("rescue") for o in self.players.values()
                   if o is not p and o.team == p.team}
        options = [s for s in waiting if s["id"] not in claimed] or waiting
        s = min(options, key=lambda s: math.dist(s["p"], p.pos))
        if math.dist(s["p"], p.pos) > 160.0:
            return False
        mind["rescue"] = s["id"]
        if math.dist(s["p"], p.pos) < PICKUP_REACH - 0.8:
            self.pick_up(p)
            return True
        self._go(brain, s["p"], "rescue%d" % s["id"])
        place = self._place(s["p"])
        self.doing(brain, "going to rescue somebody stranded%s" % (" near " + place if place else ""))
        self.callout(brain, ["someone's stranded" + (" by " + place.replace("the ", "", 1)
                                                      if place else ""),
                             "ill get them", "on the rescue", "going for the stranded one"],
                     "rescue", chance=0.35, every=45.0)
        return True

    def _bot_crate(self, brain, mind) -> bool:
        p = brain.p
        open_ = [c for c in self.crates.values() if not c["taken"]]
        if not open_:
            return False
        c = min(open_, key=lambda c: math.dist(c["p"], p.pos))
        if math.dist(c["p"], p.pos) > 120.0:
            return False
        self._go(brain, c["p"], "crate%d" % c["id"])
        self.doing(brain, "going for a supply crate")
        self.callout(brain, ["crate!", "supplies", "getting the crate", "mine"], "crate",
                     chance=0.25, every=40.0)
        return True

    def safe_kind(self) -> List[str]:
        """Where a sensible person goes for the coming disaster: the mark
        kinds, best first."""
        spec = self.current or {}
        if spec.get("safe"):
            return list(spec["safe"])
        kinds = [p["kind"] for p in spec.get("parts") or []]
        if "level" in kinds:
            return ["high"]
        if "front" in kinds or "tornado" in kinds or "cold" in kinds or "rain" in kinds:
            return ["shelter", "heat"]
        if "quake" in kinds or "fire" in kinds or "sinkholes" in kinds:
            return ["open", "high"]
        return ["shelter"]

    def _bot_safety(self, brain, mind, moment) -> None:
        p = brain.p
        kinds = self.safe_kind()
        spec = self.current or {}
        key = "%s:%d" % (spec.get("id", ""), self.index)
        spot = mind.get("safe")
        if mind.get("safe_for") != key or spot is None or not self._still_safe(spot):
            if mind.get("safe_for") != key and kinds:
                self.callout(brain, PLAN_LINES.get(kinds[0], PLAN_LINES["shelter"]), "plan",
                             chance=0.5, every=30.0)
            spot = self._pick_safe(brain, kinds)
            mind["safe"] = spot
            mind["safe_for"] = key
        if spot is None:
            return
        self._go(brain, spot, "safe")
        near = math.hypot(p.pos[0] - spot[0], p.pos[2] - spot[2]) < 3.0
        self.doing(brain, "sheltering %s" % ("near " + self._place(spot) if self._place(spot) else "")
                   if near else "heading for safety ahead of the %s" % (spec.get("name") or "disaster").lower())

    def _still_safe(self, spot: Sequence[float]) -> bool:
        for part in self.parts:
            if part["kind"] == "level" and spot[1] + 1.4 < part["state"].get("y", -99.0):
                return False
            if part["kind"] == "fire":
                cells = self.marks.get(part.get("marks", "fire"), [])
                for i in part["state"].get("burning", {}):
                    if math.dist(cells[i]["p"], spot) < float(part.get("r", 7.0)) + 3.0:
                        return False
        return True

    def _pick_safe(self, brain, kinds: Sequence[str]) -> Optional[List[float]]:
        p = brain.p
        need = -99.0
        for part in (self.current or {}).get("parts") or []:
            if part["kind"] == "level" and not part.get("rect"):
                need = max(need, float(part.get("to", 0.0)) * 1.12 + 1.0)
        crowd: Dict[Tuple[int, int, int], int] = {}
        for other in self.players.values():
            spot = other.extra.get("cc_mind", {}).get("safe")
            if other is not p and spot:
                k = (int(spot[0]), int(spot[1]), int(spot[2]))
                crowd[k] = crowd.get(k, 0) + 1
        best, best_s = None, -1e9
        smart = 0.4 + brain.skill * 0.6
        for rank, kind in enumerate(kinds):
            for m in self.marks.get(kind, []):
                spot = m["p"]
                if kind == "high" and spot[1] < need:
                    continue
                if not self._still_safe(spot):
                    continue
                d = math.dist(spot, p.pos)
                score = -d * (0.5 + smart) - rank * 40.0 + brain.rng.uniform(0.0, 30.0)
                score -= crowd.get((int(spot[0]), int(spot[1]), int(spot[2])), 0) * 25.0
                if score > best_s:
                    best, best_s = list(spot), score
        return best

    def bot_context(self) -> List[str]:
        spec = self.current or {}
        lines = ["You are playing Calamity Coast: survive disasters for points; carry "
                 "stranded townsfolk to the evacuation point; nobody can hurt anybody."]
        if spec:
            lines.append("Disaster %d of %d: %s (%s)." % (self.index + 1, DISASTERS,
                                                            spec.get("name", "?"), self.stage))
        lines.append("Points: %s %d, %s %d." % (self.team_name("red"), self.points.get("red", 0),
                                                self.team_name("blue"), self.points.get("blue", 0)))
        return lines

    def bot_me(self, brain) -> Dict[str, Any]:
        p = brain.p
        return {"role": brain.role, "carrying": bool(p.extra.get("cc_carry")),
                "powers": list(p.extra.get("cc_pw", ())),
                "doing": p.extra.get("bot_doing", "")}

    def bot_spread(self, players: List[Player]) -> None:
        """Nothing to balance: every role is a way to score."""

    def observe(self) -> Dict[str, Any]:
        return {"stage": self.stage, "index": self.index, "parts": [p["kind"] for p in self.parts]}

    def selftest(self, result: Dict[str, Any]) -> List[Tuple[str, bool, Any]]:
        c = self.counts
        return [
            ("disasters strike", c["disasters"] >= 2, c["disasters"]),
            ("people survive them", c["survived"] >= 2, c["survived"]),
            ("townsfolk are rescued", c["rescued"] >= 1, dict(c)),
            ("crates are opened", c["crates"] >= 1, c["crates"]),
        ]


WORLD_CLASS = CalamityCoastWorld
