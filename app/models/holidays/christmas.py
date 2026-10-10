"""Christmas: snow on everything, and a crate under every tree.

  2022  Frostfall             the first snow: a snow globe, cocoa, sledges and snowmen
  2023  Gingerbread Junction  the gingerbread railway: a cookie tin, candy canes, icing
  2024  North Pole Express    the overnight mail train: a coal tender, steam and parcels
  2025  Krampusnacht          Santa's dark companion comes calling with a basket
  2026  Aurora Winterlight    the northern lights over the pole -- waiting for December

Every December from the first to the thirtieth.  2026 is on the calendar but
has not started yet; its crate is built and boxed like the others, so the
shop can show it coming.
"""
from __future__ import annotations

import math

from .kit import (BLACK, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, gift_bow, mix, part,
                  place, pompom, ringband, rotate, shade, sides, straps)

# the colours every year shares
BERRY = "#d0141c"
HOLLY = "#1e7a36"
COAL = "#1e1f24"
CARROT = "#ff8a1f"
SNOWBALL = "#f7fbff"
ICE = "#dff4ff"
CANDY_RED = "#d62828"


def _frame(facing):
    """A little local frame for a figure facing yaw ``facing``: offsets are
    (side, up, forward)."""
    fwd = (math.sin(facing), math.cos(facing))
    side = (math.cos(facing), -math.sin(facing))

    def off(at, dx, dy, dz):
        return [at[0] + side[0] * dx + fwd[0] * dz, at[1] + dy, at[2] + side[1] * dx + fwd[1] * dz]
    return off


def _snowman(at, k=1.0, facing=0.0, scarf=CANDY_RED, hat=True, arms=True, wave=False):
    """A snowman standing on ``at`` (the bottom of its lowest ball), facing
    yaw ``facing``: three balls of snow, coal eyes and buttons, a carrot nose,
    a scarf, stick arms and a little top hat."""
    off = _frame(facing)
    out = [
        part("sph", off(at, 0, 0.40 * k, 0), [0.80 * k, 0.76 * k, 0.80 * k], SNOWBALL,
             decal="xm_snow", wrap=True),
        part("sph", off(at, 0, 0.98 * k, 0), [0.60 * k, 0.56 * k, 0.60 * k], SNOWBALL,
             decal="xm_snow", wrap=True),
        part("sph", off(at, 0, 1.42 * k, 0), [0.46 * k, 0.44 * k, 0.46 * k], SNOWBALL,
             decal="xm_snow", wrap=True),
        # the scarf, round the neck, a tail down the front
        part("cyl", off(at, 0, 1.22 * k, 0), [0.50 * k, 0.10 * k, 0.50 * k], scarf,
             decal="knit", wrap=True),
        part("rbox", off(at, 0.12 * k, 1.08 * k, 0.24 * k), [0.10 * k, 0.26 * k, 0.04 * k], scarf,
             [0.25, facing, -0.15], decal="knit"),
        # carrot nose and coal
        place("carrot", off(at, 0, 1.42 * k, 0.20 * k), [0.08 * k, 0.24 * k, 0.08 * k], CARROT,
              anchor=[0, 1, 0], r=[-PI / 2 + 0.1, facing, 0]),
    ]
    for s in (1, -1):
        out.append(part("sph", off(at, 0.08 * k * s, 1.50 * k, 0.19 * k),
                        [0.06 * k, 0.06 * k, 0.04 * k], COAL))
    for n in range(3):
        out.append(part("sph", off(at, 0, (0.84 + n * 0.14) * k, 0.29 * k - abs(n - 1) * 0.01 * k),
                        [0.07 * k, 0.07 * k, 0.04 * k], COAL))
    if hat:
        out += [part("cyl", off(at, 0, 1.63 * k, 0), [0.40 * k, 0.03 * k, 0.40 * k], COAL),
                part("cyl", off(at, 0, 1.76 * k, 0), [0.26 * k, 0.24 * k, 0.26 * k], COAL),
                part("cyl", off(at, 0, 1.68 * k, 0), [0.27 * k, 0.05 * k, 0.27 * k], scarf)]
    if arms:
        for s in (1, -1):
            lift = 0.9 if (wave and s > 0) else 0.35
            out.append(part("cyl", off(at, 0.42 * k * s, (1.02 + (0.18 if lift > 0.5 else 0.04)) * k, 0),
                            [0.035 * k, 0.48 * k, 0.035 * k], "#5a3a22",
                            [0, facing, -s * (PI / 2 - lift)]))
    return out


def _mug(at, k=1.0, body="#f4f6f8", cocoa="#5a3020", handle_side=1, steam=True, lid=None):
    """A mug of hot cocoa: a printed mug, a handle, cocoa, marshmallows, a
    swirl of cream and the steam coming off it.  ``at`` is the bottom."""
    x, y, z = at
    out = [
        part("cyl", [x, y + 0.40 * k, z], [0.78 * k, 0.80 * k, 0.78 * k], body,
             decal="xm_mug", wrap=True),
        part("torus", [x, y + 0.80 * k, z], [0.80 * k, 0.40 * k, 0.80 * k], body),
        part("cyl", [x, y + 0.74 * k, z], [0.66 * k, 0.04 * k, 0.66 * k], cocoa),
        part("torus", [x + 0.40 * k * handle_side, y + 0.42 * k, z], [0.46 * k, 0.70 * k, 0.46 * k],
             body, [PI / 2, 0, 0]),
        part("sph", [x, y + 0.80 * k, z], [0.44 * k, 0.20 * k, 0.44 * k], WHITE),
        place("spiral", [x, y + 0.84 * k, z], [0.22 * k, 0.16 * k, 0.22 * k], WHITE),
        part("sph", [x, y + 0.96 * k, z], [0.10 * k, 0.10 * k, 0.10 * k], WHITE),
    ]
    for n, (dx, dz, turn) in enumerate(((0.22, 0.10, 0.3), (-0.20, 0.14, 1.1), (0.04, -0.22, 0.7))):
        out.append(part("rbox", [x + dx * k, y + 0.80 * k, z + dz * k], [0.13 * k, 0.11 * k, 0.13 * k],
                        "#fff6f0", [0.2, turn, 0.1]))
    if steam:
        for n, (dx, h) in enumerate(((-0.12, 0.30), (0.10, 0.40), (0.0, 0.26))):
            out.append(place("teardrop", [x + dx * k, y + (1.10 + n * 0.14) * k, z - 0.06 * k],
                             [0.12 * k, h * k, 0.12 * k], "#ffffff", a=0.35))
    if lid:
        for p in out:
            p["lid"] = 1
    return out


def _holly(at, k=1.0, yaw=0.0, berries=3):
    """A sprig of holly: two leaves and a cluster of berries, lying flat-ish."""
    x, y, z = at
    out = [place("holly", [x - 0.16 * k * math.cos(yaw), y, z + 0.16 * k * math.sin(yaw)],
                 [0.40 * k, 0.40 * k, 0.6 * k], HOLLY, r=[0, yaw, 0.5]),
           place("holly", [x + 0.16 * k * math.cos(yaw), y, z - 0.16 * k * math.sin(yaw)],
                 [0.40 * k, 0.40 * k, 0.6 * k], "#2a9446", r=[0, yaw, -0.5])]
    for n in range(berries):
        a = n * TAU / max(1, berries)
        out.append(part("sph", [x + math.sin(a) * 0.05 * k, y + 0.04 * k + math.cos(a) * 0.04 * k,
                                z + 0.05 * k], [0.09 * k, 0.09 * k, 0.09 * k], BERRY, m="glass"))
    return out


# ============================================================ 2022
FROST = "#8fd0ff"
NIGHT_BLUE = "#13264a"
LACQUER = "#9a1b22"
XM22 = Event(
    "christmas_2022", "christmas", 2022, "xm22",
    name="Frostfall", title="Frostfall",
    blurb="December 2022 brought Blockhaven its very first snow. It started on the "
          "first, did not stop until the thirtieth, and buried the Relay up to its "
          "antennas. Somebody built a snowman on the spawn pad. Nobody has had the "
          "heart to knock it down.",
    tagline="It's snowing. It's actually snowing!",
    starts="2022-12-01", ends="2022-12-30",
    colors={"accent": FROST, "deep": "#0c1830", "glow": "#e8f6ff"},
    family_effects=["frostbite", "starstruck", "candlelight_vigil"],
    hero_effect="snowglobe_swirl", stencil="stencil_xm22")


@XM22.crate_model("Snow Globe Crate",
                  "A snow globe the size of a crate: a lacquered music-box base, a "
                  "winding key, and under the glass a tiny Blockhaven in its very first "
                  "snow. The glass lifts. The snow keeps falling anyway. Holds the "
                  "Frostfall set. Needs a Snowflake Key.",
                  hinge=[0, -0.04, -0.70], keyhole=[0, -0.40, 0.86])
def _():
    wood = "#4a2814"
    parts = [
        # the music-box plinth: a dark wood foot, the red lacquer drum, gilt rims
        part("cyl", [0, -0.74, 0], [1.76, 0.16, 1.76], wood, decal="planks", wrap=True),
        part("cyl", [0, -0.40, 0], [1.60, 0.54, 1.60], LACQUER, decal="xm_giltscroll",
             wrap=True),
        part("cyl", [0, -0.665, 0], [1.66, 0.05, 1.66], GOLD, m="metal"),
        part("cyl", [0, -0.135, 0], [1.66, 0.05, 1.66], GOLD, m="metal"),
        part("cyl", [0, -0.08, 0], [1.46, 0.08, 1.46], wood),
        # the scene under the glass: a drift of snow, a pine with a star, a
        # snowman, and a cabin with its lamp lit
        place("hemi", [0, -0.05, 0], [1.30, 0.30, 1.30], SNOWBALL, anchor=[0, 0, 0],
              decal="xm_snow", wrap=True),
        place("tree", [-0.32, 0.02, -0.12], [0.44, 0.70, 0.44], "#2f6a3e", anchor=[0, 0, 0]),
        place("tree", [-0.32, 0.30, -0.12], [0.30, 0.36, 0.30], SNOWBALL, anchor=[0, 0, 0]),
        place("star", [-0.32, 0.76, -0.12], 0.14, GOLD, m="neon"),
        part("rbox", [0.14, 0.13, -0.34], [0.36, 0.24, 0.26], "#6a3a1e", decal="planks"),
        part("wedge", [0.14, 0.31, -0.40], [0.42, 0.14, 0.15], SNOWBALL, [0, PI, 0]),
        part("wedge", [0.14, 0.31, -0.28], [0.42, 0.14, 0.15], SNOWBALL),
        part("box", [0.14, 0.12, -0.205], [0.10, 0.10, 0.01], "#ffd36a", m="neon"),
        # the glass, and the snow caught in it (the glass is the lid)
        part("sph", [0, 0.58, 0], [1.36, 1.36, 1.36], "#e8f6ff", m="glass", a=0.2, lid=1),
        part("torus", [0, -0.02, 0], [1.42, 0.40, 1.42], GOLD, m="metal", lid=1),
        # the lock on the front of the drum, the winding key on its side
        part("rbox", [0, -0.40, 0.80], [0.36, 0.34, 0.08], BRASS, m="metal", decal="keyhole",
             lock=1),
        part("cyl", [0.86, -0.40, 0], [0.08, 0.16, 0.08], GOLD, [0, 0, PI / 2], m="metal"),
        part("torus", [0.98, -0.31, 0], [0.22, 0.30, 0.22], GOLD, [0, 0, PI / 2], m="metal"),
        part("torus", [0.98, -0.49, 0], [0.22, 0.30, 0.22], GOLD, [0, 0, PI / 2], m="metal"),
        part("sph", [0.97, -0.40, 0], [0.09, 0.09, 0.09], GOLD, m="metal"),
        # a brass plaque on the back with the year's stencil
        part("rbox", [0, -0.40, -0.80], [0.66, 0.42, 0.05], BRASS, m="metal"),
        part("box", [0, -0.40, -0.83], [0.58, 0.38, 0.02], "#000000", [0, PI, 0],
             decal="stencil_xm22", a=-1),
    ]
    parts += _snowman([0.30, 0.04, 0.16], 0.36, facing=0.25)
    parts += _holly([-0.48, -0.16, 0.70], 0.7, yaw=0.2)
    parts += _holly([0.48, -0.16, 0.70], 0.7, yaw=-0.2)
    # snow in the water: flakes and specks, which go up with the glass
    for n in range(18):
        a = n * 2.39996
        rr = 0.18 + (n * 37 % 10) / 10 * 0.36
        y = 0.30 + (n * 53 % 17) / 17 * 0.72
        p = [math.sin(a) * rr, y, math.cos(a) * rr]
        if n % 3 == 0:
            parts.append(place("snowflake", p, 0.12, "#ffffff", r=[0.3 * n, a, 0], lid=1))
        else:
            parts.append(part("sph", p, [0.05, 0.05, 0.05], "#ffffff", lid=1))
    return parts


@XM22.key_model("Snowflake Key",
                "A silver key whose bow is a snowflake that never melts, with two "
                "icicles for teeth. Opens one Snow Globe Crate, and is cold to the "
                "touch for a week afterwards.", shoulder=-0.30)
def _():
    silver = "#cfe3f2"
    return [
        place("snowflake", [-0.64, 0, 0], 0.66, silver, m="metal"),
        part("sph", [-0.64, 0, 0.02], [0.16, 0.16, 0.10], FROST, m="glass"),
        part("torus", [-0.30, 0, 0], [0.20, 0.40, 0.20], "#9fc4e0", [0, 0, PI / 2], m="metal"),
        part("cyl", [0.12, 0, 0], [0.09, 0.90, 0.09], silver, [0, 0, PI / 2], m="metal"),
        place("icicle", [0.40, -0.03, 0], [0.13, 0.26, 0.13], ICE, anchor=[0, 1, 0], m="glass"),
        place("icicle", [0.54, -0.03, 0], [0.13, 0.36, 0.13], ICE, anchor=[0, 1, 0], m="glass"),
        part("sph", [0.58, 0, 0], [0.11, 0.11, 0.11], silver, m="metal"),
    ]


@XM22.hat("globe_helmet", "Snowed In",
          "Your very own snow globe, worn: a glass bubble on a music-box collar, and a "
          "pine and a snowman stood on your head inside it while the snow comes down "
          "forever. Please do not shake the wearer.", "legendary")
def _():
    glass = "#e8f6ff"
    parts = [
        part("sph", [0, -0.45, 0], [2.24, 2.42, 2.20], glass, m="glass", a=0.16),
        # the collar it stands on, lacquered, gilt, with its winding key behind
        place("ring", [0, -1.36, 0], [1.98, 0.62, 1.94], LACQUER, anchor=[0, 0, 0],
              decal="xm_giltscroll", wrap=True),
        part("torus", [0, -1.23, 0], [2.00, 0.30, 1.96], GOLD, m="metal"),
        part("cyl", [0, -1.30, -1.02], [0.07, 0.14, 0.07], GOLD, [PI / 2, 0, 0], m="metal"),
        part("torus", [0.09, -1.30, -1.10], [0.18, 0.30, 0.18], GOLD, [PI / 2, 0, PI / 2],
             m="metal"),
        part("torus", [-0.09, -1.30, -1.10], [0.18, 0.30, 0.18], GOLD, [PI / 2, 0, PI / 2],
             m="metal"),
        # snow on the crown of the head, and the scene stood on it
        part("rbox", [0, 0.03, 0], [1.30, 0.10, 1.24], SNOWBALL, decal="xm_snow", wrap=True),
        place("hemi", [0.05, 0.04, -0.05], [1.0, 0.36, 0.9], SNOWBALL, anchor=[0, 0, 0],
              decal="xm_snow", wrap=True),
        place("tree", [-0.30, 0.10, -0.18], [0.44, 0.62, 0.44], "#2f6a3e", anchor=[0, 0, 0]),
        place("tree", [-0.30, 0.34, -0.18], [0.30, 0.32, 0.30], SNOWBALL, anchor=[0, 0, 0]),
        place("star", [-0.30, 0.78, -0.18], 0.12, GOLD, m="neon"),
    ]
    parts += _snowman([0.28, 0.10, 0.18], 0.34, facing=0.3, wave=True)
    # flakes caught in the glass all round
    for n in range(16):
        a = n * 2.39996
        y = -0.95 + (n * 41 % 16) / 16 * 1.55
        rr = 1.0 if y < 0.0 else 0.35 + (n % 4) * 0.12
        parts.append(place("snowflake", [math.sin(a) * rr, y, math.cos(a) * rr * 0.98],
                           0.10 + (n % 3) * 0.02, "#ffffff", r=[0.4 * n, a, 0]))
    return parts


@XM22.hat("snowman_head", "Snowman Head",
          "A whole snowman's head, coal, carrot and all, pulled down over your own. "
          "It is warmer in there than you would think. The carrot is load-bearing.",
          "rare", hair="hide", face_cover=True)
def _():
    shell = dome(-0.62, 1.10, SNOWBALL, decal="xm_snow", wrap=True)
    w = shell["s"][0]
    parts = [
        shell,
        part("cyl", [0, -0.95, 0], [w, 0.66, w * 0.97], SNOWBALL, decal="xm_snow", wrap=True),
        part("torus", [0, -1.26, 0], [w * 1.02, 1.0, w * 0.99], SNOWBALL, decal="xm_snow",
             wrap=True),
        # a knitted scarf, the tails hanging off to one side
        part("cyl", [0, -1.06, 0], [w + 0.10, 0.26, w * 0.97 + 0.10], "#c4281c", decal="knit",
             wrap=True),
        part("rbox", [0.46, -1.30, 0.92], [0.22, 0.56, 0.08], "#c4281c", [0.15, 0.4, 0.15],
             decal="knit"),
        part("rbox", [0.62, -1.24, 0.84], [0.22, 0.44, 0.08], "#2a8a4a", [0.10, 0.6, 0.35],
             decal="knit"),
        # coal eyes, a carrot, a coal smile
        part("sph", [0.24, -0.24, 0.90], [0.18, 0.18, 0.10], COAL),
        part("sph", [-0.24, -0.24, 0.90], [0.18, 0.18, 0.10], COAL),
        place("carrot", [0, -0.46, 0.94], [0.18, 0.56, 0.18], CARROT, anchor=[0, 1, 0],
              r=[-PI / 2 + 0.12, 0.10, 0]),
        # a battered top hat with a sprig of holly
        part("cyl", [0.10, 0.48, -0.05], [1.00, 0.05, 0.96], COAL, [0, 0, -0.12]),
        part("cyl", [0.13, 0.78, -0.05], [0.66, 0.56, 0.64], COAL, [0, 0, -0.12], decal="felt",
             wrap=True),
        part("cyl", [0.11, 0.58, -0.05], [0.68, 0.12, 0.66], "#c4281c", [0, 0, -0.12]),
    ]
    for n, x in enumerate((-0.30, -0.15, 0.0, 0.15, 0.30)):
        parts.append(part("sph", [x, -0.70 + abs(x) * -0.25 + 0.08, 0.96], [0.10, 0.10, 0.07], COAL))
    parts += _holly([-0.28, 0.62, 0.30], 0.55, yaw=0.3)
    return parts


@XM22.hat("earmuffs", "Fluffy Earmuffs",
          "Two clouds of white fluff on a red band, and a snowflake on each. You "
          "will not hear a single snowball coming.", "uncommon", hair="show")
def _():
    red = "#c4281c"
    parts = [
        part("rbox", [0, 0.05, 0], [1.22, 0.08, 0.18], red),
        part("rbox", [0.71, -0.03, 0], [0.32, 0.08, 0.18], red, [0, 0, -0.80]),
        part("rbox", [-0.71, -0.03, 0], [0.32, 0.08, 0.18], red, [0, 0, 0.80]),
        part("rbox", [0.81, -0.30, 0], [0.08, 0.46, 0.18], red),
        part("rbox", [-0.81, -0.30, 0], [0.08, 0.46, 0.18], red),
    ]
    for s in (1, -1):
        parts += [
            part("cyl", [0.83 * s, -0.62, 0], [0.48, 0.10, 0.48], red, [0, 0, PI / 2]),
            part("sph", [0.97 * s, -0.62, 0], [0.34, 0.58, 0.58], SNOWBALL, decal="fur", wrap=True),
            place("snowflake", [1.15 * s, -0.62, 0], 0.30, FROST, r=[0, PI / 2 * s, 0], m="metal"),
        ]
    return parts


@XM22.hat("snowdrift_robin", "Snowdrift & Robin",
          "You stood still for one minute in the first snow of the year and this "
          "happened. The robin has moved in. The robin is not moving out.", "uncommon")
def _():
    brown, breast = "#7a5a3a", "#e2552a"
    parts = [
        cap(-0.26, 0.10, SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [0, 0.12, 0], [1.40, 0.56, 1.30], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [0.34, 0.26, -0.16], [0.80, 0.50, 0.70], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [-0.36, 0.20, 0.18], [0.66, 0.40, 0.62], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [-0.10, 0.40, -0.24], [0.56, 0.40, 0.50], SNOWBALL, decal="xm_snow", wrap=True),
    ]
    # lumps of snow spilling over the edge all round
    parts += around(11, 0.76, -0.04, lambda a, x, z: part(
        "sph", [x * 1.02, -0.06 + 0.04 * math.sin(a * 3), z], [0.46, 0.34, 0.46], SNOWBALL,
        decal="xm_snow", wrap=True), start=0.2)
    # icicles off the side and the back of the drift
    for x, z, h in ((0.83, -0.30, 0.30), (0.83, 0.12, 0.22), (-0.83, -0.20, 0.26),
                    (-0.83, 0.16, 0.20), (-0.40, -0.80, 0.30), (0.05, -0.80, 0.24),
                    (0.42, -0.80, 0.34)):
        parts.append(place("icicle", [x, -0.24, z], [0.11, h, 0.11], ICE, anchor=[0, 1, 0],
                           m="glass"))
    # the robin, on top of the drift
    rb = [0.18, 0.62, 0.08]
    parts += [
        part("sph", [rb[0], rb[1], rb[2]], [0.34, 0.30, 0.42], brown),
        part("sph", [rb[0], rb[1] - 0.02, rb[2] + 0.12], [0.26, 0.24, 0.16], breast),
        part("sph", [rb[0], rb[1] + 0.18, rb[2] + 0.12], [0.22, 0.22, 0.22], brown),
        part("sph", [rb[0], rb[1] + 0.16, rb[2] + 0.20], [0.14, 0.12, 0.08], breast),
        place("cone", [rb[0], rb[1] + 0.18, rb[2] + 0.28], [0.05, 0.10, 0.05], "#e8b23a",
              r=[PI / 2, 0, 0]),
        part("sph", [rb[0] + 0.07, rb[1] + 0.22, rb[2] + 0.21], [0.04, 0.04, 0.03], COAL),
        part("sph", [rb[0] - 0.07, rb[1] + 0.22, rb[2] + 0.21], [0.04, 0.04, 0.03], COAL),
        part("rbox", [rb[0], rb[1] + 0.02, rb[2] - 0.26], [0.14, 0.04, 0.24], "#5a3e26",
             [-0.5, 0, 0]),
        part("cyl", [rb[0] + 0.06, rb[1] - 0.17, rb[2]], [0.02, 0.10, 0.02], "#3a2a1a"),
        part("cyl", [rb[0] - 0.06, rb[1] - 0.17, rb[2]], [0.02, 0.10, 0.02], "#3a2a1a"),
    ]
    parts += _holly([-0.30, 0.42, 0.34], 0.7, yaw=-0.4)
    return parts


@XM22.hat("lost_mitten", "The Lost Mitten",
          "Somebody lost one mitten in the first snow, and it was enormous, so now "
          "it is a hat. The string it hung on is still attached, in case you lose "
          "it again.", "uncommon")
def _():
    red, cream = "#b8222a", "#f4ecdc"
    shell = dome(-0.28, 1.30, red, decal="knit", wrap=True)
    return [
        shell,
        ringband(-0.08, 0.36, cream, decal="knit", wrap=True),
        # the thumb, sticking out at a jaunty angle
        place("capsule", [0.50, 0.32, 0.10], [0.36, 0.30, 0.36], red, anchor=[0, 0, 0],
              r=[0.2, 0, -0.80], decal="knit", wrap=True),
        # a white knitted snowflake on the back of the hand
        place("snowflake", [0, 0.42, 0.80], 0.52, cream, r=[-0.42, 0, 0]),
        # the string, looping off the cuff
        place("arch", [-0.80, -0.36, 0.0], [0.30, 0.70, 1.0], "#e8e0d0", anchor=[0, 1, 0],
              r=[0, PI / 2, PI]),
        part("cyl", [-0.84, -0.62, -0.26], [0.04, 0.52, 0.04], "#e8e0d0", [0.4, 0, 0.1]),
    ]


@XM22.hat("snow_day_umbrella", "Snow Day Umbrella",
          "An umbrella hat, for keeping the snow off. It has kept a great deal of "
          "snow off. All of it is still on the umbrella.", "rare", hair="show")
def _():
    parts = [
        band(-0.22, 0.12, "#2a2a30", grow=0.02),
        part("cyl", [0, 0.30, 0], [0.08, 0.66, 0.08], "#c9ced6", m="metal"),
        part("rbox", [0, -0.02, 0], [0.30, 0.10, 0.30], "#2a2a30"),
        place("hemi", [0, 0.58, 0], [2.70, 1.30, 2.70], "#c4281c", anchor=[0, 0, 0],
              decal="xm_umbrella", wrap=True),
        # the snow on top of it, heaped
        place("hemi", [0, 0.66, 0], [2.24, 1.56, 2.24], SNOWBALL, anchor=[0, 0, 0],
              decal="xm_snow", wrap=True),
        part("sph", [0.24, 1.36, 0.10], [0.80, 0.46, 0.74], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [-0.26, 1.30, -0.20], [0.66, 0.40, 0.62], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [0, 1.56, 0], [0.34, 0.30, 0.34], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [0, 1.72, 0], [0.12, 0.12, 0.12], GOLD, m="metal"),
    ]
    # ribs under the canopy, and icicles off every tip
    for k in range(8):
        a = k * TAU / 8 + TAU / 16
        tip = [math.sin(a) * 1.32, 0.58, math.cos(a) * 1.32]
        mid = [tip[0] / 2, 0.61, tip[2] / 2]
        parts.append(part("cyl", mid, [0.03, 1.33, 0.03], "#c9ced6", [PI / 2 + 0.05, a, 0], m="metal"))
        parts.append(part("sph", tip, [0.07, 0.07, 0.07], "#c9ced6", m="metal"))
        parts.append(place("icicle", [tip[0], 0.56, tip[2]], [0.14, 0.32 + (k % 3) * 0.10, 0.14],
                           ICE, anchor=[0, 1, 0], m="glass"))
    return parts


@XM22.hat("cocoa_mug", "Bottomless Cocoa",
          "A mug of hot cocoa the size of your head, cream, marshmallows and all, "
          "kept warm on a knitted cosy. It has never once gone cold. It has never "
          "once been drunk.", "rare")
def _():
    parts = [
        cap(-0.24, 0.10, "#2a8a4a", decal="knit", wrap=True),
        band(-0.20, 0.10, "#f4ecdc", grow=0.04, decal="knit", wrap=True),
    ]
    parts += _mug([0, 0.08, 0], 1.80, handle_side=1)
    parts.append(place("cane", [-0.36, 1.16, -0.06], [0.80, 1.10, 0.80], WHITE, anchor=[0, 0, 0],
                       r=[0, 0.4, 0.30], decal="candy", wrap=True))
    return parts


@XM22.back("toboggan", "Old Toboggan",
           "A wooden toboggan with a proper curl at the front and a red pull-rope, "
           "worn on your back between runs. It has a scratch for every hill in "
           "Blockhaven.", "rare")
def _():
    wood, dark = "#b07a44", "#7a4a26"
    parts = [
        part("rbox", [0, 0.06, -0.30], [1.00, 2.10, 0.08], wood, [-0.10, 0, 0], decal="planks",
             wrap=True),
        # the curl at the top, rolled back
        part("cyl", [0, 1.16, -0.52], [0.40, 1.00, 0.40], wood, [0, 0, PI / 2], decal="planks",
             wrap=True),
        part("rbox", [0, 1.03, -0.44], [1.00, 0.24, 0.10], wood, [-0.9, 0, 0], decal="planks"),
        # side rails and slats
        part("rbox", [0.46, 0.04, -0.37], [0.08, 2.00, 0.08], dark, [-0.10, 0, 0]),
        part("rbox", [-0.46, 0.04, -0.37], [0.08, 2.00, 0.08], dark, [-0.10, 0, 0]),
        # the pull-rope looped through the curl and down one side
        part("torus", [0, 1.16, -0.52], [0.52, 1.0, 0.52], "#c4281c", [0, 0, PI / 2]),
        part("cyl", [0.54, 0.62, -0.46], [0.05, 1.10, 0.05], "#c4281c", [-0.12, 0, 0.06]),
        part("cyl", [-0.54, 0.62, -0.46], [0.05, 1.10, 0.05], "#c4281c", [-0.12, 0, -0.06]),
        part("rbox", [0, -0.94, -0.18], [0.96, 0.06, 0.10], dark, [-0.10, 0, 0]),
        *straps("#3a2a1c", 0.34, 0.12),
    ]
    for y in (-0.55, -0.05, 0.45):
        parts.append(part("rbox", [0, y, -0.37 + (y * 0.1)], [0.96, 0.08, 0.06], dark, [-0.10, 0, 0]))
    return parts


@XM22.back("snowman_hitchhiker", "Snowman Hitchhiker",
           "A little snowman riding in a basket on your back, waving at everyone you "
           "pass. He is not heavy. He is a little bit cold. He says hello.", "legendary")
def _():
    wicker = "#9a6a3a"
    parts = [
        part("cyl", [0, 0.62, -0.55], [0.98, 0.80, 0.86], wicker, decal="xm_wicker", wrap=True),
        part("torus", [0, 1.02, -0.55], [1.02, 0.50, 0.90], shade(wicker, 0.8)),
        part("torus", [0, 0.24, -0.55], [1.02, 0.50, 0.90], shade(wicker, 0.8)),
        *straps("#5a3a22", 0.34, 0.12),
        part("rbox", [0, 0.62, -0.10], [0.70, 0.20, 0.10], "#5a3a22"),
        # a cushion of snow for him to sit in
        place("hemi", [0, 1.00, -0.55], [0.90, 0.30, 0.78], SNOWBALL, anchor=[0, 0, 0],
              decal="xm_snow", wrap=True),
    ]
    parts += _snowman([0.06, 0.92, -0.58], 1.0, facing=0.25, wave=True)
    return parts


@XM22.hairdo("frosted_spikes", "Frost-Tipped Spikes",
             "Spiked up before the first snow and frozen that way. The tips have not "
             "thawed since, and neither has the snowflake.", "uncommon")
def _():
    c = "#6b4a2a"
    parts = [place("hairshort", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    spikes = [(0.0, 0.18, 0.0, 0.48), (0.22, 0.05, -0.2, 0.40), (-0.22, 0.05, 0.2, 0.40),
              (0.20, -0.20, -0.35, 0.36), (-0.20, -0.20, 0.35, 0.36), (0.0, -0.30, 0.0, 0.38),
              (0.32, 0.25, -0.5, 0.32), (-0.32, 0.25, 0.5, 0.32), (0.0, 0.34, 0.0, 0.34)]
    for x, z, lean, h in spikes:
        r = [-0.25 - z * 0.6, 0, lean * 0.8]
        base = [x, 0.47, z]
        tip = rotate([0, h, 0], r)
        parts.append(place("cone", base, [0.20, h, 0.20], c, anchor=[0, -0.5, 0], r=r))
        parts.append(place("cone", [base[0] + tip[0] * 0.78, base[1] + tip[1] * 0.78,
                                    base[2] + tip[2] * 0.78],
                           [0.09, h * 0.30, 0.09], "#f2faff", anchor=[0, -0.2, 0], r=r))
    parts.append(place("snowflake", [0.40, 0.42, 0.30], 0.20, "#f2faff", r=[-0.3, 0.6, 0]))
    return parts


@XM22.hairdo("flurry_bob", "Flurry Bob",
             "A neat bob with a dusting of fresh snow on top and two snowflake clips "
             "that sparkle when the light catches them.", "rare")
def _():
    c = "#3e2418"
    parts = [place("hairbob", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for s in (1, -1):
        parts.append(place("snowflake", [0.56 * s, 0.18, 0.22], 0.24, "#e8f6ff",
                           r=[0, PI / 2 * s, 0.3 * s], m="neon"))
    for n in range(9):
        a = n * 2.39996
        rr = 0.12 + (n % 3) * 0.12
        parts.append(part("sph", [math.sin(a) * rr, 0.54 - rr * 0.12, math.cos(a) * rr - 0.04],
                          [0.12, 0.05, 0.12], SNOWBALL))
    return parts


XM22.face("rosy_cheeks", "Rosy Cheeks",
          "Cheeks gone pink from the cold, a smile you cannot get off, and your "
          "breath coming out in little clouds.", [
              {"k": "arc", "x": -0.20, "y": -0.10, "r": 0.07, "a0": 0.55, "a1": 0.95, "w": 0.035,
               "c": "#1a1a1a"},
              {"k": "arc", "x": 0.20, "y": -0.10, "r": 0.07, "a0": 0.55, "a1": 0.95, "w": 0.035,
               "c": "#1a1a1a"},
              {"k": "ellipse", "x": -0.29, "y": 0.04, "w": 0.15, "h": 0.08, "c": "#ff8fa3"},
              {"k": "ellipse", "x": 0.29, "y": 0.04, "w": 0.15, "h": 0.08, "c": "#ff8fa3"},
              {"k": "arc", "x": 0, "y": 0.06, "r": 0.11, "a0": 0.08, "a1": 0.42, "w": 0.035,
               "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0.30, "y": 0.24, "w": 0.09, "h": 0.07, "c": "#eef8ff"},
              {"k": "ellipse", "x": 0.37, "y": 0.20, "w": 0.08, "h": 0.07, "c": "#eef8ff"},
              {"k": "ellipse", "x": 0.42, "y": 0.26, "w": 0.07, "h": 0.06, "c": "#eef8ff"},
          ])
XM22.face("snowflake_catcher", "Catching Snowflakes",
          "Eyes up, tongue out, waiting for the one with your name on it. It has "
          "just landed.", [
              {"k": "ellipse", "x": -0.19, "y": -0.13, "w": 0.13, "h": 0.15, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.19, "y": -0.13, "w": 0.13, "h": 0.15, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.18, "y": -0.18, "w": 0.07, "h": 0.07, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0.20, "y": -0.18, "w": 0.07, "h": 0.07, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0, "y": 0.13, "w": 0.18, "h": 0.15, "c": "#3a1a1a"},
              {"k": "ellipse", "x": 0, "y": 0.21, "w": 0.13, "h": 0.12, "c": "#ff6f8a"},
              {"k": "star", "x": 0, "y": 0.21, "r": 0.045, "n": 6, "i": 0.35, "c": "#ffffff"},
              {"k": "star", "x": 0.30, "y": -0.36, "r": 0.04, "n": 6, "i": 0.35, "c": "#bfe6ff"},
              {"k": "star", "x": -0.34, "y": -0.30, "r": 0.03, "n": 6, "i": 0.35, "c": "#bfe6ff"},
          ], "rare")
XM22.shirt("fair_isle", "Fair Isle Snow Sweater",
           "Hand-knitted, navy and cream, with a snowflake on the chest and a yoke of "
           "little stars. Your nan says it will fit you next year.",
           {"torso": "#1b2f5a", "arms": "#1b2f5a", "decal": "xm_tee_yoke", "weave": "xm_fairisle",
            "stripe": "#f4ecdc"}, "rare")
XM22.pants("snow_pants", "Puffy Snow Pants",
           "Quilted, waterproof and so padded you can sit down in a snowdrift for an "
           "hour. Walking is harder.",
           {"legs": "#3a6fb0", "weave": "xm_quilt", "cuff": "#2a2a30"})
XM22.belt("snowball_belt", "Snowball Bandolier",
          "A knitted belt with two pouches, each holding one perfectly packed "
          "snowball. For emergencies.",
          {"band": "#e8f0fa", "buckle": FROST, "width": 0.22, "weave": "knit", "pouch": True})


@XM22.weapon("snowball_gatling", "Snowball Gatling",
             "A hand-cranked gatling gun with a hopper full of snow. Every snowball "
             "that lands chills; six in a row and the target freezes solid.",
             {"kind": "projectile", "projectile": "snowball", "damage": 7, "splash": 0,
              "splash_damage": 0, "rpm": 420, "mag": 48, "reload": 3.2, "speed": 115,
              "range": 220, "auto": True, "sound": "throw", "recoil": 0.3, "reserve": 192,
              "gravity_scale": 0.55, "self_damage": 0.0, "knockback": 1,
              "on_hit": {"freeze": [0.10, 6, 1.6]}, "held": {"speed": -0.15},
              "trail_colors": ["#ffffff", "#bfe6ff"]},
             [["+", "Every snowball chills; six in a row freeze the target solid for 1.6 "
                    "seconds"],
              ["+", "48 snowballs, seven a second"],
              ["-", "Only 7 damage a snowball, and they drop with distance"],
              ["-", "You move 15% slower while you lug it about"]], rarity="legendary",
             proj=lambda: [part("sph", [0, 0, 0], [0.46, 0.46, 0.46], SNOWBALL, decal="xm_snow",
                                wrap=True)],
             two_handed=True)
def _():
    steel = "#9fc4e0"
    parts = [
        part("rbox", [0, -0.32, -0.08], [0.18, 0.46, 0.22], "#5a3a22", [0.25, 0, 0]),
        part("rbox", [0, -0.06, -0.36], [0.22, 0.24, 0.50], "#5a3a22"),
        part("cyl", [0, 0.05, 0.30], [0.54, 0.56, 0.54], "#c4281c", [PI / 2, 0, 0]),
        part("torus", [0, 0.05, 0.02], [0.56, 0.6, 0.56], GOLD, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.05, 0.58], [0.56, 0.6, 0.56], GOLD, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.05, 1.50], [0.48, 0.08, 0.48], steel, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.05, 1.05], [0.40, 0.06, 0.40], steel, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.05, 1.05], [0.08, 1.10, 0.08], steel, [PI / 2, 0, 0], m="metal"),
        # the hopper of snow, heaped with snowballs
        part("cyl", [0, 0.50, 0.30], [0.50, 0.36, 0.50], "#3a6fb0", decal="snowflakes",
             wrap=True),
        part("torus", [0, 0.68, 0.30], [0.54, 0.4, 0.54], GOLD, m="metal"),
        # the crank
        part("cyl", [0.34, 0.05, 0.30], [0.06, 0.20, 0.06], steel, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.44, -0.08, 0.30], [0.05, 0.30, 0.05], steel, m="metal"),
        part("cyl", [0.50, -0.22, 0.30], [0.08, 0.16, 0.08], "#c4281c", [0, 0, PI / 2]),
    ]
    for k in range(6):
        a = k * TAU / 6
        parts.append(part("cyl", [math.sin(a) * 0.15, 0.05 + math.cos(a) * 0.15, 1.05],
                          [0.10, 1.10, 0.10], steel, [PI / 2, 0, 0], m="metal"))
    for k, (x, z) in enumerate(((0, 0.30), (0.12, 0.20), (-0.12, 0.38), (0.06, 0.42), (-0.08, 0.18))):
        parts.append(part("sph", [x, 0.74 + (k % 2) * 0.06, z], [0.16, 0.16, 0.16], SNOWBALL))
    return parts


@XM22.weapon("icicle_crossbow", "Icicle Crossbow",
             "A crossbow strung with frost that fires one long icicle at a time. It "
             "goes clean through the first few people in its way, and it hits hardest "
             "from a long way off.",
             {"kind": "projectile", "projectile": "icicle", "damage": 40, "headshot": 1.5,
              "splash": 0, "splash_damage": 0, "rpm": 60, "mag": 1, "reload": 1.5,
              "speed": 170, "range": 400, "auto": False, "sound": "throw", "recoil": 1.2,
              "reserve": 30, "gravity_scale": 0.25, "self_damage": 0.0, "knockback": 4,
              "pierce_players": 3, "far": {"dist": 40, "bonus": 0.35},
              "near": {"dist": 12, "bonus": -0.30}, "on_hit": {"slow": [0.25, 1.5]},
              "tracer": "#bfe6ff", "trail_colors": ["#ffffff", "#bfe6ff"]},
             [["+", "Each icicle passes through up to three people"],
              ["+", "35% more damage at 40 studs and beyond; chills whoever it hits"],
              ["-", "30% less damage within 12 studs"],
              ["-", "One icicle, then a reload"]], rarity="legendary",
             proj=lambda: [place("icicle", [0, 0, 0], [0.22, 1.40, 0.22], ICE, r=[-PI / 2, 0, 0],
                                 m="glass"),
                           part("cyl", [0, 0, -0.10], [0.06, 1.0, 0.06], "#ffffff", [PI / 2, 0, 0],
                                m="neon", a=0.7)])
def _():
    wood, frost = "#5a3a22", "#cfeaff"
    return [
        part("rbox", [0, -0.02, 0.32], [0.16, 0.16, 1.40], wood, decal="planks"),
        part("rbox", [0, -0.30, -0.08], [0.16, 0.42, 0.20], wood, [0.35, 0, 0]),
        part("rbox", [0, -0.06, -0.46], [0.18, 0.28, 0.30], wood),
        place("arch", [0, 0.02, 0.92], [1.40, 0.62, 1.4], frost, anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], m="metal"),
        part("box", [0.35, 0.05, 0.735], [0.79, 0.02, 0.02], "#ffffff", [0, -0.487, 0]),
        part("box", [-0.35, 0.05, 0.735], [0.79, 0.02, 0.02], "#ffffff", [0, 0.487, 0]),
        place("icicle", [0, 0.10, 1.00], [0.14, 1.10, 0.14], ICE, r=[-PI / 2, 0, 0], m="glass"),
        place("gem", [0, 0.11, 0.30], [0.14, 0.14, 0.14], FROST, m="glass"),
        place("gem", [0, 0.11, 0.05], [0.10, 0.10, 0.10], FROST, m="glass"),
        part("rbox", [0, 0.12, 0.55], [0.06, 0.10, 0.10], "#9fc4e0", m="metal"),
    ]


@XM22.weapon("snow_globe", "Snow Globe Grenade",
             "Shake it, throw it, and the glass bursts into a blizzard the size of a "
             "room: everybody on the other side caught in it is slowed and cannot "
             "jump, while your team inside it slowly warms up.",
             {"kind": "deploy", "cooldown": 24, "sound": "throw",
              "deploy": {"type": "dome", "thrown": True, "throw": 26, "radius": 9.0,
                         "secs": 7.0, "limit": 1, "scale": 1.6, "color": "#dff4ff",
                         "particle": "flake", "name": "Blizzard",
                         "enemy": {"slow": [0.45, 1.0], "jumpless": 1.0},
                         "ally": {"regen": [4, 1.0]}}},
             [["+", "A 9 stud blizzard for 7 seconds: enemies inside are 45% slower and "
                    "cannot jump"],
              ["+", "Teammates inside heal 4 a second"],
              ["-", "Does no damage at all"],
              ["-", "24 second cooldown"]], rarity="legendary",
             deploy=lambda: [part("cyl", [0, 0.16, 0], [1.10, 0.32, 1.10], LACQUER),
                             part("cyl", [0, 0.33, 0], [1.14, 0.04, 1.14], GOLD, m="metal"),
                             place("hemi", [0, 0.34, 0], [0.96, 0.24, 0.96], SNOWBALL,
                                   anchor=[0, 0, 0]),
                             place("tree", [-0.18, 0.36, 0], [0.34, 0.54, 0.34], "#2f6a3e",
                                   anchor=[0, 0, 0]),
                             place("star", [-0.18, 0.94, 0], 0.12, GOLD, m="neon")]
             + _snowman([0.22, 0.38, 0.06], 0.30))
def _():
    return [
        part("cyl", [0, -0.02, 0.32], [0.52, 0.18, 0.52], LACQUER),
        part("cyl", [0, 0.08, 0.32], [0.54, 0.03, 0.54], GOLD, m="metal"),
        part("sph", [0, 0.34, 0.32], [0.50, 0.50, 0.50], "#e8f6ff", m="glass", a=0.25),
        place("hemi", [0, 0.09, 0.32], [0.42, 0.12, 0.42], SNOWBALL, anchor=[0, 0, 0]),
        place("tree", [-0.07, 0.10, 0.30], [0.16, 0.26, 0.16], "#2f6a3e", anchor=[0, 0, 0]),
        part("sph", [0.09, 0.16, 0.36], [0.10, 0.10, 0.10], SNOWBALL),
        part("sph", [0.09, 0.25, 0.36], [0.07, 0.07, 0.07], SNOWBALL),
        part("sph", [0.06, 0.46, 0.30], [0.03, 0.03, 0.03], "#ffffff"),
        part("sph", [-0.08, 0.42, 0.38], [0.03, 0.03, 0.03], "#ffffff"),
        part("sph", [0.12, 0.36, 0.22], [0.03, 0.03, 0.03], "#ffffff"),
    ]


@XM22.gear("hot_cocoa", "Hot Cocoa",
           "A mug of cocoa with cream and marshmallows on top. It warms you right "
           "through, slowly, and there is always enough to pass round.",
           {"kind": "consume", "cooldown": 28, "sound": "drink",
            "consume": {"heal": 40, "over": 8.0, "share": 12}},
           [["+", "Heals you 40 over 8 seconds"],
            ["+", "Teammates within 12 studs get a 20 health sip straight away"],
            ["-", "It takes its time: none of it is instant for you"],
            ["-", "28 second cooldown"]], rarity="rare")
def _():
    return _mug([0, -0.12, 0.30], 0.42, handle_side=-1)


XM22.effect("snowglobe_swirl", name="Snow Globe", rate=7.0, life=[2.4, 3.2],
            size=[0.14, 0.26], grow=0.0, gravity=-0.25, spread=0.1, rise=[0.1, 0.35],
            blend="normal", spin=1.2, colors=["#ffffff", "#e8f6ff", "#bfe6ff"],
            shapes=["flake", "flake", "flake", "flake", "snowman", "tree"], radius=1.0,
            orbit=1.5, wobble=0.3)
XM22.effect("fresh_powder", name="Fresh Powder", rate=10.0, life=[1.0, 1.6],
            size=[0.20, 0.42], grow=0.25, gravity=-1.8, spread=0.9, rise=[1.0, 1.6],
            blend="normal", spin=2.0, colors=["#ffffff", "#f2faff", "#cfe8ff"],
            shapes=["puff", "puff", "flake"], radius=0.5)
XM22.opening(
    sky={"top": "#0c1830", "horizon": "#3a5a8a", "sun": [0.3, 0.8, 0.5], "clouds": 0,
         "tint": "#dff0ff"},
    ambient="#8aa8d0", beam="#e8f6ff", seep="frostbite", after="snowglobe_swirl",
    burst=["#ffffff", "#bfe6ff", "#8fd0ff", "#ff5a5a"],
    pieces=[{"shape": "flake", "colors": ["#ffffff", "#dff4ff", "#bfe6ff"], "blend": "normal"},
            {"shape": "snowman", "colors": ["#ffffff", "#f2faff"], "blend": "normal"},
            {"shape": "mitten", "colors": ["#c4281c", "#2a8a4a"], "blend": "normal"},
            {"shape": "star", "colors": ["#fff3b0", "#ffd24a"], "blend": "add"}],
    backdrop="xm_snowfall", title_wait="Give it a good shake...",
    title_shake="Here comes the snow...")
XM22.award("Frostfall", ["Snowflake Spotter", "Snowball Thrower", "Snowman Builder",
                         "Sledge Captain", "Blizzard Chaser", "Spirit of the First Snow"],
           "Opened Snow Globe Crates during Frostfall, Christmas 2022.", "em_snowflake",
           "flake")
XM22.bundle("pair", "Globe and Key", 1, 1050, "One Snow Globe Crate, one Snowflake Key.")
XM22.bundle("snow_day", "Snow Day", 3, 3000, "Three globes, three keys. Saves 300.")


EVENTS = [XM22]
