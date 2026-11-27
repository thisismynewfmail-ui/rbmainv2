"""The twists of Rail Rivals' newer railroads (app/game/worlds/rail_rivals.py).

Dustbowl Gulch, Silverpine Pass, Redrock Mesa and Lantern Deep keep their
twists in the world itself.  Every line built since names one of these by
its area's ``extra["twist"]``; the world makes the matching :class:`Twist`
at the start of each race and hands it the race at every point where a
twist can matter:

``setup``       read the area (its ``extra`` and ``points``), reset state
``on_live``     the race has started: start the clocks
``tick``        once a tick, with everybody playing
``limit``       how far a cart may roll right now, and why (a stop)
``drive``       a cart's speed this tick, when the twist moves it itself
``crew``        extra pushers the twist lends a cart (the circus elephant)
``what_here``   what holding E does where a player stands
``do``          the hold is done: do it
``state``       what the client draws and the HUD says
``carrying``    what a player has on their back (a rail, a bucket)
``drop``        a player died or the round ended: put it down
``flee``        a place a bot should get to, now (out of harm's way)
``bot_job``     an errand worth running for this bot right now
``job_valid``   is a bot's errand still worth running
``observe`` / ``selftest``  what the headless tests watch for

A twist's numbers are its own; what it shares with the old ones is the
vocabulary -- carts stop with a ``held`` reason, a hold of E is an ``act``
with a ``kind`` and a ``key``, and things that happen go out as ``rrx``
messages (``k`` = the twist's own kinds) and speech events (``rr_*``).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import instance as engine

Act = Tuple[str, Any, float]
Stop = Tuple[float, str]


def flat(a: Sequence[float], b: Sequence[float]) -> float:
    return math.hypot(a[0] - b[0], a[2] - b[2])


class Twist:
    """The do-nothing twist every real one starts from."""

    kind = ""
    welcome = ""
    # speech the twist pushes, the stats its jobs count under, and the
    # end-of-round award for the best at it: (stat, title, "did %d things")
    jobs: Tuple[str, ...] = ()
    award: Optional[Tuple[str, str, str]] = None
    # acts that count their own progress (a dig shared by several diggers)
    continuous: Tuple[str, ...] = ()
    job_lines: Dict[str, List[str]] = {}

    def __init__(self, world):
        self.w = world

    # ------------------------------------------------------------ round
    def setup(self, area: Dict[str, Any], extra: Dict[str, Any],
              points: Dict[str, List[Dict[str, Any]]], moment: float) -> None:
        pass

    def on_live(self, moment: float) -> None:
        pass

    def tick(self, playing: List[Any], dt: float, moment: float) -> None:
        pass

    # ------------------------------------------------------------ carts
    def limit(self, cart, moment: float) -> Optional[Stop]:
        return None

    def drive(self, cart, pushers: List[Any], contested: bool, braked: bool,
              dt: float, moment: float) -> Optional[float]:
        """A speed for the cart this tick (negative rolls it back), or None
        for the usual push-and-roll."""
        return None

    def crew(self, cart, moment: float) -> int:
        return 0

    def floor(self, cart) -> float:
        """How far back a cart this twist rolls back may go."""
        return 0.0

    # ------------------------------------------------------- holding E
    def what_here(self, player, moment: float) -> Optional[Act]:
        return None

    def do(self, player, kind: str, key: Any, moment: float) -> bool:
        return False

    def act_progress(self, player, act: Dict[str, Any]) -> Optional[float]:
        return None

    # ----------------------------------------------------------- people
    def carrying(self, player) -> str:
        return str(player.extra.get("carry") or "")

    def drop(self, player) -> None:
        player.extra.pop("carry", None)

    def move_scale(self, player) -> Optional[float]:
        return 0.86 if self.carrying(player) else None

    def me(self, player) -> Dict[str, Any]:
        kind = self.carrying(player)
        return {"carry": kind} if kind else {}

    def drown_what(self, player) -> Optional[str]:
        return None

    # ------------------------------------------------------------ state
    def state(self, moment: float) -> Dict[str, Any]:
        return {}

    def context(self) -> List[str]:
        return []

    # ------------------------------------------------------------- bots
    def urgent(self, brain) -> bool:
        return False

    def flee(self, brain) -> Optional[List[float]]:
        return None

    def carry_job(self, brain) -> Optional[Dict[str, Any]]:
        """Where a bot carrying something takes it."""
        return None

    def bot_job(self, brain, own, rival, moment: float) -> Optional[Dict[str, Any]]:
        return None

    def job_valid(self, job: Dict[str, Any], team: str) -> Optional[bool]:
        return None

    # ------------------------------------------------------------ tests
    def observe(self) -> Dict[str, Any]:
        return {}

    def selftest(self, observations: List[Dict[str, Any]]) -> List[Tuple[str, bool, Any]]:
        return []

    # -------------------------------------------------------- helpers
    def lane_team(self, lane: str) -> str:
        return self.w._lane_team(lane)

    def cart_on(self, lane: str):
        return self.w.carts.get(self.lane_team(lane))

    def near(self, player, point: Sequence[float], r: float, dy: float = 4.0) -> bool:
        return flat(player.pos, point) <= r and abs(player.pos[1] - point[1]) <= dy

    def event(self, kind: str, player, team: str, **extra: Any) -> None:
        self.w._event(kind, player, team, **extra)

    def send(self, msg: Dict[str, Any]) -> None:
        self.w.broadcast(msg)

    def stat(self, player, key: str, amount: float = 1.0) -> None:
        self.w._stat(player, key, amount)

    def score(self, player, points: int, stat: str = "", badge: str = "") -> None:
        player.score += points
        if stat:
            self.stat(player, stat)
        if badge:
            self.w.badge(player, badge)


TWISTS: Dict[str, type] = {}


def register(cls: type) -> type:
    TWISTS[cls.kind] = cls
    return cls


def make(world, kind: str) -> Optional[Twist]:
    cls = TWISTS.get(kind)
    return cls(world) if cls is not None else None


def now() -> float:
    return engine.now()


# ======================================================== the railhead
RAIL_LEN = 6.0            # track one rail lays
LAY_R = 6.5               # how close to the railhead you lay one
LAY_HOLD = 1.1
PULL_HOLD = 2.0
STACK_R = 6.0
STACK_HOLD = 0.7


@register
class Railhead(Twist):
    """Golden Spike Summit: the line is not finished.

    Each lane has gaps (``extra["gaps"][lane]``: start and end distances) --
    graded and ballasted, no rails.  A cart stops at the end of what is
    laid.  Anybody can take a rail from a stack (``points["rails"]``) and
    carry it (slowly); a team lays its rails on its *own* line's first
    unfinished gap, a rail at a time, from the railhead -- before its cart
    gets there, if it is smart.  The other team can pull the last-laid rail
    back up while the cart is not on it, and walks off with it."""

    kind = "railhead"
    welcome = ("The line is not finished: carry rails from the stacks and hold E at "
               "your railhead to lay them. Pull up theirs before their cart gets there.")
    jobs = ("rails", "pulled")
    award = ("rails", "Spike Driver", "laid %d rails")
    job_lines = {"fetch_rail": ["getting rails", "rails for the railhead", "on rails"],
                 "pull_rail": ["pulling up their rails", "stealing a rail lol"]}

    def setup(self, area, extra, points, moment):
        self.gaps: Dict[str, List[Dict[str, Any]]] = {}
        for lane, spans in (extra.get("gaps") or {}).items():
            path = self.w.lanes.get(lane)
            if path is None:
                continue
            rows = []
            for span in spans:
                d0, d1 = float(span[0]), float(span[1])
                need = max(1, int(math.ceil((d1 - d0) / RAIL_LEN - 1e-6)))
                rows.append({"d0": d0, "d1": d1, "need": need, "laid": 0, "said": False})
            self.gaps[lane] = sorted(rows, key=lambda g: g["d0"])
        self.stacks = [list(m["p"]) for m in points.get("rails", [])]
        self.laid_total = 0
        self.pulled_total = 0
        self.carried = 0

    # ------------------------------------------------------------ lanes
    def open_gap(self, lane: str) -> Optional[Dict[str, Any]]:
        for gap in self.gaps.get(lane, []):
            if gap["laid"] < gap["need"]:
                return gap
        return None

    def head_d(self, gap: Dict[str, Any]) -> float:
        """How far along its line the laid track of a gap reaches."""
        return min(gap["d1"], gap["d0"] + gap["laid"] * RAIL_LEN)

    def head_point(self, lane: str, gap: Dict[str, Any]) -> List[float]:
        return self.w.lanes[lane].point(self.head_d(gap) + 1.5)

    def limit(self, cart, moment):
        gap = self.open_gap(cart.lane)
        if gap is None or cart.d > gap["d1"]:
            return None
        return (max(0.0, self.head_d(gap) - 3.5), "railhead")

    # -------------------------------------------------------- holding E
    def what_here(self, player, moment):
        team = player.team
        own = self.w.lane_for(team)
        carrying = self.carrying(player) == "rail"
        if carrying:
            gap = self.open_gap(own)
            if gap is not None and self.near(player, self.head_point(own, gap), LAY_R, 5.0):
                return ("lay", own, LAY_HOLD)
            return None
        if player.extra.get("coal"):
            return None
        # their railhead: pull up the last rail they laid
        for lane in self.gaps:
            if lane == own:
                continue
            gap = self.open_gap(lane)
            if gap is None or gap["laid"] <= 0:
                continue
            cart = self.cart_on(lane)
            if cart is not None and cart.d >= self.head_d(gap) - RAIL_LEN - 8.0:
                continue                      # the cart is on it: it stays down
            last = self.w.lanes[lane].point(self.head_d(gap) - RAIL_LEN / 2.0)
            if self.near(player, last, LAY_R, 5.0):
                return ("pull", lane, PULL_HOLD)
        for stack in self.stacks:
            if self.near(player, stack, STACK_R, 4.0):
                return ("rail", tuple(stack), STACK_HOLD)
        return None

    def do(self, player, kind, key, moment):
        if kind == "rail":
            player.extra["carry"] = "rail"
            self.carried += 1
            player.send({"t": "rrx", "k": "rail", "on": 1})
            return True
        if kind == "lay":
            gap = self.open_gap(key)
            if gap is None or self.carrying(player) != "rail":
                return True
            player.extra.pop("carry", None)
            gap["laid"] += 1
            self.laid_total += 1
            self.score(player, 6, "rails", "rr_rails")
            done = gap["laid"] >= gap["need"]
            self.send({"t": "rrx", "k": "lay", "lane": key, "laid": gap["laid"],
                       "need": gap["need"], "by": player.username, "done": 1 if done else 0})
            if done:
                self.score(player, 10)
                self.event("rr_railhead", player, self.lane_team(key),
                           what=self.w._place(self.w.lanes[key].point(gap["d1"])))
            self.w._broadcast_state()
            return True
        if kind == "pull":
            gap = self.open_gap(key)
            if gap is None or gap["laid"] <= 0 or self.carrying(player):
                return True
            gap["laid"] -= 1
            self.pulled_total += 1
            player.extra["carry"] = "rail"
            self.score(player, 6, "pulled", "rr_rails_pulled")
            victim = self.lane_team(key)
            self.send({"t": "rrx", "k": "pull", "lane": key, "laid": gap["laid"],
                       "need": gap["need"], "by": player.username})
            self.event("rr_rail_pulled", player, victim)
            self.w._broadcast_state()
            return True
        return False

    # ------------------------------------------------------------ state
    def state(self, moment):
        out = {}
        for lane, gaps in self.gaps.items():
            out[lane] = [{"d0": round(g["d0"], 1), "d1": round(g["d1"], 1), "need": g["need"],
                          "laid": g["laid"]} for g in gaps]
        return {"gaps": out}

    def context(self):
        lines = []
        for lane in sorted(self.gaps):
            gap = self.open_gap(lane)
            if gap is not None:
                lines.append("%s's line has %d of %d rails laid at its next gap." % (
                    self.w.team_name(self.lane_team(lane)), gap["laid"], gap["need"]))
        return lines

    # ------------------------------------------------------------- bots
    def _carriers(self, team: str) -> int:
        return sum(1 for p in self.w.playing() if p.team == team and self.carrying(p) == "rail")

    def carry_job(self, brain):
        p = brain.p
        own = self.w.lane_for(p.team)
        gap = self.open_gap(own)
        if gap is None:
            # nowhere to lay it: put it down and get back to the race
            p.extra.pop("carry", None)
            return None
        return {"k": "lay", "at": self.head_point(own, gap), "r": LAY_R - 2.0,
                "key": "lay%s%d" % (own, int(gap["d0"])), "say": "laying a rail at the railhead"}

    def urgent(self, brain):
        return self.carrying(brain.p) == "rail"

    def _stack_near(self, pos) -> Optional[List[float]]:
        best, best_d = None, 1e9
        for stack in self.stacks:
            d = flat(stack, pos)
            if d < best_d:
                best, best_d = stack, d
        return best

    def bot_job(self, brain, own, rival, moment):
        p = brain.p
        rng = brain.rng
        role = brain.role
        twist = self.w.pct("twist")
        gap = self.open_gap(own.lane)
        if gap is not None and gap["d0"] - own.d < 320.0 and role in ("pusher", "flex") and \
                self._carriers(p.team) < 3 and rng.random() < 0.35 + twist * 0.6:
            head = self.head_point(own.lane, gap)
            stack = self._stack_near(head) if flat(head, p.pos) < 220 else self._stack_near(p.pos)
            if stack is not None:
                return {"k": "fetch_rail", "at": [stack[0], max(0.0, stack[1] - 1.4), stack[2]],
                        "r": STACK_R - 2.0, "key": "stack%d%d" % (int(stack[0]), int(stack[2])),
                        "say": "fetching a rail for the railhead", "for": 40.0}
        raiding = role == "raider" or (role == "flex" and rival.fraction > own.fraction + 0.08)
        theirs = self.open_gap(rival.lane)
        if raiding and theirs is not None and theirs["laid"] > 0 and \
                0.0 < theirs["d0"] - rival.d < 200.0 and rng.random() < 0.3 + twist * 0.5:
            last = self.w.lanes[rival.lane].point(self.head_d(theirs) - RAIL_LEN / 2.0)
            return {"k": "pull_rail", "lane": rival.lane, "at": last, "r": LAY_R - 2.0,
                    "key": "pull%s%d" % (rival.lane, int(theirs["d0"])),
                    "say": "pulling up their rails", "for": 35.0}
        return None

    def job_valid(self, job, team):
        kind = job["k"]
        if kind == "fetch_rail":
            own = self.w.lane_for(team)
            return self.open_gap(own) is not None
        if kind == "pull_rail":
            gap = self.open_gap(job["lane"])
            cart = self.cart_on(job["lane"])
            return gap is not None and gap["laid"] > 0 and \
                (cart is None or cart.d < self.head_d(gap) - RAIL_LEN - 8.0)
        return None

    # ------------------------------------------------------------ tests
    def observe(self):
        return {"laid": self.laid_total, "pulled": self.pulled_total, "carried": self.carried,
                "open": sum(1 for gaps in self.gaps.values() for g in gaps if g["laid"] < g["need"])}

    def selftest(self, observations):
        laid = max([o.get("laid", 0) for o in observations] or [0])
        carried = max([o.get("carried", 0) for o in observations] or [0])
        return [("somebody carries rails from a stack", carried > 0, carried),
                ("somebody lays rails at a railhead", laid > 0, laid)]
