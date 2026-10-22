"""The arena worlds: fifteen servers built on one round-and-area engine.

Every world here is a :class:`~app.game.arena.base.ArenaWorld` -- one map of
four separate places, played one at a time, a set number of rounds in each
before the server shuffles to another -- with its own rules, its own bots
and its own client plugin.  ``base`` is the engine, ``kit`` builds the
places, ``entities`` the moving things in them, ``bots`` the shared bot plan
and ``items`` the weapons a world hands out instead of your own.

``WORLD_CLASSES`` is how a game host finds a world's class from its id
without importing all fifteen.
"""
from __future__ import annotations

import importlib
from typing import Dict

WORLD_CLASSES: Dict[str, str] = {
    "cataclysm": "app.game.worlds.cataclysm:Cataclysm",
    "prop_panic": "app.game.worlds.prop_panic:PropPanic",
    "rail_rumble": "app.game.worlds.rail_rumble:RailRumble",
    "convoy": "app.game.worlds.convoy:Convoy",
    "midnight_mystery": "app.game.worlds.midnight_mystery:MidnightMystery",
    "grand_heist": "app.game.worlds.grand_heist:GrandHeist",
    "splat_turf": "app.game.worlds.splat_turf:SplatTurf",
    "bonk_brawl": "app.game.worlds.bonk_brawl:BonkBrawl",
    "bastion": "app.game.worlds.bastion:Bastion",
    "dodgeball": "app.game.worlds.dodgeball:Dodgeball",
    "bomb_bash": "app.game.worlds.bomb_bash:BombBash",
    "plunder_cove": "app.game.worlds.plunder_cove:PlunderCove",
    "storm_circle": "app.game.worlds.storm_circle:StormCircle",
    "flee_beast": "app.game.worlds.flee_beast:FleeBeast",
    "tycoon_wars": "app.game.worlds.tycoon_wars:TycoonWars",
}


def world_class(world_id: str):
    """The class that runs ``world_id``, or None if it is not an arena world."""
    target = WORLD_CLASSES.get(world_id)
    if not target:
        return None
    module_name, _, class_name = target.partition(":")
    return getattr(importlib.import_module(module_name), class_name)


def is_arena(world_id: str) -> bool:
    return world_id in WORLD_CLASSES
