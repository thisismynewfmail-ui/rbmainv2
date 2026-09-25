"""A bot's body: the same collision a player's browser runs, on the server.

People are simulated in their own browser (``static/js/game/physics.js``):
every frame their box is moved one axis at a time against the map's solid
parts, stepping up low ledges, landing on floors and bumping heads on
ceilings, and the server only checks the result. Bots have no browser, so
this module is that same routine in Python, fed the same solids the server
already keeps for hit detection.

It is what stops a bot jumping for a ledge from ending up inside the block,
a fast fall from skipping past a floor, or a jump under a walkway from
coming out on top of it. Movement is split into sub-steps no longer than
``MAX_STEP`` so a 20 Hz tick cannot carry a body through a thin wall or
floor the way one long step could.
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

# Physics.SIZE and STEP_HEIGHT in the client: a bot fits where a player fits
HALF_W = 1.2
HALF_D = 0.9
HEIGHT = 5.4
STEP_HEIGHT = 2.1
MAX_STEP = 0.8          # longest move along any axis in one sub-step
MAX_SUBSTEPS = 8
MAX_FALL = 140.0        # the client's terminal velocity

Box = Tuple[Sequence[float], Sequence[float]]


class Result:
    __slots__ = ("grounded", "hit_wall", "landed", "head_bump")

    def __init__(self) -> None:
        self.grounded = False
        self.hit_wall = False
        self.landed = False
        self.head_bump = False


def _overlaps(box: Box, x0: float, x1: float, y0: float, y1: float,
              z0: float, z1: float) -> bool:
    lo, hi = box
    return hi[0] > x0 and lo[0] < x1 and hi[1] > y0 and lo[1] < y1 \
        and hi[2] > z0 and lo[2] < z1


def blocked(boxes: List[Box], x: float, y: float, z: float) -> bool:
    """Would a body standing at (x, y, z) be inside something solid?"""
    for box in boxes:
        if _overlaps(box, x - HALF_W, x + HALF_W, y + 0.05, y + HEIGHT,
                     z - HALF_D, z + HALF_D):
            return True
    return False


def supported(boxes: List[Box], x: float, y: float, z: float,
              below: float = STEP_HEIGHT + 0.5) -> bool:
    """Is there floor under a body at (x, y, z), counting a step down as floor?"""
    for lo, hi in boxes:
        if hi[0] > x - HALF_W and lo[0] < x + HALF_W and hi[2] > z - HALF_D \
                and lo[2] < z + HALF_D and y - below <= hi[1] <= y + 0.3:
            return True
    return False


def nearby(instance, pos: Sequence[float], vel: Sequence[float], dt: float) -> List[Box]:
    """Every solid the body could touch this tick, from the server's buckets."""
    reach_x = abs(vel[0] * dt) + HALF_W + 2.5
    reach_z = abs(vel[2] * dt) + HALF_D + 2.5
    reach_y = abs(vel[1] * dt) + STEP_HEIGHT + 1.0
    lo = [pos[0] - reach_x, pos[1] - reach_y, pos[2] - reach_z]
    hi = [pos[0] + reach_x, pos[1] + HEIGHT + reach_y, pos[2] + reach_z]
    return instance._colliders_near(lo, hi)


def move(boxes: List[Box], pos: List[float], vel: List[float], dt: float) -> Result:
    """Move ``pos`` by ``vel * dt`` against ``boxes``; both lists are updated.

    Horizontal velocity blocked by a wall is zeroed, vertical velocity is
    zeroed on landing or a head bump, exactly as the client does it.
    """
    result = Result()
    if vel[1] < -MAX_FALL:
        vel[1] = -MAX_FALL
    longest = max(abs(vel[0]), abs(vel[1]), abs(vel[2])) * dt
    steps = min(MAX_SUBSTEPS, max(1, int(math.ceil(longest / MAX_STEP))))
    h = dt / steps
    for _ in range(steps):
        _substep(boxes, pos, vel, h, result)
    # standing check: a thin probe under the feet
    if not result.grounded:
        x, y, z = pos
        for box in boxes:
            if _overlaps(box, x - HALF_W, x + HALF_W, y - 0.22, y + 0.1,
                         z - HALF_D, z + HALF_D):
                result.grounded = True
                break
    return result


def _substep(boxes: List[Box], pos: List[float], vel: List[float], dt: float,
             result: Result) -> None:
    # ---- X
    dx = vel[0] * dt
    if dx:
        nx = pos[0] + dx
        for box in boxes:
            if not _overlaps(box, nx - HALF_W, nx + HALF_W, pos[1] + 0.05, pos[1] + HEIGHT,
                             pos[2] - HALF_D, pos[2] + HALF_D):
                continue
            top = box[1][1]
            if top - pos[1] <= STEP_HEIGHT and top > pos[1]:
                lifted = top + 0.02
                if not blocked(boxes, nx, lifted, pos[2]):
                    pos[1] = lifted
                    continue
            nx = min(nx, box[0][0] - HALF_W - 0.001) if dx > 0 \
                else max(nx, box[1][0] + HALF_W + 0.001)
            vel[0] = 0.0
            result.hit_wall = True
        pos[0] = nx
    # ---- Z
    dz = vel[2] * dt
    if dz:
        nz = pos[2] + dz
        for box in boxes:
            if not _overlaps(box, pos[0] - HALF_W, pos[0] + HALF_W, pos[1] + 0.05,
                             pos[1] + HEIGHT, nz - HALF_D, nz + HALF_D):
                continue
            top = box[1][1]
            if top - pos[1] <= STEP_HEIGHT and top > pos[1]:
                lifted = top + 0.02
                if not blocked(boxes, pos[0], lifted, nz):
                    pos[1] = lifted
                    continue
            nz = min(nz, box[0][2] - HALF_D - 0.001) if dz > 0 \
                else max(nz, box[1][2] + HALF_D + 0.001)
            vel[2] = 0.0
            result.hit_wall = True
        pos[2] = nz
    # ---- Y
    dy = vel[1] * dt
    ny = pos[1] + dy
    for box in boxes:
        if not _overlaps(box, pos[0] - HALF_W, pos[0] + HALF_W, ny, ny + HEIGHT,
                         pos[2] - HALF_D, pos[2] + HALF_D):
            continue
        if dy <= 0:
            if box[1][1] <= pos[1] + STEP_HEIGHT + 0.5:
                ny = max(ny, box[1][1])
                if vel[1] < -12:
                    result.landed = True
                vel[1] = 0.0
                result.grounded = True
        else:
            ny = min(ny, box[0][1] - HEIGHT - 0.001)
            vel[1] = 0.0
            result.head_bump = True
    pos[1] = ny
