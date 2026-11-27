"""What every railroad built since Thunder Junction shares: the two start
yards at the west end, the depots down the lines (on ground levelled at
their track's height), the brake levers, the coal and the two termini at
the east end -- each map passing its own names, colours and ground.

A map keeps a list of the rectangles it has built on (``keep``) so the
telegraph poles and the scatter stay out of them; every helper here adds
what it builds to that list.
"""
from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..kit import WARM, WOOD, WOOD_DARK, ArenaArea, building, gable, lantern, rect, sign_decal, threshold
from . import rails
from .land import Land, height_at
from .rails import beside, buffer_stop, coal_heap, depot, lever, stair

Rect = Tuple[float, float, float, float]
DepotSpec = Tuple[str, float, float, str, int, str]


def depot_spot(path, f: float, side: float):
    """Where rails.depot will put a depot's platform (its centre and half
    sizes), so the ground can be levelled for it first."""
    total = rails.length(path)
    x, z, yaw = rails.at(path, total * f)
    rx, rz = math.cos(yaw), -math.sin(yaw)
    along_x = abs(math.sin(yaw)) > 0.7
    hx, hz = (16.0, 6.0) if along_x else (6.0, 16.0)
    offset = max(15.0, abs(rx) * hx + abs(rz) * hz + 7.0)
    return x + rx * side * offset, z + rz * side * offset, hx, hz


def plan_depots(land: Land, depots: Sequence[DepotSpec], lanes: Dict[str, Sequence],
                ys: Sequence[float], bases: Dict, blend: float = 8.0) -> None:
    """Level the ground under each depot at its track's height there."""
    for lane, f, side, _name, _stage, _roof in depots:
        path = lanes[lane]
        ox, oz, hx, hz = depot_spot(path, f, side)
        base = round(height_at(path, ys, rails.length(path) * f) * 2.0) / 2.0
        land.flatten(rect(ox - hx - 4.0, ox + hx + 4.0, oz - hz - 1.0, oz + hz + 1.0), base, blend=blend)
        bases[(lane, f)] = base


def place_depots(b: ArenaArea, depots: Sequence[DepotSpec], lanes: Dict[str, Sequence],
                 bases: Dict, keep: List[Rect]) -> None:
    for lane, f, side, name, stage, roof in depots:
        depot(b, lane, lanes[lane], f, side, name, stage, roof, base=bases[(lane, f)])
        entry = b.points["depot"][-1]
        ox, oz = entry["p"][0] - b.ox, entry["p"][2] - b.oz
        keep.append(rect(ox - 22.0, ox + 22.0, oz - 10.0, oz + 10.0))


def place_levers(b: ArenaArea, land: Land, lanes: Dict[str, Sequence], keep: List[Rect]) -> None:
    """The brake levers at the usual fractions, standing on whatever the
    ground is there (their warning plate only where it is level)."""
    for lane, sides in (("a", (-1.0, 1.0)), ("b", (1.0, -1.0))):
        path = lanes[lane]
        for index, (f, side) in enumerate(zip(rails.LEVER_FRACTIONS, sides)):
            total = rails.length(path)
            x, z, _yaw = beside(path, total * f, side * 6.5)
            base = land.height(x, z)
            level = all(abs(land.height(x + dx, z + dz) - base) < 1e-6
                        for dx in (-2.6, 2.6) for dz in (-2.6, 2.6))
            lever(b, lane, path, f, side, index, base=base, plate=level)
            keep.append(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0))


def plan_coal(land: Land, spots: Sequence[Tuple[float, float]], bases: Dict) -> None:
    for x, z in spots:
        y = float(round(land.height(x, z)))
        land.flatten(rect(x - 5.5, x + 5.5, z - 5.5, z + 5.5), y, blend=6.0)
        bases[("coal", x, z)] = y


def place_coal(b: ArenaArea, spots: Sequence[Tuple[float, float]], bases: Dict,
               rng: random.Random, keep: List[Rect]) -> None:
    for x, z in spots:
        coal_heap(b, x, z, rng, base=bases[("coal", x, z)])
        keep.append(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0))


def start_yards(b: ArenaArea, names: Tuple[str, str], roofs: Tuple[str, str], keep: List[Rect],
                post: str = WOOD_DARK,
                sign_bg: str = rails.CREAM, sign_fg: str = "#3a2414") -> None:
    """The platforms the companies start from at the west end: lane a's
    north of its track, lane b's south of its, a roofed shelter with the
    yard's name over it, twelve spawns, the buffer stop behind."""
    for lane, z, name, roof in (("a", -150.0, names[0], roofs[0]), ("b", 150.0, names[1], roofs[1])):
        side = -1.0 if z < 0 else 1.0
        pz = z + side * 15.0
        rails.platform(b, rect(-376.0, -322.0, pz - 6.0, pz + 6.0))
        stair(b, "x", -319.0, -322.0, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
        rails.shelter(b, rect(-370.0, -334.0, pz - 3.4, pz + 3.4), 1.2, 9.0, roof, post=post)
        b.box([-352.0, 1.2 + 9.6 + 1.2, pz], [30.0, 2.4, 0.5], sign_bg,
              decal=sign_decal(name, sign_bg, sign_fg, 12.5))
        for sx in (-373.0, -362.0, -354.0, -346.0, -338.0, -327.0):
            for w in (-1.4, 1.4):
                b.team_spawn(lane, sx, 1.51, pz + w, math.pi / 2.0, 0)
        buffer_stop(b, -372.0, z, math.pi / 2.0, roof)
        lantern(b, -326.0, 9.8, pz, WARM)
        b.mark("start", -362.0, 0.5, z, lane=lane)
        keep.append(rect(-380.0, -318.0, pz - 8.0, pz + 8.0))


def termini(b: ArenaArea, names: Tuple[str, str], roofs: Tuple[str, str], keep: List[Rect],
            house: str, trim: str, sign_bg: str = rails.GOLD, sign_fg: str = "#3a2414",
            house_fn: Optional[Callable[[ArenaArea, Rect, float, str], None]] = None) -> None:
    """The two stations at the east end: lane a's south of its track (its
    line ends at z 150), lane b's north (z -150); a platform, a shelter,
    the name board, the buffer stop, the finish mark and the station
    house behind -- ``house_fn(b, area, side, roof)`` to build it another
    way."""
    for lane, z, name, roof in (("a", 150.0, names[0], roofs[0]), ("b", -150.0, names[1], roofs[1])):
        side = 1.0 if z > 0 else -1.0
        pz = z + side * 15.0
        rails.platform(b, rect(310.0, 380.0, pz - 6.0, pz + 6.0))
        stair(b, "x", 307.0, 310.0, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
        rails.shelter(b, rect(318.0, 372.0, pz - 3.4, pz + 3.4), 1.2, 9.0, roof)
        b.box([345.0, 1.2 + 9.6 + 1.2, pz], [44.0, 2.4, 0.5], sign_bg,
              decal=sign_decal(name, sign_bg, sign_fg, 18.0))
        buffer_stop(b, 372.0, z, math.pi / 2.0, roof)
        area = rect(326.0, 378.0, pz + side * 8.0, pz + side * 28.0)
        if house_fn is not None:
            house_fn(b, area, side, roof)
        else:
            lo, hi = min(area[2], area[3]), max(area[2], area[3])
            building(b, area, 0.0, 12.0, house, roof_colour=roof,
                     doors={"x-": [(lo + 6.0, hi - 6.0, 9.0)]},
                     windows={"z-" if side > 0 else "z+": [(330.0, 344.0, 4.0, 9.0), (356.0, 370.0, 4.0, 9.0)]},
                     glass=True, lights=WARM)
            threshold(b, area, "x-", (lo + 6.0, hi - 6.0))
            gable(b, area, 13.2, trim, "x", 4, 1.3, 0.8)
        b.mark("finish", 362.0, 0.5, z, lane=lane)
        keep.append(rect(304.0, 382.0, min(pz - 8.0, area[2]) - 2.0, max(pz + 8.0, area[3]) + 2.0))
