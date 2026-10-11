"""Halloween: the lamps go out across the server, one October at a time.

  2022  Graveyard Shift      coffins, skeleton keys, the night shift at the cemetery
  2023  Witching Hour        cauldrons, broomsticks, a coven on the hill
  2024  Manor of Whispers    a haunted manor: candelabras, portraits, the seance
  2025  Big Top Terror       a carnival that came to town and never left
  2026  The Hallowed Harvest the current event (Oct 1 -- Nov 8): pumpkins, the
                             Plague Captain's surgeon, souls and candy

The 2026 crate shipped before the other years were written up, so its first
items keep the ids they shipped with (``hat_hexed_witch``, ``crate_halloween``,
``ev_harvest_2026``...) and live in app/models/cosmetics.py; the event here
wraps them, and adds what came later in the season (the Staff of the
Restless Dead among it).
"""
from __future__ import annotations

import math

from .. import cosmetics
from .kit import (BLACK, BONE, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, mix, part, place,
                  pompom, ringband, rod, rotate, shade, sides, straps)

GHOST_GREEN = "#9fe870"
WISP = "#6bff9a"
PUMPKIN = "#ff8c1a"
NIGHT = "#141a16"


def _lantern(at, k=1.0, flame="#6bff9a", metal=IRON, glass="#d8ffe6", hook=True):
    """An iron lantern: a cage of bars round a glass chimney and a flame,
    a peaked cap and a ring to hang it by.  ``at`` is its middle."""
    x, y, z = at
    out = [
        part("cyl", [x, y - 0.30 * k, z], [0.46 * k, 0.06 * k, 0.46 * k], metal, m="metal"),
        part("cyl", [x, y, z], [0.36 * k, 0.52 * k, 0.36 * k], glass, m="glass", a=0.35),
        place("flame", [x, y - 0.02 * k, z], [0.34 * k, 0.40 * k, 0.34 * k], flame, m="neon",
              spin=2.0),
        part("sph", [x, y - 0.06 * k, z], [0.14 * k, 0.14 * k, 0.14 * k], "#ffffff", m="neon",
             a=0.7),
        place("cone", [x, y + 0.40 * k, z], [0.50 * k, 0.22 * k, 0.50 * k], metal, m="metal"),
    ]
    for a in (0.25 * PI, 0.75 * PI, 1.25 * PI, 1.75 * PI):
        out.append(part("cyl", [x + math.sin(a) * 0.20 * k, y, z + math.cos(a) * 0.20 * k],
                        [0.035 * k, 0.60 * k, 0.035 * k], metal, m="metal"))
    if hook:
        out.append(part("torus", [x, y + 0.58 * k, z], [0.18 * k, 0.04 * k, 0.18 * k], metal,
                        [PI / 2, 0, 0], m="metal"))
    return out


def _skull(at, k=1.0, c=BONE, eyes="#16171b", facing=0.0, glow=None):
    """A little skull facing ``facing`` (yaw): a dome, a jaw, two sockets."""
    x, y, z = at
    fwd = [math.sin(facing), 0.0, math.cos(facing)]
    side = [math.cos(facing), 0.0, -math.sin(facing)]

    def off(dx, dy, dz):
        return [x + side[0] * dx + fwd[0] * dz, y + dy, z + side[2] * dx + fwd[2] * dz]
    out = [
        part("sph", off(0, 0.04 * k, 0), [0.50 * k, 0.46 * k, 0.48 * k], c),
        part("rbox", off(0, -0.18 * k, 0.04 * k), [0.32 * k, 0.16 * k, 0.32 * k], c, [0, facing, 0]),
    ]
    for s in (1, -1):
        out.append(part("sph", off(0.10 * k * s, 0.02 * k, 0.21 * k), [0.13 * k, 0.14 * k, 0.06 * k],
                        glow or eyes, m="neon" if glow else None))
    out.append(part("sph", off(0, -0.08 * k, 0.23 * k), [0.06 * k, 0.07 * k, 0.04 * k], eyes))
    for t in (-0.08, -0.027, 0.027, 0.08):
        out.append(part("box", off(t * k, -0.20 * k, 0.205 * k), [0.04 * k, 0.06 * k, 0.02 * k],
                        "#fffaf0", [0, facing, 0]))
    return out


SKELETON = {"name": "Skeleton", "model": "avatar",
            "colors": {"head": BONE, "torso": "#d9d0b8", "arms": BONE, "legs": "#cfc6ac"},
            "hp": 40, "speed": 17, "damage": 9, "reach": 4.5, "rate": 0.9, "secs": 20, "max": 2}


# ============================================================ 2022
HW22 = Event(
    "halloween_2022", "halloween", 2022, "hw22",
    name="Graveyard Shift", title="The Graveyard Shift",
    blurb="Blockhaven's first Halloween put everybody on the night shift at the old "
          "cemetery behind the Relay: lanterns, shovels, a lot of fog and a coffin "
          "that would not stay shut. It was nailed down for a reason.",
    tagline="Dig carefully. Some of them dig back.",
    starts="2022-10-01", ends="2022-11-09",
    colors={"accent": GHOST_GREEN, "deep": NIGHT, "glow": "#c8ffb0"},
    family_effects=["floating_bones", "flying_skulls", "haunted_wisps", "raven_feathers"],
    hero_effect="tombstone_rise", stencil="stencil_hw22")


@HW22.crate_model("Coffin Crate",
                  "Six boards of black oak, brass handles, and a padlock somebody "
                  "put on the OUTSIDE. Holds the Graveyard Shift set. Needs a Skeleton Key.",
                  hinge=[0, 0.42, -0.50], keyhole=[0, -0.10, 0.60])
def _():
    oak, dark, brass = "#2b2420", "#1a1512", BRASS
    parts = [
        # a coffin's long six-sided body: wide at the shoulders, narrow at the
        # head and the foot
        part("rbox", [0.0, 0.0, 0], [1.30, 0.82, 1.06], oak, decal="planks", wrap=True),
        part("rbox", [-0.82, 0.0, 0], [0.50, 0.82, 0.80], oak, decal="planks", wrap=True),
        part("rbox", [0.86, 0.0, 0], [0.46, 0.82, 0.66], oak, decal="planks", wrap=True),
        # the lid: the same outline, a board thick, with a raised panel
        part("rbox", [0.0, 0.50, 0], [1.36, 0.16, 1.12], dark, decal="planks", wrap=True, lid=1),
        part("rbox", [-0.82, 0.50, 0], [0.56, 0.16, 0.86], dark, decal="planks", wrap=True, lid=1),
        part("rbox", [0.86, 0.50, 0], [0.52, 0.16, 0.72], dark, decal="planks", wrap=True, lid=1),
        part("rbox", [0.0, 0.60, 0], [1.40, 0.06, 0.86], oak, lid=1),
        # a brass cross on the lid, and the plate that says who is inside
        part("rbox", [0.10, 0.65, 0], [0.70, 0.05, 0.12], brass, m="metal", lid=1),
        part("rbox", [-0.06, 0.65, 0], [0.12, 0.05, 0.46], brass, m="metal", lid=1),
        part("box", [0.62, 0.64, 0], [0.30, 0.03, 0.22], "#e8d8a8", m="metal", lid=1,
             decal="tombstone"),
        # the stencil down each side
        part("box", [0.0, 0.0, -0.535], [1.0, 0.62, 0.02], "#000000", [0, PI, 0],
             decal="stencil_hw22", a=-1),
        part("box", [0.0, 0.0, 0.535], [0.9, 0.30, 0.02], "#000000",
             decal="stencil_hw22", a=-1),
        # the padlock, on the outside
        part("rbox", [0, -0.10, 0.58], [0.38, 0.40, 0.10], brass, decal="keyhole", m="metal",
             lock=1),
        part("torus", [0, 0.16, 0.58], [0.30, 0.06, 0.30], IRON, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, 0.30, 0.56], [0.22, 0.10, 0.06], IRON, m="metal", lid=1),
        # the light waiting in the seam
        part("box", [0, 0.40, 0], [2.10, 0.04, 0.90], "#c8ffb0", m="neon"),
    ]
    # brass handles on the long sides, and studs
    for x in (-0.55, 0.40):
        for s in (1, -1):
            parts.append(part("torus", [x, -0.06, 0.55 * s], [0.30, 0.05, 0.30], brass,
                              [0, 0, PI / 2], m="metal"))
            parts.append(part("rbox", [x, 0.06, 0.54 * s], [0.12, 0.08, 0.04], brass, m="metal"))
    for x in (-0.95, -0.40, 0.20, 0.75):
        parts.append(part("sph", [x, -0.36, 0.0], [0.06, 0.06, 0.06], brass, m="metal"))
    # a little graveyard grass grown up the foot of it
    for k, (x, z) in enumerate(((-1.02, 0.30), (-0.95, -0.34), (1.05, 0.22), (0.98, -0.30))):
        parts.append(place("leaf", [x, -0.30, z], [0.5, 0.36, 1.0], "#3d5a2a",
                           anchor=[0, -0.5, 0], r=[0.3, k * 1.3, 0.25]))
    return parts


@HW22.key_model("Skeleton Key",
                "An iron key with a skull for a bow and a bone for a shaft. It rattles. "
                "Opens one Coffin Crate.", shoulder=-0.30)
def _():
    parts = _skull([-0.70, 0.02, 0], 1.25, facing=0.0, glow="#9fe870")
    parts += [
        place("bone", [0.10, 0, 0], [0.80, 0.55, 1.2], BONE),
        part("torus", [-0.30, 0, 0], [0.22, 0.07, 0.22], IRON, [0, 0, PI / 2], m="metal"),
        # the bit: three crooked iron teeth
        part("rbox", [0.40, -0.12, 0], [0.08, 0.22, 0.08], IRON, m="metal"),
        part("rbox", [0.52, -0.16, 0], [0.08, 0.30, 0.08], IRON, m="metal"),
        part("rbox", [0.64, -0.10, 0], [0.08, 0.18, 0.08], IRON, m="metal"),
        part("rbox", [0.52, -0.02, 0], [0.34, 0.08, 0.08], IRON, m="metal"),
    ]
    return parts


@HW22.hat("night_cap", "Night-Shift Flat Cap",
          "Tweed, worn flat, with a little green lantern clipped to the side for "
          "reading the names on the stones.", "uncommon")
def _():
    tweed, dark = "#5b5246", "#3d362e"
    parts = [
        cap(-0.30, 0.16, tweed, decal="linen", wrap=True),
        # the flat top, pulled forward and down over the brow
        part("rbox", [0, 0.02, 0.56], [1.62, 0.18, 0.46], tweed, [0.32, 0, 0], decal="linen",
             wrap=True),
        place("peak", [0, -0.17, 0], [1.66, 1.0, 1.66], dark, anchor=[0, 0, 0]),
        part("sph", [0, 0.17, -0.10], [0.16, 0.06, 0.16], dark),
        band(-0.24, 0.08, dark, grow=0.04),
    ]
    parts += _lantern([0.90, -0.12, 0.05], 0.55)
    parts.append(part("rbox", [0.83, -0.04, 0.05], [0.06, 0.12, 0.10], IRON, m="metal"))
    return parts


@HW22.hat("tombstone_topper", "Here Lies Topper",
          "A tombstone on a little mound of grave dirt, and a bony hand that has nearly "
          "dug its way out. The stone does not say whose it is.", "rare")
def _():
    stone = "#8d9196"
    parts = [
        cap(-0.26, 0.06, "#4a3424", decal="canvas", wrap=True),
        part("sph", [0.0, 0.06, 0.0], [1.30, 0.26, 1.20], "#4a3424", decal="canvas", wrap=True),
        # the stone, leaning back a touch
        part("rbox", [0, 0.50, -0.12], [0.80, 0.86, 0.20], stone, [-0.08, 0, 0], decal="tombstone"),
        part("cyl", [0, 0.92, -0.15], [0.80, 0.20, 0.80], stone, [PI / 2 - 0.08, 0, 0]),
        part("rbox", [0.22, 0.64, -0.02], [0.03, 0.30, 0.02], "#5e6166", [-0.08, 0, 0.5]),
        part("rbox", [0, 0.10, -0.12], [0.98, 0.10, 0.34], "#6e7277"),
    ]
    # the hand, coming up through the dirt at the front
    parts += [part("rbox", [0.30, 0.20, 0.42], [0.16, 0.12, 0.14], BONE, [0.4, 0.3, 0])]
    for k, ang in enumerate((-0.5, -0.2, 0.1, 0.4)):
        parts.append(part("cyl", [0.30 + k * 0.045 - 0.07, 0.32, 0.47], [0.04, 0.22, 0.04],
                          BONE, [0.5, 0, ang]))
    parts.append(part("cyl", [0.42, 0.25, 0.40], [0.04, 0.16, 0.04], BONE, [0.3, 0, -1.1]))
    # tufts of grave grass
    for k in range(7):
        a = k * TAU / 7 + 0.4
        parts.append(place("leaf", [math.sin(a) * 0.55, 0.08, math.cos(a) * 0.50],
                           [0.5, 0.30, 1.0], "#4b6b2e", anchor=[0, -0.5, 0],
                           r=[math.cos(a) * 0.4, a, -math.sin(a) * 0.4]))
    return parts


@HW22.hat("lost_lantern", "Lantern of the Lost",
          "A bent iron pole from the cemetery gate, and a lantern that burns green "
          "and has never once been lit.", "legendary", hair="show")
def _():
    parts = [
        band(-0.20, 0.10, IRON, grow=-0.08, m="metal"),
        part("rbox", [0, -0.12, -0.78], [0.22, 0.26, 0.10], IRON, m="metal"),
        # up from the back of the head, then over and forward
        part("cyl", [0, 0.40, -0.80], [0.07, 1.10, 0.07], IRON, m="metal"),
        part("sph", [0, 0.96, -0.80], [0.11, 0.11, 0.11], IRON, m="metal"),
        part("cyl", [0, 1.02, -0.30], [0.07, 1.00, 0.07], IRON, [PI / 2 - 0.12, 0, 0], m="metal"),
        part("sph", [0, 1.10, 0.18], [0.10, 0.10, 0.10], IRON, m="metal"),
        part("cyl", [0, 1.00, 0.20], [0.03, 0.22, 0.03], IRON, m="metal"),
        # a curl of iron at the elbow, the way a gate's finials go
        place("spiral", [0, 0.86, -0.72], [0.24, 0.20, 0.24], IRON, r=[PI / 2, 0, 0], m="metal"),
    ]
    parts += _lantern([0, 0.58, 0.20], 0.95)
    return parts


@HW22.hat("cobweb_topper", "Cobweb Top Hat",
          "An undertaker's top hat that spent a century on a peg in the crypt. The "
          "spider came with it and is not for sale.", "rare")
def _():
    parts = [
        place("brim", [0, -0.05, 0], [2.10, 1.6, 2.00], "#1d1f22", anchor=[0, 0, 0]),
        place("flare", [0, 0.0, 0], [1.34, 1.50, 1.28], "#24272b", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        part("cyl", [0, 0.16, 0], [1.24, 0.22, 1.18], "#3a3d42"),
        # a dent in the crown
        part("sph", [0.30, 1.18, 0.20], [0.40, 0.18, 0.40], "#1d1f22"),
        # cobwebs in the angle of the brim, and over the top
        part("box", [0.56, 0.36, 0.52], [0.70, 0.62, 0.01], "#000000", [0, 0.79, 0],
             decal="cobweb", a=-1),
        part("box", [-0.58, 0.30, -0.46], [0.66, 0.56, 0.01], "#000000", [0, 0.88, 0],
             decal="cobweb", a=-1),
        part("box", [0, 1.505, 0], [1.10, 0.01, 1.04], "#000000", decal="cobweb", a=-1),
        # the spider, down on its thread
        part("cyl", [-0.84, -0.12, 0.30], [0.012, 0.36, 0.012], "#e8e8e8", a=0.7),
        part("sph", [-0.84, -0.34, 0.30], [0.14, 0.12, 0.16], "#16171b"),
        part("sph", [-0.84, -0.30, 0.38], [0.09, 0.08, 0.09], "#16171b"),
        part("sph", [-0.81, -0.29, 0.43], [0.025, 0.025, 0.02], "#ff3b4e", m="neon"),
        part("sph", [-0.87, -0.29, 0.43], [0.025, 0.025, 0.02], "#ff3b4e", m="neon"),
    ]
    for s in (1, -1):
        for k in range(4):
            parts.append(part("cyl", [-0.84 + 0.10 * s, -0.36, 0.24 + k * 0.05],
                              [0.016, 0.20, 0.016], "#16171b", [0.3 * (k - 1.5), 0, 0.9 * s]))
    return parts


@HW22.hat("ossuary_crown", "Ossuary Crown",
          "Nobody remembers who the King of the Graveyard was. His crown is mostly "
          "the people he did not get on with.", "legendary")
def _():
    parts = [
        # a crown of bone, its points worn like teeth
        place("spikecrown", [0, -0.30, 0], [1.84, 0.72, 1.80], BONE, anchor=[0, 0, 0]),
        band(-0.24, 0.12, "#c9bfa4", grow=0.02),
    ]
    # crossed bones under the front skull, and a bone laid along each side
    parts += [place("bone", [0, -0.14, 0.86], [0.62, 0.62, 1.2], "#f2ecd8", r=[0, 0, 0.5]),
              place("bone", [0, -0.14, 0.87], [0.62, 0.62, 1.2], "#f2ecd8", r=[0, 0, -0.5])]
    for s in (1, -1):
        parts.append(place("bone", [0.86 * s, -0.20, -0.30], [0.70, 0.55, 1.2], "#f2ecd8",
                           r=[0, PI / 2, 0.15 * s]))
    # three skulls: the front and the temples
    parts += _skull([0, 0.12, 0.90], 0.62, facing=0.0, glow="#ff3b4e")
    parts += _skull([0.96, 0.02, 0.18], 0.44, facing=PI / 2)
    parts += _skull([-0.96, 0.02, 0.18], 0.44, facing=-PI / 2)
    return parts


@HW22.hat("raven_perch", "Raven's Perch",
          "A raven has chosen your head. It will not say why, and it will not say "
          "anything else either, except, now and then, your name.", "uncommon", hair="show")
def _():
    black, sheen = "#16171e", "#2b2f45"
    x0 = 0.22
    parts = [
        part("sph", [x0, 0.38, -0.05], [0.52, 0.50, 0.78], black, [0.35, 0, 0]),
        part("sph", [x0, 0.72, 0.20], [0.36, 0.34, 0.38], black),
        place("cone", [x0, 0.70, 0.46], [0.14, 0.30, 0.14], "#3a3d42", r=[PI / 2 + 0.1, 0, 0]),
        part("sph", [x0 + 0.13, 0.78, 0.30], [0.07, 0.07, 0.05], "#ffd36a", m="neon"),
        part("sph", [x0 - 0.13, 0.78, 0.30], [0.07, 0.07, 0.05], "#ffd36a", m="neon"),
        # folded wings and a long tail
        place("wing", [x0 + 0.24, 0.40, -0.10], [0.62, 0.58, 1.0], sheen, r=[0.2, PI / 2, -1.2]),
        place("wing", [x0 - 0.24, 0.40, -0.10], [0.62, 0.58, 1.0], sheen, r=[0.2, -PI / 2, 1.2]),
        place("feather", [x0, 0.24, -0.54], [1.0, 0.70, 1.0], black, r=[-1.1, 0, 0]),
        place("feather", [x0 + 0.08, 0.25, -0.50], [0.9, 0.60, 1.0], sheen, r=[-1.1, 0.3, 0]),
        # feet gripping the scalp
        part("cyl", [x0 + 0.10, 0.08, 0.02], [0.04, 0.18, 0.04], "#3a3d42"),
        part("cyl", [x0 - 0.10, 0.08, 0.02], [0.04, 0.18, 0.04], "#3a3d42"),
        part("rbox", [x0 + 0.10, 0.01, 0.08], [0.06, 0.03, 0.18], "#3a3d42"),
        part("rbox", [x0 - 0.10, 0.01, 0.08], [0.06, 0.03, 0.18], "#3a3d42"),
    ]
    return parts


@HW22.hat("will_o_wisps", "Will-o'-the-Wisps",
          "Three marsh lights that followed you home from the cemetery, and now go "
          "everywhere you go, a little above your head, flickering.", "rare", hair="show")
def _():
    parts = []
    for k, (a, h, s) in enumerate(((0.0, 0.62, 1.0), (2.2, 0.82, 0.8), (4.2, 0.52, 0.9))):
        x, z = math.sin(a) * 0.58, math.cos(a) * 0.55
        parts += [
            place("teardrop", [x, h, z], [0.30 * s, 0.46 * s, 0.30 * s], "#b8ffd2", m="neon",
                  a=0.85, spin=1.5 + k),
            part("sph", [x, h + 0.10 * s, z], [0.48 * s, 0.48 * s, 0.48 * s], WISP, m="neon",
                 a=0.25),
            place("flame", [x, h + 0.30 * s, z], [0.26 * s, 0.34 * s, 0.26 * s], "#e8fff0",
                  m="neon", a=0.6, spin=3.0),
        ]
    parts.append(part("torus", [0, 0.40, 0], [1.40, 0.02, 1.36], WISP, m="neon", a=0.3, spin=0.6))
    return parts


@HW22.back("coffin_pack", "Coffin Backpack",
           "A small coffin on shoulder straps, padlocked. It knocks from inside about "
           "once an hour. Best not to answer.", "rare")
def _():
    oak, dark = "#2b2420", "#1a1512"
    return [
        part("rbox", [0, 0.18, -0.32], [0.82, 1.20, 0.36], oak, decal="planks", wrap=True),
        part("rbox", [0, 0.92, -0.32], [0.58, 0.40, 0.34], oak, decal="planks", wrap=True),
        part("rbox", [0, -0.56, -0.32], [0.54, 0.40, 0.34], oak, decal="planks", wrap=True),
        part("rbox", [0, 0.20, -0.52], [0.66, 1.70, 0.06], dark),
        part("rbox", [0, 0.30, -0.56], [0.08, 0.70, 0.03], BRASS, m="metal"),
        part("rbox", [0, 0.44, -0.56], [0.40, 0.08, 0.03], BRASS, m="metal"),
        part("rbox", [0, -0.30, -0.53], [0.22, 0.26, 0.06], BRASS, m="metal", decal="keyhole"),
        part("torus", [0, -0.14, -0.53], [0.18, 0.04, 0.18], IRON, [PI / 2, 0, 0], m="metal"),
        *straps("#2a2420", 0.36, 0.13),
    ]


@HW22.back("night_watch", "Night Watch Lantern",
           "The watchman's lantern on its pole, slung over the shoulder, swinging. It "
           "lights the way for whoever is walking behind you, which is somehow worse.",
           "uncommon")
def _():
    pole = "#4a3424"
    parts = [
        part("cyl", [0.10, 0.50, -0.20], [0.08, 2.40, 0.08], pole, [0.25, 0, -0.35]),
        part("rbox", [0.0, 0.40, -0.10], [0.70, 0.10, 0.10], "#2a2420", [0, 0, -0.35]),
        *straps("#2a2420", 0.34, 0.12),
    ]
    tip = [0.10 + math.sin(0.35) * 1.15, 0.50 + math.cos(0.35) * 1.15 * math.cos(0.25),
           -0.20 - math.sin(0.25) * 1.15]
    parts.append(part("cyl", [tip[0], tip[1] - 0.18, tip[2]], [0.03, 0.36, 0.03], IRON, m="metal"))
    parts += _lantern([tip[0], tip[1] - 0.66, tip[2]], 0.75)
    return parts


@HW22.hairdo("grave_mop", "Grave-Dust Mop",
             "Dusty, grey and slept in, with a cobweb or two. What a night on the "
             "graveyard shift does to anybody.", "uncommon")
def _():
    c, hi = "#7a7468", "#9a9488"
    parts = [place("hairmid", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k, (x, y, z, rx, rz) in enumerate(((0.30, 0.50, 0.25, -0.6, -0.5), (-0.25, 0.52, 0.20, -0.5, 0.6),
                                           (0.05, 0.56, -0.15, 0.4, 0.1), (0.40, 0.40, -0.30, 0.6, -0.8),
                                           (-0.42, 0.38, -0.25, 0.6, 0.9))):
        parts.append(place("teardrop", [x * 0.9, y - 0.04, z * 0.9], [0.15, 0.24, 0.13],
                           hi if k % 2 else c, anchor=[0, 0.1, 0], r=[rx * 1.6, 0, rz * 1.6]))
    parts.append(part("box", [0.55, 0.20, 0.0], [0.01, 0.40, 0.50], "#000000", [0, 0, 0],
                      decal="cobweb", a=-1))
    return parts


@HW22.hairdo("undertaker_part", "Undertaker's Part",
             "Black, combed flat, parted straight down the middle with a ruler. Very "
             "respectful. Very still.", "uncommon")
def _():
    c = "#121214"
    return [
        place("hairshort", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0],
              decal="strands", wrap=True),
        part("rbox", [0, 0.545, 0.10], [0.03, 0.02, 0.80], "#3a3a40"),
        part("rbox", [0.53, 0.08, 0.30], [0.02, 0.22, 0.08], c),
        part("rbox", [-0.53, 0.08, 0.30], [0.02, 0.22, 0.08], c),
    ]


HW22.face("bare_bones", "Bare Bones",
          "Sockets, a nose hole and a row of teeth -- face paint, or the face "
          "underneath. Hard to tell in the dark.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.15, "h": 0.17, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.15, "h": 0.17, "c": "#16171b"},
              {"k": "ellipse", "x": -0.20, "y": -0.12, "w": 0.04, "h": 0.04, "c": "#9fe870"},
              {"k": "ellipse", "x": 0.20, "y": -0.12, "w": 0.04, "h": 0.04, "c": "#9fe870"},
              {"k": "poly", "pts": [[0, 0.02], [-0.06, 0.10], [0.06, 0.10]], "c": "#16171b"},
              {"k": "poly", "pts": [[-0.24, 0.18], [0.24, 0.18], [0.20, 0.27], [-0.20, 0.27]],
               "c": "#16171b"},
              {"k": "line", "x1": -0.12, "y1": 0.18, "x2": -0.12, "y2": 0.27, "w": 0.025, "c": "#e8e0c8"},
              {"k": "line", "x1": -0.04, "y1": 0.18, "x2": -0.04, "y2": 0.27, "w": 0.025, "c": "#e8e0c8"},
              {"k": "line", "x1": 0.04, "y1": 0.18, "x2": 0.04, "y2": 0.27, "w": 0.025, "c": "#e8e0c8"},
              {"k": "line", "x1": 0.12, "y1": 0.18, "x2": 0.12, "y2": 0.27, "w": 0.025, "c": "#e8e0c8"},
              {"k": "line", "x1": -0.24, "y1": 0.225, "x2": 0.24, "y2": 0.225, "w": 0.02, "c": "#e8e0c8"},
          ], "rare")
HW22.face("fresh_grave", "Fresh From the Grave",
          "One eye wide, one eye not, and a mouth that has been stitched shut by "
          "somebody who was not a tailor.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.13, "h": 0.13, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.06, "h": 0.06, "c": "#16171b"},
              {"k": "line", "x1": 0.13, "y1": -0.12, "x2": 0.28, "y2": -0.14, "w": 0.04, "c": "#16171b"},
              {"k": "ellipse", "x": -0.20, "y": -0.02, "w": 0.16, "h": 0.04, "c": "#5a6b4a"},
              {"k": "ellipse", "x": 0.20, "y": -0.04, "w": 0.16, "h": 0.04, "c": "#5a6b4a"},
              {"k": "line", "x1": -0.20, "y1": 0.20, "x2": 0.20, "y2": 0.18, "w": 0.03, "c": "#16171b"},
              {"k": "line", "x1": -0.14, "y1": 0.15, "x2": -0.12, "y2": 0.24, "w": 0.02, "c": "#16171b"},
              {"k": "line", "x1": -0.04, "y1": 0.14, "x2": -0.03, "y2": 0.23, "w": 0.02, "c": "#16171b"},
              {"k": "line", "x1": 0.06, "y1": 0.14, "x2": 0.06, "y2": 0.23, "w": 0.02, "c": "#16171b"},
              {"k": "line", "x1": 0.15, "y1": 0.13, "x2": 0.15, "y2": 0.22, "w": 0.02, "c": "#16171b"},
          ], "uncommon")
HW22.shirt("skeleton_crew", "Skeleton Crew Tee",
           "Black with the ribs printed on in glow ink, so after dark you are just a "
           "skeleton walking about. Which is the point.",
           {"torso": "#16171b", "arms": "#16171b", "decal": "tee_ribs"}, "uncommon")
HW22.pants("dug_up", "Dug-Up Dungarees",
           "Work trousers in faded denim, grass-stained and dirt to the knee.",
           {"legs": "#4a5a6a", "weave": "denim", "cuff": "#3a2a1c"})
HW22.belt("gravekeeper_keys", "Gravekeeper's Keys",
          "A leather belt with the cemetery keys on an iron ring: the gate, the "
          "chapel, the crypt, and one nobody has found the lock for.",
          {"band": "#3a2a1c", "buckle": IRON, "width": 0.22, "weave": "leather",
           "pouch": "#2a2018"})


@HW22.weapon("gravediggers_spade", "Gravedigger's Spade",
             "A spade with a long memory. Whoever it puts down does not stay down: they "
             "climb back out as a skeleton, on your side.",
             {"kind": "melee", "damage": 32, "headshot": 1.1, "rpm": 74, "range": 10.5,
              "arc": 0.55, "sound": "swing", "knockback": 12,
              "on_kill": {"summon": SKELETON}},
             [["+", "A kill raises the victim as a Skeleton that fights for you for 20 "
                    "seconds (up to two at once)"],
              ["+", "Skeletons hunt the other side -- or the infected, in Last Light"],
              ["-", "Slow to swing: 74 a minute"],
              ["-", "No bonus on a headshot"]], rarity="legendary")
def _():
    wood, iron = "#5a3a22", "#55595f"
    return [
        part("cyl", [0, 0.0, 0.45], [0.14, 1.90, 0.14], wood, [PI / 2, 0, 0]),
        # the D-handle at the back
        part("torus", [0, 0.0, -0.62], [0.36, 0.08, 0.36], wood, [0, 0, PI / 2]),
        part("rbox", [0, 0.0, -0.46], [0.14, 0.10, 0.16], iron, m="metal"),
        # the socket and the blade: a broad plate, stood on its edge, worn bright
        place("cone", [0, 0.0, 1.46], [0.26, 0.34, 0.26], iron, r=[PI / 2, 0, 0], m="metal"),
        place("shield", [0, 0.0, 1.98], [0.80, 0.92, 0.55], iron, r=[0, -PI / 2, PI / 2],
              m="metal"),
        part("rbox", [0, 0.0, 2.40], [0.03, 0.56, 0.05], "#b8bec6", m="metal"),
        # a clod of grave dirt still on it
        part("sph", [0.06, 0.12, 2.00], [0.10, 0.24, 0.30], "#4a3424"),
    ]


@HW22.weapon("ecto_sprayer", "Ectoplasm Sprayer",
             "A brass garden pump filled with something green that hums. Whatever it "
             "touches glows -- through walls -- and moves like it is wading.",
             {"kind": "beam", "damage": 3, "headshot": 1.0, "rpm": 600, "mag": 0,
              "range": 42, "auto": True, "sound": "laser", "recoil": 0.05, "spread": 0.5,
              "beam": "#9fe870", "ramp": {"per_sec": 0.6, "max": 2.0},
              "heat": {"per_shot": 0.03, "cool": 0.18, "lock": 2.0, "label": "Slime"},
              "on_hit": {"slow": [0.3, 1.2], "reveal": 4.0}},
             [["+", "A stream of ectoplasm: slows what it touches by 30%"],
              ["+", "Anyone it touches is shown to your team through walls for 4 seconds"],
              ["-", "Only 42 studs of reach"],
              ["-", "Low damage until it has been on a target for a while"],
              ["-", "Runs dry after about eight seconds of spraying"]], rarity="legendary")
def _():
    brass, slime = "#c9a227", "#9fe870"
    return [
        part("rbox", [0, -0.30, 0.0], [0.18, 0.55, 0.22], "#3a2a1c", [-0.2, 0, 0]),
        part("cyl", [0, 0.20, 0.30], [0.50, 0.70, 0.50], slime, [PI / 2, 0, 0], m="glass", a=0.7),
        part("cyl", [0, 0.20, 0.30], [0.36, 0.60, 0.36], "#c8ffb0", [PI / 2, 0, 0], m="neon",
             a=0.6),
        part("torus", [0, 0.20, -0.06], [0.54, 0.08, 0.54], brass, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.20, 0.66], [0.54, 0.08, 0.54], brass, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.56, 0.30], [0.06, 0.40, 0.06], brass, m="metal"),
        part("rbox", [0, 0.78, 0.30], [0.30, 0.06, 0.06], brass, m="metal"),
        part("cyl", [0, 0.05, 1.10], [0.10, 0.90, 0.10], brass, [PI / 2, 0, 0], m="metal"),
        place("trumpet", [0, 0.05, 1.56], [0.30, 0.24, 0.30], brass, r=[PI / 2, 0, 0], m="metal"),
        part("sph", [0, 0.05, 1.70], [0.14, 0.14, 0.14], slime, m="neon"),
    ]


@HW22.weapon("coffin_nailer", "Coffin Nailer",
             "The undertaker's nail gun. It fires three-inch coffin nails through the "
             "first thing in the way and into the next, and a nail in the head pins "
             "its owner to the spot.",
             {"kind": "hitscan", "damage": 17, "headshot": 1.6, "rpm": 300, "mag": 14,
              "reload": 2.1, "spread": 1.2, "pellets": 1, "range": 160, "auto": True,
              "sound": "smg", "recoil": 0.8, "reserve": 70, "tracer": "#c9ced6",
              "pierce": 1, "on_headshot": {"root": 1.2}},
             [["+", "Nails go through the first person they hit and on into the next"],
              ["+", "A headshot nails the target to the floor for 1.2 seconds"],
              ["-", "Low damage per nail"],
              ["-", "Wide spread past middle range"]], rarity="legendary")
def _():
    body, grip = "#2b2f36", "#5a3a22"
    return [
        part("rbox", [0, 0.12, 0.40], [0.26, 0.36, 1.10], body, m="metal"),
        part("rbox", [0, -0.30, 0.0], [0.20, 0.55, 0.26], grip, [-0.3, 0, 0], decal="planks"),
        # the nail strip feeding in from below, at an angle
        part("rbox", [0, -0.14, 0.58], [0.06, 0.30, 0.46], "#c9ced6", [0.6, 0, 0], m="metal"),
        part("rbox", [0, -0.15, 0.58], [0.08, 0.04, 0.48], "#8a6a3a", [0.6, 0, 0]),
        part("rbox", [0, 0.12, 1.04], [0.18, 0.18, 0.18], "#c4281c"),
        part("cyl", [0, 0.06, 1.18], [0.08, 0.22, 0.08], "#9aa0a8", [PI / 2, 0, 0], m="metal"),
        # a coffin-shaped badge on the side
        part("rbox", [0.135, 0.14, 0.40], [0.02, 0.18, 0.40], BRASS, m="metal"),
        part("rbox", [0.14, 0.14, 0.40], [0.02, 0.04, 0.16], "#2b2420"),
    ]


@HW22.gear("candy_corn", "Fistful of Candy Corn",
           "The one sweet nobody admits to liking, and everybody eats. A sugar rush "
           "that makes you faster than is strictly safe.",
           {"kind": "consume", "cooldown": 25, "sound": "eat",
            "consume": {"heal": 10, "speed": [0.28, 6.0]}},
           [["+", "Run 28% faster for 6 seconds"],
            ["+", "Heals 10"],
            ["-", "25 second cooldown"]], rarity="uncommon")
def _():
    out = []
    # three kernels in a fan: yellow base, orange middle, white tip
    for k, (x, z, lean) in enumerate(((0.0, 0.16, 0.0), (0.12, 0.04, 0.45), (-0.12, 0.06, -0.45))):
        tilt = [0.0, 0.0, lean]
        base = rotate([0, 0.0, 0], tilt)
        mid = rotate([0, 0.20, 0], tilt)
        tip = rotate([0, 0.40, 0], tilt)
        out += [part("rbox", [x + base[0], 0.08 + base[1], z], [0.30, 0.12, 0.14], "#ffd36a", tilt),
                place("cone", [x + mid[0], 0.08 + mid[1], z], [0.30, 0.26, 0.14], "#ff8c1a", r=tilt),
                place("cone", [x + tip[0], 0.08 + tip[1], z], [0.16, 0.16, 0.08], "#fffaf0", r=tilt)]
    return out


HW22.effect("tombstone_rise", name="Tombstone Rise", rate=2.4, life=[2.2, 3.0],
            size=[0.34, 0.48], grow=0.05, gravity=-0.2, spread=0.5, rise=[0.2, 0.5],
            blend="normal", spin=0.4, colors=["#8d9196", "#a8acb0", "#6e7277"],
            shape="tombstone", radius=0.7, upright=True, wobble=0.3)
HW22.effect("coffin_waltz", name="Coffin Waltz", rate=2.0, life=[2.6, 3.2],
            size=[0.40, 0.52], grow=0.0, gravity=0.0, spread=0.15, rise=[0.05, 0.15],
            blend="normal", spin=0.8, colors=["#2b2420", "#4a3424", "#1a1512"],
            shape="coffin", radius=0.9, orbit=1.4, upright=True, wobble=0.4)
HW22.opening(
    sky={"top": "#06090a", "horizon": "#1c2a22", "sun": [0.2, 0.9, 0.6], "clouds": 0,
         "tint": "#a8d8b0"},
    ambient="#4e6a58", beam="#9fe870", seep="haunted_wisps", after="tombstone_rise",
    burst=["#9fe870", "#ece4d0", "#6bff9a", "#ffffff"],
    pieces=[{"shape": "bone", "colors": ["#ece4d0", "#d9d0b8"], "blend": "normal"},
            {"shape": "skull", "colors": ["#ece4d0", "#ffffff"], "blend": "normal"},
            {"shape": "tombstone", "colors": ["#8d9196", "#a8acb0"], "blend": "normal"},
            {"shape": "wisp", "colors": ["#b8ffd2", "#6bff9a"], "blend": "add"}],
    backdrop="graveyard", title_wait="Something is knocking...",
    title_shake="It wants out...")
HW22.award("Graveyard Shift", ["Night Watchman", "Grave Tender", "Bone Collector",
                               "Crypt Keeper", "Sexton", "Lord of the Graveyard"],
           "Opened Coffin Crates on the graveyard shift, Halloween 2022.", "em_coffin", "moon")
HW22.bundle("pair", "Coffin and Key", 1, 1050, "One Coffin Crate, one Skeleton Key.")
HW22.bundle("plot", "Family Plot", 3, 3000, "Three coffins, three keys. Saves 300.")


# ============================================================ 2023
HEX = "#b26bff"
BREW = "#7dff9a"
HW23 = Event(
    "halloween_2023", "halloween", 2023, "hw23",
    name="Witching Hour", title="The Witching Hour",
    blurb="In 2023 a coven moved into the hill above Harrow and the whole server "
          "smelled of woodsmoke and something green for a month. The cauldron is "
          "still warm. Do not drink from it.",
    tagline="Double, double, toil and trouble.",
    starts="2023-10-01", ends="2023-11-09",
    colors={"accent": HEX, "deep": "#140a1e", "glow": BREW},
    family_effects=["cursed_runes", "bat_swarm", "spider_descent", "candlelight_vigil"],
    hero_effect="witchs_brew", stencil="stencil_hw23")


@HW23.crate_model("Cauldron Crate",
                  "A black iron cauldron on three stubby legs, its lid chained shut and "
                  "something green bubbling up round the edge. Holds the Witching Hour "
                  "set. Needs a Broomstick Key.",
                  hinge=[0, 0.46, -0.84], keyhole=[0, -0.06, 0.84])
def _():
    iron, rim = "#24222a", "#3a3742"
    parts = [
        place("bowl", [0, -0.62, 0], [1.80, 1.80, 1.80], iron, anchor=[0, 0, 0], m="metal"),
        part("torus", [0, 0.44, 0], [1.86, 0.16, 1.86], rim, m="metal"),
        # three stubby legs
        *around(3, 0.62, 0, lambda a, x, z: place("cone", [x, -0.66, z], [0.24, 0.30, 0.24], iron,
                                                  r=[PI, 0, 0], m="metal"), start=PI / 3),
        # the lid, heavy iron, a ring for a handle
        part("cyl", [0, 0.53, 0], [1.78, 0.10, 1.78], rim, m="metal", lid=1),
        place("hemi", [0, 0.55, 0], [1.40, 0.30, 1.40], iron, anchor=[0, 0, 0], m="metal", lid=1),
        part("torus", [0, 0.82, 0], [0.34, 0.06, 0.34], rim, [PI / 2, 0, 0], m="metal", lid=1),
        # the chain over the lid and the padlock on the front
        part("rbox", [0, 0.58, 0.0], [0.08, 0.06, 1.88], "#5e5a66", m="metal", lid=1),
        part("rbox", [0, -0.06, 0.82], [0.34, 0.38, 0.10], "#5e5a66", m="metal", decal="keyhole",
             lock=1),
        part("torus", [0, 0.20, 0.82], [0.26, 0.05, 0.26], "#5e5a66", [PI / 2, 0, 0], m="metal"),
        # the runes on the side, and the brew showing at the rim
        part("box", [0, -0.10, -0.80], [0.90, 0.60, 0.02], "#000000", [0, PI, 0],
             decal="stencil_hw23", a=-1),
        part("cyl", [0, 0.44, 0], [1.66, 0.04, 1.66], BREW, m="neon"),
    ]
    # brew boiling over in drips, and bubbles caught on the lid's edge
    for k in range(7):
        a = k * TAU / 7 + 0.3
        parts.append(place("teardrop", [math.sin(a) * 0.90, 0.30, math.cos(a) * 0.90],
                           [0.12, 0.28, 0.12], BREW, r=[PI, 0, 0], m="glass", a=0.85))
    for k in range(5):
        a = k * 1.3
        parts.append(part("sph", [math.sin(a) * 0.70, 0.62, math.cos(a) * 0.70],
                          [0.12, 0.12, 0.12], "#c8ffb0", m="glass", a=0.6, lid=1))
    return parts


@HW23.key_model("Broomstick Key",
                "A witch's broom in miniature: a twig shaft, a bound bundle of straw for "
                "a bow, and teeth of black iron. Opens one Cauldron Crate.", shoulder=-0.36)
def _():
    straw, twine = "#c9a24a", "#6a3a1a"
    return [
        place("cone", [-0.66, 0, 0], [0.62, 0.62, 0.62], straw, r=[0, 0, PI / 2]),
        part("cyl", [-0.40, 0, 0], [0.24, 0.08, 0.24], twine, [0, 0, PI / 2]),
        part("cyl", [-0.50, 0, 0], [0.30, 0.06, 0.30], twine, [0, 0, PI / 2]),
        part("cyl", [0.12, 0, 0], [0.09, 1.10, 0.09], "#5a3a22", [0, 0, PI / 2]),
        part("rbox", [0.46, -0.12, 0], [0.08, 0.22, 0.08], "#24222a", m="metal"),
        part("rbox", [0.60, -0.16, 0], [0.08, 0.30, 0.08], "#24222a", m="metal"),
        part("sph", [0.68, 0, 0], [0.12, 0.12, 0.12], HEX, m="neon"),
    ]


@HW23.hat("coven_hat", "Midnight Coven Hat",
          "Tall, crooked and purple as a bruise, with a buckle of brass and a crescent "
          "moon pinned to the band. The point has a mind of its own.", "rare")
def _():
    felt = "#3a1f5a"
    return [
        place("brim", [0, -0.06, 0], [2.30, 1.30, 2.24], "#2a1640", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        place("cone", [0, 0.64, -0.02], [1.40, 1.36, 1.36], felt, decal="felt", wrap=True),
        place("cone", [0.10, 1.40, -0.12], [0.62, 0.62, 0.60], felt, r=[-0.30, 0, -0.35],
              decal="felt", wrap=True),
        place("cone", [0.30, 1.70, -0.30], [0.26, 0.40, 0.26], felt, r=[-0.9, 0, -0.8]),
        part("cyl", [0, 0.10, 0], [1.38, 0.20, 1.34], "#1a0d2a"),
        *buckle([0, 0.10, 0.69], 0.32, 0.22, BRASS, plate="#1a0d2a"),
        place("crescent", [-0.45, 0.30, 0.56], 0.34, "#fff3b0", r=[-0.2, -0.5, 0.3], m="neon"),
        place("star", [0.40, 0.72, 0.42], 0.14, "#fff3b0", r=[-0.3, 0.6, 0], m="neon"),
        place("star", [-0.20, 0.96, 0.32], 0.10, "#fff3b0", r=[-0.3, -0.4, 0], m="neon"),
    ]


@HW23.hat("cauldron_cap", "Bubbling Cauldron",
          "A little cauldron, worn like a helmet and still on the boil. The ladle is "
          "for stirring, not for tasting.", "legendary")
def _():
    iron = "#24222a"
    parts = [
        place("bowl", [0, -0.30, 0], [1.74, 1.40, 1.74], iron, anchor=[0, 0, 0], m="metal"),
        part("torus", [0, 0.53, 0], [1.76, 0.12, 1.76], "#3a3742", m="metal"),
        part("cyl", [0, 0.50, 0], [1.62, 0.05, 1.62], BREW, m="neon"),
        # the ladle leaning on the rim
        part("cyl", [0.42, 0.86, -0.20], [0.06, 1.0, 0.06], "#5a3a22", [0.2, 0, -0.5]),
        place("bowl", [0.22, 0.46, -0.10], [0.30, 0.30, 0.30], "#5a3a22", anchor=[0, 0, 0]),
    ]
    for k, (x, z, s) in enumerate(((0.2, 0.3, 0.22), (-0.3, 0.1, 0.30), (0.1, -0.35, 0.18),
                                   (-0.15, 0.45, 0.14), (0.38, -0.05, 0.16))):
        parts.append(part("sph", [x, 0.58 + s * 0.3, z], [s, s, s], "#c8ffb0", m="glass", a=0.65))
    return parts


@HW23.hat("toad_prince", "Toad Prince",
          "A toad in a gold crown, sat on your head, waiting for a kiss that is not "
          "coming. It has been waiting since the last coven.", "uncommon", hair="show")
def _():
    green, belly = "#4f8a3c", "#c8d890"
    return [
        part("sph", [0, 0.26, -0.05], [0.90, 0.58, 1.00], green),
        part("sph", [0, 0.20, 0.20], [0.70, 0.36, 0.60], belly),
        part("sph", [0.24, 0.56, 0.24], [0.26, 0.26, 0.26], green),
        part("sph", [-0.24, 0.56, 0.24], [0.26, 0.26, 0.26], green),
        part("sph", [0.26, 0.60, 0.34], [0.14, 0.16, 0.08], "#16171b"),
        part("sph", [-0.26, 0.60, 0.34], [0.14, 0.16, 0.08], "#16171b"),
        part("rbox", [0, 0.34, 0.47], [0.44, 0.03, 0.06], "#2d5a22"),
        part("sph", [0.44, 0.10, 0.10], [0.30, 0.20, 0.50], green, [0, 0.4, 0]),
        part("sph", [-0.44, 0.10, 0.10], [0.30, 0.20, 0.50], green, [0, -0.4, 0]),
        place("spikecrown", [0, 0.58, -0.04], [0.42, 0.24, 0.42], GOLD, anchor=[0, 0, 0],
              m="metal"),
    ]


@HW23.hat("black_cat", "Familiar",
          "A black cat curled up on your head, tail over its nose, one green eye "
          "open. It goes where you go now. It chose.", "rare", hair="show")
def _():
    fur = "#17151c"
    return [
        part("sph", [0, 0.22, -0.05], [1.10, 0.46, 0.96], fur, decal="fur", wrap=True),
        part("sph", [0.30, 0.36, 0.34], [0.46, 0.40, 0.42], fur, decal="fur", wrap=True),
        place("tri", [0.44, 0.64, 0.36], [0.20, 0.24, 0.6], fur, r=[0, -0.3, -0.2]),
        place("tri", [0.18, 0.64, 0.38], [0.20, 0.24, 0.6], fur, r=[0, 0.3, 0.2]),
        part("sph", [0.40, 0.40, 0.55], [0.10, 0.07, 0.04], BREW, m="neon"),
        part("rbox", [0.20, 0.40, 0.55], [0.10, 0.02, 0.03], "#3a3742"),
        part("sph", [0.30, 0.31, 0.56], [0.05, 0.04, 0.03], "#ff8fa8"),
        # the tail, wrapped round to the front
        part("cyl", [-0.30, 0.20, 0.42], [0.13, 0.80, 0.13], fur, [PI / 2, 0.9, 0]),
        part("sph", [0.05, 0.22, 0.60], [0.16, 0.16, 0.16], fur),
    ]


@HW23.hat("crystal_ball", "Scryer's Circlet",
          "A silver circlet and a crystal ball held over the brow, purple mist "
          "turning inside it. Look in and it looks back.", "legendary", hair="show")
def _():
    return [
        band(-0.16, 0.06, SILVER, grow=-0.10, m="metal"),
        part("rbox", [0, -0.05, 0.75], [0.16, 0.24, 0.04], SILVER, m="metal"),
        part("cyl", [0, 0.10, 0.76], [0.05, 0.20, 0.05], SILVER, m="metal"),
        place("ring", [0, 0.18, 0.76], [0.50, 0.6, 0.50], SILVER, anchor=[0, 0, 0], m="metal"),
        part("sph", [0, 0.46, 0.76], [0.56, 0.56, 0.56], "#e9dcff", m="glass", a=0.4),
        part("sph", [0, 0.46, 0.76], [0.38, 0.30, 0.38], HEX, m="neon", a=0.6, spin=1.0),
        place("spiral", [0, 0.40, 0.76], [0.30, 0.20, 0.30], "#e9dcff", m="neon", a=0.5, spin=2.0),
        *[place("star", [math.sin(a) * 0.80, -0.10, math.cos(a) * 0.78], 0.10, "#e9dcff",
                r=[0, a, 0], m="neon") for a in (-0.9, -0.45, 0.45, 0.9)],
    ]


@HW23.hat("grimoire_stack", "Grimoire Stack",
          "Three spellbooks, a candle melting into the top one, and a bookmark that "
          "is definitely a lizard's tail.", "rare")
def _():
    parts = [
        part("rbox", [0, 0.10, 0], [1.40, 0.24, 1.10], "#4a1a2a", [0, 0.1, 0], decal="leather",
             wrap=True),
        part("rbox", [0, 0.10, 0.02], [1.34, 0.18, 1.06], "#efe4c4", [0, 0.1, 0]),
        part("rbox", [0.05, 0.34, 0], [1.24, 0.22, 0.96], "#1f3a4a", [0, -0.25, 0],
             decal="leather", wrap=True),
        part("rbox", [-0.04, 0.55, 0], [1.08, 0.20, 0.84], "#3a2a1a", [0, 0.35, 0],
             decal="leather", wrap=True),
        part("cyl", [0.20, 0.82, 0.10], [0.20, 0.36, 0.20], "#f4ecd8"),
        place("flame", [0.20, 1.06, 0.10], [0.18, 0.26, 0.18], "#ffd36a", m="neon", spin=2.0),
        place("teardrop", [0.30, 0.68, 0.18], [0.10, 0.18, 0.10], "#f4ecd8", r=[PI, 0, 0]),
        place("tentacle", [-0.58, 0.40, 0.30], [0.30, 0.40, 0.40], "#4f8a3c", r=[0, 0, 1.6]),
        cap(-0.20, 0.0, "#2a1640"),
    ]
    for k in range(3):
        parts.append(part("rbox", [0.63, 0.10 + k * 0.22, 0], [0.02, 0.05, 0.90], GOLD_DARK,
                          m="metal"))
    return parts


@HW23.hat("mandrake", "Mandrake Sprout",
          "Pulled up a mandrake and it decided to grow on you instead. It only "
          "screams when somebody else pulls it.", "uncommon", hair="show")
def _():
    root, leaf = "#c9a07a", "#4b7a2e"
    parts = [
        part("sph", [0, 0.10, 0], [0.62, 0.30, 0.56], "#4a3424"),
        part("sph", [0, 0.40, 0.05], [0.50, 0.56, 0.46], root),
        part("sph", [0.11, 0.48, 0.27], [0.10, 0.12, 0.05], "#16171b"),
        part("sph", [-0.11, 0.48, 0.27], [0.10, 0.12, 0.05], "#16171b"),
        part("sph", [0, 0.32, 0.28], [0.14, 0.18, 0.05], "#3a1a1a"),
        part("cyl", [0.26, 0.40, 0.06], [0.06, 0.34, 0.06], root, [0, 0, -0.9]),
        part("cyl", [-0.26, 0.40, 0.06], [0.06, 0.34, 0.06], root, [0, 0, 0.9]),
    ]
    for k in range(6):
        a = k * TAU / 6
        parts.append(place("leaf", [math.sin(a) * 0.08, 0.66, math.cos(a) * 0.08],
                           [1.0, 0.70, 1.0], leaf, anchor=[0, -0.5, 0],
                           r=[math.cos(a) * 0.6, a, -math.sin(a) * 0.6]))
    return parts


@HW23.back("broomstick", "Broomstick",
           "A proper witch's broom, slung across the back on a strap, bristles up. "
           "Flying lessons sold separately.", "rare")
def _():
    return [
        part("cyl", [0, 0.30, -0.24], [0.10, 2.30, 0.10], "#5a3a22", [0, 0, 0.9]),
        place("cone", [-0.92, 1.00, -0.24], [0.70, 0.90, 0.70], "#c9a24a", r=[0, 0, 0.9 + PI]),
        part("cyl", [-0.66, 0.78, -0.24], [0.30, 0.08, 0.30], "#6a3a1a", [0, 0, 0.9]),
        part("cyl", [-0.74, 0.86, -0.24], [0.36, 0.06, 0.36], "#6a3a1a", [0, 0, 0.9]),
        part("rbox", [0, 0.40, -0.10], [0.16, 0.10, 0.10], "#3a2a1c"),
        *straps("#3a2a1c", 0.34, 0.12),
    ]


@HW23.back("starry_cloak", "Starry Cloak",
           "Midnight purple, lined with the night sky: the stars on the inside are "
           "real, or close enough, and one of them is moving.", "uncommon")
def _():
    return [
        place("cape", [0, 0.98, -0.08], [1.70, 1.92, 1.5], "#2a1640", anchor=[0, 0, 0],
              decal="starfield", wrap=True),
        part("rbox", [0, 0.96, -0.14], [1.40, 0.14, 0.16], "#1a0d2a"),
        place("crescent", [0.46, 0.96, -0.25], 0.22, "#fff3b0", r=[0, PI, 0], m="neon"),
        place("star", [-0.46, 0.96, -0.25], 0.16, "#fff3b0", r=[0, PI, 0], m="neon"),
    ]


@HW23.hairdo("wild_witch", "Wild Witch Locks",
             "Long, black-purple and full of the wind off the hill, with a sprig of "
             "something that is probably poisonous.", "rare")
def _():
    c, hi = "#1e1426", "#3a2a4a"
    return [
        place("hairlong", [0, 0, 0], [1.06, 1.06, 1.06], c, anchor=[0, 0, 0],
              decal="strands", wrap=True),
        place("teardrop", [0.42, -0.30, -0.30], [0.30, 0.60, 0.26], hi, anchor=[0, 0.4, 0],
              r=[0.3, 0, -0.4]),
        place("teardrop", [-0.42, -0.34, -0.28], [0.30, 0.62, 0.26], c, anchor=[0, 0.4, 0],
              r=[0.3, 0, 0.4]),
        place("leaf", [0.44, 0.36, 0.22], [0.8, 0.36, 1.0], "#4b7a2e", r=[0, 0.4, -0.6]),
        part("sph", [0.48, 0.30, 0.30], [0.08, 0.08, 0.08], HEX, m="glass"),
    ]


@HW23.hairdo("moonlit_braid", "Moonlit Braid",
             "One long braid, silver as moonlight, down to the small of the back.",
             "uncommon")
def _():
    c = "#c9ccd8"
    parts = [place("hairmid", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k in range(6):
        parts.append(part("sph", [0.03 * (1 if k % 2 else -1), -0.20 - k * 0.20, -0.60],
                          [0.24 - k * 0.012, 0.24, 0.20], shade(c, 1.05 if k % 2 else 0.92)))
    parts.append(part("cyl", [0, -1.36, -0.60], [0.16, 0.06, 0.16], HEX))
    return parts


HW23.face("hex_eyes", "Hexed",
          "Spirals where the eyes should be. Whoever cast it is not saying.", [
              {"k": "ring", "x": -0.20, "y": -0.14, "r": 0.10, "w": 0.03, "c": "#16171b"},
              {"k": "ring", "x": -0.20, "y": -0.14, "r": 0.055, "w": 0.03, "c": "#7a3ad6"},
              {"k": "ellipse", "x": -0.20, "y": -0.14, "w": 0.03, "h": 0.03, "c": "#16171b"},
              {"k": "ring", "x": 0.20, "y": -0.14, "r": 0.10, "w": 0.03, "c": "#16171b"},
              {"k": "ring", "x": 0.20, "y": -0.14, "r": 0.055, "w": 0.03, "c": "#7a3ad6"},
              {"k": "ellipse", "x": 0.20, "y": -0.14, "w": 0.03, "h": 0.03, "c": "#16171b"},
              {"k": "arc", "x": 0, "y": 0.05, "r": 0.16, "a0": 0.15, "a1": 0.35, "w": 0.04,
               "c": "#16171b"},
          ], "uncommon")
HW23.face("warty_grin", "Warty Grin",
          "A crooked, gap-toothed grin, a wart on the chin, and an eyebrow that will "
          "not come down.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.06, "h": 0.08, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.06, "h": 0.08, "c": "#16171b"},
              {"k": "line", "x1": 0.12, "y1": -0.28, "x2": 0.30, "y2": -0.22, "w": 0.04, "c": "#16171b"},
              {"k": "line", "x1": -0.30, "y1": -0.24, "x2": -0.12, "y2": -0.24, "w": 0.04, "c": "#16171b"},
              {"k": "poly", "pts": [[-0.22, 0.12], [0.24, 0.06], [0.18, 0.22], [-0.16, 0.22]],
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.08, 0.11], [-0.02, 0.10], [-0.03, 0.15], [-0.08, 0.15]],
               "c": "#fffaf0"},
              {"k": "poly", "pts": [[0.06, 0.09], [0.12, 0.08], [0.11, 0.13], [0.06, 0.14]],
               "c": "#fffaf0"},
              {"k": "ellipse", "x": 0.10, "y": 0.33, "w": 0.05, "h": 0.05, "c": "#6b8a3a"},
          ], "rare")
HW23.shirt("coven_robe", "Coven Robe",
           "Deep purple robes with silver stars, and sleeves wide enough to hide a "
           "wand, a toad, or both.",
           {"torso": "#3a1f5a", "arms": "#3a1f5a", "decal": "tee_moon", "weave": "felt",
            "stripe": "#c9ccd8"}, "rare")
HW23.pants("striped_stockings", "Striped Stockings",
           "Purple and black, stripe after stripe, all the way down.",
           {"legs": "#2a1640", "weave": "witch_stripes"})
HW23.belt("potion_bandolier", "Potion Bandolier",
          "A belt of little bottles: green, purple, and one that is not labelled.",
          {"band": "#3a2a1c", "buckle": BRASS, "width": 0.24, "weave": "leather",
           "pouch": "#7dff9a", "glow": True})


@HW23.weapon("hexing_broom", "Hexing Broom",
             "A broom that swings itself. Each sweep carries you forward with it, and "
             "whoever it catches is swept off their feet -- they cannot jump for a "
             "moment.",
             {"kind": "melee", "damage": 24, "headshot": 1.0, "rpm": 110, "range": 11.5,
              "arc": 0.78, "sound": "swing", "knockback": 9,
              "lunge": {"speed": 26}, "on_hit": {"jumpless": 2.0, "slow": [0.2, 1.0]}},
             [["+", "Each swing lunges you forward"],
              ["+", "A wide sweep: whoever it hits cannot jump for 2 seconds, and is slowed"],
              ["-", "20% less damage than a Blockblade"],
              ["-", "The lunge will happily carry you off a ledge"]], rarity="legendary")
def _():
    return [
        part("cyl", [0, 0.0, 0.40], [0.10, 2.0, 0.10], "#5a3a22", [PI / 2, 0, 0]),
        part("cyl", [0, 0.0, -0.40], [0.12, 0.30, 0.12], "#3a2a1c", [PI / 2, 0, 0]),
        part("cyl", [0, 0.0, 1.40], [0.26, 0.12, 0.26], "#6a3a1a", [PI / 2, 0, 0]),
        part("cyl", [0, 0.0, 1.52], [0.30, 0.08, 0.30], "#6a3a1a", [PI / 2, 0, 0]),
        place("cone", [0, 0.0, 2.02], [0.72, 1.0, 0.72], "#c9a24a", r=[-PI / 2, 0, 0]),
        part("sph", [0, 0.0, 2.30], [0.70, 0.50, 0.40], "#c9a24a", a=0.0),
        place("star", [0, 0.16, 1.46], 0.12, HEX, r=[0, PI / 2, 0], m="neon"),
    ]


@HW23.weapon("cauldron_bubbler", "Cauldron Bubbler",
             "Lobs a stoppered flask of the coven's brew. It breaks into a cloud of "
             "green that poisons whoever stands in it.",
             {"kind": "projectile", "projectile": "flask", "damage": 18, "splash": 4.0,
              "splash_damage": 14, "rpm": 50, "mag": 3, "reload": 2.4, "speed": 54,
              "range": 260, "auto": False, "sound": "throw", "recoil": 1.2, "reserve": 18,
              "gravity_scale": 1.3, "self_damage": 0.0, "knockback": 4,
              "ground_zone": {"radius": 7.0, "secs": 5.0, "color": "#7dff9a",
                              "particle": "bubble", "enemy": {"poison": [7, 1.0]},
                              "name": "Witch's Brew"}},
             [["+", "The flask leaves a cloud of brew for 5 seconds: 7 poison a second to "
                    "enemies inside"],
              ["+", "Your own brew cannot hurt you"],
              ["-", "A small blast on its own"],
              ["-", "A slow, high lob"]], rarity="legendary",
             proj=lambda: [part("sph", [0, 0, 0], [0.50, 0.50, 0.50], "#7dff9a", m="glass", a=0.8),
                           part("cyl", [0, 0, 0.34], [0.16, 0.24, 0.16], "#c8ffb0",
                                [PI / 2, 0, 0], m="glass", a=0.8),
                           part("cyl", [0, 0, 0.50], [0.18, 0.10, 0.18], "#6a3a1a", [PI / 2, 0, 0])])
def _():
    return [
        part("rbox", [0, -0.28, 0.0], [0.18, 0.52, 0.22], "#3a2a1c", [-0.2, 0, 0]),
        place("bowl", [0, 0.0, 0.50], [0.70, 0.90, 0.70], "#24222a", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.0, 1.06], [0.72, 0.08, 0.72], "#3a3742", [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.0, 1.02], [0.60, 0.04, 0.60], BREW, [PI / 2, 0, 0], m="neon"),
        part("rbox", [0, 0.10, 0.20], [0.14, 0.14, 0.60], "#5a3a22"),
        part("sph", [0, 0.20, 1.10], [0.16, 0.16, 0.16], "#c8ffb0", m="glass", a=0.6),
    ]


@HW23.weapon("toad_wand", "Toad Wand",
             "A crooked hawthorn wand that does one thing and does it well. Whoever "
             "the bolt hits spends the next few seconds as a toad.",
             {"kind": "projectile", "projectile": "spellbolt", "damage": 12, "splash": 2.2,
              "splash_damage": 12, "rpm": 34, "mag": 1, "reload": 3.2, "speed": 96,
              "range": 300, "auto": False, "sound": "magic", "recoil": 0.6, "reserve": 20,
              "gravity_scale": 0.0, "self_damage": 0.0, "knockback": 2,
              "homing": {"turn": 2.4, "range": 26}, "tracer": "#b26bff",
              "on_hit": {"polymorph": 2.5}},
             [["+", "A slow, seeking bolt: whoever it hits is a toad for 2.5 seconds -- "
                    "slow, and unable to use anything"],
              ["-", "Hardly any damage"],
              ["-", "One bolt, then a long reload"]], rarity="legendary",
             proj=lambda: [part("sph", [0, 0, 0], [0.40, 0.40, 0.40], "#e9dcff", m="neon"),
                           part("sph", [0, 0, 0], [0.70, 0.70, 0.70], HEX, m="neon", a=0.35),
                           place("star", [0, 0, -0.30], 0.30, HEX, m="neon", spin=6.0)])
def _():
    wood = "#4a2f1b"
    return [
        part("cyl", [0, 0.0, 0.40], [0.08, 1.40, 0.08], wood, [PI / 2, 0, 0]),
        part("cyl", [0.03, 0.04, 0.70], [0.06, 0.30, 0.06], wood, [PI / 2, 0.4, 0]),
        part("cyl", [0, 0.0, -0.20], [0.12, 0.40, 0.12], "#2a1a10", [PI / 2, 0, 0]),
        part("sph", [0, 0.0, 1.14], [0.14, 0.14, 0.14], "#4f8a3c", m="glass"),
        part("sph", [0, 0.0, 1.14], [0.26, 0.26, 0.26], HEX, m="neon", a=0.3),
    ]


@HW23.gear("flying_ointment", "Flying Ointment",
           "A jar of greasy green salve the coven swears by. Rub it on and the "
           "ground stops pulling quite so hard.",
           {"kind": "consume", "cooldown": 30, "sound": "drink",
            "consume": {"jump": [0.45, 8.0], "speed": [0.10, 8.0]}},
           [["+", "Gravity drops to under half for 8 seconds: long, floaty jumps"],
            ["+", "10% faster while it lasts"],
            ["-", "30 second cooldown"]], rarity="rare")
def _():
    return [
        part("cyl", [0, 0.10, 0.10], [0.44, 0.44, 0.44], "#7dff9a", m="glass", a=0.7),
        part("cyl", [0, 0.36, 0.10], [0.48, 0.10, 0.48], "#3a2a1c"),
        part("cyl", [0, 0.06, 0.10], [0.30, 0.30, 0.30], "#4f8a3c"),
        part("box", [0, 0.12, 0.222], [0.24, 0.20, 0.01], "#efe4c4"),
    ]


HW23.effect("witchs_brew", name="Witch's Brew", rate=6.0, life=[1.4, 2.0],
            size=[0.14, 0.30], grow=0.3, gravity=-1.4, spread=0.6, rise=[0.5, 1.0],
            blend="add", spin=0.0, colors=["#7dff9a", "#c8ffb0", "#b26bff"],
            shapes=["bubble", "bubble", "potion"], radius=0.5)
HW23.effect("starry_hex", name="Starry Hex", rate=4.0, life=[1.8, 2.6],
            size=[0.18, 0.34], grow=0.0, gravity=0.0, spread=0.2, rise=[0.1, 0.3],
            blend="add", spin=1.5, colors=["#fff3b0", "#e9dcff", "#b26bff"],
            shapes=["star", "rune"], radius=0.8, orbit=1.6, wobble=0.3)
HW23.opening(
    sky={"top": "#0a0614", "horizon": "#2a1640", "sun": [0.2, 0.9, 0.6], "clouds": 0,
         "tint": "#c8a8ff"},
    ambient="#5c4a86", beam="#7dff9a", seep="witchs_brew", after="starry_hex",
    burst=["#7dff9a", "#b26bff", "#fff3b0", "#ffffff"],
    pieces=[{"shape": "potion", "colors": ["#7dff9a", "#b26bff"], "blend": "normal"},
            {"shape": "bat", "colors": ["#2a1640", "#1a0d2a"], "blend": "normal"},
            {"shape": "star", "colors": ["#fff3b0", "#e9dcff"], "blend": "add"},
            {"shape": "bubble", "colors": ["#c8ffb0", "#7dff9a"], "blend": "add"}],
    backdrop="witch", title_wait="The brew is coming to the boil...",
    title_shake="Double, double...")
HW23.award("Witching Hour", ["Herb Gatherer", "Apprentice", "Hedge Witch", "Cauldron Keeper",
                             "High Priestess", "Mother of the Coven"],
           "Opened Cauldron Crates at the Witching Hour, Halloween 2023.", "em_cauldron", "moon")
HW23.bundle("pair", "Cauldron and Broom", 1, 1050, "One Cauldron Crate, one Broomstick Key.")
HW23.bundle("coven", "Coven of Three", 3, 3000, "Three cauldrons, three keys. Saves 300.")


# ============================================================ 2024
CANDLE = "#ffd36a"
OXBLOOD = "#4a0f1a"
GHOST = "#e9f4ff"
HW24 = Event(
    "halloween_2024", "halloween", 2024, "hw24",
    name="Manor of Whispers", title="The Manor of Whispers",
    blurb="Halloween 2024 opened the doors of Whisper Manor: forty rooms, one "
          "candelabra, and a family portrait whose eyes follow you down the hall. "
          "The seance in the parlour is still going. Nobody has found the off switch.",
    tagline="Somebody is still home.",
    starts="2024-10-01", ends="2024-11-09",
    colors={"accent": "#c9a227", "deep": "#1a0f14", "glow": CANDLE},
    family_effects=["candlelight_vigil", "haunted_wisps", "spider_descent", "raven_feathers"],
    hero_effect="seance_eyes", stencil="stencil_hw24")


@HW24.crate_model("Whisper Manor Crate",
                  "The manor in miniature: black boards, a gabled roof that lifts, every "
                  "window lit, and a front door with a lock that whispers. Holds the "
                  "Manor of Whispers set. Needs a Candelabra Key.",
                  hinge=[0, 0.46, -0.58], keyhole=[0, -0.22, 0.62])
def _():
    boards, trim, roof = "#2a2024", "#c9a227", "#1e1a22"
    parts = [
        part("rbox", [0, 0.0, 0], [1.70, 0.90, 1.14], boards, decal="planks", wrap=True),
        # the roof, which is the lid: two slopes and a ridge with a weathervane bat
        part("wedge", [0, 0.72, 0.30], [1.82, 0.50, 0.62], roof, lid=1, decal="shingles", wrap=True),
        part("wedge", [0, 0.72, -0.30], [1.82, 0.50, 0.62], roof, [0, PI, 0], lid=1,
             decal="shingles", wrap=True),
        part("rbox", [0, 0.50, 0], [1.86, 0.08, 1.24], trim, m="metal", lid=1),
        part("rbox", [0, 0.98, 0], [1.84, 0.05, 0.06], trim, m="metal", lid=1),
        part("cyl", [0.62, 1.12, 0], [0.04, 0.30, 0.04], IRON, m="metal", lid=1),
        place("bat", [0.62, 1.30, 0], [0.40, 0.40, 1.0], IRON, m="metal", lid=1),
        # a chimney
        part("rbox", [-0.55, 0.92, -0.18], [0.24, 0.40, 0.24], "#4a2a2a", decal="bricks", lid=1),
        # the front: two lit windows, the door with the lock
        part("rbox", [0, -0.12, 0.575], [0.36, 0.62, 0.04], OXBLOOD, decal="planks"),
        part("rbox", [0, -0.22, 0.60], [0.24, 0.24, 0.06], trim, m="metal", decal="keyhole",
             lock=1),
        part("box", [0, 0.0, 0.0], [1.62, 0.04, 1.06], CANDLE, m="neon"),
        part("box", [0, 0.40, 0], [1.62, 0.04, 1.06], CANDLE, m="neon"),
        # the stencil on the back wall
        part("box", [0, 0.0, -0.585], [1.10, 0.66, 0.02], "#000000", [0, PI, 0],
             decal="stencil_hw24", a=-1),
    ]
    for x in (-0.55, 0.55):
        parts += [part("box", [x, 0.10, 0.575], [0.34, 0.40, 0.02], CANDLE, m="neon"),
                  part("rbox", [x, 0.10, 0.585], [0.40, 0.46, 0.02], trim, m="metal", a=0.0),
                  part("rbox", [x, 0.10, 0.59], [0.03, 0.40, 0.03], "#1e1a22"),
                  part("rbox", [x, 0.10, 0.59], [0.34, 0.03, 0.03], "#1e1a22"),
                  part("rbox", [x, -0.12, 0.60], [0.42, 0.05, 0.08], trim, m="metal")]
    for x in (-0.86, 0.86):
        parts += [part("box", [x, 0.10, 0.0], [0.02, 0.36, 0.30], CANDLE, m="neon"),
                  part("rbox", [x, 0.10, 0.0], [0.04, 0.42, 0.36], "#1e1a22", a=0.0)]
    parts += [part("cyl", [0.20, -0.30, 0.66], [0.05, 0.05, 0.05], trim, [PI / 2, 0, 0], m="metal")]
    return parts


@HW24.key_model("Candelabra Key",
                "A gold key whose bow is a candelabra, three candles lit and never "
                "burning down. Opens one Whisper Manor Crate.", shoulder=-0.32)
def _():
    gold = "#c9a227"
    parts = [
        part("cyl", [-0.62, -0.10, 0], [0.30, 0.06, 0.30], gold, m="metal"),
        part("cyl", [-0.62, 0.06, 0], [0.06, 0.34, 0.06], gold, m="metal"),
        place("arch", [-0.62, 0.20, 0], [0.62, 0.40, 1.0], gold, anchor=[0, 0, 0], m="metal"),
        part("cyl", [0.12, 0, 0], [0.09, 1.06, 0.09], gold, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.44, -0.12, 0], [0.08, 0.22, 0.08], gold, m="metal"),
        part("rbox", [0.58, -0.17, 0], [0.08, 0.30, 0.08], gold, m="metal"),
        part("torus", [-0.28, 0, 0], [0.20, 0.07, 0.20], GOLD_DARK, [0, 0, PI / 2], m="metal"),
    ]
    for x, h in ((-0.93, 0.30), (-0.62, 0.40), (-0.31, 0.30)):
        parts += [part("cyl", [x, 0.30 + h / 2, 0], [0.10, h, 0.10], "#f4ecd8"),
                  place("flame", [x, 0.42 + h, 0], [0.12, 0.18, 0.12], CANDLE, m="neon")]
    return parts


@HW24.hat("candelabra_crown", "Candelabra Crown",
          "Three arms of tarnished gold, three candles lit, and a slow river of "
          "wax down the back of your neck. Worth it.", "legendary")
def _():
    gold = "#c9a227"
    parts = [
        band(-0.16, 0.10, gold, grow=-0.08, m="metal"),
        cap(-0.20, 0.04, OXBLOOD, decal="felt", wrap=True),
        part("cyl", [0, 0.14, 0], [0.44, 0.10, 0.44], gold, m="metal"),
        part("cyl", [0, 0.40, 0], [0.10, 0.46, 0.10], gold, m="metal"),
        part("sph", [0, 0.40, 0], [0.18, 0.12, 0.18], gold, m="metal"),
        place("arch", [0, 0.56, 0], [1.10, 0.56, 1.4], gold, anchor=[0, 0, 0], m="metal"),
    ]
    for x, h in ((-0.56, 0.36), (0.0, 0.50), (0.56, 0.36)):
        base = 0.56 + (0.30 if x == 0 else 0.0)
        parts += [part("cyl", [x, base + 0.04, 0], [0.24, 0.06, 0.24], gold, m="metal"),
                  part("cyl", [x, base + 0.06 + h / 2, 0], [0.14, h, 0.14], "#f4ecd8"),
                  place("teardrop", [x + 0.06, base + 0.06 + h * 0.75, 0.06], [0.06, 0.16, 0.06],
                        "#f4ecd8", r=[PI, 0, 0]),
                  place("flame", [x, base + 0.16 + h, 0], [0.16, 0.24, 0.16], CANDLE, m="neon",
                        spin=1.6),
                  part("sph", [x, base + 0.14 + h, 0], [0.30, 0.30, 0.30], CANDLE, m="neon", a=0.25)]
    return parts


@HW24.hat("mourning_veil", "Widow's Veil",
          "A little black hat with a sweep of lace down over the eyes. She has been "
          "in mourning for a hundred and forty years and has not tired of it.", "rare",
          hair="show")
def _():
    return [
        part("cyl", [-0.30, 0.12, 0.10], [0.80, 0.22, 0.70], "#141016", [0.0, 0.2, 0.18],
             decal="felt", wrap=True),
        part("cyl", [-0.30, 0.04, 0.10], [1.10, 0.04, 0.96], "#141016", [0.0, 0.2, 0.18]),
        place("feather", [-0.66, 0.40, -0.10], 0.80, "#2a2230", anchor=[0, -0.5, 0],
              r=[-0.3, -PI / 2, 0.6]),
        part("sph", [-0.10, 0.20, 0.48], [0.14, 0.14, 0.14], "#8a1020", m="glass"),
        # the veil, lace down to the nose
        part("box", [0, -0.24, 0.725], [1.20, 0.46, 0.008], "#16121a", decal="lace", a=0.55),
        part("box", [0, 0.0, 0.66], [1.20, 0.008, 0.16], "#16121a", decal="lace", a=0.55),
    ]


@HW24.hat("sheet_ghost", "Bedsheet Ghost",
          "The oldest costume there is: a sheet with two holes. Except nobody is "
          "sure whether there is anybody inside this one.", "uncommon", hair="hide",
          face_cover=True)
def _():
    return [
        # a round top over straight sides, like a sheet thrown over a head
        dome(-0.30, 0.70, GHOST, decal="linen", wrap=True),
        part("cyl", [0, -0.76, 0], [1.86, 0.96, 1.80], GHOST, decal="linen", wrap=True),
        part("sph", [0.26, -0.50, 0.90], [0.22, 0.28, 0.05], "#16171b"),
        part("sph", [-0.26, -0.50, 0.90], [0.22, 0.28, 0.05], "#16171b"),
        place("ruffle", [0, -1.20, 0], [1.96, 2.0, 1.92], GHOST, anchor=[0, 0, 0], decal="linen",
              wrap=True),
    ]


@HW24.hat("poltergeist_plates", "Poltergeist Tea Party",
          "The good china, in the air, going round and round your head and "
          "rattling. The teapot is pouring. Nobody is holding it.", "rare", hair="show")
def _():
    china, rim = "#f4f6f8", "#4a6ab0"
    parts = [part("torus", [0, 0.50, 0], [1.90, 0.01, 1.86], GHOST, m="neon", a=0.15, spin=0.5)]
    for k in range(5):
        a = k * TAU / 5
        x, z = math.sin(a) * 0.95, math.cos(a) * 0.92
        y = 0.40 + 0.18 * math.sin(a * 2)
        if k % 2 == 0:
            parts += [part("cyl", [x, y, z], [0.46, 0.04, 0.46], china, [0.3, a, 0.2]),
                      part("torus", [x, y + 0.02, z], [0.46, 0.02, 0.46], rim, [0.3, a, 0.2])]
        else:
            parts += [place("bowl", [x, y - 0.12, z], [0.30, 0.34, 0.30], china, anchor=[0, 0, 0],
                            r=[0.4, a, 0.3]),
                      part("torus", [x + 0.16, y, z], [0.12, 0.03, 0.12], china, [0.4, a, PI / 2])]
    # the teapot over the crown, pouring into nothing
    parts += [part("sph", [0, 0.92, 0], [0.50, 0.40, 0.44], china, [0, 0, 0.3]),
              part("torus", [0, 0.94, 0], [0.50, 0.04, 0.44], rim, [0, 0, 0.3]),
              part("cyl", [0.30, 0.94, 0], [0.06, 0.32, 0.06], china, [0, 0, -0.9]),
              part("torus", [-0.28, 0.98, 0], [0.22, 0.05, 0.22], china, [PI / 2, 0, 0.3]),
              part("sph", [0, 1.14, 0], [0.12, 0.08, 0.12], rim),
              place("teardrop", [0.48, 0.78, 0], [0.06, 0.20, 0.06], "#8a5a2a", r=[PI, 0, 0],
                    a=0.8)]
    return parts


@HW24.hat("chandelier", "Falling Chandelier",
          "The ballroom chandelier, still lit, which has decided it would rather hang "
          "over you. Its chain goes up and up and nobody can see where it ends.",
          "legendary", hair="show")
def _():
    gold, crystal = "#c9a227", "#dff2ff"
    parts = [
        part("torus", [0, 1.03, 0], [0.12, 0.03, 0.12], gold, [PI / 2, 0, 0], m="metal"),
        part("sph", [0, 0.80, 0], [0.20, 0.30, 0.20], gold, m="metal"),
        part("torus", [0, 0.59, 0], [1.40, 0.06, 1.40], gold, m="metal"),
        part("torus", [0, 0.71, 0], [0.70, 0.05, 0.70], gold, m="metal"),
    ]
    # the chain, link by link, fading out as it climbs to wherever it hangs from
    for k in range(7):
        parts.append(part("torus", [0, 1.15 + k * 0.13, 0], [0.09, 0.025, 0.09], gold,
                          [PI / 2, (k % 2) * PI / 2, 0], m="metal", a=round(1.0 - k * 0.13, 2)))
    for k in range(6):
        a = k * TAU / 6
        x, z = math.sin(a) * 0.70, math.cos(a) * 0.70
        parts += [part("cyl", [x * 0.5, 0.67, z * 0.5], [0.03, 0.60, 0.03], gold,
                       [math.cos(a) * 1.3, 0, -math.sin(a) * 1.3], m="metal"),
                  part("cyl", [x, 0.67, z], [0.10, 0.14, 0.10], "#f4ecd8"),
                  place("flame", [x, 0.81, z], [0.10, 0.16, 0.10], CANDLE, m="neon", spin=1.8),
                  place("gem", [x, 0.41, z], [0.12, 0.20, 0.12], crystal, r=[PI, 0, 0],
                        m="glass", a=0.8)]
    parts.append(place("gem", [0, 0.47, 0], [0.24, 0.40, 0.24], crystal, r=[PI, 0, 0],
                       m="glass", a=0.8))
    return parts


@HW24.hat("seance_turban", "Seance Turban",
          "A madame's turban of midnight silk, a sapphire on the front the size of "
          "an egg, and a peacock feather that twitches when the spirits are near.",
          "rare")
def _():
    silk, gem = "#1a2a5a", "#3a7aff"
    parts = [
        dome(-0.30, 0.82, silk, decal="paisley", wrap=True),
        ringband(-0.20, 0.30, "#24376e", decal="paisley", wrap=True),
        part("torus", [0, 0.06, 0], [1.76, 0.18, 1.72], "#24376e", [0.1, 0, 0]),
        part("torus", [0, 0.26, 0], [1.56, 0.16, 1.52], silk, [-0.12, 0, 0]),
        place("teardrop", [0, 0.30, 0.86], [0.30, 0.40, 0.18], gem, r=[-0.1, 0, 0], m="glass"),
        part("torus", [0, 0.30, 0.86], [0.38, 0.04, 0.46], GOLD, [PI / 2 - 0.1, 0, 0], m="metal"),
        place("feather", [0.10, 0.78, 0.72], 0.90, "#2a8a6a", anchor=[0, -0.5, 0], r=[-0.3, 0, -0.2]),
        part("sph", [0.18, 1.16, 0.64], [0.14, 0.14, 0.04], "#3a7aff", [-0.3, 0, -0.2], m="glass"),
    ]
    return parts


@HW24.hat("portrait_eyes", "Watching Portrait",
          "A little gilt portrait of a stern old man, worn on a ribbon round the "
          "crown. His eyes follow whoever is behind you.", "uncommon", hair="show")
def _():
    gold = "#c9a227"
    return [
        band(-0.32, 0.07, "#2a1018", grow=-0.02),
        part("rbox", [0, 0.26, 0.62], [0.70, 0.84, 0.08], gold, [-0.15, 0, 0], m="metal"),
        part("box", [0, 0.26, 0.665], [0.56, 0.70, 0.01], "#2a2a30", [-0.15, 0, 0], decal="portrait"),
        part("sph", [0.09, 0.40, 0.69], [0.07, 0.04, 0.02], "#ff3b4e", [-0.15, 0, 0], m="neon"),
        part("sph", [-0.09, 0.40, 0.69], [0.07, 0.04, 0.02], "#ff3b4e", [-0.15, 0, 0], m="neon"),
        part("rbox", [0, -0.25, 0.735], [0.18, 0.16, 0.05], gold, m="metal"),
    ]


@HW24.back("clinging_ghost", "Clinging Ghost",
           "Great-grandfather Whisper has taken a liking to you and is riding on your "
           "back, arms round your neck. He weighs nothing at all. He will not let go.",
           "legendary")
def _():
    sheet = "#e9f4ff"
    parts = [
        # a tall wisp down your back, his head peeking over the top of yours
        part("sph", [0, 0.80, -0.50], [1.10, 2.30, 0.50], sheet, a=0.55),
        part("sph", [0, 2.48, -0.45], [0.96, 0.86, 0.62], sheet, a=0.62),
        part("sph", [0.18, 2.62, -0.19], [0.15, 0.20, 0.04], "#16171b", a=0.9),
        part("sph", [-0.18, 2.62, -0.19], [0.15, 0.20, 0.04], "#16171b", a=0.9),
        place("teardrop", [0, -0.35, -0.50], [1.00, 0.70, 0.46], sheet, r=[PI, 0, 0], a=0.45),
    ]
    # his arms: wisps over each shoulder, clear of the head, down to two
    # hands clasped on your chest
    path = [(0.70, 1.05, -0.25), (0.78, 1.10, 0.15), (0.80, 1.10, 0.55), (0.80, 1.10, 0.92),
            (0.66, 1.05, 1.19), (0.48, 0.97, 1.21)]
    for side in (1, -1):
        for n, (x, y, z) in enumerate(path):
            w = 0.21 - n * 0.008
            parts.append(part("sph", [x * side, y, z], [w, w, w], sheet, a=0.6))
        parts.append(part("sph", [0.30 * side, 0.90, 1.22], [0.22, 0.17, 0.10], sheet, a=0.7))
    return parts


@HW24.back("haunted_mirror", "Haunted Mirror",
           "An oval mirror in a gilt frame, strapped on like a shield. Look into it "
           "and there is nobody behind you. Look again and there is.", "rare")
def _():
    gold = "#c9a227"
    return [
        part("cyl", [0, 0.20, -0.20], [1.10, 0.10, 1.40], gold, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.20, -0.26], [0.92, 0.04, 1.22], "#a8b4c8", [PI / 2, 0, 0], m="glass",
             decal="mirror"),
        place("teardrop", [0, 0.20, -0.29], [0.40, 0.70, 0.02], GHOST, a=0.4),
        part("sph", [0.08, 0.36, -0.30], [0.06, 0.08, 0.01], "#16171b"),
        part("sph", [-0.08, 0.36, -0.30], [0.06, 0.08, 0.01], "#16171b"),
        place("shield", [0, 0.98, -0.20], [0.40, 0.30, 1.0], gold, r=[0, 0, PI], m="metal"),
        *straps("#2a1018", 0.34, 0.12),
    ]


@HW24.hairdo("victorian_updo", "Victorian Updo",
             "Pinned high, crimped, finished with a black velvet bow. The style of "
             "the lady in the third-floor portrait. Exactly.", "rare")
def _():
    c = "#3a1a14"
    return [
        place("hairmid", [0, 0, 0], [1.02, 1.02, 1.02], c, anchor=[0, 0, 0], decal="strands",
              wrap=True),
        part("sph", [0, 0.62, -0.10], [0.62, 0.40, 0.56], c, decal="strands", wrap=True),
        part("torus", [0, 0.64, -0.10], [0.56, 0.12, 0.52], shade(c, 1.25)),
        place("bowtie", [0, 0.50, -0.42], [0.40, 0.40, 1.0], "#141016"),
        place("spiral", [0.48, 0.0, 0.20], [0.10, 0.36, 0.10], c, anchor=[0, 0.5, 0]),
        place("spiral", [-0.48, 0.0, 0.20], [0.10, 0.36, 0.10], c, anchor=[0, 0.5, 0]),
    ]


@HW24.hairdo("ghostly_wisps", "Ghostly Wisps",
             "Hair gone white and see-through, floating a little, as if it is "
             "underwater, or no longer quite here.", "uncommon")
def _():
    c = "#e9f4ff"
    parts = [place("hairmid", [0, 0, 0], [1.05, 1.05, 1.05], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True, a=0.6)]
    for k, (x, z) in enumerate(((0.30, -0.30), (-0.30, -0.30), (0.0, -0.40), (0.40, 0.0),
                                (-0.40, 0.0))):
        parts.append(place("teardrop", [x, 0.50, z], [0.16, 0.40, 0.16], c, anchor=[0, 0.1, 0],
                           r=[0.3 * (1 if z < 0 else 0), 0, -x], a=0.45))
    return parts


HW24.face("possessed", "Possessed",
          "The eyes have rolled up and gone white, and the smile is somebody "
          "else's.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.13, "h": 0.10, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.13, "h": 0.10, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.20, "y": -0.18, "w": 0.05, "h": 0.025, "c": "#8a9aaa"},
              {"k": "ellipse", "x": 0.20, "y": -0.18, "w": 0.05, "h": 0.025, "c": "#8a9aaa"},
              {"k": "arc", "x": 0, "y": -0.02, "r": 0.30, "a0": 0.05, "a1": 0.45, "w": 0.03,
               "c": "#16171b"},
              {"k": "line", "x1": -0.30, "y1": -0.26, "x2": -0.12, "y2": -0.22, "w": 0.02, "c": "#16171b"},
              {"k": "line", "x1": 0.30, "y1": -0.26, "x2": 0.12, "y2": -0.22, "w": 0.02, "c": "#16171b"},
          ], "rare")
HW24.face("mourning_kohl", "Mourning Kohl",
          "Heavy black liner, and one black tear that has dried on its way down.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.15, "h": 0.07, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.15, "h": 0.07, "c": "#16171b"},
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.05, "h": 0.05, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.05, "h": 0.05, "c": "#ffffff"},
              {"k": "poly", "pts": [[0.22, -0.07], [0.20, 0.04], [0.24, 0.04]], "c": "#16171b"},
              {"k": "line", "x1": -0.10, "y1": 0.20, "x2": 0.10, "y2": 0.20, "w": 0.035, "c": "#4a0f1a"},
          ], "uncommon")
HW24.shirt("smoking_jacket", "Lord of the Manor",
           "A burgundy velvet smoking jacket with gold frogging, for receiving guests "
           "who may or may not be alive.",
           {"torso": "#5a1428", "arms": "#5a1428", "decal": "tee_frogging", "weave": "felt",
            "stripe": "#c9a227"}, "rare")
HW24.pants("pinstripes", "Pinstripe Trousers",
           "Charcoal with a thin chalk stripe, pressed to a crease you could cut "
           "yourself on.",
           {"legs": "#2a2a30", "weave": "pinstripe"})
HW24.belt("watch_chain", "Butler's Watch Chain",
          "A black waistband, a gold watch chain across it, and a pocket watch that "
          "runs backwards.",
          {"band": "#16171b", "buckle": "#c9a227", "width": 0.18, "metal": True,
           "chain": "#c9a227"})


@HW24.weapon("candelabra_cudgel", "Candelabra Cudgel",
             "The manor's heaviest candelabra, swung by the base. It sets alight "
             "whoever it hits, and hits harder whoever is already burning.",
             {"kind": "melee", "damage": 30, "headshot": 1.0, "rpm": 80, "range": 10.5,
              "arc": 0.6, "sound": "swing", "knockback": 12,
              "on_hit": {"burn": [6, 3.0]}, "vs_status": {"burn": 1.35},
              "held": {"dmg_taken": 0.15}},
             [["+", "Sets its target alight: 6 damage a second for 3 seconds"],
              ["+", "35% more damage to anyone already burning"],
              ["-", "You take 15% more damage while it is in your hand"],
              ["-", "Slow to swing"]], rarity="legendary")
def _():
    gold = "#c9a227"
    parts = [
        part("cyl", [0, 0.0, 0.10], [0.12, 1.20, 0.12], gold, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.0, -0.52], [0.36, 0.08, 0.36], gold, [PI / 2, 0, 0], m="metal"),
        part("sph", [0, 0.0, 0.20], [0.20, 0.20, 0.20], gold, m="metal"),
        part("sph", [0, 0.0, 0.70], [0.22, 0.22, 0.22], gold, m="metal"),
        place("arch", [0, 0.0, 0.70], [0.90, 0.50, 1.6], gold, anchor=[0, 0, 0], r=[PI / 2, 0, 0],
              m="metal"),
    ]
    for x, z in ((-0.45, 0.72), (0.0, 1.20), (0.45, 0.72)):
        parts += [part("cyl", [x, 0.0, z + 0.14], [0.13, 0.30, 0.13], "#f4ecd8", [PI / 2, 0, 0]),
                  place("flame", [x, 0.0, z + 0.40], [0.14, 0.22, 0.14], CANDLE, r=[PI / 2, 0, 0],
                        m="neon")]
    return parts


@HW24.weapon("poltergeist_pistol", "Poltergeist Pistol",
             "A duelling pistol that a ghost in the gun room will not let go of. "
             "Aim near somebody and it finds them for you.",
             {"kind": "hitscan", "damage": 24, "headshot": 1.25, "rpm": 170, "mag": 6,
              "reload": 1.9, "spread": 0.5, "pellets": 1, "range": 210, "auto": False,
              "sound": "pistol", "recoil": 1.4, "reserve": 42, "tracer": "#e9f4ff",
              "aim_assist": {"angle": 7}},
             [["+", "The ghost guides the shot to anyone within 7 degrees of your aim"],
              ["-", "Headshots only do 25% more"],
              ["-", "Six shots, then a reload"]], rarity="legendary")
def _():
    wood, steel = "#4a2a1a", "#5e636b"
    return [
        part("cyl", [0, 0.10, 0.62], [0.12, 1.00, 0.12], steel, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, 0.06, 0.20], [0.18, 0.18, 0.60], wood, decal="planks"),
        part("rbox", [0, -0.24, -0.08], [0.18, 0.50, 0.24], wood, [-0.5, 0, 0], decal="planks"),
        part("sph", [0, -0.46, -0.24], [0.22, 0.20, 0.22], "#c9a227", m="metal"),
        part("rbox", [0, 0.22, 0.04], [0.06, 0.14, 0.12], steel, [0.4, 0, 0], m="metal"),
        part("torus", [0, -0.06, 0.12], [0.20, 0.04, 0.20], steel, [0, 0, PI / 2], m="metal"),
        # the hand that is helping
        part("sph", [0.12, 0.22, 0.30], [0.30, 0.20, 0.40], GHOST, a=0.45),
    ]


@HW24.weapon("seance_bell", "Seance Bell",
             "The bell from the parlour table, rung hard. The note knocks people back, "
             "stops them dead for a moment, and leaves them glowing for the spirits -- "
             "and your team -- to see.",
             {"kind": "cone", "damage": 10, "rpm": 45, "mag": 5, "reload": 2.6, "range": 16.0,
              "auto": False, "sound": "bell", "recoil": 1.6, "reserve": 25,
              "cone": {"angle": 0.60, "push": 30, "lift": 8, "stun": 0.5, "color": "#e9f4ff"},
              "on_hit": {"reveal": 5.0}},
             [["+", "A ring of sound in front of you: shoves, stuns for half a second"],
              ["+", "Everyone it rings out is shown to your team through walls for 5 "
                    "seconds"],
              ["-", "Very little damage"],
              ["-", "16 stud reach"]], rarity="legendary")
def _():
    gold = "#c9a227"
    return [
        part("cyl", [0, 0.0, -0.10], [0.14, 0.60, 0.14], "#2a1018", [PI / 2, 0, 0]),
        part("sph", [0, 0.0, -0.42], [0.18, 0.18, 0.18], gold, m="metal"),
        # a brass hand bell, mouth forward, rung off the end of its handle
        place("handbell", [0, 0.0, 0.20], [0.62, 0.74, 0.62], gold, anchor=[0, 1.0, 0],
              r=[-PI / 2, 0, 0], m="metal"),
        place("ring", [0, 0.0, 0.90], [0.64, 0.64, 0.64], shade(gold, 0.8), r=[PI / 2, 0, 0],
              m="metal"),
        part("sph", [0, -0.08, 0.86], [0.14, 0.14, 0.14], "#3a3d42", m="metal"),
    ]


@HW24.gear("ghost_sheet", "Ghost Sheet",
           "Throw it over your head and you are just another one of the manor's "
           "residents: very nearly invisible, until you do anything at all.",
           {"kind": "ability", "cooldown": 32, "sound": "magic",
            "ability": {"cloak": {"secs": 6.0}}},
           [["+", "Near-invisible for 6 seconds; enemies more than 12 studs away cannot "
                  "target you"],
            ["-", "Firing, swinging or using anything else ends it"],
            ["-", "32 second cooldown"]], rarity="rare")
def _():
    return [
        # the same sheet as the hat, in miniature, ready to throw on
        part("hemi", [0, 0.30, 0.22], [0.46, 0.20, 0.44], GHOST, decal="linen", wrap=True),
        part("cyl", [0, 0.10, 0.22], [0.46, 0.20, 0.44], GHOST, decal="linen", wrap=True),
        part("sph", [0.09, 0.20, 0.44], [0.08, 0.10, 0.02], "#16171b"),
        part("sph", [-0.09, 0.20, 0.44], [0.08, 0.10, 0.02], "#16171b"),
        place("ruffle", [0, 0.0, 0.22], [0.50, 1.0, 0.48], GHOST, anchor=[0, 0, 0]),
    ]


HW24.effect("seance_eyes", name="Seance Eyes", rate=2.6, life=[1.8, 2.6],
            size=[0.22, 0.32], grow=0.0, gravity=0.0, spread=0.4, rise=[0.05, 0.2],
            blend="normal", spin=0.0, colors=["#ffffff", "#ffd36a", "#e9f4ff"],
            shape="eye", radius=0.9, orbit=0.8, upright=True, wobble=0.2)
HW24.effect("poltergeist", name="Poltergeist", rate=3.0, life=[2.0, 2.8],
            size=[0.26, 0.36], grow=0.1, gravity=-0.3, spread=0.5, rise=[0.2, 0.5],
            blend="normal", spin=1.0, colors=["#e9f4ff", "#ffffff", "#c9e2ff"],
            shapes=["hand", "ghost"], radius=0.7, upright=True, wobble=0.6)
HW24.opening(
    sky={"top": "#0d0709", "horizon": "#2a1418", "sun": [0.2, 0.9, 0.6], "clouds": 0,
         "tint": "#ffd8a8"},
    ambient="#6a4a3a", beam="#ffd36a", seep="candlelight_vigil", after="seance_eyes",
    burst=["#ffd36a", "#e9f4ff", "#c9a227", "#ffffff"],
    pieces=[{"shape": "ghost", "colors": ["#ffffff", "#e9f4ff"], "blend": "normal"},
            {"shape": "candle", "colors": ["#f4ecd8", "#ffd36a"], "blend": "normal"},
            {"shape": "eye", "colors": ["#ffffff", "#ffd36a"], "blend": "normal"},
            {"shape": "spark", "colors": ["#ffd36a", "#fff3b0"], "blend": "add"}],
    backdrop="manor", title_wait="The candles gutter...",
    title_shake="Is anybody there...?")
HW24.award("Manor of Whispers", ["Guest", "Lodger", "Seance Sitter", "Medium",
                                 "Master of the House", "Lord of Whisper Manor"],
           "Opened Whisper Manor Crates during the Manor of Whispers, Halloween 2024.",
           "em_manor", "moon")
HW24.bundle("pair", "A Room for the Night", 1, 1050, "One Whisper Manor Crate, one Candelabra Key.")
HW24.bundle("wing", "The East Wing", 3, 3000, "Three crates, three keys. Saves 300.")


# ============================================================ 2025
TENT = "#c4281c"
CREAM = "#f4ecd8"
GREASEPAINT = "#f6f2ee"
HARLEQUIN = "#5a2a7a"
MARQUEE = "#fff3b0"

HW25 = Event(
    "halloween_2025", "halloween", 2025, "hw25",
    name="Big Top Terror", title="The Big Top Terror",
    blurb="Halloween 2025 the circus came to Blockhaven. Nobody saw it arrive: one "
          "morning the big top was simply standing on the old fairground, lit, with "
          "the calliope playing to nobody. The clowns never take their make-up off. "
          "Every ticket is one-way.",
    tagline="Roll up, roll up. You will never leave.",
    starts="2025-10-01", ends="2025-11-09",
    colors={"accent": "#e8402a", "deep": "#1a0a12", "glow": "#ffd36a"},
    family_effects=["candlelight_vigil", "flying_skulls", "jack_o_lanterns", "bat_swarm"],
    hero_effect="carnival_lights", stencil="stencil_hw25")


@HW25.crate_model("Big Top Trunk",
                  "A performer's travelling trunk, camel-backed and striped like the big "
                  "top, brass at every corner and pasted with posters for a show nobody "
                  "remembers buying tickets for. Holds the Big Top Terror set. Needs an "
                  "Admit-One Key.",
                  hinge=[0, 0.36, -0.55], keyhole=[0, 0.20, 0.60])
def _():
    wood, strap = "#6a1018", "#3a2214"
    parts = [
        part("rbox", [0, -0.05, 0], [1.70, 0.82, 1.08], wood, decal="planks", wrap=True),
        # the camel-back lid, striped like the tent, with a brass rim and a star
        part("hemi", [0, 0.57, 0], [1.74, 0.42, 1.10], TENT, lid=1, decal="bigtop_stripes",
             wrap=True),
        part("rbox", [0, 0.37, 0], [1.78, 0.08, 1.14], BRASS, m="metal", lid=1),
        part("rbox", [0, 0.40, 0.575], [0.18, 0.16, 0.04], BRASS, m="metal", lid=1),
        place("star", [0, 0.86, 0], 0.34, GOLD, m="metal", lid=1),
        part("rbox", [0, 0.31, 0], [1.74, 0.06, 1.12], BRASS, m="metal"),
        # the clasp, which is the lock
        part("rbox", [0, 0.20, 0.575], [0.30, 0.26, 0.06], BRASS, m="metal", decal="keyhole",
             lock=1),
        # the light inside, for when the lid comes up
        part("box", [0, 0.30, 0], [1.60, 0.04, 1.00], "#ffd36a", m="neon"),
        # posters on both ends and the stencil on the back
        part("box", [0.865, -0.04, 0], [0.80, 0.62, 0.02], "#000000", [0, PI / 2, 0],
             decal="bigtop_poster", a=-1),
        part("box", [-0.865, -0.04, 0], [0.80, 0.62, 0.02], "#000000", [0, -PI / 2, 0],
             decal="bigtop_poster", a=-1),
        part("box", [0, -0.05, -0.555], [1.10, 0.62, 0.02], "#000000", [0, PI, 0],
             decal="stencil_hw25", a=-1),
    ]
    for x in (-0.45, 0.45):
        parts += [part("rbox", [x, -0.06, 0.55], [0.16, 0.80, 0.03], strap, decal="leather"),
                  part("rbox", [x, 0.16, 0.57], [0.20, 0.14, 0.03], BRASS, m="metal")]
    for x in (-0.79, 0.79):
        for z in (-0.49, 0.49):
            for y in (-0.40, 0.28):
                parts.append(part("rbox", [x, y, z], [0.18, 0.16, 0.18], BRASS, m="metal"))
            parts.append(part("sph", [x, -0.50, z], [0.14, 0.10, 0.14], BRASS, m="metal"))
    for side in (1, -1):
        parts.append(part("torus", [0.88 * side, 0.08, 0], [0.30, 0.05, 0.30], BRASS,
                          [0, 0, PI / 2], m="metal"))
    return parts


@HW25.key_model("Admit-One Key",
                "A brass key with a ticket for a bow. ADMIT ONE, it says. It does not say "
                "when, and there is no stub for coming back out. Opens one Big Top Trunk.",
                shoulder=-0.30)
def _():
    return [
        part("rbox", [-0.66, 0, 0], [0.72, 0.42, 0.05], "#e8d6a8", decal="admit_one"),
        part("rbox", [-0.66, 0, -0.005], [0.74, 0.44, 0.04], "#a8141e"),
        part("cyl", [-0.93, 0, 0], [0.09, 0.07, 0.09], "#1a0a12", [PI / 2, 0, 0]),
        part("torus", [-0.28, 0, 0], [0.20, 0.07, 0.20], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        part("cyl", [0.11, 0, 0], [0.09, 0.80, 0.09], BRASS, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.40, -0.12, 0], [0.08, 0.22, 0.08], BRASS, m="metal"),
        place("star", [0.53, -0.20, 0], 0.22, BRASS, m="metal"),
    ]


@HW25.hat("ringmaster_topper", "Ringmaster's Topper",
          "Scarlet silk, a gold band, a ring of marquee bulbs round the crown and a "
          "plume of black feathers. Whoever wears it is in charge of the show. The "
          "show has not decided whether to let them.", "legendary")
def _():
    red = "#a8141e"
    parts = [
        place("brim", [0, -0.05, 0], [2.20, 1.6, 2.10], BLACK, anchor=[0, 0, 0]),
        place("flare", [0, 0.0, 0], [1.40, 1.55, 1.34], red, anchor=[0, 0, 0], decal="felt",
              wrap=True),
        part("cyl", [0, 0.20, 0], [1.29, 0.30, 1.23], GOLD, m="metal"),
        part("cyl", [0, 0.20, 0], [1.31, 0.06, 1.25], GOLD_DARK, m="metal"),
        place("star", [0, 0.22, 0.655], 0.30, GOLD, m="metal"),
        part("sph", [0, 0.23, 0.69], [0.09, 0.09, 0.05], "#ff3b4e", m="glass"),
        part("cyl", [0, 1.555, 0], [1.42, 0.03, 1.36], BLACK),
    ]
    parts += around(12, 0.69, 1.50, lambda a, x, z: part(
        "sph", [x, 1.50, z * 0.957], [0.09, 0.09, 0.09], MARQUEE, m="neon"))
    for k, lean in enumerate((-0.25, 0.05, 0.35)):
        parts.append(place("feather", [0.52 + k * 0.04, 0.34, -0.36 + k * 0.08], 0.95,
                           "#16121a", anchor=[0, -0.5, 0], r=[lean, PI / 2 + 0.5, -0.30]))
    return parts


@HW25.hat("big_top", "The Big Top",
          "The whole tent, in miniature, pitched on your head: red and cream canvas, a "
          "scalloped valance, and a pennant on the king pole. Something is moving "
          "about inside.", "rare", hair="flat")
def _():
    parts = [
        cap(-0.28, 0.08, "#5a0f18", decal="felt", wrap=True),
        band(-0.22, 0.10, GOLD, grow=0.04, m="metal"),
        part("cyl", [0, 0.30, 0], [1.24, 0.46, 1.20], TENT, decal="bigtop_stripes", wrap=True),
        part("cone", [0, 0.92, 0], [1.56, 0.80, 1.50], TENT, decal="bigtop_stripes", wrap=True),
        # the doorway, dark, with a glow in it
        place("tri", [0, 0.28, 0.605], [0.42, 0.50, 0.3], "#1a0a12"),
        part("sph", [0, 0.24, 0.60], [0.16, 0.16, 0.04], "#ffd36a", m="neon", a=0.6),
        # king pole and pennant
        part("cyl", [0, 1.46, 0], [0.04, 0.40, 0.04], BRASS, m="metal"),
        place("flag", [0.26, 1.56, 0], [0.50, 0.42, 0.5], "#ffd36a", r=[0, 0, -0.05]),
        part("sph", [0, 1.68, 0], [0.07, 0.07, 0.07], GOLD, m="metal"),
    ]
    # the scalloped valance round the eaves
    parts += around(14, 0.74, 0.52, lambda a, x, z: place(
        "tri", [x, 0.47, z * 0.96], [0.30, 0.20, 0.4],
        TENT if int(round(a / (TAU / 14))) % 2 else CREAM, r=[PI, a, 0]))
    return parts


def _jester_prong(side, back):
    """One floppy prong of a jester's cap and the bell on its tip."""
    k = 2.3
    if back:
        at, r = [0, 0.02, -0.30], [0.0, PI / 2, -0.55]
    else:
        at, r = [0.30 * side, 0.02, 0.0], [0.0, 0.0 if side > 0 else PI, -0.55]
    tip = rotate([0.376 * k, 0.581 * k, 0], r)
    end = [at[0] + tip[0], at[1] + tip[1], at[2] + tip[2]]
    colour = HARLEQUIN if (side > 0) != back else BLACK
    return [place("horn", at, [k, k, k * 2.4], colour, anchor=[0, 0, 0], r=r,
                  decal="harlequin", wrap=True),
            part("sph", [end[0], end[1] - 0.06, end[2]], [0.20, 0.20, 0.20], GOLD, m="metal"),
            part("rbox", [end[0], end[1] - 0.11, end[2]], [0.14, 0.02, 0.21], "#3a2a10")]


@HW25.hat("jester_cap", "Jester of the Dark Carnival",
          "A three-pointed fool's cap in purple and black diamonds, a bell on every "
          "point. You can hear it coming. You will not hear it leave.", "rare")
def _():
    parts = [
        cap(-0.30, 0.18, HARLEQUIN, decal="harlequin", wrap=True),
        ringband(-0.24, 0.14, GOLD, m="metal"),
    ]
    parts += _jester_prong(1, False) + _jester_prong(-1, False) + _jester_prong(1, True)
    parts += around(8, 0.93, 0.0, lambda a, x, z: place(
        "tri", [x, -0.38, z * 0.965], [0.26, 0.26, 0.4],
        HARLEQUIN if int(round(a / (TAU / 8))) % 2 else BLACK, r=[PI, a, 0]))
    return parts


@HW25.hat("popcorn_head", "Bottomless Popcorn",
          "A striped bucket of popcorn, heaped and spilling. Nobody has ever reached "
          "the bottom of it, and the ones who tried say there is something down there "
          "eating it from below.", "uncommon")
def _():
    parts = [place("flare", [0, 0.0, 0], [1.34, 1.05, 1.34], CREAM, anchor=[0, 0, 0],
                   decal="popcorn_stripes", wrap=True),
             part("cyl", [0, 1.04, 0], [1.32, 0.04, 1.32], "#fff6d8")]
    kernels = [(0, 1.22, 0, 0.36), (0.32, 1.13, 0.16, 0.30), (-0.30, 1.14, 0.18, 0.32),
               (0.12, 1.13, -0.32, 0.32), (-0.24, 1.10, -0.22, 0.28), (0.36, 1.08, -0.18, 0.26),
               (0.06, 1.42, 0.10, 0.30), (-0.12, 1.38, -0.08, 0.28), (0.20, 1.34, -0.08, 0.26),
               (0.48, 1.10, 0.36, 0.22), (-0.46, 1.08, 0.34, 0.22), (0.0, 1.10, 0.54, 0.22),
               (-0.52, 1.08, -0.10, 0.20), (0.18, 1.30, 0.30, 0.24)]
    for k, (x, y, z, w) in enumerate(kernels):
        parts.append(part("sph", [x, y, z], [w, w * 0.86, w], "#fff6d8" if k % 3 else "#ffe9a8"))
    # a few that have spilled over the rim
    for x, y, z in ((0.62, 0.96, 0.24), (-0.36, 0.92, 0.56), (0.20, 0.84, 0.66)):
        parts.append(part("sph", [x, y, z], [0.18, 0.16, 0.18], "#fff6d8"))
    return parts


def _string_bow(at):
    """A little ribbon bow where the balloon strings are tied."""
    x, y, z = at
    return [part("sph", [x, y, z], [0.12, 0.10, 0.12], TENT),
            place("bowtie", [x, y + 0.02, z], [0.40, 0.30, 1.0], TENT)]


@HW25.hat("runaway_balloons", "Runaway Balloons",
          "A fistful of balloons from the midway, tied to a bow on your head. One of "
          "them has a face. You did not draw it on.", "rare")
def _():
    knot = [0, 0.10, 0]
    parts = [ringband(-0.30, 0.10, TENT)]
    parts += _string_bow(knot)
    balloons = [([0.62, 1.70, 0.10], "#ff3b4e", 0.86), ([-0.62, 1.86, -0.08], "#3cc8ff", 0.82),
                ([0.04, 2.40, -0.26], "#ffd36a", 0.90), ([0.36, 2.14, 0.50], "#7dff9a", 0.78),
                ([-0.34, 1.62, 0.52], GREASEPAINT, 0.86)]
    for k, (at, colour, size) in enumerate(balloons):
        parts += [place("balloon", at, [size, size * 1.15, size], colour, anchor=[0, 0, 0],
                        m="glass", a=0.95),
                  rod(knot, at, 0.02, "#f4f6f8")]
    # the one with the face
    at, size = balloons[4][0], balloons[4][2]
    parts.append(part("box", [at[0], at[1] + size * 0.66, at[2] + size * 0.50 + 0.01],
                      [size * 0.66, size * 0.66, 0.02], "#000000", decal="balloon_grin", a=-1))
    return parts


@HW25.hat("cotton_candy", "Cotton Candy Coif",
          "Somebody dropped a cotton candy on your head, floss first. It has set like a "
          "beehive, the paper cone still sticking out of the top. Sticky in the rain. "
          "Stickier in other things.", "uncommon", hair="hide")
def _():
    pink, blue = "#ffa8dc", "#a8dcff"
    parts = [dome(-0.42, 1.05, pink)]
    # the floss in lumps all over it, standing a little proud of the shell
    for k in range(26):
        a = k * 2.399
        up = 0.06 + 0.88 * (k + 0.5) / 26
        ring = math.sqrt(max(0.0, 1.0 - up * up))
        w = 0.46 - 0.16 * up
        out = 1.0 + 0.30 * w
        x, z = math.sin(a) * 0.96 * ring * out, math.cos(a) * 0.93 * ring * out
        y = -0.42 + up * 1.05 * out
        colour = ("#ffd6f0", blue, "#ff7ac8", "#d8b8ff")[k % 4]
        parts.append(part("sph", [x, y, z], [w, w * 0.86, w], colour))
    tilt = [0.0, 0.0, -0.30]
    base = [0.10, 0.50, 0.0]
    parts += [place("cone", base, [0.44, 0.86, 0.44], CREAM, anchor=[0, -0.5, 0], r=tilt,
                    decal="popcorn_stripes", wrap=True)]
    return parts


@HW25.hat("cannonball_helmet", "Human Cannonball",
          "A padded crash helmet in red and silver with a gold star on the front and "
          "the goggles pushed up. It has been fired out of a cannon two hundred times. "
          "It has landed in the net twice.", "rare", hair="hide")
def _():
    red = "#d0202a"
    parts = [
        dome(-0.62, 1.05, red, t="capcrown", m="metal"),
        ringband(-0.62, 0.16, SILVER, m="metal"),
        place("star", [0, -0.10, 0.875], 0.42, GOLD, r=[-0.35, 0, 0], m="metal"),
        # goggles pushed up on the brow, and their strap
        ringband(-0.30, 0.10, "#2a2a30", margin=0.07),
    ]
    for side in (1, -1):
        parts += [part("cyl", [0.26 * side, -0.32, 0.98], [0.30, 0.10, 0.30], SILVER,
                       [PI / 2 - 0.15, 0, 0], m="metal"),
                  part("cyl", [0.26 * side, -0.32, 1.02], [0.24, 0.02, 0.24], "#9ad8ff",
                       [PI / 2 - 0.15, 0, 0], m="glass", a=0.7),
                  part("sph", [0.97 * side, -0.48, 0], [0.18, 0.30, 0.40], SILVER, m="metal")]
    return parts


@HW25.back("carousel_steed", "Carousel Steed",
           "A painted horse off the carousel, still on its brass pole, still going up "
           "and down. The canopy turns overhead. The music has not stopped since 1931.",
           "legendary")
def _():
    white, gilt, saddle, mane = "#f6f2ee", "#d9a520", "#a8141e", "#3cc8ff"
    z, k = -0.86, 1.30

    def at(x, y, dz=0.0):
        # the horse is drawn at its own size about the pole and grown from there
        return [x * k, 0.62 + (y - 0.62) * k, z + dz * k]

    def limb(a, b, w, c, **kw):
        return rod(at(*a), at(*b), w * k, c, t="capsule", **kw)

    parts = [
        # the pole, the canopy over your head and the finial on top
        part("cyl", [0, 0.80, z + 0.10], [0.11, 4.10, 0.11], BRASS, m="metal",
             decal="bigtop_stripes", wrap=True),
        part("cone", [0, 3.10, z + 0.10], [1.90, 0.60, 1.90], TENT, decal="bigtop_stripes",
             wrap=True, spin=0.8),
        part("cyl", [0, 2.78, z + 0.10], [1.92, 0.10, 1.92], GOLD, m="metal", spin=0.8),
        part("sph", [0, 3.46, z + 0.10], [0.18, 0.18, 0.18], GOLD, m="metal"),
        # the horse, galloping to your right
        part("capsule", at(0.0, 0.62), [0.52 * k, 1.30 * k, 0.44 * k], white, [0, 0, PI / 2]),
        limb((0.46, 0.70, 0), (0.78, 1.18, 0), 0.36, white),
        part("rbox", at(0.92, 1.24), [0.46 * k, 0.28 * k, 0.30 * k], white, [0, 0, -0.35]),
        part("sph", at(1.13, 1.17), [0.16 * k, 0.16 * k, 0.22 * k], "#e8c0b0"),
        place("leaf", at(0.82, 1.44, 0.08), [0.4 * k, 0.40 * k, 1.0], white, r=[0, 0, 0.3]),
        place("leaf", at(0.82, 1.44, -0.08), [0.4 * k, 0.40 * k, 1.0], white, r=[0, 0, 0.3]),
        part("sph", at(1.00, 1.30, 0.13), [0.06, 0.06, 0.03], BLACK),
        part("sph", at(1.00, 1.30, -0.13), [0.06, 0.06, 0.03], BLACK),
        # bridle and plume
        part("torus", at(1.02, 1.20), [0.30 * k, 0.03 * k, 0.32 * k], gilt, [0, 0, PI / 2 - 0.35],
             m="metal"),
        place("feather", at(0.86, 1.56), 0.60 * k, saddle, anchor=[0, -0.5, 0], r=[0, 0, -0.5]),
        # the mane and tail
        limb((0.50, 0.90, 0), (0.86, 1.40, 0), 0.16, mane, m="glass"),
        limb((-0.60, 0.72, 0), (-0.94, 0.28, 0), 0.16, mane, m="glass"),
        limb((-0.94, 0.28, 0), (-0.98, 0.04, 0), 0.10, mane, m="glass"),
        # the saddle, its striped cloth and the stirrup
        part("rbox", at(-0.05, 0.92), [0.46 * k, 0.10 * k, 0.48 * k], saddle),
        part("rbox", at(-0.05, 0.72), [0.62 * k, 0.40 * k, 0.50 * k], CREAM,
             decal="bigtop_stripes", wrap=True),
        part("rbox", at(-0.05, 0.94), [0.50 * k, 0.04 * k, 0.50 * k], gilt, m="metal"),
        limb((-0.05, 0.62, 0.27), (-0.05, 0.36, 0.27), 0.03, gilt, m="metal"),
        part("torus", at(-0.05, 0.32, 0.27), [0.12 * k, 0.03 * k, 0.10 * k], gilt, m="metal"),
    ]
    # legs: the front pair reaching forward, the back pair kicked out behind
    for dz in (-0.12, 0.12):
        parts += [limb((0.42, 0.42, dz), (0.80, 0.10, dz), 0.14, white),
                  limb((0.80, 0.10, dz), (0.74, -0.24, dz), 0.12, white),
                  limb((-0.42, 0.42, dz), (-0.78, 0.02, dz), 0.14, white),
                  limb((-0.78, 0.02, dz), (-1.02, -0.10, dz), 0.12, white),
                  part("sph", at(0.73, -0.28, dz), [0.13 * k, 0.11 * k, 0.13 * k], gilt, m="metal"),
                  part("sph", at(-1.06, -0.12, dz), [0.13 * k, 0.11 * k, 0.13 * k], gilt, m="metal")]
    # bulbs round the canopy's rim
    parts += around(10, 0.95, 2.78, lambda a, x, zz: part(
        "sph", [x, 2.74, z + 0.10 + zz], [0.09, 0.09, 0.09], MARQUEE, m="neon"))
    return parts


@HW25.back("knife_wheel", "Wheel of Misfortune",
           "The knife-thrower's wheel, strapped on like a shield. There is a painted "
           "outline of an assistant on it, and the knives are very close to it, and "
           "one of them is not.", "rare")
def _():
    blade, handle = "#d8dde4", "#3a2214"
    centre = [0, 0.36, -0.30]
    parts = straps("#3a2214") + [
        part("disc", centre, [1.60, 1.60, 0.10], CREAM, [0, PI, 0], decal="knife_wheel"),
        part("torus", centre, [1.66, 0.10, 1.66], BRASS, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.36, -0.24], [0.30, 0.10, 0.30], IRON, [PI / 2, 0, 0], m="metal"),
    ]
    for x, y, a in ((0.38, 0.62, 0.4), (-0.42, 0.20, -0.3), (0.10, -0.10, 1.4), (-0.18, 0.80, 2.2),
                    (0.52, 0.10, -1.0)):
        p = [centre[0] + x, centre[1] + y - 0.36, -0.36]
        parts += [place("blade", [p[0], p[1], p[2] + 0.02], [0.40, 0.30, 1.0], blade,
                        r=[0, PI / 2, a], m="metal"),
                  part("rbox", [p[0], p[1], p[2] - 0.26], [0.07, 0.07, 0.30], handle, [0, 0, a])]
    return parts


@HW25.hairdo("clown_puffs", "Clown Puffs",
             "Bald as an egg on top and two great orange clouds of frizz either side. "
             "Squeezing them is not recommended. They squeeze back.", "uncommon")
def _():
    c, hi, deep = "#ff5a1a", "#ff8a3a", "#e8400e"
    parts = []
    for side in (1, -1):
        centre = [side * 0.76, 0.0, -0.08]
        parts.append(part("sph", centre, [0.48, 0.52, 0.56], c))
        # frizz round the outside of each puff
        for k in range(11):
            a = k * 2.399
            up = -0.8 + 1.6 * (k + 0.5) / 11
            ring = math.sqrt(max(0.0, 1.0 - up * up))
            dx, dz = abs(math.cos(a)) * ring, math.sin(a) * ring
            w = 0.20 + 0.06 * (k % 3)
            parts.append(part("sph", [centre[0] + side * dx * 0.22, centre[1] + up * 0.24,
                                      centre[2] + dz * 0.26], [w, w, w],
                              (hi, deep, c)[k % 3]))
    # and a fringe of it round the back
    for k, x in enumerate((-0.42, -0.21, 0.0, 0.21, 0.42)):
        parts.append(part("sph", [x, -0.10 - (k % 2) * 0.08, -0.64], [0.26, 0.26, 0.24],
                          hi if k % 2 else c))
    return parts


@HW25.hairdo("strongman_handlebar", "Strongman's Handlebar",
             "Hair slicked flat and parted dead centre, a kiss-curl on the forehead, and "
             "a moustache you could hang a barbell off. He has.", "rare")
def _():
    c = "#1a120e"
    return [
        place("hairshort", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0], decal="strands",
              wrap=True),
        part("rbox", [0, 0.50, 0.12], [0.02, 0.03, 0.70], shade(c, 0.6)),
        place("spiral", [0.06, 0.36, 0.54], [0.10, 0.14, 0.05], c, r=[PI / 2, 0, 0]),
        place("mustache", [0, -0.12, 0.53], [0.92, 0.80, 0.9], c),
        part("sph", [0.40, -0.04, 0.53], [0.07, 0.07, 0.06], c),
        part("sph", [-0.40, -0.04, 0.53], [0.07, 0.07, 0.06], c),
    ]


HW25.face("greasepaint_grin", "Greasepaint Grin",
          "Blue diamonds over the eyes, a red nose, and a red grin painted well past "
          "where the real one stops.", [
              {"k": "poly", "pts": [[-0.20, -0.34], [-0.12, -0.13], [-0.20, 0.06], [-0.28, -0.13]],
               "c": "#2f5fd0"},
              {"k": "poly", "pts": [[0.20, -0.34], [0.28, -0.13], [0.20, 0.06], [0.12, -0.13]],
               "c": "#2f5fd0"},
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.10, "h": 0.12, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.10, "h": 0.12, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.19, "y": -0.12, "w": 0.045, "h": 0.06, "c": "#16171b"},
              {"k": "ellipse", "x": 0.21, "y": -0.12, "w": 0.045, "h": 0.06, "c": "#16171b"},
              {"k": "poly", "pts": [[-0.38, 0.04], [-0.20, 0.22], [0.0, 0.28], [0.20, 0.22],
                                    [0.38, 0.04], [0.22, 0.13], [0.0, 0.17], [-0.22, 0.13]],
               "c": "#d8202a"},
              {"k": "arc", "x": 0, "y": -0.02, "r": 0.20, "a0": 0.12, "a1": 0.38, "w": 0.02,
               "c": "#16171b"},
              {"k": "ellipse", "x": 0, "y": 0.02, "w": 0.15, "h": 0.13, "c": "#e8202a"},
              {"k": "ellipse", "x": -0.025, "y": -0.005, "w": 0.04, "h": 0.03, "c": "#ffffff"},
          ], "rare")
HW25.face("sad_mime", "Sad Mime",
          "White paint, one black tear, and a mouth turned down at both ends. It is "
          "trapped in an invisible box, and so, now, are you.", [
              {"k": "ellipse", "x": 0, "y": 0.0, "w": 0.84, "h": 0.86, "c": GREASEPAINT},
              {"k": "arc", "x": -0.20, "y": -0.10, "r": 0.10, "a0": 0.55, "a1": 0.95, "w": 0.025,
               "c": "#16171b"},
              {"k": "arc", "x": 0.20, "y": -0.10, "r": 0.10, "a0": 0.55, "a1": 0.95, "w": 0.025,
               "c": "#16171b"},
              {"k": "ellipse", "x": -0.20, "y": -0.11, "w": 0.05, "h": 0.06, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.11, "w": 0.05, "h": 0.06, "c": "#16171b"},
              {"k": "poly", "pts": [[-0.20, -0.02], [-0.17, 0.06], [-0.20, 0.12], [-0.23, 0.06]],
               "c": "#16171b"},
              {"k": "arc", "x": 0, "y": 0.30, "r": 0.11, "a0": 0.62, "a1": 0.88, "w": 0.03,
               "c": "#a8141e"},
          ], "uncommon")
HW25.shirt("ringmaster_coat", "Ringmaster's Tailcoat",
           "Scarlet, double-breasted, gold buttons to the throat and a starched white "
           "front. Ladies and gentlemen, children of all ages.",
           {"torso": "#a8141e", "arms": "#a8141e", "decal": "tee_ringmaster", "weave": "felt",
            "stripe": GOLD}, "rare")
HW25.pants("harlequin_tights", "Harlequin Tights",
           "Purple and black diamonds with gold seams, for tumbling, juggling and "
           "running away from things on stilts.",
           {"legs": "#2a1238", "weave": "harlequin"})
HW25.belt("strongman_belt", "Strongman's Belt",
          "A lifting belt a hand wide, a gold star for a buckle. Rated for nine hundred "
          "pounds and one regrettable cannon.",
          {"band": "#3a2214", "buckle": GOLD, "width": 0.34, "weave": "leather", "metal": True})


def _balloon_dog(k=1.0, c="#ff3b4e", at=(0.0, 0.0, 0.0)):
    """A balloon dog, feet at ``at``, facing +Z, ``k`` times the size of the
    one that runs about (about two and a half studs tall)."""
    ox, oy, oz = at

    def p(x, y, z):
        return [ox + x * k, oy + y * k, oz + z * k]

    def s(x, y, z):
        return [x * k, y * k, z * k]

    lit = shade(c, 1.25)
    parts = [
        part("capsule", p(0, 1.15, 0), s(0.46, 1.50, 0.46), c, [PI / 2, 0, 0], m="glass", a=0.96),
        part("capsule", p(0, 1.66, 0.80), s(0.40, 1.00, 0.40), c, [0.30, 0, 0], m="glass", a=0.96),
        part("sph", p(0, 2.16, 1.00), s(0.58, 0.54, 0.62), c, m="glass", a=0.96),
        part("capsule", p(0, 2.08, 1.42), s(0.30, 0.70, 0.30), lit, [PI / 2, 0, 0], m="glass",
             a=0.96),
        part("capsule", p(0, 1.58, -0.86), s(0.24, 0.70, 0.24), lit, [-0.7, 0, 0], m="glass",
             a=0.96),
        part("sph", p(0.15, 2.26, 1.27), s(0.08, 0.10, 0.04), BLACK),
        part("sph", p(-0.15, 2.26, 1.27), s(0.08, 0.10, 0.04), BLACK),
        part("sph", p(0, 2.10, 1.78), s(0.10, 0.08, 0.06), BLACK),
    ]
    for side in (1, -1):
        parts.append(part("capsule", p(0.22 * side, 2.56, 0.92), s(0.22, 0.64, 0.22), lit,
                          [0, 0, -0.25 * side], m="glass", a=0.96))
        for dz in (0.55, -0.55):
            parts.append(part("capsule", p(0.30 * side, 0.50, dz), s(0.34, 1.00, 0.34), c,
                              m="glass", a=0.96))
    return parts


@HW25.weapon("balloon_animals", "Balloon Animals",
             "Three twists and a squeak and you have three little balloon dogs, who run "
             "at the nearest enemy wagging their tails and go off like a cannon. The "
             "clown who taught you this trick was not smiling.",
             {"kind": "summon", "cooldown": 16, "sound": "summon",
              "minion": {"name": "Balloon Dog", "model": "parts", "count": 3, "hp": 30,
                         "speed": 13, "damage": 0, "reach": 3.5, "rate": 1.0, "secs": 16,
                         "explode": {"radius": 6.5, "damage": 36, "knock": 16,
                                     "fx": "confetti"}}},
             [["+", "Twists three balloon dogs that run at the nearest enemy"],
              ["+", "Each one pops on arrival: 36 damage and a shove to everyone near"],
              ["-", "They have 30 health and pop where they stand if shot"],
              ["-", "16 seconds before you can twist the next three"]], rarity="legendary",
             minion={"name": "Balloon Dog", "model": "parts", "scale": 1.0,
                     "parts": _balloon_dog()})
def _():
    # held by the end of its tail, the rest of it dangling in front of the hand
    return _balloon_dog(0.30, at=(0.0, -0.555, 0.326)) + [
        part("sph", [0, 0.0, 0.0], [0.08, 0.08, 0.08], shade("#ff3b4e", 1.25), m="glass")]


def _pin(at, k, spin=0.0):
    """A juggling club pointing along +Z from ``at``."""
    x, y, z = at
    extra = {"spin": spin} if spin else {}
    return [part("capsule", [x, y, z + 0.30 * k], [0.10 * k, 0.60 * k, 0.10 * k], CREAM,
                 [PI / 2, 0, 0], **extra),
            part("sph", [x, y, z + 0.80 * k], [0.30 * k, 0.30 * k, 0.56 * k], CREAM, **extra),
            part("cyl", [x, y, z + 0.72 * k], [0.31 * k, 0.08 * k, 0.31 * k], TENT,
                 [PI / 2, 0, 0], **extra),
            part("cyl", [x, y, z + 0.90 * k], [0.29 * k, 0.06 * k, 0.29 * k], "#2f5fd0",
                 [PI / 2, 0, 0], **extra),
            part("sph", [x, y, z], [0.14 * k, 0.14 * k, 0.14 * k], TENT, **extra)]


@HW25.weapon("juggling_pins", "Juggler's Pins",
             "Three clubs thrown in a fan, end over end. They bounce off walls, and "
             "every wall they come off makes them hit harder, which is how the "
             "Flying Dukovnys lost two of their brothers.",
             {"kind": "projectile", "projectile": "pin", "damage": 14, "splash": 2.8,
              "splash_damage": 14, "rpm": 70, "mag": 3, "reload": 2.0, "speed": 82,
              "range": 220, "auto": False, "sound": "throw", "recoil": 0.6, "reserve": 30,
              "gravity_scale": 0.55, "self_damage": 0.0, "knockback": 4,
              "volley": [3, 0.14], "volley_spread": 1.2, "bounce": 3, "bounce_ramp": 0.5},
             [["+", "Every throw is three pins"],
              ["+", "Pins bounce off walls up to three times"],
              ["+", "Each bounce adds half again to the damage: 35 after three walls"],
              ["-", "14 damage straight from the hand"],
              ["-", "Pins drop as they fly"]], rarity="legendary",
             proj=lambda: _pin([0, 0, -0.40], 0.9, spin=12.0))
def _():
    return _pin([0.0, 0.0, 0.10], 1.0) + _pin([0.16, 0.10, -0.10], 0.8) + \
        _pin([-0.16, 0.06, -0.12], 0.8)


@HW25.weapon("ringmaster_whip", "Ringmaster's Whip",
             "Seventeen feet of black bull-hide with a crack like a pistol shot. "
             "Whoever it catches comes to heel -- dragged in across the ring -- and "
             "the whole troupe knows exactly who to aim at.",
             {"kind": "melee", "damage": 16, "headshot": 1.0, "rpm": 75, "range": 17.0,
              "arc": 0.30, "sound": "swing", "knockback": 0,
              "on_hit": {"pull": 34, "mark": [0.20, 5.0]}},
             [["+", "17 stud reach: the longest arm in the show"],
              ["+", "Drags whoever it catches across to your feet"],
              ["+", "...and marks them: they take 20% more damage from everyone for 5 "
                    "seconds"],
              ["-", "Only 16 damage a crack"],
              ["-", "A narrow lash: you have to aim it"]], rarity="legendary")
def _():
    hide = "#16121a"
    parts = [part("cyl", [0, 0.0, 0.0], [0.13, 0.62, 0.13], "#3a2214", [PI / 2, 0, 0],
                  decal="leather", wrap=True),
             part("sph", [0, 0.0, -0.34], [0.17, 0.17, 0.17], GOLD, m="metal"),
             part("torus", [0, 0.0, 0.30], [0.16, 0.05, 0.16], GOLD, [PI / 2, 0, 0], m="metal")]
    # the lash, thinning as it curls away and down
    path = [(0, 0.0, 0.30), (0, 0.06, 0.80), (0.04, 0.02, 1.30), (0.10, -0.12, 1.72),
            (0.12, -0.34, 2.02), (0.06, -0.56, 2.14), (-0.04, -0.70, 2.04)]
    for n in range(len(path) - 1):
        parts.append(rod(path[n], path[n + 1], 0.09 - n * 0.011, hide, t="capsule"))
    parts.append(place("ribbon", [-0.06, -0.76, 1.98], [0.10, 0.18, 0.10], TENT))
    return parts


@HW25.gear("toffee_apple", "Toffee Apple",
           "A red apple in a hard red shell of toffee on a stick, from the stall at the "
           "end of the midway. A sugar rush that hits like a strongman.",
           {"kind": "consume", "cooldown": 30, "sound": "eat",
            "consume": {"heal": 25, "might": [0.20, 6.0]}},
           [["+", "Heals 25"],
            ["+", "Sugar rush: 20% more damage for 6 seconds"],
            ["-", "30 second cooldown"]], rarity="rare")
def _():
    return [
        part("cyl", [0, 0.20, 0.10], [0.06, 0.60, 0.06], "#c9a26a"),
        part("sph", [0, 0.62, 0.10], [0.46, 0.42, 0.46], "#b0101a", m="glass"),
        part("sph", [0, 0.60, 0.10], [0.48, 0.30, 0.48], "#8a0a12", m="glass", a=0.8),
        part("cyl", [0, 0.86, 0.10], [0.03, 0.10, 0.03], "#4a2f1b"),
        place("leaf", [0.08, 0.88, 0.10], [0.30, 0.20, 1.0], "#4f8a3c", r=[0, 0, -0.5]),
        part("sph", [0.16, 0.44, 0.24], [0.08, 0.12, 0.08], "#8a0a12", m="glass"),
        part("sph", [-0.18, 0.46, 0.0], [0.07, 0.10, 0.07], "#8a0a12", m="glass"),
    ]


HW25.effect("carnival_lights", name="Carnival Lights", rate=7.0, life=[1.4, 2.0],
            size=[0.12, 0.18], grow=0.0, gravity=0.0, spread=0.05, rise=[0.0, 0.05],
            blend="add", spin=0.0, colors=["#ffd36a", "#ff3b4e", "#fff3b0", "#3cc8ff"],
            shape="spark", radius=0.95, orbit=2.0, wobble=0.0)
HW25.effect("runaway_balloons", name="Runaway Balloons", rate=1.6, life=[2.6, 3.4],
            size=[0.36, 0.50], grow=0.0, gravity=-0.6, spread=0.5, rise=[0.3, 0.6],
            blend="normal", spin=0.2, colors=["#ff3b4e", "#ffd36a", "#3cc8ff", "#7dff9a"],
            shape="balloon", radius=0.6, upright=True, wobble=0.4)
HW25.opening(
    sky={"top": "#120612", "horizon": "#3a0f1a", "sun": [0.2, 0.9, 0.6], "clouds": 0,
         "tint": "#ffc8a0"},
    ambient="#7a4a3a", beam="#ffd36a", seep="carnival_lights", after="runaway_balloons",
    burst=["#ff3b4e", "#ffd36a", "#f4ecd8", "#3cc8ff"],
    pieces=[{"shape": "ticket", "colors": ["#e8d6a8", "#ff3b4e"], "blend": "normal"},
            {"shape": "balloon", "colors": ["#ff3b4e", "#3cc8ff", "#ffd36a"], "blend": "normal"},
            {"shape": "mask", "colors": ["#f6f2ee", "#ff3b4e"], "blend": "normal"},
            {"shape": "confetti", "colors": ["#ffd36a", "#ff5ad1", "#7dff9a"], "blend": "normal"}],
    backdrop="circus", title_wait="The calliope starts to play...",
    title_shake="Something wants out of the trunk...")
HW25.award("Big Top Terror", ["Ticket Holder", "Front Row", "Roustabout", "Lion Tamer",
                              "Ringmaster", "Master of the Big Top"],
           "Opened Big Top Trunks during the Big Top Terror, Halloween 2025.",
           "em_circustent", "moon")
HW25.bundle("pair", "Two for the Show", 1, 1050, "One Big Top Trunk, one Admit-One Key.")
HW25.bundle("troupe", "The Whole Troupe", 3, 3000, "Three trunks, three keys. Saves 300.")


# ============================================================ 2026
HW26 = Event(
    "halloween", "halloween", 2026, "hw26",
    name="Hallowed Harvest", title="The Hallowed Harvest",
    blurb="The lamps are going out across Harrow County. A crate of things that "
          "should have stayed buried, a key with fangs, and weapons that only exist "
          "until the first of November is long gone.",
    tagline="Dug up at midnight. Something inside is still moving.",
    starts="2026-10-01", ends="2026-11-09",
    colors={"accent": "#ff8c1a", "deep": "#1a0f24", "glow": "#6bff9a"},
    grades={"uncommon": 40, "rare": 40, "legendary": 13, "mythic": 7},
    family_effects=["floating_bones", "flying_skulls", "jack_o_lanterns",
                    "skeletal_mishap", "bat_swarm", "haunted_wisps", "cursed_runes",
                    "spider_descent", "raven_feathers", "candlelight_vigil"],
    hero_effect="haunted_wisps", stencil="crate_hallowed")
HW26.crate = next(c for c in cosmetics.CRATES if c["id"] == "crate_halloween")
HW26.key = next(k for k in cosmetics.KEYS if k["id"] == "key_halloween")
HW26.key["data"]["shoulder"] = -0.40
HW26.items.extend(cosmetics.HALLOWEEN_COSMETICS)
HW26.items.extend(cosmetics.HALLOWEEN_WEAPONS)
HW26.grade_of.update({"use_hollow_harvester": "mythic", "use_jack_o_launcher": "mythic"})
# the two that shipped first get their cards written out the way the later
# weapons' are
_HW26_ATTRS = {
    "use_hollow_harvester": [
        ["+", "Banks a soul for every kill it takes, up to three"],
        ["+", "The next swing spends them all: wider, longer, +16 damage and +9 health "
              "per soul"],
        ["-", "Slow to swing: 70 a minute"],
        ["-", "A cold swing is no better than a sword"]],
    "use_jack_o_launcher": [
        ["+", "Trick: the pumpkin bursts for 40 on every enemy nearby"],
        ["+", "Treat: the candy inside heals every teammate in the blast 22, you too"],
        ["-", "A high, slow lob"],
        ["-", "No rocket jumping off it"]],
}
for _it in HW26.items:
    if _it["id"] in _HW26_ATTRS:
        _it["data"].setdefault("attrs", _HW26_ATTRS[_it["id"]])
# ...and the rest of the Hallowed Harvest: the Pumpkin King's court, the
# scarecrows of Harrow County, and the staff that wakes its churchyard
HARVEST = "#ff8c1a"
RIND = "#d9661a"
VINE = "#3f6a2a"
STRAW = "#d9b44a"
CROW = "#141218"


def _crow(at, k=1.0, facing=0.0):
    """A crow perched at ``at`` (its feet), looking along ``facing``."""
    x, y, z = at
    f = [math.sin(facing), 0.0, math.cos(facing)]

    def off(dz, dy):
        return [x + f[0] * dz * k, y + dy * k, z + f[2] * dz * k]
    return [
        part("sph", off(0.0, 0.16), [0.26 * k, 0.24 * k, 0.40 * k], CROW, [0, facing, 0]),
        part("sph", off(0.17, 0.32), [0.18 * k, 0.18 * k, 0.20 * k], CROW),
        place("cone", off(0.32, 0.31), [0.06 * k, 0.16 * k, 0.06 * k], "#c9a227",
              r=[PI / 2, facing, 0]),
        part("sph", off(0.24, 0.36), [0.04 * k, 0.04 * k, 0.04 * k], "#ffd36a", m="neon"),
        place("tri", off(-0.30, 0.12), [0.20 * k, 0.24 * k, 0.4], CROW, r=[-1.2, facing, 0]),
        part("cyl", off(0.02, 0.03), [0.03 * k, 0.08 * k, 0.03 * k], "#c9a227"),
    ]


@HW26.hat("pumpkin_king", "Pumpkin King's Crown",
          "Carved from the biggest pumpkin in Harrow County, lit from inside, with a "
          "little lantern on every point. The vine is still growing. Slowly. Towards "
          "you.", "legendary")
def _():
    parts = [
        place("spikecrown", [0, -0.30, 0], [1.86, 0.80, 1.80], HARVEST, anchor=[0, 0, 0],
              decal="felt", wrap=True),
        ringband(-0.24, 0.14, RIND),
        # the carved face in the band, lit from within
        place("tri", [0.24, 0.00, 0.905], [0.20, 0.18, 0.3], "#ffd36a", m="neon"),
        place("tri", [-0.24, 0.00, 0.905], [0.20, 0.18, 0.3], "#ffd36a", m="neon"),
        place("grin", [0, -0.14, 0.905], [0.56, 0.22, 0.3], "#ffd36a", m="neon"),
        # the vine curling round it
        place("spiral", [0.80, 0.22, 0.36], [0.20, 0.44, 0.20], VINE, r=[0.2, 0, -0.4]),
        place("spiral", [-0.66, 0.30, -0.52], [0.18, 0.40, 0.18], VINE, r=[-0.3, 0, 0.5]),
        place("leaf", [0.70, 0.46, 0.50], [0.5, 0.40, 1.0], VINE, r=[0, 0.7, -0.5]),
        place("leaf", [-0.56, 0.52, -0.62], [0.5, 0.40, 1.0], VINE, r=[0, -2.4, 0.5]),
    ]
    parts += around(7, 0.92, 0.0, lambda a, x, z: place(
        "pumpkin", [x * 0.985, 0.58, z * 0.965], 0.24, HARVEST, anchor=[0, 0, 0]),
        start=TAU / 14)
    parts += around(7, 0.92, 0.0, lambda a, x, z: part(
        "sph", [x * 0.985, 0.66, z * 0.965], [0.08, 0.08, 0.08], "#ffd36a", m="neon"),
        start=TAU / 14)
    return parts


@HW26.hat("scarecrow_slouch", "Scarecrow's Slouch",
          "A straw hat that has stood in a field for forty Octobers, patched, frayed and "
          "never once empty -- there is always a crow on the brim. Always the same "
          "crow.", "rare")
def _():
    parts = [
        place("brim", [0, -0.12, 0], [2.50, 1.3, 2.40], STRAW, anchor=[0, 0, 0],
              decal="straw", wrap=True),
        dome(-0.32, 0.86, STRAW, t="capcrown", decal="straw", wrap=True),
        # the pinch in the top, pushed in by forty Octobers of rain
        part("sph", [0.0, 0.50, 0.10], [0.60, 0.10, 0.50], shade(STRAW, 0.78), decal="straw",
             wrap=True),
        ringband(-0.22, 0.16, "#a8141e", margin=0.05, decal="canvas"),
        # a patch sewn on the crown
        part("rbox", [-0.30, 0.02, 0.86], [0.32, 0.28, 0.03], "#6a5a3a", [0.12, -0.33, 0],
             decal="stitches"),
    ]
    # straw poking out from under the brim all the way round
    for k in range(16):
        a = k * TAU / 16 + 0.1
        r0, r1 = 0.88, 1.08 + 0.08 * (k % 3)
        parts.append(rod([math.sin(a) * r0, -0.14, math.cos(a) * r0 * 0.96],
                         [math.sin(a) * r1, -0.30 - 0.06 * (k % 2), math.cos(a) * r1 * 0.96],
                         0.03, shade(STRAW, 1.1 if k % 2 else 0.85)))
    parts += _crow([0.86, -0.04, 0.42], 1.0, facing=0.6)
    return parts


@HW26.hat("harvest_moon", "Harvest Moon",
          "The big orange moon of the last week of October, hung behind your head like "
          "a saint's halo -- the bats circling it included.", "rare", hair="show")
def _():
    parts = [
        part("disc", [0, 0.50, -0.90], [2.00, 2.00, 0.10], "#ff9a3a", decal="harvest_moon",
             m="neon"),
        part("torus", [0, 0.50, -0.92], [2.04, 0.06, 2.04], "#ffd36a", [PI / 2, 0, 0], m="neon",
             a=0.5),
    ]
    for x, y, k, tilt in ((0.70, 1.20, 0.42, 0.3), (-0.82, 0.70, 0.36, -0.2), (0.30, 1.52, 0.30, 0.1),
                          (-0.40, 1.34, 0.26, -0.4)):
        parts.append(place("bat", [x, y, -0.80], [k, k, 1.0], CROW, r=[0, 0, tilt]))
    return parts


@HW26.back("scarecrow_post", "Scarecrow's Crossbar",
           "The crosspiece off the old scarecrow in the north field, rags and straw and "
           "all. Wear it and the crows will follow you home. Two of them already have.",
           "legendary")
def _():
    wood = "#5a3a22"
    z = -0.42
    parts = [
        part("rbox", [0, 0.88, z], [3.80, 0.20, 0.20], wood, decal="planks", wrap=True),
        part("rbox", [0, -0.40, z - 0.06], [0.24, 3.20, 0.20], wood, decal="planks", wrap=True),
        part("rbox", [0, 0.88, z - 0.02], [0.30, 0.30, 0.26], shade(wood, 0.8)),
        part("cyl", [0, 0.88, z + 0.12], [0.08, 0.06, 0.08], IRON, [PI / 2, 0, 0], m="metal"),
    ]
    for side in (1, -1):
        # straw bursting out of each end, and rags hanging off it
        for k in range(7):
            a = (k - 3) * 0.32
            parts.append(rod([1.86 * side, 0.88, z],
                             [(2.16 + 0.06 * (k % 2)) * side, 0.88 + math.sin(a) * 0.30,
                              z + math.cos(a) * 0.10 - 0.05],
                             0.04, shade(STRAW, 1.1 if k % 2 else 0.85)))
        for k, (x, length, c) in enumerate(((1.40, 0.90, "#6a5a3a"), (1.66, 0.70, "#4a6a3a"),
                                            (1.18, 0.60, "#8a3a22"))):
            parts.append(part("rbox", [x * side, 0.88 - length / 2 - 0.08, z - 0.04],
                              [0.20, length, 0.03], c, [0, 0, 0.06 * side * (k + 1)],
                              decal="canvas"))
    parts += _crow([1.52, 0.98, z], 1.1, facing=0.4)
    parts += _crow([-1.70, 0.98, z], 0.9, facing=-0.8)
    return parts


@HW26.back("bushel_of_gourds", "Bushel of Gourds",
           "A wicker bushel off the back of the harvest cart: three pumpkins, a warty "
           "gourd, two ears of corn and something underneath that keeps shifting.",
           "uncommon")
def _():
    parts = straps("#3a2214") + [
        place("cask", [0, -0.30, -0.52], [1.20, 1.00, 0.80], "#a8783a", anchor=[0, 0, 0],
              decal="wicker", wrap=True),
        part("torus", [0, 0.70, -0.52], [1.22, 0.08, 0.82], "#7a5426"),
    ]
    for x, y, z, k, c in ((0.24, 0.80, -0.50, 0.46, HARVEST), (-0.28, 0.78, -0.56, 0.40, RIND),
                          (0.02, 0.94, -0.62, 0.34, "#ffb347")):
        parts += [place("pumpkin", [x, y, z], k, c, anchor=[0, 0, 0]),
                  part("cyl", [x, y + 0.36 * k, z], [0.06, 0.10, 0.06], VINE)]
    parts += [place("teardrop", [-0.10, 0.82, -0.30], [0.22, 0.40, 0.22], "#e8d24a", r=[0.6, 0, 0.3]),
              part("capsule", [0.42, 0.98, -0.40], [0.14, 0.52, 0.14], "#f2c230", [0.3, 0, -0.4]),
              place("leaf", [0.46, 0.86, -0.34], [0.5, 0.70, 1.0], "#c9b06a", r=[0.3, 0, -0.6]),
              part("capsule", [-0.46, 0.96, -0.66], [0.14, 0.48, 0.14], "#f2c230", [-0.3, 0, 0.5]),
              place("leaf", [-0.48, 0.84, -0.62], [0.5, 0.66, 1.0], "#c9b06a", r=[-0.3, 0, 0.6])]
    return parts


@HW26.hairdo("banshee_locks", "Banshee's Wail",
             "Hair gone white in one night and blown straight back by a wind nobody else "
             "can feel. If you listen very carefully you can hear it screaming.", "rare")
def _():
    c = "#e8eef8"
    parts = [place("hairlong", [0, 0, 0], [1.06, 1.06, 1.06], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k, (x, y) in enumerate(((-0.30, 0.30), (0.0, 0.40), (0.30, 0.30), (-0.20, 0.05),
                                (0.20, 0.05), (0.0, -0.20))):
        parts.append(place("teardrop", [x, y, -0.52], [0.24, 0.80, 0.20], c if k % 2 else "#c9d6ea",
                           anchor=[0, 0.1, 0], r=[-1.9, 0, x * 0.6], a=0.75))
    return parts


@HW26.hairdo("ember_quiff", "Ember Quiff",
             "A pompadour combed up and forward until the tip caught light. It has been "
             "smouldering since 1958. It still looks good.", "rare")
def _():
    c = "#2a1a14"
    return [
        place("hairshort", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0], decal="strands",
              wrap=True),
        place("teardrop", [0, 0.50, 0.08], [0.56, 0.78, 0.46], c, anchor=[0, 0.1, 0],
              r=[1.05, 0, 0], decal="strands", wrap=True),
        place("teardrop", [0, 0.62, 0.42], [0.40, 0.46, 0.34], "#ff6a1a", anchor=[0, 0.1, 0],
              r=[1.25, 0, 0]),
        place("flame", [0, 0.78, 0.74], [0.32, 0.46, 0.32], "#ffd36a", r=[0.6, 0, 0], m="neon",
              spin=3.0),
        place("flame", [0.10, 0.70, 0.66], [0.20, 0.30, 0.20], "#ff8c1a", r=[0.6, 0, 0.3],
              m="neon"),
    ]


HW26.face("jacks_grin", "Jack's Grin",
          "Triangle eyes, triangle nose, and a grin cut with a kitchen knife by "
          "somebody who was in a hurry.", [
              {"k": "poly", "pts": [[-0.30, -0.06], [-0.20, -0.26], [-0.10, -0.06]], "c": "#16171b"},
              {"k": "poly", "pts": [[0.10, -0.06], [0.20, -0.26], [0.30, -0.06]], "c": "#16171b"},
              {"k": "poly", "pts": [[-0.05, 0.06], [0.0, -0.03], [0.05, 0.06]], "c": "#16171b"},
              {"k": "poly", "pts": [[-0.36, 0.10], [-0.26, 0.14], [-0.20, 0.10], [-0.14, 0.18],
                                    [-0.06, 0.13], [0.02, 0.20], [0.10, 0.13], [0.16, 0.19],
                                    [0.24, 0.12], [0.36, 0.10], [0.30, 0.24], [0.14, 0.32],
                                    [0.0, 0.34], [-0.16, 0.32], [-0.30, 0.24]], "c": "#16171b"},
              {"k": "poly", "pts": [[-0.06, 0.24], [0.02, 0.24], [-0.02, 0.32]], "c": "#ff8c1a"},
          ], "uncommon")
HW26.face("hollow_eyes", "Hollow Eyes",
          "Two empty sockets with a pinprick of light deep down in each, and a mouth "
          "sewn shut with a dozen black stitches.", [
              {"k": "ellipse", "x": -0.20, "y": -0.12, "w": 0.16, "h": 0.18, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.12, "w": 0.16, "h": 0.18, "c": "#16171b"},
              {"k": "ellipse", "x": -0.20, "y": -0.11, "w": 0.03, "h": 0.03, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.20, "y": -0.11, "w": 0.03, "h": 0.03, "c": "#ffffff"},
              {"k": "line", "x1": -0.22, "y1": 0.18, "x2": 0.22, "y2": 0.18, "w": 0.02, "c": "#16171b"},
          ] + [{"k": "line", "x1": x, "y1": 0.14, "x2": x, "y2": 0.22, "w": 0.015, "c": "#16171b"}
               for x in (-0.18, -0.11, -0.04, 0.03, 0.10, 0.17)], "rare")
HW26.shirt("harvest_flannel", "Harvest Flannel",
           "A rust-red flannel shirt with straw coming out of the collar and a patch "
           "over the heart where something tried to get in.",
           {"torso": "#8a2a14", "arms": "#8a2a14", "weave": "flannel", "decal": "tee_scarecrow"},
           "uncommon")
HW26.pants("scarecrow_patches", "Scarecrow's Dungarees",
           "Faded denim held together by patches, with straw sticking out of both cuffs.",
           {"legs": "#4a5a7a", "weave": "patched_denim", "cuff": STRAW})
HW26.belt("lantern_belt", "Jack's Lantern Belt",
          "A cracked leather belt with a lit jack-o'-lantern for a buckle and a pouch of "
          "candle stubs either side.",
          {"band": "#2a1a10", "buckle": HARVEST, "width": 0.24, "weave": "leather", "glow": True,
           "pouch": True})


@HW26.weapon("restless_staff", "Staff of the Restless Dead",
             "A blackthorn staff with a churchyard skull on the end. Strike the ground with "
             "it and four of Harrow County's dead climb out to fight for you -- and every "
             "one of them is paid for in your own blood.",
             {"kind": "summon", "cooldown": 60, "cost_hp": 25, "sound": "staff",
              "minion": {"name": "Restless Dead", "model": "zombie", "count": 4, "hp": 60,
                         "speed": 15, "damage": 12, "reach": 4.5, "rate": 1.0, "secs": 30,
                         "glow": "#6bff9a"}},
             [["+", "Raises four of the dead to fight at your side for 30 seconds"],
              ["+", "They hunt the nearest enemy -- players and infected alike -- and bite for "
                    "12"],
              ["-", "Costs you 25 health to raise them"],
              ["-", "One-minute cooldown"]], rarity="legendary")
def _():
    wood = "#2a1e16"
    parts = [part("rbox", [0, 0.0, -0.10], [0.16, 0.16, 0.44], "#5a1428", decal="canvas")]
    path = [(0, 0.0, -0.40), (0.02, 0.02, 0.30), (-0.03, 0.0, 1.00), (0.02, 0.04, 1.62)]
    for n in range(len(path) - 1):
        parts.append(rod(path[n], path[n + 1], 0.11 - n * 0.008, wood, t="capsule"))
    # knots and thorns
    for z, a in ((0.40, 0.8), (0.86, -1.2), (1.30, 2.4)):
        parts.append(rod([0.02, 0.02, z], [0.02 + math.cos(a) * 0.16, 0.02 + math.sin(a) * 0.16,
                                            z + 0.06], 0.035, wood, t="cone"))
    parts += _skull([0.02, 0.06, 1.84], 0.70, BONE, facing=0.0, glow=GHOST_GREEN)
    parts += [part("sph", [0.02, 0.06, 1.84], [0.62, 0.58, 0.62], GHOST_GREEN, m="neon", a=0.18)]
    # finger bones on cords, hanging from below the skull
    for x, length in ((0.10, 0.30), (-0.08, 0.40)):
        parts += [rod([x, -0.10, 1.66], [x, -0.10 - length, 1.66], 0.015, "#3a2a1c"),
                  part("capsule", [x, -0.18 - length, 1.66], [0.05, 0.16, 0.05], BONE)]
    return parts


@HW26.gear("trick_or_treat_bucket", "Trick-or-Treat Bucket",
           "A plastic jack-o'-lantern full of whatever Harrow County hands out at the door. "
           "Usually it's a treat. Sometimes it's a toothbrush.",
           {"kind": "consume", "cooldown": 26, "sound": "eat",
            "consume": {"random": [
                {"name": "Treat! A full-size bar.", "heal": 40},
                {"name": "Treat! A sugar rush.", "heal": 10, "speed": [0.30, 6.0]},
                {"name": "Treat! A jawbreaker.", "shield": [30, 8.0]},
                {"name": "Treat! Gold-wrapped toffee.", "heal": 15, "might": [0.20, 6.0]},
                {"name": "Trick! It was a toothbrush.", "trick": {"slow": [0.30, 3.0]}},
            ]}},
           [["+", "A lucky dip: one of four treats -- 40 health, a sugar rush, a 30 point "
                  "shield, or more damage for 6 seconds"],
            ["-", "One time in five it is a trick: a toothbrush, and 3 seconds of feeling "
                  "very slow"],
            ["-", "26 second cooldown"]], rarity="rare")
def _():
    parts = [
        place("pumpkin", [0, 0.06, 0.18], 0.62, HARVEST, anchor=[0, 0, 0], m="glass"),
        place("tri", [0.10, 0.36, 0.492], [0.10, 0.09, 0.2], BLACK),
        place("tri", [-0.10, 0.36, 0.492], [0.10, 0.09, 0.2], BLACK),
        place("grin", [0, 0.24, 0.484], [0.30, 0.10, 0.2], BLACK),
        part("cyl", [0, 0.58, 0.18], [0.54, 0.02, 0.54], "#2a1a10"),
        place("arch", [0, 0.60, 0.18], [0.60, 0.50, 0.4], BLACK, anchor=[0, 0, 0]),
    ]
    for x, z, c in ((0.10, 0.12, "#ff3b4e"), (-0.12, 0.24, "#7dff9a"), (0.04, 0.30, "#ffd36a")):
        parts.append(part("rbox", [x, 0.62, z], [0.16, 0.06, 0.08], c, [0.3, x * 4, 0.2]))
    return parts


# the two effects made for this crate turn up three times as often as the
# older crypt set
HW26.effect_weights.update({"phantom_procession": 3.0, "trick_or_treat": 3.0})
HW26.opening(
    sky={"top": "#0c0716", "horizon": "#2b1640", "sun": [0.2, 0.9, 0.6], "clouds": 0,
         "tint": "#b6a0ff"},
    ambient="#6a5c96", beam="#6bff9a", seep="haunted_wisps", after="phantom_procession",
    burst=["#6bff9a", "#c78bff", "#ff9a2e", "#ffffff"],
    pieces=[{"shape": "ghost", "colors": ["#ffffff", "#e9f4ff", "#c9e2ff"], "blend": "normal"},
            {"shape": "bat", "colors": ["#3a2a55", "#1d1830", "#443a66"], "blend": "normal"},
            {"shape": "pumpkin", "colors": ["#ffb347", "#ff8c1a", "#e8631a"], "blend": "normal"},
            {"shape": "candycorn", "colors": ["#ffe08a", "#ffffff", "#ffb347"], "blend": "normal"},
            {"shape": "wisp", "colors": ["#b8ffd2", "#6bff9a", "#2ea98a"], "blend": "add"}],
    backdrop="halloween", title_wait="Something stirs inside...",
    title_shake="It is trying to get out...")
HW26.offers = [
    {"id": "offer_halloween_pair", "name": "Hallowed Pair", "series": "halloween",
     "contents": {"crate_halloween": 1, "key_halloween": 1}, "price": 1050,
     "blurb": "A Hallowed Harvest crate and the key with fangs."},
    {"id": "offer_trick_or_treat", "name": "Trick-or-Treat Bag", "series": "halloween",
     "contents": {"crate_halloween": 3, "key_halloween": 3}, "price": 3000,
     "blurb": "Three crates, three keys and a bag to carry them in. Save 300."},
]

EVENTS = [HW22, HW23, HW24, HW25, HW26]
