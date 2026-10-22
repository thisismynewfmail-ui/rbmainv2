"""Bots in the arena worlds: the shared brain, plus a plan per world.

The brain (``app/game/bots/brain.py``) already does what every bot does in
every world -- perceive, weigh its goals by persona, walk the nav graph,
aim like a person, go AFK, tilt, wander off -- and calls ``act`` on the
world's plan whenever its goal is the objective.  A plan is the part that
knows the game: where the dig sites are and who should go for them, when a
prop should hold still, which lever to pull, when to run.

Every plan is written against the same persona traits the rest of the bot
system uses (``brain.t("aggression")``, ``"objective"``, ``"support"``,
``"explore"``, ``"chaos"``, ``"social"``, ``"jumpy"``, ``"kindness"``...)
and against its own settings in the Bots Zone, read through :meth:`cfg`
(the world's section, e.g. ``cataclysm.panic`` arrives as
``cataclysm_panic``).

A plan answers the runner and the brain through a small interface:

``tick``         once a tick, before the bots think (team-wide planning)
``act``          one bot's objective, when it thinks
``pick_role``    a role at the start of a round
``goal_weights`` reshape the brain's goal weights for this world
``urgent``       nothing should distract this bot right now
``attention``    where real players are looking (full detail there)
``spread``       place the bots of a round that has just woken up
``summary``      the live view in the Bots Zone
``bot_state``    this bot's own situation, for the language model
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ..instance import EYE_HEIGHT, now
from .entities import flat_dist


def _wrap(angle: float) -> float:
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


class ArenaPlan:
    PREFIX = ""                # the world's settings section, e.g. "cataclysm"
    falls_kill = False         # a bot that falls off the stage is out (Bonk Brawl)
    # the persona table in the Bots Zone is the world's registry entry; this
    # is only the fallback for chat when a round wakes up
    SEED_LINES: Sequence[str] = ("gg", "lol", "nice", "lets go")

    def __init__(self, runner):
        self.runner = runner
        self.inst = runner.instance
        self.rng = random.Random()

    # ================================================================ basics
    def cfg(self, key: str, default: Any = None) -> Any:
        value = self.runner.cfg.get("%s_%s" % (self.PREFIX, key))
        return default if value is None else value

    def pct(self, key: str, default: float) -> float:
        try:
            return float(self.cfg(key, default)) / 100.0
        except (TypeError, ValueError):
            return default / 100.0

    def on(self, key: str, default: bool = True) -> bool:
        return bool(self.cfg(key, default))

    @property
    def nav(self):
        return self.runner.nav

    def nav_ready(self) -> bool:
        return self.nav is not None and self.nav.ready

    def mind(self, brain) -> Dict[str, Any]:
        if not isinstance(brain.mind, dict):
            brain.mind = {}
        return brain.mind

    def bots(self) -> List[Any]:
        return list(self.runner.brains.values())

    def alive(self, brain) -> bool:
        p = brain.p
        return p.alive and not p.extra.get("out")

    def doing(self, brain, text: str) -> None:
        self.mind(brain)["doing"] = text

    # ============================================================ interface
    def tick(self, moment: float) -> None:
        pass

    def act(self, brain) -> None:
        """One bot's objective.  The default wanders the place."""
        self.wander(brain)

    def pick_role(self, brain) -> str:
        return "player"

    def goal_weights(self, brain, weights: Dict[str, float]) -> None:
        pass

    def revenge_scale(self, brain) -> float:
        return 1.0

    def urgent(self, brain) -> bool:
        return False

    def forget(self, brain) -> None:
        pass

    def reset(self) -> None:
        for brain in self.bots():
            brain.mind = {}

    def attention(self) -> List[List[float]]:
        """Where somebody real is looking: their own spot, or whoever a
        spectator is watching."""
        out = []
        inst = self.inst
        for human in self.runner.humans:
            if human.alive and not human.extra.get("out"):
                out.append(list(human.pos))
                continue
            watched = inst.players.get(int(human.extra.get("watching", 0) or 0))
            if watched is not None and watched.alive:
                out.append(list(watched.pos))
        return out

    def spread(self, players: Sequence[Any]) -> None:
        """A round that has just woken up: the bots about the place, not in
        a stack on the spawn pads."""
        if not self.nav_ready():
            return
        centre = self.inst.area["centre"]
        half = self.inst.area["rect"][1] - centre[0]
        for p in players:
            if not p.alive:
                continue
            node = self.nav.random_node(self.rng, p.pos, min(60.0, half * 0.4))
            if node < 0:
                continue
            p.pos = self.nav.point(node)
            p.last_ground_pos = list(p.pos)
            if p.brain is not None:
                p.brain.ground = list(p.pos)
                p.brain.airborne = True

    def summary(self) -> Dict[str, Any]:
        inst = self.inst
        rows = []
        for brain in self.bots():
            m = self.mind(brain)
            rows.append({"name": brain.p.username, "team": brain.p.team,
                         "role": getattr(brain, "role", ""),
                         "doing": m.get("doing", "") or brain.goal,
                         "where": inst.landmark_near(brain.p.pos) or "",
                         "out": bool(brain.p.extra.get("out")) or not brain.p.alive})
        return {"area": inst.area["name"], "phase": inst.phase,
                "round_in_area": inst.rounds_here + 1, "per_area": inst.ROUNDS_PER_AREA,
                "scores": dict(inst.scores), "bots": rows[:30]}

    def bot_state(self, brain) -> Dict[str, Any]:
        m = self.mind(brain)
        out = {"role": getattr(brain, "role", "")}
        if m.get("doing"):
            out["doing"] = m["doing"]
        where = self.inst.landmark_near(brain.p.pos)
        if where:
            out["near"] = where
        return out

    def seed_lines(self) -> List[str]:
        return list(self.SEED_LINES)

    # ============================================================ movement
    def go(self, brain, point: Sequence[float], key: str = "", precise: bool = False,
           field: str = "") -> None:
        brain.go(list(point), key or "p%d_%d" % (int(point[0]), int(point[2])),
                 field=field, precise=precise)

    def arrived(self, brain, point: Sequence[float], radius: float = 3.5) -> bool:
        return flat_dist(brain.p.pos, point) <= radius and abs(brain.p.pos[1] - point[1]) < 5.0

    def random_point(self, near: Optional[Sequence[float]] = None,
                     radius: float = 80.0) -> Optional[List[float]]:
        if not self.nav_ready():
            return None
        if near is None:
            near = self.inst.area["centre"]
        node = self.nav.random_node(self.rng, near, radius)
        return self.nav.point(node) if node >= 0 else None

    def wander(self, brain, near: Optional[Sequence[float]] = None,
               radius: float = 90.0, tag: str = "wander") -> None:
        m = self.mind(brain)
        point = m.get("wander")
        if point is None or self.arrived(brain, point, 5.0) or now() > m.get("wander_until", 0):
            point = self.random_point(near or brain.p.pos, radius)
            m["wander"] = point
            m["wander_until"] = now() + self.rng.uniform(10, 24)
        if point is not None:
            self.go(brain, point, "%s%d" % (tag, int(point[0] * 7 + point[2])))
        self.doing(brain, "wandering about")

    def flee(self, brain, threat: Sequence[float], distance: float = 60.0,
             tag: str = "flee") -> None:
        """Somewhere well away from ``threat``, and on the far side of it
        from the bot -- not just anywhere."""
        m = self.mind(brain)
        spot = m.get("flee")
        if spot is not None and flat_dist(spot, threat) > distance * 0.6 and \
                not self.arrived(brain, spot, 4.0) and now() < m.get("flee_until", 0):
            self.go(brain, spot, "%s%d" % (tag, int(spot[0] * 3 + spot[2])))
            return
        p = brain.p
        away = math.atan2(p.pos[0] - threat[0], p.pos[2] - threat[2])
        best, best_score = None, -1e9
        for _ in range(8):
            a = away + self.rng.uniform(-1.0, 1.0)
            guess = [p.pos[0] + math.sin(a) * distance, p.pos[1], p.pos[2] + math.cos(a) * distance]
            point = self.random_point(guess, distance * 0.35)
            if point is None:
                continue
            score = flat_dist(point, threat) - flat_dist(point, p.pos) * 0.3
            if score > best_score:
                best, best_score = point, score
        if best is not None:
            m["flee"] = best
            m["flee_until"] = now() + self.rng.uniform(4, 9)
            self.go(brain, best, "%s%d" % (tag, int(best[0] * 3 + best[2])))

    def stop(self, brain) -> None:
        brain.waypoints = []
        brain.dest_key = ""

    def look_at(self, brain, point: Sequence[float], secs: float = 2.0) -> None:
        p = brain.p
        brain.look_yaw = math.atan2(point[0] - p.pos[0], point[2] - p.pos[2])
        brain.look_until = now() + secs

    def face(self, brain, point: Sequence[float]) -> Tuple[float, float, List[float]]:
        """Turn to look at ``point`` and return (yaw, pitch, direction)."""
        p = brain.p
        eye = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        dx, dy, dz = point[0] - eye[0], point[1] - eye[1], point[2] - eye[2]
        yaw = math.atan2(dx, dz)
        pitch = math.atan2(dy, math.hypot(dx, dz))
        p.yaw, p.pitch = yaw, pitch
        brain.aim_yaw, brain.aim_pitch = yaw, pitch
        cos_p = math.cos(pitch)
        return yaw, pitch, [math.sin(yaw) * cos_p, math.sin(pitch), math.cos(yaw) * cos_p]

    # =============================================================== using
    def hold_use(self, brain, point: Sequence[float], key: str, reach: float = 4.5) -> bool:
        """Walk to ``point`` and hold E there.  True while in place and
        holding."""
        p = brain.p
        inst = self.inst
        if flat_dist(p.pos, point) > reach or abs(p.pos[1] - point[1]) > 5.0:
            if p.extra.get("using"):
                inst.on_action(p, {"k": "unuse"})
            self.go(brain, point, key, precise=True)
            return False
        self.stop(brain)
        self.look_at(brain, point, 1.0)
        if not inst.channelling(p):
            inst.on_action(p, {"k": "unuse"})
            inst.on_action(p, {"k": "use"})
        else:
            p.extra["using"] = True
        return True

    def release(self, brain) -> None:
        p = brain.p
        if p.extra.get("using") or self.inst.channelling(p):
            self.inst.on_action(p, {"k": "unuse"})

    def press_use(self, brain) -> None:
        """A tap of E (not held)."""
        inst = self.inst
        inst.on_action(brain.p, {"k": "use"})
        inst.on_action(brain.p, {"k": "unuse"})

    def use_tool(self, brain, slot: int, at: Optional[Sequence[float]] = None) -> None:
        """Draw a world tool and fire it (at a point, or straight ahead)."""
        p = brain.p
        inst = self.inst
        if p.slot != slot or p.stowed:
            inst.handle_slot(p, {"i": slot})
        p.next_fire = 0.0
        if at is not None:
            _yaw, _pitch, direction = self.face(brain, at)
        else:
            cos_p = math.cos(p.pitch)
            direction = [math.sin(p.yaw) * cos_p, math.sin(p.pitch), math.cos(p.yaw) * cos_p]
        inst.handle_fire(p, {"d": direction})

    def draw_slot(self, brain, slot: int) -> None:
        p = brain.p
        if p.slot != slot or p.stowed:
            self.inst.handle_slot(p, {"i": slot})

    # ============================================================== seeing
    def sees(self, brain, other, reach: float = 160.0) -> bool:
        p = brain.p
        if flat_dist(p.pos, other.pos) > reach:
            return False
        eye = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        chest = [other.pos[0], other.pos[1] + 3.0, other.pos[2]]
        try:
            return self.inst.line_of_sight(eye, chest)
        except Exception:
            return False

    def in_view(self, brain, other, reach: float = 160.0, cone: float = 1.3) -> bool:
        p = brain.p
        dx, dz = other.pos[0] - p.pos[0], other.pos[2] - p.pos[2]
        if math.hypot(dx, dz) < 10.0:
            return self.sees(brain, other, reach)
        off = abs(_wrap(math.atan2(dx, dz) - p.yaw))
        return off < cone + brain.skill * 0.3 and self.sees(brain, other, reach)

    def nearest(self, brain, things: Iterable[Any], reach: float = 1e9):
        best, best_d = None, reach
        for thing in things:
            pos = thing.pos if hasattr(thing, "pos") else thing
            d = flat_dist(brain.p.pos, pos)
            if d < best_d:
                best, best_d = thing, d
        return best

    def others(self, brain, team: Optional[str] = None, enemy: bool = False):
        mine = brain.p.team
        for other in self.inst.players.values():
            if other is brain.p or not other.alive or other.extra.get("out"):
                continue
            if team is not None and other.team != team:
                continue
            if enemy and other.team == mine and not self.inst.friendly_fire:
                continue
            yield other

    def threat_near(self, brain, threats: Iterable[Any], radius: float) -> Optional[Any]:
        return self.nearest(brain, [t for t in threats
                                    if flat_dist(t.pos, brain.p.pos) < radius])


def persona_pick(rng: random.Random, weights: Dict[str, float]) -> str:
    """One key, chosen by its weight (all-zero falls back to the first)."""
    total = sum(max(0.0, w) for w in weights.values())
    if total <= 0:
        return next(iter(weights))
    roll = rng.random() * total
    for key, weight in weights.items():
        roll -= max(0.0, weight)
        if roll <= 0:
            return key
    return next(reversed(list(weights)))
