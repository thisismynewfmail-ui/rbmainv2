"""The family pages and their JSON API.

    /parent_signup_l                 the landing page (for ads)
    /parent-signup                   the onboarding page: the ONLY place a
                                     parent account can be made
    /parent-signin, /parent-signout  the parents' own sign-in
    /parent_<name>                   the parent's page: their family at a glance
    /parent_<name>/setup             the guided set-up of a child's account
    /parent_<name>/child/<kid>       one child's dashboard
    /api/family/...                  everything those pages do

Parent pages answer only to the parent they belong to.  Anybody else --
signed out, signed in as a player, signed in as another parent -- gets the
same answer whether the name exists or not (the sign-in page, or their own
page), so the addresses cannot be used to find out who has a family account,
let alone who their children are.
"""
from __future__ import annotations

import functools
import json
import random
import re
import time
from typing import Any, Callable, Dict, Optional
from urllib.parse import quote, urlencode

from .. import config, db, security
from ..http import router as R
from ..http.router import Request, Response
from ..views import base
from ..views.base import api_error, api_ok, router, to_json
from . import accounts, activity, children, controls as rules, guard, insights, shield

FAMILY_PREFIXES = ("/parent", "/api/family/")
UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_content",
            "utm_term", "fbclid", "ref")


def is_family_path(path: str) -> bool:
    return path.startswith(FAMILY_PREFIXES)


# ---------------------------------------------------------------- sessions

def current(req: Request) -> Optional[Dict[str, Any]]:
    token = req.cookies.get(config.FAMILY_COOKIE, "")
    return accounts.session_for(token) if token else None


def csrf_ok(req: Request) -> bool:
    """The check ``webapp`` hands family paths to: unauthenticated posts
    (sign-up, sign-in) are rate-limited instead, everything else has to carry
    the parent session's own token."""
    if req.method in ("GET", "HEAD"):
        return True
    fam = current(req)
    if fam is None:
        return True
    supplied = (req.headers.get("x-csrf-token") or req.data().get("csrf")
                or req.query.get("csrf") or "")
    import hmac
    return bool(fam["csrf"]) and hmac.compare_digest(str(supplied), str(fam["csrf"]))


def _set_session_cookie(resp: Response, token: str) -> Response:
    resp.set_cookie(config.FAMILY_COOKIE, token, max_age=config.FAMILY_SESSION_TTL)
    return resp


def _home_of(parent: Dict[str, Any]) -> str:
    return "/parent_%s" % parent["username"]


def parent_required(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(req: Request, *args, **kwargs):
        fam = current(req)
        if fam is None:
            if req.wants_json:
                return api_error("Sign in to your family account first.", 401)
            return R.redirect("/parent-signin?next=%s" % quote(req.path))
        return fn(req, fam, *args, **kwargs)
    return wrapper


def _own_page(fam: Dict[str, Any], name: str) -> bool:
    return (name or "").lower() == fam["parent"]["username_lower"]


def _theme(req: Request) -> str:
    cookie = (req.cookies.get(base.THEME_COOKIE) or "").strip().lower()
    return cookie if cookie in ("light", "dark") else "auto"


def context(req: Request, fam: Optional[Dict[str, Any]] = None, **extra: Any) -> Dict[str, Any]:
    parent = fam["parent"] if fam else None
    ctx: Dict[str, Any] = {
        "brand": config.FAMILY_BRAND,
        "page_title": config.FAMILY_BRAND,
        "parent": parent,
        "csrf": fam["csrf"] if fam else "",
        "theme": _theme(req),
        "path": req.path,
        "now": int(time.time()),
        "max_children": config.FAMILY_MAX_CHILDREN,
        "pixel": "",
        "flash": base.current_flash(req),
        "to_json": to_json,
        "fmt_num": base.fmt_num,
        "fmt_date": base.fmt_date,
        "ago": base.ago,
        "home": _home_of(parent) if parent else "",
        "page_class": "",
        "extra_css": [],
        "scripts": [],
        "boot": None,
        "engine": False,
    }
    ctx.update(extra)
    # the pixel id goes into a script, so only ever digits
    ctx["pixel"] = re.sub(r"[^0-9]", "", str(ctx.get("pixel") or ""))[:20]
    return ctx


def render(req: Request, template: str, fam: Optional[Dict[str, Any]] = None,
           status: int = 200, **extra: Any) -> Response:
    resp = R.template("family/%s" % template, status, **context(req, fam, **extra))
    # These pages are about one family; nothing on them belongs in a shared cache.
    resp.headers["Cache-Control"] = "private, no-store"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp


def _utm(req: Request) -> Dict[str, str]:
    data = req.data() if req.method == "POST" else {}
    out = {}
    for key in UTM_KEYS:
        value = str(data.get(key) or req.query.get(key) or "")[:120]
        if value:
            out[key] = value
    return out


def _passthrough(req: Request) -> str:
    """The landing page's campaign tags, carried on to the sign-up page."""
    tags = {k: req.query[k][:120] for k in UTM_KEYS if req.query.get(k)}
    return ("?" + urlencode(tags)) if tags else ""


def _safe_next(value: str, fallback: str) -> str:
    value = (value or "").strip()
    if not value.startswith("/parent") or value.startswith("//"):
        return fallback
    return value


# ============================================================ public pages

def _landing_worlds():
    from ..models import worlds
    out = []
    for world in worlds.all_worlds():
        guide = rules.world_guide(world)
        out.append({"id": world["id"], "name": world["name"],
                    "thumb": world.get("thumb", ""),
                    "thumb_script": world.get("thumb_script") or "",
                    "tagline": world.get("tagline", ""), "kind": guide["kind"],
                    "intensity": guide["intensity"],
                    "intensity_label": guide["intensity_label"],
                    "colors": (world.get("colors") or ["#3d7fb4", "#f5cd30", "#c4281c"])[:3]})
    order = {"gentle": 0, "action": 1, "intense": 2}
    out.sort(key=lambda w: order.get(w["intensity"], 1))
    return out


@router.get("/parent_signup_l")
def landing(req: Request):
    fam = current(req)
    return render(req, "landing.html", fam,
                  page_title="A safe place to play, with you in charge",
                  page_class="fam-landing",
                  worlds=_landing_worlds(),
                  signup_href="/parent-signup" + _passthrough(req),
                  utm=_utm(req),
                  year=time.gmtime().tm_year,
                  pixel=config.FAMILY_FB_PIXEL,
                  extra_css=["/static/css/family/haven.css", "/static/css/family/landing.css"],
                  scripts=["/static/js/family/haven.js", "/static/js/family/landing.js"])


@router.route("/parent-signup", ("GET", "POST"))
def signup(req: Request):
    fam = current(req)
    if fam is not None and req.method == "GET":
        parent = fam["parent"]
        kids = children.count_for(int(parent["id"]))
        return R.redirect(_home_of(parent) + ("" if kids else "/setup"))
    if req.method == "GET":
        return render(req, "signup.html", None, page_title="Create your family account",
                      page_class="fam-signup", extra_css=["/static/css/family/haven.css", "/static/css/family/onboard.css"], error="", field="", values={
                          "email": req.query.get("email", "")[:120]},
                      utm=_utm(req), pixel=config.FAMILY_FB_PIXEL,
                      password_min=config.FAMILY_PASSWORD_MIN,
                      scripts=["/static/js/family/haven.js", "/static/js/family/signup.js"])
    form = req.data()
    values = {k: str(form.get(k, ""))[:160] for k in
              ("display_name", "email", "username", "relation")}

    def fail(message: str, field: str = "", status: int = 400):
        if req.wants_json:
            return R.json_response({"ok": False, "error": message, "field": field}, status)
        return render(req, "signup.html", None, status, page_title="Create your family account",
                      page_class="fam-signup", extra_css=["/static/css/family/haven.css", "/static/css/family/onboard.css"], error=message, field=field, values=values,
                      utm=_utm(req), pixel=config.FAMILY_FB_PIXEL,
                      password_min=config.FAMILY_PASSWORD_MIN,
                      scripts=["/static/js/family/haven.js", "/static/js/family/signup.js"])

    if not db.rate_limit("family.signup:%s" % req.remote_addr, 12, 3600):
        return fail("Too many sign-ups from this connection -- try again in a little while.",
                    status=429)
    if str(form.get("guardian", "")) not in ("1", "on", "true", "yes"):
        return fail("Please confirm you're the child's parent or legal guardian, and over 18.",
                    "guardian")
    password = str(form.get("password", ""))
    if form.get("confirm") is not None and str(form.get("confirm")) != password:
        return fail("Those passwords don't match.", "confirm")
    try:
        parent = accounts.create(values["username"], password, values["display_name"],
                                 values["email"], values["relation"] or "parent",
                                 str(form.get("timezone", "")), form.get("tz_offset", 0),
                                 _utm(req))
    except accounts.ParentError as exc:
        return fail(str(exc), exc.field)
    session = accounts.start_session(int(parent["id"]), req.headers.get("user-agent", ""),
                                     req.remote_addr)
    target = _home_of(parent) + "/setup?welcome=1"
    resp = (R.json_response({"ok": True, "redirect": target}) if req.wants_json
            else R.redirect(target))
    return _set_session_cookie(resp, session["token"])


@router.route("/parent-signin", ("GET", "POST"))
def signin(req: Request):
    fam = current(req)
    nxt = req.query.get("next", "") or str(req.data().get("next", "") if req.method == "POST" else "")
    if fam is not None and req.method == "GET":
        return R.redirect(_safe_next(nxt, _home_of(fam["parent"])))
    if req.method == "GET":
        return render(req, "signin.html", None, page_title="Family sign in",
                      page_class="fam-signin", extra_css=["/static/css/family/onboard.css"], error="", login="", next_url=nxt)
    form = req.data()
    login = str(form.get("login", "")).strip()[:254]
    if not db.rate_limit("family.signin:%s" % login.lower()[:60], 10, 300) or \
            not db.rate_limit("family.signin.ip:%s" % req.remote_addr, 60, 300):
        return render(req, "signin.html", None, 429, page_title="Family sign in",
                      page_class="fam-signin", extra_css=["/static/css/family/onboard.css"], login=login, next_url=nxt,
                      error="Too many tries. Wait a minute, then try again.")
    try:
        parent = accounts.authenticate(login, str(form.get("password", "")))
    except accounts.ParentError as exc:
        return render(req, "signin.html", None, 401, page_title="Family sign in",
                      page_class="fam-signin", extra_css=["/static/css/family/onboard.css"], login=login, next_url=nxt, error=str(exc))
    session = accounts.start_session(int(parent["id"]), req.headers.get("user-agent", ""),
                                     req.remote_addr)
    return _set_session_cookie(R.redirect(_safe_next(nxt, _home_of(parent))),
                               session["token"])


def sign_parent_in(parent: Dict[str, Any], req: Request) -> Response:
    """Used by the players' /login page when the name is a parent's."""
    session = accounts.start_session(int(parent["id"]), req.headers.get("user-agent", ""),
                                     req.remote_addr)
    return _set_session_cookie(R.redirect(_home_of(parent)), session["token"])


@router.route("/parent-signout", ("GET", "POST"))
def signout(req: Request):
    fam = current(req)
    if fam is not None:
        accounts.end_session(fam["token"])
    resp = R.redirect("/parent-signin?msg=%s" % quote("You're signed out. See you soon!"))
    resp.delete_cookie(config.FAMILY_COOKIE)
    return resp


# ============================================================= parent pages

def _owner_or_redirect(req: Request, fam: Dict[str, Any], name: str) -> Optional[Response]:
    if not _own_page(fam, name):
        return R.redirect(_home_of(fam["parent"]))
    return None


def _attention(kids) -> list:
    """Approvals waiting and serious alerts unseen, across the family."""
    items = []
    for kid in kids:
        uid = int(kid["id"])
        for row in db.query(
                "SELECT a.id, a.direction, a.created_at, u.username FROM family_approvals a"
                " JOIN users u ON u.id=a.other_id WHERE a.child_id=? AND a.status='waiting'"
                " ORDER BY a.id DESC LIMIT 5", (uid,)):
            items.append({"kind": "approval", "child": kid["first_name"],
                          "child_username": kid["username"], "id": int(row["id"]),
                          "uid": uid, "other": row["username"],
                          "direction": row["direction"], "at": int(row["created_at"])})
        for row in db.query(
                "SELECT id, title, detail, severity, created_at FROM family_alerts"
                " WHERE user_id=? AND seen_at=0 AND severity IN ('warn','high')"
                " ORDER BY id DESC LIMIT 4", (uid,)):
            items.append({"kind": "alert", "child": kid["first_name"],
                          "child_username": kid["username"], "uid": uid,
                          "title": row["title"], "detail": row["detail"],
                          "severity": row["severity"], "at": int(row["created_at"])})
    items.sort(key=lambda i: -i["at"])
    return items[:12]


@router.get("/parent_<name>")
@parent_required
def hub(req: Request, fam: Dict[str, Any], name: str = ""):
    redirect = _owner_or_redirect(req, fam, name)
    if redirect:
        return redirect
    parent = fam["parent"]
    kids = children.list_for(int(parent["id"]))
    overview = insights.family_overview(parent, kids)
    return render(req, "hub.html", fam, page_title="Your family",
                  page_class="fam-app fam-hub",
                  extra_css=["/static/css/family/onboard.css", "/static/css/family/dashboard.css"],
                  engine=True,
                  kids=overview, attention=_attention(kids),
                  greeting=accounts.greeting(parent),
                  slots_left=config.FAMILY_MAX_CHILDREN - len(kids),
                  relations=accounts.RELATIONS,
                  scripts=["/static/js/family/hub.js"],
                  boot={"kids": overview, "csrf": fam["csrf"], "home": _home_of(parent)})


@router.get("/parent_<name>/setup")
@parent_required
def setup(req: Request, fam: Dict[str, Any], name: str = ""):
    redirect = _owner_or_redirect(req, fam, name)
    if redirect:
        return redirect
    from ..models import catalog
    parent = fam["parent"]
    kids = children.list_for(int(parent["id"]))
    if len(kids) >= config.FAMILY_MAX_CHILDREN:
        return R.redirect(_home_of(parent) + "?msg=%s" % quote(
            "You've set up all %d child accounts a family can have."
            % config.FAMILY_MAX_CHILDREN))
    from ..models import worlds
    world_rows = []
    for world in worlds.all_worlds():
        guide = rules.world_guide(world)
        world_rows.append({"id": world["id"], "name": world["name"], "kind": guide["kind"],
                           "note": guide["note"], "intensity": guide["intensity"],
                           "intensity_label": guide["intensity_label"],
                           "color": (world.get("colors") or ["#3d7fb4"])[0]})
    this_year = time.gmtime().tm_year
    from ..models import avatars
    return render(req, "setup.html", fam, page_title="Set up your child's account",
                  page_class="fam-app fam-setup",
                  extra_css=["/static/css/family/haven.css", "/static/css/family/onboard.css"],
                  engine=True,
                  welcome=req.query.get("welcome") == "1",
                  kids=kids, slot_number=len(kids) + 1,
                  years=list(range(this_year - 4, this_year - 19, -1)),
                  scripts=["/static/js/family/haven.js", "/static/js/family/setup.js"],
                  pixel=config.FAMILY_FB_PIXEL if req.query.get("welcome") == "1" else "",
                  boot={
                      "csrf": fam["csrf"], "home": _home_of(parent),
                      "parent": parent["display_name"],
                      "palette": catalog.BODY_PALETTE,
                      "parts": catalog.BODY_PARTS,
                      "defaults_by_age": {str(a): rules.defaults(a) for a in range(4, 19)},
                      "defaults_unknown": rules.defaults(None),
                      "worlds": world_rows,
                      "minutes": rules.MINUTE_CHOICES,
                      "labels": rules.LABELS,
                      "help": rules.HELP,
                      "this_year": this_year,
                      "kids": [{"first_name": k["first_name"], "username": k["username"]}
                               for k in kids],
                      "max": config.FAMILY_MAX_CHILDREN,
                      "password_min": children.CHILD_PASSWORD_MIN,
                      "avatar": avatars.default_descriptor("New player"),
                      "welcome": req.query.get("welcome") == "1",
                  })


@router.get("/parent_<name>/child/<kid>")
@parent_required
def child_page(req: Request, fam: Dict[str, Any], name: str = "", kid: str = ""):
    redirect = _owner_or_redirect(req, fam, name)
    if redirect:
        return redirect
    from ..models import avatars
    parent = fam["parent"]
    child = children.get(int(parent["id"]), kid)
    if child is None:
        return R.redirect(_home_of(parent))
    report = insights.child_report(child)
    siblings = [{"username": k["username"], "first_name": k["first_name"],
                 "current": k["id"] == child["id"]}
                for k in children.list_for(int(parent["id"]))]
    return render(req, "child.html", fam,
                  page_title="%s's dashboard" % child["first_name"],
                  page_class="fam-app fam-child",
                  extra_css=["/static/css/family/onboard.css", "/static/css/family/dashboard.css"],
                  child=child, report=report, siblings=siblings,
                  avatar=avatars.descriptor(int(child["id"]), child["username"]),
                  scripts=["/static/js/family/charts.js", "/static/js/family/child.js"],
                  engine=True,
                  boot={"csrf": fam["csrf"], "home": _home_of(parent),
                        "child": {"id": child["id"], "username": child["username"],
                                  "first_name": child["first_name"],
                                  "paused": child["paused"]},
                        "report": report})


# ================================================================== the API

def _api(fn: Callable) -> Callable:
    """Parent session + CSRF for every family API call, and a child id that
    must belong to this parent when the route has one."""
    @functools.wraps(fn)
    def wrapper(req: Request, *args, **kwargs):
        fam = current(req)
        if fam is None:
            return api_error("Sign in to your family account first.", 401)
        if req.method not in ("GET", "HEAD") and not csrf_ok(req):
            return api_error("Your session expired. Reload the page.", 403)
        child = None
        if "uid" in kwargs:
            child = children.get(int(fam["parent"]["id"]), int(kwargs.pop("uid")))
            if child is None:
                return api_error("Not found.", 404)
            kwargs["child"] = child
        try:
            return fn(req, fam, *args, **kwargs)
        except (children.ChildError, accounts.ParentError) as exc:
            return R.json_response({"ok": False, "error": str(exc),
                                    "field": getattr(exc, "field", "")}, 400)
    return wrapper


ADJECTIVES = ["Pixel", "Turbo", "Cosmic", "Brave", "Lucky", "Sunny", "Rocket", "Mighty",
              "Super", "Happy", "Ninja", "Starry", "Bouncy", "Clever", "Zippy", "Jolly",
              "Frosty", "Golden", "Sneaky", "Wild", "Thunder", "Sparkle", "Captain", "Epic"]
NOUNS = ["Panda", "Otter", "Dragon", "Falcon", "Comet", "Llama", "Koala", "Tiger", "Fox",
         "Penguin", "Wizard", "Robot", "Builder", "Racer", "Knight", "Dino", "Narwhal",
         "Pirate", "Explorer", "Beetle", "Phoenix", "Badger", "Yeti", "Gecko"]


def _suggest(seed: str = "") -> list:
    rng = random.Random()
    out = []
    tries = 0
    while len(out) < 4 and tries < 40:
        tries += 1
        name = rng.choice(ADJECTIVES) + rng.choice(NOUNS) + str(rng.randint(2, 99))
        if len(name) <= config.USERNAME_MAX and not accounts.name_taken(name) \
                and name not in out:
            out.append(name)
    return out


@router.post("/api/family/username")
def api_username(req: Request):
    """Is this name free?  Open to the sign-up page (rate-limited) as well as
    to a signed-in parent setting up a child."""
    if not db.rate_limit("family.name:%s" % req.remote_addr, 90, 300):
        return api_error("Slow down a little.", 429)
    data = req.data()
    name = str(data.get("username", "")).strip()[:40]
    kind = str(data.get("kind", "child"))
    if kind == "parent":
        problem = accounts.check_username(name)
        return api_ok(available=problem is None, problem=problem or "")
    problem = children.check_username(name)
    year = data.get("birth_year")
    try:
        year = int(year) if year else None
    except (TypeError, ValueError):
        year = None
    return api_ok(available=problem is None, problem=problem or "",
                  warnings=shield.username_warnings(name, str(data.get("first_name", "")), year),
                  suggestions=_suggest() if problem else [])


@router.post("/api/family/safechat-demo")
def api_safechat_demo(req: Request):
    """The landing page's "be the stranger" demo: the real Safe Chat filter
    over one line, as if somebody had sent it to a child.  Nothing is
    stored, and nothing is sent anywhere."""
    if not db.rate_limit("family.demo:%s" % req.remote_addr, 60, 300):
        return api_error("That's a lot of tries -- give it a minute.", 429)
    text = security.clean_text(str(req.data().get("text", "")), 200, allow_newlines=False)
    if not text:
        return api_error("Type something first.")
    verdict = shield.scan(text, author_is_child=False, channel="private")
    return api_ok(action=verdict.action, severity=verdict.severity,
                  categories=list(verdict.categories), what=verdict.describe(),
                  masked=verdict.masked or text)


@router.get("/api/family/suggest")
def api_suggest(req: Request):
    if not db.rate_limit("family.suggest:%s" % req.remote_addr, 60, 300):
        return api_error("Slow down a little.", 429)
    return api_ok(suggestions=_suggest())


@router.post("/api/family/children")
@_api
def api_create_child(req: Request, fam: Dict[str, Any]):
    data = req.data()
    if not db.rate_limit("family.child:%d" % int(fam["parent"]["id"]), 12, 3600):
        return api_error("That's a lot of new accounts at once -- try again later.", 429)
    child = children.create(fam["parent"], str(data.get("first_name", "")),
                            data.get("birth_year"), str(data.get("username", "")),
                            str(data.get("password", "")),
                            data.get("look") if isinstance(data.get("look"), dict) else {},
                            data.get("controls") if isinstance(data.get("controls"), dict) else {})
    parent = fam["parent"]
    return api_ok(child={"id": child["id"], "username": child["username"],
                         "first_name": child["first_name"]},
                  dashboard="%s/child/%s" % (_home_of(parent), child["username"]),
                  slots_left=config.FAMILY_MAX_CHILDREN - children.count_for(int(parent["id"])))


@router.post("/api/family/setup-later")
@_api
def api_setup_later(req: Request, fam: Dict[str, Any]):
    parent = fam["parent"]
    if children.count_for(int(parent["id"])) == 0:
        accounts.set_setup_state(int(parent["id"]), "later")
    return api_ok(redirect=_home_of(parent))


@router.get("/api/family/live")
@_api
def api_family_live(req: Request, fam: Dict[str, Any]):
    kids = children.list_for(int(fam["parent"]["id"]))
    return api_ok(kids=[dict(insights.live_status(k), id=k["id"]) for k in kids])


@router.get("/api/family/child/<uid:int>/live")
@_api
def api_child_live(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    return api_ok(status=insights.live_status(child),
                  sessions=insights.sessions(child, 8))


@router.get("/api/family/child/<uid:int>/report")
@_api
def api_child_report(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    return api_ok(report=insights.child_report(child))


@router.get("/api/family/child/<uid:int>/transcript")
@_api
def api_transcript(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    return api_ok(**insights.transcript(child, str(req.query.get("with", ""))[:40]))


@router.post("/api/family/child/<uid:int>/controls")
@_api
def api_controls(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    data = req.data()
    raw = data.get("controls") if isinstance(data.get("controls"), dict) else data
    saved = children.set_controls(int(fam["parent"]["id"]), int(child["id"]), raw)
    return api_ok(controls=saved, today=activity.today_summary(
        children.directory.get(child["id"])))


@router.post("/api/family/child/<uid:int>/pause")
@_api
def api_pause(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    paused = children.set_paused(int(fam["parent"]["id"]), int(child["id"]),
                                 bool(req.data().get("paused")))
    return api_ok(paused=paused)


@router.post("/api/family/child/<uid:int>/password")
@_api
def api_child_password(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    children.reset_password(int(fam["parent"]["id"]), int(child["id"]),
                            str(req.data().get("password", "")))
    return api_ok()


@router.post("/api/family/child/<uid:int>/details")
@_api
def api_child_details(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    data = req.data()
    updated = children.update_details(int(fam["parent"]["id"]), int(child["id"]),
                                      str(data.get("first_name", "")), data.get("birth_year"))
    return api_ok(first_name=updated["first_name"], age=updated["age"])


@router.post("/api/family/child/<uid:int>/signout")
@_api
def api_child_signout(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    children.sign_out_everywhere(int(fam["parent"]["id"]), int(child["id"]))
    return api_ok()


@router.post("/api/family/child/<uid:int>/signin-here")
@_api
def api_child_signin_here(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    session = children.sign_in_here(int(fam["parent"]["id"]), int(child["id"]),
                                    req.headers.get("user-agent", ""), req.remote_addr)
    resp = api_ok(redirect="/avatar?welcome=1")
    resp.set_cookie(config.SESSION_COOKIE, session["token"], max_age=config.SESSION_TTL)
    return resp


@router.post("/api/family/child/<uid:int>/delete")
@_api
def api_child_delete(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    if str(req.data().get("confirm", "")).strip().lower() != child["username"].lower():
        return api_error("Type their username exactly to confirm.")
    children.delete(int(fam["parent"]["id"]), int(child["id"]))
    return api_ok(redirect=_home_of(fam["parent"]))


@router.post("/api/family/child/<uid:int>/approval")
@_api
def api_approval(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    data = req.data()
    try:
        approval_id = int(data.get("id", 0))
    except (TypeError, ValueError):
        return api_error("Bad request.")
    state = children.decide_approval(int(fam["parent"]["id"]), int(child["id"]),
                                     approval_id, str(data.get("decision")) == "approve")
    return api_ok(state=state)


@router.post("/api/family/child/<uid:int>/unfriend")
@_api
def api_unfriend(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    children.remove_friend(int(fam["parent"]["id"]), int(child["id"]),
                           str(req.data().get("username", ""))[:40])
    return api_ok()


@router.post("/api/family/child/<uid:int>/alerts-seen")
@_api
def api_alerts_seen(req: Request, fam: Dict[str, Any], child: Dict[str, Any]):
    insights.mark_alerts_seen(int(child["id"]))
    return api_ok()


@router.post("/api/family/account")
@_api
def api_account(req: Request, fam: Dict[str, Any]):
    data = req.data()
    parent = accounts.update_profile(int(fam["parent"]["id"]),
                                     str(data.get("display_name", "")),
                                     str(data.get("email", "")),
                                     str(data.get("timezone", "")),
                                     str(data.get("relation", "")))
    children.directory.invalidate()
    return api_ok(display_name=parent["display_name"], email=parent["email"],
                  timezone=parent["timezone"])


@router.post("/api/family/account/password")
@_api
def api_account_password(req: Request, fam: Dict[str, Any]):
    data = req.data()
    accounts.change_password(int(fam["parent"]["id"]), str(data.get("current", "")),
                             str(data.get("new", "")))
    accounts.end_all_sessions(int(fam["parent"]["id"]), keep=fam["token"])
    return api_ok()


@router.post("/api/family/account/signout-all")
@_api
def api_account_signout_all(req: Request, fam: Dict[str, Any]):
    accounts.end_all_sessions(int(fam["parent"]["id"]), keep=fam["token"])
    return api_ok()


@router.post("/api/family/account/delete")
@_api
def api_account_delete(req: Request, fam: Dict[str, Any]):
    parent = fam["parent"]
    if str(req.data().get("confirm", "")).strip().lower() != parent["username_lower"]:
        return api_error("Type your username exactly to confirm.")
    accounts.delete(int(parent["id"]))
    resp = api_ok(redirect="/parent_signup_l")
    resp.delete_cookie(config.FAMILY_COOKIE)
    return resp
