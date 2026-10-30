"""The event worlds: servers built from several areas played one at a time.

Each world here is one module holding everything the *web* side needs to
know about it, as plain data, so the website, the badge catalogue, the bot
director and the Bots Zone can all read it without importing any game code:

``WORLD``           its entry in the world registry (app/models/worlds.py)
``FAMILY``          (name, colours) of the plate its badges are struck on
``BADGES``          its badge ladders, as ``badges._badge`` arguments
``DERIVED``         stats counted from other stats ({"x_areas": "x_area_"})
``SPEECH``          its speech events: (id, label, chance, help)
``describe``        what one of those events reads like from a bot's side
``CANNED``          stock lines for when the language model is down
``BOT_SECTION``     (id, label, blurb, icon) of its Bots Zone subtab
``BOT_FIELDS``      that subtab's settings, as ``bots.config.Field`` args
``PERSONA_TIES``    what each persona does there (the subtab's table)
``PERSONA_TAG``     the "favourite world" persona tag for it
``PROMPT``          what the language model is told the world is
``HISTORY``         how a new bot's made-up play history is booked there
``history_badges``  the badge stats that history earns
``DORMANT``         how a sleeping round of it advances

The game rules live in ``app/game/worlds/<id>.py`` (an
:class:`~app.game.worlds.arena.ArenaWorld`), the maps in
``app/game/maps/events/<id>/`` and the client in ``static/js/worlds/``.
``howto_readmes/event_worlds.txt`` walks through adding one.

**Order matters.**  The bot director keeps each bot's world as an index into
the world registry, and the registry appends these after the original
worlds in exactly this order, so a new world goes on the *end* of
``MODULES`` and nothing is ever taken out of the middle of it.
"""
from __future__ import annotations

import importlib
from typing import Any, Dict, List, Optional

MODULES: List[str] = [
    "rail_rivals",
    "prop_panic",
    "calamity_coast",
    "whodunit",
    "sky_sprint",
    "plunder_bay",
]

_loaded: Optional[List[Any]] = None


def modules() -> List[Any]:
    """Every event world's metadata module, in registry order."""
    global _loaded
    if _loaded is None:
        _loaded = [importlib.import_module("%s.%s" % (__name__, name))
                   for name in MODULES]
    return _loaded


def by_id(world_id: str) -> Optional[Any]:
    for module in modules():
        if module.WORLD["id"] == world_id:
            return module
    return None


def world_defs() -> List[Dict[str, Any]]:
    """The registry entries, ready to be appended to ``worlds.WORLDS``."""
    out = []
    for module in modules():
        entry = dict(module.WORLD)
        entry.setdefault("engine", "arena")
        entry.setdefault("creator", "BLOCKHAVEN")
        entry.setdefault("shuffle", False)
        entry.setdefault("display_order", 10)
        world_id = entry["id"]
        entry.setdefault("cls", "app.game.worlds.%s" % world_id)
        entry.setdefault("thumb_script", "/static/js/worlds/%s_thumbs.js" % world_id)
        entry.setdefault("game_scripts", ["/static/js/worlds/%s.js" % world_id])
        for area in entry.get("areas") or []:
            area.setdefault("thumb", "%s_%s" % (entry.get("prefix", world_id), area["id"]))
        out.append(entry)
    return out


def ids() -> List[str]:
    return [m.WORLD["id"] for m in modules()]


def label_of(world_id: str) -> str:
    module = by_id(world_id)
    return module.WORLD["name"] if module else world_id
