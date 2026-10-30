"""Sky Sprint's course kit: the pieces every obstacle course is made of.

A course is a run of platforms in the sky from a start deck to a finish,
broken by checkpoints.  Every piece here draws its platforms *and* lays the
**line** along them -- ``route`` marks, in order, each saying how to get to
the next one (walk, jump, step onto a pad, wait for a hazard) -- which is
what the bots run, what the progress bar measures and what
``tools/mapcheck.py`` runs a simulated body along to prove every jump can be
made.

Moving things are described, not built: a sweeper's arm, a pendulum
hammer, a laser, a conveyor's belt and a gust of wind are numbers in
``extra`` that the server (for the bots) and the client (for you) turn into
the same motion from the same clock.  Platforms that come and go -- blinking
tiles, crumbling biscuits, the start gates -- are switchable solids.

The numbers to design to (app/game/instance.py): a run is 22 a second, a
jump leaves the ground at 34 and gravity is 62, so a jump rises 9.3 and a
flat one carries about 24 at a run.  Gaps here are kept to 12 and rises to
6, so a person who misses has misjudged it, not run out of legs.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..kit import ArenaArea

DECK_T = 1.2                  # how thick a platform is
WALK, JUMP, PAD = 0, 1, 2     # how to get from a route mark to the next one


class Course:
    """Everything one course knows about itself while it is being built."""

    def __init__(self, b: ArenaArea, theme: Dict[str, str]):
        self.b = b
        self.t = theme
        self.route: List[Dict[str, Any]] = []
        self.cps = 0
        self.extra: Dict[str, List[Any]] = {"belts": [], "sweepers": [], "hammers": [],
                                            "lasers": [], "blink": [], "crumble": [],
                                            "jelly": [], "taffy": [], "wind": []}
        self.hazards = 0
        self.dyn = 0

    # ------------------------------------------------------------- the line
    def node(self, x: float, y: float, z: float, how: int = WALK, **extra: Any) -> None:
        """The next point on the line; ``how`` is how to get from here to the
        one after (walk, jump, or walk onto the pad).  ``haz`` (a hazard's id)
        or ``blink`` (a tile group) says what to wait out here first."""
        entry: Dict[str, Any] = {"i": len(self.route), "seg": self.cps + 1, "how": how}
        entry.update(extra)
        self.b.mark("route", x, y, z, **entry)
        self.route.append({"p": (x, y, z), "how": how})

    def last(self) -> Tuple[float, float, float]:
        return self.route[-1]["p"]

    # ------------------------------------------------------------ platforms
    def deck(self, x0: float, x1: float, z0: float, z1: float, y: float,
             colour: Optional[str] = None, trim: Optional[str] = None,
             material: str = "", studs: bool = True, under: bool = True,
             skip: Sequence[str] = ()) -> None:
        """A platform whose top is at ``y``: a slab, a band of trim round its
        edge and a lighter skirt underneath.  ``skip`` names the sides
        ("x0", "x1", "z0", "z1") that butt against another deck, which get
        no trim (it would lie on the neighbour's top)."""
        b = self.b
        w, d = x1 - x0, z1 - z0
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        b.box([cx, y - DECK_T / 2.0, cz], [w, DECK_T, d], colour or self.t["deck"],
              studs=studs, material=material)
        edge = trim or self.t["trim"]
        em = self.t.get("trim_m", "")
        # the trim: thin bands on the slab's sides, flush with its top; the
        # x bands run the slab's depth, the z bands its width plus corners
        ex0 = x0 - (0.2 if "x0" not in skip else 0.0)
        ex1 = x1 + (0.2 if "x1" not in skip else 0.0)
        if "z0" not in skip:
            b.box([(ex0 + ex1) / 2.0, y - 0.3, z0 - 0.1], [ex1 - ex0, 0.6, 0.2], edge, collide=False,
                  material=em)
        if "z1" not in skip:
            b.box([(ex0 + ex1) / 2.0, y - 0.3, z1 + 0.1], [ex1 - ex0, 0.6, 0.2], edge, collide=False,
                  material=em)
        if "x0" not in skip:
            b.box([x0 - 0.1, y - 0.3, cz], [0.2, 0.6, d], edge, collide=False, material=em)
        if "x1" not in skip:
            b.box([x1 + 0.1, y - 0.3, cz], [0.2, 0.6, d], edge, collide=False, material=em)
        if under and w > 2.5 and d > 2.5:
            b.box([cx, y - DECK_T - 0.6, cz], [w - 1.6, 1.2, d - 1.6], self.t["under"],
                  collide=False)

    def pillar(self, x: float, z: float, top: float, bottom: float, r: float = 1.6,
               colour: Optional[str] = None) -> None:
        """A support under something, down to whatever is below.  Solid: a
        body that falls past one meets it, as it would a real one."""
        if top - bottom < 0.5:
            return
        self.b.cyl([x, (top + bottom) / 2.0, z], [r, top - bottom, r], colour or self.t["post"])

    def stones(self, points: Sequence[Tuple[float, float, float]], size: float = 6.0,
               colour: Optional[str] = None, shape: str = "box") -> None:
        """Stepping stones, jumped one to the next."""
        for k, (x, y, z) in enumerate(points):
            c = colour or (self.t["stone_a"] if k % 2 else self.t["stone_b"])
            if shape == "cyl":
                self.b.cyl([x, y - DECK_T / 2.0, z], [size, DECK_T, size], c, studs=True)
                self.b.cyl([x, y - DECK_T - 0.5, z], [size * 0.7, 1.0, size * 0.7], self.t["under"],
                           collide=False)
            else:
                self.deck(x - size / 2.0, x + size / 2.0, z - size / 2.0, z + size / 2.0, y,
                          colour=c, under=False)

    def rail(self, x0: float, z0: float, x1: float, z1: float, y: float,
             colour: Optional[str] = None, h: float = 2.4) -> None:
        """A low rail along an edge: a top bar on posts."""
        length = math.hypot(x1 - x0, z1 - z0)
        if length < 1.0:
            return
        yaw = math.atan2(x1 - x0, z1 - z0)
        c = colour or self.t["rail"]
        self.b.box([(x0 + x1) / 2.0, y + h, (z0 + z1) / 2.0], [0.4, 0.4, length], c,
                   r=[0.0, yaw, 0.0], collide=False)
        n = max(2, int(length / 6.0) + 1)
        for k in range(n):
            f = k / (n - 1)
            # each post runs up through the bar to a cap above it
            self.b.box([x0 + (x1 - x0) * f, y + (h + 0.4) / 2.0, z0 + (z1 - z0) * f],
                       [0.5, h + 0.4, 0.5], c, collide=False)

    # ----------------------------------------------------------- checkpoints
    def checkpoint(self, x: float, y: float, z: float, name: str, yaw: float = 0.0,
                   r: float = 8.0, finish: bool = False) -> None:
        """A checkpoint: an arch over the line, its banner in the course's
        colours, and the mark the rules watch for."""
        self.cps += 1
        b = self.b
        c, s = math.cos(yaw), math.sin(yaw)
        span = r + 1.0
        post = self.t["finish"] if finish else self.t["arch"]
        for side in (-1, 1):
            px, pz = x + c * span * side, z - s * span * side
            b.cyl([px, y + 5.0, pz], [1.2, 10.0, 1.2], post)
            b.sphere([px, y + 10.4, pz], [1.6, 1.6, 1.6], self.t["glow"], material="neon",
                     collide=False)
        b.box([x, y + 9.4, z], [span * 2.0, 1.2, 0.8], post, r=[0.0, yaw, 0.0], collide=False)
        label = "FINISH" if finish else "CHECKPOINT %d" % self.cps
        b.box([x, y + 11.1, z], [span * 1.4, 2.2, 0.3], post, r=[0.0, yaw, 0.0], collide=False,
              decal="t~%s~%s~#ffffff~%.2f" % (label, post, span * 1.4 / 2.2))
        b.cyl([x, y + 0.04, z], [r * 2.0, 0.08, r * 2.0], self.t["glow"], collide=False,
              material="neon", alpha=0.45)
        b.mark("cp", x, y, z, i=self.cps, r=r, name=name, finish=finish)

    # --------------------------------------------------------------- moving
    def pad(self, x: float, y: float, z: float, up: float = 62.0, forward: float = 0.0,
            yaw: float = 0.0, r: float = 2.6) -> None:
        """A jump pad: a ring set into the deck that throws you up (and on)."""
        b = self.b
        b.cyl([x, y + 0.15, z], [r * 2.0, 0.3, r * 2.0], self.t["pad"], material="metal",
              collide=False)
        b.cyl([x, y + 0.32, z], [r * 1.2, 0.06, r * 1.2], "#ffffff", material="neon",
              collide=False, alpha=0.7)
        b.mark("pad", x, y, z, v=up, f=forward, yaw=round(yaw, 3), r=r)

    def jelly(self, x0: float, x1: float, z0: float, z1: float, y: float, colour: str,
              up: float = 50.0, thick: float = 2.0) -> None:
        """A block of jelly set on the deck at ``y`` (its top ``thick`` higher,
        a step up): solid, wobbly, and a pad -- whoever lands on it is
        bounced (the client wobbles it)."""
        b = self.b
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        b.box([cx, y + thick / 2.0, cz], [x1 - x0, thick, z1 - z0], colour, material="glass",
              alpha=0.82)
        y += thick
        r = round(min(x1 - x0, z1 - z0) / 2.0 * 0.92, 2)
        b.mark("pad", cx, y, cz, v=up, f=0.0, yaw=0.0, r=r, jelly=1, c=colour,
               s=[x1 - x0, z1 - z0])

    def boost(self, x: float, y: float, z: float, yaw: float, length: float = 8.0,
              width: float = 4.0, speed: float = 48.0) -> None:
        """A speed strip: chevrons on the deck that fling you along it."""
        b = self.b
        b.box([x, y + 0.05, z], [width, 0.1, length], self.t["boost"], r=[0.0, yaw, 0.0],
              material="neon", collide=False, alpha=0.6)
        for k in range(3):
            off = (k - 1) * length / 3.2
            b.box([x + math.sin(yaw) * off, y + 0.12, z + math.cos(yaw) * off],
                  [width * 0.8, 0.06, 0.6], "#ffffff", r=[0.0, yaw, 0.0], material="neon",
                  collide=False, alpha=0.8)
        b.mark("boost", x, y, z, yaw=round(yaw, 3), l=length, w=width, speed=speed)

    def belt(self, x0: float, x1: float, z0: float, z1: float, y: float,
             vx: float, vz: float, skip: Sequence[str] = ()) -> None:
        """A conveyor: the deck itself, with the rollers at its ends; the
        belt's motion is the client's and the server's to apply."""
        b = self.b
        self.deck(x0, x1, z0, z1, y, colour=self.t["belt"], studs=False, under=False, skip=skip)
        # the rollers under each end, and the frame between them
        ry = y - DECK_T - 0.75
        if abs(vx) >= abs(vz):
            for xe in (x0 + 1.0, x1 - 1.0):
                b.cyl([xe, ry, (z0 + z1) / 2.0], [1.5, z1 - z0 - 0.4, 1.5], self.t["roller"],
                      r=[math.pi / 2.0, 0.0, 0.0], collide=False, material="metal")
            b.box([(x0 + x1) / 2.0, ry, (z0 + z1) / 2.0], [x1 - x0 - 3.6, 1.5, z1 - z0 - 1.6],
                  self.t["under"], collide=False)
        else:
            for ze in (z0 + 1.0, z1 - 1.0):
                b.cyl([(x0 + x1) / 2.0, ry, ze], [1.5, x1 - x0 - 0.4, 1.5], self.t["roller"],
                      r=[0.0, 0.0, math.pi / 2.0], collide=False, material="metal")
            b.box([(x0 + x1) / 2.0, ry, (z0 + z1) / 2.0], [x1 - x0 - 1.6, 1.5, z1 - z0 - 3.6],
                  self.t["under"], collide=False)
        lo, hi = b.at(x0, y, z0), b.at(x1, y, z1)
        self.extra["belts"].append({"rect": [lo[0], hi[0], lo[2], hi[2]], "y": round(y, 2),
                                    "v": [round(vx, 2), round(vz, 2)]})

    def sweeper(self, x: float, y: float, z: float, r: float, w: float = 1.4,
                h: float = 2.2, arms: int = 2, speed: float = 1.4, phase: float = 0.0,
                hub: float = 2.6, look: str = "") -> int:
        """A hub on a round deck with arms that sweep round it at ``h`` over
        the deck: jump them, or be knocked off."""
        b = self.b
        b.cyl([x, y + 2.4, z], [hub, 4.8, hub], self.t["hub"], material="metal")
        b.cyl([x, y + 5.0, z], [hub * 0.7, 0.6, hub * 0.7], self.t["glow"], material="neon",
              collide=False)
        self.extra["sweepers"].append({"c": b.at(x, y, z), "r": r, "h": h, "t": w, "arms": arms,
                                       "w": speed, "ph": round(phase, 3), "id": self.hazards,
                                       "look": look or self.t.get("look", "")})
        self.hazards += 1
        return self.hazards - 1

    def hammer(self, px: float, py: float, pz: float, length: float, axis: str,
               amp: float = 1.0, period: float = 2.6, phase: float = 0.0,
               head: Sequence[float] = (4.0, 4.0, 4.0)) -> int:
        """A pendulum hung from a beam at (px, py, pz), swinging in the
        plane of ``axis`` ('x' or 'z') across the line."""
        b = self.b
        # the bearing it hangs from, under whatever holds it up
        b.box([px, py - 0.6, pz], [3.0, 1.2, 3.0], self.t["hub"], collide=False, material="metal")
        self.extra["hammers"].append({"pivot": b.at(px, py, pz), "len": length, "axis": axis,
                                      "amp": amp, "period": period, "ph": round(phase, 3),
                                      "head": list(head), "id": self.hazards})
        self.hazards += 1
        return self.hazards - 1

    def laser(self, ax: float, ay: float, az: float, bx: float, bz: float,
              move: Sequence[float], period: float = 3.0, phase: float = 0.0) -> int:
        """A beam from (ax, az) to (bx, bz) at ``ay``, sliding back and forth
        by ``move``; touch it and you are back at your checkpoint."""
        b = self.b
        self.extra["lasers"].append({"a": b.at(ax, ay, az), "b": b.at(bx, ay, bz),
                                     "move": [round(m, 2) for m in move], "period": period,
                                     "ph": round(phase, 3), "id": self.hazards})
        self.hazards += 1
        return self.hazards - 1

    def blinking(self, group: str, period: float, on: float, phase: float) -> None:
        """A group of switchable tiles that come and go on a beat."""
        self.extra["blink"].append({"group": group, "period": period, "on": on,
                                    "ph": round(phase, 3)})

    def tile(self, key: str, x0: float, x1: float, z0: float, z1: float, y: float,
             colour: str, group: str = "", material: str = "") -> None:
        """One switchable platform (blinking, crumbling)."""
        b = self.b
        with b.detached() as parts:
            b.box([(x0 + x1) / 2.0, y - DECK_T / 2.0, (z0 + z1) / 2.0], [x1 - x0, DECK_T, z1 - z0],
                  colour, studs=True, material=material)
            b.box([(x0 + x1) / 2.0, y - DECK_T - 0.35, (z0 + z1) / 2.0],
                  [x1 - x0 - 0.8, 0.7, z1 - z0 - 0.8], self.t["under"], collide=False)
        b.dynamic(key, parts, on=True, group=group)

    def crumble(self, key: str, x0: float, x1: float, z0: float, z1: float, y: float,
                colour: str) -> None:
        self.tile(key, x0, x1, z0, z1, y, colour, group="crumble")
        lo, hi = self.b.at(x0, y, z0), self.b.at(x1, y, z1)
        self.extra["crumble"].append({"key": key, "rect": [lo[0], hi[0], lo[2], hi[2]],
                                      "y": round(y, 2)})

    def zone(self, kind: str, x0: float, x1: float, z0: float, z1: float, y: float,
             **extra: Any) -> None:
        """A patch of deck that does something to whoever stands on it (jelly
        bounces you, taffy slows you, wind blows over it)."""
        lo, hi = self.b.at(x0, y, z0), self.b.at(x1, y, z1)
        entry = {"rect": [lo[0], hi[0], lo[2], hi[2]], "y": round(y, 2)}
        entry.update(extra)
        self.extra[kind].append(entry)

    def power(self, x: float, y: float, z: float) -> None:
        """Where a power-up turns up."""
        self.b.cyl([x, y + 0.1, z], [3.4, 0.2, 3.4], self.t["glow"], material="neon",
                   collide=False, alpha=0.5)
        self.b.mark("power", x, y, z)

    # ------------------------------------------------------------- the start
    def start(self, x: float, y: float, z: float, yaw: float, width: float = 34.0,
              depth: float = 22.0) -> Tuple[float, float, float]:
        """The start deck: two lanes, red and blue, behind a gate that drops
        at GO.  Returns the middle of the gate line."""
        b = self.b
        c, s = math.cos(yaw), math.sin(yaw)
        fx, fz = s, c                       # forward
        rx, rz = c, -s                      # right
        # the deck itself, laid out along +z and turned
        hw, hd = width / 2.0, depth / 2.0
        corners = [(x + rx * a + fx * f, z + rz * a + fz * f) for a in (-hw, hw) for f in (-hd, hd)]
        x0, x1 = min(p[0] for p in corners), max(p[0] for p in corners)
        z0, z1 = min(p[1] for p in corners), max(p[1] for p in corners)
        front = ("x1" if fx > 0.5 else "x0" if fx < -0.5 else "z1" if fz > 0.5 else "z0")
        self.deck(x0, x1, z0, z1, y, colour=self.t["start"], skip=(front,))
        gx, gz = x + fx * hd, z + fz * hd
        # the lanes painted on the deck, and the spawns
        for team, side, colour in (("red", -1, "#d84a3a"), ("blue", 1, "#3a7ad8")):
            lx, lz = x + rx * side * hw / 2.0, z + rz * side * hw / 2.0
            b.box([lx, y + 0.03, lz], [abs(rx) * (hw - 2.0) + abs(fx) * (depth - 2.0), 0.06,
                                         abs(rz) * (hw - 2.0) + abs(fz) * (depth - 2.0)],
                  colour, collide=False, alpha=0.55)
            for k in range(8):
                a = side * (3.0 + (k % 4) * (hw - 5.0) / 3.0)
                f = -hd + 4.0 + (k // 4) * 5.0
                b.team_spawn(team, x + rx * a + fx * f, y, z + rz * a + fz * f, yaw=yaw)
        # the gate: a bar across the front of each lane, switched off at GO
        with b.detached() as parts:
            b.box([gx, y + 3.0, gz], [abs(rx) * width + abs(fx) * 1.0, 6.0,
                                      abs(rz) * width + abs(fz) * 1.0], self.t["gate"],
                  material="glass", alpha=0.6)
        b.dynamic("gate", parts, on=True, group="gate")
        # its posts stand on the deck just behind the gate line
        for side in (-1, 1):
            px = gx + rx * side * (hw - 1.0) - fx * 1.5
            pz = gz + rz * side * (hw - 1.0) - fz * 1.5
            b.box([px, y + 4.5, pz], [2.0, 9.0, 2.0], self.t["arch"])
        bx, bz = gx - fx * 1.5, gz - fz * 1.5
        b.box([bx, y + 10.0, bz], [abs(rx) * width + abs(fx) * 2.0, 2.0,
                                   abs(rz) * width + abs(fz) * 2.0], self.t["arch"],
              decal="t~SKY SPRINT~%s~#ffffff~%.2f" % (self.t["arch"], width / 2.0))
        return gx, y, gz

    # -------------------------------------------------------------- finish
    def done(self, fall_y: float, twist: str, **extra: Any) -> None:
        """Hand the course's numbers to the rules."""
        self.b.extra.update({k: v for k, v in self.extra.items() if v})
        self.b.extra.update({"fall_y": fall_y, "twist": twist, "checkpoints": self.cps,
                             "route_len": len(self.route)})
        self.b.extra.update(extra)
