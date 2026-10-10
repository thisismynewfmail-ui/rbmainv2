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
                  pompom, ringband, rotate, shade, sides, straps)

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
        parts.append(place("teardrop", [x, 0.50, z], [0.16, 0.40, 0.16], c, anchor=[0, -0.5, 0],
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

EVENTS = [HW22, HW23, HW24, HW26]
