"""The modelled cosmetics: every hat, the crate-era back items, the crates
and keys themselves, and the Halloween set.

Each item is built from the sculpted meshes in ``static/js/engine/shapes.js``
(domes, bills, brims, horns, pumpkins, bevelled medals...) plus the core
primitives, placed with :mod:`app.models.modeling` so a part can be put
where it belongs on the shape -- a horn's root on the skull, a bill's inner
edge on the crown -- rather than by guessing at bounding boxes.

Coordinates follow the catalogue's conventions (see catalog.py): a hat's
origin is the TOP CENTRE OF THE HEAD, +Y up, +Z the face.  Both heads are a
rounded box (male 1.46 x 1.28 x 1.40, female 1.34 x 1.27 x 1.34) hanging
below that origin, so a band that has to go *round* the head is a rounded
box a little larger than the bigger one, and a crown that sits *on* it can be
round.  Keep everything at the front above y -0.30: the eyes are printed at
about -0.44.

Everything here is plain data by the time the module has imported; the
browser never sees the helpers, only the part lists they produce.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from .modeling import part, place, rotate

PI = math.pi
TAU = math.tau

# A few shared finishes.
GOLD = "#f2c230"
GOLD_DARK = "#b8860b"
SILVER = "#c9ced6"
IRON = "#3a3d42"
BRASS = "#c9a227"
BONE = "#ece4d0"
NEON_GREEN = "#6bff9a"


def _hat(item_id: str, name: str, price: int, parts: List[Dict[str, Any]],
         desc: str, rarity: str = "common", order: int = 0,
         **extra: Any) -> Dict[str, Any]:
    item = {"id": item_id, "name": name, "slot": "hat", "price": price,
            "rarity": rarity, "description": desc, "sort_order": order,
            "data": {"parts": parts}}
    item.update(extra)
    return item


def _around(count: int, radius: float, y: float, fn, start: float = 0.0):
    """``fn(angle, x, z)`` at ``count`` points round a circle (angle 0 = the
    front, +Z, turning towards +X)."""
    out = []
    for k in range(count):
        a = start + TAU * k / count
        got = fn(a, math.sin(a) * radius, math.cos(a) * radius)
        if isinstance(got, list):
            out.extend(got)
        elif got:
            out.append(got)
    return out


def _horn_point(t: float, at, scale: float, r) -> List[float]:
    """A point along the 'horn' mesh's centreline (t 0..1), in item space,
    for a horn placed with its root at ``at``."""
    a = t * PI * 0.42
    local = [(0.5 - math.cos(a) * 0.5) * scale, math.sin(a) * 0.6 * scale, 0.0]
    turned = rotate(local, r)
    return [at[0] + turned[0], at[1] + turned[1], at[2] + turned[2]]


def _visor(radius: float, y: float, c: str, drop: float = 1.0, t: str = "visor",
           **kw) -> Dict[str, Any]:
    """A bill whose inner edge sits on a crown of ``radius`` at height ``y``."""
    k = radius * 2.0
    return place(t, [0, y, 0], [k, k * drop, k], c, anchor=[0, 0, 0], **kw)


# =================================================================== HATS
def _red_cap():
    R = 0.82
    parts = [
        place("capcrown", [0, -0.27, 0], [2 * R, 1.55, 2 * R], "#c4281c",
              anchor=[0, 0, 0], decal="panels", wrap=True),
        _visor(R, -0.17, "#9e1f15", drop=1.15),
        # the underside of the bill, the grey every real cap has
        _visor(R - 0.01, -0.20, "#5d6670", drop=1.05),
        part("sph", [0, 0.535, 0], [0.2, 0.12, 0.2], "#8c1c15"),
        # the patch on the front, leaning back with the crown
        part("disc", [0, 0.05, 0.775], [0.5, 0.5, 0.07], "#f2f3f3",
             [-0.30, 0, 0], decal="letter_R"),
        # the strap and its buckle across the gap at the back
        place("arch", [0, -0.26, -0.80], [0.32, 0.30, 0.6], "#7a120c",
              anchor=[0, 0, 0]),
        part("rbox", [0, -0.19, -0.83], [0.16, 0.08, 0.04], SILVER, mat="metal"),
    ]
    # air holes, one on each panel near the top
    parts += _around(6, 0.47, 0.42, lambda a, x, z: part(
        "sph", [x, 0.40, z], [0.07, 0.07, 0.07], "#6e120c"), start=PI / 6)
    return parts


def _top_hat():
    return [
        place("brim", [0, -0.05, 0], [2.12, 1.7, 2.02], "#16171b", anchor=[0, 0, 0]),
        place("flare", [0, 0.0, 0], [1.36, 1.46, 1.30], "#1b1d23", anchor=[0, 0, 0]),
        # silk band and a bow on the left
        part("cyl", [0, 0.17, 0], [1.25, 0.26, 1.19], "#7a1414"),
        part("rbox", [0.63, 0.17, 0.0], [0.07, 0.17, 0.11], "#5e0e0e"),
        part("sph", [0.63, 0.18, 0.15], [0.07, 0.17, 0.2], "#7a1414", [0, 0, 0.2]),
        part("sph", [0.63, 0.18, -0.15], [0.07, 0.17, 0.2], "#7a1414", [0, 0, -0.2]),
        # the ace tucked into the band
        part("box", [-0.34, 0.36, 0.50], [0.24, 0.32, 0.02], "#fbfaf5",
             [0, -0.58, 0.14], decal="card_ace"),
    ]


def _hard_hat():
    parts = [
        place("hemi", [0, -0.22, 0], [1.70, 1.92, 1.78], "#f2b01e", anchor=[0, 0, 0]),
        # the ridge over the top: an arch just inside the shell, so only its
        # crest stands proud along the crown
        place("arch", [0, -0.24, 0], [1.56, 1.94, 1.0], "#dc9c10", anchor=[0, 0, 0],
              r=[0, PI / 2, 0]),
        part("rbox", [0, 0.70, 0], [0.16, 0.08, 0.70], "#dc9c10"),
        # the rolled lip round the rim and the short peak at the front
        place("ring", [0, -0.27, 0], [1.86, 0.5, 1.94], "#e8a414", anchor=[0, 0, 0]),
        _visor(0.88, -0.20, "#e8a414", drop=1.0, t="peak"),
        # reflective band
        place("ring", [0, 0.0, 0], [1.66, 0.55, 1.74], "#e9eef3", anchor=[0, 0, 0],
              mat="metal"),
        # the head lamp
        part("rbox", [0, 0.20, 0.80], [0.26, 0.20, 0.12], "#2a2d31", [-0.35, 0, 0]),
        part("cyl", [0, 0.22, 0.88], [0.24, 0.16, 0.24], "#3a3d42", [PI / 2 - 0.35, 0, 0],
             mat="metal"),
        part("disc", [0, 0.25, 0.95], [0.19, 0.19, 0.04], "#fff4c0", [-0.35, 0, 0],
             mat="neon"),
        # a site sticker on each side
        part("disc", [0.80, 0.18, 0.0], [0.30, 0.30, 0.03], "#f2b01e", [0, PI / 2, 0.0],
             decal="hazard"),
        part("disc", [-0.80, 0.18, 0.0], [0.30, 0.30, 0.03], "#f2b01e", [0, -PI / 2, 0.0],
             decal="hazard"),
    ]
    return parts


def _beanie():
    return [
        place("hemi", [0, -0.30, 0], [1.62, 2.0, 1.62], "#2f5fa8", anchor=[0, 0, 0],
              decal="knit", wrap=True),
        place("cask", [0, -0.36, 0], [1.74, 0.38, 1.74], "#e8e8e8", anchor=[0, 0, 0],
              decal="knit", wrap=True),
        part("sph", [0, 0.76, 0], [0.48, 0.44, 0.48], "#f2f3f3", decal="fur", wrap=True),
        part("rbox", [0.40, -0.17, 0.77], [0.24, 0.13, 0.04], "#c4281c", [0, 0.48, 0]),
    ]


def _crown():
    parts = [
        place("hemi", [0, -0.02, 0], [1.30, 1.30, 1.30], "#8b1a1a", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        place("ring", [0, -0.08, 0], [1.58, 1.9, 1.58], GOLD, anchor=[0, 0, 0],
              mat="metal"),
        part("torus", [0, -0.07, 0], [1.66, 0.09, 1.66], GOLD_DARK, mat="metal"),
        part("torus", [0, 0.30, 0], [1.64, 0.08, 1.64], GOLD_DARK, mat="metal"),
        # the orb and cross
        part("sph", [0, 0.71, 0], [0.22, 0.22, 0.22], GOLD, mat="metal"),
        part("box", [0, 0.92, 0], [0.06, 0.26, 0.06], GOLD, mat="metal"),
        part("box", [0, 0.94, 0], [0.18, 0.06, 0.06], GOLD, mat="metal"),
        part("torus", [0, 0.62, 0], [0.36, 0.05, 0.36], GOLD_DARK, mat="metal"),
        # the great ruby at the front
        place("gem", [0, 0.11, 0.80], [0.30, 0.30, 0.30], "#d01c2a", anchor=[0, 0.36, 0],
              r=[PI / 2, 0, 0], mat="glass"),
    ]

    def point(a, x, z):
        tall = (round(a / (TAU / 8)) % 2) == 0
        h = 0.56 if tall else 0.38
        out = [place("leaf", [x * 0.96, 0.28, z * 0.96], [0.9, h, 1.6], GOLD,
                     anchor=[0, -0.5, 0], r=[-0.10, a, 0], mat="metal")]
        if tall:
            top = rotate([0, h, 0], [-0.10, a, 0])
            out.append(part("sph", [x * 0.96 + top[0], 0.28 + top[1] + 0.05,
                                    z * 0.96 + top[2]], [0.13, 0.13, 0.13],
                            "#fdf7ea", mat="metal"))
        return out
    parts += _around(8, 0.76, 0.28, point)
    colours = ["#2d6be0", "#1fa35b", "#d01c2a", "#9b3fd6"]
    parts += _around(8, 0.80, 0.11, lambda a, x, z: None if abs(a) < 0.1 else place(
        "gem", [x, 0.11, z], [0.15, 0.15, 0.15], colours[int(round(a / (TAU / 8))) % 4],
        anchor=[0, 0.36, 0], r=[PI / 2, a, 0], mat="glass"))
    return parts


def _cowboy():
    return [
        place("cowbrim", [0, -0.04, 0], [2.52, 2.1, 2.52], "#8a5a2b", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        place("cask", [0, -0.02, 0], [1.34, 0.86, 1.26], "#9c6733", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        place("hemi", [0, 0.80, 0], [1.14, 0.42, 1.06], "#9c6733", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        # the cattleman's crease down the crown and the pinch either side of
        # the front, pressed in rather than stuck on
        part("rbox", [0, 0.98, -0.08], [0.14, 0.07, 0.80], "#6f4a22", [0.12, 0, 0]),
        part("sph", [0.30, 0.86, 0.38], [0.22, 0.20, 0.30], "#7d5228", [0.3, 0.6, -0.3]),
        part("sph", [-0.30, 0.86, 0.38], [0.22, 0.20, 0.30], "#7d5228", [0.3, -0.6, 0.3]),
        # leather band, a silver concho with turquoise
        part("cyl", [0, 0.12, 0], [1.38, 0.18, 1.31], "#3b2312", decal="leather", wrap=True),
        part("disc", [0, 0.12, 0.665], [0.20, 0.20, 0.05], SILVER, mat="metal"),
        part("sph", [0, 0.12, 0.69], [0.09, 0.09, 0.05], "#2fb3a8"),
        # a feather in the band
        place("feather", [0.62, 0.32, -0.18], 0.75, "#e0cba6", r=[0, PI / 2, -0.55]),
        place("feather", [0.63, 0.30, -0.10], 0.55, "#8a6a4a", r=[0, PI / 2, -0.35]),
    ]


def _pot():
    return [
        place("cask", [0, -0.32, 0], [1.64, 0.95, 1.64], "#9a9da2", anchor=[0, 0, 0],
              mat="metal", decal="rivets", wrap=True),
        place("ring", [0, -0.34, 0], [1.76, 0.55, 1.76], "#7f8287", anchor=[0, 0, 0],
              mat="metal"),
        part("cyl", [0, 0.63, 0], [1.34, 0.04, 1.34], "#3d3f43", mat="metal"),
        # the long handle and its hanging loop
        place("capsule", [0.70, -0.12, 0], [0.16, 0.32, 0.12], "#26282c",
              anchor=[0, 0, 0], r=[0, 0, -PI / 2]),
        part("torus", [1.70, -0.12, 0], [0.24, 0.06, 0.24], "#26282c", [PI / 2, 0, 0]),
        # a dent, and a scorch mark from the last time it was on the stove
        part("sph", [0.45, 0.18, 0.60], [0.30, 0.22, 0.08], "#878a8f", [0, 0.6, 0],
             mat="metal"),
    ]


def _horns():
    parts = [
        # a blackened circlet round the brow, with an ember set in the front
        part("rbox", [0, -0.24, 0], [1.54, 0.12, 1.48], "#2a0b0b", decal="leather", wrap=True),
        part("rbox", [0, -0.19, 0], [1.56, 0.03, 1.50], "#7a2a12", mat="metal"),
        place("gem", [0, -0.24, 0.76], [0.22, 0.22, 0.22], "#ff6a1a", anchor=[0, 0.36, 0],
              r=[PI / 2, 0, 0], mat="neon"),
    ]
    for side in (1, -1):
        at = [0.42 * side, -0.10, 0.12]
        r = [0.0, 0.0 if side > 0 else PI, -0.30]
        # the root, cracked open and glowing where it breaks the skin
        parts.append(part("sph", [0.42 * side, -0.02, 0.12], [0.40, 0.22, 0.40], "#3a0f0f"))
        parts.append(place("horn", at, 2.0, "#6e1a12", anchor=[0, 0, 0], r=r))
        for t, w in ((0.20, 0.44), (0.38, 0.35), (0.56, 0.26), (0.72, 0.18)):
            p = _horn_point(t, at, 2.0, r)
            parts.append(part("torus", p, [w, 0.07, w], "#4a0f0b",
                              [0, r[1], r[2] + 0.55 * side]))
        parts.append(place("flame", [0.42 * side, 0.05, 0.36], 0.26, "#ff7a1a", mat="neon"))
        parts.append(place("flame", [0.56 * side, 0.02, 0.22], 0.18, "#ffb02e",
                           r=[0, 0.5 * side, 0], mat="neon"))
    return parts


def _propeller():
    return [
        place("hemi", [0, -0.28, 0], [1.60, 1.84, 1.60], "#c4281c", anchor=[0, 0, 0],
              decal="panels", wrap=True),
        _visor(0.80, -0.20, "#0d69ac", drop=0.9, t="peak"),
        part("cyl", [0, 0.68, 0], [0.08, 0.26, 0.08], "#f2f3f3"),
        part("cone", [0, 0.83, 0], [0.18, 0.12, 0.18], "#f5cd30", mat="metal"),
        place("prop", [0, 0.79, 0], [2.0, 2.0, 2.0], "#0d69ac", r=[PI / 2, 0, 0], spin=8.0),
        place("prop", [0, 0.775, 0], [1.9, 1.9, 1.9], "#f5cd30", r=[PI / 2, PI / 2, 0],
              spin=8.0),
        part("sph", [0, 0.81, 0], [0.12, 0.10, 0.12], "#f2f3f3"),
    ]


def _neon_visor():
    parts = [
        part("rbox", [0, -0.30, 0], [1.56, 0.30, 1.50], "#1d2127"),
        # the glass, its frame and the light along the top
        part("rbox", [0, -0.44, 0.73], [1.42, 0.30, 0.08], "#19f0d8", alpha=0.72,
             mat="glass"),
        part("rbox", [0, -0.27, 0.74], [1.48, 0.06, 0.10], "#2a2f36"),
        part("rbox", [0, -0.61, 0.74], [1.48, 0.06, 0.10], "#2a2f36"),
        part("rbox", [0, -0.27, 0.79], [1.10, 0.03, 0.03], "#19f0d8", mat="neon"),
        # side pods, one with an antenna
        part("cyl", [0.80, -0.42, 0.18], [0.34, 0.14, 0.34], "#2a2f36", [0, 0, PI / 2],
             mat="metal"),
        part("cyl", [-0.80, -0.42, 0.18], [0.34, 0.14, 0.34], "#2a2f36", [0, 0, PI / 2],
             mat="metal"),
        part("torus", [0.88, -0.42, 0.18], [0.24, 0.06, 0.24], "#19f0d8", [0, 0, PI / 2],
             mat="neon"),
        part("torus", [-0.88, -0.42, 0.18], [0.24, 0.06, 0.24], "#19f0d8", [0, 0, PI / 2],
             mat="neon"),
        part("cyl", [0.86, -0.06, 0.18], [0.03, 0.5, 0.03], "#8a9099", mat="metal"),
        part("sph", [0.86, 0.20, 0.18], [0.07, 0.07, 0.07], "#ff3b5c", mat="neon"),
    ]
    parts += [part("sph", [x, -0.27, 0.80], [0.04, 0.04, 0.03], "#ff3bd0", mat="neon")
              for x in (-0.56, -0.45, 0.45, 0.56)]
    return parts


def _bucket():
    return [
        place("bell", [0, -0.30, 0], [2.26, 0.66, 2.26], "#6d8c55", anchor=[0, 0, 0],
              decal="canvas", wrap=True),
        place("cask", [0, -0.14, 0], [1.50, 0.80, 1.50], "#5e7c4a", anchor=[0, 0, 0],
              decal="canvas", wrap=True),
        part("cyl", [0, -0.05, 0], [1.55, 0.13, 1.55], "#41583a"),
        # stitched rings on the brim
        part("torus", [0, -0.21, 0], [1.94, 0.025, 1.94], "#4b6440"),
        part("torus", [0, -0.25, 0], [2.10, 0.025, 2.10], "#4b6440"),
        # a fishing fly hooked through the band
        part("sph", [0.56, -0.02, 0.48], [0.09, 0.09, 0.14], "#c4281c"),
        place("feather", [0.60, 0.04, 0.42], 0.22, "#f5cd30", r=[0, 0.8, 0.6]),
        place("feather", [0.54, 0.04, 0.50], 0.20, "#2fa84f", r=[0, 0.8, -0.4]),
        place("hook", [0.62, -0.10, 0.52], 0.16, SILVER, anchor=[0, 0, 0], r=[PI, 0.8, 0],
              mat="metal"),
        # air holes either side
        part("torus", [0.74, 0.30, 0.0], [0.10, 0.03, 0.10], SILVER, [0, 0, PI / 2],
             mat="metal"),
        part("torus", [-0.74, 0.30, 0.0], [0.10, 0.03, 0.10], SILVER, [0, 0, PI / 2],
             mat="metal"),
    ]


def _headphones():
    parts = [
        place("arch", [0, -0.48, 0], [1.66, 1.14, 1.6], "#2f3640", anchor=[0, 0, 0]),
        part("rbox", [0, 0.11, 0], [0.62, 0.08, 0.20], "#4a525e"),
    ]
    for side in (1, -1):
        parts += [
            part("rbox", [0.84 * side, -0.38, 0], [0.08, 0.30, 0.10], SILVER, mat="metal"),
            part("cask", [0.86 * side, -0.66, 0.02], [0.84, 0.30, 0.84], "#1b1f26",
                 [0, 0, PI / 2]),
            part("torus", [0.73 * side, -0.66, 0.02], [0.74, 0.14, 0.74], "#3a3f48",
                 [0, 0, PI / 2]),
            part("torus", [1.01 * side, -0.66, 0.02], [0.66, 0.08, 0.66], "#c4281c",
                 [0, 0, PI / 2], mat="metal"),
            part("disc", [1.02 * side, -0.66, 0.02], [0.44, 0.44, 0.05], "#2a2f36",
                 [0, PI / 2 * side, 0], decal="logo_block"),
        ]
    parts += [
        place("capsule", [0.92, -0.98, 0.05], [0.05, 0.20, 0.05], "#15171a",
              anchor=[0, 3.0, 0], r=[0.2, 0, -0.15]),
        part("rbox", [0.98, -1.60, 0.18], [0.07, 0.16, 0.07], SILVER, [0.2, 0, -0.15],
             mat="metal"),
    ]
    return parts


def _antlers():
    parts = [
        part("rbox", [0, -0.26, 0], [1.54, 0.13, 1.48], "#5a3d22", decal="leather", wrap=True),
    ]
    beam = "#8b6a45"
    tip = "#e9dcc4"
    for side in (1, -1):
        at = [0.40 * side, -0.06, -0.02]
        r = [-0.25, 0.0 if side > 0 else PI, -0.05]
        parts.append(place("horn", at, 2.3, beam, anchor=[0, 0, 0], r=r))
        # the burr where the antler meets the skull, and a strap down to the band
        parts.append(part("torus", [0.40 * side, 0.0, -0.02], [0.36, 0.10, 0.36], "#6e5232"))
        parts.append(part("rbox", [0.58 * side, -0.14, -0.02], [0.08, 0.26, 0.16], "#5a3d22",
                          [0, 0, 0.5 * side]))
        # three tines off the beam, each turned up and a little forward
        for t, size, lean in ((0.30, 1.0, 0.25), (0.55, 0.85, 0.10), (0.80, 0.62, -0.05)):
            base = _horn_point(t, at, 2.3, r)
            rr = [0.55 + lean, (0.2 if side > 0 else PI - 0.2), 0.55]
            parts.append(place("horn", base, size, beam, anchor=[0, 0, 0], r=rr))
            tipp = _horn_point(1.0, base, size, rr)
            parts.append(part("sph", tipp, [0.05, 0.05, 0.05], tip))
        end = _horn_point(1.0, at, 2.3, r)
        parts.append(part("sph", end, [0.06, 0.06, 0.06], tip))
        # moss and a sprig of leaves at the root
        parts.append(place("leaf", [0.52 * side, -0.22, 0.62], 0.34, "#3f8a3a",
                           r=[-0.3, 0.4 * side, 0.6 * side]))
        parts.append(place("leaf", [0.64 * side, -0.24, 0.50], 0.28, "#5aa84a",
                           r=[-0.3, 0.9 * side, 1.2 * side]))
        parts.append(part("sph", [0.58 * side, -0.20, 0.64], [0.07, 0.07, 0.07], "#c4281c"))
    # a little toadstool growing out of the band
    parts += [part("cyl", [-0.24, -0.14, 0.76], [0.06, 0.14, 0.06], "#f2ead8"),
              place("hemi", [-0.24, -0.08, 0.76], [0.22, 0.26, 0.22], "#d8312a",
                    anchor=[0, 0, 0]),
              part("sph", [-0.20, -0.01, 0.81], [0.04, 0.03, 0.04], "#ffffff")]
    return parts


def _halo():
    parts = [
        part("torus", [0, 0.95, 0], [1.52, 0.16, 1.52], "#fff2a8", mat="neon"),
        part("torus", [0, 0.95, 0], [1.20, 0.05, 1.20], "#fffbe0", mat="neon"),
        part("cyl", [0, 0.95, 0], [1.40, 0.02, 1.40], "#fff6c4", alpha=0.25, mat="neon"),
        # a second ring that precesses round the first
        part("torus", [0, 0.95, 0], [1.80, 0.04, 1.80], "#ffe27a", [0.42, 0, 0],
             mat="neon", spin=1.4),
    ]
    parts += _around(6, 0.76, 0.95, lambda a, x, z: place(
        "star", [x, 0.95, z], 0.16, "#ffffff", r=[0, a, 0], mat="neon"))
    return parts


def _bandana():
    # The cloth is a low dome wide enough to clear the corners of either head
    # (a rounded box pokes through anything narrower), tied off with a band
    # round the brow and a knot at the back.
    return [
        place("hemi", [0, -0.25, 0], [1.84, 0.82, 1.78], "#b83a3a", anchor=[0, 0, 0],
              decal="paisley", wrap=True),
        part("rbox", [0, -0.30, 0], [1.56, 0.17, 1.50], "#a32f2f", decal="paisley",
             wrap=True),
        part("sph", [0, -0.28, -0.80], [0.30, 0.22, 0.20], "#a32f2f", decal="paisley",
             wrap=True),
        place("ribbon", [0.10, -0.32, -0.84], [0.26, 0.56, 0.06], "#b83a3a",
              anchor=[0, 0.5, 0], r=[-0.30, 0, 0.30], decal="paisley", wrap=True),
        place("ribbon", [-0.10, -0.32, -0.84], [0.24, 0.48, 0.06], "#a32f2f",
              anchor=[0, 0.5, 0], r=[-0.25, 0, -0.35], decal="paisley", wrap=True),
    ]


def _pirate():
    return [
        place("tricorn", [0, -0.04, 0], [2.40, 1.7, 2.40], "#2b2118", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        place("hemi", [0, -0.06, 0], [1.38, 1.36, 1.32], "#3a2c20", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        # skull and crossbones on the crown
        place("bone", [0, 0.24, 0.62], 0.62, BONE, r=[-0.3, 0, 0.62]),
        place("bone", [0, 0.24, 0.62], 0.62, BONE, r=[-0.3, 0, -0.62]),
        part("disc", [0, 0.27, 0.665], [0.34, 0.34, 0.05], "#f2f3f3", [-0.3, 0, 0],
             decal="skull"),
        # gold cockade and a red plume over it
        part("disc", [-0.56, 0.42, 0.22], [0.24, 0.24, 0.05], GOLD, [0, -1.2, 0],
             mat="metal"),
        place("feather", [-0.62, 0.42, 0.10], 1.15, "#c94f4f", anchor=[0, -0.5, 0],
              r=[-0.6, -1.0, 0.55]),
        place("feather", [-0.58, 0.42, 0.06], 0.9, "#f2f3f3", anchor=[0, -0.5, 0],
              r=[-0.5, -1.2, 0.35]),
    ]


def _spikes():
    colours = ["#19c8d8", "#2fb0e0", "#5a8ef0", "#8a6cf0", "#b04fe8", "#d43cd0", "#f02aa8"]
    parts = [
        # the shaved strip the spikes grow from, and a studded band round the brow
        part("rbox", [0, 0.01, -0.02], [0.40, 0.08, 1.36], "#1b1b1b"),
        part("rbox", [0, -0.28, 0], [1.56, 0.16, 1.50], "#1b1b1b", decal="leather", wrap=True),
    ]
    for k, c in enumerate(colours):
        z = 0.60 - k * 0.20
        h = 0.62 + 0.48 * math.sin(PI * (k + 0.5) / len(colours))
        parts.append(place("cone", [0, 0.03, z], [0.30, h, 0.30], c, anchor=[0, -0.5, 0],
                           r=[0.30 - k * 0.07, 0, 0]))
    for side in (1, -1):
        parts += [place("cone", [0.77 * side, -0.28, z], [0.08, 0.12, 0.08], SILVER,
                        anchor=[0, -0.5, 0], r=[0, 0, -PI / 2 * side], mat="metal")
                  for z in (-0.5, -0.25, 0.0, 0.25, 0.5)]
    parts += [place("cone", [x, -0.28, 0.75], [0.08, 0.12, 0.08], SILVER,
                    anchor=[0, -0.5, 0], r=[PI / 2, 0, 0], mat="metal")
              for x in (-0.5, -0.25, 0.25, 0.5)]
    return parts


def _teacup():
    parts = [
        place("brim", [0, -0.02, 0], [1.56, 0.95, 1.56], "#f4f1ea", anchor=[0, 0, 0]),
        part("torus", [0, 0.09, 0], [1.56, 0.04, 1.56], GOLD, mat="metal"),
        place("bowl", [0, 0.06, 0], [1.08, 1.28, 1.08], "#f4f1ea", anchor=[0, 0, 0],
              decal="rosebuds", wrap=True),
        part("cyl", [0, 0.58, 0], [0.92, 0.02, 0.92], "#8a4a1a"),
        part("torus", [0, 0.81, 0], [1.08, 0.03, 1.08], GOLD, mat="metal"),
        place("arch", [0.53, 0.42, 0], [0.42, 0.40, 0.9], "#f4f1ea", anchor=[0, 0, 0],
              r=[0, 0, -PI / 2]),
        # a sugar cube and a teaspoon on the saucer
        part("rbox", [-0.58, 0.12, 0.30], [0.14, 0.14, 0.14], "#ffffff", [0, 0.4, 0]),
        place("capsule", [0.18, 0.11, 0.55], [0.05, 0.14, 0.04], SILVER, anchor=[0, 0, 0],
              r=[PI / 2, 0.9, 0], mat="metal"),
        part("sph", [0.50, 0.11, 0.78], [0.14, 0.05, 0.20], SILVER, [0, 0.9, 0], mat="metal"),
    ]
    # steam curling off the tea
    parts += [place("teardrop", [x, y, z], [0.12, 0.32, 0.12], "#ffffff",
                    anchor=[0, 0, 0], r=[0, 0, lean], alpha=0.35)
              for x, y, z, lean in ((0.10, 0.95, 0.0, 0.2), (-0.12, 1.08, 0.06, -0.25),
                                    (0.02, 1.25, -0.08, 0.1))]
    return parts


def _party():
    parts = [
        part("cone", [0, 0.78, 0], [1.46, 1.62, 1.46], "#c4281c", decal="party", wrap=True),
        part("torus", [0, -0.02, 0], [1.54, 0.16, 1.54], "#f2f3f3"),
        part("sph", [0, 1.64, 0], [0.42, 0.42, 0.42], "#f5c518", decal="fur", wrap=True),
        # curly streamers off the pom
        place("hook", [0.06, 1.58, 0.06], 0.55, "#3c6fd6", anchor=[0, 0, 0],
              r=[PI, 0.6, 0.2]),
        place("hook", [-0.06, 1.58, -0.04], 0.5, "#2fa84f", anchor=[0, 0, 0],
              r=[PI, 2.6, -0.2]),
        place("hook", [0.0, 1.58, -0.08], 0.45, "#f5c518", anchor=[0, 0, 0],
              r=[PI, -1.6, 0.1]),
    ]
    # a frill of little tassels round the rim
    parts += _around(12, 0.78, -0.06, lambda a, x, z: place(
        "teardrop", [x, -0.04, z], [0.12, 0.16, 0.12],
        ["#f5c518", "#3c6fd6", "#2fa84f"][int(round(a / (TAU / 12))) % 3],
        anchor=[0, 1.0, 0], r=[PI, 0, 0]))
    return parts


def _fur_cap():
    fur = "#7a6248"
    return [
        place("capcrown", [0, -0.27, 0], [1.66, 1.42, 1.62], "#3b3f46", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        # the turned-up front, the flaps tied up over the crown, all in fur
        part("rbox", [0, 0.02, 0.78], [1.58, 0.46, 0.26], fur, [-0.28, 0, 0],
             decal="fur", wrap=True),
        place("star", [0, 0.05, 0.93], 0.30, GOLD, r=[-0.28, 0, 0], mat="metal"),
        part("disc", [0, 0.05, 0.91], [0.38, 0.38, 0.04], "#c4281c", [-0.28, 0, 0]),
        place("shield", [0.84, 0.0, -0.04], [0.30, 0.64, 1.9], fur, r=[0, PI / 2, -0.32],
              decal="fur", wrap=True),
        place("shield", [-0.84, 0.0, -0.04], [0.30, 0.64, 1.9], fur, r=[0, -PI / 2, 0.32],
              decal="fur", wrap=True),
        part("rbox", [0, -0.24, -0.70], [1.40, 0.30, 0.22], fur, [0.25, 0, 0],
             decal="fur", wrap=True),
        # the tie that holds the flaps up, knotted on top
        place("arch", [0, 0.30, -0.04], [1.60, 0.62, 0.18], "#1e1e1e", anchor=[0, 0, 0]),
        part("sph", [0, 0.64, -0.04], [0.09, 0.07, 0.09], "#1e1e1e"),
    ]


def _snow_cap():
    parts = [
        place("hemi", [0, -0.30, 0], [1.60, 1.92, 1.60], "#2f6fd6", anchor=[0, 0, 0],
              decal="snowflakes", wrap=True),
        place("cask", [0, -0.36, 0], [1.72, 0.32, 1.72], "#f2f3f3", anchor=[0, 0, 0],
              decal="knit", wrap=True),
        part("sph", [0, 0.72, 0], [0.50, 0.46, 0.50], "#f2f3f3", decal="fur", wrap=True),
    ]
    for side in (1, -1):
        parts += [
            place("shield", [0.80 * side, -0.58, 0.0], [0.62, 0.60, 1.3], "#2f6fd6",
                  r=[0, PI / 2 * side, 0], decal="knit", wrap=True),
            place("capsule", [0.80 * side, -0.88, 0.0], [0.09, 0.17, 0.09], "#f2f3f3",
                  anchor=[0, 3.0, 0], decal="knit", wrap=True),
            part("sph", [0.80 * side, -1.42, 0.0], [0.17, 0.17, 0.17], "#f2f3f3",
                 decal="fur", wrap=True),
        ]
    return parts


def _candy_cap():
    return [
        place("hemi", [0, -0.30, 0], [1.60, 1.96, 1.60], "#c4281c", anchor=[0, 0, 0],
              decal="candy", wrap=True),
        place("cask", [0, -0.36, 0], [1.72, 0.32, 1.72], "#2fa84f", anchor=[0, 0, 0],
              decal="knit", wrap=True),
        place("hook", [0.12, 0.55, 0.0], 0.95, "#c4281c", anchor=[0, 0, 0],
              r=[0, 0.3, 0], decal="candy", wrap=True),
        place("leaf", [-0.58, -0.10, 0.58], 0.36, "#1e7a36", r=[-0.4, -0.7, 0.9]),
        place("leaf", [-0.68, -0.08, 0.44], 0.34, "#2a9446", r=[-0.4, -1.0, -0.4]),
        place("leaf", [-0.50, -0.04, 0.66], 0.30, "#1e7a36", r=[-0.4, -0.5, -1.4]),
        part("sph", [-0.60, -0.08, 0.62], [0.10, 0.10, 0.10], "#d0141c"),
        part("sph", [-0.66, -0.12, 0.56], [0.09, 0.09, 0.09], "#e0242c"),
        part("sph", [-0.56, -0.15, 0.64], [0.08, 0.08, 0.08], "#b80f16"),
    ]


def _lantern():
    pumpkin_c = "#e2621b"
    glow = "#ffd23a"
    parts = [
        place("pumpkin", [0, -1.42, 0], [2.24, 2.62, 2.24], pumpkin_c, anchor=[0, 0.047, 0]),
        # the stem, curling, and a leaf off it
        place("hook", [0, 0.40, 0], 0.62, "#5a6b2a", anchor=[0, 0, 0], r=[0, 0.4, 0]),
        place("leaf", [0.26, 0.42, 0.10], 0.45, "#3f7a2a", r=[-1.2, 0.3, -0.5]),
        # the carving, lit from inside
        place("tri", [-0.34, -0.36, 1.02], [0.36, 0.34, 0.6], glow, r=[0.05, -0.26, 0],
              mat="neon"),
        place("tri", [0.34, -0.36, 1.02], [0.36, 0.34, 0.6], glow, r=[0.05, 0.26, 0],
              mat="neon"),
        place("tri", [0, -0.62, 1.07], [0.18, 0.16, 0.5], glow, r=[0.15, 0, PI],
              mat="neon"),
        place("grin", [0, -0.92, 0.96], [1.0, 0.95, 0.6], glow, r=[0.38, 0, 0], mat="neon"),
    ]
    return parts


def _astro():
    return [
        part("sph", [0, -0.55, 0], [2.06, 1.96, 2.02], "#bfe9ff", alpha=0.32, mat="glass"),
        place("ring", [0, -1.50, 0], [2.0, 1.3, 2.0], "#d8dde2", anchor=[0, 0, 0],
              mat="metal"),
        part("torus", [0, -1.24, 0], [2.0, 0.10, 2.0], "#9aa3ad", mat="metal"),
        # a glint across the glass
        part("rbox", [-0.40, 0.08, 0.80], [0.60, 0.07, 0.04], "#ffffff", [-0.7, -0.4, 0.5],
             alpha=0.55),
        part("rbox", [-0.62, -0.12, 0.74], [0.20, 0.05, 0.04], "#ffffff", [-0.6, -0.6, 0.5],
             alpha=0.45),
        # antenna and side lamps
        part("cyl", [0.42, 0.52, -0.22], [0.04, 0.42, 0.04], "#9aa3ad", [0.0, 0, -0.25],
             mat="metal"),
        part("sph", [0.48, 0.74, -0.22], [0.10, 0.10, 0.10], "#ff3b3b", mat="neon"),
        part("sph", [0.99, -0.60, 0.22], [0.12, 0.12, 0.12], "#f5c518", mat="neon"),
        part("sph", [-0.99, -0.60, 0.22], [0.12, 0.12, 0.12], "#f5c518", mat="neon"),
        part("disc", [0, -1.40, 0.99], [0.34, 0.34, 0.05], "#1b4f9c", decal="logo_block"),
    ]


def _traffic_cone():
    # The reflective band is not a ring slipped over the cone -- that is what
    # made it read as a floating doughnut.  It is a second cone sharing the
    # first one's apex, so its surface *is* the cone's surface, truncated at
    # the height the band starts.  A third cone, sharing the apex again, puts
    # the orange back on above the band.  Each shell has a hair more slope
    # than the one inside it (0.5192 -> 0.5294 -> 0.5382), which is what keeps
    # them strictly nested instead of z-fighting.
    return [
        part("cone", [0, 0.62, 0], [1.35, 1.3, 1.35], "#e2621b"),
        part("rbox", [0, 0.06, 0], [1.74, 0.14, 1.74], "#d2561a"),
        part("rbox", [0, -0.02, 0], [1.70, 0.04, 1.70], "#2a2a2a"),
        part("cone", [0, 0.845, 0], [0.9, 0.85, 0.9], "#f2f3f3"),
        part("cone", [0, 0.995, 0], [0.592, 0.55, 0.592], "#e2621b"),
        part("cyl", [0, 1.25, 0], [0.12, 0.06, 0.12], "#2a2a2a"),
    ]


HATS: List[Dict[str, Any]] = [
    _hat("hat_red_cap", "Classic Red Cap", 250, _red_cap(),
         "Six stitched panels, a bent bill and the R on the front. The cap every "
         "nooger owns.", "common", 1),
    _hat("hat_top_hat", "Silk Top Hat", 750, _top_hat(),
         "Black silk, a rolled brim, a red band -- and an ace tucked in it, for luck.",
         "uncommon", 2),
    _hat("hat_hard_hat", "Builder's Hard Hat", 300, _hard_hat(),
         "Ridged shell, reflective band and a head lamp. Officially issued by the "
         "Build Corps.", "common", 3),
    _hat("hat_beanie", "Winter Beanie", 180, _beanie(),
         "Knitted by somebody's grandmother, cuff and bobble included.", "common", 4),
    _hat("hat_crown", "Golden Crown", 1500, _crown(),
         "Eight points, eight pearls, a velvet cap and a ruby the size of a fist.",
         "rare", 5),
    _hat("hat_cowboy", "Ten Gallon Hat", 600, _cowboy(),
         "A cattleman's crease, a silver concho and a curled brim. Smells faintly of hay.",
         "uncommon", 6),
    _hat("hat_pot", "Cooking Pot", 120, _pot(),
         "Doubles as a helmet. Mostly. Somebody left the spoon in.", "common", 7),
    _hat("hat_horns", "Ruin Horns", 900, _horns(),
         "Recovered from the lava caves. The roots are still smouldering.", "rare", 8),
    _hat("hat_propeller", "Propeller Beanie", 450, _propeller(),
         "Four blades, one bill, zero lift. Socially essential.", "uncommon", 9),
    _hat("hat_visor", "Neon Visor", 350, _neon_visor(),
         "Cyberpunk on a budget: a lit glass visor, side pods and an antenna.",
         "uncommon", 10),
    _hat("hat_bucket", "Bucket Hat", 200, _bucket(),
         "Fisherman chic, with a fly still hooked through the band.", "common", 11),
    _hat("hat_headphones", "Retro Headphones", 500, _headphones(),
         "Padded cups, steel sliders and a cable to nowhere. Playing the lobby theme.",
         "uncommon", 12),
    _hat("hat_antlers", "Forest Antlers", 700, _antlers(),
         "Shed by something enormous in the northern woods. Moss not included -- it "
         "came anyway.", "rare", 13),
    _hat("hat_halo", "Ring of Light", 2000, _halo(),
         "A ring of light, a second one turning round it, and six stars. Awarded to "
         "those who never once used the report button.", "legendary", 14),
    _hat("hat_bandana", "Faded Bandana", 150, _bandana(),
         "Paisley, knotted at the back, tails flying. Worn by the veterans of the old "
         "server.", "common", 15),
    _hat("hat_pirate", "Pirate Tricorn", 800, _pirate(),
         "Three corners, a skull and crossbones and a plume. Captain of a ship that "
         "sank in 2007.", "rare", 16),
    _hat("hat_spikes", "Mohawk Spikes", 650, _spikes(),
         "Seven spikes in seven colours on a studded band. Ninety percent hair gel by "
         "volume.", "uncommon", 17),
    _hat("hat_teacup", "Teacup", 400, _teacup(),
         "Rosebud china on a gilded saucer, still steaming. Perfectly balanced. Do "
         "not run.", "uncommon", 18),
    _hat("hat_party", "Birthday Cone", 260, _party(),
         "Streamers, a bobble and a frill. One candle short of a cake.", "common", 21),
    _hat("hat_fur_cap", "Fur Cap", 420, _fur_cap(),
         "Ear flaps tied up, a star on the front. Warm, heavy, slightly shedding.",
         "uncommon", 22),
    _hat("hat_snow_cap", "Snowfall Cap", 380, _snow_cap(),
         "It is snowing on it. It is always snowing on it. Braided tassels, too.",
         "uncommon", 23),
    _hat("hat_candy_cap", "Candy Cane Cap", 340, _candy_cap(),
         "Peppermint stripes, holly and a candy cane. You can smell it across the lobby.",
         "uncommon", 24),
    _hat("hat_lantern", "Lantern Head", 1100, _lantern(),
         "A whole carved pumpkin, worn as a head, lit from the inside. Still glowing, "
         "somehow.", "rare", 25),
    _hat("hat_astro", "Astro Dome", 1300, _astro(),
         "A full glass helmet on a steel collar. Certified for vacuum, lava and "
         "awkward silences.", "rare", 19),
    _hat("hat_traffic_cone", "Traffic Cone", 90, _traffic_cone(),
         "Borrowed. Definitely borrowed.", "common", 20),
]


# ============================================================ BACK ITEMS
# Back parts are relative to the centre of the torso's back face: +Y up, -Z
# away from the body.  The shoulders are about +0.95, the seat about -1.0.
def _back(item_id: str, name: str, price: int, parts: List[Dict[str, Any]],
          desc: str, rarity: str = "common", order: int = 0,
          **extra: Any) -> Dict[str, Any]:
    item = {"id": item_id, "name": name, "slot": "back", "price": price,
            "rarity": rarity, "description": desc, "sort_order": order,
            "data": {"parts": parts}}
    item.update(extra)
    return item


def _backpack():
    khaki = "#7a5a34"
    dark = "#4f3a22"
    return [
        part("rbox", [0, 0.02, -0.36], [1.30, 1.50, 0.62], khaki, decal="canvas", wrap=True),
        part("rbox", [0, 0.80, -0.40], [1.36, 0.24, 0.72], dark, [0.10, 0, 0],
             decal="canvas", wrap=True),
        part("rbox", [0, -0.30, -0.74], [0.96, 0.66, 0.24], khaki, decal="canvas", wrap=True),
        part("rbox", [0, -0.02, -0.80], [1.00, 0.20, 0.18], dark, [0.25, 0, 0]),
        part("rbox", [0, -0.12, -0.90], [0.14, 0.12, 0.04], BRASS, mat="metal"),
        # a bedroll strapped on top
        place("capsule", [-0.66, 1.06, -0.40], [0.36, 0.44, 0.36], "#3f6b3a",
              anchor=[0, 0, 0], r=[0, 0, -PI / 2], decal="canvas", wrap=True),
        part("torus", [0.36, 1.06, -0.40], [0.40, 0.06, 0.40], dark, [0, 0, PI / 2]),
        part("torus", [-0.36, 1.06, -0.40], [0.40, 0.06, 0.40], dark, [0, 0, PI / 2]),
        # a canteen on one side, a rolled map on the other
        part("cyl", [0.74, -0.20, -0.36], [0.26, 0.56, 0.26], "#2f5fa8", mat="metal"),
        part("cyl", [0.74, 0.12, -0.36], [0.12, 0.10, 0.12], "#22262b"),
        place("capsule", [-0.72, -0.50, -0.30], [0.14, 0.24, 0.14], "#e6d7b0",
              anchor=[0, 0, 0], r=[0.3, 0, 0]),
        # straps over the shoulders
        part("rbox", [0.40, 0.90, 0.16], [0.18, 0.08, 0.80], dark),
        part("rbox", [-0.40, 0.90, 0.16], [0.18, 0.08, 0.80], dark),
    ]


def _wing_pair(colours, root_y=0.55, spread=0.32, lift=0.38, size=1.55):
    parts = []
    for layer, (c, k, dz, dlift) in enumerate(zip(colours, (1.0, 0.82, 0.62),
                                                   (0.0, -0.05, -0.10),
                                                   (0.0, -0.18, -0.36))):
        for side in (1, -1):
            ry = spread if side > 0 else PI - spread
            parts.append(place("wing", [0.18 * side, root_y - layer * 0.10, -0.40 + dz],
                               size * k, c, anchor=[-0.5, 0.0, 0],
                               r=[0, ry, (lift + dlift) if side > 0 else (lift + dlift)]))
    return parts


def _wings():
    parts = _wing_pair(["#f6f7fb", "#e4e8f0", "#ccd3df"])
    parts.append(part("rbox", [0, 0.50, -0.30], [0.40, 0.46, 0.20], "#d8dde6"))
    return parts


def _jetpack():
    rust = "#a3392b"
    parts = [part("rbox", [0, 0.20, -0.42], [0.62, 0.86, 0.40], "#6d6e6c", mat="metal",
                  decal="rivets", wrap=True)]
    for side in (1, -1):
        x = 0.44 * side
        parts += [
            place("capsule", [x, -0.70, -0.55], [0.56, 0.52, 0.56], rust, anchor=[0, 0, 0],
                  decal="rivets", wrap=True, mat="metal"),
            part("torus", [x, 0.20, -0.55], [0.60, 0.07, 0.60], "#4a4a4a", mat="metal"),
            part("torus", [x, -0.30, -0.55], [0.60, 0.07, 0.60], "#4a4a4a", mat="metal"),
            place("bell", [x, -0.66, -0.55], [0.46, 0.34, 0.46], "#2e2f31", anchor=[0, 1.0, 0],
                  r=[0, 0, 0], mat="metal"),
            place("flame", [x, -1.02, -0.55], 0.34, "#5ab4ff", r=[0, 0, PI], mat="neon",
                  alpha=0.85),
            part("disc", [x, 0.52, -0.84], [0.22, 0.22, 0.05], "#f2f3f3", [0, PI, 0],
                 decal="rivets"),
        ]
    parts += [part("cyl", [0, 0.72, -0.42], [0.10, 0.30, 0.10], "#22262b", mat="metal"),
              part("sph", [0, 0.90, -0.42], [0.14, 0.14, 0.14], "#ff3b3b", mat="neon")]
    return parts


def _hero_cape():
    return [
        place("cape", [0, 0.96, -0.08], [1.62, 1.86, 1.4], "#8b1a1a", anchor=[0, 0, 0]),
        place("ring", [0, 0.92, 0.50], [1.30, 0.6, 1.20], GOLD, anchor=[0, 0, 0],
              mat="metal"),
        part("disc", [0.52, 0.94, 0.98], [0.26, 0.26, 0.06], GOLD, mat="metal"),
        part("disc", [-0.52, 0.94, 0.98], [0.26, 0.26, 0.06], GOLD, mat="metal"),
        place("star", [0, 0.30, -0.24], 0.44, GOLD, r=[0.10, PI, 0], mat="metal"),
    ]


BACK_ITEMS: List[Dict[str, Any]] = [
    _back("back_backpack", "Explorer Backpack", 300, _backpack(),
          "Bedroll on top, canteen on the side, a map in the pocket and exactly one "
          "sandwich.", "common", 1),
    _back("back_wings", "Feather Wings", 1400, _wings(),
          "Three layers of white feathers on each side. Purely decorative. Gravity is "
          "undefeated.", "rare", 2),
    _back("back_jetpack", "Rusted Jetpack", 1600, _jetpack(),
          "Twin riveted tanks, two nozzles and a pilot light that will not go out. "
          "Ignition sold separately.", "rare", 3),
    _back("back_cape", "Hero Cape", 900, _hero_cape(),
          "Billows even indoors. Gold clasps, a gold star, a great deal of red.",
          "uncommon", 4),
]


# ======================================================= HALLOWEEN 2026
def _hexed_witch():
    hat = "#2a1f3d"
    parts = [
        place("brim", [0, -0.06, 0], [2.46, 1.5, 2.46], "#211830", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        place("bell", [0, -0.02, 0], [1.34, 1.48, 1.34], hat, anchor=[0, 0, 0],
              decal="felt", wrap=True),
        place("hook", [0, 1.40, 0], 0.80, hat, anchor=[0, 0, 0], r=[0, PI / 2, 0],
              decal="felt", wrap=True),
        # a violet band, a silver buckle with its hole
        place("ring", [0, 0.06, 0], [1.24, 1.0, 1.24], "#6b2fa3", anchor=[0, 0, 0]),
        part("rbox", [0, 0.16, 0.62], [0.34, 0.28, 0.07], "#c9ced6", mat="metal"),
        part("rbox", [0, 0.16, 0.655], [0.20, 0.15, 0.03], "#6b2fa3"),
        # a patch sewn on, and a crescent charm that glows
        part("rbox", [0.44, 0.62, 0.16], [0.24, 0.24, 0.03], "#3d2f55", [0.0, 1.25, 0.2],
             decal="stitches"),
        place("crescent", [-0.62, 0.14, 0.30], 0.30, "#c78bff", r=[0, -1.1, 0.2], mat="neon"),
        place("star", [-0.66, -0.04, 0.24], 0.12, "#e8d6ff", r=[0, -1.1, 0], mat="neon"),
        # a raven feather tucked in behind
        place("feather", [0.30, 0.42, -0.56], 0.95, "#1a1a2a", anchor=[0, -0.5, 0],
              r=[0.5, PI, -0.5]),
        # and a spider, let down on its thread from the brim
        part("cyl", [0.80, -0.30, 0.80], [0.012, 0.50, 0.012], "#d8d8e8", alpha=0.7),
        part("sph", [0.80, -0.58, 0.80], [0.13, 0.12, 0.13], "#15121c"),
        part("sph", [0.80, -0.68, 0.80], [0.17, 0.17, 0.17], "#1d1828"),
        part("sph", [0.84, -0.56, 0.86], [0.03, 0.03, 0.03], "#ff3b3b", mat="neon"),
        part("sph", [0.76, -0.56, 0.86], [0.03, 0.03, 0.03], "#ff3b3b", mat="neon"),
    ]
    for k in range(4):
        for side in (1, -1):
            a = -0.9 + k * 0.6
            parts.append(part("box", [0.80 + side * 0.13, -0.62 + a * 0.05,
                                      0.80 + (k - 1.5) * 0.06],
                              [0.22, 0.025, 0.025], "#15121c", [0, (k - 1.5) * 0.3,
                                                                -0.5 * side]))
    return parts


def _plague_doctor():
    leather = "#cdbf9f"
    black = "#1e1a17"
    parts = [
        place("brim", [0, -0.04, 0], [2.22, 1.3, 2.22], black, anchor=[0, 0, 0],
              decal="leather", wrap=True),
        place("cask", [0, -0.02, 0], [1.38, 0.66, 1.38], black, anchor=[0, 0, 0],
              decal="leather", wrap=True),
        place("ring", [0, 0.04, 0], [1.42, 0.7, 1.42], "#4a3424", anchor=[0, 0, 0]),
        part("rbox", [0.70, 0.10, 0.0], [0.06, 0.16, 0.20], BRASS, mat="metal"),
        # a black hood over the head, and the mask over the face: a leather
        # shield that narrows to the chin, with the long curved beak
        part("rbox", [0, -0.62, -0.02], [1.58, 1.16, 1.52], "#191512", decal="felt",
             wrap=True),
        place("shield", [0, -0.62, 0.70], [1.42, 0.98, 1.6], leather, decal="stitches"),
        place("teardrop", [0, -0.70, 0.74], [0.66, 1.40, 0.60], leather,
              anchor=[0, 0.12, 0], r=[1.93, 0, 0], decal="stitches", wrap=True),
        part("torus", [0, -0.76, 0.90], [0.62, 0.08, 0.58], "#8a6a4a", [1.93, 0, 0]),
        # brass-rimmed lenses of red glass
        part("rbox", [0, -0.43, -0.02], [1.56, 0.08, 1.50], "#2a221c"),
    ]
    for side in (1, -1):
        parts += [
            place("ring", [0.30 * side, -0.40, 0.75], [0.40, 0.7, 0.40], BRASS,
                  anchor=[0, 0, 0], r=[PI / 2, 0, 0], mat="metal"),
            part("disc", [0.30 * side, -0.40, 0.80], [0.30, 0.30, 0.03], "#b3202a",
                 alpha=0.85, mat="glass"),
        ]
    return parts


def _mummy():
    linen = "#e3dbc6"
    shades = ["#ddd4bd", "#ece5d2", "#d6ccb2", "#e8e0cc"]
    parts = [
        place("hemi", [0, -0.24, 0], [1.84, 0.84, 1.78], linen, anchor=[0, 0, 0],
              decal="linen", wrap=True),
    ]
    # strips wound round and round, leaving a gap for the eyes, with one
    # pulled across like a patch
    for k, (y, tilt, twist) in enumerate(((-0.24, 0.06, 0.05), (-0.31, -0.08, -0.1),
                                          (-0.60, 0.10, 0.12), (-0.74, -0.06, -0.05),
                                          (-0.90, 0.08, 0.1), (-1.04, -0.05, 0.0))):
        parts.append(part("rbox", [0, y, 0], [1.56, 0.14, 1.50], shades[k % 4],
                          [twist, 0, tilt], decal="linen", wrap=True))
    parts += [
        part("rbox", [-0.20, -0.46, 0.73], [0.62, 0.15, 0.08], "#d6ccb2", [0, 0, 0.55],
             decal="linen", wrap=True),
        place("ribbon", [0.30, -0.30, -0.76], [0.22, 0.80, 0.05], "#e8e0cc",
              anchor=[0, 0.5, 0], r=[-0.3, 0.2, 0.25], decal="linen", wrap=True),
        place("ribbon", [-0.62, -0.92, 0.40], [0.18, 0.50, 0.05], "#ddd4bd",
              anchor=[0, 0.5, 0], r=[0.1, -1.2, -0.2], decal="linen", wrap=True),
        # something green glows in the dark under the wraps
        part("sph", [0.24, -0.47, 0.71], [0.10, 0.06, 0.03], NEON_GREEN, mat="neon"),
    ]
    return parts


def _tagalong_ghost():
    sheet = "#f4f6ff"
    # hovering at your shoulder, level with your ear
    x, y, z = 1.10, -0.32, -0.08
    parts = [
        place("bell", [x, y - 0.10, z], [0.70, 0.64, 0.70], sheet, anchor=[0, 0, 0]),
        part("sph", [x, y + 0.48, z], [0.62, 0.60, 0.60], sheet),
        # its face: two black ovals and a little "o"
        part("sph", [x - 0.10, y + 0.52, z + 0.27], [0.09, 0.14, 0.05], "#15151f"),
        part("sph", [x + 0.10, y + 0.52, z + 0.27], [0.09, 0.14, 0.05], "#15151f"),
        part("sph", [x, y + 0.36, z + 0.28], [0.07, 0.08, 0.04], "#15151f"),
        part("sph", [x - 0.18, y + 0.40, z + 0.24], [0.07, 0.04, 0.02], "#ffb3c8"),
        part("sph", [x + 0.18, y + 0.40, z + 0.24], [0.07, 0.04, 0.02], "#ffb3c8"),
        # stubby arms, one holding up a lantern
        place("teardrop", [x + 0.30, y + 0.20, z], [0.16, 0.30, 0.16], sheet,
              anchor=[0, 0, 0], r=[0, 0, -1.2]),
        place("teardrop", [x - 0.30, y + 0.18, z], [0.16, 0.28, 0.16], sheet,
              anchor=[0, 0, 0], r=[0, 0, 1.5]),
        place("arch", [x + 0.56, y + 0.26, z], [0.12, 0.10, 0.4], IRON, anchor=[0, 0, 0]),
        place("cask", [x + 0.56, y + 0.02, z], [0.16, 0.22, 0.16], "#ffcf5a",
              anchor=[0, 0, 0], mat="neon", alpha=0.9),
        part("cyl", [x + 0.56, y + 0.25, z], [0.18, 0.03, 0.18], IRON, mat="metal"),
        part("cyl", [x + 0.56, y + 0.0, z], [0.18, 0.03, 0.18], IRON, mat="metal"),
    ]
    # the wavy hem: soft scallops round the bottom of the sheet
    parts += [part("sph", [x + math.sin(a) * 0.29, y - 0.10, z + math.cos(a) * 0.29],
                   [0.20, 0.17, 0.20], sheet)
              for a in [k * TAU / 7 for k in range(7)]]
    return parts


def _nightwing_cloak():
    return [
        place("cape", [0, 0.98, -0.08], [1.70, 1.90, 1.5], "#121018", anchor=[0, 0, 0]),
        place("cape", [0, 0.96, -0.04], [1.58, 1.84, 1.2], "#7a0f1c", anchor=[0, 0, 0]),
        # the stand-up collar, black outside and blood red within
        place("collar", [0, 0.88, 0.52], [1.16, 1.0, 1.12], "#121018", anchor=[0, 0, 0]),
        place("collar", [0, 0.90, 0.52], [1.08, 0.92, 1.04], "#7a0f1c", anchor=[0, 0, 0]),
        # a gold clasp at each collarbone and the chain between them
        part("disc", [0.50, 0.86, 0.98], [0.24, 0.24, 0.06], GOLD, mat="metal"),
        part("disc", [-0.50, 0.86, 0.98], [0.24, 0.24, 0.06], GOLD, mat="metal"),
        place("gem", [0.50, 0.86, 1.02], [0.12, 0.12, 0.12], "#d01c2a", anchor=[0, 0.36, 0],
              r=[PI / 2, 0, 0], mat="glass"),
        place("gem", [-0.50, 0.86, 1.02], [0.12, 0.12, 0.12], "#d01c2a", anchor=[0, 0.36, 0],
              r=[PI / 2, 0, 0], mat="glass"),
        place("arch", [0, 0.86, 1.00], [1.0, 0.30, 0.25], GOLD, anchor=[0, 0, 0],
              r=[PI, 0, 0], mat="metal"),
        # and a bat brooch sewn on between the shoulders
        place("bat", [0, 0.60, -0.17], 0.62, "#c8a030", r=[0, PI, 0], mat="metal"),
    ]


def _hallowed(item_id, name, price, slot, parts, desc, rarity, order):
    return {"id": item_id, "name": name, "slot": slot, "price": price,
            "rarity": rarity, "description": desc, "sort_order": order,
            "event": "halloween", "data": {"parts": parts}}


HALLOWEEN_COSMETICS: List[Dict[str, Any]] = [
    _hallowed("hat_hexed_witch", "Hexed Witch's Hat", 2400, "hat", _hexed_witch(),
              "A crooked crown, a crescent charm that will not stop glowing, and a "
              "spider who came with the hat.", "legendary", 101),
    _hallowed("hat_plague_doctor", "Plague Doctor's Visage", 1600, "hat", _plague_doctor(),
              "The Captain's own surgeon wore it. Brass-rimmed lenses, a beak of stitched "
              "leather, and the herbs are long gone.", "rare", 102),
    _hallowed("hat_mummy", "Mummy's Wrappings", 900, "hat", _mummy(),
              "Six strips of very old linen, wound round twice. Something green looks out "
              "from underneath.", "uncommon", 103),
    _hallowed("hat_tagalong_ghost", "Boo, the Tagalong Ghost", 1800, "hat",
              _tagalong_ghost(),
              "A small ghost has decided it lives with you now. It brought its own "
              "lantern.", "rare", 104),
    _hallowed("back_nightwing_cloak", "Nightwing Cloak", 1700, "back", _nightwing_cloak(),
              "Black outside, blood red within, a collar to the ears and a bat on the "
              "back. Count not included.", "rare", 105),
]


# ====================================================== CRATES AND KEYS
# A crate's lid parts carry ``lid: 1`` and the crate names the hinge the lid
# turns about (``data.hinge``, a point and the axis is X), so the opening
# animation can swing exactly the lid open.  The lock carries ``lock: 1`` so
# the key knows where to go.
def _classic_crate():
    wood = "#a06e3e"
    dark = "#6b4524"
    iron = "#4a4d52"
    parts = [
        part("rbox", [0, 0.0, 0], [1.64, 1.00, 1.12], wood, decal="planks", wrap=True),
        part("rbox", [0, 0.64, 0], [1.70, 0.28, 1.18], wood, decal="planks", wrap=True,
             lid=1),
        # iron straps round body and lid
        part("rbox", [0.56, 0.0, 0], [0.12, 1.04, 1.16], iron, mat="metal"),
        part("rbox", [-0.56, 0.0, 0], [0.12, 1.04, 1.16], iron, mat="metal"),
        part("rbox", [0.56, 0.64, 0], [0.12, 0.32, 1.22], iron, mat="metal", lid=1),
        part("rbox", [-0.56, 0.64, 0], [0.12, 0.32, 1.22], iron, mat="metal", lid=1),
        # stencil on both sides
        part("box", [0.835, 0.02, 0], [0.02, 0.66, 0.80], "#000000", [0, PI / 2, 0],
             decal="crate_logo", alpha=-1),
        part("box", [-0.835, 0.02, 0], [0.02, 0.66, 0.80], "#000000", [0, -PI / 2, 0],
             decal="crate_logo", alpha=-1),
        # the lock: a brass plate with a keyhole and a hasp from the lid
        part("rbox", [0, 0.10, 0.575], [0.40, 0.46, 0.06], BRASS, decal="keyhole",
             mat="metal", lock=1),
        part("rbox", [0, 0.48, 0.60], [0.18, 0.30, 0.06], iron, mat="metal", lid=1),
        # handles on the ends
        place("arch", [0.83, 0.10, 0], [0.42, 0.28, 0.6], iron, anchor=[0, 0, 0],
              r=[0, PI / 2, -PI / 2], mat="metal"),
        place("arch", [-0.83, 0.10, 0], [0.42, 0.28, 0.6], iron, anchor=[0, 0, 0],
              r=[0, PI / 2, PI / 2], mat="metal"),
        # the light that waits inside, seen through the seam once it opens
        part("box", [0, 0.48, 0], [1.50, 0.04, 0.98], "#ffe9a8", mat="neon"),
    ]
    # brass corners
    for x in (-0.80, 0.80):
        for zz in (-0.54, 0.54):
            for yy, lid in ((-0.46, 0), (0.74, 1)):
                parts.append(part("rbox", [x, yy, zz], [0.14, 0.14, 0.14], BRASS,
                                  mat="metal", lid=lid or None))
    return parts


def _hallowed_crate():
    wood = "#3b2a2a"
    iron = "#202024"
    parts = [
        part("rbox", [0, 0.0, 0], [1.66, 0.98, 1.08], wood, decal="planks", wrap=True),
        part("rbox", [0, 0.62, 0], [1.72, 0.30, 1.14], "#33231f", decal="planks", wrap=True,
             lid=1),
        part("rbox", [0, 0.86, 0], [1.40, 0.16, 0.86], "#2a1c19", lid=1),
        part("rbox", [0.60, 0.0, 0], [0.10, 1.02, 1.12], iron, mat="metal"),
        part("rbox", [-0.60, 0.0, 0], [0.10, 1.02, 1.12], iron, mat="metal"),
        part("rbox", [0.60, 0.62, 0], [0.10, 0.34, 1.18], iron, mat="metal", lid=1),
        part("rbox", [-0.60, 0.62, 0], [0.10, 0.34, 1.18], iron, mat="metal", lid=1),
        part("box", [0, 0.02, -0.552], [0.86, 0.74, 0.02], "#000000", [0, PI, 0],
             decal="crate_hallowed", alpha=-1),
        # the lock is a little jack-o'-lantern
        place("pumpkin", [0, -0.12, 0.56], [0.46, 0.50, 0.40], "#e2621b", anchor=[0, 0.047, 0],
              lock=1),
        place("tri", [-0.08, 0.06, 0.765], [0.09, 0.08, 0.2], "#ffd23a", mat="neon"),
        place("tri", [0.08, 0.06, 0.765], [0.09, 0.08, 0.2], "#ffd23a", mat="neon"),
        place("grin", [0, -0.04, 0.755], [0.22, 0.20, 0.2], "#ffd23a", r=[0.3, 0, 0],
              mat="neon"),
        place("hook", [0, 0.24, 0.56], 0.14, "#4a5d23", anchor=[0, 0, 0]),
        # bat wings on the ends
        place("bat", [0.88, 0.10, 0], 0.80, "#2a1f3d", r=[0, PI / 2, 0]),
        place("bat", [-0.88, 0.10, 0], 0.80, "#2a1f3d", r=[0, -PI / 2, 0]),
        # a candle burning on the lid, wax running down it
        part("cyl", [0.46, 1.06, 0.20], [0.16, 0.30, 0.16], "#efe6d0", lid=1),
        place("teardrop", [0.40, 1.04, 0.27], [0.07, 0.16, 0.07], "#efe6d0",
              anchor=[0, 1.0, 0], r=[PI, 0, 0], lid=1),
        place("flame", [0.46, 1.30, 0.20], 0.20, "#ffb02e", mat="neon", lid=1),
        # cobwebs across two corners
        part("box", [0.70, 0.38, 0.50], [0.36, 0.01, 0.01], "#e8e8f0", [0, 0, 0.78],
             alpha=0.5),
        part("box", [0.70, 0.38, 0.50], [0.36, 0.01, 0.01], "#e8e8f0", [0, 0, -0.2],
             alpha=0.5),
        part("box", [-0.70, -0.38, 0.50], [0.36, 0.01, 0.01], "#e8e8f0", [0, 0, 0.78],
             alpha=0.5),
        # ivy creeping up one corner
        place("hook", [-0.82, -0.48, 0.52], 0.5, "#2f5d2a", anchor=[0, 0, 0], r=[0, -0.6, 0]),
        place("leaf", [-0.80, -0.20, 0.58], 0.24, "#3f7a2a", r=[0.3, -0.7, 0.8]),
        place("leaf", [-0.86, 0.02, 0.54], 0.20, "#4a8a32", r=[0.3, -0.9, -0.5]),
        # a green glow waiting in the seam
        part("box", [0, 0.48, 0], [1.52, 0.04, 0.96], NEON_GREEN, mat="neon"),
    ]
    for x in (-0.80, 0.80):
        for zz in (-0.52, 0.52):
            parts.append(part("sph", [x, -0.46, zz], [0.14, 0.14, 0.14], "#8a8f99",
                              mat="metal"))
    return parts


def _classic_key():
    return [
        place("cog", [-0.62, 0, 0], 0.66, GOLD, mat="metal"),
        part("disc", [-0.62, 0, 0], [0.40, 0.40, 0.16], "#8a6410", mat="metal"),
        place("star", [-0.62, 0.01, 0.06], 0.30, "#fff3b0", mat="neon"),
        part("cyl", [0.12, 0, 0], [0.11, 1.10, 0.11], GOLD, [0, 0, PI / 2], mat="metal"),
        part("torus", [-0.24, 0, 0], [0.22, 0.10, 0.22], GOLD_DARK, [0, 0, PI / 2],
             mat="metal"),
        part("torus", [0.10, 0, 0], [0.16, 0.06, 0.16], GOLD_DARK, [0, 0, PI / 2],
             mat="metal"),
        part("rbox", [0.56, -0.14, 0], [0.10, 0.22, 0.06], GOLD, mat="metal"),
        part("rbox", [0.38, -0.11, 0], [0.08, 0.16, 0.06], GOLD, mat="metal"),
        part("rbox", [0.66, -0.07, 0], [0.06, 0.12, 0.06], GOLD, mat="metal"),
    ]


def _hallowed_key():
    steel = "#aeb6bf"
    return [
        place("pumpkin", [-0.64, -0.24, 0], [0.56, 0.60, 0.48], "#e2621b",
              anchor=[0, 0.047, 0]),
        place("tri", [-0.73, 0.0, 0.25], [0.10, 0.10, 0.2], "#ffd23a", mat="neon"),
        place("tri", [-0.55, 0.0, 0.25], [0.10, 0.10, 0.2], "#ffd23a", mat="neon"),
        place("grin", [-0.64, -0.10, 0.24], [0.26, 0.22, 0.2], "#ffd23a", mat="neon"),
        place("hook", [-0.64, 0.18, 0], 0.16, "#4a5d23", anchor=[0, 0, 0]),
        place("bat", [-0.64, 0.14, -0.04], 0.95, "#2a1f3d", r=[0, 0, 0]),
        part("cyl", [0.10, 0, 0], [0.10, 1.04, 0.10], steel, [0, 0, PI / 2], mat="metal"),
        part("torus", [-0.30, 0, 0], [0.20, 0.08, 0.20], "#6b2fa3", [0, 0, PI / 2],
             mat="metal"),
        part("sph", [0.02, 0, 0], [0.16, 0.16, 0.16], BONE),
        part("sph", [0.62, 0, 0], [0.14, 0.14, 0.14], steel, mat="metal"),
        # the bit is a row of fangs
        place("cone", [0.50, -0.06, 0], [0.08, 0.20, 0.08], BONE, anchor=[0, 0.5, 0],
              r=[0, 0, PI]),
        place("cone", [0.38, -0.06, 0], [0.08, 0.14, 0.08], BONE, anchor=[0, 0.5, 0],
              r=[0, 0, PI]),
        place("cone", [0.62, -0.06, 0], [0.07, 0.12, 0.07], BONE, anchor=[0, 0.5, 0],
              r=[0, 0, PI]),
        place("teardrop", [-0.64, 0.30, 0.0], [0.14, 0.26, 0.14], NEON_GREEN,
              anchor=[0, 0, 0], mat="neon", alpha=0.85),
    ]


CRATES: List[Dict[str, Any]] = [
    {"id": "crate_classic", "name": "Blockhaven Hat Crate", "slot": "crate", "price": 500,
     "rarity": "rare", "sort_order": 2, "series": "classic",
     "description": "Iron-strapped, brass-cornered and stencilled: every hat ever made "
                    "for Blockhaven is in one of these. Needs a Crate Key.",
     "data": {"parts": _classic_crate(), "hinge": [0, 0.50, -0.56]}},
    {"id": "crate_halloween", "name": "Hallowed Harvest Crate", "slot": "crate",
     "price": 500, "rarity": "legendary", "sort_order": 4, "series": "halloween",
     "event": "halloween",
     "description": "Dug up at midnight. Bat wings, a lantern for a lock, a candle that "
                    "lit itself. Holds the Halloween set and its two weapons. Needs a "
                    "Hallowed Key.",
     "data": {"parts": _hallowed_crate(), "hinge": [0, 0.48, -0.54]}},
]

KEYS: List[Dict[str, Any]] = [
    {"id": "key_standard", "name": "Crate Key", "slot": "key", "price": 500,
     "rarity": "uncommon", "sort_order": 1, "opens": ["classic"],
     "description": "Brass, star in the bow. Unlocks one Blockhaven Hat Crate -- and is "
                    "used up doing it.",
     "data": {"parts": _classic_key(), "opens": ["classic"]}},
    {"id": "key_halloween", "name": "Hallowed Key", "slot": "key", "price": 600,
     "rarity": "rare", "sort_order": 3, "opens": ["halloween"], "event": "halloween",
     "description": "A lantern for a bow and a row of fangs for teeth. Unlocks one "
                    "Hallowed Harvest Crate, then crumbles.",
     "data": {"parts": _hallowed_key(), "opens": ["halloween"]}},
]


# ==================================================== HALLOWEEN WEAPONS
# Held parts are relative to the right hand's grip, the business end towards
# +Z.  Both weapons carry a gimmick the game hosts implement
# (app/game/instance.py) -- the stats below are the whole of their tuning.
def _hollow_harvester():
    wood = "#2b1d14"
    return [
        part("cyl", [0, 0, 0.90], [0.15, 3.30, 0.15], wood, [PI / 2, 0, 0]),
        part("cyl", [0, 0, 0.0], [0.16, 0.50, 0.16], "#4a2f1e", [PI / 2, 0, 0],
             decal="leather", wrap=True),
        part("cyl", [0, 0, 1.25], [0.15, 0.36, 0.15], "#4a2f1e", [PI / 2, 0, 0],
             decal="leather", wrap=True),
        place("cone", [0, 0, -0.76], [0.14, 0.30, 0.14], IRON, anchor=[0, 0.5, 0],
              r=[-PI / 2, 0, 0], mat="metal"),
        # the blade, its spine, and a ghost-green edge where the souls gather
        place("blade", [0.04, 0.02, 2.52], 2.2, "#c9ccd6", anchor=[-0.5, 0.08, 0],
              r=[PI / 2, 0, 0], mat="metal"),
        place("blade", [0.04, 0.02, 2.50], [2.25, 2.14, 0.6], NEON_GREEN,
              anchor=[-0.5, 0.08, 0], r=[PI / 2, 0, 0], mat="neon", alpha=0.55),
        part("cyl", [0, 0, 2.52], [0.20, 0.22, 0.20], GOLD_DARK, [PI / 2, 0, 0], mat="metal"),
        # a little skull at the join, and the soul lantern hung beneath it
        part("sph", [0, 0.16, 2.46], [0.24, 0.22, 0.22], BONE),
        part("sph", [-0.06, 0.18, 2.36], [0.06, 0.07, 0.04], "#15121c"),
        part("sph", [0.06, 0.18, 2.36], [0.06, 0.07, 0.04], "#15121c"),
        part("cyl", [0, -0.14, 2.40], [0.015, 0.16, 0.015], IRON),
        place("teardrop", [0, -0.24, 2.40], [0.12, 0.20, 0.12], NEON_GREEN,
              anchor=[0, 1.0, 0], r=[PI, 0, 0], mat="neon", alpha=0.9),
    ]


def _jack_o_launcher():
    iron = "#2b2b30"
    return [
        part("cyl", [0, 0, 0.62], [0.40, 1.70, 0.40], iron, [PI / 2, 0, 0], mat="metal",
             decal="rivets", wrap=True),
        place("bell", [0, 0, 1.40], [0.70, 0.40, 0.70], iron, anchor=[0, 0, 0],
              r=[-PI / 2, 0, 0], mat="metal"),
        part("torus", [0, 0, 1.42], [0.72, 0.10, 0.72], "#e2621b", [PI / 2, 0, 0]),
        part("torus", [0, 0, 0.30], [0.46, 0.08, 0.46], "#e2621b", [PI / 2, 0, 0]),
        # the drum: a jack-o'-lantern full of more of itself
        place("pumpkin", [0, 0.16, 0.42], [0.78, 0.84, 0.74], "#e2621b",
              anchor=[0, 0.047, 0]),
        place("tri", [0.36, 0.48, 0.32], [0.14, 0.12, 0.2], "#ffd23a", r=[0, PI / 2, 0],
              mat="neon"),
        place("tri", [0.36, 0.48, 0.54], [0.14, 0.12, 0.2], "#ffd23a", r=[0, PI / 2, 0],
              mat="neon"),
        place("grin", [0.37, 0.32, 0.43], [0.34, 0.28, 0.2], "#ffd23a", r=[0, PI / 2, 0],
              mat="neon"),
        place("hook", [0, 0.72, 0.42], 0.22, "#4a5d23", anchor=[0, 0, 0]),
        # a candle for a sight
        part("cyl", [0, 0.30, 1.12], [0.08, 0.16, 0.08], "#efe6d0"),
        place("flame", [0, 0.44, 1.12], 0.10, "#ffb02e", mat="neon"),
        # stock, grip and a twist of vine
        part("rbox", [0, -0.16, -0.46], [0.22, 0.30, 0.82], "#5a3a22", decal="leather",
             wrap=True),
        part("rbox", [0, -0.36, -0.08], [0.18, 0.40, 0.22], "#4a2f18", [0.3, 0, 0]),
        place("hook", [0.18, -0.10, 0.90], 0.32, "#2f5d2a", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0.5]),
        place("leaf", [0.22, 0.08, 0.98], 0.20, "#3f7a2a", r=[0.2, 0.9, 0.4]),
    ]


HALLOWEEN_WEAPONS: List[Dict[str, Any]] = [
    {"id": "use_hollow_harvester", "name": "Hollow Harvester", "slot": "usable",
     "price": 1666, "rarity": "legendary", "sort_order": 11, "event": "halloween",
     "description": "Every kill it takes, it keeps: up to three souls ride the blade. "
                    "The next swing spends them all in one wide reaping arc that hits "
                    "harder for each and mends you as it goes.",
     "data": {"stats": {
         "kind": "melee", "damage": 40, "headshot": 1.3, "rpm": 70,
         "range": 11.5, "arc": 0.62, "sound": "sword", "knockback": 14,
         # the gimmick: souls banked on kills, spent on the next swing
         "souls": 3, "soul_damage": 16, "soul_heal": 9, "soul_arc": 1.25,
         "soul_range": 2.5,
     }, "parts": _hollow_harvester()}},
    {"id": "use_jack_o_launcher", "name": "Jack-o'-Launcher", "slot": "usable",
     "price": 1999, "rarity": "legendary", "sort_order": 12, "event": "halloween",
     "description": "Lobs grinning pumpkins in a high arc. Trick: they burst on whatever "
                    "they hit, hurting every enemy nearby. Treat: the candy inside patches "
                    "up every teammate in the blast -- you included.",
     "data": {"stats": {
         "kind": "projectile", "projectile": "pumpkin", "damage": 50, "splash": 10.0,
         "splash_damage": 40, "rpm": 50, "mag": 3, "reload": 2.8, "speed": 62,
         "range": 400, "auto": False, "sound": "rocket", "recoil": 3.8, "reserve": 21,
         # a heavier lob than a rocket, no rocket jump, and the treat
         "gravity_scale": 1.25, "self_damage": 0.0, "knockback": 18,
         "self_knockback": 0.0, "treat_heal": 22,
     }, "parts": _jack_o_launcher()}},
]
