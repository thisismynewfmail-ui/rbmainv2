"""Sky Sprint: an obstacle-course race in the sky
(app/models/event_worlds/sky_sprint.py).

Two teams -- the **Red Rockets** and the **Blue Comets** -- race the same
course from a start deck to a finish high above it.  The gates drop at GO;
everybody runs, jumps and rides the course's machinery past its
checkpoints, and a fall (into the lava, the chocolate, the grid or the
clouds) puts you back at the last checkpoint you reached.

**Points** go to your team: one for every checkpoint you reach, three more
for the first racer to reach each one, and for the finish 12, 9, 7, 5, 4,
3, 2 and 1 by place.  Bonk a rival off the course (they fall within a few
seconds of your glove) and that is two more.  The team with the most when
everybody is home -- or the clock runs out, or the hurry-up after half the
field has finished does -- wins the round.

**The bonk glove** is everybody's only kit: a shove, no damage, on a short
cooldown.  **Power-ups** turn up on their spots round the course: spring
shoes (higher jumps), a rocket (E: a dash), a feather (you fall slowly) and
a bubble (nothing knocks you about).

**The course** (app/game/maps/events/sky_sprint/common.py) is platforms
and the numbers for everything that moves.  Four clocks run from the
moment the course is set up: the *hazard clock* (sweepers and wind), the
*hammer* and *laser clocks*, and the *beat clock* (the blinking tiles).
A twist that speeds something up runs its clock faster, so nothing jumps
when it starts or stops.  All four go to the clients many times a second,
so what you see swing and what the server knocks the bots about with are
the same.  People's own bodies are moved by their browser (static/js/worlds/
sky_sprint.js does the pads, belts, wind and knocks on the local player);
bots are moved here, by the same rules.

**Each place has a twist** (``extra["twist"]``): the Foundry's conveyors
run backwards, Candy Clouds' sugar rush speeds everybody up, Neon Grid's
drop doubles the beat, and the Jade Temple's typhoon blows hard across
every bridge.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import instance as engine
from ..instance import JUMP_SPEED, Player, normalise
from ..maps.events import sky_sprint as ss_map
from .arena import NEVER, ArenaWorld

CP_POINTS = 1
FIRST_POINTS = 3
PLACE_POINTS = (12, 9, 7, 5, 4, 3, 2, 1)
RING_OUT_POINTS = 2
RING_OUT_SECONDS = 4.0
BONK_REACH = 7.5
BONK_COOL = 1.1
BONK_FORCE = 32.0
BONK_UP = 15.0
BONK_GRACE = 2.5          # a racer just bonked cannot be bonked again yet
POWERS = ("spring", "rocket", "feather", "shield")
POWER_NAMES = {"spring": "spring shoes", "rocket": "a rocket", "feather": "a feather",
               "shield": "a bubble"}
POWER_SECONDS = {"spring": 14.0, "feather": 12.0, "shield": 10.0}
POWER_REACH = 3.4
POWER_RESPAWN = 14.0
SPRING_SCALE = 1.3
FEATHER_GRAVITY = 0.42
ROCKET_SPEED = 56.0
ROCKET_UP = 12.0
SWEEP_KNOCK = 32.0
# The Candy course's sweepers carry a lollipop on the end of each arm: a disc
# stood on edge, side on to whoever it is coming at, rising well past the
# bar -- and as solid as the bar.  Its middle sits LOLLY_AT along the arm from
# the tip and LOLLY_UP over the bar (static/js/worlds/sky_sprint.js draws it
# from the same numbers).
LOLLY_AT = -0.9
LOLLY_UP = 0.4
LOLLY_R = 1.7
LOLLY_T = 0.5
HAMMER_KNOCK = 40.0
KNOCK_UP = 16.0
HIT_COOL = 0.7
CP_HEIGHT = 9.0
CRUMBLE_AFTER = 0.6
CRUMBLE_BACK = 2.6
HURRY_SECONDS = 25.0
PROGRESS_EVERY = 0.25
TWIST_RATES = {"reverse": {"hammer": 1.45}, "drop": {"beat": 2.0, "laser": 1.7},
               "sugar_rush": {}, "typhoon": {"wind": 1.4}}
DEFAULTS: Dict[str, Any] = {}


def _defaults() -> Dict[str, Any]:
    if not DEFAULTS:
        from ...models.event_worlds import sky_sprint as meta
        for spec in meta.BOT_FIELDS:
            DEFAULTS[spec[0]] = spec[3]
    return DEFAULTS


def _item(item_id: str, name: str, kind: str, parts: List[Dict[str, Any]],
          **stats: Any) -> Dict[str, Any]:
    body = {"kind": kind, "rpm": stats.pop("rpm", 120), "mag": stats.pop("mag", 99),
            "reserve": 0, "range": stats.pop("range", 60), "custom": True}
    body.update(stats)
    return ArenaWorld.item(item_id, name, body, parts)


# A cartoon boxing glove, worn rather than held: the hand's frame has +Z out
# along the punch, +Y up the back of the hand and +X to the inside, where the
# thumb tucks.  The round cuff is wide enough to take the arm (it shows as a
# sleeve on the wrist), and from behind -- in first person -- as the glove's
# dark opening inside a blue rolled rim.
GLOVE_RED, GLOVE_SHADE, GLOVE_CUFF, GLOVE_BAND = "#e5352c", "#b9241e", "#f4f1ea", "#2a6fd6"
GLOVE = _item("ss_glove", "Bonk Glove", "ss_bonk", [
    {"t": "cyl", "p": [0, 0, -0.4], "s": [1.22, 0.56, 1.22], "c": GLOVE_CUFF, "r": [1.5708, 0, 0]},
    {"t": "cyl", "p": [0, 0, -0.27], "s": [1.26, 0.1, 1.26], "c": GLOVE_BAND, "r": [1.5708, 0, 0]},
    {"t": "torus", "p": [0, 0, -0.67], "s": [1.18, 0.2, 1.18], "c": GLOVE_BAND, "r": [1.5708, 0, 0]},
    {"t": "cyl", "p": [0, 0, -0.672], "s": [1.0, 0.02, 1.0], "c": "#5a1210", "r": [1.5708, 0, 0]},
    {"t": "cyl", "p": [0, 0.02, -0.12], "s": [1.04, 0.36, 1.1], "c": GLOVE_RED, "r": [1.5708, 0, 0],
     "m": "glass"},
    {"t": "sph", "p": [0, 0.06, 0.42], "s": [1.48, 1.34, 1.48], "c": GLOVE_RED, "m": "glass"},
    {"t": "sph", "p": [0, 0.18, 0.9], "s": [1.22, 0.9, 0.66], "c": GLOVE_RED, "m": "glass"},
    {"t": "sph", "p": [0.64, -0.16, 0.5], "s": [0.44, 0.52, 0.96], "c": GLOVE_SHADE,
     "r": [0.2, 0, 0.25], "m": "glass"},
    {"t": "star", "p": [0, 0.69, 0.38], "s": [0.5, 0.48, 0.1], "c": "#ffd23f", "r": [-1.2708, 0, 0]}],
    rpm=int(60.0 / BONK_COOL), range=BONK_REACH, melee=True, sound="ss_bonk")


# =============================================================== the motion
# The same formulas are in static/js/worlds/sky_sprint.js: keep them in step.
def hammer_angle(h: Dict[str, Any], t: float) -> Tuple[float, float]:
    """A pendulum's angle at hazard time ``t``, and which way it is going."""
    w = 2.0 * math.pi / h["period"]
    a = w * t + h["ph"]
    return h["amp"] * math.sin(a), math.copysign(1.0, math.cos(a))


def hammer_head(h: Dict[str, Any], t: float) -> Tuple[List[float], float]:
    theta, going = hammer_angle(h, t)
    px, py, pz = h["pivot"]
    s, c = math.sin(theta) * h["len"], math.cos(theta) * h["len"]
    if h["axis"] == "x":
        return [px + s, py - c, pz], going
    return [px, py - c, pz + s], going


def hammer_hit(h: Dict[str, Any], t: float, pos: Sequence[float]
               ) -> Optional[Tuple[float, float]]:
    """Does the head overlap a body standing at ``pos``?  Returns the way it
    knocks them (x, z) or None."""
    head, going = hammer_head(h, t)
    sx, sy, sz = h["head"]
    if abs(pos[0] - head[0]) > sx / 2.0 + 1.2 or abs(pos[2] - head[2]) > sz / 2.0 + 0.9:
        return None
    if pos[1] > head[1] + sy / 2.0 or pos[1] + 5.4 < head[1] - sy / 2.0:
        return None
    return (going, 0.0) if h["axis"] == "x" else (0.0, going)


def sweeper_hit(sw: Dict[str, Any], t: float, pos: Sequence[float]
                ) -> Optional[Tuple[float, float]]:
    """Is a body at ``pos`` in the way of one of a sweeper's arms (or, on the
    Candy course, the lollipop on the end of one)?  Returns the way the arm
    is moving at it, or None."""
    cx, cy, cz = sw["c"]
    bar = cy + sw["h"]
    half = sw["t"] / 2.0
    lolly = sw.get("look") == "lolly"
    head = bar + LOLLY_UP
    top = max(bar + half, head + LOLLY_R) if lolly else bar + half
    low = min(bar - half, head - LOLLY_R) if lolly else bar - half
    if pos[1] > top or pos[1] + 5.4 < low:
        return None
    dx, dz = pos[0] - cx, pos[2] - cz
    if math.hypot(dx, dz) > sw["r"] + (LOLLY_AT + LOLLY_R + 1.0 if lolly else 1.4):
        return None
    turn = sw["ph"] + sw["w"] * t
    sign = 1.0 if sw["w"] >= 0 else -1.0
    for k in range(int(sw["arms"])):
        a = turn + k * 2.0 * math.pi / sw["arms"]
        ux, uz = math.cos(a), math.sin(a)
        along = dx * ux + dz * uz
        across = -dx * uz + dz * ux
        # the bar
        if -1.2 <= along <= sw["r"] + 1.2 and abs(across) < half + 1.3 and \
                pos[1] <= bar + half and pos[1] + 5.4 >= bar - half:
            return (-uz * sign, ux * sign)
        # the lollipop: a disc stood on edge across the arm's way, so how
        # near the body comes to its middle, in the plane of the disc
        if lolly and abs(across) < LOLLY_T / 2.0 + 1.3:
            off_along = max(0.0, abs(along - (sw["r"] + LOLLY_AT)) - 1.0)
            off_up = max(0.0, pos[1] - head, head - (pos[1] + 5.4))
            if math.hypot(off_along, off_up) < LOLLY_R:
                return (-uz * sign, ux * sign)
    return None


def laser_beam(lz: Dict[str, Any], t: float) -> Tuple[List[float], List[float]]:
    k = math.sin(2.0 * math.pi * t / lz["period"] + lz["ph"])
    off = [m * k for m in lz["move"]]
    a = [lz["a"][i] + off[i] for i in range(3)]
    b = [lz["b"][i] + off[i] for i in range(3)]
    return a, b


def laser_hit(lz: Dict[str, Any], t: float, pos: Sequence[float]) -> bool:
    a, b = laser_beam(lz, t)
    y = a[1]
    if not (pos[1] - 0.2 < y < pos[1] + 5.4):
        return False
    ax, az, bx, bz = a[0], a[2], b[0], b[2]
    vx, vz = bx - ax, bz - az
    length2 = vx * vx + vz * vz
    f = 0.0 if length2 < 1e-6 else max(0.0, min(1.0, ((pos[0] - ax) * vx + (pos[2] - az) * vz)
                                                / length2))
    return math.hypot(pos[0] - (ax + vx * f), pos[2] - (az + vz * f)) < 1.3


def blink_on(spec: Dict[str, Any], beat: float) -> bool:
    return ((beat + spec["ph"]) % spec["period"]) / spec["period"] < spec["on"]


def wind_now(spec: Dict[str, Any], t: float) -> float:
    """How hard a gust zone is blowing (0 between gusts)."""
    k = math.sin(2.0 * math.pi * t / spec["period"] + spec["ph"])
    return max(0.0, (k - 0.25) / 0.75)


def _off_leg(pos: Sequence[float], a: Sequence[float], b: Sequence[float]) -> float:
    """How far a body is from the leg of the line between marks a and b."""
    vx, vy, vz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    length2 = vx * vx + vy * vy + vz * vz
    f = 0.0 if length2 < 1e-6 else max(0.0, min(1.0, ((pos[0] - a[0]) * vx + (pos[1] - a[1]) * vy
                                                      + (pos[2] - a[2]) * vz) / length2))
    return math.dist(pos, [a[0] + vx * f, a[1] + vy * f, a[2] + vz * f])


def _in_rect(rect: Sequence[float], pos: Sequence[float], pad: float = 0.0) -> bool:
    return rect[0] - pad <= pos[0] <= rect[1] + pad and rect[2] - pad <= pos[2] <= rect[3] + pad


class SkySprintWorld(ArenaWorld):
    MAP = ss_map
    TEAMS = ("red", "blue")
    TEAM_NAMES = {"red": "Red Rockets", "blue": "Blue Comets"}
    ROUNDS_PER_AREA = 2
    SETUP_SECONDS = 10.0
    ROUND_SECONDS = 180.0
    RESULTS_SECONDS = 15.0
    ELIMINATION = False
    CATCHES_FALLS = True
    LOGO = "Sky Sprint"
    FREEZE_COUNTDOWN = True
    CUSTOM_KINDS = ("ss_bonk",)
    respawn_seconds = 1.0
    BOT_CHATTER = ["go go go", "gg", "so close", "nooo", "that hammer", "wait up", "lol",
                   "ez", "how do you do this jump", "nice", "almost there"]

    # ------------------------------------------------------------ settings
    def setting(self, key: str) -> Any:
        cfg = getattr(self.bots, "cfg", None) if self.bots is not None else None
        value = (cfg or {}).get("sky_sprint_" + key)
        return _defaults().get(key) if value is None else value

    def pct(self, key: str) -> float:
        try:
            return max(0.0, min(1.0, float(self.setting(key)) / 100.0))
        except (TypeError, ValueError):
            return 0.5

    # ================================================================ setup
    def world_setup(self) -> None:
        self.route: List[Dict[str, Any]] = []
        self.cps: List[Dict[str, Any]] = []
        self.pads: List[Dict[str, Any]] = []
        self.boosts: List[Dict[str, Any]] = []
        self.spots: List[Dict[str, Any]] = []
        self.extra: Dict[str, Any] = {}
        self.points: Dict[str, int] = {"red": 0, "blue": 0}
        self.firsts: Dict[int, int] = {}
        self.finished: List[int] = []
        self.ht = 0.0
        self.hc = 0.0
        self.lc = 0.0
        self.bt = 0.0
        self.t0 = 0.0
        self.hurry_until = 0.0
        self.crumbled: Dict[str, Dict[str, float]] = {}
        self.blinks: Dict[str, bool] = {}
        self.blink_keys: Dict[str, List[str]] = {}
        self.twist: Dict[str, Any] = {"kind": "", "on": False, "until": 0.0, "next": NEVER,
                                      "warned": False}
        self.round_stats: Dict[int, Dict[str, float]] = {}
        self.counts: Dict[str, int] = {"checkpoints": 0, "finishes": 0, "falls": 0, "bonks": 0,
                                       "home_bonks": 0, "ring_outs": 0, "powers": 0, "rockets": 0,
                                       "hits": 0,
                                       "pads": 0, "twists": 0, "crumbles": 0, "zaps": 0}
        self.events_said: Dict[str, float] = {}
        self.landmarks: List[Tuple[List[float], str]] = []
        self.next_progress = 0.0

    def round_setup(self) -> None:
        area = self.area
        extra = area.get("extra") or {}
        self.extra = extra
        self.ROUND_SECONDS = float(extra.get("round_seconds") or SkySprintWorld.ROUND_SECONDS)
        points = area.get("points") or {}
        self.route = sorted([dict(m) for m in points.get("route") or []], key=lambda m: m["i"])
        self.cps = sorted([dict(m) for m in points.get("cp") or []], key=lambda m: m["i"])
        self.pads = [dict(m) for m in points.get("pad") or []]
        self.boosts = [dict(m) for m in points.get("boost") or []]
        self.spots = [{"p": list(m["p"]), "kind": "", "back": 0.0}
                      for m in points.get("power") or []]
        self.landmarks = [(list(m["p"]), m["name"]) for m in area.get("landmarks") or []]
        self.points = {"red": 0, "blue": 0}
        self.firsts = {}
        self.finished = []
        self.round_stats = {}
        self.events_said = {}
        self.hurry_until = 0.0
        self.crumbled = {}
        moment = engine.now()
        self.t0 = moment
        self.ht = self.hc = self.lc = 0.0
        self.bt = 0.0
        kind = extra.get("twist", "")
        lo, hi = extra.get("twist_every") or (40.0, 55.0)
        self.twist = {"kind": kind, "on": False, "until": 0.0, "warned": False,
                      "next": moment + self.SETUP_SECONDS + self.rng.uniform(lo, hi)
                      if kind else NEVER}
        # everything switchable as the course starts: the gates up, every
        # tile there
        for key, d in (area.get("dynamic") or {}).items():
            self.set_dynamic(key, True)
        self.blinks = {spec["group"]: True for spec in extra.get("blink") or []}
        self.blink_keys = {}
        for key, d in (area.get("dynamic") or {}).items():
            if d.get("group") in self.blinks:
                self.blink_keys.setdefault(d["group"], []).append(key)
        for k, spot in enumerate(self.spots):
            spot["kind"] = POWERS[(k + self.round_number) % len(POWERS)]
        for player in self.players.values():
            self.reset_player(player)
            self.set_loadout(player, [GLOVE], quiet=True)

    def reset_player(self, player: Player) -> None:
        for key in ("ss_cp", "ss_spot", "ss_done", "ss_place", "ss_pw", "ss_rocket",
                    "ss_bonked_by", "ss_hit_at", "ss_boost", "ss_push", "ss_mind", "ss_prog",
                    "ss_node", "ss_slow", "ss_seen_boost", "ss_on_pad", "ss_drift", "ss_belt"):
            player.extra.pop(key, None)

    # ============================================================ spawning
    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        spawns = self.area.get("spawns") or {}
        return list(spawns.get(team) or spawns.get("red") or []) or super().spawn_points(team)

    def on_spawned(self, player: Player) -> None:
        if player.extra.get("loadout") is None:
            self.set_loadout(player, [GLOVE], quiet=True)
        player.extra.setdefault("ss_cp", 0)

    def on_player_join(self, player: Player) -> None:
        super().on_player_join(player)
        self.set_loadout(player, [GLOVE], quiet=True)

    def welcome_lines(self, player: Player) -> List[str]:
        lines = super().welcome_lines(player)
        lines.append("Race the course to the finish: every checkpoint scores for your team, "
                     "and so does your place at the end. Fall and you are back at your last "
                     "checkpoint.")
        lines.append("Your glove bonks rivals off the course. Power-ups: spring shoes, a rocket "
                     "(press E), a feather and a bubble.")
        return lines

    # ============================================================ movement
    def _power(self, player: Player, kind: str) -> bool:
        return (player.extra.get("ss_pw") or {}).get(kind, 0.0) > engine.now()

    def move_scale(self, player: Player) -> float:
        moment = engine.now()
        scale = 1.0
        if player.extra.get("ss_boost", 0.0) > moment:
            scale *= 2.2
        if self.twist["on"] and self.twist["kind"] == "sugar_rush":
            scale *= 1.3
        if player.brain is not None and player.extra.get("ss_slow", 0.0) > moment:
            scale *= 0.5                          # a jump misjudged: short of the far side
        for zone in self.extra.get("taffy") or []:
            if _in_rect(zone["rect"], player.pos) and abs(player.pos[1] - zone["y"]) < 0.8:
                scale *= float(zone.get("scale", 0.55))
        return scale

    def can_fire(self, player: Player) -> bool:
        # (home already, a racer may still swing: at rivals home too -- _bonk)
        return self.phase == "active" and self.in_play(player)

    def can_hurt(self, attacker: Player, victim: Player) -> bool:
        return False

    def hostiles_for(self, player: Player):
        return iter(())

    # ============================================================== rounds
    def on_live(self) -> None:
        self.set_dynamic_group("gate", False)
        self.broadcast({"t": "ssx", "k": "go"})

    def round_tick(self, dt: float, moment: float) -> None:
        self._clocks(dt, moment)
        self._twist_tick(moment)
        self._blink_tick()
        playing = self.playing()
        self._crumble_tick(playing, moment)
        self._spots_tick(moment)
        for player in playing:
            self._player_tick(player, dt, moment)
        if moment >= self.next_progress:
            self.next_progress = moment + PROGRESS_EVERY
            for player in playing:
                self._progress(player)
        racers = [p for p in playing if p.team in self.TEAMS]
        if racers:
            done = sum(1 for p in racers if p.extra.get("ss_done") is not None)
            if done == len(racers):
                self._finish("everybody is home")
                return
            if not self.hurry_until and done >= max(1, (len(racers) + 1) // 2):
                self.hurry_until = moment + HURRY_SECONDS
                self.broadcast({"t": "ssx", "k": "hurry", "in": HURRY_SECONDS})
                self._event("ss_hurry", None, "")
            if self.hurry_until and moment >= self.hurry_until:
                self._finish("the hurry-up ran out")

    def setup_tick(self, dt: float, moment: float) -> None:
        # the course runs while everybody waits at the gate
        self._clocks(dt, moment)
        self._blink_tick()
        # and everybody waits ON the start deck: it has no rails, and the
        # sky has ground at the bottom of it, so anybody below it now (a
        # browser that moved before it heard it was held) goes back up --
        # nobody starts the race from the floor of the world
        for player in self.playing():
            starts = self.spawn_points(player.team if player.team in self.TEAMS else "red")
            if starts and player.pos[1] < min(s["p"][1] for s in starts) - 3.0:
                self._send_back(player, moment)

    def _clocks(self, dt: float, moment: float) -> None:
        self.ht += dt
        self.hc += dt * self._rate("hammer")
        self.lc += dt * self._rate("laser")
        self.bt += dt * self._rate("beat")

    def _rate(self, what: str) -> float:
        if not self.twist["on"]:
            return 1.0
        return TWIST_RATES.get(self.twist["kind"], {}).get(what, 1.0)

    def time_up(self) -> None:
        self._finish("time ran out")

    def _finish(self, why: str) -> None:
        red, blue = self.points.get("red", 0), self.points.get("blue", 0)
        if red == blue:
            first = self.players.get(self.finished[0]) if self.finished else None
            winner = first.team if first is not None and first.team in self.TEAMS else ""
        else:
            winner = "red" if red > blue else "blue"
        self.finish_round(winner, why)

    def leader(self) -> str:
        red, blue = self.points.get("red", 0), self.points.get("blue", 0)
        return "" if red == blue else ("red" if red > blue else "blue")

    def headline(self, winner: str, reason: str) -> str:
        if not winner:
            return "A dead heat -- %d all" % self.points.get("red", 0)
        loser = "blue" if winner == "red" else "red"
        return "%s win, %d to %d" % (self.team_name(winner), self.points.get(winner, 0),
                                     self.points.get(loser, 0))

    # ============================================================== twists
    def _twist_tick(self, moment: float) -> None:
        tw = self.twist
        kind = tw["kind"]
        if not kind:
            return
        warn = float(self.extra.get("warn", 3.0))
        if not tw["on"] and not tw["warned"] and moment >= tw["next"] - warn:
            tw["warned"] = True
            self.broadcast({"t": "ssx", "k": "twist_warn", "twist": kind, "in": warn})
        if not tw["on"] and moment >= tw["next"]:
            length = float(self.extra.get("twist_for", 12.0))
            tw.update({"on": True, "until": moment + length, "warned": False})
            self.counts["twists"] += 1
            self.broadcast({"t": "ssx", "k": "twist", "twist": kind, "on": True, "for": length})
            self._event("ss_twist", None, "", twist=kind)
        elif tw["on"] and moment >= tw["until"]:
            lo, hi = self.extra.get("twist_every") or (40.0, 55.0)
            tw.update({"on": False, "next": moment + self.rng.uniform(lo, hi)})
            self.broadcast({"t": "ssx", "k": "twist", "twist": kind, "on": False})

    # ===================================================== the switchables
    def _blink_tick(self) -> None:
        dyn = self.area.get("dynamic") or {}
        for spec in self.extra.get("blink") or []:
            group = spec["group"]
            on = blink_on(spec, self.bt)
            keys = self.blink_keys.get(group) or []
            if self.blinks.get(group) != on:
                self.blinks[group] = on
                if not on:
                    self.set_dynamic_keys(keys, False)
                    continue
            if not on:
                continue
            # back -- but never into anybody: a tile with somebody in its way
            # (on the ram under it, falling past) waits until they are clear
            due = [key for key in keys if not self.dyn_on.get(key)]
            if due:
                self.set_dynamic_keys([key for key in due
                                       if not self._in_the_way(dyn[key].get("boxes") or [])], True)

    def _in_the_way(self, boxes: Sequence[Sequence[Sequence[float]]]) -> bool:
        """Is anybody's body inside one of these boxes, deeper than the step
        a solid coming on lifts them up?"""
        for player in self.players.values():
            if not player.alive:
                continue
            x, y, z = player.pos
            for lo, hi in boxes:
                if lo[0] < x + 1.2 and hi[0] > x - 1.2 and lo[2] < z + 0.9 and hi[2] > z - 0.9 \
                        and lo[1] < y + 5.4 and hi[1] > y + 0.05 and hi[1] - y > 2.1:
                    return True
        return False

    def _crumble_tick(self, playing: List[Player], moment: float) -> None:
        for tile in self.extra.get("crumble") or []:
            key = tile["key"]
            state = self.crumbled.setdefault(key, {"at": 0.0, "back": 0.0})
            if state["back"]:
                if moment >= state["back"]:
                    # back -- unless somebody is in its way (somebody stood
                    # at its edge, level with it, is not)
                    boxes = ((self.area.get("dynamic") or {}).get(key) or {}).get("boxes") or []
                    if not self._in_the_way(boxes):
                        state["back"] = 0.0
                        state["at"] = 0.0
                        self.set_dynamic(key, True)
                continue
            if not state["at"]:
                for p in playing:
                    if _in_rect(tile["rect"], p.pos, 1.0) and abs(p.pos[1] - tile["y"]) < 0.6:
                        state["at"] = moment + CRUMBLE_AFTER
                        self.broadcast({"t": "ssx", "k": "creak", "key": key})
                        break
            elif moment >= state["at"]:
                state["back"] = moment + CRUMBLE_BACK
                self.counts["crumbles"] += 1
                self.set_dynamic(key, False)

    def _spots_tick(self, moment: float) -> None:
        for k, spot in enumerate(self.spots):
            if not spot["kind"] and spot["back"] and moment >= spot["back"]:
                spot["kind"] = POWERS[self.rng.randrange(len(POWERS))]
                spot["back"] = 0.0

    # ============================================================ a racer
    def _player_tick(self, player: Player, dt: float, moment: float) -> None:
        pos = player.pos
        extra = self.extra
        # off the course: back to the last checkpoint
        if pos[1] < float(extra.get("fall_y", -40.0)):
            self._fell(player, moment)
            return
        cp = int(player.extra.get("ss_cp", 0))
        if player.extra.get("ss_done") is None and cp < len(self.cps):
            target = self.cps[cp]
            tp = target["p"]
            if math.hypot(pos[0] - tp[0], pos[2] - tp[2]) < float(target["r"]) and \
                    -2.0 < pos[1] - tp[1] < CP_HEIGHT:
                self._reach(player, target, moment)
        for k, spot in enumerate(self.spots):
            if spot["kind"] and math.dist(spot["p"], pos) < POWER_REACH:
                self._pick_up(player, spot, k, moment)
        if player.brain is not None:
            self._bot_body(player, dt, moment)
        else:
            self._grace(player, moment)
        # a bonked rival who falls soon after is the bonker's ring-out
        hit = player.extra.get("ss_bonked_by")
        if hit and moment - hit[1] > RING_OUT_SECONDS:
            player.extra.pop("ss_bonked_by", None)

    def _grace(self, player: Player, moment: float) -> None:
        """A person's browser moves them on pads, belts and in the wind, and
        knocks them about; let the movement check allow for it nearby."""
        pos = player.pos
        near = False
        for pad in self.pads:
            if math.hypot(pos[0] - pad["p"][0], pos[2] - pad["p"][2]) < pad["r"] + 5.0:
                near = True
                break
        if not near:
            for boost in self.boosts:
                if math.dist(boost["p"], pos) < boost["l"] + 6.0:
                    near = True
                    break
        if not near:
            for key in ("belts", "wind", "jelly"):
                for zone in self.extra.get(key) or []:
                    if _in_rect(zone["rect"], pos, 4.0) and -3.0 < pos[1] - zone["y"] < 16.0:
                        near = True
                        break
        if not near:
            for sw in self.extra.get("sweepers") or []:
                if math.dist(sw["c"], pos) < sw["r"] + 6.0:
                    near = True
                    break
        if not near:
            for h in self.extra.get("hammers") or []:
                if math.dist(h["pivot"], pos) < h["len"] + 8.0:
                    near = True
                    break
        if near or self._power(player, "feather") or self._power(player, "spring"):
            player.extra["launch_until"] = max(player.extra.get("launch_until", 0.0), moment + 1.6)

    def _fell(self, player: Player, moment: float) -> None:
        self.counts["falls"] += 1
        if player.extra.get("ss_done") is None:
            self._stat(player, "falls")
        hit = player.extra.pop("ss_bonked_by", None)
        if hit and moment - hit[1] <= RING_OUT_SECONDS:
            bonker = self.players.get(hit[0])
            if bonker is not None and bonker.team != player.team and bonker.team in self.TEAMS:
                self.counts["ring_outs"] += 1
                self.points[bonker.team] = self.points.get(bonker.team, 0) + RING_OUT_POINTS
                bonker.score += RING_OUT_POINTS
                self._stat(bonker, "ring_outs")
                self.badge(bonker, "ss_ring_outs")
                self.broadcast({"t": "ssx", "k": "ring_out", "by": bonker.pid, "who": player.pid})
                self._event("ss_ring_out", bonker, bonker.team, victim=player.username)
                self._broadcast_state()
        self._send_back(player, moment)
        self.broadcast({"t": "ssx", "k": "fell", "id": player.pid})
        if player.brain is not None:
            self.callout(player.brain, ["nooo", "missed it", "ugh", "again??", "that jump"],
                         "fell", chance=0.25, every=40.0)

    def _send_back(self, player: Player, moment: float) -> None:
        cp = int(player.extra.get("ss_cp", 0))
        if player.extra.get("ss_done") is not None and self.cps:
            mark = self.cps[-1]["p"]
        elif cp > 0 and cp <= len(self.cps):
            mark = self.cps[cp - 1]["p"]
        else:
            starts = self.spawn_points(player.team if player.team in self.TEAMS else "red")
            mark = list(starts[player.pid % len(starts)]["p"]) if starts else list(player.pos)
        spot = [mark[0] + self.rng.uniform(-2.0, 2.0), mark[1] + 0.2,
                mark[2] + self.rng.uniform(-2.0, 2.0)]
        player.pos = spot
        player.vel = [0.0, 0.0, 0.0]
        player.extra["tp_grace"] = moment + 1.0
        player.extra.pop("ss_push", None)
        if player.brain is not None:
            brain = player.brain
            brain.airborne = False
            brain.vy = 0.0
            brain.ground = list(spot)
            brain.waypoints = []
            mind = self._mind(player)
            mind["i"] = self._nearest_node(spot, cp + 1 if player.extra.get("ss_done") is None
                                           else len(self.cps))
            mind["wait_since"] = 0.0
            # home, and off the finish (or out running the course backwards):
            # back to standing about on it
            mind.pop("back", None)
            mind.pop("spot", None)
        else:
            player.send({"t": "tp", "p": [round(v, 2) for v in spot]})

    def _reach(self, player: Player, mark: Dict[str, Any], moment: float) -> None:
        index = int(mark["i"])
        player.extra["ss_cp"] = index
        team = player.team if player.team in self.TEAMS else ""
        first = index not in self.firsts
        if first:
            self.firsts[index] = player.pid
        self.counts["checkpoints"] += 1
        self._stat(player, "checkpoints")
        self.badge(player, "ss_checkpoints")
        gain = CP_POINTS + (FIRST_POINTS if first and not mark.get("finish") else 0)
        if first and not mark.get("finish"):
            self._stat(player, "firsts")
            self.badge(player, "ss_firsts")
        place = 0
        if mark.get("finish"):
            self.finished.append(player.pid)
            place = len(self.finished)
            player.extra["ss_done"] = round(moment - self.t0 - self.SETUP_SECONDS, 2)
            player.extra["ss_place"] = place
            gain += PLACE_POINTS[place - 1] if place <= len(PLACE_POINTS) else 0
            self.counts["finishes"] += 1
            self._stat(player, "finished")
            self.badge(player, "ss_finishes")
            if place == 1:
                self.badge(player, "ss_first_place")
            if place <= 3:
                self.badge(player, "ss_podium")
            if self.round_stats.get(player.pid, {}).get("falls", 0) == 0:
                self.badge(player, "ss_clean_run")
            self._event("ss_finish", player, team, place=place, n=place)
        if team:
            self.points[team] = self.points.get(team, 0) + gain
        player.score += gain
        self.broadcast({"t": "ssx", "k": "cp", "id": player.pid, "i": index, "first": first,
                        "finish": bool(mark.get("finish")), "place": place, "gain": gain,
                        "name": mark.get("name", "")})
        if first and not mark.get("finish"):
            self._event("ss_first_cp", player, team, n=index, place_name=mark.get("name", ""))
        self._broadcast_state()
        self._send_me(player, force=True)

    def _pick_up(self, player: Player, spot: Dict[str, Any], index: int, moment: float) -> None:
        kind = spot["kind"]
        spot["kind"] = ""
        spot["back"] = moment + POWER_RESPAWN
        self.counts["powers"] += 1
        self._stat(player, "powers")
        self.badge(player, "ss_powers")
        if kind == "rocket":
            player.extra["ss_rocket"] = min(2, int(player.extra.get("ss_rocket", 0)) + 1)
        else:
            pw = player.extra.setdefault("ss_pw", {})
            pw[kind] = moment + POWER_SECONDS.get(kind, 10.0)
        player.send({"t": "ssx", "k": "power", "kind": kind,
                     "for": POWER_SECONDS.get(kind, 0.0)})
        self.broadcast({"t": "ssx", "k": "took", "spot": index, "id": player.pid, "kind": kind},
                       exclude=player.pid)
        self._send_me(player, force=True)

    # ============================================================ the glove
    def custom_fire(self, player: Player, stats: Dict[str, Any],
                    direction: List[float], origin: List[float]) -> None:
        if stats.get("kind") != "ss_bonk":
            return
        self._bonk(player, direction)

    def _bonk(self, player: Player, direction: Sequence[float]) -> Optional[Player]:
        moment = engine.now()
        flat = normalise([direction[0], 0.0, direction[2]])
        # a racer bonks racers; one who is home only bonks rivals home too (a
        # scuffle on the finish while the rest come in, for no points)
        home = player.extra.get("ss_done") is not None
        best, best_s = None, 1e9
        for other in self.playing():
            if other is player or other.team == player.team or \
                    (other.extra.get("ss_done") is not None) != home:
                continue
            hit = other.extra.get("ss_bonked_by")
            if hit and moment - hit[1] < BONK_GRACE:
                continue
            dx, dz = other.pos[0] - player.pos[0], other.pos[2] - player.pos[2]
            d = math.hypot(dx, dz)
            if d > BONK_REACH or abs(other.pos[1] - player.pos[1]) > 4.0 or d < 1e-3:
                continue
            if (dx * flat[0] + dz * flat[2]) / d < 0.45:
                continue
            if d < best_s:
                best, best_s = other, d
        self.broadcast({"t": "ssx", "k": "swing", "id": player.pid,
                        "hit": best.pid if best is not None else 0})
        if best is None:
            return None
        if self._power(best, "shield"):
            self.broadcast({"t": "ssx", "k": "bubble", "id": best.pid})
            return None
        dx, dz = best.pos[0] - player.pos[0], best.pos[2] - player.pos[2]
        d = math.hypot(dx, dz) or 1.0
        self._knock(best, dx / d * BONK_FORCE, BONK_UP, dz / d * BONK_FORCE, moment)
        if home:
            self.counts["home_bonks"] += 1
            return best
        best.extra["ss_bonked_by"] = (player.pid, moment)
        self.counts["bonks"] += 1
        self._stat(player, "bonks")
        self.badge(player, "ss_bonks")
        return best

    def _knock(self, player: Player, vx: float, vy: float, vz: float, moment: float) -> None:
        player.extra["launch_until"] = moment + 1.6
        if player.brain is not None:
            brain = player.brain
            brain.airborne = True
            brain.vy = max(brain.vy, vy)
            player.extra["ss_push"] = (vx, vz, moment + 0.55)
            brain.waypoints = []
            return
        player.send({"t": "knock", "v": [round(vx, 2), round(vy, 2), round(vz, 2)]})

    def use(self, player: Player, message: Dict[str, Any]) -> None:
        """E: light the rocket, if there is one."""
        if self.phase != "active" or not self.in_play(player):
            return
        if int(player.extra.get("ss_rocket", 0)) <= 0:
            return
        player.extra["ss_rocket"] = int(player.extra["ss_rocket"]) - 1
        moment = engine.now()
        yaw = player.yaw
        self._knock(player, math.sin(yaw) * ROCKET_SPEED, ROCKET_UP, math.cos(yaw) * ROCKET_SPEED,
                    moment)
        player.extra["launch_until"] = moment + 2.2
        self.counts["rockets"] += 1
        self._stat(player, "rockets")
        self.badge(player, "ss_rockets")
        self.broadcast({"t": "ssx", "k": "rocket", "id": player.pid})
        self._send_me(player, force=True)

    def on_action(self, player: Player, message: Dict[str, Any]) -> None:
        kind = message.get("k")
        moment = engine.now()
        if kind == "zap":
            # a person's browser saw them touch a laser
            if self.phase == "active" and self.in_play(player) and not self._power(player, "shield"):
                self.counts["zaps"] += 1
                self._stat(player, "zaps")
                self.broadcast({"t": "ssx", "k": "zap", "id": player.pid})
                self._send_back(player, moment)
            return
        if kind == "hit":
            # knocked by a hammer or a sweeper on their own screen
            if self.in_play(player):
                self.counts["hits"] += 1
                self._stat(player, "hits")
                player.extra["launch_until"] = moment + 1.6
            return
        if kind == "pad":
            if self.in_play(player):
                self.counts["pads"] += 1
                player.extra["launch_until"] = moment + 2.6
            return
        super().on_action(player, message)

    # ============================================================ the bots
    def _mind(self, p: Player) -> Dict[str, Any]:
        return p.extra.setdefault("ss_mind", {"i": 0, "wait_since": 0.0, "bonk_at": 0.0,
                                              "detour": None})

    def _nearest_node(self, pos: Sequence[float], seg: int) -> int:
        best, best_d = 0, 1e9
        for k, node in enumerate(self.route):
            if node.get("seg", 1) != seg:
                continue
            d = math.dist(node["p"], pos)
            if d < best_d:
                best, best_d = k, d
        return best

    def _bot_body(self, player: Player, dt: float, moment: float) -> None:
        """What the course does to a bot's body (a person's browser does it
        to theirs): pads, belts, speed strips, wind, jelly, hammers,
        sweepers and lasers -- and, for the bot's own legs, when to jump."""
        brain = player.brain
        pos = player.pos
        grounded = not brain.airborne
        extra = self.extra
        shielded = self._power(player, "shield")
        push = [0.0, 0.0]
        if grounded:
            for pad in self.pads:
                if math.hypot(pos[0] - pad["p"][0], pos[2] - pad["p"][2]) < pad["r"] and \
                        abs(pos[1] - pad["p"][1]) < 0.7:
                    brain.airborne = True
                    brain.vy = float(pad["v"])
                    f = float(pad.get("f", 0.0))
                    if f:
                        player.extra["ss_push"] = (math.sin(pad["yaw"]) * f, math.cos(pad["yaw"]) * f,
                                                   moment + 1.5)
                    self.counts["pads"] += 1
                    self.broadcast({"t": "ssx", "k": "pad", "id": player.pid})
                    # up and away: on to the mark after this pad's
                    mind = self._mind(player)
                    i = int(mind.get("i", 0))
                    for k in range(i, min(len(self.route), i + 3)):
                        if self.route[k].get("how") == 2 and \
                                math.dist(self.route[k]["p"], pad["p"]) < pad["r"] + 1.0:
                            mind["i"] = k + 1
                            brain.waypoints = [list(self.route[m]["p"])
                                               for m in range(k + 1, min(len(self.route), k + 4))]
                            break
                    break
            sign = -1.0 if (self.twist["on"] and self.twist["kind"] == "reverse") else 1.0
            for belt in extra.get("belts") or []:
                if _in_rect(belt["rect"], pos) and abs(pos[1] - belt["y"]) < 0.5:
                    push[0] += belt["v"][0] * sign
                    push[1] += belt["v"][1] * sign
            for boost in self.boosts:
                if math.dist(boost["p"], pos) < boost["l"] / 2.0 + 0.5:
                    player.extra["ss_boost"] = moment + 0.9
            for zone in extra.get("jelly") or []:
                if _in_rect(zone["rect"], pos) and abs(pos[1] - zone["y"]) < 0.6:
                    brain.airborne = True
                    brain.vy = float(zone.get("v", 46.0))
        rate = self._rate("wind")
        wind = [0.0, 0.0]
        for zone in extra.get("wind") or []:
            if _in_rect(zone["rect"], pos) and -1.0 < pos[1] - zone["y"] < 14.0:
                k = 1.0 if (self.twist["on"] and self.twist["kind"] == "typhoon") else \
                    wind_now(zone, self.ht)
                if k > 0.0:
                    wind[0] += zone["dir"][0] * zone["strength"] * k * rate
                    wind[1] += zone["dir"][1] * zone["strength"] * k * rate
        player.extra["ss_drift"] = wind if (wind[0] or wind[1]) else None
        player.extra["ss_belt"] = push if (push[0] or push[1]) else None
        if shielded or moment < player.extra.get("ss_hit_at", 0.0) + HIT_COOL:
            pass
        else:
            t = self.ht
            for h in extra.get("hammers") or []:
                hit = hammer_hit(h, self.hc, pos)
                if hit:
                    player.extra["ss_hit_at"] = moment
                    self.counts["hits"] += 1
                    self._knock(player, hit[0] * HAMMER_KNOCK, KNOCK_UP, hit[1] * HAMMER_KNOCK, moment)
                    self.broadcast({"t": "ssx", "k": "thwack", "id": player.pid})
                    break
            for sw in extra.get("sweepers") or []:
                hit = sweeper_hit(sw, t, pos)
                if hit:
                    player.extra["ss_hit_at"] = moment
                    self.counts["hits"] += 1
                    self._knock(player, hit[0] * SWEEP_KNOCK, KNOCK_UP, hit[1] * SWEEP_KNOCK, moment)
                    self.broadcast({"t": "ssx", "k": "thwack", "id": player.pid})
                    break
            for lz in extra.get("lasers") or []:
                if laser_hit(lz, self.lc, pos):
                    self.counts["zaps"] += 1
                    self.broadcast({"t": "ssx", "k": "zap", "id": player.pid})
                    self._send_back(player, moment)
                    return
        if self.phase == "active" and player.extra.get("ss_done") is None:
            self._bot_legs(player, moment)

    def bot_push(self, player: Player) -> Optional[Tuple[float, float]]:
        moment = engine.now()
        vx = vz = 0.0
        push = player.extra.get("ss_push")
        if push and push[2] > moment:
            vx += push[0]
            vz += push[1]
        belt = player.extra.get("ss_belt")
        if belt:
            vx += belt[0]
            vz += belt[1]
        drift = player.extra.get("ss_drift")
        if drift:
            # a bot leans into the wind, the way a person steers against it:
            # most of it, the less skilled less so
            skill = self.pct("skill") * 0.6 + (player.brain.skill if player.brain else 0.5) * 0.4
            keep = 0.04 + 0.14 * (1.0 - skill)
            vx += drift[0] * keep
            vz += drift[1] * keep
        return (vx, vz) if (vx or vz) else None

    def bot_gravity(self, player: Player) -> float:
        # a feather: you fall slowly (going up is as usual)
        falling = player.brain is not None and player.brain.vy < 0.0
        return FEATHER_GRAVITY if falling and self._power(player, "feather") else 1.0

    def _bot_legs(self, player: Player, moment: float) -> None:
        """Along the line: when at a mark, wait out what is in the way, then
        go -- jumping off a jump mark -- and steer for the next few."""
        brain = player.brain
        mind = self._mind(player)
        route = self.route
        if not route:
            return
        i = max(0, min(len(route) - 1, int(mind.get("i", 0))))
        node = route[i]
        pos = player.pos
        np_ = node["p"]
        # lost the line (knocked off, carried away): find it again
        prev = route[i - 1]["p"] if i > 0 else np_
        if not brain.airborne and _off_leg(pos, prev, np_) > 14.0:
            cp = int(player.extra.get("ss_cp", 0))
            i = self._nearest_node(pos, cp + 1)
            mind["i"] = i
            node = route[i]
            np_ = node["p"]
        # a pad's mark is left by the pad, not on foot; and a bot that came
        # down short of the ledge above it goes back to the pad
        if i > 0 and route[i - 1].get("how") == 2 and not brain.airborne and \
                pos[1] < np_[1] - 6.0:
            i -= 1
            mind["i"] = i
            node = route[i]
            np_ = node["p"]
        # right under the mark (dropped on to the ram under a tile, say):
        # the way on is straight up
        rise = np_[1] - pos[1]
        if not brain.airborne and 2.3 < rise < 8.0 and \
                math.hypot(np_[0] - pos[0], np_[2] - pos[2]) < 2.2:
            brain.airborne = True
            brain.vy = JUMP_SPEED
        close = math.hypot(np_[0] - pos[0], np_[2] - pos[2]) < (1.6 if node.get("how") == 1 else 1.2)
        if close and node.get("how") == 2:
            close = False
        if close and abs(np_[1] - pos[1]) < 2.6 and not brain.airborne and i + 1 < len(route):
            nxt = route[i + 1]
            if not self._clear_to_go(player, node, nxt, moment):
                brain.waypoints = []
                if not mind.get("wait_since"):
                    mind["wait_since"] = moment
                self.doing(brain, "waiting for a gap")
                # patience runs out, and on a sweeper's deck a jump is the
                # answer anyway
                if moment - mind["wait_since"] > 2.5 + 6.0 * self.pct("patience"):
                    mind["wait_since"] = 0.0
                else:
                    return
            mind["wait_since"] = 0.0
            if node.get("how") == 1:
                spring = SPRING_SCALE if self._power(player, "spring") else 1.0
                if self.twist["on"] and self.twist["kind"] == "sugar_rush":
                    spring *= 1.15
                brain.airborne = True
                brain.vy = JUMP_SPEED * spring
                # a misjudged take-off: short, and down
                skill = self.pct("skill") * 0.7 + brain.skill * 0.3
                if brain.rng.random() < (1.0 - skill) * 0.14:
                    player.extra["ss_slow"] = moment + 1.1
            i += 1
            mind["i"] = i
        # sweepers and lasers: hop the arm or the beam as it arrives
        if not brain.airborne:
            hop = False
            for sw in self.extra.get("sweepers") or []:
                if math.dist(sw["c"], pos) < sw["r"] + 2.0 and sweeper_hit(sw, self.ht + 0.22, pos):
                    hop = True
                    break
            if not hop:
                ahead = self.lc + 0.2 * self._rate("laser")
                for lz in self.extra.get("lasers") or []:
                    if laser_hit(lz, ahead, pos):
                        hop = True
                        break
            if hop and brain.rng.random() < 0.55 + 0.45 * self.pct("skill"):
                brain.airborne = True
                brain.vy = JUMP_SPEED
        # a short way off the line for a power-up, then back on it
        detour = mind.get("detour")
        if detour is not None:
            spot = self.spots[detour[0]] if detour[0] < len(self.spots) else None
            if spot is None or not spot["kind"] or moment > detour[1] or \
                    math.dist(spot["p"], pos) < 1.5:
                mind["detour"] = None
            else:
                if not brain.waypoints or brain.waypoints[0] != list(spot["p"]):
                    brain.waypoints = [list(spot["p"])] + [list(route[k]["p"])
                                                          for k in range(i, min(len(route), i + 2))]
                return
        if not brain.waypoints or brain.waypoints[0] != list(route[i]["p"]):
            brain.waypoints = [list(route[k]["p"]) for k in range(i, min(len(route), i + 3))]

    def _clear_to_go(self, player: Player, node: Dict[str, Any], nxt: Dict[str, Any],
                     moment: float) -> bool:
        """Will the way from ``node`` to ``nxt`` be clear while we cross it?"""
        haz, group, tiles = node.get("haz"), node.get("blink"), node.get("crumble")
        if haz is None and group is None and not tiles:
            return True
        if tiles:
            # a crumbling bridge: wait for all of it to be there, then run
            for key in tiles:
                state = self.crumbled.get(key)
                if state is not None and (state["back"] or state["at"]):
                    return False
        a, b = node["p"], nxt["p"]
        span = math.hypot(b[0] - a[0], b[2] - a[2])
        cross = span / 22.0 + (0.45 if node.get("how") == 1 else 0.1)
        if group is not None:
            spec = next((s for s in self.extra.get("blink") or [] if s["group"] == group), None)
            if spec is not None:
                rate = self._rate("beat")
                land = self.bt + cross * rate
                if not (blink_on(spec, land) and blink_on(spec, land + 0.45 * rate)):
                    return False
        if haz is not None:
            t = self.ht
            for step in range(9):
                tau = cross * step / 8.0 + 0.1
                f = min(1.0, tau / max(0.05, cross))
                p = [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f]
                for h in self.extra.get("hammers") or []:
                    if h.get("id") == haz and hammer_hit(h, self.hc + tau * self._rate("hammer"),
                                                         p):
                        return False
                for sw in self.extra.get("sweepers") or []:
                    # inside an arm's reach already: keep going and hop it
                    if sw.get("id") == haz and math.dist(sw["c"], player.pos) > sw["r"] + 1.5 \
                            and sweeper_hit(sw, t + tau, p):
                        return False
                for lz in self.extra.get("lasers") or []:
                    if lz.get("id") == haz and laser_hit(lz, self.lc + tau * self._rate("laser"),
                                                         p):
                        return False
        return True

    def bot_role(self, brain) -> str:
        return "racer"

    def bot_goal_weights(self, brain, weights: Dict[str, float]) -> Dict[str, float]:
        for key in list(weights):
            weights[key] = 0.0
        weights["objective"] = 1.0
        return weights

    def bot_urgent(self, brain) -> bool:
        return True

    def bot_tick(self, moment: float) -> None:
        """Nothing extra: a bot's body and legs are moved in round_tick."""

    def bot_objective(self, brain) -> None:
        p = brain.p
        moment = engine.now()
        if not self.setting("enabled"):
            return
        mind = self._mind(p)
        if self.phase != "active":
            self.doing(brain, "waiting at the gate")
            return
        if p.extra.get("ss_done") is not None:
            self._bot_home(brain, mind, moment)
            return
        # a rival close by on our part of the course: bonk them
        if moment >= mind.get("bonk_at", 0.0) and brain.rng.random() < 0.02 + 0.1 * self.pct("bonk"):
            for other in self.playing():
                if other.team == p.team or other.extra.get("ss_done") is not None:
                    continue
                hit = other.extra.get("ss_bonked_by")
                if hit and moment - hit[1] < BONK_GRACE:
                    continue
                d = math.hypot(other.pos[0] - p.pos[0], other.pos[2] - p.pos[2])
                if d < BONK_REACH - 1.0 and abs(other.pos[1] - p.pos[1]) < 3.0:
                    yaw = math.atan2(other.pos[0] - p.pos[0], other.pos[2] - p.pos[2])
                    p.yaw = yaw
                    mind["bonk_at"] = moment + BONK_COOL + brain.rng.uniform(1.5, 4.5)
                    if self._bonk(p, [math.sin(yaw), 0.0, math.cos(yaw)]):
                        self.callout(brain, ["bonk", "byeee", "get bonked", "move", "outta my way"],
                                     "bonk", chance=0.35, every=30.0)
                    break
        # a rocket on a long straight: light it
        rockets = int(p.extra.get("ss_rocket", 0))
        if rockets and brain.rng.random() < 0.08 + 0.3 * self.pct("powerups"):
            i = int(mind.get("i", 0))
            if i + 2 < len(self.route):
                a, b = self.route[i]["p"], self.route[i + 1]["p"]
                if self.route[i].get("how") == 0 and abs(b[1] - a[1]) < 1.0 and \
                        math.hypot(b[0] - a[0], b[2] - a[2]) > 20.0 and not self.route[i].get("haz"):
                    p.yaw = math.atan2(b[0] - p.pos[0], b[2] - p.pos[2])
                    self.use(p, {})
        # a power-up close to the line
        if self.pct("powerups") > 0.05 and mind.get("detour") is None:
            for k, spot in enumerate(self.spots):
                if spot["kind"] and math.dist(spot["p"], p.pos) < 12.0 * self.pct("powerups") + 3.0 \
                        and abs(spot["p"][1] - p.pos[1]) < 1.0 and not brain.airborne:
                    mind["detour"] = (k, moment + 4.0)
                    self.doing(brain, "grabbing %s" % POWER_NAMES.get(spot["kind"], "a power-up"))
                    return
        cp = int(p.extra.get("ss_cp", 0))
        nxt = self.cps[cp]["name"] if cp < len(self.cps) else "the finish"
        self.doing(brain, "racing for %s" % nxt)

    # ---- home: the finish while the rest come in
    def _post_style(self, brain, mind: Dict[str, Any]) -> str:
        """What a racer does once it is home, from its persona: most hang about
        and watch, the friendly cheer their team in from the edge, show-offs
        hop and spin, the pushy square up to rivals who are home too, and now
        and then an explorer goes back down the course for the fun of it."""
        style = mind.get("post")
        if style is None:
            weights = {
                "idle": 0.9,
                "cheer": 0.2 + brain.t("social", 0.5) * 0.6 + brain.t("support", 0.2) * 0.8,
                "show": 0.08 + brain.t("jumpy", 0.2) * 1.2 + brain.t("chaos", 0.08) * 1.0,
                "bump": 0.04 + brain.t("aggression", 0.5) * 0.5 + brain.t("chaos", 0.08) * 1.4,
                "back": 0.02 + brain.t("explore", 0.2) * 0.25 + brain.t("chaos", 0.08) * 0.3,
            }
            style = brain.rng.choices(list(weights), list(weights.values()))[0]
            mind["post"] = style
            mind["home_at"] = engine.now()
        return style

    def _floor_top(self, x: float, y: float, z: float) -> Optional[float]:
        """The top of the solid under (x, z) within a step of ``y`` -- if a
        body could stand there (no post or arch leg in the way above it)."""
        top = None
        for lo, hi in self._colliders_near([x - 0.05, y - 1.6, z - 0.05], [x + 0.05, y + 5.0, z + 0.05]):
            if not (lo[0] <= x <= hi[0] and lo[2] <= z <= hi[2]):
                continue
            if hi[1] <= y + 1.0:
                if hi[1] >= y - 1.6:
                    top = hi[1] if top is None else max(top, hi[1])
            elif lo[1] < y + 5.0:
                return None
        return top

    def _home_spots(self) -> List[List[float]]:
        """Places to stand on the finish: well in from its edges, clear of its
        posts and of anything that would launch you (worked out once a round)."""
        key = (self.area_id, self.round_number)
        cached = getattr(self, "_homes", None)
        if cached is not None and cached[0] == key:
            return cached[1]
        spots: List[List[float]] = []
        if self.cps:
            c = self.cps[-1]["p"]
            for i in range(-11, 12):
                for j in range(-11, 12):
                    if (i * i + j * j) * 4.0 > 22.0 ** 2:
                        continue
                    x, z = c[0] + i * 2.0, c[2] + j * 2.0
                    top = self._floor_top(x, c[1], z)
                    if top is None or any(self._floor_top(x + ox, top, z + oz) is None
                                          for ox, oz in ((2.4, 0.0), (-2.4, 0.0), (0.0, 2.4), (0.0, -2.4))):
                        continue
                    if any(math.hypot(x - pad["p"][0], z - pad["p"][2]) < pad["r"] + 2.0 for pad in self.pads):
                        continue
                    if any(_in_rect(zone["rect"], [x, top, z], 1.5)
                           for kind in ("belts", "jelly", "wind", "taffy")
                           for zone in self.extra.get(kind) or []):
                        continue
                    spots.append([x, top, z])
        self._homes = (key, spots)
        return spots

    def _bot_home(self, brain, mind: Dict[str, Any], moment: float) -> None:
        p = brain.p
        style = self._post_style(brain, mind)
        back = mind.get("back")
        if back is not None and self._bot_back(brain, mind, back):
            return
        homes = [o for o in self.playing() if o is not p and o.extra.get("ss_done") is not None]
        self._cheer_finishers(brain, mind)
        if style == "bump" and self._bot_bump(brain, mind, homes, moment):
            return
        if style == "back" and not mind.get("went_back") and moment > mind.get("home_at", 0.0) + 3.0:
            mind["went_back"] = True
            mind["back"] = {"j": len(self.route) - 1, "left": brain.rng.randint(3, 8), "out": True}
            self.callout(brain, ["going back for fun", "one more time", "brb", "speedrun it backwards"],
                         "back", chance=0.4, every=120.0)
            return
        spots = self._home_spots()
        if not spots:
            brain.waypoints = []
            self.doing(brain, "home, watching the others")
            return
        spot = mind.get("spot")
        if spot is None or moment >= mind.get("spot_until", 0.0):
            spot = self._pick_home(brain, style, spots, homes)
            lo, hi = {"show": (3.0, 7.0), "cheer": (15.0, 40.0), "bump": (5.0, 10.0)}.get(style, (8.0, 22.0))
            mind["spot"] = spot
            mind["spot_until"] = moment + brain.rng.uniform(lo, hi)
        d = math.hypot(spot[0] - p.pos[0], spot[2] - p.pos[2])
        if d > 1.2:
            # walking over (and if something is in the way, somewhere else)
            best = mind.get("spot_best")
            if best is None or best[2] is not spot or d < best[0] - 0.5:
                mind["spot_best"] = (d, moment, spot)
            elif moment - best[1] > 2.5:
                mind.pop("spot", None)
                mind.pop("spot_best", None)
            brain.waypoints = [list(spot)]
            self.doing(brain, "finding a spot on the finish")
            return
        brain.waypoints = []
        self._watch_the_race(brain, mind, style, moment)

    def _pick_home(self, brain, style: str, spots: List[List[float]], homes: List[Player]) -> List[float]:
        """A spot of its own: the cheerers at the edge the racers come in
        over, everybody else anywhere -- not on top of anybody."""
        p = brain.p
        come = self.route[max(0, len(self.route) - 4)]["p"] if self.route else p.pos
        taken = [o.pos for o in homes] + [self._mind(o).get("spot") for o in homes if o.brain is not None]
        best, best_s = spots[0], -1e9
        for q in spots:
            s = brain.rng.uniform(0.0, 10.0)
            near = min([math.hypot(q[0] - t[0], q[2] - t[2]) for t in taken if t is not None] or [99.0])
            s += min(near, 8.0) * 3.0
            if style == "cheer":
                s -= math.hypot(q[0] - come[0], q[2] - come[2]) * 1.5
            if s > best_s:
                best, best_s = q, s
        return list(best)

    def _watch_the_race(self, brain, mind: Dict[str, Any], style: str, moment: float) -> None:
        """Stood on its spot: eyes on the racers still coming (the nearest of
        its own team, for a cheerer), and whatever its temperament does with
        its hands and feet."""
        p = brain.p
        racing = [o for o in self.playing() if o.extra.get("ss_done") is None and o.team in self.TEAMS]
        mine = [o for o in racing if o.team == p.team]
        grounded = not brain.airborne
        if style == "show":
            # a little show for anybody watching: hops, and spins on the spot
            if grounded and brain.rng.random() < 0.12:
                brain.airborne = True
                brain.vy = JUMP_SPEED
            if moment >= mind.get("spin_at", 0.0):
                mind["spin_at"] = moment + brain.rng.uniform(0.25, 0.5)
                brain.look_yaw = p.yaw + 2.2 * (1.0 if p.pid % 2 else -1.0)
            self.doing(brain, "showing off on the finish")
            return
        watch = (mine if style == "cheer" and mine else racing) or []
        if watch:
            them = min(watch, key=lambda o: math.dist(o.pos, p.pos))
            if moment >= mind.get("glance_at", 0.0):
                mind["glance_at"] = moment + brain.rng.uniform(0.6, 2.0)
                brain.look_yaw = math.atan2(them.pos[0] - p.pos[0], them.pos[2] - p.pos[2]) + \
                    brain.rng.uniform(-0.25, 0.25)
            if style == "cheer" and them.team == p.team and math.dist(them.pos, p.pos) < 50.0:
                if grounded and brain.rng.random() < 0.08:
                    brain.airborne = True
                    brain.vy = JUMP_SPEED
                self.callout(brain, ["come on %s" % them.username, "GO GO GO", "almost there",
                                     "you got this %s" % them.username, "jump!!"],
                             "cheer%d" % them.pid, chance=0.4, every=30.0)
                self.doing(brain, "cheering %s in" % them.username)
                return
            self.doing(brain, "watching %s come in" % them.username if style != "cheer"
                       else "cheering the team on")
        else:
            if moment >= mind.get("glance_at", 0.0):
                mind["glance_at"] = moment + brain.rng.uniform(1.0, 3.0)
                brain.look_yaw = p.yaw + brain.rng.uniform(-1.5, 1.5)
            self.doing(brain, "home, watching the others")
        # an idle hop or two, by temperament
        if grounded and brain.rng.random() < 0.01 + 0.03 * brain.t("jumpy", 0.2):
            brain.airborne = True
            brain.vy = JUMP_SPEED

    def _cheer_finishers(self, brain, mind: Dict[str, Any]) -> None:
        """Somebody just got home: a teammate gets a hop and a word."""
        seen = int(mind.get("seen_home", 0))
        if seen >= len(self.finished):
            return
        mind["seen_home"] = len(self.finished)
        p = brain.p
        for pid in self.finished[seen:]:
            other = self.players.get(pid)
            if other is None or other is p or other.team != p.team:
                continue
            if not brain.airborne and brain.rng.random() < 0.5 + 0.4 * brain.t("social", 0.5):
                brain.airborne = True
                brain.vy = JUMP_SPEED
            self.callout(brain, ["gg %s" % other.username, "nice %s" % other.username, "lets gooo",
                                 "WOO", "welcome home"], "welcome", chance=0.35, every=20.0)

    def _bot_bump(self, brain, mind: Dict[str, Any], homes: List[Player], moment: float) -> bool:
        """A scuffle on the finish: walk up to a rival who is home too and bonk
        them off it (it scores nothing -- they land back on the finish)."""
        p = brain.p
        if moment < mind.get("bump_rest", 0.0):
            return False
        rivals = [o for o in homes if o.team != p.team and abs(o.pos[1] - p.pos[1]) < 4.0 and
                  math.hypot(o.pos[0] - p.pos[0], o.pos[2] - p.pos[2]) < 30.0]
        if not rivals:
            return False
        them = self.players.get(mind.get("bump_on", 0))
        if them not in rivals or moment > mind.get("bump_until", 0.0):
            them = brain.rng.choice(rivals)
            mind["bump_on"] = them.pid
            mind["bump_until"] = moment + brain.rng.uniform(8.0, 16.0)
        d = math.hypot(them.pos[0] - p.pos[0], them.pos[2] - p.pos[2])
        yaw = math.atan2(them.pos[0] - p.pos[0], them.pos[2] - p.pos[2])
        if d > BONK_REACH - 1.5:
            brain.waypoints = [[them.pos[0], p.pos[1], them.pos[2]]]
            brain.look_yaw = yaw
            self.doing(brain, "squaring up to %s" % them.username)
            return True
        brain.waypoints = []
        p.yaw = yaw
        brain.look_yaw = yaw
        if moment >= mind.get("bonk_at", 0.0):
            mind["bonk_at"] = moment + BONK_COOL + brain.rng.uniform(0.6, 2.0)
            if self._bonk(p, [math.sin(yaw), 0.0, math.cos(yaw)]):
                mind["bump_rest"] = moment + brain.rng.uniform(4.0, 10.0)
                self.callout(brain, ["get off my finish", "bonk", "move over", "byeee", "my spot"],
                             "bump", chance=0.4, every=25.0)
        self.doing(brain, "bonking %s off the finish" % them.username)
        return True

    def _bot_back(self, brain, mind: Dict[str, Any], back: Dict[str, Any]) -> bool:
        """Back down the course a few marks for the fun of it -- only the legs
        anybody can run either way (no pads, hazards or tiles that come and
        go) -- and home again.  A fall just puts it back on the finish."""
        p = brain.p
        route = self.route
        j = int(back["j"])
        k = j + (-1 if back["out"] else 1)
        if back["out"] and (back["left"] <= 0 or k < 0 or not self._two_way(route[k], route[j])):
            back["out"] = False
            return True
        if k >= len(route):
            mind.pop("back", None)
            mind.pop("spot", None)
            return False
        target = route[k]["p"]
        if not brain.airborne and math.hypot(target[0] - p.pos[0], target[2] - p.pos[2]) < 1.6 and \
                abs(target[1] - p.pos[1]) < 2.6:
            back["j"] = k
            if back["out"]:
                back["left"] -= 1
            return True
        here = route[j]["p"]
        if route[min(j, k)].get("how") == 1 and not brain.airborne and \
                math.hypot(here[0] - p.pos[0], here[2] - p.pos[2]) < 1.8:
            brain.airborne = True
            brain.vy = JUMP_SPEED
        brain.waypoints = [list(target)]
        self.doing(brain, "running the course backwards" if back["out"] else "on the way home again")
        return True

    @staticmethod
    def _two_way(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        """Can the leg from mark ``a`` to the next one, ``b``, be run back the
        other way?"""
        if a.get("how", 0) not in (0, 1) or a.get("haz") is not None or a.get("blink") is not None \
                or a.get("crumble"):
            return False
        rise = a["p"][1] - b["p"][1]
        return rise < 4.5 and math.hypot(a["p"][0] - b["p"][0], a["p"][2] - b["p"][2]) < 24.0

    def bot_context(self) -> List[str]:
        lines = ["You are playing Sky Sprint, an obstacle-course race in two teams: reach "
                 "checkpoints and the finish for points; bonk rivals off the course."]
        lines.append("Points: %s %d, %s %d. Finished: %d." % (
            self.team_name("red"), self.points.get("red", 0), self.team_name("blue"),
            self.points.get("blue", 0), len(self.finished)))
        return lines

    def bot_me(self, brain) -> Dict[str, Any]:
        p = brain.p
        return {"checkpoint": int(p.extra.get("ss_cp", 0)),
                "finished": p.extra.get("ss_place") or 0,
                "doing": p.extra.get("bot_doing", "")}

    def bot_spread(self, players: List[Player]) -> None:
        """Nothing to balance: everybody races."""

    # ============================================================ progress
    def _progress(self, player: Player) -> None:
        """How far round the course a racer is, 0 to 1, for the bar."""
        if player.extra.get("ss_done") is not None:
            player.extra["ss_prog"] = 1.0
            return
        if not self.route:
            return
        cp = int(player.extra.get("ss_cp", 0))
        if player.brain is not None:
            i = int(self._mind(player).get("i", 0))
        else:
            i = self._nearest_node(player.pos, cp + 1)
        player.extra["ss_node"] = i
        player.extra["ss_prog"] = round(min(0.99, i / max(1, len(self.route) - 1)), 3)

    # ============================================================== state
    def _stat(self, player: Player, key: str, amount: float = 1.0) -> None:
        stats = self.round_stats.setdefault(player.pid, {})
        stats[key] = stats.get(key, 0.0) + amount

    def _place(self, pos: Sequence[float]) -> str:
        best, best_d = "", 1e9
        for p, name in self.landmarks:
            d = math.hypot(p[0] - pos[0], p[2] - pos[2])
            if d < best_d:
                best, best_d = name, d
        return best

    def _event(self, kind: str, player: Optional[Player], team: str, **extra: Any) -> None:
        moment = engine.now()
        if moment - self.events_said.get(kind, -99.0) < 6.0:
            return
        self.events_said[kind] = moment
        data = {"world": "sky_sprint", "by": player.username if player else "",
                "by_team": team, "team": team}
        data.update(extra)
        if self.bots is not None:
            self.bots.on_game_event(kind, data)

    def _broadcast_state(self) -> None:
        self.broadcast({"t": "sss", "s": self.hud_state()})

    def hud_state(self) -> Dict[str, Any]:
        moment = engine.now()
        tw = self.twist
        return {"ss": {"pts": dict(self.points), "cps": len(self.cps), "done": len(self.finished),
                       "racers": sum(1 for p in self.playing() if p.team in self.TEAMS),
                       "hurry": round(max(0.0, self.hurry_until - moment), 1) if self.hurry_until
                       else 0, "twist": tw["kind"], "on": tw["on"],
                       "left": round(max(0.0, tw["until"] - moment), 1) if tw["on"] else 0}}

    def snapshot_extra(self) -> Any:
        if self.phase not in ("active", "setup"):
            return None
        out: Dict[str, Any] = {"ht": round(self.ht, 3), "hc": round(self.hc, 3),
                               "lc": round(self.lc, 3), "bt": round(self.bt, 3),
                               "rate": [self._rate("hammer"), self._rate("beat"),
                                        self._rate("laser"), self._rate("wind")]}
        # progress, checkpoint, place, and what they are carrying (1 spring
        # shoes, 2 a feather, 4 a bubble, 8 a rocket) for everybody to see
        out["pr"] = {str(p.pid): [p.extra.get("ss_prog", 0.0), int(p.extra.get("ss_cp", 0)),
                                  int(p.extra.get("ss_place") or 0), self._flags(p)]
                     for p in self.playing()}
        out["pw"] = [[k, s["kind"]] for k, s in enumerate(self.spots) if s["kind"]]
        if self.twist["on"]:
            out["tw"] = self.twist["kind"]
        return out

    def _flags(self, player: Player) -> int:
        flags = 0
        for bit, kind in ((1, "spring"), (2, "feather"), (4, "shield")):
            if self._power(player, kind):
                flags |= bit
        if int(player.extra.get("ss_rocket", 0)) > 0:
            flags |= 8
        return flags

    def me_state(self, player: Player) -> Dict[str, Any]:
        moment = engine.now()
        pw = {k: round(v - moment, 1) for k, v in (player.extra.get("ss_pw") or {}).items()
              if v > moment}
        return {"cp": int(player.extra.get("ss_cp", 0)), "place": player.extra.get("ss_place") or 0,
                "time": player.extra.get("ss_done") or 0, "pw": pw,
                "rocket": int(player.extra.get("ss_rocket", 0))}

    def score_row(self, player: Player, row: Dict[str, Any]) -> None:
        row["cp"] = int(player.extra.get("ss_cp", 0))
        row["place"] = player.extra.get("ss_place") or 0

    def result_columns(self) -> List[List[str]]:
        return [["place", "Place"], ["time", "Time"], ["cps", "Checkpoints"], ["bonks", "Bonks"],
                ["falls", "Falls"], ["score", "Points"]]

    def results_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for p in self.players.values():
            if p.team not in self.TEAMS:
                continue
            stats = self.round_stats.get(p.pid, {})
            place = p.extra.get("ss_place") or 0
            t = p.extra.get("ss_done")
            rows.append({"id": p.pid, "name": p.username, "team": p.team, "score": p.score,
                         "place": ("%d" % place) if place else "-",
                         "time": ("%d:%04.1f" % (int(t // 60), t % 60)) if t else "-",
                         "cps": int(p.extra.get("ss_cp", 0)), "bonks": int(stats.get("bonks", 0)),
                         "falls": int(stats.get("falls", 0)), "_place": place or 99,
                         "_cp": int(p.extra.get("ss_cp", 0))})
        rows.sort(key=lambda r: (r["_place"], -r["_cp"], -r["score"], r["name"]))
        for r in rows:
            r.pop("_place")
            r.pop("_cp")
        return rows

    def awards(self, winner: str) -> List[str]:
        out = []
        if self.finished:
            first = self.players.get(self.finished[0])
            if first is not None:
                out.append("Fastest: %s (%s)" % (first.username, first.extra.get("ss_done")))
        bonks = sorted(((s.get("bonks", 0), pid) for pid, s in self.round_stats.items()),
                       reverse=True)
        if bonks and bonks[0][0] >= 2:
            who = self.players.get(bonks[0][1])
            if who is not None:
                out.append("Heavy hands: %s (%d bonks)" % (who.username, bonks[0][0]))
        return out

    def result_extra(self, winner: str) -> Dict[str, Any]:
        return {"points": dict(self.points)}

    def on_round_over(self, winner: str, reason: str, winners: List[Player]) -> None:
        for player in winners:
            self.badge(player, "ss_wins")
            self.badge(player, "ss_area_" + self.area_id, 1, "max")

    def describe(self) -> Dict[str, Any]:
        out = super().describe()
        out["points"] = dict(self.points)
        return out

    def observe(self) -> Dict[str, Any]:
        return {"done": len(self.finished), "ht": round(self.ht, 1),
                "cps": {p.username: int(p.extra.get("ss_cp", 0)) for p in self.playing()}}

    def selftest(self, result: Dict[str, Any]) -> List[Tuple[str, bool, Any]]:
        c = self.counts
        return [
            ("racers reach checkpoints", c["checkpoints"] >= 10, c["checkpoints"]),
            ("racers finish", c["finishes"] >= 2, dict(c)),
            ("the glove bonks", c["bonks"] >= 1, c["bonks"]),
            ("power-ups are taken", c["powers"] >= 1, c["powers"]),
            ("the course knocks people about", c["hits"] + c["falls"] >= 1, c["hits"]),
        ]


WORLD_CLASS = SkySprintWorld
