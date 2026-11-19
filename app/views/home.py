"""Home page, search and help."""
from __future__ import annotations

from urllib.parse import urlencode

import time

from .. import db
from ..http import router as R
from ..http.router import Request
from ..game import registry as game_registry
from ..models import avatars, events, users, worlds
from ..social import feed, friends, posts
from .base import ago, render, router

# How "Jump back in" can be sorted (the menu at the top right of it).  The
# choice is kept in a cookie, so the page comes back sorted the same way.
JUMP_SORTS = [
    ("recent", "Recently played"),
    ("playtime", "Most play time"),
    ("newest", "Newest added"),
    ("popular", "Most popular"),
    ("rated", "Top rated"),
    ("playing", "Playing now"),
    ("favourites", "Favourites"),
    ("name", "A to Z"),
]
JUMP_KEYS = {key for key, _label in JUMP_SORTS}
JUMP_COOKIE = "bh_jump"
JUMP_DEFAULT = "recent"


def _played(uid: int):
    """When this player was last in each world, and how long they have
    played there: {world_id: (last_visit, seconds)}."""
    out = {}
    for row in db.query("SELECT world_id, MAX(created_at) AS last, SUM(seconds) AS secs"
                        " FROM world_visits WHERE user_id=? GROUP BY world_id", (uid,)):
        out[row["world_id"]] = (int(row["last"] or 0), int(row["secs"] or 0))
    return out


def _span(seconds: int) -> str:
    minutes = max(1, int(seconds) // 60)
    if minutes < 60:
        return "%d min played" % minutes
    hours, rest = divmod(minutes, 60)
    return ("%dh %dm played" % (hours, rest)) if rest else ("%dh played" % hours)


def sort_jump(rows, key: str):
    """Sort the world rows (each already carrying the player's own numbers)
    for "Jump back in", and give each card the line that explains its place."""
    def rated(r):
        return (-int(r["stats"]["rating"]), -int(r["stats"]["rating_votes"]), r["order"])
    keys = {
        "recent": lambda r: (-r["last_played"], r["order"]),
        "playtime": lambda r: (-r["playtime"], r["order"]),
        "newest": lambda r: (-int(r["added"].replace("-", "") or 0), r["order"]),
        "popular": lambda r: (-int(r["stats"]["visits"]), r["order"]),
        "rated": rated,
        "playing": lambda r: (-int(r["status"]["players"]), r["order"]),
        "favourites": lambda r: (r["fav"] < 0, r["fav"] if r["fav"] >= 0 else 0, r["order"]),
        "name": lambda r: (r["world"]["name"].lower(), r["order"]),
    }
    rows.sort(key=keys.get(key, keys[JUMP_DEFAULT]))
    for r in rows:
        r["sortnote"] = jump_note(r, key)
    return rows


def jump_note(r, key: str) -> str:
    if key == "recent":
        return ("Played " + ago(r["last_played"])) if r["last_played"] else ""
    if key == "playtime":
        return _span(r["playtime"]) if r["playtime"] else ""
    if key == "newest":
        if not r["added"]:
            return ""
        try:
            day = time.strptime(r["added"], "%Y-%m-%d")
            return "Added " + time.strftime("%b %d", day).replace(" 0", " ")
        except ValueError:
            return ""
    if key == "popular":
        return "{:,} visits".format(int(r["stats"]["visits"]))
    if key == "rated":
        return ("%d%% liked" % int(r["stats"]["rating"])) if r["stats"]["rating_votes"] else "Not rated yet"
    if key == "favourites":
        return "\u2605 Favourite" if r["fav"] >= 0 else ""
    return ""


@router.get("/")
def home(req: Request):
    world_rows = []
    for world in worlds.all_worlds():
        status = game_registry.world_status(world["id"])
        stats = worlds.stats(world["id"])
        world_rows.append({"world": world, "status": status, "stats": stats})
    spotlight = events.current()
    if spotlight["id"] == "world_spotlight" and world_rows:
        # point the world spotlight at whichever world is busiest right now
        featured = max(world_rows, key=lambda r: (r["status"]["players"],
                                                  r["stats"]["visits"]))
        spotlight = dict(spotlight)
        spotlight["title"] = "World Spotlight: %s" % featured["world"]["name"]
        spotlight["href"] = "/worlds/%s" % featured["world"]["id"]
        spotlight["cta"] = "Open %s" % featured["world"]["name"]
    if req.user is None:
        return render(req, "landing.html", worlds=world_rows,
                      site_stats=feed.stats_snapshot(),
                      recent_users=users.recent(10),
                      spotlight=spotlight,
                      spotlight_left=events.seconds_left(),
                      upcoming=events.upcoming(2))
    uid = int(req.user["id"])
    # "Jump back in", sorted the way this player chose (the ?jump= of the
    # menu without JavaScript, otherwise the cookie the menu leaves)
    asked = (req.query.get("jump") or "").strip()
    jump = asked if asked in JUMP_KEYS else (req.cookies.get(JUMP_COOKIE) or "").strip()
    if jump not in JUMP_KEYS:
        jump = JUMP_DEFAULT
    played = _played(uid)
    own = worlds.player_stats(uid)
    favs = worlds.favourites_of(uid)
    for index, row in enumerate(world_rows):
        wid = row["world"]["id"]
        last, secs = played.get(wid, (0, 0))
        row["order"] = index
        row["last_played"] = last
        row["playtime"] = max(int((own["worlds"].get(wid) or {}).get("playtime") or 0), secs)
        row["added"] = str(row["world"].get("added") or "")
        row["fav"] = favs.index(wid) if wid in favs else -1
    sort_jump(world_rows, jump)
    # The spotlight banner is a greeting, not furniture: it is claimed once
    # per sign-in and then stays gone until the next one, so reloading the
    # home page (or coming back to it from a profile) does not re-serve it.
    show_spotlight = users.claim_spotlight(
        req.session["token"] if req.session else "")
    from ..family import guard as family_guard
    held = {row["username"] for row in family_guard.waiting_for(uid)}
    requests = friends.incoming_requests(uid)[:5]
    for row in requests:
        row["waiting"] = row["username"] in held
    resp = render(
        req, "home.html",
        show_spotlight=show_spotlight,
        worlds=world_rows,
        jump=jump,
        jump_sorts=JUMP_SORTS,
        friends_list=friends.list_friends(uid, 12),
        friend_count=friends.count_friends(uid),
        requests=requests,
        activity=feed.recent_activity(14),
        site_stats=feed.stats_snapshot(),
        online=users.online_users(12),
        favourites=favs,
        avatar=avatars.descriptor(uid, req.user["username"]),
        stats=own,
        spotlight=spotlight,
        spotlight_left=events.seconds_left(),
        upcoming=events.upcoming(2),
    )
    if asked in JUMP_KEYS:
        resp.set_cookie(JUMP_COOKIE, asked, max_age=60 * 60 * 24 * 365)
    return resp


# There was a People tab here once (/users, the newest sixty accounts); the
# Pet Zone took its place in the navigation and the header search finds
# players.  Old links -- bookmarks, the "Meet the Crew" spotlight in
# somebody's history -- land on the search, with their ?q= intact.
@router.get("/users")
def people(req: Request):
    term = (req.query.get("q") or "").strip()
    return R.redirect("/search?" + urlencode({"q": term}) if term else "/search", 301)


# An empty search (the header box submitted blank, or one of those old
# People links) shows the newest arrivals rather than nothing at all.
NEWEST_LIMIT = 24


@router.get("/search")
def search(req: Request):
    term = (req.query.get("q") or "").strip()
    from ..models import market
    items = market.listing(None, "featured", term)[:24] if term else []
    people_rows = users.search(term, 12) if term else []
    world_rows = [w for w in worlds.all_worlds()
                  if term.lower() in w["name"].lower()] if term else []
    return render(req, "search.html", term=term, items=items,
                  people=people_rows, worlds=world_rows,
                  newest=[] if term else users.recent(NEWEST_LIMIT))


@router.get("/help")
def help_page(req: Request):
    return render(req, "help.html", page_title="Help")
