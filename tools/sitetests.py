#!/usr/bin/env python3
"""HTTP-level tests for the website.

Exercises the flows a browser performs -- registration, the starter kit, the
market (including the server-side price and ownership checks), avatar slots,
the social features, messaging, and the administrator dashboard's access
control -- against a running server.

    python3 tools/sitetests.py [--port 80]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import ssl
import string
from http.client import HTTPConnection, HTTPSConnection
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

# The port the site answers plain HTTP on; main.py binds 80 by default and
# BLOCKHAVEN_PORT moves both together.
DEFAULT_PORT = int(os.environ.get("BLOCKHAVEN_PORT", "80"))

PASSED: List[str] = []
FAILED: List[str] = []


def check(name: str, condition: bool, detail: Any = "") -> bool:
    if condition:
        PASSED.append(name)
        print("  PASS  %s" % name)
    else:
        FAILED.append(name)
        print("  FAIL  %s  %s" % (name, str(detail)[:200]))
    return bool(condition)


class Client:
    def __init__(self, host: str, port: int, tls: bool = False):
        self.host, self.port = host, port
        self.tls = tls
        self.cookie = ""
        self.csrf = ""

    def _connect(self):
        if not self.tls:
            return HTTPConnection(self.host, self.port, timeout=15)
        # A developer's certificate is self-signed, so the trust check is off
        # here; the point of running the suite this way is to prove the
        # server speaks TLS at all, not to audit somebody's chain.
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return HTTPSConnection(self.host, self.port, timeout=15, context=ctx)

    def request(self, method: str, path: str, body: Optional[str] = None,
                json_body: bool = False,
                headers: Optional[Dict[str, str]] = None) -> Tuple[int, bytes, Dict[str, str]]:
        conn = self._connect()
        head = dict(headers or {})
        if self.cookie:
            head["Cookie"] = self.cookie
        if body is not None:
            head.setdefault("Content-Type", "application/json" if json_body
                            else "application/x-www-form-urlencoded")
            if self.csrf and "X-CSRF-Token" not in head:
                head["X-CSRF-Token"] = self.csrf
        conn.request(method, path, body, head)
        response = conn.getresponse()
        data = response.read()
        out_headers = {k.lower(): v for k, v in response.getheaders()}
        if "set-cookie" in out_headers:
            self.cookie = out_headers["set-cookie"].split(";")[0]
        status = response.status
        conn.close()
        return status, data, out_headers

    def get(self, path: str) -> Tuple[int, str]:
        status, data, _ = self.request("GET", path)
        return status, data.decode("utf-8", "replace")

    def api(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        status, data, _ = self.request("POST", path, json.dumps(payload), True)
        try:
            return json.loads(data.decode())
        except Exception:
            return {"ok": False, "error": "bad json (%s)" % status, "status": status}

    def websocket_handshake(self, path: str) -> str:
        """Open a game socket the way the browser does; return the status line."""
        conn = self._connect()
        conn.connect()
        sock = conn.sock
        key = "dGhlIHNhbXBsZSBub25jZQ=="
        head = ("GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\n"
                "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
                "Sec-WebSocket-Version: 13\r\n" % (path, self.host, self.port, key))
        if self.cookie:
            head += "Cookie: %s\r\n" % self.cookie
        sock.sendall((head + "\r\n").encode("latin-1"))
        sock.settimeout(10)
        data = b""
        try:
            while b"\r\n" not in data:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                data += chunk
        except OSError:
            pass
        finally:
            conn.close()
        return data.split(b"\r\n", 1)[0].decode("latin-1", "replace")

    def get_api(self, path: str) -> Dict[str, Any]:
        status, data, _ = self.request("GET", path, None, False,
                                       {"X-Requested-With": "fetch"})
        try:
            return json.loads(data.decode())
        except Exception:
            return {"ok": False, "error": "bad json (%s)" % status}

    def refresh_csrf(self) -> None:
        _, html = self.get("/")
        match = re.search(r'csrf: "([^"]*)"', html)
        self.csrf = match.group(1) if match else ""

    def login(self, username: str, password: str) -> int:
        status, _, _ = self.request(
            "POST", "/login", urlencode({"username": username,
                                         "password": password}))
        self.refresh_csrf()
        return status


def random_name() -> str:
    return "test_" + "".join(random.choice(string.ascii_lowercase) for _ in range(8))


def run(host: str, port: int, tls: bool = False) -> int:
    print("== registration and the starter kit ==")
    client = Client(host, port, tls)
    name = random_name()
    status, _, _ = client.request("POST", "/register", urlencode(
        {"username": name, "password": "hunter22", "confirm": "hunter22"}))
    if not check("register: a new account is created", status in (302, 303),
                 status):
        print("  (registration was refused -- the per-hour limit may have been "
              "hit; restart the server or wait before re-running)")
        return 1
    client.refresh_csrf()
    inventory = client.get_api("/api/inventory")
    check("register: the account starts with 2,000 Noogets",
          inventory.get("balance") == 2000, inventory.get("balance"))
    owned = {item["item_id"] for item in inventory.get("items", [])}
    check("register: the starter kit is granted",
          {"use_pistol", "use_shotgun", "use_stick"} <= owned, sorted(owned))
    avatar = client.get_api("/api/avatar")
    hotbar = [entry["item_id"] if entry else None
              for entry in avatar.get("avatar", {}).get("hotbar", [])]
    check("register: the hotbar is pre-filled with the starter weapons",
          hotbar[:3] == ["use_pistol", "use_shotgun", "use_stick"], hotbar)
    check("register: five hotbar slots exist", len(hotbar) == 5, hotbar)

    print("\n== duplicate accounts and validation ==")
    fresh = Client(host, port, tls)
    status, data, _ = fresh.request("POST", "/register", urlencode(
        {"username": name, "password": "hunter22", "confirm": "hunter22"}))
    check("register: duplicate usernames are refused",
          b"already taken" in data, status)
    status, data, _ = fresh.request("POST", "/register", urlencode(
        {"username": "bad name!", "password": "hunter22", "confirm": "hunter22"}))
    check("register: invalid usernames are refused", b"Usernames must be" in data,
          status)
    status, data, _ = fresh.request("POST", "/register", urlencode(
        {"username": random_name(), "password": "abc", "confirm": "abc"}))
    check("register: short passwords are refused", b"at least" in data, status)

    print("\n== market rules ==")
    catalog_items = client.get_api("/api/catalog").get("items", [])
    shelf = sorted((i for i in catalog_items
                    if i.get("for_sale") and i.get("slot") in ("face", "shirt", "pants")
                    and int(i.get("price", 0)) > 0),
                   key=lambda i: int(i["price"]))
    check("market: the catalogue lists items for sale", bool(shelf), len(catalog_items))
    cheap = shelf[0] if shelf else {"id": "face_smile", "price": 0}
    balance = 2000
    result = client.api("/api/market/buy", {"item_id": cheap["id"]})
    check("market: buying charges the catalogue price",
          result.get("ok") and result.get("balance") == balance - int(cheap["price"]), result)
    check("market: a purchase always has a tier",
          result.get("tier") in ("normal", "unusual"), result.get("tier"))
    if result.get("ok"):
        balance = result["balance"]
    hat = client.api("/api/market/buy", {"item_id": "hat_traffic_cone"})
    check("market: hats are not sold on the shelf any more -- they come from crates",
          not hat.get("ok") and "crate" in hat.get("error", ""), hat)
    expensive = client.api("/api/market/buy", {"item_id": "key_standard", "qty": 9})
    check("market: you cannot buy what you cannot afford",
          not expensive.get("ok") and "Noogets" in expensive.get("error", ""),
          expensive)
    unknown = client.api("/api/market/buy", {"item_id": "hat_does_not_exist"})
    check("market: unknown items are rejected", not unknown.get("ok"), unknown)
    free_again = client.api("/api/market/buy", {"item_id": "use_pistol"})
    check("market: free starter items cannot be farmed",
          not free_again.get("ok"), free_again)
    exclusive = client.api("/api/market/buy", {"item_id": "hat_hexed_witch"})
    check("market: event cosmetics only come out of the event crate",
          not exclusive.get("ok") and "crate" in exclusive.get("error", ""), exclusive)
    status, event_html = client.get("/market?slot=event")
    check("market: the event aisle sells the event's weapons while it runs",
          status == 200 and 'data-buy="use_hollow_harvester"' in event_html
          and 'data-buy="use_jack_o_launcher"' in event_html, status)

    print("\n== crates and keys ==")
    keys = client.api("/api/market/buy", {"item_id": "key_standard", "qty": 2})
    check("crates: keys stack -- two bought in one go",
          keys.get("ok") and len(keys.get("inv_ids", [])) == 2
          and keys.get("balance") == balance - 1000, keys)
    if keys.get("ok"):
        balance = keys["balance"]
    crate = client.api("/api/market/buy", {"item_id": "crate_classic"})
    check("crates: a crate costs 500 and goes to the inventory",
          crate.get("ok") and crate.get("balance") == balance - 500, crate)
    if crate.get("ok"):
        balance = crate["balance"]
    stash = client.get_api("/api/crates/stash").get("counts", {})
    check("crates: the stash counts one crate and two keys",
          stash.get("classic") == {"crates": 1, "keys": 2}, stash)
    everything = client.get_api("/api/inventory").get("items", [])
    check("crates: crates and keys show up under Everything",
          {"crate_classic", "key_standard"} <= {i["item_id"] for i in everything})
    status, inv_html = client.get("/inventory")
    check("crates: the inventory page has the crate shelf",
          status == 200 and "stash-card" in inv_html and "data-use-key" in inv_html, status)
    contents = client.get_api("/api/crates/contents?series=classic")
    odds = sum(g.get("chance", 0) for g in contents.get("grades", []))
    check("crates: the published odds add up to 100%", abs(odds - 100) < 0.5, odds)
    opened = client.api("/api/crates/open", {"series": "classic"})
    won = opened.get("item") or {}
    reel = opened.get("reel") or []
    check("crates: opening a crate hands over a hat", opened.get("ok")
          and won.get("slot") == "hat", opened.get("error") or won.get("item_id"))
    check("crates: the reel lands on what was won",
          len(reel) > 40 and 0 <= opened.get("win_index", -1) < len(reel)
          and reel[opened["win_index"]].get("item_id") == won.get("item_id"),
          len(reel))
    check("crates: the crate and one key were used up",
          opened.get("left", {}).get("classic") == {"crates": 0, "keys": 1},
          opened.get("left"))
    again = client.api("/api/crates/open", {"series": "classic"})
    check("crates: no crate, no opening", not again.get("ok"), again)
    feed = client.get_api("/api/crates/feed")
    check("crates: the opening is on the live drop feed",
          any(d.get("username") == name for d in feed.get("feed", [])),
          [d.get("username") for d in feed.get("feed", [])][:5])
    sold = client.api("/api/market/sell", {"inv_id": (keys.get("inv_ids") or [0])[-1]})
    check("crates: a spare key sells back for 40%",
          sold.get("ok") and sold.get("refund") == 200, sold)
    if sold.get("ok"):
        balance = sold["balance"]

    print("\n== badges ==")
    counts = client.get_api("/api/social/counts")
    notes = counts.get("notes") or []
    check("badges: opening a first crate earns Unboxer, with a notification",
          any(n.get("kind") == "badge" and (n.get("data") or {}).get("badge") == "mk_unboxer"
              for n in notes), [n.get("title") for n in notes])
    seen = client.api("/api/notifications/seen", {"ids": [n["id"] for n in notes]})
    check("badges: notifications can be marked seen",
          seen.get("ok") and not client.get_api("/api/social/counts").get("notes"), seen)
    status, editor_html = client.get("/profile-editor")
    check("badges: the Badge Inventory is on the profile editor",
          status == 200 and 'id="badge-pool"' in editor_html and "Unboxer" in editor_html,
          status)
    status, data, _ = client.request("POST", "/profile-editor", json.dumps(
        {"blurb": "", "location": "", "badges": ["mk_unboxer", "ll_medic"]}), True,
        {"X-Requested-With": "fetch"})
    try:
        shown = json.loads(data.decode())
    except ValueError:
        shown = {"ok": False, "status": status}
    check("badges: only earned badges can be put on show",
          shown.get("ok") and shown.get("badges") == ["mk_unboxer"], shown)
    worn = client.api("/api/avatar/badge", {"badge_id": "mk_unboxer"})
    check("badges: an earned badge can be worn",
          worn.get("ok") and (worn.get("avatar", {}).get("badge") or {}).get("id") == "mk_unboxer"
          and len((worn["avatar"]["badge"] or {}).get("parts", [])) >= 3,
          worn.get("error") or (worn.get("avatar") or {}).get("badge"))
    unearned = client.api("/api/avatar/badge", {"badge_id": "ll_medic"})
    check("badges: a badge you have not earned cannot be worn",
          not unearned.get("ok"), unearned)
    status, profile_html = client.get("/profile/%s" % name)
    check("badges: the profile shows the badge row",
          status == 200 and "badge-tile" in profile_html and "Unboxer" in profile_html,
          status)

    print("\n== avatar ownership checks ==")
    inventory = client.get_api("/api/inventory")
    cone = next((i for i in inventory["items"] if i["item_id"] == won.get("item_id")),
                None) or {"inv_id": 0}
    equip = client.api("/api/avatar/equip", {"slot": "hat",
                                             "inv_id": cone["inv_id"]})
    check("avatar: you can wear something you own", equip.get("ok"), equip)
    wrong_slot = client.api("/api/avatar/equip", {"slot": "shirt",
                                                  "inv_id": cone["inv_id"]})
    check("avatar: an item cannot go in the wrong slot",
          not wrong_slot.get("ok"), wrong_slot)
    stolen = client.api("/api/avatar/equip", {"slot": "hat", "inv_id": 1})
    check("avatar: you cannot wear another player's copy",
          not stolen.get("ok"), stolen)
    bad_colour = client.api("/api/avatar/colors", {"colors": {"head": "javascript:1"}})
    check("avatar: colours are validated", not bad_colour.get("ok"), bad_colour)
    good_colour = client.api("/api/avatar/colors", {"colors": {"head": "#12ab34"}})
    check("avatar: a valid colour is stored",
          good_colour.get("ok") and good_colour["colors"]["head"] == "#12ab34",
          good_colour)
    hotbar_theft = client.api("/api/avatar/hotbar", {"index": 4, "inv_id": 1})
    check("avatar: the hotbar rejects unowned items",
          not hotbar_theft.get("ok"), hotbar_theft)

    print("\n== social features ==")
    post = client.api("/api/social/post", {"body": "hello from the site tests"})
    check("social: status posts are retired with the timeline", not post.get("ok"), post)
    _status, home = client.get("/")
    check("social: the home page has no timeline and no post box",
          "Your timeline" not in home and 'id="post-form"' not in home)
    friend = client.api("/api/social/friend", {"action": "request",
                                               "username": "builderman_x"})
    check("social: a friend request is recorded",
          friend.get("ok") and friend.get("state") in ("pending_out", "friends"),
          friend)
    self_friend = client.api("/api/social/friend", {"action": "request",
                                                    "username": name})
    check("social: you cannot befriend yourself", not self_friend.get("ok"),
          self_friend)
    follow = client.api("/api/social/follow", {"username": "PixelPatty"})
    check("social: following works", follow.get("ok"), follow)
    wall = client.api("/api/profile/comment", {"username": "builderman_x",
                                               "body": "great base"})
    check("social: profile comments work", wall.get("ok"), wall)

    print("\n== messaging ==")
    client_name = name
    sent = client.api("/api/messages/send", {"to": "builderman_x",
                                             "subject": "hello",
                                             "body": "testing the mail"})
    check("messages: a message can be sent", sent.get("ok"), sent)
    nobody = client.api("/api/messages/send", {"to": "not_a_real_user",
                                               "subject": "x", "body": "y"})
    check("messages: unknown recipients are refused", not nobody.get("ok"), nobody)
    other = Client(host, port, tls)
    other.login("builderman_x", "blockhaven")
    counts = other.get_api("/api/social/counts")
    status, inbox_html = other.get("/messages")
    check("messages: it arrives in the recipient's inbox",
          "testing the mail" in inbox_html or "hello" in inbox_html, status)

    # Three more from the same sender.  The mailbox is a list of people, so
    # all four have to collapse into one row rather than taking four -- and
    # the row has to carry the latest of them, not the first.
    for n in range(3):
        client.api("/api/messages/send", {"to": "builderman_x",
                                          "subject": "follow up %d" % (n + 1),
                                          "body": "still testing %d" % (n + 1)})
    threads = other.get_api("/api/messages/recent").get("rows", [])
    mine = [t for t in threads if t.get("who") == client_name]
    check("messages: four from one sender make one conversation row",
          len(mine) == 1, [t.get("who") for t in threads])
    if mine:
        check("messages: the row counts the whole conversation",
              mine[0].get("total", 0) >= 4, mine[0])
        check("messages: the row shows the latest message",
              "follow up 3" in str(mine[0].get("subject", "")), mine[0])
        check("messages: the row counts what is unread",
              mine[0].get("unread", 0) >= 4, mine[0])
        status, threaded_html = other.get("/messages")
        check("messages: the mailbox page shows that one row too",
              threaded_html.count('class="msgrow') ==
              len(threads), threaded_html.count('class="msgrow'))
    check("messages: the unread counter moves",
          other.get_api("/api/social/counts").get("unread", 0) >= 1, counts)
    match = re.search(r'/messages/(\d+)', inbox_html)
    if match:
        message_id = match.group(1)
        status, _body = client.get("/messages/%s" % message_id)
        check("messages: the sender can read their own message", status == 200,
              status)
        snooper = Client(host, port, tls)
        snooper.login("PixelPatty", "blockhaven")
        status, snooped = snooper.get("/messages/%s" % message_id)
        # A message that is not yours is not there as far as you are
        # concerned, and "not there" sends you to the home page.  What is
        # checked is the part that matters -- none of the message comes
        # back -- rather than the status code that carries it, so this
        # holds whichever way a dead end is answered.
        check("messages: an unrelated player cannot read someone else's mail",
              status in (302, 303, 404)
              and "testing the mail" not in snooped
              and "hello" not in snooped.lower(),
              "%s / %d bytes" % (status, len(snooped)))

    print("\n== admin access control ==")
    status, _, headers = client.request("GET", "/admin-dashboard")
    check("admin: normal players are redirected away from the dashboard",
          status in (302, 303) and headers.get("location", "").endswith("/"),
          "%s %s" % (status, headers.get("location")))
    denied = client.api("/api/admin/credits", {"username": name, "amount": 999999,
                                               "mode": "add"})
    check("admin: normal players cannot grant themselves Noogets",
          not denied.get("ok"), denied)
    balance_now = client.get_api("/api/inventory").get("balance")
    check("admin: the balance really did not change", balance_now == balance,
          balance_now)

    admin = Client(host, port, tls)
    admin.login("admin_system", "passman69")
    status, html = admin.get("/admin-dashboard")
    check("admin: administrators can open the dashboard", status == 200, status)
    granted = admin.api("/api/admin/credits", {"username": name, "amount": 500,
                                               "mode": "add", "reason": "test"})
    check("admin: administrators can adjust Noogets",
          granted.get("ok") and granted.get("balance") == balance + 500, granted)
    if granted.get("ok"):
        balance = granted["balance"]
    unusual = admin.api("/api/admin/grant", {"username": name,
                                             "item_id": "hat_crown",
                                             "tier": "unusual",
                                             "effect": "frostbite"})
    check("admin: administrators can grant an Unusual hat",
          unusual.get("ok") and unusual["item"]["tier"] == "unusual", unusual)
    bad_unusual = admin.api("/api/admin/grant", {"username": name,
                                                 "item_id": "shirt_tux",
                                                 "tier": "unusual"})
    check("admin: only hats can be Unusual", not bad_unusual.get("ok"), bad_unusual)
    key_grant = admin.api("/api/admin/grant", {"username": name, "item_id": "key_halloween"})
    check("admin: a Crate Key can be granted from the item picker",
          key_grant.get("ok"), key_grant)
    dropped = admin.api("/api/admin/drop-crate", {"username": name, "crate": "crate_halloween",
                                                  "count": 2, "keys": True,
                                                  "note": "Happy haunting!"})
    check("admin: Drop A Crate gives a player crates and keys",
          dropped.get("ok") and dropped.get("count") == 2, dropped)
    stash = client.get_api("/api/crates/stash").get("counts", {})
    check("admin: the dropped crates are in the player's stash",
          stash.get("halloween") == {"crates": 2, "keys": 3}, stash)
    crate_notes = [n for n in client.get_api("/api/social/counts").get("notes") or []
                   if n.get("kind") == "crate"]
    check("admin: the player is told about the drop", bool(crate_notes), crate_notes)
    no_one = admin.api("/api/admin/drop-crate", {"username": "not_a_real_user_x",
                                                 "crate": "crate_classic"})
    check("admin: Drop A Crate refuses an unknown player", not no_one.get("ok"), no_one)
    denied_drop = client.api("/api/admin/drop-crate", {"username": name,
                                                       "crate": "crate_classic"})
    check("admin: players cannot drop crates on themselves",
          not denied_drop.get("ok"), denied_drop)

    print("\n== bundles ==")
    admin.api("/api/admin/credits", {"username": name, "amount": 1000, "mode": "add",
                                     "reason": "bundle test"})
    bundle = client.api("/api/market/bundle", {"offer_id": "offer_classic_pair"})
    check("bundles: the Crate + Key pair can be bought",
          bundle.get("ok") and client.get_api("/api/crates/stash").get("counts", {})
          .get("classic") == {"crates": 1, "keys": 1}, bundle)
    status, market_html = client.get("/market")
    check("bundles: the market shows the Crate Hall and its bundles",
          status == 200 and "Crate Hall" in market_html and "offer_classic_pair" in market_html,
          status)

    print("\n== csrf ==")
    raw = Client(host, port, tls)
    raw.login(name, "hunter22")
    raw.csrf = "not-the-right-token"
    forged = raw.api("/api/market/buy", {"item_id": "key_standard"})
    check("csrf: a request with a bad token is rejected", not forged.get("ok"),
          forged)

    print("\n== page smoke test ==")
    pages = ["/", "/worlds", "/market", "/market?slot=stash", "/market?slot=event",
             "/users", "/help", "/inventory", "/inventory?slot=stash",
             "/avatar", "/friends", "/messages", "/settings", "/profile-editor",
             "/profile/%s" % name, "/inventory/%s" % name,
             "/worlds/blackout_relay", "/worlds/last_light",
             "/blackout_relay", "/last_light",
             "/search?q=hat", "/api/catalog",
             "/api/worlds/status"]
    broken = []
    for page in pages:
        status, _ = client.get(page)
        if status != 200:
            broken.append((page, status))
    check("pages: every page renders", not broken, broken)

    print("\n== hidden worlds ==")
    hidden = ["capture_the_flag", "burger_tycoon", "fortress_team_2"]
    still_there = []
    for world in hidden:
        for page in ("/worlds/%s" % world, "/%s" % world):
            status, html = client.get(page)
            if status == 200:
                still_there.append(page)
    check("hidden: Capture the Flag, Fortress Team 2 and Burger Tycoon have no pages",
          not still_there, still_there)
    world_status = client.get_api("/api/worlds/status").get("worlds", {})
    check("hidden: and are not in the world status",
          not (set(hidden) & set(world_status)), sorted(world_status))
    joins = [client.api("/api/game/join", {"world_id": w}) for w in hidden]
    check("hidden: and cannot be joined",
          not any(j.get("ok") for j in joins)
          and all(j.get("error") and "nothing at" not in j.get("error", "") for j in joins),
          [j.get("error") for j in joins])

    print("\n== joining a world with everything equipped ==")
    # The join ticket rides in the socket URL.  It used to carry every model
    # the avatar wore and held, and two event weapons on the hotbar pushed it
    # past the game host's request-line limit: the ticket was cut short, its
    # signature failed and the join hung on "waiting for the world".
    for item_id, index in (("use_hollow_harvester", 3), ("use_jack_o_launcher", 4)):
        admin.api("/api/admin/grant", {"username": name, "item_id": item_id})
        owned = client.get_api("/api/inventory").get("items", [])
        copy = next((i for i in owned if i["item_id"] == item_id), None)
        if copy:
            client.api("/api/avatar/hotbar", {"index": index, "inv_id": copy["inv_id"]})
    for world in ("last_light", "blackout_relay"):
        ticket = client.api("/api/game/join", {"world_id": world})
        ws_path = ticket.get("ws", "")
        check("join: %s hands out a compact ticket with the event weapons held" % world,
              ticket.get("ok") and 0 < len(ws_path) < 4096, len(ws_path))
        if ws_path:
            status_line = client.websocket_handshake(ws_path)
            check("join: the %s host accepts that ticket" % world,
                  " 101 " in status_line, status_line)
    status, worlds_html = client.get("/worlds")
    check("hidden: the world browser does not list them",
          not any(w in worlds_html for w in hidden), status)

    print("\n==================== %d passed, %d failed ===================="
          % (len(PASSED), len(FAILED)))
    for item in FAILED:
        print("  FAILED:", item)
    return 1 if FAILED else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--https", action="store_true",
                        help="drive the suite over TLS (port 443 unless "
                             "--port says otherwise)")
    args = parser.parse_args()
    port = args.port
    if args.https and port == DEFAULT_PORT:
        port = int(os.environ.get("BLOCKHAVEN_HTTPS_PORT", "443"))
    print("== %s://%s:%d ==" % ("https" if args.https else "http", args.host, port))
    return run(args.host, port, args.https)


if __name__ == "__main__":
    raise SystemExit(main())
