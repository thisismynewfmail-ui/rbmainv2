"""Interiors for Prop Panic's buildings: walls with doors and windows that
line up storey to storey, the paint and floors of each room, and the trim
round a doorway.

A building is drawn the Last Light way (app/game/maps/lastlight/kit.py):
the outer walls are solid and meet at the corners without overlapping,
partitions butt against them, and a floor slab sits between the walls.
What makes a room *a room* here is laid over that -- a coat of paint a
hair proud of each wall face (wallpaper, tiles, panelling), a floor
covering a hair above the slab -- and never collides, so the walls a
player meets are the walls the rules know about.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..kit import wall

Rect = Tuple[float, float, float, float]
Hole = Tuple[float, float, float, float]

PAINT = 0.05          # how proud of its wall a coat of paint stands
# how big a square of floor one print of a floor decal covers
DECAL_TILE = {"planks": 18.0, "bricks": 10.0, "tiles": 8.0, "harlequin": 8.0}
GLASS = "#8fb8c8"


def openings(b, axis: str, at: float, thickness: float, lo: float, hi: float, y0: float,
             y1: float, colour: str, holes: Sequence[Hole] = (), glass: bool = False,
             **kw) -> None:
    """A straight wall with any number of openings, stacked or side by side
    (a window over a window, a door under a fanlight).  ``axis`` is the way
    the wall runs ("z": it stands at x = ``at``); each hole is (start, end,
    bottom, top), a bottom at or below ``y0`` making it a doorway.  The wall
    is cut into strips at every hole edge, and each strip into the pieces
    between its holes, so the pieces tile the wall exactly.  ``glass``
    glazes the windows (a pane in the middle of the wall)."""
    holes = [(max(lo, min(hi, a)), max(lo, min(hi, c)), bottom, top)
             for a, c, bottom, top in holes]
    holes = [h for h in holes if h[1] - h[0] > 1e-6]
    cuts = sorted({lo, hi} | {v for h in holes for v in (h[0], h[1])})

    def piece(a: float, c: float, ya: float, yb: float, col: str = colour,
              t: float = thickness, **extra) -> None:
        if c - a < 1e-6 or yb - ya < 1e-6:
            return
        options = dict(kw)
        options.update(extra)
        if axis == "z":
            b.box([at, (ya + yb) / 2.0, (a + c) / 2.0], [t, yb - ya, c - a], col, **options)
        else:
            b.box([(a + c) / 2.0, (ya + yb) / 2.0, at], [c - a, yb - ya, t], col, **options)

    # strips that no hole crosses are merged back into one piece
    strips: List[Tuple[float, float, List[Hole]]] = []
    for a, c in zip(cuts, cuts[1:]):
        inside = sorted((h for h in holes if h[0] < c - 1e-6 and h[1] > a + 1e-6),
                        key=lambda h: h[2])
        if strips and not inside and not strips[-1][2]:
            strips[-1] = (strips[-1][0], c, [])
        else:
            strips.append((a, c, inside))
    for a, c, inside in strips:
        cursor = y0
        for _, _, bottom, top in inside:
            bottom, top = max(y0, bottom), min(y1, top)
            piece(a, c, cursor, bottom)
            cursor = max(cursor, top)
        piece(a, c, cursor, y1)
    if glass:
        for a, c, bottom, top in holes:
            if bottom > y0 + 1e-6 and top > bottom:
                piece(a, c, bottom, min(y1, top), GLASS, thickness * 0.3, material="glass",
                      alpha=0.42)


def paint(b, axis: str, face: float, facing: int, lo: float, hi: float, y0: float,
          y1: float, colour: str, holes: Sequence[Hole] = ()) -> None:
    """A coat of paint on a wall face.  ``axis`` is the way the wall runs
    ("z": the face is at x = ``face``), ``facing`` the way the face looks
    (+1 or -1); ``holes`` are the wall's doors and windows, (start, end,
    bottom, top)."""
    openings(b, axis, face + facing * PAINT / 2.0, PAINT, lo, hi, y0, y1, colour,
             list(holes), collide=False)


def interior(b, inner: Rect, y0: float, y1: float, colour: str,
             holes: Optional[Dict[str, Sequence[Hole]]] = None,
             floor: str = "", floor_decal: str = "", sides: Iterable[str] = ("x-", "x+", "z-", "z+"),
             walls: Optional[Dict[str, str]] = None) -> None:
    """Paint a room: ``inner`` is the rectangle its walls' faces enclose.
    The two walls along z run the full depth and the two along x fit
    between them, so the coats never overlap in a corner.  ``walls``
    overrides the colour of a side; ``floor`` lays a floor covering."""
    x0, x1, z0, z1 = inner
    holes = holes or {}
    walls = walls or {}
    sides = list(sides)
    if "x-" in sides:
        paint(b, "z", x0, 1, z0, z1, y0, y1, walls.get("x-", colour), holes.get("x-", ()))
    if "x+" in sides:
        paint(b, "z", x1, -1, z0, z1, y0, y1, walls.get("x+", colour), holes.get("x+", ()))
    xa = x0 + (PAINT if "x-" in sides else 0.0)
    xb = x1 - (PAINT if "x+" in sides else 0.0)
    if "z-" in sides:
        paint(b, "x", z0, 1, xa, xb, y0, y1, walls.get("z-", colour), holes.get("z-", ()))
    if "z+" in sides:
        paint(b, "x", z1, -1, xa, xb, y0, y1, walls.get("z+", colour), holes.get("z+", ()))
    if floor and floor_decal:
        tiled(b, inner, y0, floor, floor_decal, DECAL_TILE.get(floor_decal, 8.0))
    elif floor:
        covering(b, inner, y0, floor)


def covering(b, area: Rect, y: float, colour: str, decal: str = "") -> None:
    """A floor covering on the slab whose top is ``y`` (boards, tiles,
    carpet): paint, as far as feet are concerned."""
    x0, x1, z0, z1 = area
    part = b.box([(x0 + x1) / 2.0, y + 0.02, (z0 + z1) / 2.0], [x1 - x0, 0.04, z1 - z0],
                 colour, collide=False, decal=decal)
    if decal:
        part["dw"] = 1                 # boards and tiles on the top, not the edge


def tiled(b, area: Rect, y: float, colour: str, decal: str = "tiles", size: float = 8.0) -> None:
    """A floor covering laid in squares of about ``size``: a decal is
    stretched over the face it is printed on, so a big floor in one piece
    would wear its pattern at the size of the room."""
    import math
    x0, x1, z0, z1 = area
    nx = max(1, int(math.ceil((x1 - x0) / size - 1e-6)))
    nz = max(1, int(math.ceil((z1 - z0) / size - 1e-6)))
    for i in range(nx):
        for j in range(nz):
            covering(b, (x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx,
                         z0 + (z1 - z0) * j / nz, z0 + (z1 - z0) * (j + 1) / nz), y, colour, decal)


def trim(b, axis: str, at: float, thickness: float, a: float, c: float, y0: float,
         head: float, colour: str, width: float = 0.5, proud: float = 0.15) -> None:
    """The architrave round a doorway in a wall ``thickness`` thick at
    ``at``, on both faces: two jambs and a head, standing ``proud`` of the
    wall."""
    depth = thickness + 2 * proud
    # each piece reaches a hair into the opening, so none of its faces lies
    # in the plane of the wall's own edge
    pieces = [(a - (width - 0.05) / 2.0, width + 0.05, y0, head - 0.05),
              (c + (width - 0.05) / 2.0, width + 0.05, y0, head - 0.05),
              ((a + c) / 2.0, c - a + 2 * width, head - 0.05, head + width)]
    for centre, length, ya, yb in pieces:
        if axis == "z":
            b.box([at, (ya + yb) / 2.0, centre], [depth, yb - ya, length], colour)
        else:
            b.box([centre, (ya + yb) / 2.0, at], [length, yb - ya, depth], colour)


def partition(b, axis: str, at: float, lo: float, hi: float, y0: float, y1: float,
              colour: str, doors: Sequence[Tuple[float, float, float]] = (),
              thickness: float = 0.6, trim_colour: str = "") -> None:
    """An inside wall with doorways (start, end, head), and their trim."""
    wall(b, axis, at, thickness, lo, hi, y0, y1, colour, gaps=list(doors))
    if trim_colour:
        for a, c, head in doors:
            trim(b, axis, at, thickness, a, c, y0, min(head, y1 - 0.6), trim_colour)


def door_holes(doors: Sequence[Tuple[float, float, float]], y0: float) -> List[Hole]:
    """Doorways as paint holes (their trim covers the edge of the paint)."""
    return [(a - 0.5, c + 0.5, y0 - 1.0, head + 0.5) for a, c, head in doors]


def window(b, axis: str, at: float, thickness: float, a: float, c: float, sill: float,
           top: float, colour: str, proud: float = 0.2, shutters: str = "",
           out: int = 1) -> None:
    """A window's frame round its hole in a wall (the hole and its glass
    come from holed_wall), proud of both faces, with shutters on the
    outside (``out`` is the side the outside is on, +1 or -1)."""
    depth = thickness + 2 * proud
    pieces = [((a + c) / 2.0, c - a + 1.0, sill - 0.5, sill + 0.05),
              ((a + c) / 2.0, c - a + 1.0, top - 0.05, top + 0.5),
              (a - 0.225, 0.55, sill + 0.05, top - 0.05), (c + 0.225, 0.55, sill + 0.05, top - 0.05)]
    for centre, length, ya, yb in pieces:
        if axis == "z":
            b.box([at, (ya + yb) / 2.0, centre], [depth, yb - ya, length], colour)
        else:
            b.box([centre, (ya + yb) / 2.0, at], [length, yb - ya, depth], colour)
    if shutters:
        w = (c - a) / 2.0
        for centre in (a - 0.5 - w / 2.0, c + 0.5 + w / 2.0):
            if axis == "z":
                b.box([at + out * (thickness / 2.0 + 0.12), (sill + top) / 2.0, centre],
                      [0.24, top - sill, w], shutters)
            else:
                b.box([centre, (sill + top) / 2.0, at + out * (thickness / 2.0 + 0.12)],
                      [w, top - sill, 0.24], shutters)


def stairwell_floor(b, area: Rect, top: float, thickness: float, colour: str,
                    holes: Sequence[Rect]) -> None:
    """A floor slab with openings in it (stairwells), cut so the pieces
    tile it exactly."""
    from ..kit import carve, plate
    plate(b, carve(area, list(holes)), top, thickness, colour)


def shell(b, area: Rect, y0: float, y1: float, colour: str,
          holes: Optional[Dict[str, Sequence[Hole]]] = None, t: float = 1.2,
          glass: bool = True, frame: str = "", shutters: str = "") -> None:
    """A building's four outer walls round ``area`` (the walls along z run
    the full depth, the two along x fit between them), with ``holes`` per
    side, glazed, and a frame round every window."""
    x0, x1, z0, z1 = area
    holes = holes or {}
    openings(b, "z", x0 + t / 2.0, t, z0, z1, y0, y1, colour, holes.get("x-", ()), glass=glass)
    openings(b, "z", x1 - t / 2.0, t, z0, z1, y0, y1, colour, holes.get("x+", ()), glass=glass)
    openings(b, "x", z0 + t / 2.0, t, x0 + t, x1 - t, y0, y1, colour, holes.get("z-", ()),
             glass=glass)
    openings(b, "x", z1 - t / 2.0, t, x0 + t, x1 - t, y0, y1, colour, holes.get("z+", ()),
             glass=glass)
    if not frame:
        return
    for side, axis, at, out in (("x-", "z", x0 + t / 2.0, -1), ("x+", "z", x1 - t / 2.0, 1),
                                ("z-", "x", z0 + t / 2.0, -1), ("z+", "x", z1 - t / 2.0, 1)):
        for a, c, sill, top in holes.get(side, ()):
            if sill > y0 + 0.5:
                window(b, axis, at, t, a, c, sill, top, frame, shutters=shutters, out=out)


def pen_door(b, axis: str, at: float, a: float, c: float, y0: float, head: float,
             thickness: float, colour: str, key: str = "pen", decal: str = "panels") -> None:
    """The door that holds the seekers in their pen through the countdown:
    a switchable solid filling the doorway (a ``pen`` group), off until
    the rules switch it on, so the map as built has the doorway open."""
    with b.detached() as parts:
        if axis == "z":
            b.box([at, (y0 + head) / 2.0, (a + c) / 2.0], [thickness, head - y0, c - a], colour,
                  material="metal", decal=decal)
        else:
            b.box([(a + c) / 2.0, (y0 + head) / 2.0, at], [c - a, head - y0, thickness], colour,
                  material="metal", decal=decal)
    b.dynamic(key, parts, on=False, group="pen")


def grow(area: Rect, by: float) -> Rect:
    """A rectangle ``by`` bigger all round (a floor covering is cut back
    from a stairwell's edge, so the rail standing on that edge never shares
    a face with it)."""
    x0, x1, z0, z1 = area
    return (x0 - by, x1 + by, z0 - by, z1 + by)


def skirt(b, half_x: float, half_z: float, colour: str, reach: float = 220.0) -> None:
    """Ground beyond the edge of the world, under the scenery out there, so
    the backdrop stands on something.  Its top is a hair under the area's
    own ground, out of reach and never in the way."""
    b.box([0.0, -1.05, 0.0], [2 * (half_x + reach), 2.0, 2 * (half_z + reach)], colour,
          collide=False)
