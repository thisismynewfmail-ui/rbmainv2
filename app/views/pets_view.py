"""Pets: the market's Pets shelf, the pet editor, the Pet Zone and their API.

Buying goes through the market's own till (/api/market/buy), which knows a
pet is one per species and sets the first one you adopt following you; this
module is everything after that -- naming her, colouring her, picking her
persona and dressing her (app/models/pets.py), and looking after her in the
Pet Zone (app/models/pet_care.py).
"""
from __future__ import annotations

from .. import db
from ..http import router as R
from ..http.router import Request
from ..models import catalog, crates, economy, pet_care, pets
from .base import api_error, api_ok, login_required, render, router


def _uid(req: Request) -> int:
    return int(req.user["id"]) if req.user else 0


def _chosen(req: Request, mine, active: int) -> int:
    """The pet a page is about: ?pet= if it is one of yours, else the active
    pet, else the first."""
    want = req.query.get("pet", "")
    try:
        chosen = int(want) if want else (active or mine[0]["inv_id"])
    except ValueError:
        chosen = active or mine[0]["inv_id"]
    if not any(p["inv_id"] == chosen for p in mine):
        chosen = mine[0]["inv_id"]
    return chosen


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
    chosen = _chosen(req, mine, active)
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


# ----------------------------------------------------------------- Pet Zone
@router.get("/pet-zone")
@login_required
def pet_zone(req: Request):
    """The Pet Zone: her room, and looking after her -- the active pet
    unless ?pet= picks another of yours.  Like Edit Pet, it is only for
    someone with a pet; anybody else goes and meets some."""
    uid = _uid(req)
    mine = pets.all_payloads(uid)
    if not mine:
        return R.redirect("/market/pets")
    active = pets.active_id(uid)
    chosen = _chosen(req, mine, active)
    current = next(m for m in mine if m["inv_id"] == chosen)
    moods = pet_care.summary(uid)
    boot = {
        "pets": mine, "active": active, "chosen": chosen, "user": req.user["username"],
        "care": pet_care.state(uid, chosen), "summary": moods,
        "species": {k: {"name": v["name"], "signature": v["signature"]}
                    for k, v in pets.SPECIES.items()},
    }
    boot.update(pet_care.catalogue())
    return render(req, "pet_zone.html", page_title="Pet Zone",
                  boot=boot, mine=mine, current=current, chosen=chosen, active=active,
                  moods=moods, care=boot["care"], need_labels=pet_care.NEED_LABELS,
                  needs=pet_care.NEEDS, care_actions=boot["actions"],
                  treats=boot["treats"], toys=boot["toys"], milestones=pet_care.MILESTONES,
                  species=pets.SPECIES,
                  extra_scripts=["/static/js/engine/audio.js", "/static/js/ui/pets_shop.js",
                                 "/static/js/ui/pet_zone.js"])


@router.get("/api/pets/care")
@login_required
def pet_care_json(req: Request):
    """How one of your pets is doing (?pet=, else the active one)."""
    uid = _uid(req)
    want = req.query.get("pet", "") or pets.active_id(uid)
    try:
        return api_ok(care=pet_care.state(uid, int(want or 0)))
    except ValueError:
        return api_error("Unknown pet.")
    except pet_care.CareError as exc:
        return api_error(str(exc), exc.status)


@router.post("/api/pets/care")
@login_required
def pet_care_act(req: Request):
    """Do something for one of your pets: {inv_id, action, item?}.  A refusal
    (she is full, asleep, still busy) answers with her state, so the page can
    show her saying no rather than an error."""
    uid = _uid(req)
    if not db.rate_limit("petcare:%d" % uid, *pet_care.RATE_LIMIT):
        return api_error("Slow down -- she can only keep up with so much.", 429)
    data = req.data()
    try:
        out = pet_care.act(uid, data.get("inv_id"), data.get("action"), data.get("item"))
    except pet_care.CareError as exc:
        payload = {"ok": False, "error": str(exc), "reason": exc.code}
        if exc.retry_in:
            payload["retry_in"] = exc.retry_in
        if exc.care:
            payload["care"] = exc.care
        return R.json_response(payload, exc.status)
    return api_ok(**out)
