"""The building kit for Blackout Relay's maps.

Every map is capture the flag the Blackout Relay way: red's flag at the
west end, blue's at the east, and both teams deploying out of the *relay*
in the middle -- the one building the whole map turns on -- each through
the doors on its own side.  Two *outposts* on each half are where a team
falls back to while its flag is away (Outpost lockdown), which puts them
across the carrier's road home.

**Mirrored.**  A capture-the-flag map is fair or it is nothing, so every
solid on one half has a twin on the other, to the hundredth of a unit, and
``tools/mapcheck.py`` holds every map to it (the package says
``MIRROR_AXIS = "x"``).  The way to keep that true while drawing anything
is :class:`Half`: build one team's half with magnitudes along x and let it
flip them -- the same code builds both, so they cannot drift apart.  Only
decoration (no collision) is free to differ: a red banner here and a blue
one there.

**Areas sit on the z axis** (app/game/maps/relay/__init__.py), so that
mirror line is the world's own x = 0 for every one of them.

**Terrain is added, not dug** -- the ground is one plane at y = 0 (Last
Light's rule) -- except where a map carves a channel: then the ground plate
is cut round it and the channel gets a floor and sides of its own.  Hills,
ridges and terraces are stacks of slabs, each tier sitting on the one below
(never through it), so no two faces ever share a plane facing the same way.
A tier 2 units high is a step; anything taller needs stairs (``flight``).
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ..events.kit import (  # noqa: F401  (re-exported for the area modules)
    ASPHALT, BRICK, BRICK_DARK, CONCRETE, CONCRETE_DARK, CONCRETE_LIGHT, GLASS,
    HAZARD, LAMP, LINE_WHITE, LINE_YELLOW, PAVEMENT, RUST, STEEL, STEEL_DARK,
    WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, Surfaces, backdrop, barrier, bench,
    building, car, carve, crate, crenels, deploy_pad, dumpster, flight, floodlight, gable,
    hazard_rim, holed_wall, kerb, lantern, letters, plate, rect, ring_points,
    room_walls, sandbags, sign_decal, slab, step_paint, strip_light, wall,
    wall_sign)
from ..lastlight.kit import face_sign  # noqa: F401

Rect = Tuple[float, float, float, float]

TEAMS = ("red", "blue")
RED = "#c4281c"
RED_DARK = "#8c1c15"
RED_NEON = "#ff6a54"
RED_LIGHT = "#e8705e"
BLUE = "#0d69ac"
BLUE_DARK = "#0a3c69"
BLUE_NEON = "#63c0ff"
BLUE_LIGHT = "#5a9fd6"
TEAM_COLOUR = {"red": RED, "blue": BLUE}
TEAM_DARK = {"red": RED_DARK, "blue": BLUE_DARK}
TEAM_NEON = {"red": RED_NEON, "blue": BLUE_NEON}
TEAM_LIGHT = {"red": RED_LIGHT, "blue": BLUE_LIGHT}
STAIR_LIGHT = "#9fe8ff"

FLAG_LIFT = 0.2         # the flag marker floats this far over the pedestal top
NEW_CAPTURES = 3        # the new maps' rounds: first to three...
NEW_ROUND = 900.0       # ...or fifteen minutes


# =================================================================== the area
class RelayArea(ArenaArea):
    """One Blackout Relay map, drawn round the origin (red at -x)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.markers: Dict[str, Any] = {"mode": "ctf"}
        self.probes: List[Dict[str, Any]] = []
        self.captures_to_win = NEW_CAPTURES
        self.round_seconds = NEW_ROUND
        self.intro: List[str] = []

    # --------------------------------------------------------- the flags
    def flag(self, team: str, x: float, y: float, z: float, radius: float = 16.0) -> None:
        """Where ``team``'s flag stands: ``y`` is the top of its pedestal."""
        point = self.at(x, y + FLAG_LIFT, z)
        self.markers["flag_%s" % team] = {"p": point, "team": team}
        self.markers["base_%s" % team] = {"p": point, "radius": radius}
        self.mark("flag", x, y + FLAG_LIFT, z, team=team)
        self.probes.append({"p": point, "label": "flag_%s" % team})

    def muster(self, team: str, x: float, y: float, z: float, yaw: float,
               pad: bool = True, size: float = 7.0) -> None:
        """A deploy pad in the relay: where ``team`` comes in."""
        if pad:
            deploy_pad(self, x, z, y, TEAM_COLOUR[team], size)
        self.team_spawn(team, x, y + 1.0, z, yaw)
        entry = {"p": self.at(x, y + 1.0, z), "yaw": round(yaw, 3)}
        self.markers.setdefault("muster_%s" % team, []).append(entry)
        self.probes.append({"p": entry["p"], "label": "muster_%s" % team})

    def outpost(self, team: str, x: float, y: float, z: float, yaw: float,
                pad: bool = True, size: float = 6.5) -> None:
        """A lockdown spawn: where ``team`` comes back while its flag is out."""
        if pad:
            deploy_pad(self, x, z, y, "#9fe8ff", size)
        entry = {"p": self.at(x, y + 1.0, z), "yaw": round(yaw, 3)}
        self.markers.setdefault("outpost_%s" % team, []).append(entry)
        self.mark("outpost", x, y + 1.0, z, team=team)
        self.probes.append({"p": entry["p"], "label": "outpost_%s" % team})

    def relay(self, name: str, radius: float) -> None:
        self.markers["relay"] = {"radius": radius, "name": name}

    # ----------------------------------------------------------- finish
    def finish(self) -> Dict[str, Any]:
        record = super().finish()
        markers = dict(self.markers)
        markers["captures_to_win"] = int(self.captures_to_win)
        markers["round_seconds"] = float(self.round_seconds)
        markers["intro"] = list(self.intro)
        for team in TEAMS:
            for key in ("flag_%s" % team, "muster_%s" % team, "outpost_%s" % team):
                if key not in markers:
                    raise ValueError("relay map %s has no %s" % (self.id, key))
        record["markers"] = markers
        record["probes"] = list(self.probes)
        return record


# ================================================================ the mirror
class Half:
    """One team's half of a mirrored map.

    Every x handed to it is a distance from the centre line, flipped onto
    the team's own side (red west, blue east); z and y are as given.  Parts
    turned about y turn the other way on the other side.  ``inward`` and
    ``outward`` are facings towards the middle and towards the team's end.
    """

    def __init__(self, b: RelayArea, sx: int):
        self.b = b
        self.sx = sx
        self.team = "red" if sx < 0 else "blue"
        self.enemy = "blue" if sx < 0 else "red"
        self.colour = TEAM_COLOUR[self.team]
        self.dark = TEAM_DARK[self.team]
        self.neon = TEAM_NEON[self.team]
        self.light = TEAM_LIGHT[self.team]
        self.inward = "x+" if sx < 0 else "x-"
        self.outward = "x-" if sx < 0 else "x+"
        # the yaw that looks towards the middle of the map
        self.yaw_in = math.pi / 2.0 if sx < 0 else -math.pi / 2.0
        self.yaw_out = -self.yaw_in

    def x(self, v: float) -> float:
        return self.sx * v

    def xs(self, a: float, c: float) -> Tuple[float, float]:
        return (min(self.sx * a, self.sx * c), max(self.sx * a, self.sx * c))

    def r(self, x0: float, x1: float, z0: float, z1: float) -> Rect:
        lo, hi = self.xs(x0, x1)
        return (lo, hi, min(z0, z1), max(z0, z1))

    def face(self, facing: str) -> str:
        """A facing as seen from this side ("x+" on red is "x-" on blue)."""
        if self.sx > 0 and facing.startswith("x"):
            return "x-" if facing == "x+" else "x+"
        return facing

    def _rot(self, r):
        if not r:
            return r
        return [r[0], -r[1] if self.sx > 0 else r[1], -r[2] if self.sx > 0 else r[2]]

    def box(self, x, y, z, w, h, d, c, **kw):
        if "r" in kw:
            kw["r"] = self._rot(kw["r"])
        return self.b.box([self.sx * x, y, z], [w, h, d], c, **kw)

    def cyl(self, x, y, z, w, h, d, c, **kw):
        if "r" in kw:
            kw["r"] = self._rot(kw["r"])
        return self.b.cyl([self.sx * x, y, z], [w, h, d], c, **kw)

    def sphere(self, x, y, z, w, h, d, c, **kw):
        if "r" in kw:
            kw["r"] = self._rot(kw["r"])
        return self.b.sphere([self.sx * x, y, z], [w, h, d], c, **kw)

    def cone(self, x, y, z, w, h, d, c, **kw):
        if "r" in kw:
            kw["r"] = self._rot(kw["r"])
        return self.b.cone([self.sx * x, y, z], [w, h, d], c, **kw)

    def slab(self, x0, x1, z0, z1, top, thick, c, **kw):
        return slab(self.b, self.r(x0, x1, z0, z1), top, thick, c, **kw)

    def flight_x(self, near: float, far: float, z0: float, z1: float, y_near: float,
                 y_far: float, c: str, **kw) -> None:
        """A stair running along x, from ``near`` to ``far`` (magnitudes)."""
        flight(self.b, "x", self.sx * near, self.sx * far, min(z0, z1), max(z0, z1),
               y_near, y_far, c, **kw)

    def flight_z(self, near: float, far: float, x0: float, x1: float, y_near: float,
                 y_far: float, c: str, **kw) -> None:
        lo, hi = self.xs(x0, x1)
        flight(self.b, "z", near, far, lo, hi, y_near, y_far, c, **kw)

    def car(self, x: float, z: float, along: str = "x", colour: str = "#8a2a24",
            y: float = 0.0, wrecked: bool = False) -> None:
        """A car whose twin on the other half is its mirror image."""
        sedan(self.b, self.sx * x, z, along=along, colour=colour, y=y,
              flip=self.sx if along == "x" else 1, wrecked=wrecked)

    def sign(self, x, y, z, w, h, decal, facing, colour="#f2f3f3") -> None:
        face_sign(self.b, self.sx * x, y, z, w, h, decal, self.face(facing), colour)


def halves(b: RelayArea) -> List[Half]:
    return [Half(b, -1), Half(b, 1)]


def mirror_x(points: Iterable[Tuple[float, float]]) -> List[Tuple[float, float]]:
    return [(-x, z) for x, z in points]


# ==================================================================== terrain
def ground(b: RelayArea, colour: str, soil: str = "#5a4a38", holes: Sequence[Rect] = (),
           studs: bool = True, material: str = "grass") -> None:
    """The ground plane out to under the boundary, with ``holes`` left
    for channels the map digs (it fills them in itself)."""
    m = b.margin
    whole = rect(-b.half_x - m, b.half_x + m, -b.half_z - m, b.half_z + m)
    pieces = carve(whole, list(holes)) if holes else [whole]
    plate(b, pieces, 0.0, 0.6, colour, studs=studs, material=material)
    plate(b, pieces, -0.6, 5.4, soil)


def tier_stack(b, footprints: Sequence[Sequence[Rect]], y0: float, rises: Sequence[float],
               colours: Sequence[str], studs: bool = True, material: str = "") -> float:
    """Terraces: tier k is ``footprints[k]`` (non-overlapping rectangles),
    a slab from the top of the tier below to ``rises[k]`` higher.  Returns
    the top.  Each tier must lie on the one below it."""
    y = y0
    for k, rects in enumerate(footprints):
        rise = rises[k] if k < len(rises) else rises[-1]
        colour = colours[k] if k < len(colours) else colours[-1]
        for r in rects:
            if r[1] - r[0] < 1e-3 or r[3] - r[2] < 1e-3:
                continue
            slab(b, r, y + rise, rise, colour, studs=studs,
                 **({"material": material} if material else {}))
        y += rise
    return y


def ellipse_rects(cx: float, cz: float, rx: float, rz: float, band: float = 6.0,
                  quant: float = 1.0) -> List[Rect]:
    """An ellipse as a stack of z-bands, ``band`` deep, on a grid shared
    by every ellipse with the same centre and band (so tiers line up)."""
    out: List[Rect] = []
    if rx <= 0 or rz <= 0:
        return out
    n = int(rz // band)
    for k in range(-n, n):
        z0, z1 = cz + k * band, cz + (k + 1) * band
        mid = abs((k + 0.5) * band)
        if mid >= rz:
            continue
        half = rx * math.sqrt(max(0.0, 1.0 - (mid / rz) ** 2))
        half = math.floor(half / quant) * quant
        if half < band * 0.5:
            continue
        out.append((cx - half, cx + half, z0, z1))
    return out


def mound(b, cx: float, cz: float, rx: float, rz: float, levels: int, rise: float,
          colours: Sequence[str], y0: float = 0.0, band: float = 6.0,
          shrink: float = 0.0, studs: bool = True) -> float:
    """A blocky hill: ``levels`` elliptical tiers, each ``rise`` high,
    narrowing evenly to a top a fraction ``shrink`` of the base (0: about a
    quarter).  Returns the height of its top."""
    footprints = []
    top_frac = shrink or 0.25
    for k in range(levels):
        f = 1.0 - (1.0 - top_frac) * k / max(1, levels - 1)
        footprints.append(ellipse_rects(cx, cz, rx * f, rz * f, band))
    return tier_stack(b, footprints, y0, [rise], colours, studs=studs)


def ridge(b, x0: float, x1: float, z0: float, z1: float, levels: int, rise: float,
          colours: Sequence[str], inset: float = 4.0, y0: float = 0.0,
          inset_x: Optional[float] = None, studs: bool = True) -> float:
    """A rectangular stepped berm: each tier ``inset`` in from the one
    below on the long sides (``inset_x`` on the ends)."""
    ix = inset if inset_x is None else inset_x
    footprints = []
    for k in range(levels):
        r = (x0 + ix * k, x1 - ix * k, z0 + inset * k, z1 - inset * k)
        if r[1] - r[0] < 2 or r[3] - r[2] < 2:
            break
        footprints.append([r])
    return tier_stack(b, footprints, y0, [rise], colours, studs=studs)


def channel(b, area: Rect, depth: float, floor: str, wall_c: str = "",
            studs: bool = True, material: str = "",
            openings: Optional[Dict[str, Sequence[Tuple[float, float]]]] = None) -> None:
    """A dug channel (a ditch, a cutting, a dry wash): its floor ``depth``
    below the ground.  The ground plate must have been laid with ``area``
    among its holes; the turf and the soil under it are the channel's sides
    down to y = -6, and ``wall_c`` lines them below that -- except where
    ``openings`` ({"z+": [(x0, x1)], "x-": [(z0, z1)]...}) leave a side open
    for a stair that comes down into the channel there."""
    x0, x1, z0, z1 = area
    slab(b, area, -depth, 3.0, floor, studs=studs,
         **({"material": material} if material else {}))
    if depth > 6.0 and wall_c:
        t = 0.8
        gaps = openings or {}

        def holes(side):
            return [(a, c, -depth - 1.0, -5.0) for a, c in gaps.get(side, ())]
        holed_wall(b, "x", z0 - t / 2.0, t, x0 - t, x1 + t, -depth, -6.0, wall_c,
                   holes=holes("z-"))
        holed_wall(b, "x", z1 + t / 2.0, t, x0 - t, x1 + t, -depth, -6.0, wall_c,
                   holes=holes("z+"))
        holed_wall(b, "z", x0 - t / 2.0, t, z0, z1, -depth, -6.0, wall_c, holes=holes("x-"))
        holed_wall(b, "z", x1 + t / 2.0, t, z0, z1, -depth, -6.0, wall_c, holes=holes("x+"))


def steps_down(b, axis: str, near: float, far: float, lo: float, hi: float,
               depth: float, colour: str) -> None:
    """Stairs from the ground (at ``near``) down a channel to its floor."""
    flight(b, axis, near, far, lo, hi, 0.0, -depth, colour, fill=-depth - 2.0)


# ============================================================== the CTF bits
def pedestal(b, x: float, z: float, y: float, colour: str, neon: str,
             base: str = CONCRETE_DARK, wide: float = 24.0, top_w: float = 15.0) -> float:
    """The flag's pedestal on a floor at ``y``: two walkable steps and a
    lit ring.  Returns the top (where :meth:`RelayArea.flag` goes)."""
    b.box([x, y + 1.0, z], [wide, 2.0, wide], base, studs=True)
    b.box([x, y + 3.0, z], [top_w, 2.0, top_w], colour, studs=True)
    b.cyl([x, y + 4.15, z], [top_w * 0.75, 0.3, top_w * 0.75], neon, material="neon",
          collide=False)
    return y + 4.0


def banner_mast(b, x: float, z: float, y: float, height: float, team: str,
                facing: str, mast: str = STEEL_DARK) -> None:
    """A mast with the team's banner hoisted on it -- the landmark a flag
    run is steered by.  The banner hangs flat against the mast's side, its
    face out along ``facing``."""
    b.cyl([x, y + height / 2.0, z], [1.4, height, 1.4], mast, material="metal")
    off = {"x+": (1.05, 0.0), "x-": (-1.05, 0.0), "z+": (0.0, 1.05), "z-": (0.0, -1.05)}[facing]
    face_sign(b, x + off[0], y + height - 8.0, z + off[1], 10.0, 12.0, "banner_%s" % team,
              facing, TEAM_COLOUR[team])
    b.sphere([x, y + height + 1.2, z], [2.8, 2.8, 2.8], TEAM_NEON[team], material="neon",
             collide=False)


def outpost_room(h: Half, x0: float, x1: float, z0: float, z1: float, y: float,
                 wall_c: str, roof_c: str, height: float = 12.0, door_w: float = 14.0,
                 pads: int = 2, yaw: Optional[float] = None, t: float = 3.0,
                 doors: Sequence[str] = ("in", "out"), lights: str = STAIR_LIGHT,
                 roof: bool = True) -> None:
    """A small strongpoint on ``h``'s half with lockdown pads inside: a
    room with a door towards the middle and one towards the base, roofed.
    x0 < x1 are magnitudes from the centre line."""
    b = h.b
    area = h.r(x0, x1, z0, z1)
    zc = (z0 + z1) / 2.0
    door = (zc - door_w / 2.0, zc + door_w / 2.0, y + 9.0)
    sides = {}
    if "in" in doors:
        sides[h.inward] = [door]
    if "out" in doors:
        sides[h.outward] = [door]
    room_walls(b, area, t, y, y + height, wall_c, doors=sides)
    if roof:
        slab(b, area, y + height + 1.2, 1.2, roof_c, studs=True)
        strip_light(b, (area[0] + area[1]) / 2.0, zc, y + height,
                    max(4.0, abs(x1 - x0) - 10.0), "x", lights)
    if yaw is None:
        yaw = h.yaw_in
    inner = abs(x1 - x0) - 2 * t
    depth = abs(z1 - z0) - 2 * t
    for i in range(pads):
        px = min(x0, x1) + t + inner * (i + 0.5) / pads
        pz = zc + (depth * 0.25 if i % 2 else -depth * 0.25)
        b.outpost(h.team, h.x(px), y, pz, yaw)


def muster_room(h: Half, x0: float, x1: float, z0: float, z1: float, y: float,
                wall_c: str, roof_c: str, height: float = 14.0, door_w: float = 14.0,
                rows: int = 2, cols: int = 3, back_door: bool = True,
                t: float = 3.0, lights: str = LAMP, roof: bool = True) -> None:
    """A deploy hall on ``h``'s face of the relay: pads in rows facing out
    of the door onto the team's own half, a back door into the relay.
    x0 < x1 are magnitudes (x0 the relay side)."""
    b = h.b
    area = h.r(x0, x1, z0, z1)
    zc = (z0 + z1) / 2.0
    out_door = [(zc - door_w / 2.0, zc + door_w / 2.0, y + 10.0)]
    sides = {h.outward: out_door}
    if back_door:
        sides[h.inward] = [(zc - 6.0, zc + 6.0, y + 9.0)]
    room_walls(b, area, t, y, y + height, wall_c, doors=sides)
    if roof:
        slab(b, area, y + height + 1.4, 1.4, roof_c, studs=True)
        strip_light(b, (area[0] + area[1]) / 2.0, zc, y + height, abs(x1 - x0) - 10.0, "x", lights)
    inner_w = abs(x1 - x0) - 2 * t
    inner_d = abs(z1 - z0) - 2 * t
    for i in range(cols):
        for j in range(rows):
            px = x0 + t + inner_w * (i + 0.5) / cols
            pz = min(z0, z1) + t + inner_d * (j + 0.5) / rows
            b.muster(h.team, h.x(px), y, pz, h.yaw_out)
    # the team's colours over the way out, on the inside of the outer wall
    h.sign(x1 - t - 0.36, y + height - 2.6, zc, 12.0, 3.4, "sign_%s" % h.team, "x+")


# ===================================================================== props
def lamp_post(b, x: float, z: float, y: float = 0.0, h: float = 12.0,
              colour: str = LAMP, pole: str = STEEL_DARK) -> None:
    b.cyl([x, y + h / 2.0, z], [1.0, h, 1.0], pole, material="metal")
    b.box([x, y + h + 0.6, z], [2.6, 1.2, 2.6], pole, collide=False, material="metal")
    b.box([x, y + h - 0.2, z], [2.0, 0.4, 2.0], colour, material="neon", collide=False)


def pine(b, x: float, z: float, y: float = 0.0, s: float = 1.0, trunk: str = WOOD_DARK,
         leaf: str = "#2a5f3c", snow: str = "") -> None:
    b.cyl([x, y + 3.0 * s, z], [1.8 * s, 6.0 * s, 1.8 * s], trunk)
    for i in range(3):
        b.cone([x, y + 7.0 * s + i * 3.6 * s, z], [(10.0 - i * 2.4) * s, 6.0 * s,
                                                   (10.0 - i * 2.4) * s],
               leaf, collide=False)
    if snow:
        b.cone([x, y + 7.0 * s + 2 * 3.6 * s + 1.6 * s, z], [3.2 * s, 2.6 * s, 3.2 * s],
               snow, collide=False)


def tree(b, x: float, z: float, y: float = 0.0, s: float = 1.0, trunk: str = WOOD,
         leaf: str = "#2f6b42") -> None:
    h = 9.0 * s
    b.cyl([x, y + h / 2.0, z], [2.0 * s, h, 2.0 * s], trunk)
    b.sphere([x, y + h + 3.0 * s, z], [9.0 * s, 8.0 * s, 9.0 * s], leaf, collide=False)
    b.sphere([x + 2.4 * s, y + h + 0.6 * s, z - 1.6 * s], [6.0 * s, 5.4 * s, 6.0 * s], leaf,
             collide=False)


def boulder(b, x: float, z: float, y: float = 0.0, s: float = 1.0,
            colour: str = "#8f9296") -> None:
    b.sphere([x, y + 1.6 * s, z], [5.0 * s, 3.4 * s, 4.4 * s], colour)


def crate_pile(b, x: float, z: float, y: float, rng: random.Random, colours: Sequence[str],
               n: int = 3, size: float = 5.0, sx: int = 1) -> None:
    """A few crates stacked by a fixed recipe.  ``rng`` is seeded per pile
    and the same seed is used for its mirror twin, with ``sx`` the side it
    is on (offsets along x are flipped with it), so the cover matches."""
    for i in range(n):
        s = size * rng.uniform(0.8, 1.15)
        dx, dz = rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5)
        if i == n - 1 and n > 2:
            b.box([x + sx * dx * 0.3, y + size * 1.4 + s * 0.4, z + dz * 0.3],
                  [s * 0.8, s * 0.8, s * 0.8], rng.choice(colours), studs=True)
        else:
            b.box([x + sx * (dx + i * size * 1.05), y + s / 2.0, z + dz], [s, s, s],
                  rng.choice(colours), studs=True)


def sedan(b, x: float, z: float, along: str = "x", colour: str = "#8a2a24", y: float = 0.0,
          flip: int = 1, length: float = 11.0, wrecked: bool = False) -> None:
    """A car, axis-aligned so all of it collides; ``flip`` = -1 points its
    nose the other way (a mirrored map's twin of a car along x)."""
    w = 5.0
    body = "#2b2b2b" if wrecked else colour
    cab = "#1d2226" if wrecked else "#2b3a44"

    def box(cx, cy, cz, sx_, sy, sz, c, **kw):
        cx *= flip
        if along == "x":
            b.box([x + cx, y + cy, z + cz], [sx_, sy, sz], c, **kw)
        else:
            b.box([x + cz, y + cy, z + cx], [sz, sy, sx_], c, **kw)

    box(0, 1.85, 0, length, 2.5, w, body, material="metal")
    box(-0.6, 3.85, 0, length * 0.5, 1.5, w - 0.6, cab, material="metal")
    box(-0.6, 4.75, 0, length * 0.5 - 0.6, 0.3, w - 1.2, body, material="metal")
    for side in (-1, 1):
        for end in (-1, 1):
            if along == "x":
                b.cyl([x + end * length * 0.32, y + 1.1, z + side * (w / 2.0 - 0.2)],
                      [2.2, 0.9, 2.2], "#1b1d20", r=[math.pi / 2.0, 0, 0], collide=False)
            else:
                b.cyl([x + side * (w / 2.0 - 0.2), y + 1.1, z + end * length * 0.32],
                      [2.2, 0.9, 2.2], "#1b1d20", r=[0, 0, math.pi / 2.0], collide=False)
    if not wrecked:
        for side in (-1, 1):
            box(length / 2.0 + 0.04, 2.3, side * 1.6, 0.08, 0.6, 1.0, "#fff3c4",
                material="neon", collide=False)
            box(-length / 2.0 - 0.04, 2.3, side * 1.6, 0.08, 0.5, 1.0, "#c42b20",
                material="neon", collide=False)


def board_letters(b, x: float, y: float, z: float, text: str, h: float, background: str,
                  colour: str, facing: str = "z+", depth: float = 0.3, solid: bool = True) -> None:
    """A name in channel letters, one board per letter (as ``letters``),
    optionally not solid -- for a name that differs between the halves of
    a mirrored map, out of reach, where a solid board would be lopsided."""
    pitch = h * 0.86
    width = pitch - h * 0.08
    run = {"z+": (1.0, 0.0), "z-": (-1.0, 0.0), "x+": (0.0, -1.0), "x-": (0.0, 1.0)}[facing]
    out = {"z+": (0.0, 1.0), "z-": (0.0, -1.0), "x+": (1.0, 0.0), "x-": (-1.0, 0.0)}[facing]
    turn = {"z+": 0.0, "z-": math.pi, "x+": math.pi / 2.0, "x-": -math.pi / 2.0}[facing]
    advances = [pitch * (0.55 if ch == " " else 1.0) for ch in text]
    along = -sum(advances) / 2.0
    for ch, step in zip(text, advances):
        if ch != " ":
            centre = along + step / 2.0
            b.box([x + run[0] * centre + out[0] * depth / 2.0, y,
                   z + run[1] * centre + out[1] * depth / 2.0], [width, h, depth], background,
                  r=[0.0, turn, 0.0], decal=sign_decal(ch, background, colour, width / h),
                  collide=solid)
        along += step


def rails(b, area: Rect, y: float, h: float = 3.2, c: str = STEEL, t: float = 0.8,
          sides: Sequence[str] = ("x-", "x+", "z-", "z+"),
          gaps: Optional[Dict[str, Sequence[Tuple[float, float]]]] = None) -> None:
    """A solid railing round a deck: it is cover, and it stops a walk off
    the edge.  ``gaps`` leaves openings ((start, end) along a side)."""
    doors = {side: [(a, c_, y + h) for a, c_ in spans] for side, spans in (gaps or {}).items()}
    room_walls(b, area, t, y, y + h, c, doors=doors, sides=sides, material="metal")


def water_sheet(b, area: Rect, y: float, colour: str = "#2f6f8f", alpha: float = 0.72) -> None:
    """Water you can see through and walk on the bed of (it does not stop you)."""
    x0, x1, z0, z1 = area
    b.box([(x0 + x1) / 2.0, y - 0.2, (z0 + z1) / 2.0], [x1 - x0, 0.4, z1 - z0], colour,
          collide=False, material="glass", alpha=alpha)
