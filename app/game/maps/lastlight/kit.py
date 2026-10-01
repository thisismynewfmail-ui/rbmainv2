"""The building kit every Last Light area is made from.

Last Light is one map holding several separate places -- a round is played
in one of them, and the next round in another -- so every area is drawn in
its own local coordinates (centre at the origin, ground at y = 0) by an
:class:`Area`, which shifts each part into the area's slot on the big map as
it is added.  The parts an area adds are one contiguous run of the map's
part list, which is how the game host can send a client only the area it is
standing in.

The rules this kit enforces so that ``tools/mapcheck.py`` stays clean:

* **One ground plane.**  The ground's top is y = 0.  Every surface laid on it
  -- roads, pavements, lawns, car parks -- goes through :class:`Surfaces`,
  which carves each new rectangle around everything already laid.  Two
  covers therefore never overlap, so two faces can never share a plane.
* **Solids abut.**  Walls meet at the corners the way ``room_walls`` does it
  (the two walls facing along x run the full depth, the other two fit
  between them), roofs sit *on* walls rather than around them, and trim
  stands proud of the face it is fixed to.
* **Anything a body can reach is solid.**  A prop below head height that
  looks like it is in the way is collidable; the only see-through-and-walk-
  through parts are leaves, light, paint and things overhead.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..builder import MapBuilder
from ..ironvale import (  # noqa: F401  (re-exported for the area modules)
    carve, crenels, deploy_pad, face_sign, flight, floodlight, hazard_rim,
    kerb, plate, rect, room_walls, slab, step_paint, strip_light, wall)

Rect = Tuple[float, float, float, float]

FLOOR = 0.4          # an interior floor pad: well inside a step
STOREY = 14.0        # ground floor to the underside of the floor above
WALL_T = 2.0
KILL_Y = -80.0

# ----------------------------------------------------------------- palette
ASPHALT = "#3d4248"
ASPHALT_DARK = "#33373c"
LINE_WHITE = "#d9dcd6"
LINE_YELLOW = "#d8b23a"
PAVEMENT = "#9b9a92"
PAVEMENT_DARK = "#86857e"
CONCRETE = "#9aa0a6"
CONCRETE_DARK = "#787f86"
CONCRETE_LIGHT = "#b6bcc1"
BRICK = "#9a4f3a"
BRICK_DARK = "#7c3d2d"
STEEL = "#6f767d"
STEEL_DARK = "#4a5057"
RUST = "#8a5a3a"
WOOD = "#7a5335"
WOOD_DARK = "#543923"
WOOD_LIGHT = "#a07a52"
GLASS = "#8fb8c8"
LAMP = "#ffe2a8"
WARM = "#ffcf7a"
COLD = "#9fe8ff"
BLOOD = "#6a1410"
SANDBAG = "#a8956a"
HAZARD = "#f2b01e"


def sign_decal(text: str, background: str = "#f2f3f3",
               colour: str = "#1b2a35", aspect: float = 1.0) -> str:
    """A text decal, painted by the client the first time it is needed.

    The atlas cell is square and is stretched over the sign's face, so the
    lettering is drawn squeezed by the face's own aspect and comes out the
    right shape once it is on the sign.  ``~`` separates the fields and so
    may not appear in the text.
    """
    text = text.replace("~", "-")
    return "t~%s~%s~%s~%.2f" % (text, background, colour, max(0.25, aspect))


# ==================================================================== areas
class Area(MapBuilder):
    """One playable place, drawn at the origin and placed at (ox, oz).

    It shares its parts list with the root builder, so everything it adds
    lands in the map in order; ``start``/``end`` bracket its run.
    """

    def __init__(self, root: MapBuilder, area_id: str, name: str,
                 ox: float, oz: float, half: float, sky: Dict[str, Any],
                 ambient: str, ground: str, fog: float = 760.0):
        super().__init__(name, sky=sky, ambient=ambient, fog=fog, ground=ground)
        self.root = root
        self.parts = root.parts
        self.id = area_id
        self.ox, self.oz = float(ox), float(oz)
        self.half = float(half)
        self.start = len(root.parts)
        self.end = self.start
        self.safe: List[Dict[str, Any]] = []
        self.zspawns: List[Dict[str, Any]] = []
        self.points: Dict[str, List[Dict[str, Any]]] = {}
        self.lure: Optional[Dict[str, Any]] = None
        self.landmarks: List[Dict[str, Any]] = []
        self.margin = 16.0

    # ------------------------------------------------------------ placing
    def add(self, t, p, s, c, **kw):           # type: ignore[override]
        return super().add(t, [p[0] + self.ox, p[1], p[2] + self.oz], s, c, **kw)

    def at(self, x: float, y: float, z: float) -> List[float]:
        return [round(x + self.ox, 2), round(y, 2), round(z + self.oz, 2)]

    def safe_spawn(self, x: float, y: float, z: float, yaw: float = 0.0) -> None:
        self.safe.append({"p": self.at(x, y, z), "yaw": round(yaw, 3)})

    def zombie_spawn(self, x: float, z: float, tag: str = "",
                     y: Optional[float] = None) -> None:
        """A place the infected come from.  Its height is read off whatever
        stands under it once the area is finished, so a spawn on a road, a
        pavement or a platform is on it rather than inside it."""
        entry: Dict[str, Any] = {"local": [x, z], "y": y}
        if tag:
            entry["tag"] = tag
        self.zspawns.append(entry)

    def _solids(self) -> List[Tuple[List[float], List[float]]]:
        out = []
        for part in self.parts[self.start:]:
            if not part.get("col") or ("r" in part and any(
                    abs(v) > 1e-3 for v in part["r"])):
                continue
            px, py, pz = part["p"]
            sx, sy, sz = part["s"]
            if part.get("t") == "cyl":
                sx, sz = sx * 0.86, sz * 0.86
            elif part.get("t") == "sph":
                sx, sy, sz = sx * 0.78, sy * 0.78, sz * 0.78
            out.append(([px - sx / 2 - self.ox, py - sy / 2, pz - sz / 2 - self.oz],
                        [px + sx / 2 - self.ox, py + sy / 2, pz + sz / 2 - self.oz]))
        return out

    def _clear_spot(self, boxes, x: float, z: float, y: Optional[float]):
        """(x, z) if a body standing there has room round it, else the nearest
        spot that does -- so a spawn never ends up inside a gravestone."""
        def free(px: float, pz: float) -> bool:
            top = y if y is not None else self.surface(px, pz, 6.0)
            hw, hd = 1.6 + 1.3, 1.0 + 1.3
            for lo, hi in boxes:
                if hi[0] > px - hw and lo[0] < px + hw and hi[2] > pz - hd and \
                        lo[2] < pz + hd and hi[1] > top + 0.05 and lo[1] < top + 5.4:
                    return False
            return True
        if free(x, z):
            return x, z
        for radius in (3.0, 5.0, 7.0, 9.0, 12.0, 15.0):
            for k in range(16):
                a = math.pi * 2.0 * k / 16.0
                nx, nz = x + math.cos(a) * radius, z + math.sin(a) * radius
                if abs(nx) < self.half - 3.0 and abs(nz) < self.half - 3.0 and free(nx, nz):
                    return round(nx, 2), round(nz, 2)
        return x, z

    def surface(self, x: float, z: float, below: float = 40.0) -> float:
        """The highest solid top under (x, z), at or below ``below``."""
        wx, wz = x + self.ox, z + self.oz
        best = 0.0
        for part in self.parts[self.start:]:
            if not part.get("col") or "r" in part:
                continue
            px, py, pz = part["p"]
            sx, sy, sz = part["s"]
            if part.get("t") == "cyl":
                sx, sz = sx * 0.86, sz * 0.86
            if abs(wx - px) > sx / 2.0 or abs(wz - pz) > sz / 2.0:
                continue
            top = py + sy / 2.0
            if top <= below and top > best:
                best = top
        return best

    def mark(self, kind: str, x: float, y: float, z: float, **extra: Any) -> None:
        entry: Dict[str, Any] = {"p": self.at(x, y, z)}
        entry.update(extra)
        self.points.setdefault(kind, []).append(entry)

    def set_lure(self, x: float, y: float, z: float, name: str, verb: str,
                 sound: str, focus: Sequence[float]) -> None:
        """The area's noise-maker: where you stand to use it, and where the
        horde is drawn to while it sounds."""
        self.lure = {"p": self.at(x, y, z), "name": name, "verb": verb,
                     "sound": sound, "focus": self.at(*focus)}

    def landmark(self, x: float, z: float, name: str) -> None:
        """A named place, for callouts in chat and the spectator's caption."""
        self.landmarks.append({"p": self.at(x, 0.0, z), "name": name})

    # ------------------------------------------------------------- finish
    def rect_world(self) -> List[float]:
        h = self.half + self.margin
        return [self.ox - h, self.ox + h, self.oz - h, self.oz + h]

    def finish(self) -> Dict[str, Any]:
        self.end = len(self.parts)
        settled = []
        boxes = self._solids()
        for entry in self.zspawns:
            if "local" not in entry:
                settled.append(entry)
                continue
            x, z = entry["local"]
            x, z = self._clear_spot(boxes, x, z, entry["y"])
            y = entry["y"] if entry["y"] is not None else self.surface(x, z, 6.0)
            out: Dict[str, Any] = {"p": self.at(x, y, z)}
            if entry.get("tag"):
                out["tag"] = entry["tag"]
            settled.append(out)
        self.zspawns = settled
        return {
            "id": self.id, "name": self.name, "sky": self.sky,
            "ambient": self.ambient, "fog": self.fog, "ground": self.ground,
            "rect": self.rect_world(), "centre": [self.ox, 0.0, self.oz],
            "parts": [self.start, self.end], "safe": self.safe,
            "zspawn": self.zspawns, "points": self.points, "lure": self.lure,
            "landmarks": self.landmarks,
        }


# ================================================================ surfaces
class Surfaces:
    """Ground covers that never overlap.

    Each rectangle is carved around every rectangle laid before it, so the
    first thing laid in a spot wins and later ones fit round it.  Covers are
    boxes from the ground up to their own top, so two of different heights
    meet back to back and two of the same height meet edge to edge -- in
    neither case is there a pair of faces on one plane pointing one way.
    """

    def __init__(self, b: MapBuilder):
        self.b = b
        self.laid: List[Rect] = []

    def lay(self, area: Rect, top: float, colour: str, collide: bool = True,
            studs: bool = False, material: str = "") -> None:
        pieces = carve(area, self.laid)
        self.laid.append(area)
        for x0, x1, z0, z1 in pieces:
            if x1 - x0 < 1e-3 or z1 - z0 < 1e-3:
                continue
            self.b.box([(x0 + x1) / 2.0, top / 2.0, (z0 + z1) / 2.0],
                       [x1 - x0, top, z1 - z0], colour, collide=collide,
                       studs=studs, material=material)

    def reserve(self, area: Rect) -> None:
        """Keep covers off a rectangle (a building's footprint, say)."""
        self.laid.append(area)


def ground(b: Area, colour: str, soil: str = "#5a4a38",
           material: str = "grass") -> None:
    """The area's ground: turf over soil, out to under the boundary."""
    h = b.half + b.margin
    slab(b, rect(-h, h, -h, h), 0.0, 0.6, colour, studs=True, material=material)
    slab(b, rect(-h, h, -h, h), -0.6, 5.4, soil)


# =================================================================== walls
def holed_wall(b: MapBuilder, axis: str, at: float, thickness: float,
               lo: float, hi: float, y0: float, y1: float, colour: str,
               holes: Sequence[Tuple[float, float, float, float]] = (),
               glass: bool = False, boards: bool = False, **kw) -> None:
    """A straight wall with rectangular openings.

    ``axis`` is the axis the wall runs along ("z": it stands at x = ``at``).
    Each hole is ``(start, end, bottom, top)``; a bottom at or below ``y0``
    makes it a doorway.  Windows can be glazed (a collidable pane in the
    middle of the wall) or boarded (solid planks across, inside the wall's
    own thickness, with gaps between them you can shoot through but not
    climb through).
    """
    def piece(a: float, c: float, ya: float, yb: float, col: str = colour,
              t: float = thickness, **extra) -> None:
        if c - a < 1e-6 or yb - ya < 1e-6:
            return
        options = dict(kw)
        options.update(extra)
        if axis == "z":
            b.box([at, (ya + yb) / 2.0, (a + c) / 2.0], [t, yb - ya, c - a],
                  col, **options)
        else:
            b.box([(a + c) / 2.0, (ya + yb) / 2.0, at], [c - a, yb - ya, t],
                  col, **options)

    cursor = lo
    for a, c, bottom, top in sorted(holes):
        a, c = max(lo, min(hi, a)), max(lo, min(hi, c))
        if c - a < 1e-6:
            continue
        piece(cursor, a, y0, y1)
        piece(a, c, y0, max(y0, bottom))
        piece(a, c, min(y1, top), y1)
        if bottom > y0 + 1e-6 and top > bottom:
            if glass:
                piece(a, c, bottom, min(y1, top), GLASS, thickness * 0.3,
                      material="glass", alpha=0.42)
            elif boards:
                span = min(y1, top) - bottom
                for k in range(3):
                    y = bottom + span * (0.2 + 0.3 * k)
                    piece(a, c, y, y + min(0.9, span * 0.16), WOOD_LIGHT,
                          thickness * 0.5)
        cursor = max(cursor, c)
    piece(cursor, hi, y0, y1)


def building(b: MapBuilder, area: Rect, y0: float, height: float, colour: str,
             *, t: float = WALL_T, roof_colour: str = CONCRETE_DARK,
             roof_t: float = 1.2, eave: float = 0.0, floor_colour: str = "",
             doors: Optional[Dict[str, Sequence[Tuple[float, float, float]]]] = None,
             windows: Optional[Dict[str, Sequence[Tuple[float, float, float, float]]]] = None,
             glass: bool = False, boards: bool = False, roof: bool = True,
             roof_holes: Sequence[Rect] = (), parapet: float = 0.0,
             parapet_gaps: Optional[Dict[str, Sequence[Tuple[float, float]]]] = None,
             lights: str = LAMP, studs_roof: bool = True,
             no_lights: Sequence[Rect] = ()) -> None:
    """A hollow building: floor pad, four walls with openings, a roof.

    ``doors`` maps a side ("x-", "x+", "z-", "z+") to ``(start, end, head)``
    openings measured along that wall; ``windows`` to ``(start, end, sill,
    lintel)``.  Heights are absolute.  The roof's underside is the interior
    ceiling, and strip lights are fixed into it.
    """
    x0, x1, z0, z1 = area
    y1 = y0 + height
    doors = doors or {}
    windows = windows or {}

    def holes(side: str):
        out = [(a, c, y0 - 1.0, head) for a, c, head in doors.get(side, ())]
        out += [(a, c, sill, top) for a, c, sill, top in windows.get(side, ())]
        return out

    if floor_colour:
        slab(b, rect(x0 + t, x1 - t, z0 + t, z1 - t), y0 + FLOOR, FLOOR,
             floor_colour)
    holed_wall(b, "z", x0 + t / 2.0, t, z0, z1, y0, y1, colour, holes("x-"),
               glass=glass, boards=boards)
    holed_wall(b, "z", x1 - t / 2.0, t, z0, z1, y0, y1, colour, holes("x+"),
               glass=glass, boards=boards)
    holed_wall(b, "x", z0 + t / 2.0, t, x0 + t, x1 - t, y0, y1, colour,
               holes("z-"), glass=glass, boards=boards)
    holed_wall(b, "x", z1 - t / 2.0, t, x0 + t, x1 - t, y0, y1, colour,
               holes("z+"), glass=glass, boards=boards)
    if not roof:
        return
    outer = rect(x0 - eave, x1 + eave, z0 - eave, z1 + eave)
    plate(b, carve(outer, list(roof_holes)), y1 + roof_t, roof_t, roof_colour,
          studs=studs_roof)
    if parapet > 0:
        gaps = parapet_gaps or {}
        room_walls(b, outer, 1.2, y1 + roof_t, y1 + roof_t + parapet, colour,
                   doors={side: [(a, c, y1 + roof_t + parapet)
                                 for a, c in spans]
                          for side, spans in gaps.items()})
    if lights:
        inner_w = x1 - x0 - 2 * t
        inner_d = z1 - z0 - 2 * t
        holes_list = list(roof_holes) + list(no_lights)

        def clear(cx: float, cz: float, length: float, along_x: bool) -> bool:
            hx = length / 2.0 if along_x else 1.0
            hz = 1.0 if along_x else length / 2.0
            return not any(h[0] - 1.0 < cx + hx and h[1] + 1.0 > cx - hx and
                           h[2] - 1.0 < cz + hz and h[3] + 1.0 > cz - hz
                           for h in holes_list)

        if inner_w >= inner_d:
            rows = max(1, int(inner_d // 14))
            for k in range(rows):
                cz = z0 + t + inner_d * (k + 0.5) / rows
                length = max(4.0, inner_w - 8.0)
                if clear((x0 + x1) / 2.0, cz, length, True):
                    strip_light(b, (x0 + x1) / 2.0, cz, y1, length, "x", lights)
        else:
            rows = max(1, int(inner_w // 14))
            for k in range(rows):
                cx = x0 + t + inner_w * (k + 0.5) / rows
                length = max(4.0, inner_d - 8.0)
                if clear(cx, (z0 + z1) / 2.0, length, False):
                    strip_light(b, cx, (z0 + z1) / 2.0, y1, length, "z", lights)


def gable(b: MapBuilder, area: Rect, y: float, colour: str, along: str = "x",
          tiers: int = 4, rise: float = 1.4, overhang: float = 1.0) -> None:
    """A stepped pitched roof: tiers of slabs, each narrower than the last.

    Stepped rather than sloped, because a slope is a rotated part and a
    rotated part has no collision -- and a roof you fall through is worse
    than a roof that is a little blocky.  It sits on top of a flat roof slab
    whose top is ``y``.
    """
    x0, x1, z0, z1 = area
    x0, x1, z0, z1 = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang
    for i in range(tiers):
        if along == "x":
            inset = (z1 - z0) / 2.0 * (i + 1) / (tiers + 0.6)
            r = (x0, x1, z0 + inset, z1 - inset)
        else:
            inset = (x1 - x0) / 2.0 * (i + 1) / (tiers + 0.6)
            r = (x0 + inset, x1 - inset, z0, z1)
        slab(b, r, y + rise * (i + 1), rise, colour)


def wall_sign(b: MapBuilder, x: float, y: float, z: float, w: float, h: float,
              decal: str, facing: str, colour: str = "#f2f3f3") -> None:
    """A sign fixed flat to a wall, facing out along ``facing``.  Solid,
    because anything a player can end up level with should be."""
    turn = {"z+": 0.0, "z-": math.pi, "x+": math.pi / 2.0,
            "x-": -math.pi / 2.0}[facing]
    b.box([x, y, z], [w, h, 0.7], colour, r=[0, turn, 0], decal=decal)


def flood(b: MapBuilder, x: float, z: float, y: float = 0.0,
          height: float = 24.0, colour: str = LAMP) -> None:
    """A floodlight mast with a solid head (the head is somewhere you can
    end up standing beside, on a roof)."""
    b.cyl([x, y + height / 2.0, z], [2.2, height, 2.2], STEEL_DARK,
          material="metal")
    b.box([x, y + height + 1.4, z], [7.0, 2.8, 5.0], STEEL, material="metal")
    b.box([x, y + height - 0.05, z], [5.6, 0.1, 3.8], colour, material="neon",
          collide=False)


# ================================================================== props
def crate(b: MapBuilder, x: float, y: float, z: float, size: float = 5.0,
          colour: str = WOOD, studs: bool = True) -> None:
    b.box([x, y + size / 2.0, z], [size, size, size], colour, studs=studs)


def dumpster(b: MapBuilder, x: float, z: float, along: str = "x",
             colour: str = "#2f5f3a") -> None:
    w, d = (9.0, 5.0) if along == "x" else (5.0, 9.0)
    b.box([x, 2.6, z], [w, 5.2, d], colour, material="metal")
    b.box([x, 5.45, z], [w + 0.4, 0.5, d + 0.4], STEEL_DARK, material="metal")


def barrier(b: MapBuilder, x: float, z: float, length: float, along: str = "x",
            colour: str = CONCRETE_LIGHT, stripes: bool = True) -> None:
    """A concrete jersey barrier: waist-high cover, vaultable."""
    if along == "x":
        b.box([x, 1.4, z], [length, 2.8, 2.6], colour)
        b.box([x, 3.4, z], [length, 1.2, 1.4], colour)
    else:
        b.box([x, 1.4, z], [2.6, 2.8, length], colour)
        b.box([x, 3.4, z], [1.4, 1.2, length], colour)


def sandbags(b: MapBuilder, x: float, z: float, length: float,
             along: str = "x", height: float = 4.0, y: float = 0.0) -> None:
    w, d = (length, 3.0) if along == "x" else (3.0, length)
    b.box([x, y + height / 2.0, z], [w, height, d], SANDBAG, studs=True)
    tw, td = (length - 1.0, 2.0) if along == "x" else (2.0, length - 1.0)
    b.box([x, y + height + 0.5, z], [tw, 1.0, td], "#968457", studs=True)


def bench(b: MapBuilder, x: float, z: float, along: str = "x",
          colour: str = WOOD_LIGHT, y: float = 0.0) -> None:
    w, d = (7.0, 2.4) if along == "x" else (2.4, 7.0)
    b.box([x, y + 1.2, z], [w, 0.5, d], colour, studs=True)
    for k in (-1, 1):
        if along == "x":
            b.box([x + k * 2.8, y + 0.475, z], [0.6, 0.95, d - 0.4], STEEL_DARK)
        else:
            b.box([x, y + 0.475, z + k * 2.8], [w - 0.4, 0.95, 0.6], STEEL_DARK)


def car(b: MapBuilder, x: float, z: float, along: str = "x",
        colour: str = "#8a2a24", length: float = 11.0, wrecked: bool = False,
        y: float = 0.0) -> None:
    """A car, axis-aligned so all of it collides.  ``wrecked`` burns it out."""
    w = 5.0
    body = "#2b2b2b" if wrecked else colour
    cab = "#1d2226" if wrecked else "#2b3a44"

    def box(cx, cy, cz, sx, sy, sz, c, **kw):
        if along == "x":
            b.box([x + cx, y + cy, z + cz], [sx, sy, sz], c, **kw)
        else:
            b.box([x + cz, y + cy, z + cx], [sz, sy, sx], c, **kw)

    box(0, 1.85, 0, length, 2.5, w, body, material="metal")
    box(-0.6, 3.85, 0, length * 0.5, 1.5, w - 0.6, cab, material="metal")
    box(-0.6, 4.75, 0, length * 0.5 - 0.6, 0.3, w - 1.2, body, material="metal")
    for side in (-1, 1):
        for end in (-1, 1):
            if along == "x":
                b.cyl([x + end * length * 0.32, y + 1.1, z + side * (w / 2.0 - 0.2)],
                      [2.2, 0.9, 2.2], "#1b1d20", r=[math.pi / 2.0, 0, 0],
                      collide=False)
            else:
                b.cyl([x + side * (w / 2.0 - 0.2), y + 1.1, z + end * length * 0.32],
                      [2.2, 0.9, 2.2], "#1b1d20", r=[0, 0, math.pi / 2.0],
                      collide=False)
    if not wrecked:
        for side in (-1, 1):
            box(length / 2.0 + 0.04, 2.3, side * 1.6, 0.08, 0.6, 1.0, "#fff3c4",
                material="neon", collide=False)
            box(-length / 2.0 - 0.04, 2.3, side * 1.6, 0.08, 0.5, 1.0, "#c42b20",
                material="neon", collide=False)


def bus(b: MapBuilder, x: float, z: float, along: str = "x",
        colour: str = "#e0a62a", length: float = 34.0, label: str = "") -> None:
    """A school bus: a long climbable box, windows down both sides."""
    w = 7.6

    def box(cx, cy, cz, sx, sy, sz, c, **kw):
        if along == "x":
            b.box([x + cx, cy, z + cz], [sx, sy, sz], c, **kw)
        else:
            b.box([x + cz, cy, z + cx], [sz, sy, sx], c, **kw)

    box(0, 1.1, 0, length - 2.0, 1.4, w - 1.0, "#22262b")
    box(0, 5.4, 0, length, 7.2, w, colour, studs=True)
    for side in (-1, 1):
        box(1.0, 6.4, side * (w / 2.0 + 0.06), length - 8.0, 2.2, 0.12,
            "#1f2a33", collide=False)
        box(0, 3.1, side * (w / 2.0 + 0.06), length - 1.0, 0.5, 0.12, "#1b1b1b",
            collide=False)
    if label:
        box(0, 8.4, w / 2.0 + 0.4, length * 0.5, 1.4, 0.7, colour,
            collide=False, decal=sign_decal(label, colour, "#1b1b1b",
                                            length * 0.5 / 1.4))


def barrel_prop(b: MapBuilder, x: float, z: float, colour: str = RUST,
                y: float = 0.0) -> None:
    """A drum that is always there (not one of the explosive ones)."""
    b.cyl([x, y + 2.0, z], [3.0, 4.0, 3.0], colour, material="metal")


def pallet_stack(b: MapBuilder, x: float, z: float, layers: int = 3) -> None:
    for i in range(layers):
        b.box([x, 0.4 + i * 0.8, z], [5.0, 0.8, 5.0],
              WOOD_LIGHT if i % 2 else WOOD, studs=False)


def lamp_post(b: MapBuilder, x: float, z: float, h: float = 15.0,
              colour: str = STEEL_DARK, light: str = LAMP, y: float = 0.0,
              arm: str = "") -> None:
    """A street lamp.  ``arm`` ("x+", "x-", "z+", "z-") hangs the head out
    over a road on a bracket; otherwise it sits on top of the pole."""
    b.cyl([x, y + h / 2.0, z], [1.1, h, 1.1], colour, material="metal")
    if not arm:
        b.box([x, y + h + 0.5, z], [2.8, 1.0, 2.8], colour)
        b.box([x, y + h - 0.25, z], [2.0, 0.5, 2.0], light, material="neon",
              collide=False)
        return
    dx, dz = {"x+": (1, 0), "x-": (-1, 0), "z+": (0, 1), "z-": (0, -1)}[arm]
    reach = 4.0
    if dx:
        b.box([x + dx * reach / 2.0, y + h - 0.4, z], [reach + 0.5, 0.6, 0.6],
              colour)
        b.box([x + dx * reach, y + h - 0.95, z], [2.6, 0.5, 1.6], colour)
        b.box([x + dx * reach, y + h - 1.45, z], [2.0, 0.5, 1.2], light,
              material="neon", collide=False)
    else:
        b.box([x, y + h - 0.4, z + dz * reach / 2.0], [0.6, 0.6, reach + 0.5],
              colour)
        b.box([x, y + h - 0.95, z + dz * reach], [1.6, 0.5, 2.6], colour)
        b.box([x, y + h - 1.45, z + dz * reach], [1.2, 0.5, 2.0], light,
              material="neon", collide=False)


def solid_fence(b: MapBuilder, x0: float, z0: float, x1: float, z1: float,
                h: float = 6.0, colour: str = WOOD, post: str = WOOD_DARK,
                every: float = 10.0, t: float = 0.8, first_post: bool = True,
                last_post: bool = True) -> None:
    """A board fence along x or z: panels and posts, all of it solid.

    Panels stop at each post and posts are deeper than the panels, so no
    two faces line up on one plane.
    """
    along_x = abs(z1 - z0) < 1e-6
    length = abs(x1 - x0) if along_x else abs(z1 - z0)
    count = max(1, int(round(length / every)))
    step = length / count
    start = min(x0, x1) if along_x else min(z0, z1)
    fixed = z0 if along_x else x0
    for i in range(count + 1):
        if (i == 0 and not first_post) or (i == count and not last_post):
            continue
        u = start + i * step
        if along_x:
            b.box([u, (h + 0.6) / 2.0, fixed], [1.2, h + 0.6, t + 0.6], post)
        else:
            b.box([fixed, (h + 0.6) / 2.0, u], [t + 0.6, h + 0.6, 1.2], post)
    for i in range(count):
        a = start + i * step + 0.6
        c = start + (i + 1) * step - 0.6
        if c - a < 0.1:
            continue
        if along_x:
            b.box([(a + c) / 2.0, h / 2.0, fixed], [c - a, h, t], colour)
        else:
            b.box([fixed, h / 2.0, (a + c) / 2.0], [t, h, c - a], colour)


def chain_fence(b: MapBuilder, x0: float, z0: float, x1: float, z1: float,
                h: float = 9.0, every: float = 12.0) -> None:
    """Chain link: see-through mesh panels between steel posts.  Solid --
    you can watch the horde through it, and it can watch you back."""
    along_x = abs(z1 - z0) < 1e-6
    length = abs(x1 - x0) if along_x else abs(z1 - z0)
    count = max(1, int(round(length / every)))
    step = length / count
    start = min(x0, x1) if along_x else min(z0, z1)
    fixed = z0 if along_x else x0
    for i in range(count + 1):
        u = start + i * step
        if along_x:
            b.cyl([u, h / 2.0 + 0.3, fixed], [0.9, h + 0.6, 0.9], STEEL,
                  material="metal")
        else:
            b.cyl([fixed, h / 2.0 + 0.3, u], [0.9, h + 0.6, 0.9], STEEL,
                  material="metal")
    for i in range(count):
        a = start + i * step + 0.45
        c = start + (i + 1) * step - 0.45
        if along_x:
            b.box([(a + c) / 2.0, h / 2.0, fixed], [c - a, h, 0.3], "#9aa3a8",
                  material="metal", alpha=0.38)
        else:
            b.box([fixed, h / 2.0, (a + c) / 2.0], [0.3, h, c - a], "#9aa3a8",
                  material="metal", alpha=0.38)


def boundary(b: Area, height: float = 30.0, colour: str = "#3c4a3a",
             cap: str = "#2f3b2e", rng: Optional[random.Random] = None,
             ragged: bool = False, horizon: str = "") -> None:
    """The edge of the world: a wall round the playable square, thick
    enough that nothing reaches over it, with a ragged skyline on top."""
    h = b.half
    t = b.margin
    rng = rng or random.Random(hash(b.id) & 0xFFFF)
    room_walls(b, rect(-h - t, h + t, -h - t, h + t), t, 0.0, height, colour)
    if horizon:
        skyline(b, horizon, height, rng)
    if not ragged:
        return
    for side in (-1, 1):
        for i in range(12):
            u = -h + (i + 0.5) * (2 * h) / 12.0
            top = rng.uniform(8.0, 22.0)
            b.box([side * (h + t / 2.0), height + top / 2.0, u],
                  [t + 2.0, top, 2 * h / 12.0 - 2.0], cap, collide=False)
            b.box([u, height + top / 2.0 + 0.01, side * (h + t / 2.0)],
                  [2 * h / 12.0 - 2.0, top, t + 2.0], cap, collide=False)


def treeline(b: MapBuilder, x0: float, z0: float, x1: float, z1: float,
             count: int, rng: random.Random, scale: float = 1.3,
             leaf: str = "#2a5f3c", trunk: str = WOOD_DARK,
             jitter: float = 4.0, kinds: str = "pine",
             avoid: Sequence[Rect] = ()) -> None:
    for i in range(count):
        f = i / float(max(1, count - 1))
        x = x0 + (x1 - x0) * f + rng.uniform(-jitter, jitter)
        z = z0 + (z1 - z0) * f + rng.uniform(-jitter, jitter)
        s = scale * rng.uniform(0.85, 1.25)
        if any(r[0] - 6.0 < x < r[1] + 6.0 and r[2] - 6.0 < z < r[3] + 6.0
               for r in avoid):
            continue
        if kinds == "pine" or (kinds == "mixed" and i % 3):
            b.pine(x, z, 0.0, s, trunk, leaf)
        else:
            b.tree(x, z, 0.0, s, trunk, leaf)


def supply_ammo(b: Area, x: float, y: float, z: float, facing: str = "z+") -> None:
    """An ammunition crate: the client draws the glowing lid and the prompt;
    this is the box itself, and the point the server uses."""
    b.box([x, y + 1.6, z], [6.0, 3.2, 4.0], "#3f5a2a", studs=True)
    b.box([x, y + 3.35, z], [6.2, 0.3, 4.2], "#2f4420")
    turn = {"z+": 0.0, "z-": math.pi, "x+": math.pi / 2.0, "x-": -math.pi / 2.0}
    dx, dz = {"z+": (0, 2.04), "z-": (0, -2.04), "x+": (3.04, 0),
              "x-": (-3.04, 0)}[facing]
    b.box([x + dx, y + 1.6, z + dz], [3.4, 1.4, 0.1], "#f2d23a",
          r=[0, turn[facing], 0], collide=False,
          decal=sign_decal("AMMO", "#f2d23a", "#1b1b1b", 3.4 / 1.4))
    b.mark("ammo", x, y, z)


def supply_med(b: Area, x: float, y: float, z: float, facing: str = "z+") -> None:
    """A first aid cabinet on legs, white with the red cross."""
    b.box([x, y + 2.4, z], [5.0, 4.8, 2.6], "#e8ecee", studs=False)
    turn = {"z+": 0.0, "z-": math.pi, "x+": math.pi / 2.0, "x-": -math.pi / 2.0}
    dx, dz = {"z+": (0, 1.34), "z-": (0, -1.34), "x+": (2.54, 0),
              "x-": (-2.54, 0)}[facing]
    b.box([x + dx, y + 2.8, z + dz], [2.6, 2.6, 0.08], "#ffffff",
          r=[0, turn[facing], 0], collide=False,
          decal=sign_decal("+", "#ffffff", "#c42b20", 1.0))
    b.mark("med", x, y, z)


def barrel_spot(b: Area, x: float, y: float, z: float) -> None:
    """Where an explosive drum stands each wave (the drum is live, not map)."""
    b.mark("barrel", x, y, z)


# ================================================================== houses
def house(b: MapBuilder, area: Rect, facing: str, colour: str,
          roof_colour: str, *, height: float = 13.0, enterable: bool = True,
          porch: bool = True, trim: str = "#e8e2d4", rng: Optional[random.Random] = None,
          door_w: float = 8.0, furnish: bool = True, back_door: bool = False,
          porch_depth: float = 6.0) -> None:
    """A detached house facing ``facing`` ("z-", "z+", "x-", "x+").

    Boarded windows, a porch with a roof on two posts, a stepped gable, and
    -- when it is ``enterable`` -- a front door you can walk through into a
    furnished room.  A house you cannot enter has its door as a solid panel
    flush with nothing: it stands proud of the wall and collides.
    """
    rng = rng or random.Random(int(area[0] * 7 + area[2] * 13))
    x0, x1, z0, z1 = area
    along_x = facing in ("z-", "z+")           # the front wall runs along x
    lo, hi = (x0, x1) if along_x else (z0, z1)
    mid = (lo + hi) / 2.0
    door = (mid - door_w / 2.0, mid + door_w / 2.0)
    head = 10.0
    sill, lintel = 3.6, 8.4
    span = hi - lo
    win = []
    for f in (0.18, 0.82):
        c = lo + span * f
        if abs(c - mid) > door_w / 2.0 + 3.5:
            win.append((c - 3.0, c + 3.0, sill, lintel))
    side_lo, side_hi = (z0, z1) if along_x else (x0, x1)
    side_mid = (side_lo + side_hi) / 2.0
    side_win = [(side_mid - 3.0, side_mid + 3.0, sill, lintel)]
    back = {"z-": "z+", "z+": "z-", "x-": "x+", "x+": "x-"}[facing]
    sides = ("x-", "x+") if along_x else ("z-", "z+")
    doors: Dict[str, List[Tuple[float, float, float]]] = {}
    windows: Dict[str, List[Tuple[float, float, float, float]]] = {
        facing: win, back: list(win), sides[0]: side_win, sides[1]: side_win}
    if enterable:
        doors[facing] = [(door[0], door[1], head)]
        if back_door:
            doors[back] = [(door[0], door[1], head)]
    building(b, area, 0.0, height, colour, roof_colour=roof_colour,
             floor_colour="#8a6f52" if enterable else "", doors=doors,
             windows=windows, boards=True, eave=1.0, lights=WARM if enterable else "")
    if enterable:
        threshold(b, area, facing, door)
        if back_door:
            threshold(b, area, back, door)
    gable(b, area, height + 1.2, roof_colour, "x" if along_x else "z", tiers=3,
          rise=1.5, overhang=0.0)
    out = {"z-": (0, -1), "z+": (0, 1), "x-": (-1, 0), "x+": (1, 0)}[facing]
    front = {"z-": z0, "z+": z1, "x-": x0, "x+": x1}[facing]
    if not enterable:
        # the front door, painted shut: a panel proud of the wall, solid
        if along_x:
            b.box([mid, 4.8, front + out[1] * 0.25], [door_w - 1.0, 9.0, 0.5],
                  "#5a3a22")
        else:
            b.box([front + out[0] * 0.25, 4.8, mid], [0.5, 9.0, door_w - 1.0],
                  "#5a3a22")
    if porch:
        depth = porch_depth
        if along_x:
            pz0, pz1 = sorted((front, front + out[1] * depth))
            slab(b, rect(mid - 9.0, mid + 9.0, pz0, pz1), 1.2, 1.2, WOOD_LIGHT)
            post_z = front + out[1] * (depth - 0.8)
            for k in (-1, 1):
                b.box([mid + k * 8.2, 1.2 + 4.65, post_z], [1.2, 9.3, 1.2], trim)
            slab(b, rect(mid - 9.6, mid + 9.6, pz0, pz1), 11.1, 0.6, roof_colour)
        else:
            px0, px1 = sorted((front, front + out[0] * depth))
            slab(b, rect(px0, px1, mid - 9.0, mid + 9.0), 1.2, 1.2, WOOD_LIGHT)
            post_x = front + out[0] * (depth - 0.8)
            for k in (-1, 1):
                b.box([post_x, 1.2 + 4.65, mid + k * 8.2], [1.2, 9.3, 1.2], trim)
            slab(b, rect(px0, px1, mid - 9.6, mid + 9.6), 11.1, 0.6, roof_colour)
    if enterable and furnish:
        _furnish(b, area, facing, rng)


def threshold(b: MapBuilder, area: Rect, side: str, span: Tuple[float, float],
              t: float = WALL_T, y0: float = 0.0) -> None:
    """Floor across a doorway, flush with the room's floor pad, so the way
    in has no trench the depth of the wall."""
    x0, x1, z0, z1 = area
    a, c = span
    if side == "z-":
        slab(b, rect(a, c, z0, z0 + t), y0 + FLOOR, FLOOR, "#8a6f52")
    elif side == "z+":
        slab(b, rect(a, c, z1 - t, z1), y0 + FLOOR, FLOOR, "#8a6f52")
    elif side == "x-":
        slab(b, rect(x0, x0 + t, a, c), y0 + FLOOR, FLOOR, "#8a6f52")
    else:
        slab(b, rect(x1 - t, x1, a, c), y0 + FLOOR, FLOOR, "#8a6f52")


def _furnish(b: MapBuilder, area: Rect, facing: str, rng: random.Random) -> None:
    """A sofa, a table and a bookcase, kept to the back half of the room so
    the doorway and the middle of the floor stay clear."""
    x0, x1, z0, z1 = area
    inner = rect(x0 + WALL_T + 1.5, x1 - WALL_T - 1.5, z0 + WALL_T + 1.5,
                 z1 - WALL_T - 1.5)
    ix0, ix1, iz0, iz1 = inner
    y = FLOOR
    sofa = rng.choice(["#6b3a3a", "#3a4f6b", "#5a6b3a", "#6b5a3a"])
    if facing in ("z-", "z+"):
        back_z = iz1 - 1.5 if facing == "z-" else iz0 + 1.5
        b.box([ix0 + 6.0, y + 1.4, back_z], [9.0, 2.8, 3.0], sofa, studs=True)
        b.box([ix1 - 5.0, y + 1.6, (iz0 + iz1) / 2.0], [6.0, 3.2, 6.0],
              WOOD, studs=True)
        b.box([ix1 - 1.2, y + 4.0, back_z - (2.0 if facing == "z-" else -2.0)],
              [2.4, 8.0, 6.0], WOOD_DARK)
    else:
        back_x = ix1 - 1.5 if facing == "x-" else ix0 + 1.5
        b.box([back_x, y + 1.4, iz0 + 6.0], [3.0, 2.8, 9.0], sofa, studs=True)
        b.box([(ix0 + ix1) / 2.0, y + 1.6, iz1 - 5.0], [6.0, 3.2, 6.0],
              WOOD, studs=True)
        b.box([back_x - (2.0 if facing == "x-" else -2.0), y + 4.0, iz1 - 1.2],
              [6.0, 8.0, 2.4], WOOD_DARK)


# ================================================================ vehicles
def van(b: MapBuilder, x: float, z: float, along: str = "x",
        colour: str = "#f2f2f2", stripe: str = "", length: float = 16.0,
        lights: str = "", label: str = "", y: float = 0.0,
        front: int = 1) -> None:
    """A box van -- an ambulance with a stripe and a light bar, or a plain
    delivery van.  ``front`` (+1/-1) is which end the cab is at."""
    w = 6.4

    def box(cx, cy, cz, sx, sy, sz, c, **kw):
        if along == "x":
            b.box([x + cx, y + cy, z + cz], [sx, sy, sz], c, **kw)
        else:
            b.box([x + cz, y + cy, z + cx], [sz, sy, sx], c, **kw)

    body = length * 0.68
    cab = length - body
    box(-front * cab / 2.0, 4.6, 0, body, 7.2, w, colour, material="metal")
    box(front * body / 2.0, 3.2, 0, cab, 4.4, w - 0.4, colour, material="metal")
    box(front * (body / 2.0 + cab * 0.1), 6.0, 0, cab * 0.6, 2.4, w - 1.0,
        "#24323c", material="metal")
    box(0, 0.6, 0, length - 2.0, 1.2, w - 1.2, "#1b1d20")
    if stripe:
        for side in (-1, 1):
            box(-front * cab / 2.0, 4.4, side * (w / 2.0 + 0.05), body, 1.0, 0.1,
                stripe)
    if lights:
        box(-front * (cab / 2.0 - body / 2.0 + 1.0), 8.45, 0, 1.2, 0.5, w - 1.6,
            lights, material="neon")
    if label:
        for side in (-1, 1):
            turn = "z+" if side > 0 else "z-"
            if along != "x":
                turn = "x+" if side > 0 else "x-"
            cx = -front * cab / 2.0
            if along == "x":
                wall_sign(b, x + cx, y + 6.4, z + side * (w / 2.0 + 0.4),
                          body * 0.7, 1.6, sign_decal(label, colour, stripe or
                                                      "#c42b20", body * 0.7 / 1.6),
                          turn, colour)
            else:
                wall_sign(b, x + side * (w / 2.0 + 0.4), y + 6.4, z + cx,
                          body * 0.7, 1.6, sign_decal(label, colour, stripe or
                                                      "#c42b20", body * 0.7 / 1.6),
                          turn, colour)
    for end in (-1, 1):
        for side in (-1, 1):
            if along == "x":
                b.cyl([x + end * length * 0.33, y + 1.3, z + side * (w / 2.0 - 0.3)],
                      [2.6, 1.0, 2.6], "#1b1d20", r=[math.pi / 2.0, 0, 0],
                      collide=False)
            else:
                b.cyl([x + side * (w / 2.0 - 0.3), y + 1.3, z + end * length * 0.33],
                      [2.6, 1.0, 2.6], "#1b1d20", r=[0, 0, math.pi / 2.0],
                      collide=False)


def army_truck(b: MapBuilder, x: float, z: float, along: str = "x",
               colour: str = "#4a5a3a", front: int = 1) -> None:
    """A canvas-backed army truck: cab, flatbed, a canvas tilt over it."""
    length, w = 22.0, 7.2

    def box(cx, cy, cz, sx, sy, sz, c, **kw):
        if along == "x":
            b.box([x + cx, cy, z + cz], [sx, sy, sz], c, **kw)
        else:
            b.box([x + cz, cy, z + cx], [sz, sy, sx], c, **kw)

    box(0, 1.2, 0, length - 2.0, 1.6, w - 1.6, "#1b1d20")
    box(front * (length / 2.0 - 3.0), 4.6, 0, 6.0, 5.2, w, colour, material="metal")
    box(front * (length / 2.0 - 2.2), 6.0, 0, 4.0, 1.8, w - 0.8, "#24323c")
    box(-front * 3.0, 2.8, 0, length - 6.0, 1.6, w, colour, studs=True)
    box(-front * 3.0, 6.7, 0, length - 6.4, 6.2, w - 0.4, "#6b6a4a")
    for k in (-1, 0, 1):
        for side in (-1, 1):
            if along == "x":
                b.cyl([x + k * 7.0, 1.6, z + side * (w / 2.0 - 0.4)], [3.2, 1.2, 3.2],
                      "#1b1d20", r=[math.pi / 2.0, 0, 0], collide=False)
            else:
                b.cyl([x + side * (w / 2.0 - 0.4), 1.6, z + k * 7.0], [3.2, 1.2, 3.2],
                      "#1b1d20", r=[0, 0, math.pi / 2.0], collide=False)


def hesco(b: MapBuilder, x: float, z: float, count: int, along: str = "x",
          height: float = 5.6) -> None:
    """A line of Hesco bastions: wire-mesh sacks of earth, chest high plus."""
    for i in range(count):
        u = (i - (count - 1) / 2.0) * 4.2
        cx, cz = (x + u, z) if along == "x" else (x, z + u)
        b.box([cx, height / 2.0, cz], [4.0, height, 4.0], "#a8956a", studs=True)
        b.box([cx, height + 0.15, cz], [3.4, 0.3, 3.4], "#7a6a4a")


def tent(b: MapBuilder, area: Rect, height: float, colour: str,
         doors: Optional[Dict[str, Sequence[Tuple[float, float, float]]]] = None,
         floor: str = "#6b6a52", lights: str = WARM) -> None:
    """A big canvas tent: thin walls, a ridged roof, a floor of boards."""
    building(b, area, 0.0, height, colour, t=0.8, roof_colour=colour,
             roof_t=0.6, floor_colour=floor, doors=doors, lights=lights,
             studs_roof=False)
    x0, x1, z0, z1 = area
    along = "x" if x1 - x0 >= z1 - z0 else "z"
    gable(b, area, height + 0.6, colour, along, tiers=3, rise=1.2, overhang=0.0)
    for side, spans in (doors or {}).items():
        for span in spans:
            threshold(b, area, side, (span[0], span[1]), t=0.8)


def watchtower(b: MapBuilder, x: float, z: float, h: float = 16.0,
               colour: str = WOOD, stair: str = "z-") -> None:
    """Four legs, a platform with solid rails, a roof, and a stair up."""
    half = 6.0
    for dx in (-1, 1):
        for dz in (-1, 1):
            b.box([x + dx * (half - 0.6), h / 2.0, z + dz * (half - 0.6)],
                  [1.2, h, 1.2], colour)
    slab(b, rect(x - half, x + half, z - half, z + half), h + 0.8, 0.8, WOOD_LIGHT,
         studs=True)
    gap = {"z-": "z-", "z+": "z+", "x-": "x-", "x+": "x+"}[stair]
    room_walls(b, rect(x - half, x + half, z - half, z + half), 0.8, h + 0.8,
               h + 3.6, colour, doors={gap: [(-2.6 + (x if gap[0] == "z" else z),
                                                2.6 + (x if gap[0] == "z" else z),
                                                h + 3.6)]})
    for dx in (-1, 1):
        for dz in (-1, 1):
            b.box([x + dx * (half - 0.4), h + 3.6 + 3.0, z + dz * (half - 0.4)],
                  [0.8, 6.0, 0.8], colour)
    slab(b, rect(x - half - 0.6, x + half + 0.6, z - half - 0.6, z + half + 0.6),
         h + 10.2, 0.6, "#4a3a2a")
    # the stair: straight up to the gap in the rail
    run = max(14.0, (h + 0.8) * 1.6)
    if stair == "z-":
        flight(b, "z", z - half - run, z - half, x - 2.6, x + 2.6, 0.0, h + 0.8,
               colour, fill=0.0)
    elif stair == "z+":
        flight(b, "z", z + half + run, z + half, x - 2.6, x + 2.6, 0.0, h + 0.8,
               colour, fill=0.0)
    elif stair == "x-":
        flight(b, "x", x - half - run, x - half, z - 2.6, z + 2.6, 0.0, h + 0.8,
               colour, fill=0.0)
    else:
        flight(b, "x", x + half + run, x + half, z - 2.6, z + 2.6, 0.0, h + 0.8,
               colour, fill=0.0)


def skyline(b: Area, kind: str, height: float, rng: random.Random) -> None:
    """What stands on top of the boundary: the horizon the area is set in.

    ``forest`` is a ridge of pines, ``city`` a row of dark towers with a few
    windows still lit, ``fog`` a low bank of sea mist with nothing in it.
    Nothing up there collides -- it is out of reach by twenty units.
    """
    h = b.half
    t = b.margin
    for side in (-1, 1):
        for axis in ("x", "z"):
            count = int(2 * h // 24)
            for i in range(count):
                u = -h + (i + 0.5) * (2 * h) / count
                at = side * (h + t / 2.0)
                cx, cz = (u, at) if axis == "x" else (at, u)
                if kind == "forest":
                    s = rng.uniform(1.6, 2.6)
                    b.cone([cx, height + 5.0 * s, cz], [11.0 * s, 10.0 * s, 11.0 * s],
                           rng.choice(["#1f3524", "#24402a", "#1b2e20"]),
                           collide=False)
                elif kind == "city":
                    tall = rng.uniform(14.0, 60.0)
                    wide = rng.uniform(16.0, 22.0)
                    b.box([cx, height + tall / 2.0, cz],
                          [wide if axis == "x" else t, tall, t if axis == "x" else wide],
                          rng.choice(["#1c222b", "#20262f", "#181d24"]), collide=False)
                    for k in range(int(tall // 9)):
                        if rng.random() < 0.3:
                            wy = height + 5.0 + k * 9.0
                            off = -side * (t / 2.0 + 0.06)
                            wx, wz = (cx + rng.uniform(-5, 5), cz + off) if axis == "x" \
                                else (cx + off, cz + rng.uniform(-5, 5))
                            b.box([wx, wy, wz], [2.4 if axis == "x" else 0.12, 2.0,
                                                 0.12 if axis == "x" else 2.4],
                                  rng.choice(["#ffd27a", "#cfe8ff", "#ffb35a"]),
                                  material="neon", collide=False)
                elif kind == "fog":
                    # tiled edge to edge (no two banks overlap) and each a
                    # hair deeper than the last, so no two faces line up
                    tall = rng.uniform(6.0, 14.0)
                    span = 2 * h / count
                    deep = t + 4.0 + (i % 7) * 0.07 + (0.03 if axis == "x" else 0.0)
                    lift = 0.0 if axis == "x" else 0.03
                    b.box([cx, height + lift + tall / 2.0, cz],
                          [span if axis == "x" else deep, tall,
                           deep if axis == "x" else span], "#3a4652",
                          collide=False, alpha=0.55)


# ================================================================ harbour
CONTAINER_H = 8.0     # a jump for a player and, just, for the infected too
CONTAINER_COLOURS = ["#8a3a2a", "#2f5f8a", "#3a6a3a", "#c8862a", "#6a3a6a",
                     "#5a6a72", "#a8322a", "#2a4a6a"]


def container(b: MapBuilder, x: float, y: float, z: float, along: str = "x",
              colour: str = "#8a3a2a", length: float = 26.0) -> None:
    """A shipping container: the box, and a darker rim round its top so a
    stack reads as boxes rather than as a wall."""
    w = 8.6
    sx, sz = (length, w) if along == "x" else (w, length)
    b.box([x, y + (CONTAINER_H - 0.4) / 2.0, z], [sx, CONTAINER_H - 0.4, sz],
          colour, material="metal")
    b.box([x, y + CONTAINER_H - 0.2, z], [sx - 0.4, 0.4, sz - 0.4], "#2a2d31",
          studs=True)
    # the doors, a darker panel on the end
    if along == "x":
        b.box([x + length / 2.0 + 0.06, y + 3.8, z], [0.12, 6.4, w - 1.4],
              "#2a2d31")
    else:
        b.box([x, y + 3.8, z + length / 2.0 + 0.06], [w - 1.4, 6.4, 0.12],
              "#2a2d31")


def bollard(b: MapBuilder, x: float, z: float, y: float = 0.0) -> None:
    b.cyl([x, y + 1.2, z], [1.8, 2.4, 1.8], "#2a2d31", material="metal")
    b.cyl([x, y + 2.6, z], [2.6, 0.4, 2.6], "#2a2d31", material="metal",
          collide=False)


def boat(b: MapBuilder, x: float, z: float, along: str = "x", length: float = 30.0,
         colour: str = "#e8e8e8", deck: float = 2.0, cabin: bool = True,
         base: float = -4.0) -> None:
    """A fishing boat afloat: a stepped hull from the seabed, a deck you can
    stand on and a wheelhouse."""
    w = 11.0

    def box(cx, cy0, cy1, cz, sx, sz, c, **kw):
        if along == "x":
            b.box([x + cx, (cy0 + cy1) / 2.0, z + cz], [sx, cy1 - cy0, sz], c, **kw)
        else:
            b.box([x + cz, (cy0 + cy1) / 2.0, z + cx], [sz, cy1 - cy0, sx], c, **kw)

    box(0, base, deck - 1.0, 0, length - 6.0, w - 2.0, "#3a2a24")
    box(0, deck - 1.0, deck, 0, length, w, colour, studs=True)
    box(length / 2.0 + 1.5, base + 2.0, deck, 0, 3.0, w - 4.0, colour)
    for side in (-1, 1):
        box(0, deck, deck + 2.0, side * (w / 2.0 - 0.4), length - 4.0, 0.8, colour)
    if cabin:
        box(-length * 0.18, deck, deck + 8.0, 0, 9.0, w - 3.0, "#c8c4b8")
        box(-length * 0.18, deck + 8.0, deck + 8.6, 0, 10.0, w - 2.4, "#2a3a4a")
