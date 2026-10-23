"""Prop Panic -- four places full of things, and some of the things are
people.

Every area is a building and its grounds, furnished from one catalogue of
props (catalogue.py): each prop that is placed is also a disguise the
hiders can take, and the area's ``extra["props"]`` carries the drawings so
the client can put a hider inside one.  ``extra["decor"]`` is every placed
prop, which is what a hunter's wrong guess hits.
"""
from __future__ import annotations

from typing import Any, Dict

from ..kit import build_world
from . import grandma, megamart, museum, toyshop

AREAS = [
    ("grandma", grandma, "Grandma's Cottage"),
    ("toyshop", toyshop, "Tinker's Toy Emporium"),
    ("megamart", megamart, "MegaMart"),
    ("museum", museum, "The Museum After Dark"),
]


def build() -> Dict[str, Any]:
    return build_world("Prop Panic", "prop_hunt", AREAS)
