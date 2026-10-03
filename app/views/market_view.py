"""The market, crates and keys, and the personal inventory."""
from __future__ import annotations

import time

from .. import db
from ..http import router as R
from ..http.router import Request
from ..models import (avatars, catalog, crates, economy, inventory, market,
                      notifications)
from .base import api_error, api_ok, login_required, render, router

# The market's aisles.  Hats are not one of them any more -- they come out of
# crates -- so the first aisle is the crates and the keys that open them.
MARKET_TABS = [("all", "Everything", "star"), ("stash", "Crates & Keys", "crate"),
               ("event", "Hallowed Harvest", "pumpkin"), ("usable", "Gear", "blade"),
               ("hair", "Hair", "hair"), ("face", "Faces", "face"),
               ("shirt", "Shirts", "shirt"), ("pants", "Pants", "pants"),
               ("belt", "Belts", "belt"), ("back", "Back", "wing")]

INVENTORY_TABS = [("all", "Everything"), ("stash", "Crates & Keys"), ("hat", "Hats"),
                  ("hair", "Hair"), ("face", "Faces"), ("shirt", "Shirts"),
                  ("pants", "Pants"), ("belt", "Belts"), ("back", "Back"),
                  ("usable", "Usables")]

# kept for anything that still imports the old name
SLOT_TABS = INVENTORY_TABS


def _owned_counts(uid: int):
    owned = {}
    for row in db.query("SELECT item_id, COUNT(*) AS n FROM inventory WHERE user_id=?"
                        " GROUP BY item_id", (uid,)):
        owned[row["item_id"]] = int(row["n"])
    return owned


@router.get("/market")
def market_page(req: Request):
    slot = req.query.get("slot", "all")
    sort = req.query.get("sort", "featured")
    term = req.query.get("q", "")
    events = crates.active_events()
    tabs = [t for t in MARKET_TABS if t[0] != "event" or events]
    if slot not in [t[0] for t in tabs]:
        slot = "all"
    items = market.listing(slot, sort, term)
    owned = _owned_counts(int(req.user["id"])) if req.user else {}
    stash = crates.stash_counts(int(req.user["id"])) if req.user else {}
    series = crates.all_series()
    offers = [dict(o, active=crates.series_active(crates.SERIES[o["series"]]),
                   value=sum(int(catalog.get(i)["price"]) * n
                             for i, n in o["contents"].items()))
              for o in crates.OFFERS]
    offers = [o for o in offers if o["active"]]
    spotlight = [catalog.get(i) for i in ("hat_hexed_witch", "hat_halo", "hat_lantern",
                                          "hat_tagalong_ghost", "hat_crown",
                                          "back_nightwing_cloak")]
    return render(req, "market.html", page_title="Market",
                  items=items, slot=slot, sort=sort, term=term, tabs=tabs,
                  owned=owned, stash=stash, series=series, offers=offers,
                  events=events, feed=crates.recent_openings(14),
                  crate_stats=crates.stats(), spotlight=[s for s in spotlight if s],
                  grades=crates.GRADES, tiers=catalog.TIERS,
                  effects=catalog.UNUSUAL_EFFECTS,
                  extra_scripts=["/static/js/ui/crates.js"])


@router.get("/inventory")
@login_required
def inventory_page(req: Request):
    uid = int(req.user["id"])
    slot = req.query.get("slot", "all")
    if slot not in [t[0] for t in INVENTORY_TABS]:
        slot = "all"
    owned = inventory.list_for_user(uid)
    # Crates and keys stack: one card per kind with a count, rather than a
    # wall of identical boxes.  They lead "Everything", so a new crate is never
    # buried, and each series sits key-then-crate, the order you use them in.
    stacks: dict = {}
    for it in owned:
        if not it["stash"]:
            continue
        stack = stacks.get(it["item_id"])
        if stack is None:
            stack = stacks[it["item_id"]] = db.AttrDict(it)
            stack["ids"] = []
        stack["ids"].append(int(it["inv_id"]))
    numbers = {s["id"]: s["number"] for s in crates.SERIES.values()}

    def _stack_order(st):
        series = st["series"] or (st["opens"] or [""])[0]
        return (numbers.get(series, 99), 0 if st["slot"] == "key" else 1, st["item_id"])

    stash_cards = sorted(stacks.values(), key=_stack_order)
    for st in stash_cards:
        st["ids"].sort()
        st["count"] = len(st["ids"])
        st["series_key"] = st["series"] or (st["opens"] or [""])[0]
    if slot == "stash":
        items = []
    elif slot == "all":
        items = [i for i in owned if not i["stash"]]
    else:
        items = [i for i in owned if i["slot"] == slot]
        stash_cards = []
    raw = avatars.raw_avatar(uid)
    equipped_ids = set(raw["equipped"].values())
    hotbar_ids = set(x for x in raw["hotbar"] if x)
    stash = crates.stash_counts(uid)
    return render(req, "inventory.html", page_title="Inventory",
                  items=items, stash_cards=stash_cards, slot=slot, tabs=INVENTORY_TABS,
                  summary=inventory.summary(uid),
                  equipped=equipped_ids, hotbar=hotbar_ids,
                  tiers=catalog.TIERS, ledger=economy.history(uid, 12),
                  stash=stash, series=crates.all_series(),
                  series_by_id={s["id"]: s for s in crates.all_series()},
                  grades=crates.GRADES,
                  extra_scripts=["/static/js/ui/crates.js"])


@router.get("/inventory/<username>")
def inventory_of(req: Request, username: str = ""):
    from ..models import users
    target = users.get_by_username(username)
    if target is None:
        return R.not_found("No such player.")
    uid = int(target["id"])
    viewer = int(req.user["id"]) if req.user else 0
    # Same privacy rule the profile page applies, enforced here too so the
    # direct URL is not a way around it.
    if not users.can_view(target, "inventory", viewer,
                          bool(req.user and req.user["is_admin"])):
        return render(req, "inventory_public.html", target=target, items=[],
                      summary=inventory.summary(uid), tiers=catalog.TIERS,
                      private=True)
    return render(req, "inventory_public.html", target=target,
                  items=inventory.list_for_user(uid), private=False,
                  summary=inventory.summary(uid), tiers=catalog.TIERS)


# ------------------------------------------------------------------ buying
@router.post("/api/market/buy")
@login_required
def buy(req: Request):
    data = req.data()
    item_id = str(data.get("item_id", ""))
    if not db.rate_limit("buy:%d" % int(req.user["id"]), 60, 60):
        return api_error("Slow down a little -- the till is still ringing.")
    try:
        result = market.purchase(int(req.user["id"]), item_id, data.get("qty", 1))
    except market.MarketError as exc:
        return api_error(str(exc))
    return api_ok(**result)


@router.post("/api/market/bundle")
@login_required
def buy_bundle(req: Request):
    try:
        result = crates.buy_offer(int(req.user["id"]), str(req.data().get("offer_id", "")))
    except crates.CrateError as exc:
        return api_error(str(exc))
    return api_ok(**result)


@router.post("/api/market/sell")
@login_required
def sell(req: Request):
    try:
        inv_id = int(req.data().get("inv_id", 0))
    except (TypeError, ValueError):
        return api_error("Bad item.")
    try:
        result = market.sell_back(int(req.user["id"]), inv_id)
    except market.MarketError as exc:
        return api_error(str(exc))
    return api_ok(balance=economy.balance(int(req.user["id"])), **result)


# ------------------------------------------------------------------ crates
@router.get("/api/crates/contents")
def crate_contents(req: Request):
    series = str(req.query.get("series", ""))
    if series not in crates.SERIES:
        crate = crates.CRATE_SERIES.get(series) or crates.KEY_SERIES.get(series)
        series = crate["id"] if crate else ""
    try:
        return api_ok(**crates.contents(series))
    except crates.CrateError as exc:
        return api_error(str(exc), 404)


@router.get("/api/crates/stash")
@login_required
def crate_stash(req: Request):
    uid = int(req.user["id"])
    return api_ok(stash=crates.stash(uid), counts=crates.stash_counts(uid),
                  series=crates.all_series())


@router.post("/api/crates/open")
@login_required
def crate_open(req: Request):
    data = req.data()
    uid = int(req.user["id"])
    if not db.rate_limit("open:%d" % uid, 40, 60):
        return api_error("Let the last one finish opening first.")
    try:
        crate_inv = int(data.get("crate_inv", 0) or 0)
        key_inv = int(data.get("key_inv", 0) or 0)
    except (TypeError, ValueError):
        return api_error("Bad crate or key.")
    # Either half may be left for the server to pick: "open one of these" is
    # what the quick-open buttons ask for.
    if not crate_inv or not key_inv:
        stash = crates.stash(uid)
        series = str(data.get("series", ""))
        if crate_inv and not series:
            row = inventory.get_row(uid, crate_inv)
            found = crates.CRATE_SERIES.get(row["item_id"]) if row else None
            series = found["id"] if found else ""
        if key_inv and not series:
            row = inventory.get_row(uid, key_inv)
            item = catalog.get(row["item_id"]) if row else None
            series = ((item or {}).get("opens") or [""])[0]
        held = stash.get(series) or {"crates": [], "keys": []}
        crate_inv = crate_inv or (held["crates"][0] if held["crates"] else 0)
        key_inv = key_inv or (held["keys"][0] if held["keys"] else 0)
        if not crate_inv:
            return api_error("You have no crate for that key.")
        if not key_inv:
            return api_error("You need a key for that crate.")
    try:
        result = crates.open_crate(uid, crate_inv, key_inv)
    except crates.CrateError as exc:
        return api_error(str(exc))
    return api_ok(balance=economy.balance(uid), **result)


@router.get("/api/crates/feed")
def crate_feed(req: Request):
    try:
        limit = max(1, min(40, int(req.query.get("limit", 14))))
    except ValueError:
        limit = 14
    return api_ok(feed=crates.recent_openings(limit), stats=crates.stats(),
                  at=int(time.time()))


# --------------------------------------------------------------- catalogue
@router.get("/api/catalog")
def catalog_json(req: Request):
    return api_ok(items=market.catalog_listing(),
                  tiers=catalog.TIERS, effects=catalog.UNUSUAL_EFFECTS,
                  grades=crates.GRADES,
                  palette=catalog.BODY_PALETTE,
                  random_palette=catalog.RANDOM_PALETTE)


@router.get("/api/inventory")
@login_required
def inventory_json(req: Request):
    uid = int(req.user["id"])
    return api_ok(items=inventory.list_for_user(uid),
                  summary=inventory.summary(uid),
                  balance=economy.balance(uid),
                  stash=crates.stash_counts(uid))


# ----------------------------------------------------------- notifications
@router.post("/api/notifications/seen")
@login_required
def notes_seen(req: Request):
    ids = req.data().get("ids") or []
    if not isinstance(ids, list):
        ids = []
    return api_ok(marked=notifications.mark_seen(int(req.user["id"]), ids))


@router.get("/api/notifications")
@login_required
def notes_recent(req: Request):
    return api_ok(notes=notifications.recent(int(req.user["id"]), 20))
