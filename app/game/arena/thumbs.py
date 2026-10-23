"""The arena worlds' pictures, shot from their real geometry.

Each place stages a moment (``ArenaArea.thumb``): a camera and a few players
posed in it -- in the classic yellow, red and blue -- and the world stages
one more for its card in the world browser (``build_world(card=...)``).
The picture is rendered in the browser (``static/js/ui/world_thumbs.js``)
from the parts this module picks out of the built map: the ones in front of
that camera and near enough to matter, biggest on screen first, so a card is
the place exactly as it is played and never a hand-made model that drifts
away from it.

A world's map is built once per process, its five shots cut from it, and
the map let go; the shots are kept.
"""
from __future__ import annotations

import math
import threading
from typing import Any, Dict, List, Optional, Sequence

from . import WORLD_CLASSES, world_class
from . import items as arena_items

MAX_PARTS = 3600
REACH = 620.0
_shots: Dict[str, Dict[str, Any]] = {}
_failed: set = set()
_lock = threading.Lock()

# what a figure can hold in a picture, by name
HOLD = {
    "ball": lambda: arena_items.ball("#d83a2a", 1.3),
    "ball_blue": lambda: arena_items.ball("#2f6fd8", 1.3),
    "bomb": lambda: [{"t": "sph", "p": [0, 0.1, 0.5], "s": [1.3, 1.3, 1.3], "c": "#1a1a22"},
                     {"t": "cyl", "p": [0, 0.85, 0.5], "s": [0.12, 0.5, 0.12], "c": "#c8a060"},
                     {"t": "sph", "p": [0, 1.15, 0.5], "s": [0.3, 0.3, 0.3], "c": "#ff9a2a",
                      "m": "neon"}],
    "blaster_pink": lambda: arena_items.blaster("#ff4fa8", "#ff9ad8"),
    "blaster_teal": lambda: arena_items.blaster("#1fc8b8", "#9af4ea"),
    "club": lambda: arena_items.club("#8a5a2a", "#c8a060"),
    "hammer": lambda: arena_items.club("#4a4a52", "#9aa0a8", 2.2),
    "knife": lambda: arena_items.knife(),
    "revolver": lambda: arena_items.revolver(),
    "gadget": lambda: arena_items.gadget("#2a2d31", "#3affd8"),
    "shovel": lambda: [{"t": "cyl", "p": [0, 0, 0.5], "s": [0.14, 1.8, 0.14], "c": "#8a5a2a",
                        "r": [1.5708, 0, 0]},
                       {"t": "box", "p": [0, 0, 1.5], "s": [0.6, 0.08, 0.7], "c": "#9aa0a8",
                        "m": "metal"}],
    "bag": lambda: [{"t": "sph", "p": [0, -0.2, 0.3], "s": [1.4, 1.5, 1.2], "c": "#3a7a3a"},
                    {"t": "box", "p": [0, 0.3, 0.3], "s": [0.5, 0.3, 0.5], "c": "#f2d24a",
                     "dec": "t~$~#3a7a3a~#f2d24a~1"}],
    "torch": lambda: [{"t": "cyl", "p": [0, 0, 0.3], "s": [0.2, 0.8, 0.2], "c": "#2a2a2a"},
                      {"t": "cyl", "p": [0, 0, 0.75], "s": [0.32, 0.18, 0.32], "c": "#fff4c8",
                       "m": "neon"}],
}


def _holding(name: Any) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    if isinstance(name, list):
        parts = name
    elif name in HOLD:
        parts = HOLD[name]()
    else:
        try:
            from ...models import catalog
            item = catalog.get(str(name))
        except Exception:
            item = None
        if not item:
            return None
        return {"item_id": item["id"], "name": item["name"], "data": item["data"]}
    return {"item_id": "thumb_" + str(name)[:20], "name": "", "data": {"parts": parts, "stats": {}}}


def _cull(parts: Sequence[Dict[str, Any]], eye: Sequence[float], look: Sequence[float],
          fov: float) -> List[Dict[str, Any]]:
    fwd = [look[0] - eye[0], look[1] - eye[1], look[2] - eye[2]]
    length = math.sqrt(sum(v * v for v in fwd)) or 1.0
    fwd = [v / length for v in fwd]
    tan_v = math.tan(math.radians(fov) / 2.0)
    tan_h = tan_v * 16.0 / 9.0
    spread = math.sqrt(tan_v * tan_v + tan_h * tan_h) * 1.08
    kept = []
    for part in parts:
        p, s = part.get("p"), part.get("s")
        if not p or not s:
            continue
        radius = 0.5 * math.sqrt(s[0] * s[0] + s[1] * s[1] + s[2] * s[2])
        v = [p[0] - eye[0], p[1] - eye[1], p[2] - eye[2]]
        along = v[0] * fwd[0] + v[1] * fwd[1] + v[2] * fwd[2]
        if along + radius < 0.5:
            continue
        dist = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        if dist - radius > REACH:
            continue
        lateral = math.sqrt(max(0.0, dist * dist - along * along))
        if lateral - radius > max(0.0, along) * spread + 2.0:
            continue
        # how big it looks: what goes first when there is too much
        kept.append((radius / max(1.0, along), part))
    kept.sort(key=lambda kv: -kv[0])
    out = []
    for _size, part in kept[:MAX_PARTS]:
        clean = {k: v for k, v in part.items() if k in ("t", "p", "s", "c", "r", "m", "a", "dec", "st", "dw")}
        out.append(clean)
    return out


def _shot(map_data: Dict[str, Any], area: Dict[str, Any], spec: Dict[str, Any],
          title: str) -> Dict[str, Any]:
    parts = map_data["parts"][area["parts"][0]:area["parts"][1]]
    eye, look, fov = spec["eye"], spec["look"], float(spec.get("fov", 44.0))
    culled = _cull(parts, eye, look, fov)
    culled.extend(dict(p) for p in spec.get("props") or [])
    figures = []
    for f in spec.get("figures") or []:
        figures.append({"p": f["p"], "yaw": f["yaw"], "pose": f.get("pose") or "idle",
                        "holding": _holding(f.get("holding")), "extra": f.get("extra")})
    return {"title": title, "eye": eye, "look": look, "fov": fov,
            "sky": spec.get("sky") or area["sky"], "parts": culled, "figures": figures}


def _build(world_id: str) -> None:
    cls = world_class(world_id)
    map_data = cls.build_map()
    markers = map_data.get("markers") or {}
    areas = {a["id"]: a for a in markers.get("areas", [])}
    for area_id, area in areas.items():
        spec = area.get("thumb") or {}
        if not spec:
            centre = area["centre"]
            spec = {"eye": [centre[0] + 90, centre[1] + 60, centre[2] + 90],
                    "look": [centre[0], centre[1] + 6, centre[2]], "fov": 44.0}
        _shots["ar_%s_%s" % (world_id, area_id)] = _shot(map_data, area, spec, area["name"])
    card = markers.get("card") or {}
    if card and card.get("area") in areas:
        _shots["ar_" + world_id] = _shot(map_data, areas[card["area"]], card, map_data["name"])
    elif areas:
        first = next(iter(areas))
        _shots["ar_" + world_id] = _shots["ar_%s_%s" % (world_id, first)]


def shot(key: str) -> Optional[Dict[str, Any]]:
    """The picture called ``key``: ``ar_<world>`` (its card) or
    ``ar_<world>_<area>`` (one place)."""
    if not key.startswith("ar_"):
        return None
    with _lock:
        if key in _shots:
            return _shots[key]
        world_id = None
        for candidate in sorted(WORLD_CLASSES, key=len, reverse=True):
            if key == "ar_" + candidate or key.startswith("ar_" + candidate + "_"):
                world_id = candidate
                break
        if world_id is None or world_id in _failed:
            return None
        try:
            _build(world_id)
        except Exception:
            import traceback
            traceback.print_exc()
            _failed.add(world_id)
            return None
        return _shots.get(key)
