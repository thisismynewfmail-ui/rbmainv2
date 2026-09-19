"""The live terminal read-out.

``run.sh`` (and ``main.py``) print a status block every few seconds instead of
a one-off banner, so the window the server runs in actually tells you what the
platform is doing: who is online, what the worlds are carrying, how much
traffic the web server has taken and what has just happened.

The block is deliberately small -- one line per section and one per world --
so it fits a portrait monitor or a phone-shaped SSH window whole, and it is
redrawn in place rather than reprinted, so the numbers update where they stand
instead of scrolling the previous copy away.  It still re-flows for the width
it is given: the meters, the sparklines and the softer columns drop out before
anything that carries a number does.

Everything the admin dashboard shows is here as well -- accounts, presence,
worlds, hosts, the catalogue and the economy, down to the ledger transaction
count and the number of market purchases -- but rendered for a terminal
rather than for a browser: sparkline histories for the numbers that move,
change arrows on the counters that only ever climb, and meters for anything
with a ceiling.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

BANNER = r"""
  ____  _     ___   ____ _  ___   _    ___     _______ _   _
 | __ )| |   / _ \ / ___| |/ / | | |  / \ \   / / ____| \ | |
 |  _ \| |  | | | | |   | ' /| |_| | / _ \ \ / /|  _| |  \| |
 | |_) | |__| |_| | |___| . \|  _  |/ ___ \ V / | |___| |\  |
 |____/|_____\___/ \____|_|\_\_| |_/_/   \_\_/  |_____|_| \_|
"""

# Colour is opt-in: only when the stream is a terminal and NO_COLOR is unset.
_COLOR = (sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
          and os.environ.get("TERM", "") not in ("", "dumb"))


def _unicode_ok() -> bool:
    """Whether the block and braille glyphs will survive the output stream."""
    encoding = (getattr(sys.stdout, "encoding", "") or "").lower()
    if "utf" not in encoding:
        return False
    try:
        "\u2581\u2807".encode(sys.stdout.encoding)
    except Exception:
        return False
    return True


_GLYPHS = _unicode_ok()

# Eight levels for the sparklines, a braille wheel for the heartbeat, and
# solid/shade blocks for the meters -- each with an ASCII understudy so a
# dumb terminal still gets a read-out rather than a screen of question marks.
SPARK = "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588" if _GLYPHS else "_.-~=+*#"
SPIN = ("\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"
        if _GLYPHS else "|/-\\")
METER_ON = "\u2588" if _GLYPHS else "#"
METER_OFF = "\u2591" if _GLYPHS else "."
UP_ARROW = "\u25b2" if _GLYPHS else "+"
DOWN_ARROW = "\u25bc" if _GLYPHS else "-"
RULE_CHAR = "\u2500" if _GLYPHS else "-"


def _c(code: str, text: str) -> str:
    return "\033[%sm%s\033[0m" % (code, text) if _COLOR else text


def bold(t: str) -> str: return _c("1", t)
def dim(t: str) -> str: return _c("2", t)
def cyan(t: str) -> str: return _c("36", t)
def green(t: str) -> str: return _c("32", t)
def yellow(t: str) -> str: return _c("33", t)
def red(t: str) -> str: return _c("31", t)


def term_size() -> Tuple[int, int]:
    try:
        size = shutil.get_terminal_size(fallback=(80, 24))
        return max(38, size.columns), max(10, size.lines)
    except Exception:
        return 80, 24


def human_bytes(value: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return "%.0f %s" % (value, unit) if unit == "B" else "%.1f %s" % (value, unit)
        value /= 1024.0
    return "%.1f GB" % value


def human_time(seconds: float) -> str:
    seconds = int(max(0, seconds))
    if seconds < 60:
        return "%ds" % seconds
    if seconds < 3600:
        return "%dm %02ds" % (seconds // 60, seconds % 60)
    if seconds < 86400:
        return "%dh %02dm" % (seconds // 3600, (seconds % 3600) // 60)
    return "%dd %02dh" % (seconds // 86400, (seconds % 86400) // 3600)


def rule(width: int, char: str = "") -> str:
    return dim((char or RULE_CHAR) * width)


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def visible_len(text: str) -> int:
    """Length as the terminal sees it -- colour codes take up no columns."""
    return len(_ANSI_RE.sub("", text))


def clip(text: str, width: int) -> str:
    """Trim to ``width`` visible columns without cutting an escape in half."""
    if visible_len(text) <= width:
        return text
    out, shown, index = [], 0, 0
    while index < len(text) and shown < width:
        match = _ANSI_RE.match(text, index)
        if match:
            out.append(match.group(0))
            index = match.end()
            continue
        out.append(text[index])
        shown += 1
        index += 1
    out.append("\033[0m" if _COLOR else "")
    return "".join(out)


def bar(value: float, total: float, width: int) -> str:
    """A small meter -- clamped so it never wraps the line."""
    width = max(4, width)
    if total <= 0:
        filled = 0
    else:
        filled = int(round(min(1.0, value / total) * width))
    return METER_ON * filled + METER_OFF * (width - filled)


def spark(values: List[float], width: int) -> str:
    """A sparkline of the last ``width`` samples, oldest on the left.

    The scale is the run's own maximum rather than a fixed ceiling, so a
    quiet server still shows the shape of its traffic instead of a flat line
    along the bottom.  A run that never moved stays flat on purpose.
    """
    width = max(4, width)
    series = list(values)[-width:]
    # Pad the left so the chart is always the same size and new samples push
    # in from the right, rather than the whole line growing for two minutes.
    floor = SPARK[0] * max(0, width - len(series))
    if not series:
        return floor
    top = max(series)
    if top <= 0:
        return floor + SPARK[0] * len(series)
    steps = len(SPARK) - 1
    return floor + "".join(
        SPARK[int(round(min(1.0, v / top) * steps))] for v in series)


def arrow(delta: float, colour: bool = True) -> str:
    """The change since the last block, or nothing at all when it held still."""
    if not delta:
        return ""
    if delta > 0:
        text = "%s%s" % (UP_ARROW, _num(delta))
        return green(text) if colour else text
    text = "%s%s" % (DOWN_ARROW, _num(-delta))
    return red(text) if colour else text


def _num(value: float) -> str:
    return "{:,}".format(int(value))


# The running dashboard, so any module can drop a line into the read-out
# without threading a reference through the whole application.
_active: Optional["Dashboard"] = None


def attach(dashboard: "Dashboard") -> None:
    global _active
    _active = dashboard


def note(text: str) -> None:
    """Record an event for the next status block (a no-op with no console)."""
    board = _active
    if board is not None:
        board.note(text)


class Dashboard:
    """Collects the numbers and renders the periodic status block."""

    def __init__(self, application: Any, port: int, address: str,
                 supervisor: Any = None, interval: float = 10.0,
                 scheme: str = "http", domain: str = ""):
        self.app = application
        self.port = port
        self.address = address
        # How to reach this server, as a visitor would type it: the scheme it
        # is actually serving and, when it has a name, the name rather than
        # the address behind it.
        self.scheme = scheme
        self.domain = domain
        self.supervisor = supervisor
        self.interval = max(2.0, float(interval))
        self.started = time.time()
        self.last_requests = int(getattr(application, "request_count", 0) or 0)
        self.last_sample = time.time()
        self.last_rate = 0.0
        self.frame = 0             # ticks the heartbeat and the sparklines
        # Rolling histories, one sample per block, so the read-out shows the
        # shape of the last few minutes rather than only this instant.
        self.history: Dict[str, List[float]] = {
            "rate": [], "online": [], "in_game": [], "sockets": [],
        }
        self.previous: Dict[str, Any] = {}
        self.events: List[str] = []
        self._painted = 0          # lines the last in-place repaint left behind
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def url(self, path: str = "/", host: str = "") -> str:
        """A URL a visitor could paste, with the port left off when it is the
        default for the scheme -- nobody types :443."""
        name = host or self.domain or self.address
        default = 443 if self.scheme == "https" else 80
        port = "" if self.port == default else ":%d" % self.port
        return "%s://%s%s%s" % (self.scheme, name, port, path)

    # ------------------------------------------------------------- lifecycle
    def start(self) -> None:
        attach(self)
        self._thread = threading.Thread(target=self._loop, name="console",
                                        daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        # first block a beat after boot so the game hosts have reported in
        if self._stop.wait(3.0):
            return
        while not self._stop.is_set():
            try:
                self.render()
            except Exception as exc:            # never let the read-out kill the server
                print("[console] %s" % exc, flush=True)
            if self._stop.wait(self.interval):
                return

    # ---------------------------------------------------------------- events
    def note(self, text: str) -> None:
        """Record a one-line event for the next status block."""
        stamp = time.strftime("%H:%M:%S")
        with self._lock:
            self.events.append("%s %s" % (stamp, text))
            del self.events[:-40]

    def _drain_events(self, limit: int) -> List[str]:
        with self._lock:
            rows = self.events[-limit:]
            return list(rows)

    # ----------------------------------------------------------------- data
    def snapshot(self) -> Dict[str, Any]:
        from . import config
        from .game import registry as game_registry
        from .models import worlds as world_registry
        from .social import feed

        now = time.time()
        requests = int(getattr(self.app, "request_count", 0) or 0)
        sockets = getattr(self.app, "ws_count", 0)
        elapsed = now - self.last_sample
        if elapsed < 0.25:
            # two reads in the same instant (a test calling block() twice, a
            # manual repaint) would otherwise divide by almost nothing and
            # report a rate in the thousands
            rate = self.last_rate
        else:
            rate = (requests - self.last_requests) / elapsed
            self.last_requests = requests
            self.last_sample = now
            self.last_rate = rate

        try:
            stats = feed.stats_snapshot()
        except Exception:
            stats = {"users": 0, "visits": 0, "items_owned": 0, "unusuals": 0,
                     "posts": 0, "messages": 0, "friendships": 0,
                     "new_users_today": 0}
        # The economy and the catalogue: the same figures the admin dashboard
        # carries, plus the two the ledger and the shop can answer directly.
        money = {"circulating": 0, "granted": 0, "spent": 0, "transactions": 0}
        market = pending = follows = catalogue = 0
        try:
            from . import db
            from .models import economy, inventory
            money = economy.totals()
            catalogue = inventory.global_stats().get("catalogue", 0)
            market = db.scalar("SELECT COUNT(*) FROM inventory"
                               " WHERE source='market'")
            pending = db.scalar("SELECT COUNT(*) FROM friendships"
                                " WHERE status='pending'")
            follows = db.scalar("SELECT COUNT(*) FROM follows")
        except Exception:
            pass
        try:
            from .models import users
            online = len(users.online_users(500))
        except Exception:
            online = 0

        world_rows = []
        try:
            for world in world_registry.all_worlds():
                status = game_registry.world_status(world["id"])
                try:
                    visits = world_registry.stats(world["id"]).get("visits", 0)
                except Exception:
                    visits = 0
                world_rows.append({
                    "id": world["id"],
                    "name": world["name"],
                    "players": status["players"],
                    "instances": status["instances"],
                    "capacity": world["max_players"],
                    "online": status["online"],
                    "tick_ms": status.get("tick_ms", 0),
                    "visits": visits,
                })
        except Exception:
            pass

        hosts = []
        if self.supervisor is not None:
            try:
                hosts = self.supervisor.status()
            except Exception:
                hosts = []

        db_bytes = 0
        try:
            for suffix in ("", "-wal", "-shm"):
                path = str(config.DB_PATH) + suffix
                if os.path.exists(path):
                    db_bytes += os.path.getsize(path)
        except Exception:
            pass

        data = {
            "uptime": now - self.started,
            "requests": requests,
            "rate": rate,
            "sockets": sockets,
            "threads": threading.active_count(),
            "accounts": stats.get("users", 0),
            "new_today": stats.get("new_users_today", 0),
            "online": online,
            "visits": stats.get("visits", 0),
            "items": stats.get("items_owned", 0),
            "unusuals": stats.get("unusuals", 0),
            "messages": stats.get("messages", 0),
            "posts": stats.get("posts", 0),
            "friendships": stats.get("friendships", 0),
            "pending": pending,
            "follows": follows,
            "catalogue": catalogue,
            "circulating": money.get("circulating", 0),
            "granted": money.get("granted", 0),
            "spent": money.get("spent", 0),
            "transactions": money.get("transactions", 0),
            "market_buys": market,
            "worlds": world_rows,
            "hosts": hosts,
            "db_bytes": db_bytes,
            "in_game": sum(w["players"] for w in world_rows),
        }
        # Feed the sparklines.  Twenty-four samples is two minutes at the
        # four second refresh -- long enough to show a shape, short enough to
        # still be about now.
        for key in self.history:
            series = self.history[key]
            series.append(float(data.get(key, 0)))
            del series[:-24]
        return data

    # -------------------------------------------------------------- rendering
    def render(self) -> None:
        """Repaint the status block.

        On a terminal the block is redrawn *in place*: the cursor walks back
        up over the previous copy and each line is rewritten with an
        erase-to-end-of-line, so the read-out behaves like a dashboard rather
        than a log that reprints itself every few seconds.  Only the block
        itself is touched -- the start-up banner and anything printed before
        it stay where they are, and a shorter block blanks the rows the taller
        one left behind.  Redirected to a file or a pipe there is no cursor to
        move, so it falls back to appending.
        """
        lines = self.lines()
        if not _COLOR:
            sys.stdout.write("\n".join([""] + lines) + "\n")
            sys.stdout.flush()
            return
        out = []
        if self._painted:
            out.append("\033[%dA" % self._painted)
        out.extend("%s\033[K\n" % line for line in lines)
        leftover = max(0, self._painted - len(lines))
        if leftover:
            out.append("\033[K\n" * leftover)
            out.append("\033[%dA" % leftover)
        self._painted = len(lines)
        sys.stdout.write("".join(out))
        sys.stdout.flush()

    def block(self) -> str:
        """The status block as plain text (used by tests and log mode)."""
        return "\n".join(self.lines()) + "\n"

    # The read-out has to survive a portrait monitor and a phone-shaped SSH
    # window, so it is built to a line budget rather than to whatever the
    # numbers happen to need: one line per section, worlds on one line each,
    # and the event log soaking up only the room that is genuinely spare.
    HEADROOM = 4

    def lines(self) -> List[str]:
        width, height = term_size()
        data = self.snapshot()
        self.frame += 1
        rows: List[str] = []
        clock = time.strftime("%H:%M:%S")
        rows.append(self._title(width, clock, data))
        rows.append(rule(width))
        rows.extend(self._stat_lines(data, width))
        rows.extend(self._world_lines(data, width))
        rows.extend(self._host_line(data, width))

        # Events take whatever is left over, newest last, and vanish entirely
        # in a short window rather than pushing the numbers off the screen.
        spare = height - len(rows) - self.HEADROOM
        if spare >= 2:
            events = self._drain_events(min(spare - 1, 4))
            if events:
                label = "recent"
                for index, row in enumerate(events):
                    rows.append(self._pair(label if index == 0 else "",
                                           dim(row), width))
        rows.append(rule(width))
        footer = self.url()
        if width >= 58:
            footer += "  (+/admin-dashboard)"
        footer += "   Ctrl+C to stop"
        rows.append(clip(dim(footer), width))
        self.previous = data
        return rows

    @staticmethod
    def _join(*parts: str) -> str:
        """Join the parts that have something to say, two spaces apart."""
        return "  ".join(part for part in parts if part)

    def _delta(self, data: Dict[str, Any], key: str) -> str:
        """The change in a counter since the last block, as an arrow."""
        if not self.previous:
            return ""
        return arrow(data.get(key, 0) - self.previous.get(key, 0))

    def _trend(self, key: str, width: int) -> str:
        return dim(spark(self.history.get(key, []), width))

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _pair(label: str, value: str, width: int) -> str:
        """One ``label  value`` line, clipped to the window's real width."""
        return clip("%-7s %s" % (label[:7], value), width)

    def _title(self, width: int, clock: str, data: Dict[str, Any]) -> str:
        # The wheel turns once per block, so a glance at the top line says
        # whether the read-out is live or the server has stopped answering.
        wheel = SPIN[self.frame % len(SPIN)]
        left = "BLOCKHAVEN %s %s" % (clock, wheel)
        right = "up %s" % human_time(data["uptime"])
        gap = max(1, width - visible_len(left) - visible_len(right))
        return clip(bold(cyan(left)) + " " * gap + dim(right), width)

    def _stat_lines(self, data: Dict[str, Any], width: int) -> List[str]:
        """Everything the admin dashboard carries, one subject per line.

        Counters that only ever climb get a change arrow, so a still frame
        still says what just happened; the ones that go up and down get a
        sparkline of the last two minutes instead.
        """
        narrow = width < 60
        wide = width >= 78
        trend = 12 if wide else (8 if width >= 64 else 0)
        rows: List[str] = []

        web = self._join(
            "%s req" % _num(data["requests"]), "%.1f/s" % data["rate"],
            self._trend("rate", trend) if trend else "",
            "%s ws" % data["sockets"], "%s thr" % data["threads"],
            "" if narrow else "%s db" % human_bytes(data["db_bytes"]))
        rows.append(self._pair("web", web, width))

        people = "%s accounts" % _num(data["accounts"])
        if data["new_today"]:
            people += dim(" (+%s%s)" % (_num(data["new_today"]),
                                        "" if narrow else " today"))
        people = self._join(
            people,
            "%s on site" % green(str(data["online"])),
            "%s in game" % cyan(str(data["in_game"])),
            self._trend("in_game", trend) if trend else "")
        rows.append(self._pair("people", people, width))

        site = self._join(
            "%s visits" % _num(data["visits"]), self._delta(data, "visits"),
            "%s items" % _num(data["items"]),
            "%s unusual" % yellow(_num(data["unusuals"])),
            "" if narrow else "%s in shop" % _num(data["catalogue"]))
        rows.append(self._pair("site", site, width))

        # The same five numbers either way -- a tight window just gets tighter
        # words for them, rather than losing the last two off the end.
        social = self._join(
            "%s friend%s" % (_num(data["friendships"]),
                             "s" if narrow else "ships"),
            "%s pend%s" % (_num(data["pending"]), "" if narrow else "ing"),
            "%s follow%s" % (_num(data["follows"]), "" if narrow else "s"),
            "%s posts" % _num(data["posts"]),
            "%s msgs" % _num(data["messages"]))
        rows.append(self._pair("social", social, width))

        # The economy gets a meter as well as its numbers: how much of every
        # credit ever handed out is still in players' pockets.
        meter_w = 10 if wide else (6 if width >= 60 else 0)
        money = self._join(
            "%s %s" % (yellow(_num(data["circulating"])),
                       "out" if narrow else "credits out"),
            bar(data["circulating"], data["granted"], meter_w)
            if meter_w and data["granted"] else "",
            "%s granted" % _num(data["granted"]),
            "%s spent" % _num(data["spent"]))
        rows.append(self._pair("money", money, width))

        trade = self._join(
            "%s ledger %s" % (_num(data["transactions"]),
                              "rows" if narrow else "entries"),
            self._delta(data, "transactions"),
            "%s %s" % (_num(data["market_buys"]),
                       "bought" if narrow else "market buys"),
            self._delta(data, "market_buys"))
        rows.append(self._pair("trade", trade, width))
        if narrow:
            rows.append(self._pair("db", human_bytes(data["db_bytes"]), width))
        return rows

    def _world_lines(self, data: Dict[str, Any], width: int) -> List[str]:
        rows = data["worlds"]
        if not rows:
            return []
        # The meter is the first thing to go when the window is tight; the
        # numbers themselves never are.
        name_w = 16 if width >= 62 else 11
        meter_w = 10 if width >= 72 else (6 if width >= 56 else 0)
        out: List[str] = []
        for index, row in enumerate(rows):
            meter = (bar(row["players"], max(1, row["capacity"]), meter_w) + " "
                     if meter_w else "")
            state = green("up") if row["online"] else red("DOWN")
            body = "%-*s %s%s/%-3s %si %sms %s" % (
                name_w, row["name"][:name_w], meter,
                row["players"], row["capacity"], row["instances"],
                int(row["tick_ms"]), state)
            if width >= 78:
                body += dim("  %s visits" % _num(row.get("visits", 0)))
            out.append(self._pair("worlds" if index == 0 else "", body, width))
        return out

    def _host_line(self, data: Dict[str, Any], width: int) -> List[str]:
        hosts = data["hosts"]
        if not hosts:
            return []
        alive = sum(1 for h in hosts if h.get("alive"))
        restarts = sum(int(h.get("restarts", 0)) for h in hosts)
        oldest = max((float(h.get("uptime", 0) or 0) for h in hosts),
                     default=0.0)
        text = "%d/%d alive" % (alive, len(hosts))
        text = green(text) if alive == len(hosts) else red(text)
        if restarts:
            text += yellow("  %d restart%s"
                           % (restarts, "" if restarts == 1 else "s"))
        if oldest:
            text += "  up %s" % human_time(oldest)
        if width >= 64:
            pids = " ".join(str(h.get("pid", "-")) for h in hosts)
            text += dim("  pids " + pids)
        return [self._pair("hosts", text, width)]

    # ------------------------------------------------------------- start-up
    def intro(self, world_rows: List[Dict[str, Any]], admin: Tuple[str, str],
              games: bool) -> str:
        from . import config
        width, _ = term_size()
        lines = [BANNER if width >= 64 else bold("  BLOCKHAVEN")]
        lines.append("  %s  --  %s" % (bold(config.SITE_NAME), config.SITE_TAGLINE))
        lines.append(rule(width))
        lines.append("  Website     " + cyan(self.url()))
        lines.append("  Local       " + cyan(self.url("/", "127.0.0.1")))
        lines.append("  Admin       %s  (%s / %s)"
                     % (self.url("/admin-dashboard"), admin[0], admin[1]))
        if games:
            for world in world_rows:
                lines.append("  World       %-38s %s"
                             % (self.url("/" + world["id"]), world["name"]))
        else:
            lines.append("  " + yellow("Game hosts disabled (--no-games)"))
        lines.append(rule(width))
        lines.append("  Status refreshes every %ds. Ctrl+C to stop."
                     % int(self.interval))
        lines.append("")
        return "\n".join(lines)
