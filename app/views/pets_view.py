"""Pets: the market's Pets shelf, the pet editor and their API.

Buying goes through the market's own till (/api/market/buy), which knows a
pet is one per species and sets the first one you adopt following you; this
module is everything after that -- naming her, colouring her, picking her
persona and dressing her (app/models/pets.py).
"""
from __future__ import annotations

from .. import db
from ..http import router as R
from ..http.router import Request
from ..models import catalog, crates, economy, pets
from .base import api_error, api_ok, login_required, render, router


def _uid(req: Request) -> int:
    return int(req.user["id"]) if req.user else 0


@router.get("/market/pets")
def pets_shelf(req: Request):
    """The Pets shelf: the five pets on top, the wardrobe underneath."""
    uid = _uid(req)
    shelf = pets.shelf(uid or None)
    slot = req.query.get("slot", "")
    if slot not in pets.COSMETIC_SLOTS:
        slot = pets.COSMETIC_SLOTS[0]
    return render(req, "market_pets.html", page_title="Pets",
                  shelf=shelf, slot=slot, tags=pets.tag_list(),
                  grades=crates.GRADES, color_labels=pets.COLOR_LABELS,
                  extra_scripts=["/static/js/ui/crates.js", "/static/js/ui/pets_shop.js"])


@router.get("/pet")
@login_required
def pet_editor(req: Request):
    """Edit Pet: choose which pet follows you, then name, colour, persona and
    dress her.  Nobody with no pet has anything to edit, so they go and
    meet some."""
    uid = _uid(req)
    mine = pets.all_payloads(uid)
    if not mine:
        return R.redirect("/market/pets")
    active = pets.active_id(uid)
    want = req.query.get("pet", "")
    try:
        chosen = int(want) if want else (active or mine[0]["inv_id"])
    except ValueError:
        chosen = active or mine[0]["inv_id"]
    if not any(p["inv_id"] == chosen for p in mine):
        chosen = mine[0]["inv_id"]
    owned = pets.cosmetics_owned(uid)
    by_slot = {slot: [c for c in owned if c["slot"] == slot] for slot in pets.COSMETIC_SLOTS}
    raw = pets.owned(uid)
    boot = {
        "pets": raw, "cosmetics": owned, "active": active, "chosen": chosen,
        "tags": pets.tag_list(), "maxTags": pets.MAX_TAGS, "nameMax": pets.NAME_MAX,
        "colorKeys": pets.COLOR_KEYS, "colorLabels": pets.COLOR_LABELS,
        "species": {k: {"name": v["name"], "colors": v["colors"], "tags": v["tags"],
                        "signature": v["signature"]} for k, v in pets.SPECIES.items()},
        "slots": pets.COSMETIC_SLOTS, "slotLabels": pets.SHELF_LABELS,
    }
    current = next(p for p in raw if p["inv_id"] == chosen)
    return render(req, "pet_editor.html", page_title="Edit Pet",
                  boot=boot, mine=mine, current=current, chosen=chosen, active=active,
                  current_pet=next(m for m in mine if m["inv_id"] == chosen),
                  by_slot=by_slot, slots=pets.COSMETIC_SLOTS, slot_labels=pets.SHELF_LABELS,
                  color_keys=pets.COLOR_KEYS, color_labels=pets.COLOR_LABELS,
                  species=pets.SPECIES, tag_options=pets.tag_list(), max_tags=pets.MAX_TAGS,
                  name_max=pets.NAME_MAX, palette=catalog.BODY_PALETTE,
                  extra_scripts=["/static/js/ui/pets_shop.js", "/static/js/ui/pet_editor.js"])


@router.get("/api/pets")
@login_required
def pets_json(req: Request):
    uid = _uid(req)
    return api_ok(pets=pets.all_payloads(uid), active=pets.active_id(uid),
                  cosmetics=pets.cosmetics_owned(uid), balance=economy.balance(uid))


@router.post("/api/pets/save")
@login_required
def pets_save(req: Request):
    uid = _uid(req)
    if not db.rate_limit("petsave:%d" % uid, 120, 60):
        return api_error("Give her a moment to get changed.")
    data = req.data()
    try:
        inv_id = int(data.get("inv_id") or 0)
    except (TypeError, ValueError):
        return api_error("Unknown pet.")
    try:
        pet = pets.save(uid, inv_id, name=data.get("name"), colors=data.get("colors"),
                        tags=data.get("tags"), equipped=data.get("equipped"))
    except pets.PetError as exc:
        return api_error(str(exc))
    names = {c["inv_id"]: c["item_id"] for c in pets.cosmetics_owned(uid)}
    return api_ok(pet=pets.describe(pet, names), active=pets.active_id(uid))


@router.post("/api/pets/active")
@login_required
def pets_active(req: Request):
    uid = _uid(req)
    data = req.data()
    try:
        inv_id = int(data.get("inv_id") or 0)
    except (TypeError, ValueError):
        return api_error("Unknown pet.")
    try:
        active = pets.set_active(uid, inv_id)
    except pets.PetError as exc:
        return api_error(str(exc))
    return api_ok(active=active, pet=pets.payload(uid))
