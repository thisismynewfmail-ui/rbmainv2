"""Authoring helpers for item models.

The catalogue describes every item as a list of parts -- a mesh name, a
centre, a size, a colour and optionally a rotation, material, decal or alpha
-- and the renderer draws each one as a unit mesh moved, turned and scaled
into place.  That is a fine wire format and a poor way to *model*: placing a
bent horn so its root sits on the skull means knowing where the root is in
the horn's own bounding box, turned by the part's rotation.

This module does that arithmetic once.  ``SHAPES`` mirrors the native size
and centre of every sculpted mesh in ``static/js/engine/shapes.js`` (run
``node`` on that file to regenerate the numbers if a shape changes), and
:func:`place` puts a point *on* the shape at a point in item space, with the
same rotation order the renderer uses (``R = Ry * Rx * Rz``).

Nothing here is needed at runtime by the browser: the catalogue is resolved
to plain part dicts at import time, exactly as if they had been typed out.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

Vec = Sequence[float]

# Native size and centre of each sculpted mesh (see shapes.js, Shapes.native
# and Shapes.centre).  A part drawn with ``s`` equal to the native size times
# a uniform factor keeps the proportions the mesh was modelled at.
SHAPES: Dict[str, Dict[str, List[float]]] = {
    "hemi": {"size": [1, 0.5, 1], "centre": [0, 0.25, 0]},
    "capcrown": {"size": [1, 0.52, 1], "centre": [0, 0.26, 0]},
    "brim": {"size": [1, 0.13, 1], "centre": [0, 0.065, 0]},
    "ring": {"size": [1, 0.2, 1], "centre": [0, 0.1, 0]},
    "flare": {"size": [1, 1, 1], "centre": [0, 0.5, 0]},
    "bell": {"size": [1, 1.02, 1], "centre": [0, 0.51, 0]},
    "bowl": {"size": [1, 0.6, 1], "centre": [0, 0.3, 0]},
    "pumpkin": {"size": [1, 0.7062, 1], "centre": [0, 0.4, 0]},
    "gem": {"size": [1, 0.72, 1], "centre": [0, 0.36, 0]},
    "teardrop": {"size": [1, 1, 1], "centre": [0, 0.5, 0]},
    "capsule": {"size": [1, 3, 1], "centre": [0, 1.5, 0]},
    "cask": {"size": [1, 1, 1], "centre": [0, 0.5, 0]},
    "disc": {"size": [1, 1, 0.16], "centre": [0, 0, 0]},
    "star": {"size": [0.9511, 0.9045, 0.14], "centre": [0, 0.0477, 0]},
    "shield": {"size": [0.9718, 1.0108, 0.14], "centre": [0, 0.0054, 0]},
    "wing": {"size": [1, 0.9, 0.08], "centre": [0, 0.05, 0]},
    "blade": {"size": [1.0034, 0.5008, 0.05], "centre": [0.0017, 0.0504, 0]},
    "crescent": {"size": [0.54, 1.0077, 0.12], "centre": [-0.17, 0, 0]},
    "bat": {"size": [1, 0.46, 0.06], "centre": [0, 0.03, 0]},
    "leaf": {"size": [0.3422, 1, 0.05], "centre": [0, 0, 0]},
    "feather": {"size": [0.31, 1.03, 0.04], "centre": [0.005, -0.015, 0]},
    "flame": {"size": [0.6025, 0.995, 0.12], "centre": [0.0013, 0.0025, 0]},
    "bone": {"size": [0.9986, 0.4361, 0.12], "centre": [0, 0, 0]},
    "candycorn": {"size": [0.6206, 1, 0.24], "centre": [0, 0, 0]},
    "ribbon": {"size": [1, 1, 0.05], "centre": [0, 0, 0]},
    "chevron": {"size": [1, 0.82, 0.12], "centre": [0, 0.09, 0]},
    "cog": {"size": [0.9956, 0.9956, 0.14], "centre": [0, 0, 0]},
    "heart": {"size": [0.9724, 0.9685, 0.16], "centre": [0, -0.0157, 0]},
    "visor": {"size": [1.1855, 0.2427, 0.8257], "centre": [0, -0.1213, 0.5672]},
    "cowbrim": {"size": [1, 0.3025, 0.982], "centre": [0, 0.0687, 0]},
    "tricorn": {"size": [1.076, 0.4399, 1.0604], "centre": [0, 0.18, -0.0069]},
    "cape": {"size": [1.3, 1.4011, 0.2168], "centre": [0, -0.6995, -0.0931]},
    "horn": {"size": [0.5109, 0.589, 0.2613], "centre": [0.1215, 0.2904, 0]},
    "hook": {"size": [0.6069, 0.8315, 0.3666], "centre": [0.1884, 0.2341, 0]},
    "arch": {"size": [1.1196, 0.5647, 0.1141], "centre": [0, 0.2776, 0]},
    "peak": {"size": [0.9693, 0.109, 0.5117], "centre": [0, -0.0545, 0.4641]},
    "prop": {"size": [1, 0.26, 0.03], "centre": [0, 0, 0]},
    "tri": {"size": [1, 0.9, 0.12], "centre": [0, 0.05, 0]},
    "grin": {"size": [1, 0.42, 0.12], "centre": [0, -0.03, 0]},
    "collar": {"size": [1.5996, 0.9179, 1.1689], "centre": [0, 0.4589, -0.2156]},
}

# The built-in primitives are all unit meshes centred on the origin.
for _name in ("box", "rbox", "cyl", "sph", "cone", "wedge", "torus"):
    SHAPES.setdefault(_name, {"size": [1, 1, 1], "centre": [0, 0, 0]})


def rotate(v: Vec, r: Optional[Vec]) -> List[float]:
    """Turn ``v`` by the euler ``r`` exactly as the renderer does (Ry*Rx*Rz)."""
    if not r:
        return [float(v[0]), float(v[1]), float(v[2])]
    rx, ry, rz = float(r[0]), float(r[1]), float(r[2])
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    m00 = cy * cz + sy * sx * sz
    m01 = cx * sz
    m02 = -sy * cz + cy * sx * sz
    m10 = -cy * sz + sy * sx * cz
    m11 = cx * cz
    m12 = sy * sz + cy * sx * cz
    m20 = sy * cx
    m21 = -sx
    m22 = cy * cx
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    return [m00 * x + m10 * y + m20 * z,
            m01 * x + m11 * y + m21 * z,
            m02 * x + m12 * y + m22 * z]


def _r(values: Sequence[float], digits: int = 4) -> List[float]:
    return [round(float(v), digits) for v in values]


def part(t: str, p: Vec, s: Vec, c: str, r: Optional[Vec] = None,
         **extra: Any) -> Dict[str, Any]:
    """A plain part dict, rounded, with only the keys that mean something."""
    out: Dict[str, Any] = {"t": t, "p": _r(p), "s": _r(s), "c": c}
    if r and any(abs(float(a)) > 1e-9 for a in r):
        out["r"] = _r(r)
    for key, value in extra.items():
        if value is None or value is False:
            continue
        out[key] = value
    return out


def place(t: str, at: Vec, scale: Any, c: str, anchor: Optional[Vec] = None,
          r: Optional[Vec] = None, **extra: Any) -> Dict[str, Any]:
    """Draw mesh ``t`` so that ``anchor`` -- a point in the mesh's own
    modelling space -- lands at ``at`` in item space.

    ``scale`` multiplies the mesh's native size: one number keeps the
    proportions it was modelled at, three stretch it per axis.  ``anchor``
    defaults to the mesh's centre, which makes this a plain placement.
    """
    info = SHAPES.get(t, SHAPES["box"])
    if isinstance(scale, (int, float)):
        k = [float(scale)] * 3
    else:
        k = [float(scale[0]), float(scale[1]), float(scale[2])]
    size = [info["size"][i] * k[i] for i in range(3)]
    if anchor is None:
        offset = [0.0, 0.0, 0.0]
    else:
        offset = [(info["centre"][i] - float(anchor[i])) * k[i] for i in range(3)]
    turned = rotate(offset, r)
    centre = [float(at[i]) + turned[i] for i in range(3)]
    return part(t, centre, size, c, r, **extra)


def mirror_x(parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The same parts reflected across the X axis (left <-> right).

    A rotation cannot reflect a mesh, so this mirrors positions and turns
    each part's yaw and roll the other way -- which is exact for every shape
    that is symmetric front to back in its own space (all of them here)."""
    out = []
    for piece in parts:
        copy = dict(piece)
        copy["p"] = [-piece["p"][0], piece["p"][1], piece["p"][2]]
        if piece.get("r"):
            rx, ry, rz = piece["r"]
            copy["r"] = [rx, -ry, -rz]
        out.append(copy)
    return out


def ring_of(count: int, radius: float, y: float, make, start: float = 0.0,
            arc: float = math.tau) -> List[Dict[str, Any]]:
    """``make(angle, x, z)`` called round a circle, for studs, gems, points."""
    out = []
    for k in range(count):
        a = start + arc * (k / count if arc >= math.tau - 1e-6 else
                           (k / max(1, count - 1)))
        out.append(make(a, math.sin(a) * radius, math.cos(a) * radius))
    return out
