"""The avatar base system: body colours, cosmetic slots and the hotbar.

The whole system is slot driven so new slots or new items only need a
catalogue entry.  Everything that leaves this module is a *descriptor*: a
plain, fully resolved dict the renderer (browser) and the game hosts consume
without needing database access.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from .. import db, security
from . import badges, catalog, inventory


class AvatarError(Exception):
    pass


def _now() -> int:
    return int(time.time())


def _load_json(raw: Any, fallback: Any) -> Any:
    try:
        value = json.loads(raw)
        if isinstance(value, type(fallback)):
            return value
    except Exception:
        pass
    return fallback


def raw_avatar(user_id: int) -> Dict[str, Any]:
    row = db.query_one("SELECT * FROM avatars WHERE user_id=?", (user_id,))
    if row is None:
        db.execute("INSERT OR IGNORE INTO avatars(user_id,colors,equipped,hotbar,"
                   "body_type,updated_at) VALUES(?,?,?,?,?,?)",
                   (user_id, json.dumps(catalog.DEFAULT_COLORS), "{}", "[]",
                    catalog.DEFAULT_BODY_TYPE, _now()))
        row = db.query_one("SELECT * FROM avatars WHERE user_id=?", (user_id,))
    colors = _load_json(row["colors"], {})
    equipped = _load_json(row["equipped"], {})
    hotbar = _load_json(row["hotbar"], [])
    merged = dict(catalog.DEFAULT_COLORS)
    for part in catalog.BODY_PARTS:
        value = colors.get(part)
        if isinstance(value, str) and security.valid_color(value):
            merged[part] = value
    if "hips" not in colors:
        # The hips were drawn in the left leg's colour before they became a
        # part of their own, so an avatar saved before that keeps exactly the
        # character it had.  It sticks the next time anything is saved.
        legacy = colors.get("left_leg")
        if isinstance(legacy, str) and security.valid_color(legacy):
            merged["hips"] = legacy
    hotbar = [int(x) if isinstance(x, (int, float)) and int(x) > 0 else 0
              for x in hotbar][:catalog.HOTBAR_SIZE]
    hotbar += [0] * (catalog.HOTBAR_SIZE - len(hotbar))
    clean_equipped: Dict[str, int] = {}
    for slot in catalog.SLOTS:
        value = equipped.get(slot)
        if isinstance(value, (int, float)) and int(value) > 0:
            clean_equipped[slot] = int(value)
    body_type = catalog.normalize_body_type(
        row["body_type"] if "body_type" in row.keys() else "")
    return {"user_id": user_id, "colors": merged, "equipped": clean_equipped,
            "hotbar": hotbar, "body_type": body_type,
            "updated_at": row["updated_at"]}


def _save(user_id: int, colors: Dict[str, str], equipped: Dict[str, int],
          hotbar: List[int], body_type: Optional[str] = None) -> None:
    if body_type is None:
        body_type = raw_avatar(user_id)["body_type"]
    body_type = catalog.normalize_body_type(body_type)
    db.execute("UPDATE avatars SET colors=?, equipped=?, hotbar=?, body_type=?,"
               " updated_at=? WHERE user_id=?",
               (json.dumps(colors, separators=(",", ":")),
                json.dumps(equipped, separators=(",", ":")),
                json.dumps(hotbar, separators=(",", ":")), body_type,
                _now(), user_id))


def set_body_type(user_id: int, body_type: str) -> str:
    """Switch between the two rigs (male or female).

    Nothing else changes: both rigs share the same head-top hat anchor, the
    same eye height and the same hitbox, so every hat, face and outfit
    already owned carries straight over.
    """
    body_type = str(body_type or "").strip().lower()
    if body_type not in catalog.BODY_TYPES:
        # A retired build posted by an old page is honoured rather than
        # rejected; anything else is simply not a build.
        if body_type not in catalog.RETIRED_BODY_TYPES:
            raise AvatarError("Unknown body type.")
        body_type = catalog.normalize_body_type(body_type)
    avatar = raw_avatar(user_id)
    _save(user_id, avatar["colors"], avatar["equipped"], avatar["hotbar"],
          body_type)
    return body_type


def apply_defaults(user_id: int) -> None:
    """Equip the free starter cosmetics and fill the default hotbar."""
    avatar = raw_avatar(user_id)
    equipped = dict(avatar["equipped"])
    for slot, item_id in catalog.DEFAULT_EQUIPPED.items():
        if not item_id or slot in equipped:
            continue
        row = inventory.first_of(user_id, item_id)
        if row:
            equipped[slot] = row["id"]
    hotbar = list(avatar["hotbar"])
    for index, item_id in enumerate(catalog.DEFAULT_HOTBAR):
        if index >= catalog.HOTBAR_SIZE or not item_id or hotbar[index]:
            continue
        row = inventory.first_of(user_id, item_id)
        if row:
            hotbar[index] = row["id"]
    _save(user_id, avatar["colors"], equipped, hotbar)


# ------------------------------------------------------------------- mutation

def set_colors(user_id: int, colors: Dict[str, str]) -> Dict[str, str]:
    avatar = raw_avatar(user_id)
    merged = dict(avatar["colors"])
    for part, value in (colors or {}).items():
        if part not in catalog.BODY_PARTS:
            continue
        if not isinstance(value, str) or not security.valid_color(value):
            raise AvatarError("Invalid colour for %s." % part)
        merged[part] = value.lower()
    _save(user_id, merged, avatar["equipped"], avatar["hotbar"])
    return merged


def equip(user_id: int, slot: str, inv_id: int) -> Dict[str, Any]:
    """Equip an owned copy into a cosmetic slot. ``inv_id`` 0 clears the slot."""
    if slot not in catalog.SLOTS:
        raise AvatarError("Unknown slot.")
    avatar = raw_avatar(user_id)
    equipped = dict(avatar["equipped"])
    inv_id = int(inv_id or 0)
    if inv_id <= 0:
        equipped.pop(slot, None)
    else:
        row = inventory.get_row(user_id, inv_id)
        if row is None:
            raise AvatarError("You do not own that item.")
        item = catalog.get(row["item_id"])
        if item is None:
            raise AvatarError("That item no longer exists.")
        if item["slot"] != slot:
            raise AvatarError("A %s cannot go in the %s slot."
                              % (item["slot"], slot))
        equipped[slot] = inv_id
    _save(user_id, avatar["colors"], equipped, avatar["hotbar"])
    return equipped


def set_hotbar_slot(user_id: int, index: int, inv_id: int) -> List[int]:
    index = int(index)
    if not (0 <= index < catalog.HOTBAR_SIZE):
        raise AvatarError("Hotbar slot out of range.")
    avatar = raw_avatar(user_id)
    hotbar = list(avatar["hotbar"])
    inv_id = int(inv_id or 0)
    if inv_id <= 0:
        hotbar[index] = 0
    else:
        row = inventory.get_row(user_id, inv_id)
        if row is None:
            raise AvatarError("You do not own that item.")
        item = catalog.get(row["item_id"])
        if item is None or item["slot"] != "usable":
            raise AvatarError("Only usable items go on the hotbar.")
        for other in range(catalog.HOTBAR_SIZE):
            if other != index and hotbar[other] == inv_id:
                hotbar[other] = 0
        hotbar[index] = inv_id
    _save(user_id, avatar["colors"], avatar["equipped"], hotbar)
    return hotbar


def unequip_missing(user_id: int) -> None:
    """Drop references to inventory rows that no longer exist."""
    avatar = raw_avatar(user_id)
    equipped = {slot: inv for slot, inv in avatar["equipped"].items()
                if inventory.get_row(user_id, inv)}
    hotbar = [inv if inv and inventory.get_row(user_id, inv) else 0
              for inv in avatar["hotbar"]]
    if equipped != avatar["equipped"] or hotbar != avatar["hotbar"]:
        _save(user_id, avatar["colors"], equipped, hotbar)


# ----------------------------------------------------------------- descriptor

def descriptor(user_id: int, username: Optional[str] = None) -> Dict[str, Any]:
    """Fully resolved avatar used by every renderer and by the game hosts."""
    avatar = raw_avatar(user_id)
    if username is None:
        username = db.scalar("SELECT username FROM users WHERE id=?",
                             (user_id,), "Player")
    items: Dict[str, Any] = {}
    for slot, inv_id in avatar["equipped"].items():
        row = inventory.get_row(user_id, inv_id)
        if row is None:
            continue
        item = catalog.get(row["item_id"])
        if item is None or item["slot"] != slot:
            continue
        items[slot] = _item_payload(item, row)
    hotbar: List[Optional[Dict[str, Any]]] = []
    for inv_id in avatar["hotbar"]:
        entry = None
        if inv_id:
            row = inventory.get_row(user_id, inv_id)
            if row:
                item = catalog.get(row["item_id"])
                if item and item["slot"] == "usable":
                    entry = _item_payload(item, row)
        hotbar.append(entry)
    return {
        "user_id": user_id,
        "username": username,
        "colors": avatar["colors"],
        "body_type": avatar["body_type"],
        "items": items,
        "hotbar": hotbar,
        # the badge pinned to the chest, with its model, or None
        "badge": badges.worn_payload(user_id),
        "updated_at": avatar["updated_at"],
    }


def _item_payload(item: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
    tier = catalog.TIERS.get(row.get("tier", "normal"), catalog.TIERS["normal"])
    effect_id = row.get("effect") or ""
    payload = {
        "inv_id": row["id"],
        "item_id": item["id"],
        "name": item["name"],
        "slot": item["slot"],
        "tier": tier["id"],
        "tier_color": tier["color"],
        "effect": effect_id,
        "data": item.get("data", {}),
    }
    if effect_id and effect_id in catalog.UNUSUAL_EFFECTS:
        payload["effect_def"] = catalog.UNUSUAL_EFFECTS[effect_id]
    return payload


# ------------------------------------------------------- compact form
# A descriptor carries every equipped item's model -- its parts -- which is
# what every renderer needs and far more than a *reference* to the avatar
# needs.  The game join ticket rides in the socket URL, and a full descriptor
# with a sculpted hat, wings and two event weapons on the hotbar is past ten
# kilobytes: long enough that the host's request line cut it off and the
# ticket's signature no longer matched.  So the ticket carries this compact
# form (what is worn and held, by id) and the host rebuilds the rest from the
# same catalogue with expand().

_REF_KEYS = ("inv_id", "item_id", "tier", "effect")


def _ref(entry: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not entry:
        return None
    return {k: entry.get(k) for k in _REF_KEYS}


def compact(descriptor: Dict[str, Any]) -> Dict[str, Any]:
    """The descriptor with each item reduced to its id, copy, tier and effect."""
    out = dict(descriptor)
    out["items"] = {slot: _ref(entry) for slot, entry in
                    (descriptor.get("items") or {}).items() if entry}
    out["hotbar"] = [_ref(entry) for entry in descriptor.get("hotbar") or []]
    badge = descriptor.get("badge")
    if isinstance(badge, dict):
        out["badge"] = {k: badge.get(k) for k in
                        ("id", "name", "level", "tier", "tier_label", "rank")}
    return out


def _expand_entry(entry: Any, slot: Optional[str]) -> Optional[Dict[str, Any]]:
    if not isinstance(entry, dict):
        return None
    if entry.get("data") is not None:
        return entry                      # already whole
    item = catalog.get(str(entry.get("item_id", "")))
    if item is None or (slot is not None and item["slot"] != slot):
        return None
    tier = entry.get("tier") if entry.get("tier") in catalog.TIERS else "normal"
    effect = entry.get("effect") if entry.get("effect") in catalog.UNUSUAL_EFFECTS else ""
    return _item_payload(item, {"id": int(entry.get("inv_id") or 0), "tier": tier,
                                "effect": effect})


def expand(descriptor: Dict[str, Any]) -> Dict[str, Any]:
    """Undo compact(): rebuild each item (and the worn badge) from the
    catalogue.  A whole descriptor passes through unchanged."""
    if not isinstance(descriptor, dict):
        return default_descriptor()
    out = dict(descriptor)
    items = {}
    for slot, entry in (descriptor.get("items") or {}).items():
        whole = _expand_entry(entry, slot)
        if whole is not None:
            items[slot] = whole
    out["items"] = items
    hotbar = [_expand_entry(entry, "usable") for entry in descriptor.get("hotbar") or []]
    hotbar += [None] * (catalog.HOTBAR_SIZE - len(hotbar))
    out["hotbar"] = hotbar[:catalog.HOTBAR_SIZE]
    badge = descriptor.get("badge")
    if isinstance(badge, dict) and not badge.get("parts") and badge.get("id") in badges.BADGES:
        badge = dict(badge)
        badge["parts"] = badges.model(str(badge["id"]), int(badge.get("level") or 1))
        out["badge"] = badge
    return out


def default_descriptor(username: str = "Guest") -> Dict[str, Any]:
    face = catalog.get("face_smile")
    return {
        "user_id": 0,
        "username": username,
        "colors": dict(catalog.DEFAULT_COLORS),
        "body_type": catalog.DEFAULT_BODY_TYPE,
        "items": {"face": {"inv_id": 0, "item_id": "face_smile",
                           "name": "Smile", "slot": "face", "tier": "normal",
                           "tier_color": "#e8b71a", "effect": "",
                           "data": face["data"] if face else {}}},
        "hotbar": [None] * catalog.HOTBAR_SIZE,
        "updated_at": 0,
    }
