"""Easter: eggs, bunnies, and chocolate in quantities nobody should eat.

Nine days either side of Easter Sunday, every spring since the first:

  2022  Eggstravaganza    the first hunt: ten thousand painted eggs, three still lost
  2023  Bunny Burrow      the warren under the hill, its round door and its carrots
  2024  The Great Hatch   the incubator in the barn, and everything that hatched
  2025  Choc-o-Lock       the chocolatier's vault, foil, fondue and a hollow bunny
  2026  Faberge Gala      the jewelled egg at the imperial ball, and its surprise

Every egg in here is the one egg mesh (``egg``) or the two halves of a broken
one (``crackedshell`` and ``ea_eggtop``, which share an anchor and a scale and
close into a whole egg along the same zig-zag); ``_egg`` paints one up with
bands and spots, and ``_egg_r`` says how wide the egg is at any height, so a
band or a spot can sit on its surface instead of in it or off it.
"""
from __future__ import annotations

import math

from .kit import (BLACK, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, gift_bow, mix, part,
                  place, pompom, ringband, rotate, shade, sides, straps)

# the egg mesh: native 0.92 wide and 1.30 tall, its bottom at its origin
EGG_W, EGG_H = 0.92, 1.30


def _egg_r(f, k=1.0):
    """The egg's radius a fraction ``f`` of the way up it (0 the bottom, 1
    the top), for an egg mesh scaled by ``k`` across."""
    f = min(1.0, max(0.0, f))
    return k * math.sqrt(f * (1.0 - f)) * (1.0 - 0.16 * f)


def _egg_band(f0, f1, k, ky, y0, c, grow=0.012, mesh="ring", **kw):
    """A painted band round an upright egg (scaled ``k`` across and ``ky``
    up, its bottom at ``y0``) from ``f0`` to ``f1`` of its height: a washer
    just proud of the widest point it has to cover.  ``mesh`` "spikecrown"
    makes it a zig-zag."""
    rad = max(_egg_r(f0 + (f1 - f0) * i / 8.0, k) for i in range(9)) + grow
    h = EGG_H * ky * (f1 - f0)
    native_h = 0.2 if mesh == "ring" else 1.0
    return place(mesh, [0, y0 + EGG_H * ky * f0, 0], [rad * 2, h / native_h, rad * 2], c,
                 anchor=[0, 0, 0], **kw)


def _egg_spot(f, ang, k, ky, y0, d, c, depth=0.05, **kw):
    """A painted spot on an upright egg's surface, ``f`` of the way up and
    ``ang`` round from the front, turned to face out of the shell."""
    r = _egg_r(f, k)
    e = 0.01
    dr = _egg_r(f + e, k) - _egg_r(f - e, k)
    dy = EGG_H * ky * 2 * e
    tilt = math.atan2(dr, dy)          # the surface leans in as it climbs
    p = [math.sin(ang) * (r + depth * 0.25), y0 + EGG_H * ky * f, math.cos(ang) * (r + depth * 0.25)]
    return part("sph", p, [d, d, depth], c, [tilt, ang, 0], **kw)


def _egg(w, c, bands=(), zig=None, dots=None, m=None):
    """A painted egg ``w`` wide, upright with its bottom at the origin:
    ``bands`` are (f0, f1, colour), ``zig`` one (f0, f1, colour) zig-zag,
    ``dots`` (f, count, colour, size) a ring of spots.  Move it into place
    with ``at_frame`` (which turns it as a whole)."""
    k = w / EGG_W
    parts = [place("egg", [0, 0, 0], [k, k, k], c, anchor=[0, 0, 0], m=m)]
    for f0, f1, bc in bands:
        parts.append(_egg_band(f0, f1, k, k, 0.0, bc, grow=0.006 * w))
    if zig:
        parts.append(_egg_band(zig[0], zig[1], k, k, 0.0, zig[2], grow=0.008 * w,
                               mesh="spikecrown"))
    if dots:
        f, count, dc, size = dots
        r = _egg_r(f, k)
        for n in range(count):
            a = n * TAU / count
            parts.append(part("sph", [math.sin(a) * r, EGG_H * k * f, math.cos(a) * r],
                              [size * w, size * w, size * w], dc))
    return parts


def _lid(parts):
    """Mark every part as part of a crate's lid."""
    for p in parts:
        p["lid"] = 1
    return parts


def _euler(*steps):
    """The renderer's euler angles (R = Ry * Rx * Rz) for a sequence of
    turns about the world axes, applied in order: ``_euler(("y", a), ("x",
    PI / 2))`` spins a part about its own up axis and then lays it forward."""
    m = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    for axis, a in steps:
        c, s = math.cos(a), math.sin(a)
        r = {"x": [[1, 0, 0], [0, c, -s], [0, s, c]],
             "y": [[c, 0, s], [0, 1, 0], [-s, 0, c]],
             "z": [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis]
        m = [[sum(r[i][k] * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    rx = math.asin(max(-1.0, min(1.0, -m[1][2])))
    ry = math.atan2(m[0][2], m[2][2])
    rz = math.atan2(m[1][0], m[1][1])
    return [rx, ry, rz]


def _flower(at, k, petals, centre="#ffd84a", r=None, leaf=None):
    """A five-petalled blossom facing +Z (turned by ``r``), a bead of a
    centre, and a leaf behind it if asked."""
    x, y, z = at
    rr = list(r or [0, 0, 0])
    fwd = rotate([0, 0, 1], rr)
    out = [place("flower", [x, y, z], [k, k, k], petals, r=rr),
           part("sph", [x + fwd[0] * 0.04 * k, y + fwd[1] * 0.04 * k, z + fwd[2] * 0.04 * k],
                [0.30 * k, 0.30 * k, 0.16 * k], centre, rr)]
    if leaf:
        back = [x - fwd[0] * 0.03 * k, y - fwd[1] * 0.03 * k, z - fwd[2] * 0.03 * k]
        out.append(place("leaf", back, [k * 1.1, k * 0.9, k], leaf,
                         r=[rr[0], rr[1], rr[2] + 2.2]))
    return out


# ============================================================ 2022
LILAC = "#c7a8f0"
PINK = "#ff9cc9"
MINT = "#8fe3c0"
BUTTER = "#ffe58a"
SKYBLUE = "#9fd4ff"
CREAM = "#fff6e0"
STRAW = "#f1d98f"
GRASS = "#8fd36a"

EA22 = Event(
    "easter_2022", "easter", 2022, "ea22",
    name="Eggstravaganza", title="The Eggstravaganza",
    blurb="Blockhaven's first Easter. The mayor hid ten thousand painted eggs across "
          "every map in one night and declared a hunt. Nine thousand nine hundred and "
          "ninety-seven were found by Monday. The other three are still out there, and "
          "the big egg in the square has been rattling ever since.",
    tagline="Ten thousand eggs hidden. Three still missing.",
    starts="2022-04-08", ends="2022-04-26",
    colors={"accent": "#ff8fc8", "deep": "#2a1f3d", "glow": "#fff0a8"},
    family_effects=["sunbeam", "bubbly", "starstruck"],
    hero_effect="painted_parade", stencil="stencil_ea22")


@EA22.crate_model("Eggstravaganza Egg",
                  "The big egg from the town square: lilac, hand-painted, sat in a nest of "
                  "paper grass and cracked right round the top, which lifts off. Holds the "
                  "Eggstravaganza set. Needs a Painted Egg Key.",
                  hinge=[0, 0.12, -0.72], keyhole=[0, 0.01, 0.79])
def _():
    y0, k, ky = -0.80, 1.565, 1.33

    def Y(f):
        return y0 + EGG_H * ky * f
    parts = [
        place("crackedshell", [0, y0, 0], [k, ky, k], LILAC, anchor=[0, 0, 0],
              decal="ea_eggdots", wrap=True),
        place("ea_eggtop", [0, y0, 0], [k, ky, k], LILAC, anchor=[0, 0, 0],
              decal="ea_eggdots", wrap=True, lid=1),
        # the light inside, showing at the crack
        part("cyl", [0, Y(0.50), 0], [1.30, 0.05, 1.30], "#fff0a8", m="neon"),
        # painted bands on the bottom half: mint, then a zig-zag of butter
        _egg_band(0.12, 0.17, k, ky, y0, MINT),
        _egg_band(0.39, 0.49, k, ky, y0, BUTTER, mesh="spikecrown"),
        _egg_band(0.36, 0.39, k, ky, y0, PINK),
        # the nest: a shallow straw bowl, and paper grass spilling over it
        place("bowl", [0, -0.88, 0], [1.56, 0.56, 1.56], STRAW, anchor=[0, 0, 0],
              decal="ea_straw", wrap=True),
        part("torus", [0, -0.56, 0], [1.54, 0.5, 1.54], shade(STRAW, 0.9), decal="ea_straw",
             wrap=True),
        # the lock: a gold plate on the front, and a hasp down off the lid
        part("rbox", [0, 0.01, 0.745], [0.30, 0.32, 0.07], GOLD, decal="keyhole", m="metal",
             lock=1),
        part("rbox", [0, 0.24, 0.735], [0.12, 0.30, 0.05], GOLD, [0.08, 0, 0], m="metal", lid=1),
        part("torus", [0, 0.14, 0.775], [0.16, 0.25, 0.16], GOLD_DARK, [PI / 2, 0, 0], m="metal"),
        # the stencil, painted on the back
        part("box", [0, Y(0.30), -0.70], [0.62, 0.62, 0.02], "#000000", [0, PI, 0],
             decal="stencil_ea22", a=-1),
    ]
    # a row of spots round the front of the bottom half, two rows on the lid
    for n in range(7):
        a = -1.6 + n * 3.2 / 6
        parts.append(_egg_spot(0.25, a, k, ky, y0, 0.16, CREAM if n % 2 else PINK))
    for n in range(10):
        a = n * TAU / 10
        parts.append(_egg_spot(0.84, a, k, ky, y0, 0.14, PINK if n % 2 else SKYBLUE, lid=1))
    for n in range(6):
        a = n * TAU / 6 + 0.5
        parts.append(_egg_spot(0.93, a, k, ky, y0, 0.10, BUTTER, lid=1))
    # a pink bow tied on top
    parts += _lid(gift_bow([0, Y(1.0) - 0.02, 0], 0.55, PINK, knot="#ff7ab8"))
    # crinkled paper grass round the egg, in three greens and a pink
    for n in range(26):
        a = n * TAU / 26 + (0.12 if n % 2 else 0.0)
        rad = 0.66 if n % 2 else 0.74
        col = [GRASS, "#b5e88a", "#6fc25a", "#ffc4e1"][n % 4]
        parts.append(place("leaf", [math.sin(a) * rad, -0.50, math.cos(a) * rad],
                           [0.55, 0.42, 0.6], col, anchor=[0, -0.5, 0],
                           r=[0.45, a, 0]))
    return parts


@EA22.key_model("Painted Egg Key",
                "A key whose bow is a little painted egg, tied on with a pink ribbon, its "
                "teeth cut in a zig-zag like a crack. Opens one Eggstravaganza Egg.",
                shoulder=-0.30)
def _():
    parts = at_frame(_egg(0.46, LILAC, bands=[(0.16, 0.24, MINT), (0.62, 0.70, PINK)],
                          zig=(0.36, 0.50, BUTTER), dots=(0.84, 5, CREAM, 0.08)),
                     [-0.30, 0, 0], r=[0, 0, PI / 2])
    parts += [
        part("cyl", [0.18, 0, 0], [0.10, 0.98, 0.10], GOLD, [0, 0, PI / 2], m="metal"),
        part("cyl", [-0.30, 0, 0], [0.22, 0.08, 0.22], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        # the bit: teeth in a zig-zag, each a different pastel
        part("rbox", [0.40, -0.13, 0], [0.09, 0.20, 0.08], PINK),
        part("rbox", [0.50, -0.10, 0], [0.09, 0.14, 0.08], MINT),
        part("rbox", [0.60, -0.15, 0], [0.09, 0.24, 0.08], BUTTER),
        part("sph", [0.68, 0, 0], [0.12, 0.12, 0.12], GOLD, m="metal"),
    ]
    parts += gift_bow([-0.24, 0.10, 0], 0.30, PINK, knot="#ff7ab8", yaw=PI / 2)
    return parts


@EA22.hat("parade_bonnet", "Easter Parade Bonnet",
          "A wide straw picture hat with a satin band, a bow down the back, and more "
          "silk flowers than a garden centre. Something has been nesting in them.",
          "rare")
def _():
    parts = [
        dome(-0.24, 0.78, STRAW, decal="ea_straw", wrap=True),
        place("brim", [0, -0.02, 0], [2.70, 1.2, 2.60], STRAW, anchor=[0, 0, 0],
              decal="ea_straw", wrap=True),
        part("cyl", [0, 0.10, 0], [1.74, 0.18, 1.70], PINK),
        # the bow at the back and its tails
        *gift_bow([0, 0.12, -0.84], 0.62, PINK, knot="#ff7ab8", yaw=0.0, tails=False),
        place("ribbon", [0.12, 0.02, -1.00], [0.16, 0.86, 0.05], PINK, anchor=[0, 0.5, 0],
              r=[0.25, 0, 0.16]),
        place("ribbon", [-0.12, 0.02, -1.00], [0.16, 0.80, 0.05], PINK, anchor=[0, 0.5, 0],
              r=[0.25, 0, -0.16]),
        # a painted egg tucked into the flowers
        *at_frame(_egg(0.30, SKYBLUE, bands=[(0.30, 0.40, CREAM)], dots=(0.64, 5, PINK, 0.12)),
                  [0.30, 0.12, 0.86], r=[0.3, 0, -0.4]),
    ]
    # silk flowers bunched up the front left of the brim
    for (x, y, z, c, s, tilt) in ((-0.42, 0.30, 0.88, "#ffb3d8", 0.62, -0.45),
                                  (-0.80, 0.30, 0.56, "#fff3b0", 0.56, -0.40),
                                  (-0.04, 0.24, 1.00, "#c7a8f0", 0.46, -0.6),
                                  (-0.98, 0.28, 0.12, "#ffffff", 0.48, -0.35),
                                  (-0.64, 0.58, 0.62, "#9fd4ff", 0.42, -0.2),
                                  (-0.24, 0.56, 0.84, "#ffd0a0", 0.40, -0.2)):
        parts += _flower([x, y, z], s, c, r=[tilt, math.atan2(x, z), 0], leaf="#6fc25a")
    # a butterfly that has decided this is the best flower in town
    for side in (1, -1):
        parts.append(place("heart", [0.10 * side, 0.58, 0.06], [0.24, 0.26, 0.5], "#ffb35a",
                           r=[0, 0, -0.9 * side]))
    parts.append(part("capsule", [0, 0.56, 0.06], [0.05, 0.18, 0.05], BLACK))
    return parts


@EA22.hat("egg_cosy", "Egg Cosy",
          "Knitted by a grandmother for an egg of unusual size. You are the egg of "
          "unusual size. It is very warm and it has a pompom.", "uncommon")
def _():
    return [
        dome(-0.28, 1.02, WHITE, decal="ea_cosy", wrap=True),
        ringband(-0.20, 0.22, "#ff9cc9", decal="knit", wrap=True),
        pompom([0, 0.80, 0], 0.44, "#ffb3d8"),
        # a felt chick sewn on the front
        part("sph", [0, 0.16, 0.80], [0.34, 0.32, 0.08], "#ffe14d", [-0.35, 0, 0]),
        part("sph", [0, 0.36, 0.73], [0.20, 0.18, 0.06], "#ffe14d", [-0.45, 0, 0]),
        part("sph", [0.05, 0.38, 0.77], [0.04, 0.04, 0.02], BLACK, [-0.45, 0, 0]),
        place("tri", [0.0, 0.31, 0.75], [0.08, 0.08, 0.3], "#ff8c1a", r=[-0.45, 0, PI]),
    ]


@EA22.hat("humpty_wall", "Humpty's Wall",
          "A good stretch of brick wall and the egg who sits on it, swinging his legs, "
          "with a bow tie on and a hairline crack he would rather you did not mention.",
          "legendary")
def _():
    shell, suit = "#f6eedc", "#4a6ab0"
    parts = [
        # the wall, coping stones along its top
        part("rbox", [0, 0.06, 0], [1.98, 0.56, 1.62], "#b8613e", decal="bricks", wrap=True),
        part("rbox", [0, 0.38, 0], [2.06, 0.10, 1.70], "#c9b8a4"),
        # Humpty, sat square on the top
        place("egg", [0, 0.43, 0.28], [0.82, 0.78, 0.82], shell, anchor=[0, 0, 0]),
        # his face: two eyes, a smile, and a little crack
        part("sph", [0.13, 0.98, 0.65], [0.13, 0.16, 0.06], WHITE, [-0.2, 0.35, 0]),
        part("sph", [-0.13, 0.98, 0.65], [0.13, 0.16, 0.06], WHITE, [-0.2, -0.35, 0]),
        part("sph", [0.137, 0.97, 0.675], [0.07, 0.09, 0.03], BLACK, [-0.2, 0.35, 0]),
        part("sph", [-0.137, 0.97, 0.675], [0.07, 0.09, 0.03], BLACK, [-0.2, -0.35, 0]),
        place("grin", [0, 0.84, 0.67], [0.26, 0.26, 0.4], "#7a2a2a", r=[-0.15, 0, 0]),
        part("box", [0.24, 1.10, 0.55], [0.012, 0.12, 0.02], "#6a5a4a", [0, 0.8, 0.5]),
        part("box", [0.28, 1.02, 0.54], [0.012, 0.09, 0.02], "#6a5a4a", [0, 0.8, -0.4]),
        # his bow tie and the front of his waistcoat
        place("bowtie", [0, 0.70, 0.70], [0.30, 0.30, 0.6], "#e0405a", r=[-0.3, 0, 0]),
        # arms resting on the coping, legs dangling over the front
        part("capsule", [0.38, 0.60, 0.40], [0.08, 0.32, 0.08], shell, [0.4, 0, 1.0]),
        part("capsule", [-0.38, 0.60, 0.40], [0.08, 0.32, 0.08], shell, [0.4, 0, -1.0]),
    ]
    for side in (1, -1):
        parts += [
            part("cyl", [0.15 * side, 0.50, 0.74], [0.11, 0.30, 0.11], suit, [PI / 2, 0, 0]),
            part("sph", [0.15 * side, 0.50, 0.89], [0.12, 0.12, 0.12], suit),
            part("cyl", [0.15 * side, 0.30, 0.91], [0.11, 0.40, 0.11], suit, [0.12, 0, 0]),
            part("rbox", [0.15 * side, 0.10, 0.98], [0.16, 0.10, 0.24], BLACK),
        ]
    return parts


@EA22.hat("flower_crown", "Spring Flower Crown",
          "A ring of every pastel flower in the meadow, woven together on a vine. "
          "Bees will follow you. Accept this.", "uncommon", hair="show")
def _():
    parts = [ringband(-0.16, 0.08, "#5a9a3a")]
    cols = ["#ffb3d8", "#fff3b0", "#c7a8f0", "#ffffff", "#9fd4ff"]
    r = 0.96
    for n in range(10):
        a = n * TAU / 10
        parts += _flower([math.sin(a) * r, -0.12, math.cos(a) * r * 0.96],
                         0.30 if n % 2 else 0.36, cols[n % len(cols)],
                         r=[-0.35, a, 0], leaf="#6fc25a" if n % 2 else None)
    # ribbons trailing down the back
    for side in (1, -1):
        parts.append(place("ribbon", [0.10 * side, -0.16, -1.00], [0.14, 0.70, 0.05],
                           PINK if side > 0 else SKYBLUE, anchor=[0, 0.5, 0],
                           r=[0.18, 0, 0.12 * side]))
    return parts


@EA22.hat("dye_pot", "Dye Pot Topper",
          "The enamel cup from the egg-dyeing table, worn upside down after an "
          "incident, still running pink, blue and yellow down the sides. The egg on "
          "the dipper came out half done.", "rare")
def _():
    enamel = "#f4f6f8"
    parts = [
        part("cyl", [0, 0.30, 0], [1.24, 0.58, 1.24], enamel),
        part("torus", [0, 0.01, 0], [1.36, 0.55, 1.36], "#4a6ab0"),
        part("cyl", [0, 0.57, 0], [1.10, 0.04, 1.10], "#4a6ab0"),
        # the handle, round the side
        place("arch", [0.62, 0.30, 0], [0.42, 0.50, 0.9], enamel, anchor=[0, 0, 0],
              r=[0, 0, -PI / 2]),
    ]
    # three colours run down the sides from the bottom (the cup's upturned
    # mouth), drips hanging off the rim
    for n, (a, c) in enumerate(((0.3, "#ff7ab8"), (1.5, "#6ab8ff"), (2.6, "#ffd84a"),
                                (3.7, "#ff7ab8"), (4.8, "#6ab8ff"), (5.7, "#ffd84a"))):
        x, z = math.sin(a), math.cos(a)
        h = 0.50 + 0.06 * (n % 3)
        parts += [
            part("capsule", [x * 0.625, 0.60 - h / 2, z * 0.625], [0.22, h, 0.05], c, [0, a, 0],
                 m="glass"),
            part("sph", [x * 0.52, 0.595, z * 0.52], [0.30, 0.03, 0.30], c, m="glass"),
        ]
        if n % 2 == 0:
            parts.append(place("teardrop", [x * 0.66, 0.66 - h, z * 0.66], [0.13, 0.22, 0.13], c,
                               r=[PI, 0, 0], m="glass"))
    # the wire dipper, still holding the egg that came out half dyed
    parts += [
        part("cyl", [-0.30, 0.86, 0.10], [0.035, 0.80, 0.035], SILVER, [0.2, 0, 0.5], m="metal"),
        part("torus", [-0.52, 1.24, 0.18], [0.30, 0.15, 0.30], SILVER, [0.3, 0, 0.5], m="metal"),
    ]
    parts += at_frame(_egg(0.30, "#ff9cc9", bands=[(0.5, 1.0, CREAM)]),
                      [-0.54, 1.12, 0.18], r=[0.3, 0, 0.5])
    return parts


@EA22.hat("hunt_deerstalker", "Egg Hunter's Deerstalker",
          "A deerstalker in pastel tweed, flaps tied up, a magnifying glass in the band. "
          "Eleven eggs found under it on the first morning. Elementary.", "rare")
def _():
    tweed = "#b8a6d8"
    parts = [
        dome(-0.30, 0.86, tweed, decal="ea_gingham", wrap=True),
        part("sph", [0, 0.56, 0], [0.16, 0.10, 0.16], "#7a5aa8"),
        # front and back peaks, turned down a little
        place("peak", [0, -0.22, 0], [1.05, 2.2, 1.70], shade(tweed, 0.88), anchor=[0, 0, 0],
              decal="ea_gingham", wrap=True),
        place("peak", [0, -0.22, 0], [1.05, 2.2, 1.70], shade(tweed, 0.88), anchor=[0, 0, 0],
              r=[0, PI, 0], decal="ea_gingham", wrap=True),
        ringband(-0.20, 0.10, "#7a5aa8"),
        # the ear flaps, tied up over the crown with a bow
        part("rbox", [0.73, 0.29, 0], [0.08, 0.60, 0.50], shade(tweed, 1.08), [0, 0, 0.735],
             decal="ea_gingham", wrap=True),
        part("rbox", [-0.73, 0.29, 0], [0.08, 0.60, 0.50], shade(tweed, 1.08), [0, 0, -0.735],
             decal="ea_gingham", wrap=True),
        part("cyl", [0, 0.53, 0], [0.025, 0.95, 0.025], PINK, [0, 0, PI / 2]),
        place("bowtie", [0, 0.53, 0], [0.30, 0.30, 0.6], PINK, r=[0, PI / 2, 0]),
        # the magnifying glass, tucked in at the side
        part("torus", [0.86, 0.18, 0.30], [0.40, 0.50, 0.40], BRASS, [PI / 2, PI / 2, 0.4],
             m="metal"),
        part("cyl", [0.86, 0.18, 0.30], [0.34, 0.02, 0.34], "#dff2ff", [PI / 2, PI / 2, 0.4],
             m="glass", a=0.5),
        part("cyl", [0.88, -0.10, 0.18], [0.08, 0.36, 0.08], "#5a3a22", [0.4, 0, 0.0]),
    ]
    return parts


@EA22.hat("egg_crown", "Crown of a Dozen Eggs",
          "A gold circlet set with twelve eggs, one from every map, each painted by "
          "hand and sat in its own cup. The thirteenth setting is empty. It knows.",
          "legendary", hair="show")
def _():
    parts = [
        ringband(-0.10, 0.20, GOLD, m="metal"),
        part("torus", [0, 0.0, 0], [1.92, 0.45, 1.88], GOLD_DARK, m="metal"),
    ]
    paints = [(LILAC, MINT), (PINK, CREAM), (BUTTER, SKYBLUE), (MINT, PINK),
              (SKYBLUE, BUTTER), (CREAM, LILAC)]
    for n in range(13):
        a = n * TAU / 13
        x, z = math.sin(a) * 0.93, math.cos(a) * 0.91
        parts.append(part("cyl", [x, 0.03, z], [0.18, 0.08, 0.18], GOLD, m="metal"))
        if n == 0:
            # the empty setting, front and centre
            parts.append(part("torus", [x, 0.08, z], [0.18, 0.2, 0.18], GOLD_DARK, m="metal"))
            continue
        body, stripe = paints[n % len(paints)]
        parts += at_frame(_egg(0.20, body, bands=[(0.40, 0.52, stripe)],
                               dots=(0.74, 4, WHITE, 0.10)),
                          [x, 0.07, z], r=[0.18 * math.cos(a), 0, -0.18 * math.sin(a)])
    return parts


@EA22.back("hunt_basket", "Egg Hunt Basket",
           "A wicker basket on your back, heaped with paper grass and the morning's "
           "haul. Some of the eggs in it are not yours. Keep walking.", "rare")
def _():
    parts = [
        place("bowl", [0, -0.42, -0.68], [1.60, 1.30, 1.18], "#d8b06a", anchor=[0, 0, 0],
              decal="ea_wicker", wrap=True),
        part("torus", [0, 0.33, -0.68], [1.58, 0.7, 1.16], "#b88a4a", decal="ea_wicker", wrap=True),
        place("arch", [0, 0.34, -0.68], [1.30, 1.15, 1.0], "#b88a4a", anchor=[0, 0, 0],
              decal="ea_wicker", wrap=True),
        *straps("#b88a4a", 0.36, 0.13),
        part("rbox", [0, 0.40, -0.08], [0.20, 0.12, 0.10], "#8a6a3a"),
    ]
    # paper grass heaped up, and the eggs on top of it
    for n in range(14):
        a = n * TAU / 14
        parts.append(place("leaf", [math.sin(a) * 0.52, 0.30, -0.68 + math.cos(a) * 0.36],
                           [0.45, 0.40, 0.5], [GRASS, "#b5e88a", "#ffc4e1"][n % 3],
                           anchor=[0, -0.5, 0], r=[0.45, a, 0]))
    for (x, z, c, s, tilt) in ((-0.30, -0.58, PINK, 0.36, 0.3), (0.24, -0.78, SKYBLUE, 0.38, -0.3),
                               (0.02, -0.46, BUTTER, 0.34, 0.1), (-0.14, -0.90, MINT, 0.36, 0.5),
                               (0.42, -0.52, LILAC, 0.32, -0.6)):
        parts += at_frame(_egg(s, c, bands=[(0.42, 0.52, CREAM)], dots=(0.72, 4, WHITE, 0.10)),
                          [x, 0.22, z], r=[0.2, 0, tilt])
    return parts


@EA22.back("butterfly_wings", "Pastel Butterfly Wings",
           "Four wings in sugared-almond colours, spotted like a painted egg, and they "
           "flutter when you run. Caterpillars are very jealous.", "uncommon")
def _():
    parts = [part("capsule", [0, 0.42, -0.20], [0.14, 0.80, 0.14], "#4a3a5a")]
    for side in (1, -1):
        parts += [
            place("heart", [0.74 * side, 0.86, -0.34], [1.36, 1.36, 0.5], "#d2b6ff",
                  r=[0.15, 0.35 * side, -0.785 * side]),
            place("heart", [0.54 * side, 0.02, -0.28], [0.92, 0.92, 0.5], "#ffbfdf",
                  r=[0.15, 0.35 * side, -2.36 * side]),
            part("sph", [0.86 * side, 1.00, -0.42], [0.32, 0.32, 0.05], BUTTER,
                 [0.15, 0.35 * side, 0]),
            part("sph", [0.60 * side, -0.06, -0.35], [0.22, 0.22, 0.05], WHITE,
                 [0.15, 0.35 * side, 0]),
            part("cyl", [0.10 * side, 1.00, -0.20], [0.03, 0.44, 0.03], "#4a3a5a",
                 [0, 0, -0.5 * side]),
            part("sph", [0.21 * side, 1.20, -0.20], [0.08, 0.08, 0.08], "#4a3a5a"),
        ]
    return parts


@EA22.hairdo("pastel_pigtails", "Pastel Pigtails",
             "Candyfloss pink, in two bunches tied off with little painted-egg bobbles.",
             "uncommon")
def _():
    c = "#f2a7c8"
    parts = [place("hairmid", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for side in (1, -1):
        parts += [
            place("teardrop", [0.60 * side, 0.14, -0.14], [0.38, 0.70, 0.38], c,
                  anchor=[0, 1.0, 0], r=[0, 0, 0.85 * side], decal="strands", wrap=True),
            *at_frame(_egg(0.12, BUTTER if side > 0 else MINT, bands=[(0.40, 0.55, WHITE)]),
                      [0.56 * side, 0.13, -0.14], r=[0, 0, -PI / 2 * side]),
        ]
    return parts


@EA22.hairdo("bobbed_bow", "Sunday Best Bob",
             "A neat lilac bob with a fringe, a big pink bow and a hair clip shaped like "
             "a fried egg. It was a long morning.", "rare")
def _():
    c = "#b89ae0"
    return [
        place("hairbob", [0, 0, 0], [1.05, 1.05, 1.05], c, anchor=[0, 0, 0],
              decal="strands", wrap=True),
        place("bowtie", [0.30, 0.50, 0.12], [0.44, 0.44, 0.9], PINK, r=[-0.6, 0.6, 0.3]),
        part("sph", [0.31, 0.51, 0.14], [0.11, 0.11, 0.10], "#ff7ab8", [-0.6, 0.6, 0.3]),
        # the fried egg clip, over the other ear
        part("cyl", [-0.585, 0.12, 0.16], [0.24, 0.03, 0.21], WHITE, [0, 0, PI / 2 - 0.15]),
        part("sph", [-0.605, 0.12, 0.16], [0.06, 0.10, 0.10], "#ffc21a", [0, 0, -0.15]),
    ]


EA22.face("egg_cited", "Egg-cited",
          "Eyes like saucers and a grin that will not quit. Somebody found the golden "
          "egg. It was not you, but you are happy for them. Mostly.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.17, "h": 0.20, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.17, "h": 0.20, "c": "#16171b"},
              {"k": "ellipse", "x": -0.23, "y": -0.17, "w": 0.06, "h": 0.07, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.17, "y": -0.17, "w": 0.06, "h": 0.07, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.17, "y": -0.08, "w": 0.03, "h": 0.03, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.23, "y": -0.08, "w": 0.03, "h": 0.03, "c": "#ffffff"},
              {"k": "poly", "pts": [[-0.20, 0.06], [0.20, 0.06], [0.14, 0.20], [0.0, 0.25],
                                    [-0.14, 0.20]], "c": "#16171b"},
              {"k": "ellipse", "x": 0.0, "y": 0.18, "w": 0.14, "h": 0.06, "c": "#ff7a9a"},
              {"k": "ellipse", "x": -0.33, "y": 0.04, "w": 0.09, "h": 0.05, "c": "#ffa8c8"},
              {"k": "ellipse", "x": 0.33, "y": 0.04, "w": 0.09, "h": 0.05, "c": "#ffa8c8"},
          ], "uncommon")
EA22.face("sunny_side_up", "Sunny Side Up",
          "Two eggs, fried, where the eyes go, and a satisfied smile. Breakfast is the "
          "most important face of the day.", [
              {"k": "poly", "pts": [[-0.34, -0.14], [-0.30, -0.24], [-0.20, -0.27], [-0.10, -0.22],
                                    [-0.06, -0.12], [-0.11, -0.03], [-0.22, -0.01], [-0.31, -0.05]],
               "c": "#fffaf0"},
              {"k": "poly", "pts": [[0.06, -0.15], [0.11, -0.24], [0.22, -0.28], [0.32, -0.21],
                                    [0.35, -0.12], [0.30, -0.03], [0.18, -0.01], [0.09, -0.06]],
               "c": "#fffaf0"},
              {"k": "ellipse", "x": -0.20, "y": -0.14, "w": 0.10, "h": 0.10, "c": "#ffb81a"},
              {"k": "ellipse", "x": 0.21, "y": -0.14, "w": 0.10, "h": 0.10, "c": "#ffb81a"},
              {"k": "ellipse", "x": -0.22, "y": -0.16, "w": 0.03, "h": 0.03, "c": "#fff3c0"},
              {"k": "ellipse", "x": 0.19, "y": -0.16, "w": 0.03, "h": 0.03, "c": "#fff3c0"},
              {"k": "arc", "x": 0, "y": 0.04, "r": 0.15, "a0": 0.08, "a1": 0.42, "w": 0.035,
               "c": "#16171b"},
          ], "rare")
EA22.shirt("hunt_marshal", "Hunt Marshal's Polo",
           "Mint green, a pink trim, and the badge that lets you say 'that one is mine, I "
           "saw it first' with real authority.",
           {"torso": "#9fe3c8", "arms": "#9fe3c8", "decal": "ea_tee_marshal",
            "stripe": "#ff9cc9", "sleeves": 0.45}, "rare")
EA22.pants("zigzag_dungarees", "Zig-Zag Dungarees",
           "Lilac, with a crack of every pastel running round and round. Hard to lose "
           "in a hedge.", {"legs": "#c7a8f0", "weave": "ea_zigzag"})
EA22.belt("egg_pouches", "Egg Hunter's Belt",
          "Gingham, with two padded pouches on the front for carrying eggs. They are "
          "padded for a reason. Ask about the first one.",
          {"band": "#ff9cc9", "buckle": "#fff3b0", "width": 0.22, "weave": "ea_gingham",
           "pouch": True})


@EA22.weapon("clutch_launcher", "Clutch Launcher",
             "A painted tube that lobs a whole clutch of eggs in one shell. A moment out "
             "of the barrel the shell cracks, and four eggs fan out across the field.",
             {"kind": "projectile", "projectile": "egg", "damage": 22, "splash": 3.6,
              "splash_damage": 18, "rpm": 54, "mag": 4, "reload": 2.4, "speed": 64,
              "range": 280, "auto": False, "sound": "pop", "recoil": 1.8, "reserve": 24,
              "gravity_scale": 0.9, "self_damage": 0.0, "knockback": 7,
              "split": {"after": 0.30, "count": 4, "spread": 9, "damage": 15,
                        "splash_damage": 14}},
             [["+", "The shell cracks a moment out of the barrel into four eggs that fan "
                    "out side by side"],
              ["+", "Your own eggs cannot hurt you"],
              ["-", "Each egg is small: 15 on a hit, a 3.6 stud splash"],
              ["-", "Up close, the shell has not cracked yet"]], rarity="legendary",
             proj=lambda: at_frame(_egg(0.42, LILAC, bands=[(0.30, 0.40, MINT)],
                                        zig=(0.52, 0.64, BUTTER)),
                                   [0, 0, -0.28], r=[PI / 2, 0, 0]))
def _():
    tube = "#c7a8f0"
    parts = [
        part("cyl", [0, 0.08, 0.50], [0.40, 1.30, 0.40], tube, [PI / 2, 0, 0],
             decal="ea_eggdots", wrap=True),
        part("torus", [0, 0.08, 1.14], [0.48, 0.5, 0.48], PINK, [PI / 2, 0, 0]),
        part("torus", [0, 0.08, -0.12], [0.46, 0.5, 0.46], MINT, [PI / 2, 0, 0]),
        part("rbox", [0, -0.22, 0.02], [0.16, 0.46, 0.22], "#7a5aa8", [-0.25, 0, 0]),
        part("rbox", [0, -0.10, 0.50], [0.14, 0.30, 0.20], "#7a5aa8", [0.3, 0, 0]),
        # the ammunition: a half-dozen box clipped on top
        part("rbox", [0, 0.40, 0.30], [0.30, 0.14, 0.50], CREAM),
    ]
    for n in range(3):
        parts.append(part("sph", [0, 0.50, 0.14 + n * 0.16], [0.13, 0.15, 0.13],
                          [PINK, BUTTER, SKYBLUE][n]))
    # an egg peeking out of the muzzle
    parts += at_frame(_egg(0.30, BUTTER, bands=[(0.40, 0.50, PINK)]), [0, 0.08, 1.06],
                      r=[PI / 2, 0, 0])
    return parts


@EA22.weapon("dye_hard", "Dye Hard",
             "A wire dipper and a bucket of eggs blown hollow and filled with dye. Whoever "
             "is splashed cannot see for the paint, and everyone else can see them a mile "
             "off.",
             {"kind": "projectile", "projectile": "paintegg", "damage": 8, "splash": 5.5,
              "splash_damage": 10, "rpm": 46, "mag": 2, "reload": 2.2, "speed": 58,
              "range": 220, "auto": False, "sound": "throw", "recoil": 0.8, "reserve": 20,
              "gravity_scale": 1.3, "self_damage": 0.0, "knockback": 3,
              "on_hit": {"blind": [1.8, "confetti"], "mark": [0.20, 4.0]}},
             [["+", "Everyone in the splash is blinded by dye for 1.8 seconds"],
              ["+", "...and marked: they take 20% more damage from everybody for 4 seconds"],
              ["-", "Barely hurts: 10 at the most"],
              ["-", "Two eggs, then a reload"]], rarity="legendary",
             proj=lambda: at_frame(_egg(0.40, WHITE, bands=[(0.0, 0.34, "#ff7ab8"),
                                                            (0.34, 0.62, "#6ab8ff")]),
                                   [0, 0, -0.26], r=[PI / 2, 0, 0]))
def _():
    wire = SILVER
    parts = [
        part("cyl", [0, 0.0, 0.55], [0.07, 1.70, 0.07], wire, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.0, -0.20], [0.18, 0.56, 0.18], "#ff9cc9", [PI / 2, 0, 0]),
        part("torus", [0, 0.0, -0.50], [0.20, 0.4, 0.20], "#ff7ab8", [PI / 2, 0, 0]),
        part("torus", [0, 0.0, 1.62], [0.62, 0.3, 0.62], wire, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.0, 1.62], [0.62, 0.3, 0.62], wire, [PI / 2, PI / 2, 0], m="metal"),
    ]
    # the dyed egg in the dipper's cradle, dripping
    parts += at_frame(_egg(0.44, WHITE, bands=[(0.0, 0.36, "#ff7ab8"), (0.36, 0.64, "#6ab8ff")]),
                      [0, -0.24, 1.62])
    parts += [place("teardrop", [0.08, -0.38, 1.62], [0.10, 0.18, 0.10], "#ff7ab8",
                    r=[PI, 0, 0], m="glass"),
              place("teardrop", [-0.10, -0.32, 1.58], [0.08, 0.14, 0.08], "#6ab8ff",
                    r=[PI, 0, 0], m="glass")]
    return parts


@EA22.weapon("balloon_whisk", "Balloon Whisk",
             "The big whisk from the bake-off tent. It does not hit hard, but keep "
             "whisking and it whips up a froth that hits harder with every stroke.",
             {"kind": "melee", "damage": 17, "headshot": 1.0, "rpm": 160, "range": 9.5,
              "arc": 0.62, "sound": "swing", "knockback": 4,
              "combo": {"window": 1.2, "step": 0.15, "max": 0.75, "label": "Froth"}},
             [["+", "Every hit within 1.2 seconds of the last whips up 15% more damage, "
                    "up to +75%"],
              ["+", "Very quick: 160 strokes a minute"],
              ["-", "Starts out feeble: 17 damage"],
              ["-", "Miss, or stop for breath, and the froth goes flat"]], rarity="legendary")
def _():
    wire = "#dfe4ea"
    parts = [
        part("cyl", [0, 0.0, 0.0], [0.20, 0.80, 0.20], PINK, [PI / 2, 0, 0]),
        part("cyl", [0, 0.0, 0.44], [0.13, 0.14, 0.13], wire, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.0, -0.46], [0.18, 0.4, 0.18], wire, [0, 0, PI / 2], m="metal"),
    ]
    # the balloon of wires: half-loops standing round the axis
    for n in range(5):
        a = n * PI / 5
        parts.append(place("arch", [0, 0.0, 0.48], [0.80, 2.40, 1.4], wire, anchor=[0, 0, 0],
                           r=_euler(("y", a), ("x", PI / 2)), m="metal"))
    parts.append(part("sph", [0, 0.0, 1.70], [0.22, 0.22, 0.22], CREAM, a=0.7))
    return parts


@EA22.weapon("hunt_basket_toss", "Egg Hunt Basket",
           "A little basket of painted eggs, thrown underarm. It tips out where it lands "
           "and the eggs roll about for your team to find -- each one a bite of chocolate "
           "in a painted shell.",
           {"kind": "projectile", "projectile": "basket", "damage": 0, "splash": 0,
            "splash_damage": 0, "rpm": 30, "mag": 1, "reload": 20.0, "speed": 40,
            "range": 120, "auto": False, "sound": "throw", "recoil": 0.4, "reserve": 30,
            "gravity_scale": 1.4, "self_damage": 0.0, "knockback": 0, "held_item": True,
            "pickups": {"count": 5, "spread": 6.0, "heal": 15, "haste": [0.15, 3.0],
                        "secs": 15.0, "radius": 3.0, "color": "#ff9cc9"}},
           [["+", "Spills five eggs where it lands; each heals whoever of your team finds "
                  "it 15, with a quick burst of speed"],
            ["+", "Lobs well over cover"],
            ["-", "Takes 20 seconds to fill a new basket"],
            ["-", "The eggs only keep for 15 seconds"]], rarity="rare", grade="",
             proj=lambda: [place("bowl", [0, -0.2, 0], [0.9, 0.7, 0.9], "#d8b06a", anchor=[0, 0, 0],
                                 decal="ea_wicker", wrap=True),
                           place("arch", [0, 0.2, 0], [0.8, 1.1, 1.0], "#b88a4a", anchor=[0, 0, 0],
                                 r=[0, PI / 2, 0]),
                           part("sph", [0.1, 0.18, 0.05], [0.24, 0.30, 0.24], PINK),
                           part("sph", [-0.12, 0.16, -0.06], [0.24, 0.30, 0.24], SKYBLUE)])
def _():
    parts = [
        place("bowl", [0, -0.30, 0.42], [0.90, 0.72, 0.84], "#d8b06a", anchor=[0, 0, 0],
              decal="ea_wicker", wrap=True),
        part("torus", [0, 0.12, 0.42], [0.90, 0.5, 0.84], "#b88a4a"),
        place("arch", [0, 0.14, 0.42], [0.72, 1.10, 0.8], "#b88a4a", anchor=[0, 0, 0],
              r=[0, PI / 2, 0]),
    ]
    for (x, z, c) in ((-0.14, 0.34, PINK), (0.14, 0.52, SKYBLUE), (0.0, 0.42, BUTTER),
                      (0.16, 0.28, MINT)):
        parts += at_frame(_egg(0.22, c, bands=[(0.42, 0.55, WHITE)]), [x, -0.02, z],
                          r=[0.25, 0, x * 2])
    # carried by the handle: the hand closes round the top of the arch
    return at_frame(parts, [0, -0.72, -0.42])


EA22.effect("painted_parade", name="Painted Parade", rate=2.8, life=[2.2, 3.0],
            size=[0.26, 0.38], grow=0.0, gravity=0.0, spread=0.15, rise=[0.05, 0.2],
            blend="normal", spin=0.4, colors=["#ff9cc9", "#c7a8f0", "#8fe3c0", "#ffe58a"],
            shape="egg", radius=0.86, orbit=1.2, upright=True, wobble=0.35)
EA22.effect("spring_shower", name="Spring Shower", rate=6.0, life=[1.8, 2.6],
            size=[0.18, 0.30], grow=0.0, gravity=0.5, spread=0.8, rise=[0.6, 1.0],
            blend="normal", spin=2.0, colors=["#ffb3d8", "#fff3b0", "#c7a8f0", "#ffffff"],
            shapes=["flower", "flower", "butterfly"], radius=0.7, wobble=0.5)
EA22.opening(
    sky={"top": "#6fbaf0", "horizon": "#ffe3f1", "sun": [0.3, 0.8, 0.5], "clouds": 0,
         "tint": "#fff4fb"},
    ambient="#e8dcff", beam="#fff0a8", seep="painted_parade", after="spring_shower",
    burst=["#ff9cc9", "#c7a8f0", "#8fe3c0", "#ffe58a", "#ffffff"],
    pieces=[{"shape": "egg", "colors": ["#ff9cc9", "#c7a8f0", "#8fe3c0", "#ffe58a", "#9fd4ff"],
             "blend": "normal"},
            {"shape": "flower", "colors": ["#ffb3d8", "#fff3b0", "#ffffff"], "blend": "normal"},
            {"shape": "confetti", "colors": ["#ff9cc9", "#8fe3c0", "#ffe58a"], "blend": "normal"},
            {"shape": "star", "colors": ["#fff0a8", "#ffffff"], "blend": "add"}],
    backdrop="ea_eggfair", title_wait="Somebody is checking under the bandstand...",
    title_shake="Found one!")
EA22.award("Eggstravaganza", ["Egg Spotter", "Basket Carrier", "Dye Dipper", "Hunt Marshal",
                              "Golden Yolk", "Grand Eggsplorer"],
           "Opened Eggstravaganza Eggs during Blockhaven's first Easter, 2022.", "em_egg", "egg")
EA22.bundle("pair", "Egg and Key", 1, 1050, "One Eggstravaganza Egg, one Painted Egg Key.")
EA22.bundle("clutch", "A Clutch of Three", 3, 3000, "Three eggs, three keys. Saves 300.")


EVENTS = [EA22]
