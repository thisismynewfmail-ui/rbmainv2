"""Play-time metering, limits and quiet hours.

The game hosts already tell the web server who is in every round, every
couple of seconds (``/internal/heartbeat``).  This module listens to those
beats for child accounts only and keeps three things from them:

* ``family_playtime``: seconds played per child, per day and hour of the
  *family's own* calendar, per world -- the daily limit, the week's chart,
  the heat map and the world breakdown all come from it;
* ``family_play_log``: one row per stretch of play in one world, for the
  sessions timeline;
* the verdicts: a child out of time, inside quiet hours, paused, or in a
  world their parent has switched off is sent back with the heartbeat's
  reply as a kick, and one coming up on a limit gets a five-minute and a
  one-minute warning in their chat.

Time is counted from what the hosts report rather than from the client, so
it cannot be paused by a closed laptop lid or a doctored page: a stretch
between two sightings counts only up to GAP_CAP seconds, so a host that
stalls never books time nobody played.  Writes are batched (every
FLUSH_EVERY seconds), and the joins check (`play_block`) adds the
not-yet-written seconds, so the limit is exact either way.
"""
from __future__ import annotations

import atexit
import datetime as _dt
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from .. import db
from . import children, controls as rules

FLUSH_EVERY = 15.0
GAP_CAP = 10.0
SESSION_GAP = 25.0
REKICK_AFTER = 8.0
WARN_AT = (300, 60)


def _local(info: Dict[str, Any], at: float) -> _dt.datetime:
    return _dt.datetime.fromtimestamp(at, info["tz"])


def _world_name(world_id: str) -> str:
    from ..models import worlds
    world = worlds.get_any(world_id)
    return world["name"] if world else world_id


class Tracker:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.pending: Dict[Tuple[int, str, int, str], float] = {}
        self.seen: Dict[int, Tuple[str, float]] = {}
        self.sessions: Dict[int, Dict[str, Any]] = {}
        self.warned: Dict[Tuple[int, str], set] = {}
        self.kicked: Dict[int, float] = {}
        self.last_flush = time.time()

    # -------------------------------------------------------------- totals
    def seconds_today(self, info: Dict[str, Any], at: Optional[float] = None) -> float:
        at = time.time() if at is None else at
        day = _local(info, at).strftime("%Y-%m-%d")
        uid = int(info["uid"])
        stored = float(db.scalar("SELECT COALESCE(SUM(seconds),0) FROM family_playtime"
                                 " WHERE user_id=? AND day=?", (uid, day)))
        with self.lock:
            extra = sum(v for (u, d, _h, _w), v in self.pending.items()
                        if u == uid and d == day)
        return stored + extra

    def _add(self, uid: int, info: Dict[str, Any], world_id: str,
             seconds: float, at: float) -> None:
        local = _local(info, at)
        key = (uid, local.strftime("%Y-%m-%d"), local.hour, world_id)
        self.pending[key] = self.pending.get(key, 0.0) + seconds

    # ------------------------------------------------------------ sessions
    def _open(self, uid: int, world_id: str, at: float) -> None:
        cur = db.execute("INSERT INTO family_play_log(user_id, world_id, started_at,"
                         " ended_at, seconds) VALUES(?,?,?,?,0)",
                         (uid, world_id, int(at), int(at)))
        self.sessions[uid] = {"id": int(cur.lastrowid), "world": world_id,
                              "start": at, "last": at, "ended_by": ""}

    def _close(self, uid: int, ended_by: str = "") -> None:
        sess = self.sessions.pop(uid, None)
        if sess is None:
            return
        db.execute("UPDATE family_play_log SET ended_at=?, seconds=?, ended_by=?"
                   " WHERE id=?", (int(sess["last"]), int(sess["last"] - sess["start"]),
                                   ended_by or sess.get("ended_by", ""), sess["id"]))

    def _session(self, uid: int, world_id: str, at: float) -> None:
        sess = self.sessions.get(uid)
        if sess and sess["world"] == world_id and at - sess["last"] <= SESSION_GAP:
            sess["last"] = at
            return
        if sess:
            self._close(uid)
        self._open(uid, world_id, at)

    # ------------------------------------------------------------- the beat
    def on_heartbeat(self, world_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = time.time()
        present: List[Tuple[int, Dict[str, Any]]] = []
        for inst in payload.get("instances") or []:
            for player in inst.get("players") or []:
                if player.get("bot"):
                    continue
                try:
                    uid = int(player.get("user_id") or 0)
                except (TypeError, ValueError):
                    continue
                info = children.directory.get(uid)
                if info is not None:
                    present.append((uid, info))
        kicks: List[Dict[str, Any]] = []
        notices: List[Dict[str, Any]] = []
        with self.lock:
            for uid, info in present:
                prev = self.seen.get(uid)
                if prev and prev[0] == world_id:
                    elapsed = max(0.0, min(GAP_CAP, now - prev[1]))
                    if elapsed:
                        self._add(uid, info, world_id, elapsed, now)
                self.seen[uid] = (world_id, now)
                self._session(uid, world_id, now)
                reason, kind = play_block(info, world_id, now, tracker=self)
                if reason:
                    if now - self.kicked.get(uid, 0.0) >= REKICK_AFTER:
                        self.kicked[uid] = now
                        kicks.append({"uid": uid, "reason": reason})
                        sess = self.sessions.get(uid)
                        if sess:
                            sess["ended_by"] = kind
                        self._note_kick(uid, info, kind, world_id, now)
                    continue
                notices.extend(self._warnings(uid, info, now))
            here = {uid for uid, _ in present}
            for uid, sess in list(self.sessions.items()):
                if sess["world"] == world_id and uid not in here and now - sess["last"] > 4:
                    self._close(uid)
            self._sweep(now)
            if now - self.last_flush >= FLUSH_EVERY:
                self._flush(now)
        if not kicks and not notices:
            return None
        return {"kick": kicks, "notice": notices}

    def _warnings(self, uid: int, info: Dict[str, Any], now: float) -> List[Dict[str, Any]]:
        c = info["controls"]
        local = _local(info, now)
        day = local.strftime("%Y-%m-%d")
        done = self.warned.setdefault((uid, day), set())
        out = []
        limit = rules.limit_minutes(c, local.date())
        if limit:
            left = limit * 60 - self.seconds_today(info, now)
            for mark in WARN_AT:
                tag = "limit%d" % mark
                if left <= mark and tag not in done:
                    done.add(tag)
                    out.append({"uid": uid, "text": (
                        "5 minutes of play left today -- start wrapping up!" if mark == 300
                        else "1 minute left today -- time to say bye!")})
                    break
        if c.get("quiet"):
            start = c.get("quiet_start") or "21:00"
            hours, minutes = (int(x) for x in start.split(":"))
            begins = local.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            if begins < local:
                begins += _dt.timedelta(days=1)
            until = (begins - local).total_seconds()
            for mark in (600, 60):
                tag = "quiet%d" % mark
                if until <= mark and tag not in done:
                    done.add(tag)
                    out.append({"uid": uid, "text": (
                        "Quiet time starts at %s -- 10 minutes to go." % rules.clock_label(start)
                        if mark == 600 else
                        "Quiet time in 1 minute -- time to say goodnight!")})
                    break
        return out

    def _note_kick(self, uid: int, info: Dict[str, Any], kind: str, world_id: str,
                   now: float) -> None:
        """Tell the parent once a day that a limit did its job."""
        if kind not in ("limit", "quiet"):
            return
        local = _local(info, now)
        day = local.strftime("%Y-%m-%d")
        done = self.warned.setdefault((uid, day), set())
        tag = "noted_" + kind
        if tag in done:
            return
        done.add(tag)
        from . import guard
        first = info.get("first_name") or "Your child"
        when = local.strftime("%I:%M %p").lstrip("0").lower()
        if kind == "limit":
            guard.alert(uid, "limit_reached", "info", "game", "Daily play time used up",
                        "%s reached today's play limit and was signed out of %s at %s."
                        % (first, _world_name(world_id), when), world_id=world_id)
        else:
            guard.alert(uid, "quiet_hours", "info", "game", "Quiet hours started",
                        "Quiet hours began, so %s left %s at %s."
                        % (first, _world_name(world_id), when), world_id=world_id)

    def _sweep(self, now: float) -> None:
        for uid, sess in list(self.sessions.items()):
            if now - sess["last"] > SESSION_GAP:
                self._close(uid)
        for uid, (_w, seen_at) in list(self.seen.items()):
            if now - seen_at > 600:
                self.seen.pop(uid, None)
        if len(self.warned) > 2000 or (int(now) % 600 == 0):
            cutoff = _dt.date.fromtimestamp(now - 3 * 86400).strftime("%Y-%m-%d")
            for key in [k for k in self.warned if k[1] < cutoff]:
                self.warned.pop(key, None)
        for uid, at in list(self.kicked.items()):
            if now - at > 3600:
                self.kicked.pop(uid, None)

    # ---------------------------------------------------------------- flush
    def _flush(self, now: Optional[float] = None) -> None:
        now = time.time() if now is None else now
        self.last_flush = now
        rows = []
        for key, seconds in list(self.pending.items()):
            whole = int(seconds)
            if whole <= 0:
                continue
            rows.append(key + (whole,))
            remainder = seconds - whole
            if remainder > 0.001:
                self.pending[key] = remainder
            else:
                self.pending.pop(key, None)
        live = [(int(s["last"]), int(s["last"] - s["start"]), s["id"])
                for s in self.sessions.values()]
        if not rows and not live:
            return
        try:
            with db.transaction() as conn:
                conn.executemany(
                    "INSERT INTO family_playtime(user_id, day, hour, world_id, seconds)"
                    " VALUES(?,?,?,?,?) ON CONFLICT(user_id, day, hour, world_id)"
                    " DO UPDATE SET seconds=seconds+excluded.seconds", rows)
                conn.executemany("UPDATE family_play_log SET ended_at=?, seconds=?"
                                 " WHERE id=?", live)
        except Exception:
            # put the seconds back for the next try
            for uid, day, hour, world_id, whole in rows:
                key = (uid, day, hour, world_id)
                self.pending[key] = self.pending.get(key, 0.0) + whole

    def flush(self) -> None:
        with self.lock:
            self._flush()

    def live_session(self, uid: int) -> Optional[Dict[str, Any]]:
        with self.lock:
            sess = self.sessions.get(int(uid))
            return dict(sess) if sess else None


tracker = Tracker()
atexit.register(tracker.flush)


def on_heartbeat(world_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        return tracker.on_heartbeat(world_id, payload)
    except Exception:
        import traceback
        traceback.print_exc()
        return None


def play_block(info: Dict[str, Any], world_id: str = "", now: Optional[float] = None,
               tracker: Optional[Tracker] = None) -> Tuple[Optional[str], str]:
    """(why this child may not be playing ``world_id`` right now, which rule),
    or (None, "")."""
    tracker = tracker or globals()["tracker"]
    now = time.time() if now is None else now
    c = info["controls"]
    if info.get("paused"):
        return "Your account is paused right now. Ask your grown-up!", "paused"
    if world_id and world_id in c.get("worlds_blocked", []):
        return ("Your grown-up has switched %s off for now. Try another world!"
                % _world_name(world_id)), "world"
    local = _local(info, now)
    if rules.in_quiet_hours(c, local):
        return ("It's quiet time -- games are off until %s. See you then!"
                % rules.quiet_ends_label(c)), "quiet"
    limit = rules.limit_minutes(c, local.date())
    if limit is not None:
        if limit == 0:
            return ("No games on %s -- that's your family's rule."
                    % ("weekends" if rules.is_weekend(local.date()) else "school days")), "limit"
        if tracker.seconds_today(info, now) >= limit * 60:
            return "That's all your play time for today. See you tomorrow!", "limit"
    return None, ""


def today_summary(info: Dict[str, Any]) -> Dict[str, Any]:
    now = time.time()
    c = info["controls"]
    local = _local(info, now)
    limit = rules.limit_minutes(c, local.date())
    used = int(tracker.seconds_today(info, now))
    left = None if limit is None else max(0, limit * 60 - used)
    quiet_now = rules.in_quiet_hours(c, local)
    return {
        "used": used,
        "limit": None if limit is None else limit * 60,
        "left": left,
        "pct": (100 if limit == 0 else min(100, round(100.0 * used / (limit * 60))))
               if limit is not None else None,
        "quiet": bool(c.get("quiet")),
        "quiet_now": quiet_now,
        "quiet_start": rules.clock_label(c.get("quiet_start") or "21:00"),
        "quiet_end": rules.clock_label(c.get("quiet_end") or "07:00"),
        "weekend": rules.is_weekend(local.date()),
        "paused": bool(info.get("paused")),
        "used_label": rules.minutes_label(used // 60) if used >= 60 else
                      ("%d sec" % used if used else "0 min"),
        "left_label": (rules.minutes_label(left // 60) if left and left >= 60
                       else ("under a minute" if left else "none")) if left is not None else "",
        "limit_label": rules.minutes_label(limit),
    }


def seconds_today(info: Dict[str, Any]) -> float:
    return tracker.seconds_today(info)
