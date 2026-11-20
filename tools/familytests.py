#!/usr/bin/env python3
"""Family accounts: parents, child accounts, the controls and Safe Chat.

Needs no server and works in a throwaway data directory:

    python3 tools/familytests.py            # everything
    python3 tools/familytests.py shield     # one group (shield, accounts,
                                            # social, privacy, play, money,
                                            # bots, game, insights, pages)

The groups prove the rules rather than assume them: a child in "approve"
mode really cannot gain a friend without the parent's OK, a phone number in
a message really never reaches the other side, the daily limit really kicks
a child out of a round, and nothing a stranger can see says an account is a
child's or has a parent.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import traceback

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from app import config  # noqa: E402

_tmp = tempfile.mkdtemp(prefix="bh-familytests-")
config.DATA_DIR = config.Path(_tmp)
config.DB_PATH = config.DATA_DIR / "t.sqlite3"
os.environ["BLOCKHAVEN_BOTS"] = "0"

from app import db  # noqa: E402

RESULTS = {"pass": 0, "fail": 0}


def check(cond, label):
    if cond:
        RESULTS["pass"] += 1
    else:
        RESULTS["fail"] += 1
        print("  FAIL  %s" % label)


def raises(fn, exc_type, label):
    try:
        fn()
    except exc_type:
        RESULTS["pass"] += 1
        return
    except Exception as exc:  # pragma: no cover - reported
        RESULTS["fail"] += 1
        print("  FAIL  %s (raised %r)" % (label, exc))
        return
    RESULTS["fail"] += 1
    print("  FAIL  %s (did not raise)" % label)


def setup():
    from app import bootstrap
    db.init_db()
    bootstrap.sync_catalog()
    from app.models import worlds
    worlds.ensure_rows()


# ------------------------------------------------------------------ fixtures

_n = [0]


def player(prefix="Player"):
    from app.models import users
    _n[0] += 1
    return users.create_user("%s%d" % (prefix, _n[0]), "pass1234")


def parent(prefix="Mum"):
    from app.family import accounts
    _n[0] += 1
    name = "%s%d" % (prefix, _n[0])
    return accounts.create(name, "longenough1", "Sam", "%s@example.com" % name.lower(),
                           "parent", "America/New_York", -300, {"utm_source": "facebook"})


def kid(par, name=None, controls=None, year=None):
    from app.family import children
    _n[0] += 1
    return children.create(par, "Mia", year or (time.gmtime().tm_year - 9),
                           name or "Kid%d" % _n[0], "kidpass9",
                           {"body_type": "female", "colors": {"torso": "#c4281c"}},
                           controls or {})


def befriend(a, b):
    db.execute("INSERT OR REPLACE INTO friendships(user_low,user_high,requester_id,status,"
               "created_at,updated_at) VALUES(?,?,?,'accepted',?,?)",
               (min(a, b), max(a, b), a, int(time.time()), int(time.time())))


def make_bot():
    from app.models import users
    bot = player("Bot")
    db.execute("UPDATE users SET is_bot=1 WHERE id=?", (bot["id"],))
    return users.get_by_id(int(bot["id"]))


# -------------------------------------------------------------------- groups

def test_shield():
    from app.family import shield
    allow = ["gg", "good game. gg", "3 in a row!", "only 1 way in", "10 kills in a row",
             "my phone is dead brb", "my xbox is broken", "meet me at the flag",
             "follow me to the cart", "add me", "i have 1000000 noogets",
             "call me when ur ready", "score is 12 - 8", "push the steam cart",
             "hold the signal cabin", "my number one fan", "2nd place again",
             "we won 12 games in a row", "cockpit view", "nice shot!", "lol"]
    for text in allow:
        check(shield.scan(text).action == "allow", "allowed: %r" % text)
    check(shield.scan("are you alone? need help", channel="game").action == "allow",
          "game chat: 'are you alone' is gameplay")
    block = ["my number is 555-123-4567", "five five five one two three four",
             "email me bob.smith@gmail.com", "its bob at gmail dot com",
             "i live at 42 maple street", "123 Oak Way is my house", "add me on snap",
             "add me on s n a p", "dm me on d1sc0rd", "my snap is coolkid_22",
             "r u on discord", "discord.gg/abc", "check out www.example.com",
             "where do you live", "dont tell your parents", "send me a pic", "kys",
             "are you home alone", "are you alone right now", "whats your real name",
             "asl?", "my xbox gamertag is Kid123", "text me"]
    for text in block:
        check(shield.scan(text).blocked, "blocked: %r" % text)
    check(shield.scan("i want to die lol").action == "flag", "wellbeing flagged")
    check(shield.scan("this is shit").masked == "this is •••", "language masked")
    check(shield.scan("sh1t").action == "mask", "leetspeak language masked")
    v = shield.scan("call 555 123 4567 now")
    check("555" not in v.masked, "phone number blanked in the excerpt")
    # asking to meet somewhere: stopped in private, left alone in a game
    for text in ("meet me at the park after school", "wanna meet up?", "can we meet tomorrow",
                 "lets meet at the mall"):
        check(shield.scan(text).blocked, "meet-up blocked: %r" % text)
    for text in ("nice to meet you", "i want to meet new friends", "lets meet in the lobby",
                 "meet me at the spawn"):
        check(shield.scan(text).action == "allow", "not a meet-up: %r" % text)
    check(shield.scan("meet me at the park", channel="game").action == "allow",
          "game chat: meeting places are gameplay")
    # the parent's excerpt blanks the details and keeps the words around them
    ex = shield.excerpt("my number is 555 201 3344 text me")
    check("555" not in ex and ex.startswith("my number is"), "excerpt keeps context: %r" % ex)
    check(shield.excerpt("meet me at the park") == "meet me at the park", "meet-up quoted whole")
    check("maple" not in shield.excerpt("i live at 42 maple street"), "address blanked")
    check("fuck" not in shield.excerpt("this fucking map"), "language blanked for parents")
    check(shield.username_warnings("Mia2015", "Mia", 2015), "username warnings")
    check(not shield.username_warnings("PixelPanda42", "Mia", 2015), "clean username")


def test_accounts():
    from app.family import accounts, children
    from app.models import users
    p = parent()
    check(p["display_name"] == "Sam" and p["timezone"] == "America/New_York", "parent stored")
    check(accounts.authenticate(p["username"], "longenough1")["id"] == p["id"], "auth by name")
    check(accounts.authenticate(p["email"].upper(), "longenough1")["id"] == p["id"],
          "auth by email (any case)")
    raises(lambda: accounts.authenticate(p["username"], "wrong"), accounts.ParentError,
           "wrong password refused")
    raises(lambda: accounts.create("signup_l", "longenough1", "X", "a@b.co"),
           accounts.ParentError, "reserved name refused")
    pl = player()
    raises(lambda: accounts.create(pl["username"], "longenough1", "X", "q@b.co"),
           accounts.ParentError, "a player's name cannot be a parent's")
    raises(lambda: users.create_user(p["username"], "pass1234"), users.AuthError,
           "a parent's name cannot be a player's")
    raises(lambda: accounts.create("NewMum1", "short", "X", "x@y.co"), accounts.ParentError,
           "short parent password refused")
    raises(lambda: accounts.create("NewMum2", "longenough1", "X", p["email"]),
           accounts.ParentError, "duplicate email refused")
    sess = accounts.start_session(int(p["id"]))
    got = accounts.session_for(sess["token"])
    check(got and got["parent"]["id"] == p["id"] and got["csrf"] == sess["csrf"], "session")
    accounts.end_session(sess["token"])
    check(accounts.session_for(sess["token"]) is None, "session ended")
    # children: up to the limit, and the link private to this parent
    kids = [kid(p) for _ in range(config.FAMILY_MAX_CHILDREN)]
    raises(lambda: kid(p), children.ChildError, "a fifth child refused")
    other = parent()
    check(children.get(int(other["id"]), kids[0]["id"]) is None,
          "another parent cannot reach my child")
    check(children.get(int(p["id"]), kids[0]["username"])["id"] == kids[0]["id"],
          "child by username")
    check(children.directory.is_child(kids[0]["id"]), "directory knows the child")
    check(not children.directory.is_child(pl["id"]), "a player is not a child")
    from app.models import avatars
    raw = avatars.raw_avatar(int(kids[0]["id"]))
    check(raw["body_type"] == "female" and raw["colors"]["torso"] == "#c4281c", "look applied")
    privacy = users.privacy_of(users.get_by_id(int(kids[0]["id"])))
    check(privacy["wall"] == "friends" and privacy["online"] == "friends",
          "child privacy defaults")
    raises(lambda: kid(other, name="5551234567"), children.ChildError,
           "phone-number username refused")
    # pausing signs the child out and stops sign-in
    child = kids[1]
    users.start_session(int(child["id"]))
    children.set_paused(int(p["id"]), int(child["id"]), True)
    check(db.scalar("SELECT COUNT(*) FROM sessions WHERE user_id=?", (child["id"],)) == 0,
          "pause ends sessions")
    raises(lambda: users.authenticate(child["username"], "kidpass9"), users.AuthError,
           "paused child cannot sign in")
    children.set_paused(int(p["id"]), int(child["id"]), False)
    check(users.authenticate(child["username"], "kidpass9")["id"] == child["id"],
          "resumed child signs in")
    children.reset_password(int(p["id"]), int(child["id"]), "newpass77")
    check(users.authenticate(child["username"], "newpass77")["id"] == child["id"],
          "parent reset the child's password")
    # deleting the family deletes the children with it
    theirs = kid(other)
    gone = accounts.delete(int(other["id"]))
    check(gone == 1 and accounts.get(int(other["id"])) is None, "family deleted")
    check(users.get_by_id(int(theirs["id"])) is None, "their child's account went too")
    check(not children.directory.is_child(theirs["id"]), "directory forgot the child")


def test_social():
    from app.family import children, guard
    from app.models import users
    from app.social import comments, friends, messages
    p = parent()
    child = kid(p)
    cid = int(child["id"])
    stranger = player()
    pal = player()
    # messages: friends only by default, both ways, without saying why
    raises(lambda: messages.send(cid, stranger["username"], "", "hi"),
           messages.MessageError, "child cannot message a non-friend")
    try:
        messages.send(int(stranger["id"]), child["username"], "", "hi there")
        check(False, "stranger reached the child")
    except messages.MessageError as exc:
        check("child" not in str(exc).lower() and "parent" not in str(exc).lower(),
              "refusal does not give the child away: %s" % exc)
    befriend(cid, int(pal["id"]))
    check(messages.send(cid, pal["username"], "", "want to play sky sprint?") > 0,
          "child messages a friend")
    raises(lambda: messages.send(cid, pal["username"], "", "my number is 555 123 4567"),
           messages.MessageError, "child's phone number stopped")
    raises(lambda: messages.send(int(pal["id"]), child["username"], "", "add me on snap"),
           messages.MessageError, "invite to another app stopped on the way in")
    alerts = db.query("SELECT kind FROM family_alerts WHERE user_id=?", (cid,))
    kinds = {r["kind"] for r in alerts}
    check({"blocked_out", "blocked_in"} <= kinds, "parent told about both: %s" % kinds)
    mid = messages.send(int(pal["id"]), child["username"], "", "that was shit lol")
    body = db.scalar("SELECT body FROM messages WHERE id=?", (mid,))
    check("shit" not in body, "strong language blanked for the child")
    # friends: a new child chooses their own friends until the parent switches
    # approval on; then "approve" holds every new friendship for the parent
    fresh = children.get(int(p["id"]), child["username"])["controls"]
    check(fresh["friends"] == "open", "new friends: they choose, by default")
    check(fresh["weekday_minutes"] is None and fresh["weekend_minutes"] is None,
          "no daily limits, by default")
    check(fresh["quiet"] is False, "quiet hours off, by default")
    check(guard.check_join(cid, "sky_sprint") is None, "a new child can join at any hour")
    children.set_controls(int(p["id"]), cid, {"friends": "approve"})
    other = player()
    state = friends.request(cid, int(other["id"]))
    check(state == "awaiting_parent", "child's request waits for the parent")
    check(friends.relationship(cid, int(other["id"])) is None, "nothing sent yet")
    appr = db.query_one("SELECT id FROM family_approvals WHERE child_id=? AND other_id=?",
                        (cid, other["id"]))
    check(appr is not None, "approval queued")
    check(children.decide_approval(int(p["id"]), cid, int(appr["id"]), True) == "requested",
          "parent OK sends the request")
    check(friends.accept(int(other["id"]), cid) == "friends", "the other side accepts")
    check(friends.are_friends(cid, int(other["id"])), "now friends")
    asker = player()
    check(friends.request(int(asker["id"]), cid) == "pending_out", "someone asks the child")
    check(friends.accept(cid, int(asker["id"])) == "awaiting_parent", "child says yes: held")
    check(not friends.are_friends(cid, int(asker["id"])), "not friends before the OK")
    appr = db.query_one("SELECT id FROM family_approvals WHERE child_id=? AND other_id=?",
                        (cid, asker["id"]))
    check(children.decide_approval(int(p["id"]), cid, int(appr["id"]), True) == "friends",
          "parent OK completes it")
    check(friends.are_friends(cid, int(asker["id"])), "friends after the OK")
    rude = player()
    friends.request(int(rude["id"]), cid)
    friends.accept(cid, int(rude["id"]))
    appr = db.query_one("SELECT id FROM family_approvals WHERE child_id=? AND other_id=?",
                        (cid, rude["id"]))
    children.decide_approval(int(p["id"]), cid, int(appr["id"]), False)
    check(friends.relationship(cid, int(rude["id"])) is None, "declined request removed")
    children.set_controls(int(p["id"]), cid, {"friends": "off"})
    raises(lambda: friends.request(int(player()["id"]), cid), friends.FriendError,
           "friends off: requests refused")
    children.set_controls(int(p["id"]), cid, {"friends": "open"})
    newbie = player()
    friends.request(int(newbie["id"]), cid)
    check(friends.accept(cid, int(newbie["id"])) == "friends", "open: child decides")
    # profile comments: friends only, and Safe Chat
    raises(lambda: comments.add_to_profile(cid, int(stranger["id"]), "hi!"),
           comments.CommentError, "stranger cannot comment on the child's wall")
    check(comments.add_to_profile(cid, int(pal["id"]), "gg today!") > 0, "friend comments")
    raises(lambda: comments.add_to_profile(cid, int(pal["id"]), "where do you live?"),
           comments.CommentError, "risky comment stopped")
    raises(lambda: comments.add_to_profile(int(pal["id"]), cid, "my insta is mia_rocks"),
           comments.CommentError, "child's own risky comment stopped")
    # the guard costs nothing for everybody else
    check(guard.filter_message(int(stranger["id"]), dict(pal), "", "add me on snap")
          == ("", "add me on snap"), "adults are not filtered")


def test_privacy():
    from app.family import children
    from app.models import users
    from app.social import feed
    p = parent()
    child = kid(p, name="HiddenKid%d" % int(time.time() % 10000))
    cid = int(child["id"])
    users.set_privacy(cid, {"wall": "public", "online": "public", "friends_list": "public"})
    priv = users.privacy_of(users.get_by_id(cid))
    check(priv["wall"] == "friends" and priv["online"] == "friends"
          and priv["friends_list"] == "friends", "child cannot loosen past the rules")
    users.set_privacy(cid, {"wall": "private"})
    check(users.privacy_of(users.get_by_id(cid))["wall"] == "private",
          "child can tighten further")
    children.set_controls(int(p["id"]), cid, {"presence": "nobody"})
    check(users.privacy_of(users.get_by_id(cid))["online"] == "private",
          "parent's presence rule applies at once")
    users.update_profile(cid, "I love dragons! call me 555-123-4567", "Springfield, Ohio")
    row = users.get_by_id(cid)
    check("555" not in row["blurb"] and "dragons" in row["blurb"], "About Me scrubbed")
    check(row["location"] == "", "no location for a child")
    names = [u["username"] for u in users.recent(50)]
    check(child["username"] not in names, "child not in the newest arrivals")
    check(child["username"] not in [u["username"] for u in users.search("hiddenkid")],
          "child not found by a partial search")
    check(child["username"] in [u["username"] for u in users.search(child["username"])],
          "child found by their exact username")
    check(child["username"] not in [u["username"] for u in users.suggest("hiddenk")],
          "child not suggested by a partial name")
    check(child["username"] in [u["username"] for u in users.search("hiddenkid", 40,
                                                                    include_children=True)],
          "admin search sees the child")
    pal = player()
    befriend(cid, int(pal["id"]))
    texts = " ".join(e["text"] for e in feed.recent_activity(40))
    check(child["username"] not in texts, "a child's friendships are not news")
    public = users.public(users.get_by_id(cid))
    check(not any(k in public for k in ("parent", "family", "child")), "public() is clean")


def test_play():
    from app.family import activity, children, guard
    p = parent()
    child = kid(p, controls={"weekday_minutes": 30, "weekend_minutes": 30, "quiet": False,
                             "worlds_blocked": ["last_light"]})
    cid = int(child["id"])
    check(guard.check_join(cid, "last_light") is not None, "switched-off world refused")
    check(guard.check_join(cid, "sky_sprint") is None, "allowed world joins")
    check(guard.ticket_flags(cid) == {"chat": "safe"}, "ticket carries Safe Chat")
    check(guard.ticket_flags(int(player()["id"])) is None, "players carry nothing")
    beat = {"instances": [{"id": 1, "players": [{"user_id": cid, "bot": False}]}]}
    tr = activity.tracker
    tr.seen.pop(cid, None)
    t0 = time.time()
    tr.on_heartbeat("sky_sprint", beat)
    tr.seen[cid] = ("sky_sprint", time.time() - 8)
    tr.on_heartbeat("sky_sprint", beat)
    check(7 <= tr.seconds_today(children.directory.get(cid)) <= 11, "seconds metered")
    # spend the rest of the day's half hour and the next beat kicks
    info = children.directory.get(cid)
    local = activity._local(info, time.time())
    key = (cid, local.strftime("%Y-%m-%d"), local.hour, "sky_sprint")
    tr.pending[key] = tr.pending.get(key, 0) + 30 * 60
    tr.seen[cid] = ("sky_sprint", time.time() - 2)
    reply = tr.on_heartbeat("sky_sprint", beat)
    check(reply and reply["kick"] and reply["kick"][0]["uid"] == cid, "limit kicks")
    check("play time" in reply["kick"][0]["reason"], "kid-friendly reason")
    check(guard.check_join(cid, "sky_sprint") is not None, "no new rounds once used up")
    tr.flush()
    stored = db.scalar("SELECT SUM(seconds) FROM family_playtime WHERE user_id=?", (cid,))
    check(stored >= 30 * 60, "flushed to the database")
    check(db.scalar("SELECT COUNT(*) FROM family_alerts WHERE user_id=? AND"
                    " kind='limit_reached'", (cid,)) == 1, "parent told once")
    check(db.scalar("SELECT COUNT(*) FROM family_play_log WHERE user_id=?", (cid,)) >= 1,
          "session logged")
    # warnings before the limit
    kid2 = kid(p, controls={"weekday_minutes": 30, "weekend_minutes": 30, "quiet": False})
    k2 = int(kid2["id"])
    info2 = children.directory.get(k2)
    local = activity._local(info2, time.time())
    tr.pending[(k2, local.strftime("%Y-%m-%d"), local.hour, "sky_sprint")] = 26 * 60
    beat2 = {"instances": [{"id": 1, "players": [{"user_id": k2, "bot": False}]}]}
    reply = tr.on_heartbeat("sky_sprint", beat2)
    check(reply and reply["notice"] and "5 minutes" in reply["notice"][0]["text"],
          "five-minute warning")
    check(not (tr.on_heartbeat("sky_sprint", beat2) or {}).get("notice"),
          "warning given once")
    # quiet hours straddling now
    kid3 = kid(p)
    k3 = int(kid3["id"])
    now_local = activity._local(children.directory.get(k3), time.time())
    start = (now_local.hour - 1) % 24
    end = (now_local.hour + 1) % 24
    children.set_controls(int(p["id"]), k3, {"quiet": True,
                                              "quiet_start": "%02d:00" % start,
                                              "quiet_end": "%02d:00" % end})
    check("quiet" in (guard.check_join(k3, "sky_sprint") or ""), "quiet hours refuse")
    banner = guard.banner({"id": k3})
    check(banner and banner["quiet_now"], "the child's strip says quiet time")
    children.set_controls(int(p["id"]), k3, {"weekday_minutes": 0, "weekend_minutes": 0,
                                              "quiet": False})
    check("No games" in (guard.check_join(k3, "sky_sprint") or ""), "a zero-minute day")


def test_money():
    from app.family import children, guard
    p = parent()
    child = kid(p, year=time.gmtime().tm_year - 9)
    cid = int(child["id"])
    check(guard.check_crates(cid) is not None, "crates off by default under 13")
    check(guard.check_spend(cid, "crate_classic") is not None, "buying a crate is a crate")
    check(guard.check_spend(cid, "hat_red_cap") is None, "a hat is fine")
    children.set_controls(int(p["id"]), cid, {"spending": False})
    check(guard.check_spend(cid, "hat_red_cap") is not None, "spending switched off")
    teen = kid(p, year=time.gmtime().tm_year - 14)
    check(guard.check_crates(int(teen["id"])) is None, "crates on by default for 13+")


def test_bots():
    from app.bots import social
    p = parent()
    child = kid(p)
    cid = int(child["id"])
    bot = make_bot()
    bid = int(bot["id"])
    check(social.request_friend(bid, cid) == "blocked", "bot cannot friend a child")
    check(social.dm(bid, child["username"], "hey") is None, "bot cannot DM a child")
    check(social.comment(bid, cid, "nice profile") is None, "bot cannot comment")
    from app.models import users
    check(not social.wall_open_to(users.get_by_id(cid), bid), "child's wall closed to bots")
    from app.social import friends, messages
    raises(lambda: friends.request(cid, bid), friends.FriendError,
           "child cannot friend a bot")
    raises(lambda: messages.send(cid, bot["username"], "", "hi"), messages.MessageError,
           "child cannot DM a bot")


def test_game():
    """Safe Chat in a game instance, with a stand-in host and sockets."""
    from app.game.instance import GameInstance, Player

    class Host:
        def __init__(self):
            self.reports = []

        def queue_report(self, report):
            self.reports.append(report)

    class Sock:
        def __init__(self):
            self.sent = []

        def send_json(self, payload):
            self.sent.append(payload)

    inst = GameInstance.__new__(GameInstance)
    inst.host = Host()
    inst.world_id = "sky_sprint"
    inst.players = {}
    inst.chat_log = []
    inst.bots = None
    import threading
    inst.lock = threading.RLock()

    def seat(pid, uid, name, family=None):
        p = Player(pid, uid, name, {}, Sock())
        p.family = family
        p.team = "red"
        inst.players[pid] = p
        return p

    adult = seat(1, 101, "Adult")
    child = seat(2, 102, "Kiddo", {"chat": "safe"})
    muted = seat(3, 103, "Quiet", {"chat": "off"})
    inst.handle_chat(adult, {"m": "add me on snap: creep99"})
    check(any(m.get("m") == "add me on snap: creep99" for m in adult.ws.sent),
          "adults see adults")
    check(not any(m.get("from") == "Adult" for m in child.ws.sent), "child never sees it")
    check(not any(m.get("from") == "Adult" for m in muted.ws.sent), "chat-off child neither")
    check(any(r["event"] == "heard" for r in inst.host.reports), "reported for the parent")
    inst.handle_chat(adult, {"m": "that was shit lol"})
    seen = [m["m"] for m in child.ws.sent if m.get("from") == "Adult"]
    check(seen and "shit" not in seen[-1], "language blanked for the child")
    before = len(adult.ws.sent)
    inst.handle_chat(child, {"m": "my number is 555 123 4567"})
    check(len(adult.ws.sent) == before, "child's phone number never broadcast")
    check(any("wasn't sent" in m.get("m", "") for m in child.ws.sent), "child told kindly")
    inst.handle_chat(child, {"m": "gg everyone"})
    check(any(m.get("m") == "gg everyone" for m in adult.ws.sent), "child's gg goes out")
    inst.handle_chat(muted, {"m": "hello"})
    check(any("switched off" in m.get("m", "") for m in muted.ws.sent), "chat off says so")
    hist = inst.chat_history_for(child)
    check(all("snap" not in e.get("m", "") for e in hist), "history filtered for the child")
    check(any("snap" in e.get("m", "") for e in inst.chat_history_for(adult)),
          "history unchanged for adults")
    check("family" not in adult.public() and "family" not in child.public(),
          "nobody is told who is a child")


def test_insights():
    from app.family import children, insights
    from app.social import messages
    p = parent()
    child = kid(p)
    cid = int(child["id"])
    pal = player()
    befriend(cid, int(pal["id"]))
    messages.send(cid, pal["username"], "", "see you in prop panic")
    messages.send(int(pal["id"]), child["username"], "", "ok!")
    db.execute("INSERT INTO family_playtime(user_id, day, hour, world_id, seconds)"
               " VALUES(?,?,?,?,?)", (cid, time.strftime("%Y-%m-%d"), 16, "prop_panic", 1500))
    report = insights.child_report(children.get(int(p["id"]), cid))
    for key in ("status", "play", "sessions", "signins", "social", "messages", "wall",
                "alerts", "achievements", "controls"):
        check(key in report, "report has %s" % key)
    check(len(report["play"]["chart"]) == 14, "fourteen days charted")
    check(report["social"]["count"] == 1, "one friend")
    check(report["messages"]["threads"][0]["total"] == 2, "conversation counted")
    tr = insights.transcript(children.get(int(p["id"]), cid), pal["username"])
    check(len(tr["rows"]) == 2 and tr["rows"][0]["mine"], "transcript in order")
    over = insights.family_overview(p, children.list_for(int(p["id"])))
    check(over and over[0]["username"] == child["username"], "hub overview")


def test_pages():
    """The family routes through the real dispatcher (no sockets)."""
    from app import webapp
    from app.http.router import Request
    from app.family import accounts

    def call(method, path, body=b"", headers=None, cookies=""):
        hdrs = {"host": "localhost", "user-agent": "tests"}
        if cookies:
            hdrs["cookie"] = cookies
        hdrs.update(headers or {})
        path_only, _, query = path.partition("?")
        req = Request(method, path_only, query, hdrs, body, "127.0.0.1")
        return webapp.dispatch(req)

    resp = call("GET", "/parent_signup_l?utm_source=facebook&utm_campaign=fall")
    check(resp.status == 200 and b"parent-signup?utm_source=facebook" in resp.body,
          "landing page carries the campaign on to sign-up")
    resp = call("GET", "/parent-signup")
    check(resp.status == 200 and b"guardian" in resp.body, "sign-up page")
    form = ("display_name=Alex&email=alex%40example.com&username=AlexFamily&password="
            "supersecret1&guardian=1&timezone=Europe%2FLondon&tz_offset=0&utm_source=facebook")
    resp = call("POST", "/parent-signup", form.encode(),
                {"content-type": "application/x-www-form-urlencoded"})
    check(resp.status == 303 and resp.headers["Location"] == "/parent_AlexFamily/setup?welcome=1",
          "sign-up lands on the set-up")
    cookie = [c for c in resp.cookies if c.startswith(config.FAMILY_COOKIE)][0].split(";")[0]
    check(accounts.get_by_username("AlexFamily")["source"].find("facebook") > 0,
          "campaign stored")
    resp = call("GET", "/parent_AlexFamily/setup?welcome=1", cookies=cookie)
    check(resp.status == 200 and b"you'll want your child" in resp.body.lower().replace(b"&rsquo;", b"'"),
          "set-up asks for the child")
    resp = call("GET", "/parent_AlexFamily", cookies=cookie)
    check(resp.status == 200, "the parent's page")
    resp = call("GET", "/parent_SomebodyElse")
    check(resp.status == 303 and resp.headers["Location"].startswith("/parent-signin"),
          "signed out: to the sign-in, whoever it was")
    resp = call("GET", "/parent_SomebodyElse", cookies=cookie)
    check(resp.status == 303 and resp.headers["Location"] == "/parent_AlexFamily",
          "another family's page: back to your own")
    fam = accounts.session_for(cookie.split("=", 1)[1])
    import json
    payload = json.dumps({"first_name": "Robin", "birth_year": time.gmtime().tm_year - 8,
                          "username": "RobinRocket7", "password": "robinpass",
                          "look": {"body_type": "male", "colors": {"torso": "#c4281c"}},
                          "controls": {"weekday_minutes": 45}}).encode()
    resp = call("POST", "/api/family/children", payload,
                {"content-type": "application/json"}, cookies=cookie)
    check(resp.status == 403, "API refuses without the parent's CSRF token")
    resp = call("POST", "/api/family/children", payload,
                {"content-type": "application/json", "x-csrf-token": fam["csrf"]},
                cookies=cookie)
    data = json.loads(resp.body)
    check(resp.status == 200 and data.get("ok"), "child created over the API: %s" % data)
    resp = call("GET", "/parent_AlexFamily/child/RobinRocket7", cookies=cookie)
    check(resp.status == 200 and b"RobinRocket7" in resp.body, "the child's dashboard")
    resp = call("GET", "/profile/RobinRocket7")
    body = resp.body.decode("utf-8", "replace")
    check(resp.status == 200 and "AlexFamily" not in body and "Alex" not in body.split("<title>")[0]
          and "family" not in body.lower().split("for parents")[0].split("parent_signup_l")[0]
          .replace("family-", ""),
          "the child's public profile says nothing of the family")
    check("AlexFamily" not in body, "parent never named on the child's profile")
    resp = call("GET", "/parent_AlexFamily/child/RobinRocket7")
    check(resp.status == 303, "dashboard needs the parent")


GROUPS = [("shield", test_shield), ("accounts", test_accounts), ("social", test_social),
          ("privacy", test_privacy), ("play", test_play), ("money", test_money),
          ("bots", test_bots), ("game", test_game), ("insights", test_insights),
          ("pages", test_pages)]


def main(argv):
    setup()
    wanted = set(argv[1:]) or {name for name, _ in GROUPS}
    for name, fn in GROUPS:
        if name not in wanted:
            continue
        before = RESULTS["fail"]
        try:
            fn()
        except Exception:
            RESULTS["fail"] += 1
            print("  FAIL  %s crashed:" % name)
            traceback.print_exc()
        print("%-9s %s" % (name, "ok" if RESULTS["fail"] == before else "FAILED"))
    print("\n%d passed, %d failed  (data in %s)" % (RESULTS["pass"], RESULTS["fail"], _tmp))
    return 1 if RESULTS["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
