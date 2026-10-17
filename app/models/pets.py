"""Pets: a little companion who follows her owner about.

A pet is an item like any other -- an owned copy in the ``inventory`` table,
bought on the market's Pets shelf -- and so is everything she wears.  What
makes her *yours* lives here, keyed on that inventory row:

  * her name, her six colours and her persona tags (``pets`` table)
  * what she is wearing, one pet cosmetic per pet slot
  * which of your pets is the active one, following you about
    (``avatars.pet``)

The active pet rides in the avatar descriptor (avatars.descriptor), so the
profile preview, the thumbnails and every game host get her the same way
they get a hat.  How she looks is static/js/engine/pet.js; how she behaves
in a world is static/js/game/pets.js, driven by the persona tags below.

Pet cosmetics are authored round anchors on the pet rather than on the
avatar (see ANCHORS), and every species shares the same head, the same neck
and the same chest, so one hat fits all five.
"""
from __future__ import annotations

import json
import math
import re
import time
from typing import Any, Dict, List, Optional

from .. import db, security
from .modeling import mirror_x, part, place, ring_of

PI = math.pi

# ------------------------------------------------------------------ species
# Colours match static/js/engine/pet.js (SPECIES), which fills any the
# server leaves out.
COLOR_KEYS = ["hair", "outfit", "accent", "eyes", "legs", "skin"]
COLOR_LABELS = {"hair": "Hair", "outfit": "Outfit", "accent": "Accent",
                "eyes": "Eyes", "legs": "Legwear", "skin": "Skin"}

SPECIES: Dict[str, Dict[str, Any]] = {
    "fern": {
        "id": "fern", "item_id": "pet_fern", "name": "Fern", "price": 1500,
        "rarity": "uncommon", "order": 1,
        "tagline": "The original. A sprout of a girl with a sprout on her head.",
        "description": ("Fern is a cheerful little sprite in a green dress, with a heavy bob, "
                        "a blunt fringe and a sprout on her crown that perks up when she is "
                        "happy and wilts when she is not. She skips when she is in a good mood."),
        "signature": "Her sprout perks up and wilts with her mood; she skips when happy.",
        "colors": {"hair": "#3f9a3a", "outfit": "#2c7a33", "accent": "#8fd16a",
                   "eyes": "#43c25a", "legs": "#1b1f1d", "skin": "#ecc3a6"},
        "tags": ["cheerful", "loyal", "curious"],
    },
    "ember": {
        "id": "ember", "item_id": "pet_ember", "name": "Ember", "price": 2500,
        "rarity": "rare", "order": 2,
        "tagline": "Twin tails that burn brighter the more fired up she gets.",
        "description": ("Ember is all go: a hoodie, sneakers, a fang in her grin and two twin "
                        "tails whose tips smoulder like coals -- and flare up when she is excited "
                        "or cross. She sneezes sparks."),
        "signature": "Her twin tails flare when she is excited and smoulder when she is sad.",
        "colors": {"hair": "#ff5a24", "outfit": "#3a2a2e", "accent": "#ffc23a",
                   "eyes": "#ffae2a", "legs": "#24191c", "skin": "#f2c7a2"},
        "tags": ["feisty", "energetic", "showoff"],
    },
    "luna": {
        "id": "luna", "item_id": "pet_luna", "name": "Luna", "price": 3500,
        "rarity": "epic", "order": 3,
        "tagline": "A sleepy moon witch who floats rather than walks.",
        "description": ("Luna never quite wakes up. She drifts along a hand's breadth off the "
                        "ground in a starry capelet and striped stockings, her hair down to her "
                        "knees, and the crescent in her hair glows when she dreams."),
        "signature": "She floats instead of walking; her crescent glows when she is content.",
        "colors": {"hair": "#3b3f8f", "outfit": "#252a5c", "accent": "#c9b6ff",
                   "eyes": "#9d8cff", "legs": "#e9e4ff", "skin": "#f3d6c8"},
        "tags": ["sleepy", "dreamy", "shy"],
    },
    "mochi": {
        "id": "mochi", "item_id": "pet_mochi", "name": "Mochi", "price": 2500,
        "rarity": "rare", "order": 4,
        "tagline": "A bunny-hood girl who hops everywhere, ears and all.",
        "description": ("Mochi wears a hood with two long ears that perk up, droop, twitch and "
                        "flop over with whatever she is feeling. She hops instead of walking, "
                        "has a pompom tail and a twitchy little nose."),
        "signature": "Her ears perk, droop and twitch with her mood; she hops everywhere.",
        "colors": {"hair": "#ff9ec0", "outfit": "#ffd3e2", "accent": "#fff6ee",
                   "eyes": "#e2507e", "legs": "#ffffff", "skin": "#f6d2bd"},
        "tags": ["playful", "clingy", "cheerful"],
    },
    "pixel": {
        "id": "pixel", "item_id": "pet_pixel", "name": "Pixel", "price": 3500,
        "rarity": "epic", "order": 5,
        "tagline": "A techno girl with LED eyes and boots with jets in the heels.",
        "description": ("Pixel's eyes are a pair of LED panels, her headphones never come off "
                        "and her antenna lights up in the colour of her mood. Her boots have "
                        "jets in the heels for catching up, and she scans anything new."),
        "signature": "LED eyes, a mood-light antenna, and jet boots for catching up.",
        "colors": {"hair": "#2bb3b1", "outfit": "#2a3140", "accent": "#4ff2ff",
                   "eyes": "#4ff2ff", "legs": "#39414f", "skin": "#efd0b8"},
        "tags": ["curious", "brave", "chatty"],
    },
}
SPECIES_ORDER = ["fern", "ember", "luna", "mochi", "pixel"]
SPECIES_BY_ITEM = {s["item_id"]: s for s in SPECIES.values()}

# ------------------------------------------------------------- persona tags
# What each one does to her in a world is static/js/game/pets.js; this is
# the name and the line on the tooltip (static/js/engine/pet.js has the same).
TAGS: Dict[str, Dict[str, str]] = {
    "cheerful": {"name": "Cheerful", "blurb": "Bounces when you win and greets everyone she meets."},
    "shy": {"name": "Shy", "blurb": "Hides behind you when strangers come close, and blushes a lot."},
    "curious": {"name": "Curious", "blurb": "Wanders off to inspect things and peers at other players."},
    "loyal": {"name": "Loyal", "blurb": "Sticks to your heel, copies your moves and waits for you."},
    "sleepy": {"name": "Sleepy", "blurb": "Yawns, sits down and dozes off whenever you stand still."},
    "energetic": {"name": "Energetic", "blurb": "Races ahead, hops about and never quite stops fidgeting."},
    "feisty": {"name": "Feisty", "blurb": "Stomps when you get hurt and shadowboxes in a fight."},
    "dreamy": {"name": "Dreamy", "blurb": "Gazes at the sky, hums little tunes and twirls."},
    "playful": {"name": "Playful", "blurb": "Circles you, chases butterflies and pounces on your landings."},
    "brave": {"name": "Brave", "blurb": "Steps in front of you when it gets dangerous, cheers your wins."},
    "clingy": {"name": "Clingy", "blurb": "Never more than a step away. Pouts when she is left behind."},
    "showoff": {"name": "Show-off", "blurb": "Strikes poses, waves at everyone and twirls for attention."},
    "chatty": {"name": "Chatty", "blurb": "Always has something to say: little bubbles over her head."},
    "clumsy": {"name": "Clumsy", "blurb": "Trips over her own feet now and then, and dusts herself off."},
}
TAG_ORDER = ["cheerful", "shy", "curious", "loyal", "sleepy", "energetic", "feisty",
             "dreamy", "playful", "brave", "clingy", "showoff", "chatty", "clumsy"]
MAX_TAGS = 3
NAME_MAX = 16

# ---------------------------------------------------------------- the slots
PET_SLOT = "pet"
COSMETIC_SLOTS = ["pet_hat", "pet_face", "pet_neck", "pet_pin", "pet_top", "pet_back"]
SLOT_LABELS = {"pet": "Pet", "pet_hat": "Pet Hat", "pet_face": "Pet Face",
               "pet_neck": "Pet Neckwear", "pet_pin": "Pet Pin", "pet_top": "Pet Outfit",
               "pet_back": "Pet Back"}
# the short labels the pet editor and the shelf use
SHELF_LABELS = {"pet_hat": "Hats", "pet_face": "Glasses & Face", "pet_neck": "Neckwear",
                "pet_pin": "Pins", "pet_top": "Outfits", "pet_back": "Back"}
ALL_SLOTS = [PET_SLOT] + COSMETIC_SLOTS

# Where each slot's parts are measured from, on every species (pet.js wear()):
#   hat   the crown of the hair, centred over the head  (+Z is her front)
#   face  the eye line, on the face plate, between the eyes
#   neck  the collar line, round the neck
#   pin   the front of the chest, over her right side
#   back  the middle of her back, between the shoulder blades (-Z is away)
# The hair's crown sits back a little from the head's centre, so hats are
# authored about z -0.08.
HAT_Z = -0.08

GOLD = "#e8b93a"
WHITE = "#f7f5f0"


def _pet_item(item_id: str, name: str, slot: str, price: int, rarity: str, desc: str,
              data: Dict[str, Any], order: int) -> Dict[str, Any]:
    return {"id": item_id, "name": name, "slot": slot, "price": price, "rarity": rarity,
            "description": desc, "sort_order": order, "data": data, "pet": True}


# --------------------------------------------------------------- pet hats
def _hats() -> List[Dict[str, Any]]:
    z = HAT_Z
    beret = [
        part("sph", [0.07, 0.1, z], [1.04, 0.26, 1.0], "#c8283c", [0, 0, -0.16], decal="felt",
             wrap=True),
        part("cyl", [0.05, 0.035, z], [0.84, 0.06, 0.8], "#a51f31", [0, 0, -0.16]),
        part("cyl", [0.05, 0.255, z], [0.05, 0.11, 0.05], "#a51f31", [0, 0, -0.16]),
    ]
    straw = [
        part("cyl", [0, 0.02, z], [1.56, 0.045, 1.5], "#e7c46a", decal="straw", wrap=True),
        part("cyl", [0, 0.17, z], [0.8, 0.3, 0.76], "#e7c46a", decal="straw", wrap=True),
        part("cyl", [0, 0.08, z], [0.82, 0.09, 0.78], "#e0496a"),
        place("bowloop", [0.38, 0.09, z + 0.12], [0.26, 0.26, 0.24], "#e0496a",
              anchor=[0, 0, 0], r=[0, -0.6, 0.3]),
        place("bowloop", [0.38, 0.09, z + 0.12], [0.26, 0.26, 0.24], "#e0496a",
              anchor=[0, 0, 0], r=[0, 0.4, 2.9]),
        part("sph", [0.38, 0.09, z + 0.12], [0.08, 0.08, 0.08], "#c23a58"),
    ]
    witch = [
        part("cyl", [0, 0.03, z], [1.42, 0.045, 1.38], "#3b2357"),
        part("cone", [0.02, 0.46, z - 0.02], [0.76, 0.86, 0.72], "#3b2357", [-0.12, 0, 0.1]),
        part("cone", [0.17, 0.95, z - 0.15], [0.26, 0.34, 0.26], "#3b2357", [-0.5, 0, 0.95]),
        part("cyl", [0, 0.11, z], [0.76, 0.1, 0.72], "#ffb43a"),
        part("rbox", [0, 0.11, z + 0.37], [0.16, 0.13, 0.04], GOLD, m="metal"),
        part("rbox", [0, 0.11, z + 0.385], [0.08, 0.06, 0.04], "#3b2357"),
        part("star", [0.39, 0.13, z + 0.08], [0.12, 0.12, 0.04], "#fff2a8", [0, PI / 2, 0],
             m="neon"),
    ]
    crown = [
        part("spikecrown", [0.08, 0.16, z + 0.02], [0.64, 0.34, 0.62], GOLD, [0, 0, -0.14],
             m="metal"),
        part("sph", [0.06, 0.12, z + 0.32], [0.11, 0.11, 0.07], "#e0284a", [0, 0, -0.14],
             m="metal"),
        part("sph", [0.34, 0.1, z + 0.15], [0.08, 0.08, 0.06], "#2a8cff", [0, PI / 2, -0.14],
             m="metal"),
        part("sph", [-0.21, 0.17, z + 0.18], [0.08, 0.08, 0.06], "#24c46a", [0, -0.6, -0.14],
             m="metal"),
    ]
    frog = [
        part("hemi", [0, 0.08, z], [1.3, 0.46, 1.22], "#5cbf4a", decal="knit", wrap=True),
        part("rbox", [0, -0.06, z], [1.32, 0.15, 1.24], "#3f9a3a", decal="knit", wrap=True),
    ] + [p for s in (-1, 1) for p in (
        part("sph", [s * 0.27, 0.33, z + 0.2], [0.3, 0.28, 0.3], "#5cbf4a"),
        part("sph", [s * 0.27, 0.37, z + 0.31], [0.19, 0.19, 0.12], WHITE),
        part("sph", [s * 0.27, 0.38, z + 0.37], [0.09, 0.1, 0.05], "#1b1b1f"),
    )] + [part("sph", [s * 0.22, 0.06, z + 0.62], [0.12, 0.06, 0.04], "#ff8fa8")
          for s in (-1, 1)]
    toque = [
        part("cyl", [0, 0.11, z], [0.82, 0.22, 0.78], WHITE, decal="linen", wrap=True),
        part("sph", [0, 0.46, z], [1.0, 0.6, 0.94], WHITE, decal="linen", wrap=True),
        part("sph", [-0.24, 0.5, z + 0.1], [0.46, 0.44, 0.44], WHITE),
        part("sph", [0.24, 0.5, z - 0.1], [0.46, 0.44, 0.44], WHITE),
    ]
    halo = [part("torus", [0, 0.36, z], [0.86, 0.09, 0.86], "#fff1a6", m="neon", spin=1.1),
            part("torus", [0, 0.36, z], [0.7, 0.04, 0.7], "#ffffff", m="neon", spin=1.1)]
    return [
        _pet_item("pet_hat_beret", "Petite Beret", "pet_hat", 450, "common",
                  "Red felt, worn at an angle she thinks is artistic.", {"parts": beret}, 1),
        _pet_item("pet_hat_straw", "Sunny Straw Hat", "pet_hat", 600, "uncommon",
                  "A straw boater with a pink ribbon, for picnics nobody planned.",
                  {"parts": straw}, 2),
        _pet_item("pet_hat_frog", "Froggy Beanie", "pet_hat", 700, "uncommon",
                  "A knitted frog sits on her head. It blushes when she does.",
                  {"parts": frog}, 3),
        _pet_item("pet_hat_toque", "Little Chef Toque", "pet_hat", 500, "common",
                  "She cannot cook. The hat does not know that.", {"parts": toque}, 4),
        _pet_item("pet_hat_witch", "Tiny Witch Hat", "pet_hat", 900, "rare",
                  "A pointy hat with a bend in it and a star on the band.",
                  {"parts": witch}, 5),
        _pet_item("pet_hat_halo", "Halo", "pet_hat", 1200, "rare",
                  "A ring of light that turns slowly over her head. Rarely deserved.",
                  {"parts": halo}, 6),
        _pet_item("pet_hat_crown", "Little Crown", "pet_hat", 1500, "epic",
                  "Gold, three gems, worn at a tilt. She rules exactly one player: you.",
                  {"parts": crown}, 7),
    ]


# ------------------------------------------------------------ pet face wear
def _faces() -> List[Dict[str, Any]]:
    E = 0.235      # the eyes' centres, either side
    specs = []
    for s in (-1, 1):
        specs += [
            part("torus", [s * E, 0, 0.06], [0.36, 0.05, 0.36], "#5a3b28", [PI / 2, 0, 0],
                 m="metal"),
            part("cyl", [s * E, 0, 0.056], [0.32, 0.02, 0.32], "#cfeaff", [PI / 2, 0, 0], a=0.3),
            part("box", [s * 0.5, 0.03, -0.12], [0.03, 0.03, 0.36], "#5a3b28"),
        ]
    specs.append(part("cyl", [0, 0.04, 0.06], [0.03, 0.12, 0.03], "#5a3b28", [0, 0, PI / 2]))
    shades = []
    for s in (-1, 1):
        shades += [
            part("star", [s * E, 0.0, 0.065], [0.4, 0.4, 0.05], "#ff4f9a", [0, 0, s * 0.1]),
            part("star", [s * E, 0.0, 0.095], [0.27, 0.27, 0.03], "#2b1240", [0, 0, s * 0.1],
                 a=0.88),
            part("box", [s * 0.5, 0.05, -0.12], [0.03, 0.03, 0.36], "#ff4f9a"),
        ]
    shades.append(part("cyl", [0, 0.05, 0.07], [0.03, 0.12, 0.03], "#ff4f9a", [0, 0, PI / 2]))
    plaster = [
        part("rbox", [0.31, -0.2, 0.014], [0.2, 0.07, 0.024], "#f4cfa5", [0, 0, 0.6]),
        part("rbox", [0.31, -0.2, 0.018], [0.2, 0.07, 0.024], "#f4cfa5", [0, 0, -0.6]),
        part("box", [0.31, -0.2, 0.032], [0.06, 0.06, 0.01], "#e8b98a", [0, 0, 0.78]),
    ]
    stickers = [
        part("heart", [0.38, -0.18, 0.016], [0.11, 0.1, 0.025], "#ff5c93"),
        part("heart", [-0.39, -0.16, 0.016], [0.08, 0.075, 0.025], "#ff8db6", [0, 0, 0.3]),
        part("star", [-0.33, -0.27, 0.016], [0.07, 0.07, 0.025], "#ffd84a", m="neon"),
    ]
    monocle = [
        part("torus", [E, 0, 0.065], [0.38, 0.05, 0.38], GOLD, [PI / 2, 0, 0], m="metal"),
        part("cyl", [E, 0, 0.06], [0.33, 0.02, 0.33], "#e9f6ff", [PI / 2, 0, 0], a=0.28),
        part("cyl", [E + 0.12, -0.33, 0.07], [0.016, 0.34, 0.016], GOLD, [0, 0, 0.3],
             m="metal"),
    ]
    return [
        _pet_item("pet_face_specs", "Round Specs", "pet_face", 350, "common",
                  "Wire glasses that make her look like she has read a book.",
                  {"parts": specs}, 11),
        _pet_item("pet_face_stars", "Star Shades", "pet_face", 550, "uncommon",
                  "Pink star-shaped sunglasses. Indoors. Obviously.", {"parts": shades}, 12),
        _pet_item("pet_face_plaster", "Brave Plaster", "pet_face", 150, "common",
                  "A plaster on her cheek from an adventure she will not stop telling you about.",
                  {"parts": plaster}, 13),
        _pet_item("pet_face_stickers", "Cheek Stickers", "pet_face", 250, "common",
                  "Two hearts and a star, stuck on with great care.", {"parts": stickers}, 14),
        _pet_item("pet_face_monocle", "Monocle", "pet_face", 400, "uncommon",
                  "Gold-rimmed, on a chain. She raises one eyebrow at everything now.",
                  {"parts": monocle}, 15),
    ]


# ------------------------------------------------------------- neckwear
def _necks() -> List[Dict[str, Any]]:
    bell = [
        part("torus", [0, -0.025, 0], [0.48, 0.08, 0.44], "#d8324a"),
        part("sph", [0, -0.1, 0.225], [0.13, 0.13, 0.13], GOLD, m="metal"),
        part("box", [0, -0.125, 0.285], [0.06, 0.015, 0.02], "#6a4a10"),
    ]
    scarf = [
        part("torus", [0, 0.0, 0], [0.52, 0.15, 0.48], "#e2533a", decal="knit", wrap=True),
        part("rbox", [0.13, -0.19, 0.22], [0.14, 0.34, 0.06], "#e2533a", [0.08, 0, 0.14],
             decal="knit", wrap=True),
        part("rbox", [0.155, -0.37, 0.235], [0.14, 0.05, 0.065], "#f3d36a", [0.08, 0, 0.14]),
    ]
    bowtie = [part("bowtie", [0, -0.05, 0.215], [0.32, 0.15, 0.08], "#2a2a6e"),
              part("rbox", [0, -0.05, 0.245], [0.07, 0.07, 0.05], "#3a3a8a")]
    pearls = ring_of(16, 0.25, 0.0, lambda a, x, zz: part(
        "sph", [x, -0.05 * (1 + math.cos(a)) / 2 - 0.005, zz * 0.9 + 0.01 * math.cos(a)],
        [0.065, 0.065, 0.065], "#f6f1e6", m="metal"))
    pearls.append(part("sph", [0, -0.11, 0.245], [0.1, 0.12, 0.08], "#fbe9f0", m="metal"))
    ruff = ring_of(12, 0.27, -0.05, lambda a, x, zz: part(
        "sph", [x, -0.05, zz * 0.92], [0.21, 0.14, 0.21],
        "#ffffff" if int(round(a / (math.tau / 12))) % 2 else "#ffc6dd"))
    return [
        _pet_item("pet_neck_bell", "Jingle Collar", "pet_neck", 300, "common",
                  "A red ribbon with a little gold bell. You will always know where she is.",
                  {"parts": bell}, 21),
        _pet_item("pet_neck_scarf", "Cosy Scarf", "pet_neck", 450, "common",
                  "Knitted, a bit too long, wound right up to her chin.", {"parts": scarf}, 22),
        _pet_item("pet_neck_bowtie", "Dapper Bow Tie", "pet_neck", 250, "common",
                  "Navy silk. She has opinions about formal wear now.", {"parts": bowtie}, 23),
        _pet_item("pet_neck_ruff", "Fluffy Ruff", "pet_neck", 500, "uncommon",
                  "A ring of pink and white puffs. Very theatrical.", {"parts": ruff}, 24),
        _pet_item("pet_neck_pearls", "Pearl Necklace", "pet_neck", 800, "rare",
                  "Sixteen pearls and a pink drop. Real? She will never tell.",
                  {"parts": pearls}, 25),
    ]


# ------------------------------------------------------------------- pins
def _pins() -> List[Dict[str, Any]]:
    star = [part("star", [0, 0, 0.03], [0.17, 0.17, 0.05], GOLD, m="metal")]
    heart = [part("heart", [0, 0, 0.03], [0.16, 0.15, 0.05], "#ff4f86"),
             part("sph", [-0.035, 0.03, 0.055], [0.03, 0.03, 0.01], "#ffd1e2")]
    nooget = [
        part("disc", [0, 0, 0.025], [0.17, 0.17, 0.04], GOLD, m="metal"),
        part("torus", [0, 0, 0.045], [0.13, 0.015, 0.13], "#b98a1c", [PI / 2, 0, 0], m="metal"),
        part("box", [-0.03, 0, 0.05], [0.018, 0.08, 0.012], "#9a7012"),
        part("box", [0.03, 0, 0.05], [0.018, 0.08, 0.012], "#9a7012"),
        part("box", [0, 0, 0.05], [0.018, 0.09, 0.012], "#9a7012", [0, 0, 0.62]),
    ]
    daisy = [part("flower", [0, 0, 0.025], [0.19, 0.19, 0.04], WHITE),
             part("sph", [0, 0, 0.05], [0.07, 0.07, 0.03], "#ffcc33")]
    moon = [part("crescent", [0.01, 0, 0.03], [0.12, 0.17, 0.04], "#ffe58a", m="neon"),
            part("star", [-0.05, 0.05, 0.03], [0.05, 0.05, 0.03], "#ffffff", m="neon")]
    return [
        _pet_item("pet_pin_star", "Gold Star", "pet_pin", 200, "common",
                  "For being good. She awarded it to herself.", {"parts": star}, 31),
        _pet_item("pet_pin_heart", "Heart Pin", "pet_pin", 200, "common",
                  "A shiny pink heart, worn over hers.", {"parts": heart}, 32),
        _pet_item("pet_pin_daisy", "Daisy Pin", "pet_pin", 250, "common",
                  "A white daisy with a sunny middle.", {"parts": daisy}, 33),
        _pet_item("pet_pin_moon", "Moon Pin", "pet_pin", 250, "uncommon",
                  "A glowing crescent and a star. Luna has one in her hair.",
                  {"parts": moon}, 34),
        _pet_item("pet_pin_nooget", "Nooget Pin", "pet_pin", 300, "uncommon",
                  "A gold Nooget with an N on it. Not legal tender.", {"parts": nooget}, 35),
    ]


# ------------------------------------------------------------------ outfits
# An outfit recolours her dress rather than adding parts: the torso, the
# sleeves, the skirt, the collar, a cloth weave, buttons or a bib (pet.js).
def _tops() -> List[Dict[str, Any]]:
    return [
        _pet_item("pet_top_cardigan", "Comfy Cardigan", "pet_top", 650, "common",
                  "A cream cardigan with wooden buttons, sleeves to the knuckles.",
                  {"torso": "#efe0c4", "arms": "#efe0c4", "sleeve": 1.0, "buttons": "#7a4f2e",
                   "weave": "knit", "nobow": True}, 41),
        _pet_item("pet_top_sailor", "Sailor Top", "pet_top", 700, "uncommon",
                  "White with a navy collar and skirt, and a red trim on the hem.",
                  {"torso": "#f6f7fb", "arms": "#f6f7fb", "sleeve": 0.55, "skirt": "#22396e",
                   "collar": "#22396e", "trim": "#d93a4a"}, 42),
        _pet_item("pet_top_overalls", "Denim Overalls", "pet_top", 600, "common",
                  "Dungarees over a white tee. Ready for gardening, or for mud.",
                  {"torso": "#f4f1e8", "arms": "#f4f1e8", "sleeve": 0.42, "skirt": "#3f6cb0",
                   "overall": "#3f6cb0", "trim": "#2d5490", "nobow": True}, 43),
        _pet_item("pet_top_raincoat", "Puddle Raincoat", "pet_top", 550, "common",
                  "Bright yellow, buttoned to the top, for splashing in puddles on purpose.",
                  {"torso": "#ffd23a", "arms": "#ffd23a", "sleeve": 1.0, "skirt": "#ffd23a",
                   "collar": "#f0b81c", "buttons": "#2a2a2a", "trim": "#f0b81c",
                   "nobow": True}, 44),
        _pet_item("pet_top_jersey", "Sporty Jersey", "pet_top", 500, "common",
                  "Red with white trim. She is on a team now. The team is her.",
                  {"torso": "#d8323e", "arms": "#d8323e", "sleeve": 0.45, "collar": "#ffffff",
                   "trim": "#ffffff"}, 45),
        _pet_item("pet_top_starry", "Starry Robe", "pet_top", 1100, "rare",
                  "Midnight blue and full of stars. It is a bit big on her.",
                  {"torso": "#232052", "arms": "#232052", "sleeve": 1.0, "skirt": "#232052",
                   "weave": "starfield", "collar": "#f2d36a", "trim": "#f2d36a"}, 46),
    ]


# ----------------------------------------------------------------- the back
def _backs() -> List[Dict[str, Any]]:
    # Her hair falls to her shoulder blades and her head is wider than her
    # shoulders, so whatever she wears on her back sits low -- at the small
    # of her back -- or reaches out past her hair, or it is never seen.
    wing = []
    for k, (lift, size, tint) in enumerate(((0.5, 0.95, "#ffb8e8"), (-0.15, 0.66, "#a8e6ff"))):
        wing.append(place("wing", [0.08, -0.02 - k * 0.16, -0.05], [size, size * 0.86, 0.6],
                          tint, anchor=[-0.5, 0, 0], r=[0, 0.42, lift], a=0.62))
    wing = wing + mirror_x(wing)
    backpack = [
        part("rbox", [0, -0.1, -0.13], [0.46, 0.46, 0.26], "#ffd1e2"),
        part("rbox", [0, 0.02, -0.135], [0.48, 0.18, 0.28], "#ffb3cc"),
        part("rbox", [0, -0.22, -0.27], [0.24, 0.16, 0.04], "#ffb3cc"),
    ] + [p for s in (-1, 1) for p in (
        part("bunnyear", [s * 0.28, 0.12, -0.13], [0.16, 0.34, 0.05], "#ffd1e2", [0, 0, s * -0.9]),
        part("box", [s * 0.08, -0.05, -0.265], [0.05, 0.06, 0.02], "#3a2430"),
    )] + [part("box", [0, -0.11, -0.265], [0.04, 0.025, 0.02], "#ff7d9b")]
    cape = [
        place("cape", [0, 0.2, -0.04], [0.66, 0.96, 0.5], "#d42a3a", anchor=[0, 0.5, 0],
              r=[0.3, 0, 0]),
    ] + [part("sph", [s * 0.22, 0.18, 0.02], [0.09, 0.09, 0.06], GOLD, m="metal")
         for s in (-1, 1)]
    bow = []
    for turn in (0.25, PI - 0.25):
        bow.append(place("bowloop", [0, -0.16, -0.12], [0.62, 0.62, 0.5], "#ff5c93",
                         anchor=[0, 0, 0], r=[0, PI / 2, turn]))
    bow += [part("sph", [0, -0.16, -0.13], [0.17, 0.16, 0.17], "#e8417a")] + [
        part("rbox", [s * 0.12, -0.42, -0.13], [0.12, 0.38, 0.03], "#ff5c93", [0, 0, s * 0.35])
        for s in (-1, 1)]
    bear = "#b07a4a"
    k = 1.25
    teddy = [
        part("sph", [0, 0.0, 0], [0.28, 0.3, 0.24], bear, decal="fur", wrap=True),
        part("sph", [0, 0.26, 0], [0.27, 0.25, 0.24], bear, decal="fur", wrap=True),
        part("sph", [0, 0.21, 0.12], [0.12, 0.09, 0.08], "#e6c79a"),
        part("sph", [0, 0.23, 0.16], [0.04, 0.03, 0.03], "#2a1a12"),
    ] + [p for s in (-1, 1) for p in (
        part("sph", [s * 0.11, 0.39, 0], [0.1, 0.1, 0.07], bear),
        part("box", [s * 0.06, 0.29, 0.11], [0.03, 0.03, 0.02], "#1b1b1f"),
        part("sph", [s * 0.15, 0.04, 0.08], [0.1, 0.16, 0.1], bear, [0.6, 0, s * 0.4]),
        part("sph", [s * 0.09, -0.16, 0.06], [0.11, 0.1, 0.13], bear),
    )]
    # the bear rides on the small of her back facing away from her: turned
    # half round about Y, which mirrors x and z and composes as [rx, PI, rz]
    plush = []
    for q in teddy:
        r = q.get("r") or [0, 0, 0]
        plush.append(dict(q, p=[round(0.12 - q["p"][0] * k, 4), round(-0.14 + q["p"][1] * k, 4),
                                round(-0.2 - q["p"][2] * k, 4)],
                          s=[round(v * k, 4) for v in q["s"]], r=[r[0], PI, r[2]]))
    jet = []
    for s in (-1, 1):
        jet += [
            part("capsule", [s * 0.13, -0.08, -0.15], [0.18, 0.46, 0.18], "#c9d2dc", m="metal"),
            part("cone", [s * 0.13, -0.37, -0.15], [0.14, 0.12, 0.14], "#3a3f48", [PI, 0, 0]),
            part("flame", [s * 0.13, -0.53, -0.15], [0.15, 0.24, 0.08], "#ff9a2a", [PI, 0, 0],
                 m="neon", a=0.9),
        ]
    jet += [part("rbox", [0, -0.06, -0.08], [0.38, 0.32, 0.08], "#e04a3a"),
            part("rbox", [0, 0.07, -0.15], [0.44, 0.06, 0.22], "#2a2f38")]
    return [
        _pet_item("pet_back_bow", "Giant Bow", "pet_back", 450, "common",
                  "A pink bow nearly as big as she is, tied at the small of her back.",
                  {"parts": bow}, 51),
        _pet_item("pet_back_backpack", "Bunny Backpack", "pet_back", 600, "common",
                  "A little pink rucksack with ears. Contents: snacks.", {"parts": backpack}, 52),
        _pet_item("pet_back_plush", "Plushie Pal", "pet_back", 550, "uncommon",
                  "A teddy bear who rides on her back and peeks round at everyone behind.",
                  {"parts": plush}, 53),
        _pet_item("pet_back_cape", "Hero Cape", "pet_back", 700, "uncommon",
                  "A red cape with gold clasps. Flying not included.", {"parts": cape}, 54),
        _pet_item("pet_back_wings", "Fairy Wings", "pet_back", 1000, "rare",
                  "Two pairs of see-through wings, pink above and blue below.",
                  {"parts": wing}, 55),
        _pet_item("pet_back_jetpack", "Mini Jetpack", "pet_back", 1100, "rare",
                  "Two tanks and two little flames. Pixel insists on hers.", {"parts": jet}, 56),
    ]


def _species_items() -> List[Dict[str, Any]]:
    out = []
    for key in SPECIES_ORDER:
        s = SPECIES[key]
        out.append(_pet_item(s["item_id"], s["name"], PET_SLOT, s["price"], s["rarity"],
                             s["tagline"],
                             {"species": key, "colors": dict(s["colors"]),
                              "tags": list(s["tags"]), "signature": s["signature"],
                              "about": s["description"]}, s["order"]))
    return out


COSMETICS: List[Dict[str, Any]] = _hats() + _faces() + _necks() + _pins() + _tops() + _backs()
ITEMS: List[Dict[str, Any]] = _species_items() + COSMETICS
ITEM_IDS = frozenset(it["id"] for it in ITEMS)
ITEMS_BY_ID = {it["id"]: it for it in ITEMS}


def is_pet_slot(slot: str) -> bool:
    return slot in ALL_SLOTS


# ----------------------------------------------------------------- storage
# The table is app/db.py's (``pets``); the active pet is ``avatars.pet``.


class PetError(Exception):
    pass


def _now() -> int:
    return int(time.time())


def _load(raw: Any, fallback: Any) -> Any:
    try:
        value = json.loads(raw)
        if isinstance(value, type(fallback)):
            return value
    except Exception:
        pass
    return fallback


def clean_name(name: Any, fallback: str) -> str:
    """A pet's name: letters, digits, spaces and a little punctuation, at
    most NAME_MAX long -- the characters a username may use, plus spaces."""
    text = security.clean_text(name or "", 64, allow_newlines=False)
    text = re.sub(r"[^A-Za-z0-9 _.'\-]", "", text).strip()
    text = re.sub(r"\s+", " ", text)[:NAME_MAX].strip()
    return text or fallback


def clean_colors(colors: Any, species: Dict[str, Any]) -> Dict[str, str]:
    out = dict(species["colors"])
    if isinstance(colors, dict):
        for key in COLOR_KEYS:
            value = colors.get(key)
            if isinstance(value, str) and security.valid_color(value):
                out[key] = value.lower()
    return out


def clean_tags(tags: Any, species: Dict[str, Any]) -> List[str]:
    if not isinstance(tags, list):
        return list(species["tags"])
    out: List[str] = []
    for tag in tags:
        tag = str(tag or "").strip().lower()
        if tag in TAGS and tag not in out:
            out.append(tag)
    return out[:MAX_TAGS]


def _owned_rows(user_id: int, slots: List[str]) -> List[Dict[str, Any]]:
    ids = [it["id"] for it in ITEMS if it["slot"] in slots]
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    rows = db.query("SELECT * FROM inventory WHERE user_id=? AND item_id IN (%s)"
                    " ORDER BY acquired_at, id" % marks, [user_id] + ids)
    return [dict(r) for r in rows]


def _config_row(user_id: int, inv_id: int, species: Dict[str, Any]) -> Dict[str, Any]:
    row = db.query_one("SELECT * FROM pets WHERE inv_id=?", (inv_id,))
    if row is None or int(row["user_id"]) != int(user_id):
        # first look at this pet (or she changed hands): her species' look
        db.execute("INSERT OR REPLACE INTO pets(inv_id,user_id,name,colors,tags,equipped,"
                   "updated_at) VALUES(?,?,?,?,?,?,?)",
                   (inv_id, user_id, species["name"], json.dumps(species["colors"]),
                    json.dumps(species["tags"]), "{}", _now()))
        row = db.query_one("SELECT * FROM pets WHERE inv_id=?", (inv_id,))
    return dict(row)


def owned(user_id: int) -> List[Dict[str, Any]]:
    """Every pet this account owns, with her name, look and outfit."""
    out = []
    cosmetics = {int(r["id"]): r for r in _owned_rows(user_id, COSMETIC_SLOTS)}
    for inv in _owned_rows(user_id, [PET_SLOT]):
        species = SPECIES_BY_ITEM.get(inv["item_id"])
        if species is None:
            continue
        cfg = _config_row(user_id, int(inv["id"]), species)
        equipped = {}
        for slot, inv_id in _load(cfg["equipped"], {}).items():
            try:
                inv_id = int(inv_id)
            except (TypeError, ValueError):
                continue
            row = cosmetics.get(inv_id)
            if slot in COSMETIC_SLOTS and row and ITEMS_BY_ID[row["item_id"]]["slot"] == slot:
                equipped[slot] = inv_id
        out.append({
            "inv_id": int(inv["id"]), "item_id": inv["item_id"], "species": species["id"],
            "species_name": species["name"], "serial": int(inv.get("serial") or 0),
            "name": clean_name(cfg["name"], species["name"]),
            "colors": clean_colors(_load(cfg["colors"], {}), species),
            "tags": clean_tags(_load(cfg["tags"], []), species),
            "equipped": equipped, "acquired_at": int(inv.get("acquired_at") or 0),
        })
    return out


def owns_any(user_id: int) -> bool:
    ids = [s["item_id"] for s in SPECIES.values()]
    marks = ",".join("?" * len(ids))
    return bool(db.scalar("SELECT 1 FROM inventory WHERE user_id=? AND item_id IN (%s) LIMIT 1"
                          % marks, [user_id] + ids, 0))


def cosmetics_owned(user_id: int) -> List[Dict[str, Any]]:
    """The pet cosmetics this account owns, one entry per copy."""
    out = []
    for row in _owned_rows(user_id, COSMETIC_SLOTS):
        item = ITEMS_BY_ID[row["item_id"]]
        out.append({"inv_id": int(row["id"]), "item_id": item["id"], "name": item["name"],
                    "slot": item["slot"], "rarity": item.get("rarity", "common")})
    return out


def active_id(user_id: int) -> int:
    row = db.query_one("SELECT pet FROM avatars WHERE user_id=?", (user_id,))
    if row is None:
        return 0
    try:
        return int(row["pet"] or 0)
    except (KeyError, IndexError, TypeError, ValueError):
        return 0


def set_active(user_id: int, inv_id: int) -> int:
    """Make one of your pets the one who follows you (0: none of them)."""
    inv_id = int(inv_id or 0)
    if inv_id:
        if not any(p["inv_id"] == inv_id for p in owned(user_id)):
            raise PetError("You do not own that pet.")
    from . import avatars
    avatars.raw_avatar(user_id)            # make sure the row exists
    db.execute("UPDATE avatars SET pet=?, updated_at=? WHERE user_id=?",
               (inv_id, _now(), user_id))
    return inv_id


def save(user_id: int, inv_id: int, name: Any = None, colors: Any = None, tags: Any = None,
         equipped: Any = None) -> Dict[str, Any]:
    """Change one pet: any of her name, colours, persona tags and outfit."""
    pet = next((p for p in owned(user_id) if p["inv_id"] == int(inv_id or 0)), None)
    if pet is None:
        raise PetError("You do not own that pet.")
    species = SPECIES[pet["species"]]
    if name is not None:
        pet["name"] = clean_name(name, species["name"])
    if colors is not None:
        if not isinstance(colors, dict):
            raise PetError("Colours must be a set of hex values.")
        for key, value in colors.items():
            if key in COLOR_KEYS and not (isinstance(value, str) and security.valid_color(value)):
                raise PetError("Invalid colour for %s." % COLOR_LABELS[key].lower())
        merged = dict(pet["colors"])
        merged.update({k: v for k, v in colors.items() if k in COLOR_KEYS})
        pet["colors"] = clean_colors(merged, species)
    if tags is not None:
        if not isinstance(tags, list):
            raise PetError("Persona tags must be a list.")
        if len(tags) > MAX_TAGS:
            raise PetError("A pet can have at most %d persona tags." % MAX_TAGS)
        pet["tags"] = clean_tags(tags, species)
    if equipped is not None:
        if not isinstance(equipped, dict):
            raise PetError("Outfit must be a set of slots.")
        mine = {c["inv_id"]: c for c in cosmetics_owned(user_id)}
        out = dict(pet["equipped"])
        for slot, value in equipped.items():
            if slot not in COSMETIC_SLOTS:
                raise PetError("Unknown pet slot.")
            try:
                value = int(value or 0)
            except (TypeError, ValueError):
                raise PetError("Unknown item.")
            if value <= 0:
                out.pop(slot, None)
                continue
            item = mine.get(value)
            if item is None:
                raise PetError("You do not own that item.")
            if item["slot"] != slot:
                raise PetError("%s does not go in that slot." % item["name"])
            out[slot] = value
        pet["equipped"] = out
    db.execute("UPDATE pets SET name=?, colors=?, tags=?, equipped=?, updated_at=? "
               "WHERE inv_id=? AND user_id=?",
               (pet["name"], json.dumps(pet["colors"], separators=(",", ":")),
                json.dumps(pet["tags"]), json.dumps(pet["equipped"], separators=(",", ":")),
                _now(), pet["inv_id"], user_id))
    if active_id(user_id) == pet["inv_id"]:
        db.execute("UPDATE avatars SET updated_at=? WHERE user_id=?", (_now(), user_id))
    return pet


def adopted(user_id: int, inv_id: int) -> None:
    """A pet was just bought: give her a config row, and if she is the
    first, make her the one who follows you."""
    species = None
    row = db.query_one("SELECT item_id FROM inventory WHERE id=? AND user_id=?", (inv_id, user_id))
    if row is not None:
        species = SPECIES_BY_ITEM.get(row["item_id"])
    if species is None:
        return
    _config_row(user_id, inv_id, species)
    current = active_id(user_id)
    if not current or not any(p["inv_id"] == current for p in owned(user_id)):
        set_active(user_id, inv_id)


def forget_missing(user_id: int) -> None:
    """Drop the active pet if she is no longer owned (sold, say)."""
    current = active_id(user_id)
    if current and not db.query_one("SELECT 1 FROM inventory WHERE id=? AND user_id=?",
                                    (current, user_id)):
        db.execute("UPDATE avatars SET pet=0 WHERE user_id=?", (user_id,))


# ---------------------------------------------------------------- payloads
def _cosmetic_payload(item_id: str) -> Optional[Dict[str, Any]]:
    item = ITEMS_BY_ID.get(item_id)
    if item is None or item["slot"] not in COSMETIC_SLOTS:
        return None
    from . import catalog
    whole = catalog.get(item_id) or item
    return {"item_id": item_id, "name": whole["name"], "slot": whole["slot"],
            "data": whole.get("data", {})}


def describe(pet: Dict[str, Any], cosmetic_items: Dict[int, str]) -> Dict[str, Any]:
    """A pet as the renderers draw her: species, name, colours, tags and the
    models of what she is wearing."""
    items = {}
    for slot, inv_id in (pet.get("equipped") or {}).items():
        item_id = cosmetic_items.get(int(inv_id))
        payload = _cosmetic_payload(item_id) if item_id else None
        if payload:
            items[slot] = payload
    species = SPECIES[pet["species"]]
    return {
        "inv_id": pet["inv_id"], "item_id": pet["item_id"], "species": pet["species"],
        "species_name": species["name"], "name": pet["name"],
        "colors": dict(pet["colors"]), "tags": list(pet["tags"]),
        "tag_info": [dict(TAGS[t], id=t) for t in pet["tags"]],
        "items": items,
    }


def payload(user_id: int) -> Optional[Dict[str, Any]]:
    """The active pet, ready to draw, or None."""
    current = active_id(user_id)
    if not current:
        return None
    pet = next((p for p in owned(user_id) if p["inv_id"] == current), None)
    if pet is None:
        return None
    names = {c["inv_id"]: c["item_id"] for c in cosmetics_owned(user_id)}
    return describe(pet, names)


def all_payloads(user_id: int) -> List[Dict[str, Any]]:
    names = {c["inv_id"]: c["item_id"] for c in cosmetics_owned(user_id)}
    return [describe(p, names) for p in owned(user_id)]


def compact(pet: Any) -> Optional[Dict[str, Any]]:
    """The active pet by reference, for the game ticket: what she is and what
    she wears by id, her colours, name and tags -- a few hundred bytes."""
    if not isinstance(pet, dict) or pet.get("species") not in SPECIES:
        return None
    return {"inv_id": pet.get("inv_id"), "species": pet["species"], "name": pet.get("name", ""),
            "colors": pet.get("colors") or {}, "tags": pet.get("tags") or [],
            "items": {slot: (entry or {}).get("item_id") for slot, entry in
                      (pet.get("items") or {}).items() if entry}}


def expand(pet: Any) -> Optional[Dict[str, Any]]:
    """Undo compact(), re-validating everything that came back."""
    if not isinstance(pet, dict) or pet.get("species") not in SPECIES:
        return None
    species = SPECIES[pet["species"]]
    items = {}
    for slot, entry in (pet.get("items") or {}).items():
        item_id = entry.get("item_id") if isinstance(entry, dict) else entry
        payload_ = _cosmetic_payload(str(item_id or ""))
        if slot in COSMETIC_SLOTS and payload_ and payload_["slot"] == slot:
            items[slot] = payload_
    tags = clean_tags(pet.get("tags"), species)
    return {"inv_id": int(pet.get("inv_id") or 0), "item_id": species["item_id"],
            "species": species["id"], "species_name": species["name"],
            "name": clean_name(pet.get("name"), species["name"]),
            "colors": clean_colors(pet.get("colors"), species), "tags": tags,
            "tag_info": [dict(TAGS[t], id=t) for t in tags], "items": items}


# ------------------------------------------------------------------- shelf
def tag_list() -> List[Dict[str, str]]:
    return [dict(TAGS[t], id=t) for t in TAG_ORDER]


def shelf(user_id: Optional[int]) -> Dict[str, Any]:
    """The Pets shelf: the five pets up top, their wardrobe below."""
    owned_items = set()
    mine: List[Dict[str, Any]] = []
    if user_id:
        rows = _owned_rows(user_id, ALL_SLOTS)
        owned_items = {r["item_id"] for r in rows}
        mine = all_payloads(user_id)
    from . import catalog, crates
    grades = crates.GRADES
    pets = []
    for key in SPECIES_ORDER:
        s = SPECIES[key]
        grade = grades.get(s["rarity"], grades["common"])
        pets.append({
            "id": s["item_id"], "species": key, "name": s["name"], "price": s["price"],
            "rarity": s["rarity"], "rarity_color": grade["color"], "tagline": s["tagline"],
            "description": s["description"], "signature": s["signature"],
            "colors": s["colors"], "tags": [dict(TAGS[t], id=t) for t in s["tags"]],
            "owned": s["item_id"] in owned_items,
            "preview": {"species": key, "colors": s["colors"], "tags": s["tags"], "items": {},
                        "name": s["name"]},
        })
    wardrobe = []
    for slot in COSMETIC_SLOTS:
        cards = []
        for it in sorted((i for i in COSMETICS if i["slot"] == slot),
                         key=lambda i: (i["sort_order"], i["name"])):
            whole = catalog.get(it["id"]) or it
            grade = grades.get(it["rarity"], grades["common"])
            cards.append({"id": it["id"], "name": it["name"], "slot": slot,
                          "price": it["price"], "rarity": it["rarity"],
                          "rarity_color": grade["color"], "description": it["description"],
                          "owned": it["id"] in owned_items, "data": whole.get("data", {})})
        wardrobe.append({"slot": slot, "label": SHELF_LABELS[slot], "cards": cards})
    return {"pets": pets, "wardrobe": wardrobe, "mine": mine,
            "owns_pet": any(p["owned"] for p in pets)}
