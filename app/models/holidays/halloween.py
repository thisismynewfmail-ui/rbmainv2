"""Halloween: the lamps go out across the server, one October at a time.

  2022  Graveyard Shift      coffins, skeleton keys, the night shift at the cemetery
  2023  Witching Hour        cauldrons, broomsticks, a coven on the hill
  2024  Manor of Whispers    a haunted manor: candelabras, portraits, the séance
  2025  Big Top Terror       a carnival that came to town and never left
  2026  The Hallowed Harvest the current event (Oct 1 -- Nov 8): pumpkins, the
                             Plague Captain's surgeon, souls and candy

The 2026 crate shipped before the other years were written up, so its items
keep the ids they shipped with (``hat_hexed_witch``, ``crate_halloween``,
``ev_harvest_2026``...) and live in app/models/cosmetics.py; the event here
wraps them, and adds what came later in the season.
"""
from __future__ import annotations

from .. import cosmetics
from .kit import Event

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

EVENTS = [HW26]
