"""Calamity Coast -- four towns, each about to have a very bad day.

Every area is a town and its surroundings, with the disasters it suffers
written into ``extra["disasters"]`` (see app/game/worlds/calamity_coast.py
for the parts they are made of) and the marks the rules and the bots use:
``high`` and ``shelter`` places, ``stranded`` townsfolk, the ``evac`` point
and ``crate`` drops.
"""
from __future__ import annotations

from typing import Any, Dict

from ..kit import build_world
from . import oldtown, palmkey, portsunny, summit

AREAS = [
    ("portsunny", portsunny, "Port Sunny"),
    ("summit", summit, "Summit Village"),
    ("palmkey", palmkey, "Palm Key"),
    ("oldtown", oldtown, "Old Town"),
]


def build() -> Dict[str, Any]:
    return build_world("Calamity Coast", "disaster_survival", AREAS)
