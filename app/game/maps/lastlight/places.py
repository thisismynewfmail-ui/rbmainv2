"""Last Light's places beyond the first four, in the order the world page
lists them.

Each entry is a module of this package (``build(area)``, ``HALF``, ``SKY``
and ``AMBIENT``), the place's name, its ground colour and how far its fog
lets you see.  They are laid out round the first four on a grid
(:data:`SLOTS`), each 2,400 units from its neighbours, so no place is ever
in sight of another.  The web side's list of the same places (names,
blurbs) is the world's registry entry in app/models/worlds.py;
tools/lltests.py holds the two to each other.
"""
from __future__ import annotations

ORDER = [
    ("drivein", "Starlite Drive-In", "#3f5a34", 640.0),
    ("zoo", "Harrow County Zoo", "#5a7a3a", 720.0),
    ("aquarium", "Harrow Point Aquarium", "#c8b48a", 600.0),
    ("backlot", "Silver Screen Studios", "#4a6438", 700.0),
]

# where each new place sits, in units of the spacing, in the order above
SLOTS = [(-1, -1), (1, -1), (-1, 1), (1, 1), (-2, 0), (2, 0), (0, -2), (0, 2),
         (-2, -1), (2, -1), (-2, 1), (2, 1), (-1, -2), (1, -2), (-1, 2), (1, 2),
         (-2, -2), (2, -2), (-2, 2), (2, 2)]
