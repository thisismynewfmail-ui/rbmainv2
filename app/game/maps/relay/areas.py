"""Blackout Relay's rotation, in the order the world page lists it.

Each entry is a module of this package (``build(area)`` and its ``HALF``,
``SKY``, ``AMBIENT``, ``GROUND`` and ``FOG``) and the map's name.  The web
side's list of the same maps (names, blurbs, thumbnails) is the world's
registry entry in app/models/worlds.py; tools/relaytests.py holds the two to
each other.
"""
from __future__ import annotations

ORDER = [
    ("substation", "Substation Nine"),
    ("thimble", "Thimble Acre"),
    ("orrery", "The Orrery"),
    ("saltglass", "Saltglass Flats"),
    ("drawdown", "Drawdown"),
    ("lantern", "Lantern Terraces"),
    ("meteora", "Meteora"),
    ("circuit", "Circuit City"),
    ("snowglobe", "Snowglobe Hollow"),
    ("bigear", "Big Ear Array"),
    ("polder", "Polderhaven"),
]
