"""Home page, search and help."""
from __future__ import annotations

from urllib.parse import urlencode

from ..http import router as R
from ..http.router import Request
from ..game import registry as game_registry
from ..models import avatars, events, users, worlds
from ..social import feed, friends, posts
from .base import render, router


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
    # The spotlight banner is a greeting, not furniture: it is claimed once
    # per sign-in and then stays gone until the next one, so reloading the
    # home page (or coming back to it from a profile) does not re-serve it.
    show_spotlight = users.claim_spotlight(
        req.session["token"] if req.session else "")
    return render(
        req, "home.html",
        show_spotlight=show_spotlight,
        worlds=world_rows,
        friends_list=friends.list_friends(uid, 12),
        friend_count=friends.count_friends(uid),
        requests=friends.incoming_requests(uid)[:5],
        activity=feed.recent_activity(14),
        site_stats=feed.stats_snapshot(),
        online=users.online_users(12),
        favourites=worlds.favourites_of(uid),
        avatar=avatars.descriptor(uid, req.user["username"]),
        stats=worlds.player_stats(uid),
        spotlight=spotlight,
        spotlight_left=events.seconds_left(),
        upcoming=events.upcoming(2),
    )


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
