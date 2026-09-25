"""One bot in a live round: what it wants, where it walks, what it shoots.

**Behaviour** is a small utility system.  Every few hundred milliseconds the
bot weighs what it could be doing -- its role in the objective, a fight in
front of it, exploring, following somebody, standing about, messing around
-- by its persona and its situation, and commits to one for a while (no
dithering between two goals every frame).  Persona decides the weights, the
settings decide the floor: every bot keeps a small chance of doing
*anything*, so the most objective-minded bot on the server still wanders off
now and then, and the most chaotic one still grabs a flag it trips over.

It reacts to what happens to it.  Die too often in a short while and it
tilts -- goes after whoever keeps killing it, rushes, or gives up on the
objective and wanders.  Get killed and it may want revenge.  A person joining
gets a hello from somebody who likes saying hello.

**Movement** follows the navigation graph (flow fields for objectives, A* for
anything that moves), string-pulled into straight lines, with real jumps:
a ledge above step height is climbed with the same jump speed and gravity the
client uses, so what everybody sees is what a player could have done.

**Aim** is a person's: a reaction delay before the first shot, a turn rate,
an error that tightens the longer it tracks the same target and widens when
it or the target moves, and a trigger finger that does not always fire the
instant the weapon is ready.  Every shot goes through the server's own fire
path, so a bot cannot hit anything a player could not.

**Detail** follows attention.  A bot near a real player (or in view of one)
thinks several times a second and fights with real shots.  One on the far
side of the map thinks about once a second and settles fights with other
far-away bots by the odds of the weapons and skills involved -- the kill feed
is the same, the ray casts are not spent.
"""
from __future__ import annotations

import math
import random
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from ..instance import EYE_HEIGHT, GRAVITY, JUMP_SPEED, WALK_SPEED, now
from . import nav as nav_module

G = GRAVITY
STEP = nav_module.STEP_UP

QUICK = {
    "hello": ["hi", "hey", "yo", "hello", "sup", "hii", "heyy", "o/", "hi {name}",
              "yo {name}", "welcome {name}", "hey {name}"],
    "kill": ["ez", "gottem", "lol", "nice", "boom", "got him", "too easy", "sit"],
    "death": ["bruh", "rip", "lag", "how", "wow", "ok", "nooo", "no way", "bro",
              "what was that", "how did that hit"],
    "revenge": ["{name} again??", "who is this {name}", "ok {name} im coming",
                "{name} stop"],
    "capture": ["lets go", "nice cap", "GG", "yesss", "ez cap", "lets gooo", "w"],
    "lost": ["they have our flag", "flag!!", "stop the carrier", "defend",
             "someone get the flag back", "carrier mid"],
    "round": ["gg", "gg wp", "ggs", "good game", "gg all", "gg everyone", "gg ez"],
    "leave": ["gtg", "bye", "cya", "brb", "gn", "bye guys"],
    "build": ["nice", "big upgrade", "we're rich", "lets go", "one more"],
    "tilt": ["this is so unfair", "im done", "ok im trying now", "sweats everywhere",
             "cant win this"],
}


def styled(text: str, traits: Dict[str, float], rng: random.Random) -> str:
    """A line in a bot's own typing habits."""
    if traits.get("caps", 0) > 0.4 and rng.random() < 0.5:
        text = text.upper()
    elif traits.get("grammar", 0) > 0.55:
        text = text[:1].upper() + text[1:]
        if text[-1:].isalpha() and rng.random() < 0.6:
            text += rng.choice([".", "!"])
    elif traits.get("lower", 0) > 0.45:
        text = text.lower()
    if traits.get("emoji", 0) > 0.45 and rng.random() < 0.5:
        text += " " + rng.choice([":D", "xD", ":P", ":)", "<3", ":(" if "rip" in text else ":)"])
    return text


def _angle_to(dx: float, dy: float, dz: float) -> Tuple[float, float]:
    yaw = math.atan2(dx, dz)
    pitch = math.atan2(dy, math.hypot(dx, dz))
    return yaw, pitch


def _wrap(angle: float) -> float:
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


class Brain:
    def __init__(self, runner, player, spec: Dict[str, Any]):
        self.runner = runner
        self.p = player
        self.uid = int(spec.get("uid", 0))
        self.name = spec.get("name") or player.username
        self.tags = list(spec.get("tags") or [])
        self.traits: Dict[str, float] = {k: float(v) for k, v in
                                         (spec.get("traits") or {}).items()
                                         if isinstance(v, (int, float))}
        bias = spec.get("bias") or {}
        self.skill = float(bias.get("skill", self.traits.get("skill", 0.5)))
        self.reaction = max(0.06, float(bias.get("reaction", 450)) / 1000.0)
        self.aim_error = math.radians(max(0.2, float(bias.get("aim", 4.0))))
        self.objective = float(bias.get("objective", 0.6))
        self.rng = random.Random(self.uid * 7919 + int(time.time()))
        stats = spec.get("stats") or [0, 0, 0]
        self.base = (int(stats[0]), int(stats[1]), int(stats[2]))
        # movement
        self.waypoints: List[List[float]] = []
        self.dest: Optional[List[float]] = None
        self.dest_key = ""
        self.repath_at = 0.0
        self.airborne = False
        self.vy = 0.0
        self.land_y: Optional[float] = None
        self.speed = WALK_SPEED
        self.strafe = 0.0
        self.strafe_until = 0.0
        self.last_progress = (list(player.pos), now())
        self.ground = list(player.pos)
        # decisions
        self.goal = "objective"
        self.goal_until = 0.0
        self.goal_data: Dict[str, Any] = {}
        self.role = self._pick_role()
        self.next_think = now() + self.rng.uniform(0.0, 1.0)
        self.near = False
        # combat
        self.target: Optional[int] = None
        self.target_since = 0.0
        self.track = 0.0
        self.next_shot = 0.0
        self.aim_yaw = player.yaw
        self.aim_pitch = 0.0
        self.last_attacker: Optional[int] = None
        self.last_hit_at = 0.0
        # mood
        self.deaths: deque = deque(maxlen=12)
        self.tilt_until = 0.0
        self.revenge: Optional[int] = None
        self.afk_until = 0.0
        self.typing_until = 0.0
        self.jumpy_until = 0.0
        self.was_alive = player.alive
        self.said: deque = deque(maxlen=8)

    # =============================================================== basics
    def t(self, key: str, default: float = 0.5) -> float:
        return self.traits.get(key, default)

    @property
    def instance(self):
        return self.runner.instance

    def _pick_role(self) -> str:
        mode = self.runner.mode
        roll = self.rng.random()
        if mode == "captures":
            if roll < self.objective * 0.55:
                return "attack"
            if roll < self.objective * 0.55 + 0.25 + self.t("support", 0.2) * 0.3:
                return "defend"
            return "roam"
        if mode == "payload":
            return "cart" if roll < 0.35 + self.objective * 0.55 else "roam"
        return "tycoon" if roll < 0.25 + self.objective * 0.7 else "wander"

    def say(self, kind: str, name: str = "", chance: float = 1.0, delay: float = 0.0) -> None:
        cfg = self.runner.cfg
        if not cfg.get("messages_quick_reactions", True) or not cfg.get("messages_ingame_chat", True):
            return
        if not self.runner.humans:
            return
        chatty = self.t("chatty", 0.4)
        if self.rng.random() > chance * (0.3 + chatty):
            return
        options = QUICK.get(kind) or []
        if not options:
            return
        line = self.rng.choice(options)
        if "{name}" in line:
            if not name:
                line = line.replace(" {name}", "").replace("{name} ", "").replace("{name}", "")
            else:
                line = line.replace("{name}", name.lower() if self.t("lower", 0) > 0.45 else name)
        line = styled(line.strip(), self.traits, self.rng)
        if line in self.said:
            return
        self.said.append(line)
        self.runner.queue_chat(self, line, delay + self.rng.uniform(0.5, 2.2), quick=True)

    # ============================================================== events
    def on_spawn(self) -> None:
        self.ground = list(self.p.pos)
        self.waypoints = []
        self.dest = None
        self.airborne = False
        self.vy = 0.0
        self.target = None
        self.goal_until = 0.0
        if self.rng.random() < 0.1:
            self.role = self._pick_role()

    def on_death(self, killer) -> None:
        moment = now()
        self.deaths.append(moment)
        self.target = None
        recent = sum(1 for t in self.deaths if moment - t < 120)
        tilt_after = int(self.runner.cfg.get("tilt_deaths", 4) or 4)
        if killer is not None and killer is not self.p:
            self.last_attacker = killer.pid
            revenge = float(self.runner.cfg.get("revenge", 40)) / 100.0 \
                * (0.6 + self.t("aggression", 0.5))
            if self.runner.mode == "endless":
                revenge *= 0.35
            if self.rng.random() < revenge:
                self.revenge = killer.pid
        if recent >= tilt_after and moment > self.tilt_until:
            self.tilt_until = moment + self.rng.uniform(40, 120)
            self.say("tilt", chance=0.2 + self.t("toxicity", 0.1) * 0.6)
        elif killer is not None and killer is not self.p:
            if self.revenge == killer.pid and self.rng.random() < 0.4:
                self.say("revenge", killer.username, 0.18 + self.t("toxicity", 0.1) * 0.5)
            else:
                self.say("death", chance=0.08 + self.t("toxicity", 0.1) * 0.5)

    def hurt_by(self, attacker) -> None:
        """Somebody shot us: we know where they are now."""
        self.last_attacker = attacker.pid
        self.last_hit_at = now()
        if self.target is None and attacker.alive:
            self.target = attacker.pid
            self.target_since = now()
            self.track = 0.0
            self.next_shot = max(self.next_shot,
                                 now() + self.reaction * self.rng.uniform(0.9, 1.5))

    def on_kill(self, victim) -> None:
        if victim is not None and victim.pid == self.revenge:
            self.revenge = None
        self.say("kill", chance=0.04 + self.t("toxicity", 0.1) * 0.6)

    # ============================================================ movement
    def step(self, dt: float) -> None:
        p = self.p
        moment = now()
        p.last_message = moment
        p.last_input = moment
        if not p.alive:
            if self.was_alive:
                self.was_alive = False
            p.anim = "idle"
            return
        if not self.was_alive:
            self.was_alive = True
            self.on_spawn()
        vx = vz = 0.0
        moving = False
        still = moment < self.afk_until or moment < self.typing_until
        if not still and self.waypoints:
            target = self.waypoints[0]
            dx, dz = target[0] - p.pos[0], target[2] - p.pos[2]
            dist = math.hypot(dx, dz)
            speed = self.speed
            if dist < 0.6:
                self.waypoints.pop(0)
                if not self.airborne:
                    self._settle(target[1])
            else:
                ux, uz = dx / dist, dz / dist
                rise = target[1] - p.pos[1]
                if not self.airborne and rise > STEP + 0.1 and dist < 7.0:
                    # a ledge: jump for it, the way a player would
                    self.airborne = True
                    self.vy = JUMP_SPEED
                    self.land_y = target[1]
                vx, vz = ux * speed, uz * speed
                move = min(dist, speed * dt)
                p.pos[0] += ux * move
                p.pos[2] += uz * move
                moving = True
        # strafing in a fight
        if self.target is not None and moment < self.strafe_until and not still:
            side = self.strafe * self.speed * 0.55
            sx, sz = math.cos(self.aim_yaw) * side, -math.sin(self.aim_yaw) * side
            nx, nz = p.pos[0] + sx * dt, p.pos[2] + sz * dt
            if self._walkable(nx, p.pos[1], nz):
                p.pos[0], p.pos[2] = nx, nz
                vx += sx
                vz += sz
                moving = True
        # vertical
        if self.airborne:
            self.vy -= G * dt
            p.pos[1] += self.vy * dt
            floor = self._floor(p.pos[0], p.pos[1] + 0.5, p.pos[2])
            if self.vy <= 0 and floor is not None and p.pos[1] <= floor:
                p.pos[1] = floor
                self.airborne = False
                self.vy = 0.0
                self.land_y = None
                self.ground = list(p.pos)
        elif moving:
            floor = self._floor(p.pos[0], p.pos[1] + STEP + 0.2, p.pos[2])
            if floor is not None and floor < p.pos[1] - STEP - 0.2:
                # walked off an edge: fall
                self.airborne = True
                self.vy = 0.0
            elif floor is not None:
                p.pos[1] = floor
                self.ground = list(p.pos)
        elif moment < self.jumpy_until and self.rng.random() < dt * 1.6:
            self.airborne = True
            self.vy = JUMP_SPEED
        p.vel = [vx, self.vy if self.airborne else 0.0, vz]
        p.grounded = not self.airborne
        # where it is looking
        if self.target is not None:
            p.yaw, p.pitch = self.aim_yaw, self.aim_pitch
        elif moving and (vx or vz):
            want = math.atan2(vx, vz)
            p.yaw = p.yaw + _wrap(want - p.yaw) * min(1.0, dt * 8.0)
            p.pitch *= max(0.0, 1.0 - dt * 4.0)
            self.aim_yaw, self.aim_pitch = p.yaw, p.pitch
        elif still and self.rng.random() < dt * 0.4:
            p.yaw = _wrap(p.yaw + self.rng.uniform(-1.2, 1.2))
            self.aim_yaw = p.yaw
        horizontal = math.hypot(vx, vz)
        if self.airborne:
            p.anim = "jump" if self.vy > 1 else "fall"
        elif horizontal > self.speed * 0.65:
            p.anim = "run"
        elif horizontal > 1.5:
            p.anim = "walk"
        else:
            p.anim = "idle"
        if self.airborne and (p.pos[1] < self.ground[1] - nav_module.DROP_MAX - 6
                              or p.pos[1] < self.runner.kill_y + 4):
            # fell somewhere no path goes: back to solid ground, the way the
            # server snaps back a player it thinks has left the map
            p.pos = list(self.ground)
            self.airborne = False
            self.vy = 0.0
            self.waypoints = []
            self.repath_at = 0.0

    def _floor(self, x: float, y: float, z: float) -> Optional[float]:
        """The surface under a point.

        The graph only holds columns a whole player fits in, so the column
        right against a wall has no node even though there is floor there;
        the neighbouring columns are asked too, nearest first.
        """
        grid = self.runner.nav
        if grid is None or not grid.ready:
            return self.p.pos[1]
        ix, iz = grid.column(x, z)
        best = None
        for ring in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),
                     (1, 1), (1, -1), (-1, 1), (-1, -1)):
            ids = grid.cols.get((ix + ring[0]) * grid.nz + (iz + ring[1]))
            if not ids:
                continue
            for node in ids:
                top = grid.py[node]
                if top <= y + 0.05 and (best is None or top > best):
                    best = top
            if best is not None and ring == (0, 0):
                break
        return best

    def _walkable(self, x: float, y: float, z: float) -> bool:
        grid = self.runner.nav
        if grid is None or not grid.ready:
            return False
        ix, iz = grid.column(x, z)
        ids = grid.cols.get(ix * grid.nz + iz)
        return bool(ids) and any(abs(grid.py[n] - y) <= STEP for n in ids)

    def _settle(self, y: float) -> None:
        if abs(self.p.pos[1] - y) <= STEP + 0.2:
            self.p.pos[1] = y

    def go(self, point: List[float], key: str = "", field: str = "",
           precise: bool = False) -> None:
        """Head for ``point``: a flow field if one is named, else A*."""
        moment = now()
        if key and key == self.dest_key and self.waypoints and moment < self.repath_at:
            return
        grid = self.runner.nav
        self.dest = list(point)
        self.dest_key = key
        self.repath_at = moment + (6.0 if field else 2.5)
        p = self.p
        if grid is None or not grid.ready:
            self.waypoints = [list(point)]
            return
        start = grid.nearest(p.pos)
        if start < 0:
            self.waypoints = [list(point)]
            return
        nodes: Optional[List[int]] = None
        if field:
            dist = grid.field(field, point)
            if dist is not None and dist[start] < 1e29:
                nodes = grid.follow(start, dist, 120)
        if nodes is None:
            goal = grid.nearest(point, 3)
            if goal < 0:
                self.waypoints = [list(point)]
                return
            budget = self.runner.path_budget()
            nodes = grid.astar(start, goal, budget) or []
        points = grid.smooth(p.pos, nodes, 12)
        if precise and points:
            points.append(list(point))
        # a little of the player in the line: nobody walks the exact centre
        wobble = 1.2 * (1.0 - self.skill * 0.5)
        for pt in points[:-1]:
            pt[0] += self.rng.uniform(-wobble, wobble)
            pt[2] += self.rng.uniform(-wobble, wobble)
        self.waypoints = points or [list(point)]

    def near_point(self, point: List[float], radius: float) -> bool:
        return math.dist(self.p.pos, point) <= radius

    # ============================================================= thinking
    def think(self, moment: float, near: bool) -> None:
        p = self.p
        if not p.alive:
            return
        self.near = near
        cfg = self.runner.cfg
        interval = 1.0 / max(0.1, float(cfg.get("think_hz" if near else "far_think_hz", 4)))
        self.next_think = moment + interval * self.rng.uniform(0.8, 1.2)
        self._stuck_check(moment)
        self._perceive(moment, near)
        if moment >= self.goal_until or self._goal_invalid():
            self._choose_goal(moment, interval)
        self._pursue(moment)
        if self.target is not None:
            self._fight(moment, near, interval)
        else:
            self._housekeeping()

    def _stuck_check(self, moment: float) -> None:
        pos, at = self.last_progress
        if moment - at < 2.5:
            return
        moved = math.dist(pos, self.p.pos)
        self.last_progress = (list(self.p.pos), moment)
        if self.waypoints and moved < 1.0 and moment >= self.afk_until and \
                moment >= self.typing_until:
            # unstick: hop, and plan again from scratch
            if not self.airborne:
                self.airborne = True
                self.vy = JUMP_SPEED
            self.repath_at = 0.0
            self.dest_key = ""
            if self.rng.random() < 0.5:
                self.waypoints = []

    # -------------------------------------------------------- perception
    def _enemies(self):
        inst = self.instance
        mine = self.p.team
        for other in inst.players.values():
            if other is self.p or not other.alive:
                continue
            if other.team == mine and not inst.friendly_fire:
                continue
            yield other

    def _perceive(self, moment: float, near: bool) -> None:
        inst = self.instance
        p = self.p
        if self.target is not None:
            tgt = inst.players.get(self.target)
            if tgt is None or not tgt.alive or math.dist(tgt.pos, p.pos) > 260:
                self.target = None
            elif near and not self._sees(tgt):
                if moment - self.target_since > 1.5:
                    self.target = None
        if self.target is not None:
            return
        if self.runner.mode == "endless":
            # a tycoon is not a battlefield: people build, and only start
            # shooting when they are in that mood or somebody started it
            provoked = (self.last_attacker is not None and moment - self.last_hit_at < 6) \
                or self.revenge is not None
            if self.goal != "fight" and not provoked:
                return
        best, best_d = None, 1e9
        eye = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        checks = 2 if near else 0
        aggression = self.t("aggression", 0.5)
        reach = 90 + aggression * 90
        if self.runner.mode == "endless":
            reach = min(45.0, reach * (0.25 + self.t("aggression", 0.5) * 0.3))
        for other in self._enemies():
            d = math.dist(other.pos, p.pos)
            if d > reach and other.pid != self.revenge:
                continue
            # a view cone, unless they are close or just shot us
            dx, dz = other.pos[0] - p.pos[0], other.pos[2] - p.pos[2]
            off = abs(_wrap(math.atan2(dx, dz) - p.yaw))
            aware = off < 1.9 or d < 18 or other.pid == self.last_attacker and \
                moment - self.last_hit_at < 3
            if not aware:
                continue
            if d < best_d:
                best, best_d = other, d
        if best is None:
            return
        if near and checks:
            if not self._sees(best):
                return
        self.target = best.pid
        self.target_since = moment
        self.track = 0.0
        # a person needs a moment to react to somebody appearing
        self.next_shot = max(self.next_shot, moment + self.reaction * self.rng.uniform(0.8, 1.35))

    def _sees(self, other) -> bool:
        p = self.p
        eye = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        chest = [other.pos[0], other.pos[1] + 3.2, other.pos[2]]
        try:
            return self.instance.line_of_sight(eye, chest)
        except Exception:
            return False

    # -------------------------------------------------------------- goals
    def _goal_invalid(self) -> bool:
        if self.goal == "revenge":
            tgt = self.instance.players.get(self.revenge or 0)
            return tgt is None or not tgt.alive
        if self.goal == "follow":
            tgt = self.instance.players.get(self.goal_data.get("pid", 0))
            return tgt is None or not tgt.alive
        return False

    def _choose_goal(self, moment: float, interval: float) -> None:
        cfg = self.runner.cfg
        floor = float(cfg.get("anything_floor", 3)) / 100.0
        tangent = float(cfg.get("tangent_per_minute", 9)) / 100.0
        afk_rate = float(cfg.get("afk_per_minute", 3)) / 100.0
        tilted = moment < self.tilt_until
        weights = {
            "objective": max(floor, self.objective * (0.35 if tilted else 1.0)),
            "fight": max(floor, self.t("aggression", 0.5) * 0.45 + (0.4 if tilted else 0.0)),
            "explore": max(floor, tangent * (0.5 + self.t("explore", 0.2) * 2.5)),
            "afk": max(floor * 0.5, afk_rate * (0.5 + self.t("afk", 0.08) * 6)),
            "jumpy": max(floor * 0.5, tangent * self.t("jumpy", 0.2) * 1.5
                         + self.t("chaos", 0.08) * 0.2),
            "follow": max(floor * 0.5, tangent * (0.2 + self.t("social", 0.5)) * 0.8
                          if self.runner.humans else floor * 0.2),
            "revenge": 0.0,
        }
        if self.revenge is not None:
            weights["revenge"] = 0.6 + (1.0 if tilted else 0.0)
        if self.runner.mode == "endless":
            weights["fight"] *= 0.12
            weights["revenge"] *= 0.3
        goal = self.rng.choices(list(weights), list(weights.values()))[0]
        self.goal = goal
        self.goal_data = {}
        span = {"objective": (12, 40), "fight": (8, 20), "explore": (15, 45),
                "afk": (5, 35), "jumpy": (4, 12), "follow": (15, 50),
                "revenge": (20, 45)}[goal]
        self.goal_until = moment + self.rng.uniform(*span)
        self.speed = WALK_SPEED
        if goal == "afk":
            self.afk_until = self.goal_until
            self.waypoints = []
        elif goal == "jumpy":
            self.jumpy_until = self.goal_until
        elif goal == "follow" and self.runner.humans:
            self.goal_data["pid"] = self.rng.choice(self.runner.humans).pid
        elif goal == "explore":
            grid = self.runner.nav
            node = grid.random_node(self.rng, self.p.pos, 140) if grid and grid.ready else -1
            self.goal_data["point"] = grid.point(node) if node >= 0 else None

    def _pursue(self, moment: float) -> None:
        goal = self.goal
        if goal == "afk" or moment < self.afk_until:
            return
        if goal == "objective":
            self.runner.objective(self)
        elif goal == "fight":
            tgt = self.instance.players.get(self.target or 0)
            if tgt is None:
                # go where the fighting is: the objective, or a nearby enemy
                enemy = self._closest_enemy()
                if enemy is not None:
                    self.go(enemy.pos, "enemy%d" % enemy.pid)
                else:
                    self.runner.objective(self)
            elif self._prefers_close():
                self.go(tgt.pos, "enemy%d" % tgt.pid)
        elif goal == "explore":
            point = self.goal_data.get("point")
            if point:
                self.go(point, "explore")
                if self.near_point(point, 6):
                    self.goal_until = 0
            else:
                self.runner.objective(self)
        elif goal == "follow":
            tgt = self.instance.players.get(self.goal_data.get("pid", 0))
            if tgt is not None and math.dist(tgt.pos, self.p.pos) > 12:
                self.go(tgt.pos, "follow%d" % tgt.pid)
            else:
                self.waypoints = []
        elif goal == "revenge":
            tgt = self.instance.players.get(self.revenge or 0)
            if tgt is not None:
                self.go(tgt.pos, "revenge%d" % tgt.pid)
        elif goal == "jumpy":
            if self.rng.random() < 0.3:
                grid = self.runner.nav
                node = grid.random_node(self.rng, self.p.pos, 12) if grid and grid.ready else -1
                if node >= 0:
                    self.go(grid.point(node), "hop")

    def _closest_enemy(self):
        best, best_d = None, 1e9
        for other in self._enemies():
            d = math.dist(other.pos, self.p.pos)
            if d < best_d:
                best, best_d = other, d
        return best if best_d < 220 else None

    # -------------------------------------------------------------- combat
    def _weapons(self) -> List[Tuple[int, Dict[str, Any]]]:
        out = []
        for slot in range(5):
            item = self.p.weapon(slot)
            if not item:
                continue
            out.append((slot, self.p.weapon_stats(slot), item.get("item_id", "")))
        return out

    def _prefers_close(self) -> bool:
        stats = self.p.weapon_stats()
        return stats.get("kind") == "melee" or int(stats.get("pellets", 1) or 1) > 1 \
            or float(stats.get("range", 200)) < 80

    def _choose_weapon(self, distance: float) -> None:
        best_slot, best_score = self.p.slot, -1.0
        prefs = {"use_sniper": "wp_sniper", "use_shotgun": "wp_shotgun",
                 "use_smg": "wp_smg", "use_rifle": "wp_rifle", "use_sword": "wp_melee",
                 "use_stick": "wp_melee", "use_rocket": "wp_rocket",
                 "use_buildhammer": "wp_melee"}
        for slot, stats, item_id in self._weapons():
            kind = stats.get("kind")
            reach = float(stats.get("range", 200))
            if kind == "support":
                continue
            if distance > reach * 0.9:
                continue
            if kind == "melee":
                fit = 1.0 if distance < reach else 0.0
            elif int(stats.get("pellets", 1) or 1) > 1:
                fit = max(0.0, 1.0 - distance / 40.0)
            elif kind == "projectile":
                fit = 0.7 if 18 < distance < 90 else 0.15
            elif reach >= 600:
                fit = 0.9 if distance > 60 else 0.2
            else:
                fit = 0.65
            ammo = self.p.ammo[slot] + self.p.reserve[slot]
            if kind != "melee" and ammo <= 0:
                continue
            score = fit * (0.6 + self.t(prefs.get(item_id, ""), 0.3))
            if score > best_score:
                best_slot, best_score = slot, score
        if best_slot != self.p.slot or self.p.stowed:
            self.instance.handle_slot(self.p, {"i": best_slot})

    def _fight(self, moment: float, near: bool, interval: float) -> None:
        inst = self.instance
        tgt = inst.players.get(self.target or 0)
        if tgt is None or not tgt.alive:
            self.target = None
            return
        p = self.p
        distance = math.dist(tgt.pos, p.pos)
        self._choose_weapon(distance)
        stats = p.weapon_stats()
        kind = stats.get("kind", "hitscan")
        # keep moving in a fight: strafe, close in or back off by weapon
        if moment >= self.strafe_until:
            self.strafe = self.rng.choice((-1.0, 1.0)) if self.rng.random() < 0.3 + self.skill * 0.6 else 0.0
            self.strafe_until = moment + self.rng.uniform(0.4, 1.4)
        if self._prefers_close() and distance > float(stats.get("range", 10)) * 0.6:
            self.go(tgt.pos, "enemy%d" % tgt.pid)
        if near:
            self._aim_and_fire(moment, tgt, distance, stats, kind, interval)
        else:
            self._abstract_fire(moment, tgt, distance, stats, interval)

    def _aim_and_fire(self, moment, tgt, distance, stats, kind, interval) -> None:
        p = self.p
        eye = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        # lead a moving target a little, badly
        lead = 0.0 if kind != "projectile" else distance / float(stats.get("speed", 70) or 70)
        chest = [tgt.pos[0] + tgt.vel[0] * lead * 0.7,
                 tgt.pos[1] + (4.6 if self.rng.random() < 0.12 + self.skill * 0.18 else 3.0),
                 tgt.pos[2] + tgt.vel[2] * lead * 0.7]
        if kind == "projectile" and self.rng.random() < 0.5:
            chest[1] = tgt.pos[1] + 0.6            # rockets at the feet
        want_yaw, want_pitch = _angle_to(chest[0] - eye[0], chest[1] - eye[1], chest[2] - eye[2])
        turn = math.radians(260 + self.skill * 520) * interval
        dyaw = _wrap(want_yaw - self.aim_yaw)
        self.aim_yaw = _wrap(self.aim_yaw + max(-turn, min(turn, dyaw)))
        self.aim_pitch += max(-turn, min(turn, want_pitch - self.aim_pitch))
        self.track += interval
        if moment < self.next_shot:
            return
        if abs(_wrap(want_yaw - self.aim_yaw)) > 0.35:
            return
        reach = float(stats.get("range", 200))
        if distance > reach:
            return
        ammo = p.ammo[p.slot]
        if kind not in ("melee",) and ammo <= 0:
            self.instance.handle_reload(p)
            return
        # the error shrinks while tracking, grows when anyone moves
        moving = math.hypot(tgt.vel[0], tgt.vel[2]) / WALK_SPEED
        err = self.aim_error * (0.35 + 0.65 * math.exp(-self.track / 0.9)) * (1.0 + moving * 0.6)
        if self.airborne:
            err *= 1.8
        yaw = self.aim_yaw + self.rng.gauss(0, err)
        pitch = self.aim_pitch + self.rng.gauss(0, err * 0.7)
        cos_p = math.cos(pitch)
        direction = [math.sin(yaw) * cos_p, math.sin(pitch), math.cos(yaw) * cos_p]
        self.instance.handle_fire(p, {"d": direction})
        rpm = float(stats.get("rpm", 240) or 240)
        cadence = 60.0 / rpm
        if not stats.get("auto"):
            cadence *= 1.0 + (1.0 - self.skill) * self.rng.uniform(0.2, 1.1)
        self.next_shot = moment + cadence
        if self.rng.random() < 0.06 + self.t("jumpy", 0.2) * 0.12:
            self.airborne = True
            self.vy = JUMP_SPEED

    def _abstract_fire(self, moment, tgt, distance, stats, interval) -> None:
        """A fight nobody real can see, settled by the odds."""
        if tgt.brain is None or tgt.brain.near:
            return      # a person, or a bot somebody is watching: no dice
        reach = float(stats.get("range", 200))
        if distance > min(reach, 120):
            return
        if moment < self.next_shot:
            return
        kind = stats.get("kind", "hitscan")
        dps = float(stats.get("damage", 20)) * int(stats.get("pellets", 1) or 1) \
            * float(stats.get("rpm", 240) or 240) / 60.0
        if kind == "melee" and distance > reach:
            return
        falloff = max(0.25, 1.0 - distance / (reach * 1.3))
        accuracy = (0.12 + self.skill * 0.42) * falloff
        damage = dps * interval * accuracy * self.rng.uniform(0.4, 1.4)
        slot = self.p.slot
        if kind not in ("melee",) and self.p.ammo[slot] > 0:
            shots = max(1, int(float(stats.get("rpm", 240)) / 60.0 * interval))
            self.p.ammo[slot] = max(0, self.p.ammo[slot] - shots)
        elif kind not in ("melee",):
            self.instance.handle_reload(self.p)
            return
        if damage > 0.5:
            name = (self.p.weapon() or {}).get("name", "Unknown")
            self.instance.apply_damage(tgt, self.p, damage, name, False)
            tgt.brain.last_attacker = self.p.pid
            tgt.brain.last_hit_at = moment
            if tgt.brain.target is None:
                tgt.brain.target = self.p.pid
        self.next_shot = moment + 0.35

    def _housekeeping(self) -> None:
        p = self.p
        stats = p.weapon_stats()
        mag = int(stats.get("mag", 0) or 0)
        if mag and p.ammo[p.slot] < mag * 0.4 and p.reserve[p.slot] > 0 \
                and p.reload_until <= now():
            self.instance.handle_reload(p)

    # ============================================================ reporting
    def stats_delta(self) -> Tuple[int, int, int]:
        p = self.p
        return (max(0, p.kills - self.base[0]), max(0, p.deaths - self.base[1]),
                max(0, p.score - self.base[2]))
