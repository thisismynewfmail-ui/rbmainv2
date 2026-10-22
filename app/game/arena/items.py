"""Weapons and tools a world hands out instead of the player's own.

A hotbar entry is the same dict the avatar descriptor carries for an owned
item -- ``item_id``, ``name``, ``data.stats`` and ``data.parts`` (the held
model, in hand coordinates) -- so the engine fires it, the client draws it
in hand and the bots choose between them exactly as they do for anything a
player owns.  ``inv_id`` is negative: nobody owns these, the round lends
them.

``kind: "arena"`` is a tool rather than a weapon: firing one does whatever
the world's ``arena_fire`` says (become a prop, taunt, throw a decoy, pass
a bomb) with no ammunition and no hit test of its own.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

_ids: Dict[str, int] = {}


def item(item_id: str, name: str, stats: Dict[str, Any],
         parts: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    inv = _ids.setdefault(item_id, -(len(_ids) + 1) * 7)
    return {"inv_id": inv, "item_id": item_id, "name": name, "slot": "usable",
            "tier": "normal", "lent": True,
            "data": {"stats": dict(stats), "parts": [dict(p) for p in parts or []]}}


def tool(item_id: str, name: str, action: str, parts: Optional[List[Dict[str, Any]]] = None,
         rpm: float = 60.0, **extra: Any) -> Dict[str, Any]:
    stats = {"kind": "arena", "action": action, "rpm": rpm, "mag": 0, "reserve": 0,
             "range": float(extra.pop("range", 12.0)), "sound": extra.pop("sound", "ui")}
    stats.update(extra)
    return item(item_id, name, stats, parts)


# ---------------------------------------------------------------- shapes
def ball(colour: str, size: float = 1.1) -> List[Dict[str, Any]]:
    return [{"t": "sph", "p": [0, 0.1, 0.4], "s": [size, size, size], "c": colour}]


def blaster(body: str, tank: str, nozzle: str = "#2a2d31") -> List[Dict[str, Any]]:
    return [{"t": "box", "p": [0, 0, 0.45], "s": [0.32, 0.36, 1.2], "c": body},
            {"t": "cyl", "p": [0, 0.36, 0.1], "s": [0.42, 0.7, 0.42], "c": tank,
             "m": "glass", "a": 0.85},
            {"t": "cyl", "p": [0, 0.02, 1.12], "s": [0.16, 0.5, 0.16], "c": nozzle,
             "r": [1.5708, 0, 0]},
            {"t": "box", "p": [0, -0.34, -0.05], "s": [0.22, 0.55, 0.32], "c": "#22262b"}]


def club(handle: str, head: str, length: float = 1.9) -> List[Dict[str, Any]]:
    return [{"t": "cyl", "p": [0, 0, length * 0.32], "s": [0.16, length * 0.7, 0.16],
             "c": handle, "r": [1.5708, 0, 0]},
            {"t": "cyl", "p": [0, 0, length * 0.78], "s": [0.42, length * 0.42, 0.42],
             "c": head, "r": [1.5708, 0, 0]}]


def knife(blade: str = "#d8dde2", grip: str = "#3a2a22") -> List[Dict[str, Any]]:
    return [{"t": "box", "p": [0, 0, 0.1], "s": [0.16, 0.2, 0.45], "c": grip},
            {"t": "box", "p": [0, 0.02, 0.62], "s": [0.06, 0.18, 0.7], "c": blade, "m": "metal"},
            {"t": "box", "p": [0, 0, 0.34], "s": [0.32, 0.08, 0.08], "c": "#8a8a8a",
             "m": "metal"}]


def revolver(colour: str = "#3a3f46") -> List[Dict[str, Any]]:
    return [{"t": "box", "p": [0, 0.02, 0.45], "s": [0.18, 0.2, 1.05], "c": colour, "m": "metal"},
            {"t": "cyl", "p": [0, 0.0, 0.18], "s": [0.36, 0.34, 0.36], "c": "#5a5f66",
             "r": [1.5708, 0, 0], "m": "metal"},
            {"t": "box", "p": [0, -0.3, -0.08], "s": [0.2, 0.52, 0.3], "c": "#6a4a2a"}]


def gadget(body: str, light: str) -> List[Dict[str, Any]]:
    return [{"t": "box", "p": [0, 0, 0.3], "s": [0.42, 0.3, 0.7], "c": body},
            {"t": "box", "p": [0, 0.17, 0.3], "s": [0.3, 0.06, 0.4], "c": light, "m": "neon"}]
