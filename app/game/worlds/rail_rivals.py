"""Rail Rivals: a payload race (app/models/event_worlds/rail_rivals.py).

Each team has an ore cart on a track of its own -- lane ``a`` or ``b`` of
the area's two (app/game/maps/events/rail_rivals/rails.py) -- and the first
cart to the far end of its line wins the race.  The teams swap tracks for
an area's second race, so neither ever has the better line twice.

**The cart** rolls while somebody of its own team stands by it and nobody of
the other team does (one of them by it and it is *contested*: it stops).
More pushers, more speed.  Leave it alone and after a while it rolls back
-- never behind the last depot it passed.  Every depot passed moves the
team's spawns up the line (``spawn_stage``).

**Brake levers** stand beside every track.  Somebody of the *other* team
holding E at one for a moment locks that track's cart for a while; its own
team frees it by holding E at the same lever.  A lever cools down after.

**Coal**: hold E at a heap for a sack, and E by your own cart to stoke it --
it runs half as fast again for a while.

**The twists**, one per area, named by the area's ``extra["twist"]``:

``signal``    Dustbowl Gulch's signal cabin: hold it, alone, for a few
              seconds and the junction signal is set against the other cart,
              which stops at the diamond until the signal clears.
``drifts``    Silverpine Pass: drifts come down across the track ahead of a
              cart; it stops at one until its own team digs it out (E).
``bridges``   Redrock Mesa: the other team can winch a line's lift bridge up
              from its cabin; the cart stops at the bank until it comes down
              (on its own, or the owners winch it).  The river kills.
``firedamp``  Lantern Deep: a gas pocket vents (a warning, then the blast)
              every so often; the lava kills.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import instance as engine
from ..instance import Player
from ..maps.events import rail_rivals as rr_map
from .arena import ArenaWorld

LANES = ("a", "b")
PUSH_R = 10.0             # how close a pusher (or a contester) stands
PUSH_DY = 7.0
BASE_SPEED = 3.4          # units a second, one pusher
CREW = (0.0, 1.0, 1.28, 1.48, 1.62)
ROLLBACK_AFTER = 12.0
ROLLBACK_SPEED = 1.3
STOKE_BOOST = 1.5
STOKE_SECONDS = 10.0
STOKE_CAP = 24.0
BRAKE_SECONDS = 9.0
LEVER_R = 4.6
LEVER_HOLD = 1.6
RELEASE_HOLD = 1.0
LEVER_COOL = 16.0
COAL_R = 6.0
COAL_HOLD = 0.8
STOKE_R = 9.0
SIGNAL_HOLD = 3.0
SIGNAL_SECONDS = 22.0
SIGNAL_REST = 14.0
DIAMOND = 18.0            # how far short of the crossing a held cart stops
DRIFT_EVERY = (38.0, 55.0)
DRIFT_DIG = 4.0           # dig-seconds a drift takes (two diggers: half)
DRIFT_R = 7.0
WINCH_R = 5.0
WINCH_RAISE = 2.4
WINCH_LOWER = 1.4
BRIDGE_WARN = 2.0
BRIDGE_UP = 18.0
BRIDGE_REST = 15.0
GAS_EVERY = (34.0, 48.0)
GAS_WARN = 6.0
GAS_R = 12.0
GAS_EDGE = 18.0
# what a bot says when it takes on an errand
JOB_LINES = {"release": ["brakes on our cart", "freeing the brakes", "on the lever"],
             "dig": ["digging us out", "drift on our line"],
             "lower": ["lowering our bridge", "our bridge is up, on it"],
             "brake": ["braking their cart", "pulling their brakes"],
             "signal": ["taking the signal", "signal cabin"],
             "raise": ["winching their bridge", "their bridge is going up lol"],
             "coal": ["getting coal", "coal run"]}
DEFAULTS: Dict[str, Any] = {}


def _defaults() -> Dict[str, Any]:
    if not DEFAULTS:
        from ...models.event_worlds import rail_rivals as meta
        for spec in meta.BOT_FIELDS:
            DEFAULTS[spec[0]] = spec[3]
    return DEFAULTS


# ===================================================================== lane
class Lane:
    """One track as the cart sees it: a polyline in world coordinates and
    the distance along it."""

    def __init__(self, points: Sequence[Sequence[float]]):
        self.pts = [(float(p[0]), float(p[2])) for p in points]
        self.cum = [0.0]
        for i in range(len(self.pts) - 1):
            (ax, az), (bx, bz) = self.pts[i], self.pts[i + 1]
            self.cum.append(self.cum[-1] + math.hypot(bx - ax, bz - az))
        self.length = self.cum[-1]

    def at(self, d: float) -> Tuple[float, float, float]:
        """(x, z, yaw) at distance ``d`` along the track."""
        d = max(0.0, min(self.length, d))
        lo, hi = 0, len(self.cum) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.cum[mid] <= d:
                lo = mid
            else:
                hi = mid
        (ax, az), (bx, bz) = self.pts[lo], self.pts[hi]
        seg = self.cum[hi] - self.cum[lo]
        f = 0.0 if seg <= 0 else (d - self.cum[lo]) / seg
        return (ax + (bx - ax) * f, az + (bz - az) * f, math.atan2(bx - ax, bz - az))

    def project(self, x: float, z: float) -> Tuple[float, float]:
        """(distance along the track, distance from it) of the nearest point."""
        best_d, best_off = 0.0, 1e9
        for i in range(len(self.pts) - 1):
            (ax, az), (bx, bz) = self.pts[i], self.pts[i + 1]
            dx, dz = bx - ax, bz - az
            seg = dx * dx + dz * dz
            f = 0.0 if seg <= 0 else max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / seg))
            off = math.hypot(ax + dx * f - x, az + dz * f - z)
            if off < best_off:
                best_off = off
                best_d = self.cum[i] + f * math.sqrt(seg)
        return best_d, best_off


def _crossing(a: Lane, b: Lane) -> Tuple[float, float]:
    """Where the two tracks cross: the distance along each."""
    for i in range(len(a.pts) - 1):
        (p0x, p0z), (p1x, p1z) = a.pts[i], a.pts[i + 1]
        for j in range(len(b.pts) - 1):
            (q0x, q0z), (q1x, q1z) = b.pts[j], b.pts[j + 1]
            rx, rz = p1x - p0x, p1z - p0z
            sx, sz = q1x - q0x, q1z - q0z
            den = rx * sz - rz * sx
            if abs(den) < 1e-9:
                continue
            t = ((q0x - p0x) * sz - (q0z - p0z) * sx) / den
            u = ((q0x - p0x) * rz - (q0z - p0z) * rx) / den
            if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
                return (a.cum[i] + t * (a.cum[i + 1] - a.cum[i]),
                        b.cum[j] + u * (b.cum[j + 1] - b.cum[j]))
    return a.length / 2.0, b.length / 2.0


# ===================================================================== cart
class Cart:
    def __init__(self, team: str, lane: str, path: Lane):
        self.team = team
        self.lane = lane
        self.path = path
        self.d = 0.0
        self.speed = 0.0
        self.pushers: List[int] = []
        self.contested = False
        self.brake_until = 0.0
        self.brake_lever = -1
        self.stoke_until = 0.0
        self.idle_since = engine.now()
        self.held = ""            # why it is stopped short: signal, drift, bridge
        self.passed = 0           # depots behind it
        self.contest_said = 0.0
        self.moved_by: Dict[int, float] = {}

    @property
    def fraction(self) -> float:
        return self.d / self.path.length if self.path.length else 0.0

    def pos(self) -> List[float]:
        x, z, _ = self.path.at(self.d)
        return [x, 0.0, z]


# ==================================================================== world
class RailRivalsWorld(ArenaWorld):
    MAP = rr_map
    TEAMS = ("red", "blue")
    TEAM_NAMES = {"red": "Crimson Line", "blue": "Bluebird Express"}
    ROUNDS_PER_AREA = 2
    SETUP_SECONDS = 12.0
    ROUND_SECONDS = 330.0
    RESULTS_SECONDS = 15.0
    LOGO = "Rail Rivals"
    FREEZE_COUNTDOWN = True
    respawn_seconds = 6.0
    BOT_CHATTER = ["push", "on the cart", "push the cart", "contest", "brakes",
                   "coal", "gg", "lets go", "go go", "anyone pushing"]

    # ------------------------------------------------------------ settings
    def setting(self, key: str) -> Any:
        cfg = getattr(self.bots, "cfg", None) if self.bots is not None else None
        value = (cfg or {}).get("rail_rivals_" + key)
        return _defaults().get(key) if value is None else value

    def pct(self, key: str) -> float:
        try:
            return max(0.0, min(1.0, float(self.setting(key)) / 100.0))
        except (TypeError, ValueError):
            return 0.5

    # ================================================================ setup
    def world_setup(self) -> None:
        self.carts: Dict[str, Cart] = {}
        self.lanes: Dict[str, Lane] = {}
        self.depots: Dict[str, List[Tuple[float, str]]] = {}
        self.levers: Dict[str, List[Dict[str, Any]]] = {}
        self.heaps: List[List[float]] = []
        self.perches: List[List[float]] = []
        self.cross: Dict[str, float] = {}
        self.round_stats: Dict[int, Dict[str, float]] = {}
        self.signal: Dict[str, Any] = {}
        self.drifts: Dict[str, Dict[str, Any]] = {}
        self.bridges: Dict[str, Dict[str, Any]] = {}
        self.gas: Dict[str, Any] = {}
        self.events_said: Dict[str, float] = {}
        self.close_said = False

    def round_setup(self) -> None:
        area = self.area
        extra = area.get("extra") or {}
        points = area.get("points") or {}
        self.twist = str(extra.get("twist") or "")
        self.drown_y = extra.get("drown_y")
        self.lanes = {k: Lane(v) for k, v in (extra.get("lanes") or {}).items()}
        if set(self.lanes) != set(LANES):
            raise ValueError("Rail Rivals area %s has no lanes" % self.area_id)
        ca, cb = _crossing(self.lanes["a"], self.lanes["b"])
        self.cross = {"a": ca, "b": cb}
        self.depots = {k: [] for k in LANES}
        for mark in points.get("depot", []):
            lane = mark.get("lane")
            if lane in self.lanes:
                d, _ = self.lanes[lane].project(mark["p"][0], mark["p"][2])
                self.depots[lane].append((d, str(mark.get("name") or "the depot")))
        for lane in LANES:
            self.depots[lane].sort()
        self.levers = {k: [] for k in LANES}
        for mark in points.get("lever", []):
            lane = mark.get("lane")
            if lane in self.lanes:
                d, _ = self.lanes[lane].project(mark["p"][0], mark["p"][2])
                self.levers[lane].append({"index": int(mark.get("index", 0)), "p": list(mark["p"]),
                                          "d": d, "pulled": "", "by": "", "cool": 0.0,
                                          "yaw": float(mark.get("yaw", 0.0))})
        self.heaps = [list(m["p"]) for m in points.get("coal", [])]
        self.perches = [list(m["p"]) for m in points.get("perch", [])]
        self.landmarks = [(list(m["p"]), m["name"]) for m in area.get("landmarks") or []]
        # who is on which track this race: the second race in an area swaps
        swap = self.area_round % 2 == 1
        self.lane_of = {"red": "b" if swap else "a", "blue": "a" if swap else "b"}
        self.carts = {team: Cart(team, lane, self.lanes[lane])
                      for team, lane in self.lane_of.items()}
        self.round_stats = {}
        self.close_said = False
        self.events_said = {}
        for player in self.players.values():
            for key in ("coal", "act", "rr_job"):
                player.extra.pop(key, None)
        # the twist's own state
        moment = engine.now()
        sig = (points.get("signal") or [None])[0]
        self.signal = {"p": list(sig["p"]) if sig else None, "r": float(sig.get("r", 5.6)) if sig else 0.0,
                       "top": float(sig.get("top", 22.0)) if sig else 0.0, "team": "",
                       "until": 0.0, "rest": 0.0, "taking": "", "progress": 0.0}
        self.drifts = {}
        self.next_drift = {k: moment + 1e9 for k in LANES}
        self.bridges = {}
        spans = extra.get("bridges") or {}
        winches = {m.get("lane"): list(m["p"]) for m in points.get("winch", [])}
        if isinstance(spans, dict):
            for lane, span in spans.items():
                if lane in self.lanes and span and span[1] > span[0]:
                    self.bridges[lane] = {"span": [float(span[0]), float(span[1])],
                                          "winch": winches.get(lane), "up": False,
                                          "warn": 0.0, "until": 0.0, "rest": 0.0,
                                          "by": "", "by_team": "", "progress": 0.0}
                    self.set_dynamic_group("bridge_" + lane, False)
                    self.set_dynamic("bridge_%s_down" % lane, True)
        self.gas_spots = [list(m["p"]) for m in points.get("gas", [])]
        self.gas = {"spot": None, "warn_until": 0.0, "next": moment + 1e9, "inside": []}

    # ------------------------------------------------------------- lanes
    def lane_for(self, team: str) -> str:
        return self.lane_of.get(team, "a")

    def rival(self, team: str) -> str:
        return "blue" if team == "red" else "red"

    def cart_of(self, team: str) -> Optional[Cart]:
        return self.carts.get(team)

    # ============================================================ spawning
    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        spawns = self.area.get("spawns") or {}
        lane = self.lane_for(team)
        points = list(spawns.get(lane) or [])
        if not points:
            return super().spawn_points(team)
        stage = self.spawn_stage(team)
        while stage > 0 and not any(int(p.get("stage", 0)) == stage for p in points):
            stage -= 1
        return [p for p in points if int(p.get("stage", 0)) == stage] or points

    def spawn_stage(self, team: str) -> int:
        cart = self.carts.get(team)
        return cart.passed if cart else 0

    def on_spawned(self, player: Player) -> None:
        for key in ("coal", "act", "rr_job"):
            player.extra.pop(key, None)

    def welcome_lines(self, player: Player) -> List[str]:
        lines = super().welcome_lines(player)
        lines.append("Push your company's cart to the end of its line before the "
                     "other one gets there. Stand by it to push; stand by theirs to stop it.")
        twist = {"signal": "Take the signal cabin on the tower to hold their cart at the diamond.",
                 "drifts": "Drifts come down on the track -- hold E by one to dig your cart out.",
                 "bridges": "Hold E in a bridge cabin to winch their lift bridge up. Mind the river.",
                 "firedamp": "When a firedamp board hisses, get clear before it goes up. "
                             "Mind the lava."}.get(self.twist)
        if twist:
            lines.append(twist)
        return lines

    # ============================================================ movement
    def move_scale(self, player: Player) -> float:
        return 0.88 if player.extra.get("coal") else 1.0

    # ============================================================== rounds
    def on_live(self) -> None:
        moment = engine.now()
        for cart in self.carts.values():
            cart.idle_since = moment
        if self.twist == "drifts":
            self.next_drift = {k: moment + self.rng.uniform(*DRIFT_EVERY) * 0.7 for k in LANES}
        if self.twist == "firedamp" and self.gas_spots:
            self.gas["next"] = moment + self.rng.uniform(*GAS_EVERY) * 0.6
        self.system_message("The race is on! %s on %s, %s on %s." % (
            self.team_name("red"), self._lane_name(self.lane_for("red")),
            self.team_name("blue"), self._lane_name(self.lane_for("blue"))))

    def _lane_name(self, lane: str) -> str:
        names = (self.area.get("extra") or {}).get("names") or {}
        return str(names.get(lane) or ("lane " + lane))

    def round_tick(self, dt: float, moment: float) -> None:
        playing = self.playing()
        self._drown(playing)
        self._interact(playing, dt, moment)
        for cart in self.carts.values():
            self._move(cart, playing, dt, moment)
        self._twist(playing, dt, moment)
        self._race_events(moment)
        winner = ""
        for team, cart in self.carts.items():
            if cart.d >= cart.path.length - 0.5:
                winner = team
                break
        if winner:
            self.finish_round(winner, "terminus")

    def time_up(self) -> None:
        self.finish_round(self.leader(), "time")

    def leader(self) -> str:
        red, blue = self.carts.get("red"), self.carts.get("blue")
        if red is None or blue is None:
            return ""
        if abs(red.fraction - blue.fraction) < 0.01:
            return ""
        return "red" if red.fraction > blue.fraction else "blue"

    def headline(self, winner: str, reason: str) -> str:
        if not winner:
            return "dead heat -- nobody wins"
        cart = self.carts.get(winner)
        end = self._terminus(cart.lane) if cart else "the terminus"
        if reason == "terminus":
            return "%s reach %s first" % (self.team_name(winner), end)
        return "%s were further down the line" % self.team_name(winner)

    def _terminus(self, lane: str) -> str:
        points = self.area.get("points") or {}
        lane_obj = self.lanes.get(lane)
        best = "the terminus"
        for mark in points.get("finish", []):
            if mark.get("lane") == lane and lane_obj is not None:
                best = self._place(mark["p"]) or best
        return best

    def _place(self, pos: Sequence[float]) -> str:
        best, best_d = "", 1e9
        for p, name in getattr(self, "landmarks", []):
            d = math.hypot(p[0] - pos[0], p[2] - pos[2])
            if d < best_d:
                best, best_d = name, d
        return best if best_d < 90 else ""

    # ======================================================== the hazards
    def _drown(self, playing: List[Player]) -> None:
        if self.drown_y is None:
            return
        for player in playing:
            if player.pos[1] < float(self.drown_y):
                what = "the lava" if self.twist == "firedamp" else "the river"
                self.kill(player, None, what)

    # ========================================================= interacting
    def _interact(self, playing: List[Player], dt: float, moment: float) -> None:
        """Everybody holding E: whatever they are standing at gets a share
        of their time, in the order a person would expect."""
        for player in playing:
            if not player.extra.get("using"):
                if player.extra.get("act"):
                    player.extra.pop("act", None)
                continue
            act = self._what_here(player)
            if act is None:
                player.extra.pop("act", None)
                continue
            kind, key, need = act
            current = player.extra.get("act") or {}
            if current.get("k") != kind or current.get("key") != key:
                current = {"k": kind, "key": key, "t": 0.0, "need": need}
            current["t"] = float(current.get("t", 0.0)) + dt
            player.extra["act"] = current
            if kind == "dig":
                continue                        # the drift counts diggers itself
            if current["t"] >= need:
                player.extra.pop("act", None)
                self._do(player, kind, key, moment)

    def _what_here(self, player: Player) -> Optional[Tuple[str, Any, float]]:
        team = player.team
        x, y, z = player.pos
        own = self.carts.get(team)
        # a sack of coal to our own cart
        if player.extra.get("coal") and own is not None:
            cx, _, cz = own.pos()
            if math.hypot(cx - x, cz - z) <= STOKE_R:
                return ("stoke", team, 0.4)
        # a brake lever
        for lane, levers in self.levers.items():
            for lever in levers:
                lx, ly, lz = lever["p"]
                if math.hypot(lx - x, lz - z) > LEVER_R or abs(ly - y) > 4.0:
                    continue
                owner = self._lane_team(lane)
                if lever["pulled"] and owner == team:
                    return ("release", (lane, lever["index"]), RELEASE_HOLD)
                if not lever["pulled"] and owner != team and moment_ok(lever, engine.now()):
                    return ("brake", (lane, lever["index"]), LEVER_HOLD)
        # a drift on our own track
        if own is not None and own.lane in self.drifts:
            drift = self.drifts[own.lane]
            dx, _, dz = drift["p"]
            if math.hypot(dx - x, dz - z) <= DRIFT_R:
                return ("dig", own.lane, DRIFT_DIG)
        # a bridge winch
        for lane, bridge in self.bridges.items():
            winch = bridge.get("winch")
            if not winch or math.hypot(winch[0] - x, winch[2] - z) > WINCH_R or \
                    abs(winch[1] - y) > 4.0:
                continue
            owner = self._lane_team(lane)
            if bridge["up"] and owner == team:
                return ("lower", lane, WINCH_LOWER)
            if not bridge["up"] and not bridge["warn"] and owner != team and \
                    engine.now() >= bridge["rest"]:
                return ("raise", lane, WINCH_RAISE)
        # a coal heap
        if not player.extra.get("coal"):
            for heap in self.heaps:
                if math.hypot(heap[0] - x, heap[2] - z) <= COAL_R and abs(heap[1] - y) < 4.0:
                    return ("coal", tuple(heap), COAL_HOLD)
        return None

    def _lane_team(self, lane: str) -> str:
        for team, mine in self.lane_of.items():
            if mine == lane:
                return team
        return ""

    def _stat(self, player: Player, key: str, amount: float = 1.0) -> None:
        row = self.round_stats.setdefault(player.pid, {})
        row[key] = row.get(key, 0.0) + amount

    def _do(self, player: Player, kind: str, key: Any, moment: float) -> None:
        team = player.team
        if kind == "coal":
            player.extra["coal"] = True
            player.send({"t": "rrx", "k": "coal", "on": 1})
            self._broadcast_state()
        elif kind == "stoke":
            cart = self.carts.get(team)
            if cart is None:
                return
            player.extra.pop("coal", None)
            cart.stoke_until = min(moment + STOKE_CAP, max(moment, cart.stoke_until) + STOKE_SECONDS)
            player.score += 10
            self._stat(player, "coal")
            self.badge(player, "rr_coal")
            self.broadcast({"t": "rrx", "k": "stoke", "team": team, "by": player.username})
            self._event("rr_stoke", player, team)
            self._broadcast_state()
        elif kind == "brake":
            lane, index = key
            lever = self._lever(lane, index)
            cart = self.carts.get(self._lane_team(lane))
            if lever is None or cart is None or lever["pulled"]:
                return
            lever["pulled"] = team
            lever["by"] = player.username
            cart.brake_until = moment + BRAKE_SECONDS
            cart.brake_lever = index
            player.score += 8
            self._stat(player, "levers")
            self.badge(player, "rr_levers")
            self.broadcast({"t": "rrx", "k": "brake", "lane": lane, "i": index, "on": 1,
                            "by": player.username, "team": cart.team})
            self._event("rr_brake", player, cart.team, what=self._place(lever["p"]))
            self._broadcast_state()
        elif kind == "release":
            lane, index = key
            lever = self._lever(lane, index)
            if lever is None or not lever["pulled"]:
                return
            self._release(lane, lever, moment)
            player.score += 6
            self._stat(player, "releases")
            self.badge(player, "rr_releases")
            self.broadcast({"t": "rrx", "k": "brake", "lane": lane, "i": index, "on": 0,
                            "by": player.username, "team": team})
            self._event("rr_release", player, team)
        elif kind == "raise":
            bridge = self.bridges.get(key)
            if bridge is None or bridge["up"] or bridge["warn"]:
                return
            cart = self.carts.get(self._lane_team(key))
            if cart is not None and bridge["span"][0] - 2.0 <= cart.d <= bridge["span"][1] + 2.0:
                player.send({"t": "rrx", "k": "nope", "m": "The cart is on the bridge."})
                return
            bridge["warn"] = moment + BRIDGE_WARN
            bridge["by"] = player.username
            bridge["by_team"] = team
            player.score += 10
            self._stat(player, "winch")
            self.badge(player, "rr_winch")
            self.broadcast({"t": "rrx", "k": "bridge", "lane": key, "state": "warn",
                            "by": player.username})
        elif kind == "lower":
            bridge = self.bridges.get(key)
            if bridge is None or not bridge["up"]:
                return
            self._lower(key, moment)
            player.score += 6
            self._stat(player, "winch")
            self.badge(player, "rr_winch")

    def _lever(self, lane: str, index: int) -> Optional[Dict[str, Any]]:
        for lever in self.levers.get(lane, []):
            if lever["index"] == index:
                return lever
        return None

    def _release(self, lane: str, lever: Dict[str, Any], moment: float) -> None:
        lever["pulled"] = ""
        lever["by"] = ""
        lever["cool"] = moment + LEVER_COOL
        cart = self.carts.get(self._lane_team(lane))
        if cart is not None and cart.brake_lever == lever["index"]:
            cart.brake_until = 0.0
            cart.brake_lever = -1
        self._broadcast_state()

    # =============================================================== carts
    def _move(self, cart: Cart, playing: List[Player], dt: float, moment: float) -> None:
        cx, _, cz = cart.pos()
        pushers, contest = [], 0
        for player in playing:
            if abs(player.pos[1]) > PUSH_DY:
                continue
            if math.hypot(player.pos[0] - cx, player.pos[2] - cz) > PUSH_R:
                continue
            if player.team == cart.team:
                pushers.append(player)
            else:
                contest += 1
        cart.pushers = [p.pid for p in pushers]
        cart.contested = contest > 0
        # the brakes come off by themselves in the end
        if cart.brake_until and moment >= cart.brake_until:
            lever = self._lever(cart.lane, cart.brake_lever)
            if lever is not None and lever["pulled"]:
                self._release(cart.lane, lever, moment)
                self.broadcast({"t": "rrx", "k": "brake", "lane": cart.lane,
                                "i": lever["index"], "on": 0, "by": "", "team": cart.team})
            cart.brake_until = 0.0
        braked = moment < cart.brake_until
        limit = self._limit(cart, moment)
        cart.held = ""
        if limit is not None and cart.d >= limit[0] - 0.05:
            cart.held = limit[1]
        speed = 0.0
        if contest:
            cart.idle_since = moment
            if moment - cart.contest_said > 25.0 and pushers:
                cart.contest_said = moment
                self._event("rr_contest", None, cart.team)
        elif braked or cart.held:
            cart.idle_since = moment if pushers else cart.idle_since
        elif pushers:
            crew = CREW[min(len(pushers), len(CREW) - 1)]
            speed = BASE_SPEED * crew * (STOKE_BOOST if moment < cart.stoke_until else 1.0)
            cart.idle_since = moment
        elif moment - cart.idle_since > ROLLBACK_AFTER:
            floor = self.depots[cart.lane][cart.passed - 1][0] if cart.passed else 0.0
            if cart.d > floor:
                cart.d = max(floor, cart.d - ROLLBACK_SPEED * dt)
        cart.speed = speed
        if speed > 0:
            step = speed * dt
            if limit is not None:
                step = max(0.0, min(step, limit[0] - cart.d))
            cart.d = min(cart.path.length, cart.d + step)
            for player in pushers:
                cart.moved_by[player.pid] = cart.moved_by.get(player.pid, 0.0) + step
                self._stat(player, "pushed", step)
                if int(cart.moved_by[player.pid] / 10.0) > int((cart.moved_by[player.pid] - step) / 10.0):
                    player.score += 1
        # depots
        depots = self.depots[cart.lane]
        while cart.passed < len(depots) and cart.d >= depots[cart.passed][0]:
            name = depots[cart.passed][1]
            cart.passed += 1
            for player in pushers:
                player.score += 10
            self.broadcast({"t": "rrx", "k": "depot", "team": cart.team, "name": name,
                            "n": cart.passed})
            self.system_message("%s pass %s -- they respawn there now." %
                                (self.team_name(cart.team), name.title()))
            self._event("rr_depot", pushers[0] if pushers else None, cart.team, what=name.title())

    def _limit(self, cart: Cart, moment: float) -> Optional[Tuple[float, str]]:
        """How far the cart may go right now, and why (None: to the end)."""
        stops: List[Tuple[float, str]] = []
        if self.twist == "signal" and self.signal.get("team") and \
                self.signal["team"] != cart.team and moment < self.signal["until"]:
            stop = self.cross[cart.lane] - DIAMOND
            if cart.d <= stop + 0.5:
                stops.append((stop, "signal"))
        drift = self.drifts.get(cart.lane)
        if drift is not None and cart.d <= drift["d"]:
            stops.append((drift["d"] - 4.0, "drift"))
        bridge = self.bridges.get(cart.lane)
        if bridge is not None and (bridge["up"] or bridge["warn"]) and \
                cart.d <= bridge["span"][0]:
            stops.append((bridge["span"][0] - 3.0, "bridge"))
        if not stops:
            return None
        return min(stops)

    # =============================================================== twists
    def _twist(self, playing: List[Player], dt: float, moment: float) -> None:
        if self.twist == "signal":
            self._signal(playing, dt, moment)
        elif self.twist == "drifts":
            self._drifts(playing, dt, moment)
        elif self.twist == "bridges":
            self._bridges(moment)
        elif self.twist == "firedamp":
            self._firedamp(playing, moment)

    # ---- Dustbowl Gulch: the signal cabin
    def in_cabin(self, player: Player) -> bool:
        sig = self.signal
        p = sig.get("p")
        if not p:
            return False
        return abs(player.pos[0] - p[0]) <= sig["r"] and abs(player.pos[2] - p[2]) <= sig["r"] \
            and p[1] - 0.5 <= player.pos[1] <= sig["top"]

    def _signal(self, playing: List[Player], dt: float, moment: float) -> None:
        sig = self.signal
        if not sig.get("p"):
            return
        if sig["team"] and moment >= sig["until"]:
            sig["team"] = ""
            sig["rest"] = moment + SIGNAL_REST
            self.broadcast({"t": "rrx", "k": "signal", "team": "", "until": 0})
            self._broadcast_state()
        inside = [p for p in playing if self.in_cabin(p)]
        teams = {p.team for p in inside}
        if len(teams) != 1 or moment < sig["rest"] or sig["team"]:
            sig["taking"] = ""
            sig["progress"] = 0.0
            return
        team = next(iter(teams))
        if sig["taking"] != team:
            sig["taking"] = team
            sig["progress"] = 0.0
        sig["progress"] += dt * (1.0 + 0.35 * (len(inside) - 1))
        if sig["progress"] < SIGNAL_HOLD:
            return
        sig["team"] = team
        sig["until"] = moment + SIGNAL_SECONDS
        sig["taking"] = ""
        sig["progress"] = 0.0
        for player in inside:
            player.score += 10
            self._stat(player, "signal")
            self.badge(player, "rr_signal")
        self.broadcast({"t": "rrx", "k": "signal", "team": team, "until": SIGNAL_SECONDS,
                        "by": inside[0].username})
        self.system_message("%s set the junction signal against %s!" % (
            self.team_name(team), self.team_name(self.rival(team))))
        self._event("rr_signal", inside[0], self.rival(team))
        self._broadcast_state()

    # ---- Silverpine Pass: drifts
    def _drifts(self, playing: List[Player], dt: float, moment: float) -> None:
        for lane in LANES:
            cart = self.carts.get(self._lane_team(lane))
            if cart is None:
                continue
            drift = self.drifts.get(lane)
            if drift is None:
                if moment >= self.next_drift[lane] and cart.d < cart.path.length - 70.0:
                    d = min(cart.path.length - 30.0, cart.d + self.rng.uniform(36.0, 80.0))
                    x, z, yaw = cart.path.at(d)
                    self.drifts[lane] = {"d": d, "p": [x, 0.0, z], "yaw": yaw, "left": DRIFT_DIG,
                                         "said": False}
                    self.broadcast({"t": "rrx", "k": "drift", "lane": lane, "d": round(d, 1),
                                    "left": DRIFT_DIG})
                    self._broadcast_state()
                continue
            if cart.held == "drift" and not drift["said"]:
                drift["said"] = True
                self._event("rr_drift", None, cart.team, what=self._place(drift["p"]))
            diggers = [p for p in playing if p.team == cart.team and p.extra.get("using")
                       and (p.extra.get("act") or {}).get("k") == "dig"]
            if not diggers:
                continue
            drift["left"] -= dt * len(diggers)
            if drift["left"] > 0:
                continue
            del self.drifts[lane]
            self.next_drift[lane] = moment + self.rng.uniform(*DRIFT_EVERY)
            for player in diggers:
                player.score += 8
                player.extra.pop("act", None)
                self._stat(player, "dig")
                self.badge(player, "rr_dig")
            self.broadcast({"t": "rrx", "k": "drift", "lane": lane, "d": -1,
                            "by": diggers[0].username})
            self._broadcast_state()

    # ---- Redrock Mesa: the lift bridges
    def _bridges(self, moment: float) -> None:
        for lane, bridge in self.bridges.items():
            if bridge["warn"] and moment >= bridge["warn"]:
                bridge["warn"] = 0.0
                cart = self.carts.get(self._lane_team(lane))
                if cart is not None and bridge["span"][0] - 2.0 <= cart.d <= bridge["span"][1] + 2.0:
                    continue                    # it rolled on in the meantime: no lift
                bridge["up"] = True
                bridge["until"] = moment + BRIDGE_UP
                self.set_dynamic("bridge_%s_down" % lane, False)
                self.set_dynamic("bridge_%s_up" % lane, True)
                self.broadcast({"t": "rrx", "k": "bridge", "lane": lane, "state": "up",
                                "by": bridge["by"]})
                by = self.players_by_name(bridge["by"])
                self._event("rr_bridge", by, cart.team if cart else self._lane_team(lane),
                            company=self.team_name(cart.team) if cart else "")
                self._broadcast_state()
            elif bridge["up"] and moment >= bridge["until"]:
                self._lower(lane, moment)

    def players_by_name(self, name: str) -> Optional[Player]:
        for player in self.players.values():
            if player.username == name:
                return player
        return None

    def _lower(self, lane: str, moment: float) -> None:
        bridge = self.bridges[lane]
        bridge["up"] = False
        bridge["warn"] = 0.0
        bridge["rest"] = moment + BRIDGE_REST
        self.set_dynamic("bridge_%s_up" % lane, False)
        self.set_dynamic("bridge_%s_down" % lane, True)
        self.broadcast({"t": "rrx", "k": "bridge", "lane": lane, "state": "down"})
        self._broadcast_state()

    # ---- Lantern Deep: firedamp
    def _firedamp(self, playing: List[Player], moment: float) -> None:
        gas = self.gas
        if not self.gas_spots:
            return
        if gas["spot"] is None:
            if moment < gas["next"]:
                return
            options = [s for s in self.gas_spots if s != gas.get("last")] or self.gas_spots
            spot = self.rng.choice(options)
            gas["spot"] = spot
            gas["warn_until"] = moment + GAS_WARN
            gas["inside"] = [p.pid for p in playing
                             if math.hypot(p.pos[0] - spot[0], p.pos[2] - spot[2]) < GAS_R]
            self.broadcast({"t": "rrx", "k": "gas", "p": spot, "state": "warn", "in": GAS_WARN})
            near = [p for p in playing if math.hypot(p.pos[0] - spot[0], p.pos[2] - spot[2]) < 60]
            if near:
                self._event("rr_gas", near[0], near[0].team, what=self._place(spot))
            self._broadcast_state()
            return
        if moment < gas["warn_until"]:
            return
        spot = gas["spot"]
        gas["last"] = spot
        gas["spot"] = None
        gas["next"] = moment + self.rng.uniform(*GAS_EVERY)
        self.broadcast({"t": "rrx", "k": "gas", "p": spot, "state": "blast"})
        for player in playing:
            dist = math.hypot(player.pos[0] - spot[0], player.pos[2] - spot[2])
            if abs(player.pos[1] - spot[1]) > 10.0:
                continue
            if dist < GAS_R:
                self.apply_damage(player, None, 95.0, "firedamp")
            elif dist < GAS_EDGE:
                self.apply_damage(player, None, 35.0, "firedamp")
            elif player.pid in gas["inside"] and player.alive:
                player.score += 4
                self._stat(player, "canary")
                self.badge(player, "rr_canary")
        gas["inside"] = []
        self._broadcast_state()

    # ======================================================== race events
    def _race_events(self, moment: float) -> None:
        red, blue = self.carts.get("red"), self.carts.get("blue")
        if red is None or blue is None or self.close_said:
            return
        last = {c.team: len(self.depots[c.lane]) for c in (red, blue)}
        if red.passed >= last["red"] and blue.passed >= last["blue"] and \
                abs(red.fraction - blue.fraction) < 0.08:
            self.close_said = True
            self._event("rr_close", None, "red")
            self.system_message("Neck and neck! Both carts are past their last depot.")

    def _event(self, kind: str, player: Optional[Player], team: str, **extra: Any) -> None:
        data = {"by": player.username if player else "", "by_team": player.team if player else "",
                "team": team, "company": self.team_name(team), "world": self.world_id}
        data.update(extra)
        self.push_event(kind, **data)

    # ============================================================== kills
    def after_kill(self, killer: Optional[Player], victim: Player, weapon: str) -> None:
        for key in ("coal", "act", "rr_job"):
            victim.extra.pop(key, None)
        if killer is None or killer.team == victim.team:
            return
        own = self.carts.get(killer.team)
        if own is None:
            return
        cx, _, cz = own.pos()
        if math.hypot(victim.pos[0] - cx, victim.pos[2] - cz) < 18.0:
            killer.score += 5
            self._stat(killer, "guard")
            self.badge(killer, "rr_guard")

    # ========================================================== the end
    def on_round_over(self, winner: str, reason: str, winners: List[Player]) -> None:
        loser = self.carts.get(self.rival(winner)) if winner else None
        photo = loser is not None and loser.fraction >= 0.9
        for player in self.players.values():
            stats = self.round_stats.get(player.pid, {})
            pushed = int(stats.get("pushed", 0.0))
            if pushed > 0:
                self.badge(player, "rr_pushed", pushed)
        for player in winners:
            self.badge(player, "rr_wins")
            self.badge(player, "rr_area_" + self.area_id, 1, "max")
            if photo:
                self.badge(player, "rr_photo")
        for player in self.players.values():
            player.extra.pop("coal", None)
            player.extra.pop("act", None)

    def results_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for p in self.players.values():
            st = self.round_stats.get(p.pid, {})
            rows.append({"id": p.pid, "name": p.username, "team": p.team, "score": p.score,
                         "kills": p.kills, "deaths": p.deaths,
                         "pushed": int(st.get("pushed", 0.0)),
                         "jobs": int(st.get("levers", 0) + st.get("releases", 0) +
                                     st.get("coal", 0) + st.get("dig", 0) +
                                     st.get("winch", 0) + st.get("signal", 0))})
        rows.sort(key=lambda r: (-r["score"], r["name"].lower()))
        return rows

    def result_columns(self) -> List[List[str]]:
        return [["pushed", "Pushed"], ["jobs", "Jobs"], ["kills", "Kills"],
                ["deaths", "Deaths"], ["score", "Score"]]

    def awards(self, winner: str) -> List[str]:
        out = []
        best = {}
        for pid, st in self.round_stats.items():
            for key in ("pushed", "levers", "coal", "guard", "releases", "dig", "winch"):
                if st.get(key, 0) > best.get(key, (0, 0))[1]:
                    best[key] = (pid, st[key])
        labels = {"pushed": ("Engineer", "pushed the cart %d units"),
                  "levers": ("Saboteur", "pulled %d brakes"),
                  "coal": ("Stoker", "shovelled %d sacks of coal"),
                  "guard": ("Lawman", "stopped %d raiders at the cart"),
                  "releases": ("Brakeman", "released %d brakes"),
                  "dig": ("Snowplow", "dug out %d drifts"),
                  "winch": ("Bridgekeeper", "worked %d bridges")}
        for key, (pid, value) in best.items():
            player = self.players.get(pid)
            if player is None or value < 1:
                continue
            title, text = labels[key]
            out.append("%s: %s %s" % (title, player.username, text % int(value)))
        return out[:5]

    def result_extra(self, winner: str) -> Dict[str, Any]:
        return {"carts": {t: round(c.fraction, 3) for t, c in self.carts.items()}}

    # ============================================================== state
    def _broadcast_state(self) -> None:
        self.broadcast({"t": "rrs", "s": self.hud_state().get("rr")})

    def hud_state(self) -> Dict[str, Any]:
        moment = engine.now()
        carts = {}
        for team, cart in self.carts.items():
            carts[team] = {"lane": cart.lane, "d": round(cart.d, 1),
                           "len": round(cart.path.length, 1), "f": round(cart.fraction, 3),
                           "push": len(cart.pushers), "contest": cart.contested,
                           "brake": round(max(0.0, cart.brake_until - moment), 1),
                           "stoke": round(max(0.0, cart.stoke_until - moment), 1),
                           "held": cart.held, "passed": cart.passed,
                           "depots": [round(d / cart.path.length, 3) for d, _ in self.depots[cart.lane]]}
        levers = {lane: [{"i": lv["index"], "pulled": lv["pulled"],
                          "cool": round(max(0.0, lv["cool"] - moment), 1)} for lv in levers]
                  for lane, levers in self.levers.items()}
        twist: Dict[str, Any] = {"kind": self.twist}
        if self.twist == "signal":
            twist.update({"team": self.signal.get("team", ""),
                          "left": round(max(0.0, self.signal.get("until", 0) - moment), 1)
                          if self.signal.get("team") else 0,
                          "rest": round(max(0.0, self.signal.get("rest", 0) - moment), 1),
                          "taking": self.signal.get("taking", ""),
                          "progress": round(self.signal.get("progress", 0.0) / SIGNAL_HOLD, 2)})
        elif self.twist == "drifts":
            twist["drifts"] = {lane: {"d": round(dr["d"], 1), "left": round(dr["left"] / DRIFT_DIG, 2)}
                               for lane, dr in self.drifts.items()}
        elif self.twist == "bridges":
            twist["bridges"] = {lane: {"up": br["up"], "warn": bool(br["warn"]),
                                       "left": round(max(0.0, br["until"] - moment), 1)
                                       if br["up"] else 0}
                                for lane, br in self.bridges.items()}
        elif self.twist == "firedamp":
            twist["gas"] = {"p": self.gas.get("spot"),
                            "left": round(max(0.0, self.gas.get("warn_until", 0) - moment), 1)
                            if self.gas.get("spot") else 0}
        return {"rr": {"carts": carts, "levers": levers, "twist": twist,
                       "lanes": dict(self.lane_of)}}

    def snapshot_extra(self) -> Any:
        out = {}
        for team, cart in self.carts.items():
            out[team] = [round(cart.d, 2), round(cart.speed, 2),
                         1 if cart.contested else 0,
                         1 if engine.now() < cart.brake_until else 0,
                         1 if engine.now() < cart.stoke_until else 0, len(cart.pushers)]
        coal = [p.pid for p in self.players.values() if p.extra.get("coal")]
        return {"c": out, "coal": coal}

    def me_state(self, player: Player) -> Dict[str, Any]:
        act = player.extra.get("act") or {}
        out = {"coal": bool(player.extra.get("coal")), "lane": self.lane_for(player.team)}
        if act:
            need = float(act.get("need", 1.0) or 1.0)
            if act.get("k") == "dig":
                cart = self.carts.get(player.team)
                drift = self.drifts.get(cart.lane) if cart else None
                prog = 1.0 - (drift["left"] / DRIFT_DIG) if drift else 1.0
            else:
                prog = float(act.get("t", 0.0)) / need
            out["act"] = {"k": act.get("k"), "p": round(max(0.0, min(1.0, prog)), 2)}
        return out

    def score_row(self, player: Player, row: Dict[str, Any]) -> None:
        st = self.round_stats.get(player.pid, {})
        row["pushed"] = int(st.get("pushed", 0.0))
        row["coal"] = bool(player.extra.get("coal"))

    def describe(self) -> Dict[str, Any]:
        info = super().describe()
        red, blue = self.carts.get("red"), self.carts.get("blue")
        if red and blue and self.phase == "active":
            info["summary"] = "Round %d · %s · Crimson %d%% / Bluebird %d%%" % (
                max(1, self.round_number), self.area["name"], red.fraction * 100,
                blue.fraction * 100)
        return info

    # ======================================================= sleep / wake
    def sleep_extra(self) -> Dict[str, Any]:
        return {"progress": max([c.fraction for c in self.carts.values()] or [0.0]),
                "carts": {t: round(c.fraction, 3) for t, c in self.carts.items()}}

    def resume_progress(self, progress: float, state: Dict[str, Any]) -> None:
        given = state.get("carts") or {}
        for team, cart in self.carts.items():
            frac = float(given.get(team, progress * self.rng.uniform(0.75, 1.0)) or 0.0)
            cart.d = max(0.0, min(0.9, frac)) * cart.path.length
            cart.passed = sum(1 for d, _ in self.depots[cart.lane] if d <= cart.d)

    # =============================================================== bots
    def bot_role(self, brain) -> str:
        if not self.setting("enabled"):
            return "fighter"
        team = brain.p.team
        counts = self.bots.role_counts(team, brain) if self.bots is not None else {}
        size = sum(counts.values()) + 1
        t = brain.t
        weights = {
            "pusher": 0.2 + self.pct("pushers") * (0.6 + brain.objective * 0.9 +
                                                   t("support", 0.2) * 0.4),
            "raider": 0.08 + self.pct("raiders") * (0.5 + t("aggression", 0.5) * 0.9 +
                                                    t("chaos", 0.1) * 0.5),
            "sniper": self.pct("snipers") * max(0.0, t("wp_sniper", 1.0) - 0.7) * 1.6,
            "flex": 0.12 + t("explore", 0.2) * 0.4 + t("support", 0.2) * 0.3,
        }
        if counts.get("pusher", 0) < int(self.setting("min_pushers") or 0):
            return "pusher"
        if counts.get("pusher", 0) < max(1, round(size * 0.35)):
            weights["pusher"] *= 2.0
        if counts.get("sniper", 0) >= max(1, round(size * 0.2)):
            weights["sniper"] *= 0.1
        if counts.get("raider", 0) >= max(1, round(size * 0.4)):
            weights["raider"] *= 0.3
        roll = brain.rng.random() * sum(weights.values())
        for role, weight in weights.items():
            roll -= weight
            if roll <= 0:
                return role
        return "pusher"

    def bot_goal_weights(self, brain, weights: Dict[str, float]) -> Dict[str, float]:
        if not self.setting("enabled"):
            return weights
        weights["objective"] = weights.get("objective", 0.5) * 2.4 + 0.4
        weights["afk"] = weights.get("afk", 0.0) * 0.4
        weights["explore"] = weights.get("explore", 0.0) * 0.6
        return weights

    def bot_urgent(self, brain) -> bool:
        if self.phase != "active" or not self.setting("enabled"):
            return False
        p = brain.p
        if p.extra.get("coal") or p.extra.get("act") or p.extra.get("rr_job"):
            # an errand under way is seen through, whatever mood comes over it
            return True
        spot = self.gas.get("spot") if self.twist == "firedamp" else None
        if spot is not None and math.hypot(p.pos[0] - spot[0], p.pos[2] - spot[2]) < GAS_EDGE + 4:
            return True
        cart = self.carts.get(p.team)
        return cart is not None and brain.role == "pusher" and (cart.contested or cart.held == "drift"
                                                                or engine.now() < cart.brake_until)

    def bot_objective(self, brain) -> None:
        p = brain.p
        if self.phase != "active" or not self.setting("enabled"):
            self._bot_drift(brain)
            return
        use = False
        try:
            use = self._bot_job(brain)
        finally:
            if use:
                p.extra["using"] = True
            else:
                p.extra.pop("using", None)

    def _bot_drift(self, brain) -> None:
        p = brain.p
        p.extra.pop("using", None)
        cart = self.carts.get(p.team)
        if cart is None or brain.waypoints:
            return
        spot = self._beside(cart, brain, behind=6.0)
        brain.go(spot, "wait%d" % int(cart.d / 20))

    def _beside(self, cart: Cart, brain, behind: float = 2.0) -> List[float]:
        """A spot by the cart, each bot its own side of it."""
        seed = (brain.p.pid * 2654435761) % 1000 / 1000.0
        d = max(0.0, cart.d - behind + (seed - 0.5) * 5.0)
        x, z, yaw = cart.path.at(d)
        side = -1.0 if seed < 0.5 else 1.0
        off = 3.2 + seed * 2.0
        rx, rz = math.cos(yaw), -math.sin(yaw)
        return [x + rx * side * off, 0.0, z + rz * side * off]

    def _go(self, brain, point: Sequence[float], key: str) -> None:
        brain.go(list(point), key)

    def _bot_job(self, brain) -> bool:
        """What this bot does about the race right now; True to hold E.

        A bot that takes on an errand -- a lever, a sack of coal, a drift, a
        winch, the signal cabin -- keeps at it until it is done or no longer
        makes sense (``rr_job``), the way a person does, instead of
        changing its mind on every think."""
        p = brain.p
        moment = engine.now()
        team = p.team
        own = self.carts.get(team)
        rival = self.carts.get(self.rival(team))
        if own is None or rival is None:
            return False
        # firedamp first: nobody stands in a venting pocket
        if self.twist == "firedamp" and self.gas.get("spot") is not None:
            spot = self.gas["spot"]
            dx, dz = p.pos[0] - spot[0], p.pos[2] - spot[2]
            dist = math.hypot(dx, dz)
            if dist < GAS_EDGE + 3 and brain.rng.random() < 0.4 + self.pct("twist") * 0.6:
                k = (GAS_EDGE + 10) / max(0.1, dist)
                away = [spot[0] + dx * k, p.pos[1], spot[2] + dz * k]
                self.doing(brain, "getting clear of the firedamp")
                p.extra.pop("rr_job", None)
                self._go(brain, away, "flee%d" % int(spot[0]))
                return False
        # carrying coal: straight to the cart
        if p.extra.get("coal"):
            p.extra.pop("rr_job", None)
            self.doing(brain, "taking coal to the cart")
            spot = own.pos()
            if math.hypot(spot[0] - p.pos[0], spot[2] - p.pos[2]) < STOKE_R - 1.5:
                brain.waypoints = []
                return True
            self._go(brain, self._beside(own, brain, 0.0), "stoke%d" % int(own.d / 15))
            return False
        job = p.extra.get("rr_job")
        if job is not None and (moment > job["until"] or not self._job_valid(job, team)):
            p.extra.pop("rr_job", None)
            job = None
        if job is None:
            job = self._pick_job(brain, own, rival, moment)
            if job is not None:
                job["until"] = moment + job.get("for", 30.0)
                p.extra["rr_job"] = job
                self.callout(brain, JOB_LINES.get(job["k"], []), "job" + job["k"], chance=0.5,
                             team=True)
        if job is not None:
            self.doing(brain, job["say"])
            return self._work_at(brain, job["at"], job["r"], job["key"], hold=job.get("hold", True))
        role = brain.role
        if role == "raider" or (role == "flex" and rival.fraction > own.fraction + 0.08):
            self.doing(brain, "contesting their cart")
            self.callout(brain, ["contest their cart", "on their cart", "stop their cart"], "raid",
                         chance=0.25, every=60.0, team=True)
            spot = self._beside(rival, brain, -2.0)
            if math.hypot(spot[0] - p.pos[0], spot[2] - p.pos[2]) > 3.0:
                self._go(brain, spot, "raid%d" % int(rival.d / 6))
            else:
                brain.waypoints = []
            return False
        if role == "sniper":
            perch = self._perch_near(own)
            if perch is not None:
                self.doing(brain, "watching the line from up high")
                if math.dist(perch, p.pos) > 4.0:
                    self._go(brain, perch, "perch%d%d" % (int(perch[0]), int(perch[2])))
                else:
                    brain.waypoints = []
                return False
        if role == "flex" and self.twist == "signal" and self.signal.get("team") == team \
                and self.in_cabin(p):
            self.doing(brain, "holding the signal cabin")
            brain.waypoints = []
            return False
        # pushers (and anybody with nothing better): on the cart
        self.doing(brain, "pushing the cart" if not own.contested else "fighting for the cart")
        spot = self._beside(own, brain, 1.0)
        if math.hypot(spot[0] - p.pos[0], spot[2] - p.pos[2]) > 2.5:
            self._go(brain, spot, "cart%d" % int(own.d / 6))
        else:
            brain.waypoints = []
        return False

    def _pick_job(self, brain, own: Cart, rival: Cart, moment: float) -> Optional[Dict[str, Any]]:
        """An errand worth running now, for this bot's role and persona."""
        p = brain.p
        team = p.team
        role = brain.role
        rng = brain.rng
        twist = self.pct("twist")
        # our own cart is braked: the nearest of our bots goes to free it
        if moment < own.brake_until and own.brake_lever >= 0:
            lever = self._lever(own.lane, own.brake_lever)
            if lever is not None and self._nearest_of_team(team, lever["p"]) is p and \
                    rng.random() < 0.3 + self.pct("release") * (0.7 + brain.t("support", 0.2)):
                return {"k": "release", "lane": own.lane, "i": lever["index"],
                        "at": _floor(lever["p"]), "r": LEVER_R - 1.2,
                        "key": "lever%s%d" % (own.lane, lever["index"]),
                        "say": "running to release the brakes", "for": 30.0}
        # snowed in: the pushers dig
        drift = self.drifts.get(own.lane)
        if drift is not None and own.d >= drift["d"] - 30.0 and role in ("pusher", "flex") and \
                rng.random() < 0.4 + twist * 0.6:
            return {"k": "dig", "lane": own.lane, "at": list(drift["p"]), "r": DRIFT_R - 2.5,
                    "key": "drift%d" % int(drift["d"]), "say": "digging the cart out of a drift",
                    "for": 25.0}
        # our bridge is up: the nearest of our bots goes to lower it
        bridge = self.bridges.get(own.lane)
        if bridge is not None and bridge["up"] and bridge.get("winch") and \
                self._nearest_of_team(team, bridge["winch"]) is p and rng.random() < 0.3 + twist:
            return {"k": "lower", "lane": own.lane, "at": list(bridge["winch"]), "r": WINCH_R - 1.5,
                    "key": "winch%s" % own.lane, "say": "going to lower the bridge", "for": 25.0}
        raiding = role == "raider" or (role == "flex" and rival.fraction > own.fraction + 0.08)
        if raiding:
            # a lever just ahead of their cart
            if rng.random() < 0.25 + self.pct("sabotage") * (0.6 + brain.t("chaos", 0.1)):
                for lever in self.levers.get(rival.lane, []):
                    ahead = lever["d"] - rival.d
                    if lever["pulled"] or moment < lever["cool"] or not (10.0 < ahead < 170.0):
                        continue
                    if math.dist(lever["p"], p.pos) > 170:
                        continue
                    return {"k": "brake", "lane": rival.lane, "i": lever["index"],
                            "at": _floor(lever["p"]), "r": LEVER_R - 1.2,
                            "key": "lever%s%d" % (rival.lane, lever["index"]),
                            "say": "going to pull the brakes on their cart", "for": 35.0}
            # the line's twist, against them
            if self.twist == "signal" and self.signal.get("p") and not self.signal.get("team") \
                    and moment >= self.signal.get("rest", 0) and rng.random() < twist:
                ahead = self.cross[rival.lane] - DIAMOND - rival.d
                if 0.0 < ahead < 220.0:
                    return {"k": "signal", "at": list(self.signal["p"]), "r": 3.0, "hold": False,
                            "key": "signal", "say": "taking the signal cabin", "for": 30.0}
            if self.twist == "bridges" and rng.random() < twist:
                bridge = self.bridges.get(rival.lane)
                if bridge is not None and bridge.get("winch") and not bridge["up"] and \
                        not bridge["warn"] and moment >= bridge["rest"]:
                    ahead = bridge["span"][0] - rival.d
                    if 6.0 < ahead < 320.0:
                        return {"k": "raise", "lane": rival.lane, "at": list(bridge["winch"]),
                                "r": WINCH_R - 1.5, "key": "winch%s" % rival.lane,
                                "say": "going to winch their bridge up", "for": 60.0}
        # coal: flex bots often, pushers now and then when the cart is safe
        if moment > own.stoke_until - 3.0 and not own.contested:
            chance = self.pct("coal") * (0.55 if role == "flex" else
                                         0.1 if role == "pusher" and len(own.pushers) >= 2 else 0.0)
            chance *= 0.6 + brain.t("support", 0.2)
            if rng.random() < chance:
                heap = self._heap_near(own.pos())
                if heap is not None and math.dist(heap, p.pos) < 140:
                    return {"k": "coal", "at": _floor(heap), "r": COAL_R - 2.0,
                            "key": "heap%d" % int(heap[0]), "say": "fetching coal for the cart",
                            "for": 30.0}
        # hold the signal for our own cart's run at the diamond
        if role == "flex" and self.twist == "signal" and self.signal.get("p") and \
                not self.signal.get("team") and moment >= self.signal.get("rest", 0) and \
                rng.random() < twist * 0.5:
            ahead = self.cross[own.lane] - own.d
            if 0.0 < ahead < 160.0 and rival.d < self.cross[rival.lane]:
                return {"k": "signal", "at": list(self.signal["p"]), "r": 3.0, "hold": False,
                        "key": "signal", "say": "taking the signal cabin", "for": 30.0}
        return None

    def _job_valid(self, job: Dict[str, Any], team: str) -> bool:
        kind = job["k"]
        moment = engine.now()
        if kind in ("brake", "release"):
            lever = self._lever(job["lane"], job["i"])
            if lever is None:
                return False
            if kind == "release":
                return bool(lever["pulled"])
            rival = self.carts.get(self._lane_team(job["lane"]))
            return not lever["pulled"] and moment >= lever["cool"] and \
                rival is not None and lever["d"] - rival.d > 3.0
        if kind == "dig":
            return job["lane"] in self.drifts
        if kind == "raise":
            bridge = self.bridges.get(job["lane"])
            rival = self.carts.get(self._lane_team(job["lane"]))
            return bridge is not None and not bridge["up"] and not bridge["warn"] and \
                moment >= bridge["rest"] and rival is not None and rival.d < bridge["span"][0] - 2.0
        if kind == "lower":
            bridge = self.bridges.get(job["lane"])
            return bridge is not None and bridge["up"]
        if kind == "signal":
            return not self.signal.get("team")
        if kind == "coal":
            return True
        return False

    def _work_at(self, brain, point: Sequence[float], radius: float, key: str,
                 hold: bool = True) -> bool:
        p = brain.p
        if math.hypot(point[0] - p.pos[0], point[2] - p.pos[2]) <= radius and \
                abs(point[1] - p.pos[1]) < 3.5:
            brain.waypoints = []
            return hold
        self._go(brain, point, key)
        return False

    def _nearest_of_team(self, team: str, point: Sequence[float]) -> Optional[Player]:
        """The team's bot nearest ``point`` (people do as they please)."""
        best, best_d = None, 1e9
        for player in self.playing():
            if player.team != team or player.brain is None:
                continue
            d = math.hypot(player.pos[0] - point[0], player.pos[2] - point[2])
            if d < best_d:
                best, best_d = player, d
        return best

    def _heap_near(self, pos: Sequence[float]) -> Optional[List[float]]:
        best, best_d = None, 1e9
        for heap in self.heaps:
            d = math.hypot(heap[0] - pos[0], heap[2] - pos[2])
            if d < best_d:
                best, best_d = heap, d
        return best if best_d < 160 else None

    def _perch_near(self, cart: Cart) -> Optional[List[float]]:
        ahead = cart.path.at(min(cart.path.length, cart.d + 60.0))
        best, best_d = None, 1e9
        for perch in self.perches:
            d = math.hypot(perch[0] - ahead[0], perch[2] - ahead[1])
            if d < best_d:
                best, best_d = perch, d
        return best if best_d < 130 else None

    def bot_context(self) -> List[str]:
        lines = []
        for team, cart in self.carts.items():
            state = []
            if cart.contested:
                state.append("contested")
            if engine.now() < cart.brake_until:
                state.append("braked")
            if cart.held:
                state.append("held at the %s" % cart.held)
            lines.append("%s's cart is %d%% of the way down %s%s." % (
                self.team_name(team), cart.fraction * 100, self._lane_name(cart.lane),
                (" (" + ", ".join(state) + ")") if state else ""))
        return lines

    def bot_me(self, brain) -> Dict[str, Any]:
        out = super().bot_me(brain)
        role = {"pusher": "you push your own cart", "raider": "you raid the other team's cart",
                "sniper": "you cover the line from a perch",
                "flex": "you fetch coal and work the levers and the twist"}.get(brain.role)
        if role:
            out.setdefault("context", []).append(role)
        if brain.p.extra.get("coal"):
            out["context"].append("you are carrying a sack of coal to your cart")
        return out

    def bot_spread(self, players: List[Player]) -> None:
        """A woken race: put each bot somewhere sensible for its job."""
        for player in players:
            brain = player.brain
            if brain is None:
                continue
            cart = self.carts.get(player.team)
            if cart is not None and player.alive:
                spot = self._beside(cart, brain, brain.rng.uniform(4.0, 30.0))
                nav = getattr(self.host, "nav", None)
                if nav is not None and getattr(nav, "ready", False):
                    node = nav.nearest(spot, 3)
                    if node >= 0:
                        spot = nav.point(node)
                player.pos = [spot[0], spot[1] + 0.5, spot[2]]
            brain.on_spawn()

    # ============================================================== tests
    def observe(self) -> Dict[str, Any]:
        return {"area": self.area_id, "phase": self.phase,
                "carts": {t: round(c.d, 1) for t, c in self.carts.items()},
                "levers": sum(1 for ls in self.levers.values() for lv in ls if lv["pulled"]),
                "coal": sum(1 for p in self.players.values() if p.extra.get("coal")),
                "held": [c.held for c in self.carts.values() if c.held]}

    def selftest(self, result: Dict[str, Any]) -> List[Tuple[str, bool, Any]]:
        obs = result.get("observations") or []
        moved = max([max(o["carts"].values() or [0]) for o in obs if o.get("phase") == "active"]
                    or [0.0])
        levers = max([o["levers"] for o in obs] or [0])
        coal = max([o["coal"] for o in obs] or [0])
        return [("the bots push their carts down the line", moved > 60.0, "%.0f units" % moved),
                ("somebody pulls a brake lever", levers > 0, levers),
                ("somebody fetches coal", coal > 0, coal)]


def moment_ok(lever: Dict[str, Any], moment: float) -> bool:
    return moment >= float(lever.get("cool", 0.0))


def _floor(point: Sequence[float]) -> List[float]:
    """A ground-level spot by something standing on the ground."""
    return [point[0], 0.0, point[2]]


WORLD_CLASS = RailRivalsWorld
