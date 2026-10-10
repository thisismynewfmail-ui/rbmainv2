"""The central item catalogue.

Everything wearable, holdable or purchasable in BLOCKHAVEN lives here.  The
catalogue is data only -- it is synchronised into the ``items`` table on boot,
so adding a new hat later is a matter of appending one dict and restarting.

Geometry convention (matches static/js/engine + app/game):
  * 1 unit == 1 "stud".  +Y is up, the avatar faces +Z.
  * Avatar root sits at the feet.  Torso 2x2x1, head 1.4x1.2x1.2,
    limbs 1x2x1.  Total height 5.2.
  * Hat parts are expressed relative to the TOP CENTRE OF THE HEAD (0,0,0).
  * Back parts are relative to the centre of the torso's back face.
  * Held ("usable") parts are relative to the right hand grip point, with the
    barrel pointing towards +Z.

Primitive types understood by the renderer and by the server side collision
helpers: box, cyl (cylinder, Y axis), sph (sphere), cone, wedge.
"""
from __future__ import annotations

from typing import Any, Dict, List

# --------------------------------------------------------------------- tiers
TIERS: Dict[str, Dict[str, Any]] = {
    "normal": {
        "id": "normal",
        "label": "Normal",
        "color": "#e8b71a",
        "text": "#4a3800",
        "border": "#b8900d",
        "glow": "#ffd95e",
        "rank": 0,
    },
    "unusual": {
        "id": "unusual",
        "label": "Unusual",
        "color": "#8b3fd6",
        "text": "#f3e6ff",
        "border": "#5d1f9c",
        "glow": "#c78bff",
        "rank": 1,
    },
}

# ------------------------------------------------------------------ effects
# Particle recipes for Unusual hats.  Consumed by static/js/engine/particles.js
UNUSUAL_EFFECTS: Dict[str, Dict[str, Any]] = {
    "burning": {
        "name": "Burning Flames", "rate": 26, "life": [0.55, 0.95],
        "size": [0.30, 0.62], "grow": -0.55, "gravity": 1.9,
        "spread": 0.34, "rise": [1.6, 2.6], "blend": "add", "spin": 2.2,
        "colors": ["#ffd24a", "#ff9422", "#ff5311", "#8f2a06"],
        "shape": "flame", "radius": 0.42,
    },
    "scorching": {
        "name": "Scorching Flames", "rate": 34, "life": [0.5, 0.85],
        "size": [0.24, 0.5], "grow": -0.4, "gravity": 2.6,
        "spread": 0.5, "rise": [2.1, 3.3], "blend": "add", "spin": 3.4,
        "colors": ["#ffffff", "#ffe66d", "#ff8c1a", "#e02b00"],
        "shape": "flame", "radius": 0.5,
    },
    "starstruck": {
        "name": "Starstruck", "rate": 14, "life": [0.9, 1.5],
        "size": [0.20, 0.42], "grow": -0.1, "gravity": -0.4,
        "spread": 0.55, "rise": [0.4, 1.1], "blend": "add", "spin": 4.5,
        "colors": ["#fff9c4", "#ffe14d", "#ffc400", "#fff"],
        "shape": "star", "radius": 0.66, "orbit": 1.1,
    },
    "void_mist": {
        "name": "Void Mist", "rate": 16, "life": [1.1, 1.9],
        "size": [0.38, 0.72], "grow": 0.18, "gravity": 0.25,
        "spread": 0.46, "rise": [0.5, 1.0], "blend": "add", "spin": 1.2,
        "colors": ["#c78bff", "#8b3fd6", "#4b1580", "#2a0a4a"],
        "shape": "puff", "radius": 0.52,
    },
    "frostbite": {
        "name": "Frostbite", "rate": 15, "life": [1.3, 2.1],
        "size": [0.18, 0.34], "grow": -0.05, "gravity": -1.4,
        "spread": 0.62, "rise": [0.1, 0.45], "blend": "normal", "spin": 2.8,
        "colors": ["#ffffff", "#cdeaff", "#8fd0ff", "#5aa9e6"],
        "shape": "flake", "radius": 0.7,
    },
    "circuitry": {
        "name": "Circuitry", "rate": 20, "life": [0.6, 1.0],
        "size": [0.14, 0.26], "grow": -0.1, "gravity": 0.0,
        "spread": 0.2, "rise": [0.0, 0.3], "blend": "add", "spin": 6.0,
        "colors": ["#b9ffcf", "#37f28a", "#0bbd63", "#e8fff2"],
        "shape": "spark", "radius": 0.78, "orbit": 2.4,
    },
    "bubbly": {
        "name": "Bubbly", "rate": 11, "life": [1.4, 2.3],
        "size": [0.22, 0.48], "grow": 0.1, "gravity": -0.8,
        "spread": 0.5, "rise": [0.6, 1.2], "blend": "normal", "spin": 1.0,
        "colors": ["#dff6ff", "#a9e4ff", "#ffffff"],
        "shape": "bubble", "radius": 0.5,
    },
    "ember_storm": {
        "name": "Ember Storm", "rate": 22, "life": [0.9, 1.6],
        "size": [0.12, 0.3], "grow": -0.2, "gravity": 1.1,
        "spread": 0.75, "rise": [1.0, 2.0], "blend": "add", "spin": 3.0,
        "colors": ["#ffb347", "#ff6b1a", "#7a2f0a", "#3d1c0a"],
        "shape": "spark", "radius": 0.6,
    },
    "sunbeam": {
        "name": "Sunbeam", "rate": 12, "life": [1.0, 1.7],
        "size": [0.30, 0.6], "grow": 0.05, "gravity": -0.2,
        "spread": 0.3, "rise": [0.2, 0.55], "blend": "add", "spin": 1.6,
        "colors": ["#fff6c9", "#ffd75e", "#ffae19"],
        "shape": "ray", "radius": 0.72, "orbit": 0.9,
    },
    "toxic_haze": {
        "name": "Toxic Haze", "rate": 17, "life": [1.2, 2.0],
        "size": [0.34, 0.66], "grow": 0.22, "gravity": 0.3,
        "spread": 0.5, "rise": [0.35, 0.85], "blend": "add", "spin": 0.9,
        "colors": ["#e8ffb0", "#9ade3a", "#4e9e17", "#1f4d08"],
        "shape": "puff", "radius": 0.55,
    },
    "static_charge": {
        "name": "Static Charge", "rate": 24, "life": [0.35, 0.7],
        "size": [0.16, 0.34], "grow": -0.3, "gravity": 0.0,
        "spread": 0.9, "rise": [0.0, 0.2], "blend": "add", "spin": 8.0,
        "colors": ["#ffffff", "#bfe9ff", "#4fa8ff", "#1450b8"],
        "shape": "spark", "radius": 0.8,
    },
    # ------------------------------------------------------------ the crypt
    # A themed set.  Each one names a shape drawn in the particle atlas
    # (static/js/engine/particles.js); sizes are in studs against a head 1.2
    # wide, so anything readable as an object sits between 0.3 and 0.6 --
    # smaller and the face on a lantern is mush, larger and it wears the
    # player rather than the other way round.
    #
    # ``orbit`` circles the crown instead of drifting off it, which is what
    # keeps a heavy shape like a skull reading as a companion rather than as
    # debris.  ``upright`` stops the iconic ones spawning upside down.
    # ``blend: normal`` keeps them solid: additive would bleach a bone to a
    # white smear and lose the silhouette that makes it a bone.
    "floating_bones": {
        # A bone is a thin diagonal shape, so it needs more size than a skull
        # to read as anything at all -- below about 0.4 a drift of them turns
        # into one white smudge.
        "name": "Floating Bones", "rate": 3.2, "life": [2.0, 3.0],
        "size": [0.44, 0.62], "grow": 0.0, "gravity": 0.0,
        "spread": 0.18, "rise": [0.05, 0.22], "blend": "normal", "spin": 1.1,
        "colors": ["#fffaf0", "#efe4cf", "#cdbfa5", "#9a8c74"],
        "shape": "bone", "radius": 0.82, "orbit": 0.55,
    },
    "flying_skulls": {
        "name": "Flying Skulls", "rate": 3.0, "life": [1.6, 2.4],
        "size": [0.40, 0.56], "grow": 0.0, "gravity": 0.0,
        "spread": 0.2, "rise": [0.08, 0.3], "blend": "normal", "spin": 0.7,
        "colors": ["#ffffff", "#ece7dc", "#b9b2a6", "#6f675c"],
        "shape": "skull", "radius": 0.74, "orbit": 1.6,
        "upright": True, "wobble": 0.7,
    },
    "jack_o_lanterns": {
        "name": "Jack-o'-Lanterns", "rate": 2.6, "life": [1.9, 2.8],
        "size": [0.42, 0.60], "grow": 0.0, "gravity": 0.0,
        "spread": 0.16, "rise": [0.04, 0.2], "blend": "normal", "spin": 0.35,
        "colors": ["#ffe3b0", "#ff9a2e", "#e8631a", "#7f2e06"],
        "shape": "pumpkin", "radius": 0.68, "orbit": 1.0,
        "upright": True, "wobble": 0.35,
    },
    "skeletal_mishap": {
        # The one that does not orbit: a skeleton coming apart over your head
        # and falling off it, which wants scatter, tumble and gravity.
        "name": "Skeletal Mishap", "rate": 7.0, "life": [1.1, 1.9],
        "size": [0.30, 0.52], "grow": -0.03, "gravity": -2.6,
        "spread": 0.85, "rise": [1.0, 1.8], "blend": "normal", "spin": 5.5,
        "colors": ["#ffffff", "#e6ded0", "#a89e8c", "#5d564a"],
        "shapes": ["skull", "bone", "ribcage", "bone"], "radius": 0.3,
    },
    "bat_swarm": {
        "name": "Bat Swarm", "rate": 5.0, "life": [1.4, 2.2],
        "size": [0.40, 0.58], "grow": 0.0, "gravity": 0.0,
        "spread": 0.3, "rise": [0.05, 0.45], "blend": "normal", "spin": 0.9,
        "colors": ["#c9bfe4", "#7d6fa6", "#443a66", "#1d1830"],
        "shape": "bat", "radius": 0.92, "orbit": 2.7,
        "upright": True, "wobble": 0.9,
    },
    "haunted_wisps": {
        "name": "Haunted Wisps", "rate": 3.0, "life": [1.7, 2.6],
        "size": [0.46, 0.68], "grow": -0.04, "gravity": 0.35,
        "spread": 0.42, "rise": [0.45, 0.9], "blend": "add", "spin": 0.35,
        "colors": ["#f2fffb", "#8fecc8", "#2ea98a", "#0b3a31"],
        "shape": "wisp", "radius": 0.66, "upright": True, "wobble": 0.5,
    },
    "cursed_runes": {
        "name": "Cursed Runes", "rate": 4.0, "life": [1.5, 2.3],
        "size": [0.30, 0.46], "grow": 0.0, "gravity": 0.0,
        "spread": 0.2, "rise": [0.05, 0.3], "blend": "add", "spin": 0.3,
        "colors": ["#f6e6ff", "#c78bff", "#7b2fd0", "#340d60"],
        "shape": "rune", "radius": 0.8, "orbit": 1.3,
        "upright": True, "wobble": 0.25,
    },
    "spider_descent": {
        # They have to actually descend: sitting still they piled up on the
        # crown in a heap.  A little lift, then a steady fall, strings them
        # out over the shoulders the way something dropping on a thread does.
        "name": "Spider Descent", "rate": 3.5, "life": [2.2, 3.1],
        "size": [0.38, 0.54], "grow": 0.0, "gravity": -1.35,
        "spread": 0.26, "rise": [0.55, 1.0], "blend": "normal", "spin": 0.35,
        "colors": ["#efe9dc", "#a49b88", "#5c5545", "#221f19"],
        "shape": "spider", "radius": 0.52, "upright": True, "wobble": 0.3,
    },
    "raven_feathers": {
        # Thrown wider and fewer at a time: overlapping feathers read as one
        # ragged lump rather than as feathers.
        "name": "Raven Feathers", "rate": 3.0, "life": [2.4, 3.4],
        "size": [0.40, 0.56], "grow": 0.0, "gravity": -0.45,
        "spread": 0.8, "rise": [0.3, 0.75], "blend": "normal", "spin": 1.5,
        "colors": ["#d3ddf6", "#6b7cae", "#333c63", "#141830"],
        "shape": "feather", "radius": 0.98,
    },
    "candlelight_vigil": {
        "name": "Candlelight Vigil", "rate": 2.6, "life": [2.0, 3.0],
        "size": [0.48, 0.66], "grow": 0.0, "gravity": 0.0,
        "spread": 0.12, "rise": [0.03, 0.16], "blend": "normal", "spin": 0.2,
        "colors": ["#fff6d8", "#ffd77a", "#e0982a", "#7d4f10"],
        "shape": "candle", "radius": 0.8, "orbit": 0.8,
        "upright": True, "wobble": 0.18,
    },
}

# ----------------------------------------------------- Halloween 2026
# The two effects that ship with the Hallowed Harvest crate.  They only roll
# out of that crate (see app/models/crates.py), and they are drawn by shapes
# of their own in the particle atlas: a little sheet ghost, and candy.
UNUSUAL_EFFECTS["phantom_procession"] = {
    # A ring of small ghosts circling the crown, bobbing as they go and
    # fading in and out -- the procession never quite stops.
    "name": "Phantom Procession", "rate": 3.4, "life": [2.0, 2.8],
    "size": [0.42, 0.56], "grow": 0.0, "gravity": 0.0,
    "spread": 0.12, "rise": [0.04, 0.22], "blend": "normal", "spin": 0.25,
    "colors": ["#ffffff", "#e9f4ff", "#c9e2ff", "#9fc4ee"],
    "shape": "ghost", "radius": 0.86, "orbit": 1.25,
    "upright": True, "wobble": 0.6, "event": "halloween",
}
UNUSUAL_EFFECTS["trick_or_treat"] = {
    # A shower of candy corn and wrapped sweets tumbling off the hat: thrown
    # up, spinning, and falling past the shoulders like a burst bag.
    "name": "Trick or Treat", "rate": 7.5, "life": [1.2, 1.9],
    "size": [0.26, 0.40], "grow": 0.0, "gravity": -2.4,
    "spread": 0.70, "rise": [1.1, 1.9], "blend": "normal", "spin": 4.2,
    "colors": ["#ffffff", "#ffe08a", "#ff9a2e", "#ff4fa0"],
    "shapes": ["candycorn", "sweet", "candycorn", "sweet_wrap"], "radius": 0.34,
    "event": "halloween",
}

EFFECT_IDS: List[str] = list(UNUSUAL_EFFECTS.keys())

# Effects that used to ship and no longer do.  Copies already rolled with one
# of these are re-rolled onto a live effect at boot, so nobody is left holding
# a purple hat that renders nothing.  Map each retired id to its replacement.
RETIRED_EFFECTS: Dict[str, str] = {
    "cloud_nine": "frostbite",
}

# ------------------------------------------------------------------- colours
BODY_PALETTE: List[Dict[str, str]] = [
    {"name": "Bright yellow", "hex": "#f5cd30"},
    {"name": "Cool yellow", "hex": "#f3cf9b"},
    {"name": "Brick yellow", "hex": "#d7c59a"},
    {"name": "Nougat", "hex": "#cc8e69"},
    {"name": "Light orange", "hex": "#f0b47b"},
    {"name": "Bright orange", "hex": "#d3592b"},
    {"name": "Bright red", "hex": "#c4281c"},
    {"name": "Really red", "hex": "#ff1b1b"},
    {"name": "Hot pink", "hex": "#ff98dc"},
    {"name": "Carnation pink", "hex": "#ff5f9e"},
    {"name": "Bright violet", "hex": "#6b327c"},
    {"name": "Lilac", "hex": "#a75fd1"},
    {"name": "Bright blue", "hex": "#0d69ac"},
    {"name": "Deep blue", "hex": "#0b3b7a"},
    {"name": "Pastel blue", "hex": "#b4d2e4"},
    {"name": "Sand blue", "hex": "#6c81a5"},
    {"name": "Teal", "hex": "#008f9c"},
    {"name": "Bright green", "hex": "#4b974b"},
    {"name": "Dark green", "hex": "#287f47"},
    {"name": "Lime", "hex": "#a4bd47"},
    {"name": "Earth green", "hex": "#27462d"},
    {"name": "Reddish brown", "hex": "#7c503a"},
    {"name": "Dark brown", "hex": "#40292a"},
    {"name": "White", "hex": "#f2f3f3"},
    {"name": "Light stone", "hex": "#c8cbcd"},
    {"name": "Medium stone", "hex": "#a3a2a5"},
    {"name": "Dark stone", "hex": "#6d6e6c"},
    {"name": "Really black", "hex": "#1b2a35"},
]

# Colours left out of every *random* look: a new bot's avatar and the
# welcome screen's shuffled characters.  They stay in BODY_PALETTE, so anyone
# can still pick them in the avatar editor -- they are just never dealt.
RANDOM_EXCLUDED_COLORS = frozenset({
    "#cc8e69",   # Nougat
    "#287f47",   # Dark green
    "#1b2a35",   # Really black
    "#40292a",   # Dark brown
    "#7c503a",   # Reddish brown
})

# The palette random looks are drawn from.
RANDOM_PALETTE: List[Dict[str, str]] = [
    entry for entry in BODY_PALETTE
    if entry["hex"].lower() not in RANDOM_EXCLUDED_COLORS]

DEFAULT_COLORS: Dict[str, str] = {
    "head": "#f5cd30",
    "torso": "#0d69ac",
    # The hips used to be drawn in the left leg's colour rather than carrying
    # one of their own, so the default matches the legs: a character nobody
    # has recoloured looks exactly as it did.
    "hips": "#a4bd47",
    "left_arm": "#f5cd30",
    "right_arm": "#f5cd30",
    "left_leg": "#a4bd47",
    "right_leg": "#a4bd47",
}

BODY_PARTS = ["head", "torso", "hips", "left_arm", "right_arm",
              "left_leg", "right_leg"]

# Two builds ship: "male" (the broader block build) and "female" (the
# slighter one, which is the build that used to be listed as "Male Thin").
# Both share the head-top hat anchor, the eye height and the hitbox, so every
# cosmetic in the catalogue fits both without a per-type variant and switching
# build never costs an outfit.
BODY_TYPES = ["male", "female"]
BODY_TYPE_LABELS = {"male": "Male", "female": "Female"}
# How the editor draws the picker: two buttons, side by side.
BODY_TYPE_OPTIONS = [
    {"id": "male", "label": "Male", "hint": "Broader build"},
    {"id": "female", "label": "Female", "hint": "Slighter build"},
]
DEFAULT_BODY_TYPE = "male"

# Builds that no longer ship, and what an account holding one becomes.  The
# retired female cut lands on the female build that replaced it, and the
# retired slim male cut lands on "male" -- that build is what the female
# option is drawn from now, so moving those players onto it would have
# changed the character they picked rather than the shape of it.
# ``bootstrap.retire_body_types`` rewrites stored rows on boot and
# ``normalize_body_type`` covers anything read before it runs.
RETIRED_BODY_TYPES = {
    "male_thin": "male",
    "female_thin": "female",
}


def normalize_body_type(value: Any) -> str:
    """Map anything stored or posted onto a build that still ships."""
    key = str(value or "").strip().lower()
    if key in BODY_TYPES:
        return key
    return RETIRED_BODY_TYPES.get(key, DEFAULT_BODY_TYPE)


SLOTS = ["face", "hair", "hat", "shirt", "pants", "belt", "back"]
HOTBAR_SIZE = 5

SLOT_LABELS = {
    "face": "Face", "hair": "Hair", "hat": "Hat", "shirt": "Shirt",
    "pants": "Pants", "belt": "Belt", "back": "Back", "usable": "Usable",
    "crate": "Crate", "key": "Key",
}

# Slots that hold things you own but do not wear: a crate waits to be opened,
# a key waits to open one.  Neither can be equipped, put on the hotbar or
# rolled Unusual.
STASH_SLOTS = ("crate", "key")


def _hat(item_id, name, price, parts, desc, rarity="common", order=0):
    return {"id": item_id, "name": name, "slot": "hat", "price": price,
            "rarity": rarity, "description": desc, "sort_order": order,
            "data": {"parts": parts}}


# --------------------------------------------------------------------- hats
# The hats are modelled rather than stacked out of boxes, so they live in
# their own module with the helpers that build them (app/models/cosmetics.py).
# Every one of them now comes out of a crate rather than off the market shelf
# (see app/models/crates.py).
from .cosmetics import HATS  # noqa: E402

# -------------------------------------------------------------------- faces
# Faces are drawn procedurally onto the texture atlas by the client
# (static/js/engine/textures.js) using this compact shape list.
def _face(item_id, name, price, shapes, desc, order=0, rarity="common"):
    return {"id": item_id, "name": name, "slot": "face", "price": price,
            "rarity": rarity, "description": desc, "sort_order": order,
            "data": {"shapes": shapes}}


FACES: List[Dict[str, Any]] = [
    _face("face_smile", "Smile", 0, [
        {"k": "ellipse", "x": -0.22, "y": -0.16, "w": 0.11, "h": 0.16, "c": "#1a1a1a"},
        {"k": "ellipse", "x": 0.22, "y": -0.16, "w": 0.11, "h": 0.16, "c": "#1a1a1a"},
        {"k": "arc", "x": 0, "y": 0.06, "r": 0.30, "a0": 0.08, "a1": 0.42,
         "w": 0.055, "c": "#1a1a1a"},
    ], "The default. Timeless.", 1),

    _face("face_grin", "Cheeky Grin", 120, [
        {"k": "ellipse", "x": -0.22, "y": -0.16, "w": 0.11, "h": 0.16, "c": "#1a1a1a"},
        {"k": "ellipse", "x": 0.22, "y": -0.16, "w": 0.11, "h": 0.16, "c": "#1a1a1a"},
        {"k": "arc", "x": 0.02, "y": 0.02, "r": 0.34, "a0": 0.05, "a1": 0.45,
         "w": 0.06, "c": "#1a1a1a"},
        {"k": "rect", "x": 0.03, "y": 0.12, "w": 0.30, "h": 0.07, "c": "#ffffff"},
    ], "Up to something. Definitely up to something.", 2),

    _face("face_cool", "Shades", 380, [
        {"k": "rect", "x": 0, "y": -0.16, "w": 0.74, "h": 0.06, "c": "#1a1a1a"},
        {"k": "rect", "x": -0.24, "y": -0.14, "w": 0.28, "h": 0.20, "c": "#12161c"},
        {"k": "rect", "x": 0.24, "y": -0.14, "w": 0.28, "h": 0.20, "c": "#12161c"},
        {"k": "rect", "x": -0.30, "y": -0.19, "w": 0.10, "h": 0.04, "c": "#7fd8ff"},
        {"k": "arc", "x": 0, "y": 0.10, "r": 0.24, "a0": 0.10, "a1": 0.40,
         "w": 0.05, "c": "#1a1a1a"},
    ], "Instantly 40% more mysterious.", 3, "uncommon"),

    _face("face_stoic", "Stoic", 90, [
        {"k": "rect", "x": -0.22, "y": -0.16, "w": 0.13, "h": 0.15, "c": "#1a1a1a"},
        {"k": "rect", "x": 0.22, "y": -0.16, "w": 0.13, "h": 0.15, "c": "#1a1a1a"},
        {"k": "rect", "x": 0, "y": 0.16, "w": 0.34, "h": 0.05, "c": "#1a1a1a"},
    ], "Has seen things. Says nothing.", 4),

    _face("face_wink", "Wink", 160, [
        {"k": "ellipse", "x": -0.22, "y": -0.16, "w": 0.11, "h": 0.16, "c": "#1a1a1a"},
        {"k": "arc", "x": 0.22, "y": -0.10, "r": 0.13, "a0": 0.55, "a1": 0.95,
         "w": 0.05, "c": "#1a1a1a"},
        {"k": "arc", "x": 0, "y": 0.06, "r": 0.30, "a0": 0.08, "a1": 0.42,
         "w": 0.055, "c": "#1a1a1a"},
    ], ";)", 5),

    _face("face_shock", "Shock", 200, [
        {"k": "ellipse", "x": -0.23, "y": -0.18, "w": 0.15, "h": 0.20, "c": "#ffffff"},
        {"k": "ellipse", "x": -0.23, "y": -0.16, "w": 0.08, "h": 0.10, "c": "#1a1a1a"},
        {"k": "ellipse", "x": 0.23, "y": -0.18, "w": 0.15, "h": 0.20, "c": "#ffffff"},
        {"k": "ellipse", "x": 0.23, "y": -0.16, "w": 0.08, "h": 0.10, "c": "#1a1a1a"},
        {"k": "ellipse", "x": 0, "y": 0.16, "w": 0.20, "h": 0.24, "c": "#1a1a1a"},
    ], "Just watched the cart reach the final checkpoint.", 6),

    _face("face_angry", "Furious", 240, [
        {"k": "rect", "x": -0.22, "y": -0.22, "w": 0.24, "h": 0.06, "c": "#1a1a1a",
         "rot": 0.35},
        {"k": "rect", "x": 0.22, "y": -0.22, "w": 0.24, "h": 0.06, "c": "#1a1a1a",
         "rot": -0.35},
        {"k": "ellipse", "x": -0.22, "y": -0.08, "w": 0.11, "h": 0.13, "c": "#1a1a1a"},
        {"k": "ellipse", "x": 0.22, "y": -0.08, "w": 0.11, "h": 0.13, "c": "#1a1a1a"},
        {"k": "arc", "x": 0, "y": 0.32, "r": 0.26, "a0": 0.58, "a1": 0.92,
         "w": 0.06, "c": "#1a1a1a"},
    ], "Someone captured the flag again.", 7),

    _face("face_derp", "Derp", 140, [
        {"k": "ellipse", "x": -0.24, "y": -0.19, "w": 0.17, "h": 0.19, "c": "#ffffff"},
        {"k": "ellipse", "x": -0.20, "y": -0.15, "w": 0.07, "h": 0.09, "c": "#1a1a1a"},
        {"k": "ellipse", "x": 0.24, "y": -0.16, "w": 0.15, "h": 0.17, "c": "#ffffff"},
        {"k": "ellipse", "x": 0.28, "y": -0.20, "w": 0.06, "h": 0.08, "c": "#1a1a1a"},
        {"k": "arc", "x": 0.02, "y": 0.08, "r": 0.24, "a0": 0.06, "a1": 0.40,
         "w": 0.05, "c": "#1a1a1a"},
        {"k": "ellipse", "x": 0.16, "y": 0.24, "w": 0.12, "h": 0.10, "c": "#e26b6b"},
    ], "Nobody is home and that is fine.", 8),

    _face("face_robot", "Circuit Face", 520, [
        {"k": "rect", "x": -0.22, "y": -0.14, "w": 0.22, "h": 0.14, "c": "#19f0d8"},
        {"k": "rect", "x": 0.22, "y": -0.14, "w": 0.22, "h": 0.14, "c": "#19f0d8"},
        {"k": "rect", "x": 0, "y": 0.16, "w": 0.46, "h": 0.12, "c": "#12161c"},
        {"k": "rect", "x": -0.14, "y": 0.16, "w": 0.05, "h": 0.12, "c": "#19f0d8"},
        {"k": "rect", "x": 0, "y": 0.16, "w": 0.05, "h": 0.12, "c": "#19f0d8"},
        {"k": "rect", "x": 0.14, "y": 0.16, "w": 0.05, "h": 0.12, "c": "#19f0d8"},
    ], "BEEP. Acquiring targets.", 9, "uncommon"),

    _face("face_cat", "Cat Face", 300, [
        {"k": "ellipse", "x": -0.22, "y": -0.14, "w": 0.09, "h": 0.20, "c": "#1a1a1a"},
        {"k": "ellipse", "x": 0.22, "y": -0.14, "w": 0.09, "h": 0.20, "c": "#1a1a1a"},
        {"k": "rect", "x": 0, "y": 0.10, "w": 0.10, "h": 0.06, "c": "#e08aa8"},
        {"k": "arc", "x": -0.10, "y": 0.08, "r": 0.14, "a0": 0.0, "a1": 0.5,
         "w": 0.045, "c": "#1a1a1a"},
        {"k": "arc", "x": 0.10, "y": 0.08, "r": 0.14, "a0": 0.0, "a1": 0.5,
         "w": 0.045, "c": "#1a1a1a"},
        {"k": "rect", "x": -0.36, "y": 0.06, "w": 0.24, "h": 0.03, "c": "#1a1a1a"},
        {"k": "rect", "x": 0.36, "y": 0.06, "w": 0.24, "h": 0.03, "c": "#1a1a1a"},
    ], ":3", 10, "uncommon"),
]

# ------------------------------------------------------------------ clothing
def _shirt(item_id, name, price, data, desc, order=0, rarity="common"):
    return {"id": item_id, "name": name, "slot": "shirt", "price": price,
            "rarity": rarity, "description": desc, "sort_order": order,
            "data": data}


SHIRTS: List[Dict[str, Any]] = [
    _shirt("shirt_none", "No Shirt", 0, {"torso": None, "arms": None},
           "Just you and your natural block finish.", 0),
    _shirt("shirt_tee_red", "Red Tee", 120,
           {"torso": "#c4281c", "arms": "#c4281c", "sleeves": 0.45,
            "decal": "logo_block"},
           "Standard issue starter shirt.", 1),
    _shirt("shirt_hoodie_blue", "Blue Hoodie", 260,
           {"torso": "#2f5fa8", "arms": "#2f5fa8", "hood": True,
            "stripe": "#e8e8e8", "weave": "canvas"},
           "Comfortable. Slightly too warm for the desert map.", 2),
    _shirt("shirt_tux", "Tuxedo Jacket", 640,
           {"torso": "#1b2a35", "arms": "#1b2a35", "decal": "tux"},
           "Black tie only.", 3, "uncommon"),
    _shirt("shirt_hivis", "Hi-Vis Vest", 220,
           {"torso": "#e9f21a", "arms": "#d7c59a", "sleeves": 0.0,
            "stripe": "#c8cbcd", "weave": "hivis"},
           "Cannot be missed, even at render distance.", 4),
    _shirt("shirt_stripes", "Referee Stripes", 300,
           {"torso": "#f2f3f3", "arms": "#f2f3f3", "stripes": 6,
            "stripe": "#1b2a35"},
           "You are the law now.", 5),
    _shirt("shirt_burger", "Burger Crew Uniform", 350,
           {"torso": "#e2621b", "arms": "#f2f3f3", "sleeves": 0.4,
            "decal": "burger"},
           "Employee of the month, seven months running.", 6, "uncommon"),
    _shirt("shirt_soldier", "Field Jacket", 480,
           {"torso": "#4a5a34", "arms": "#4a5a34", "decal": "chevron",
            "stripe": "#2f3a20"},
           "Standard issue for the Fortress campaigns.", 7, "uncommon"),
    _shirt("shirt_hawaiian", "Hawaiian Shirt", 400,
           {"torso": "#19a7c8", "arms": "#19a7c8", "decal": "flowers"},
           "Permanently on holiday.", 8),
    _shirt("shirt_void", "Void Robes", 1100,
           {"torso": "#2a0a4a", "arms": "#3d1266", "decal": "sigil",
            "stripe": "#8b3fd6"},
           "Woven from something that should not be woven.", 9, "rare"),
]


def _pants(item_id, name, price, data, desc, order=0, rarity="common"):
    return {"id": item_id, "name": name, "slot": "pants", "price": price,
            "rarity": rarity, "description": desc, "sort_order": order,
            "data": data}


PANTS: List[Dict[str, Any]] = [
    _pants("pants_none", "No Pants", 0, {"legs": None},
           "Bold. Legally questionable.", 0),
    _pants("pants_jeans", "Blue Jeans", 140,
           {"legs": "#3d5a80", "cuff": "#2c4160", "weave": "denim"},
           "They go with everything.", 1),
    _pants("pants_cargo", "Cargo Trousers", 220, {"legs": "#6b6a4a", "pocket": True},
           "Fourteen pockets. All empty.", 2),
    _pants("pants_shorts", "Summer Shorts", 160,
           {"legs": "#d3592b", "length": 0.55, "skin": "#d7c59a"},
           "Built for the beach map.", 3),
    _pants("pants_tux", "Tuxedo Trousers", 560, {"legs": "#1b2a35", "stripe": "#f2f3f3"},
           "Matches the jacket, obviously.", 4, "uncommon"),
    _pants("pants_camo", "Camo Trousers", 380,
           {"legs": "#4a5a34", "weave": "camo"},
           "You literally cannot see these.", 5, "uncommon"),
    _pants("pants_neon", "Neon Runners", 700, {"legs": "#12161c", "stripe": "#19f0d8",
                                               "glow": True},
           "Leaves a faint trail in dark rooms.", 6, "rare"),
]

# ---------------------------------------------------------------------- back
# Modelled alongside the hats, in app/models/cosmetics.py.
from .cosmetics import BACK_ITEMS  # noqa: E402

# ------------------------------------------------------------------- usables
def _usable(item_id, name, price, stats, parts, desc, order=0,
            rarity="common", default=False):
    return {"id": item_id, "name": name, "slot": "usable", "price": price,
            "rarity": rarity, "description": desc, "sort_order": order,
            "is_default": default,
            "data": {"stats": stats, "parts": parts}}


USABLES: List[Dict[str, Any]] = [
    _usable("use_pistol", "Basic Pistol", 0, {
        "kind": "hitscan", "damage": 24, "headshot": 2.0, "rpm": 320,
        "mag": 12, "reload": 1.4, "spread": 0.9, "pellets": 1, "range": 260,
        "auto": False, "sound": "pistol", "recoil": 1.1, "reserve": 96,
    }, [
        {"t": "box", "p": [0, 0, 0.35], "s": [0.22, 0.28, 1.0], "c": "#31363c"},
        {"t": "box", "p": [0, -0.32, -0.05], "s": [0.2, 0.55, 0.34], "c": "#22262b"},
        {"t": "box", "p": [0, 0.14, 0.62], "s": [0.1, 0.1, 0.4], "c": "#6d6e6c"},
    ], "Reliable, unglamorous, always in your bag.", 1, "common", True),

    _usable("use_shotgun", "Basic Shotgun", 0, {
        "kind": "hitscan", "damage": 9, "headshot": 1.5, "rpm": 72,
        "mag": 6, "reload": 2.4, "spread": 5.4, "pellets": 8, "range": 70,
        "auto": False, "sound": "shotgun", "recoil": 3.4, "reserve": 42,
        "falloff": 0.55,
    }, [
        {"t": "box", "p": [0, 0, 0.55], "s": [0.26, 0.3, 1.7], "c": "#5a3a22"},
        {"t": "cyl", "p": [0.07, 0.06, 0.95], "s": [0.14, 1.6, 0.14],
         "c": "#31363c", "r": [1.5708, 0, 0]},
        {"t": "cyl", "p": [-0.07, 0.06, 0.95], "s": [0.14, 1.6, 0.14],
         "c": "#31363c", "r": [1.5708, 0, 0]},
        {"t": "box", "p": [0, -0.3, -0.25], "s": [0.24, 0.5, 0.5], "c": "#4a2f18"},
    ], "Two barrels of extremely direct conversation.", 2, "common", True),

    _usable("use_stick", "Basic Stick", 0, {
        "kind": "melee", "damage": 30, "headshot": 1.4, "rpm": 96,
        "range": 9.5, "arc": 0.55, "sound": "swing", "knockback": 12,
    }, [
        {"t": "cyl", "p": [0, 0, 0.7], "s": [0.16, 1.9, 0.16], "c": "#7c503a",
         "r": [1.5708, 0, 0]},
        {"t": "box", "p": [0.05, 0.06, 1.35], "s": [0.14, 0.14, 0.4], "c": "#6b4229",
         "r": [0, 0.3, 0]},
    ], "A stick. It is a good stick.", 3, "common", True),

    _usable("use_smg", "Rapid SMG", 900, {
        "kind": "hitscan", "damage": 13, "headshot": 1.8, "rpm": 780,
        "mag": 30, "reload": 1.9, "spread": 2.6, "pellets": 1, "range": 180,
        "auto": True, "sound": "smg", "recoil": 0.7, "reserve": 180,
    }, [
        {"t": "box", "p": [0, 0, 0.5], "s": [0.24, 0.3, 1.3], "c": "#22262b"},
        {"t": "box", "p": [0, -0.34, 0.1], "s": [0.2, 0.7, 0.3], "c": "#31363c"},
        {"t": "box", "p": [0, -0.28, -0.15], "s": [0.18, 0.5, 0.3], "c": "#1b2a35"},
        {"t": "cyl", "p": [0, 0.05, 1.15], "s": [0.11, 0.5, 0.11], "c": "#6d6e6c",
         "r": [1.5708, 0, 0]},
    ], "Empties a magazine faster than you can regret it.", 4, "uncommon"),

    _usable("use_rifle", "Ranger Rifle", 1200, {
        "kind": "hitscan", "damage": 42, "headshot": 2.2, "rpm": 150,
        "mag": 10, "reload": 2.2, "spread": 0.35, "pellets": 1, "range": 400,
        "auto": False, "sound": "rifle", "recoil": 2.0, "reserve": 80,
    }, [
        {"t": "box", "p": [0, 0, 0.7], "s": [0.22, 0.28, 2.1], "c": "#3a2c20"},
        {"t": "cyl", "p": [0, 0.06, 1.6], "s": [0.1, 1.0, 0.1], "c": "#31363c",
         "r": [1.5708, 0, 0]},
        {"t": "box", "p": [0, 0.26, 0.55], "s": [0.14, 0.16, 0.6], "c": "#22262b"},
        {"t": "box", "p": [0, -0.3, -0.1], "s": [0.2, 0.5, 0.4], "c": "#4a3320"},
    ], "Accurate to a fault. Yours especially.", 5, "uncommon"),

    _usable("use_sniper", "Longshot", 1800, {
        "kind": "hitscan", "damage": 92, "headshot": 2.5, "rpm": 46,
        "mag": 5, "reload": 3.0, "spread": 0.05, "pellets": 1, "range": 900,
        "auto": False, "sound": "sniper", "recoil": 4.5, "reserve": 40,
        "scope": 4.0, "charge": 0.0,
    }, [
        {"t": "box", "p": [0, 0, 0.9], "s": [0.22, 0.3, 2.6], "c": "#1f2a20"},
        {"t": "cyl", "p": [0, 0.06, 2.2], "s": [0.1, 1.4, 0.1], "c": "#22262b",
         "r": [1.5708, 0, 0]},
        {"t": "cyl", "p": [0, 0.32, 0.8], "s": [0.16, 0.9, 0.16], "c": "#12161c",
         "r": [1.5708, 0, 0]},
        {"t": "box", "p": [0, -0.32, -0.15], "s": [0.2, 0.55, 0.5], "c": "#2a3524"},
    ], "One shot. Then a long, thoughtful pause.", 6, "rare"),

    # Damage is 25% below where a direct hit used to land.  That budget buys
    # the rocket jump: the launcher hurts its owner and shoves them, so the
    # trade is height for health rather than a free boost.
    _usable("use_rocket", "Blast Launcher", 2500, {
        "kind": "projectile", "damage": 66, "splash": 9.5, "splash_damage": 47,
        "rpm": 55, "mag": 4, "reload": 3.2, "speed": 78, "range": 500,
        "auto": False, "sound": "rocket", "recoil": 5.0, "reserve": 24,
        "self_damage": 0.42, "knockback": 34, "self_knockback": 1.65,
    }, [
        {"t": "cyl", "p": [0, 0.05, 0.75], "s": [0.42, 2.6, 0.42], "c": "#2f6b3a",
         "r": [1.5708, 0, 0]},
        {"t": "box", "p": [0, -0.3, 0.05], "s": [0.2, 0.5, 0.4], "c": "#22262b"},
        {"t": "box", "p": [0, 0.34, 0.5], "s": [0.14, 0.2, 0.7], "c": "#1b2a35"},
        {"t": "cyl", "p": [0, 0.05, 2.0], "s": [0.5, 0.3, 0.5], "c": "#22262b",
         "r": [1.5708, 0, 0]},
    ], "Hurts you too. Point it at the floor and go somewhere.", 7, "rare"),

    _usable("use_sword", "Blockblade", 1000, {
        "kind": "melee", "damage": 55, "headshot": 1.3, "rpm": 78,
        "range": 11.0, "arc": 0.7, "sound": "sword", "knockback": 16,
    }, [
        {"t": "box", "p": [0, 0, 1.3], "s": [0.16, 0.4, 2.4], "c": "#d8dde2",
         "mat": "metal"},
        {"t": "box", "p": [0, 0, 0.1], "s": [0.7, 0.18, 0.2], "c": "#f5c518",
         "mat": "metal"},
        {"t": "cyl", "p": [0, 0, -0.25], "s": [0.18, 0.6, 0.18], "c": "#4a2f18",
         "r": [1.5708, 0, 0]},
    ], "Sharpened on the edge of a baseplate.", 8, "uncommon"),

    _usable("use_medkit", "Field Medkit", 700, {
        "kind": "support", "heal": 34, "rpm": 40, "range": 14.0,
        "sound": "heal", "self_heal": 24, "mag": 4, "reload": 4.0, "reserve": 8,
    }, [
        {"t": "box", "p": [0, 0, 0.3], "s": [0.7, 0.5, 0.9], "c": "#f2f3f3"},
        {"t": "box", "p": [0, 0.26, 0.3], "s": [0.24, 0.06, 0.6], "c": "#c4281c"},
        {"t": "box", "p": [0, 0.26, 0.3], "s": [0.6, 0.06, 0.24], "c": "#c4281c"},
        {"t": "box", "p": [0, 0.3, 0.0], "s": [0.3, 0.14, 0.1], "c": "#a3a2a5"},
    ], "Aim at a friend. Press fire. Be thanked.", 9, "uncommon"),

    _usable("use_buildhammer", "Tycoon Hammer", 450, {
        "kind": "melee", "damage": 22, "headshot": 1.2, "rpm": 110,
        "range": 8.5, "arc": 0.5, "sound": "swing", "knockback": 8,
        "build_bonus": 0.05,
    }, [
        {"t": "cyl", "p": [0, 0, 0.55], "s": [0.14, 1.5, 0.14], "c": "#6b4a2a",
         "r": [1.5708, 0, 0]},
        {"t": "box", "p": [0, 0.05, 1.25], "s": [0.7, 0.34, 0.34], "c": "#8f9296",
         "mat": "metal"},
    ], "Grants a small bonus to Burger Tycoon income while held.", 10, "uncommon"),
]



# -------------------------------------------------------------------- hair
# Hair is the one cosmetic that has to fit the skull rather than sit on top of
# it, and the two builds have different heads.  So a style is authored in HEAD
# UNITS: 1.0 is the head's own width, height and depth, the origin is the
# middle of the head, +Z is the face and +Y is up.  The renderer scales it to
# whichever head is wearing it, so one style fits both builds with no per-type
# variant -- the same bargain every other cosmetic in here makes.
#
# Keep anything that is not a fringe above y 0.22: that is where the eyes are
# printed, and hair over them reads as a bug rather than as a style.
# The styles are modelled -- layered locks, tufts, ties and partings -- in
# app/models/cosmetics.py, next to the hats.
from .cosmetics import HAIRS  # noqa: E402

# ------------------------------------------------------------------- belts
# A belt is a band round the waist with an optional buckle, so it is described
# by colours and a width rather than by parts: the renderer sizes it from
# whichever build is wearing it, the same way a shirt or a pair of trousers is
# sized, which is what makes one belt fit both builds.  It is drawn outside
# the hips, so it sits over the trousers rather than instead of them.
def _belt(item_id, name, price, data, desc, order=0, rarity="common"):
    return {"id": item_id, "name": name, "slot": "belt", "price": price,
            "rarity": rarity, "description": desc, "sort_order": order,
            "data": data}


BELTS: List[Dict[str, Any]] = [
    _belt("belt_rope", "Rope Belt", 90, {"band": "#c2a06a", "width": 0.15},
          "Knotted once and never undone.", 1),
    _belt("belt_leather", "Leather Belt", 150,
          {"band": "#5a3a22", "buckle": "#c9a227", "metal": True,
           "weave": "leather"},
          "Honest leather, honest brass.", 2),
    _belt("belt_sash", "Red Sash", 180, {"band": "#c4281c", "width": 0.30},
          "No buckle. Just swagger.", 3),
    _belt("belt_utility", "Utility Belt", 320,
          {"band": "#3a3a3a", "buckle": "#9aa0a6", "metal": True, "pouch": True,
           "weave": "leather"},
          "Two pouches, both full of nothing useful.", 4, "uncommon"),
    _belt("belt_neon", "Neon Belt", 650,
          {"band": "#12161c", "buckle": "#19f0d8", "width": 0.17, "glow": True},
          "The buckle keeps glowing after the lights go out.", 5, "rare"),
    _belt("belt_champion", "Champion's Belt", 1400,
          {"band": "#1b2a35", "buckle": "#f5c518", "width": 0.34, "metal": True,
           "weave": "leather"},
          "Won it fair. Wears it everywhere.", 6, "rare"),
]

# -------------------------------------------------- crates, keys and events
# Crates and keys are items like any other -- owned copies, serials, a price,
# a model -- in two slots of their own that nothing can be worn in.  Which key
# opens which crate, and what is inside, is app/models/crates.py.
from .cosmetics import CRATES, KEYS  # noqa: E402

# Every event Blockhaven has run, 2022 to now -- New Year, St. Patrick's Day,
# Easter, the Fourth of July, Halloween and Christmas -- each brought a crate,
# a key, cosmetics, weapons and held items (app/models/holidays/).  The
# Hallowed Harvest's original set (cosmetics.HALLOWEEN_*) comes in with the
# 2026 Halloween event.
from . import holidays  # noqa: E402

EVENT_ITEMS: List[Dict[str, Any]] = holidays.all_items()
_EVENT_IDS = {it["id"] for it in EVENT_ITEMS}
UNUSUAL_EFFECTS.update(holidays.all_effects())
EFFECT_IDS = list(UNUSUAL_EFFECTS.keys())

ALL_ITEMS: List[Dict[str, Any]] = (
    [k for k in KEYS if k["id"] not in _EVENT_IDS]
    + [c for c in CRATES if c["id"] not in _EVENT_IDS]
    + HATS + FACES + HAIRS + SHIRTS + PANTS + BELTS + BACK_ITEMS + USABLES
    + EVENT_ITEMS)


def _normalise_parts(items: List[Dict[str, Any]]) -> None:
    """Rename the authoring keys onto the short keys the renderer reads.

    The part dicts above are written for humans (``mat``/``alpha``); the
    instance buffer packs ``m``/``a``.  Doing the rename once here means a
    metal crown is actually metal everywhere -- site thumbnails, the avatar
    preview and the game -- instead of silently falling back to plastic.
    """
    renames = (("mat", "m"), ("alpha", "a"), ("studs", "st"), ("wrap", "dw"))
    for item in items:
        data = item.get("data") or {}
        # a weapon also carries the model of what it fires and what it places
        for key in ("parts", "proj", "deploy"):
            for piece in data.get(key) or []:
                for source, target in renames:
                    if source in piece and target not in piece:
                        piece[target] = piece.pop(source)


_normalise_parts(ALL_ITEMS)

DEFAULT_EQUIPPED = {
    "face": "face_smile",
    "hat": "",
    "shirt": "shirt_none",
    "pants": "pants_none",
    "back": "",
}

# Items every new account is granted for free.
STARTER_ITEMS = ["use_pistol", "use_shotgun", "use_stick", "face_smile",
                 "shirt_none", "pants_none"]

DEFAULT_HOTBAR = ["use_pistol", "use_shotgun", "use_stick", "", ""]

ITEMS_BY_ID: Dict[str, Dict[str, Any]] = {it["id"]: it for it in ALL_ITEMS}


def get(item_id: str):
    return ITEMS_BY_ID.get(item_id)


def by_slot(slot: str) -> List[Dict[str, Any]]:
    return [it for it in ALL_ITEMS if it["slot"] == slot]
