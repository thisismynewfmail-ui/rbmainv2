"""The live terminal read-out.

``run.sh`` (and ``main.py``) print a status block every few seconds instead of
a one-off banner, so the window the server runs in actually tells you what the
platform is doing: who is online, what the worlds are carrying, how much
traffic the web server has taken and what has just happened.

The block is deliberately small -- about a dozen lines, one per section and
one per world -- so it fits a portrait monitor or a phone-shaped SSH window
whole, and it is redrawn in place rather than reprinted, so the numbers update
where they stand instead of scrolling the previous copy away.  It still
re-flows for the width it is given: the meters and the softer columns drop out
before anything that carries a number does.
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


def rule(width: int, char: str = "-") -> str:
    return dim(char * width)


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
    """A small ASCII meter -- clamped so it never wraps the line."""
    width = max(4, width)
    if total <= 0:
        filled = 0
    else:
        filled = int(round(min(1.0, value / total) * width))
    return "[" + "#" * filled + "." * (width - filled) + "]"


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
                 supervisor: Any = None, interval: float = 10.0):
        self.app = application
        self.port = port
        self.address = address
        self.supervisor = supervisor
        self.interval = max(2.0, float(interval))
        self.started = time.time()
        self.last_requests = 0
        self.last_sample = time.time()
        self.events: List[str] = []
        self._painted = 0          # lines the last in-place repaint left behind
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

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
        requests = getattr(self.app, "request_count", 0)
        sockets = getattr(self.app, "ws_count", 0)
        elapsed = max(0.001, now - self.last_sample)
        rate = (requests - self.last_requests) / elapsed
        self.last_requests = requests
        self.last_sample = now

        try:
            stats = feed.stats_snapshot()
        except Exception:
            stats = {"users": 0, "visits": 0, "items_owned": 0, "unusuals": 0,
                     "posts": 0, "messages": 0, "friendships": 0}
        try:
            from .models import users
            online = len(users.online_users(500))
        except Exception:
            online = 0

        world_rows = []
        try:
            for world in world_registry.all_worlds():
                status = game_registry.world_status(world["id"])
                world_rows.append({
                    "id": world["id"],
                    "name": world["name"],
                    "players": status["players"],
                    "instances": status["instances"],
                    "capacity": world["max_players"],
                    "online": status["online"],
                    "tick_ms": status.get("tick_ms", 0),
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

        return {
            "uptime": now - self.started,
            "requests": requests,
            "rate": rate,
            "sockets": sockets,
            "threads": threading.active_count(),
            "accounts": stats.get("users", 0),
            "online": online,
            "visits": stats.get("visits", 0),
            "items": stats.get("items_owned", 0),
            "unusuals": stats.get("unusuals", 0),
            "messages": stats.get("messages", 0),
            "worlds": world_rows,
            "hosts": hosts,
            "db_bytes": db_bytes,
            "in_game": sum(w["players"] for w in world_rows),
        }

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
        rows: List[str] = []
        clock = time.strftime("%H:%M:%S")
        rows.append(self._title(width, clock, data))
        rows.extend(self._stat_lines(data, width))
        rows.extend(self._world_lines(data, width))
        rows.extend(self._host_line(data, width))

        # Events take whatever is left over, newest last, and vanish entirely
        # in a short window rather than pushing the numbers off the screen.
        spare = height - len(rows) - self.HEADROOM
        if spare >= 2:
            events = self._drain_events(min(spare - 1, 5))
            if events:
                label = "recent"
                for index, row in enumerate(events):
                    rows.append(self._pair(label if index == 0 else "",
                                           dim(row), width))
        footer = "http://%s:%d/" % (self.address, self.port)
        if width >= 58:
            footer += "  (+/admin-dashboard)"
        footer += "   Ctrl+C to stop"
        rows.append(clip(dim(footer), width))
        return rows

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _pair(label: str, value: str, width: int) -> str:
        """One ``label  value`` line, clipped to the window's real width."""
        return clip("%-7s %s" % (label[:7], value), width)

    def _title(self, width: int, clock: str, data: Dict[str, Any]) -> str:
        left = "BLOCKHAVEN %s" % clock
        right = "up %s" % human_time(data["uptime"])
        gap = max(1, width - visible_len(left) - visible_len(right))
        return clip(bold(cyan(left)) + " " * gap + dim(right), width)

    def _stat_lines(self, data: Dict[str, Any], width: int) -> List[str]:
        """Three dense lines: the server, the people, the economy."""
        narrow = width < 56
        web = "%s req (%.1f/s)  %s ws  %s thr" % (
            f"{data['requests']:,}", data["rate"], data["sockets"],
            data["threads"])
        if not narrow:
            web += "  %s db" % human_bytes(data["db_bytes"])
        people = "%s accounts  %s on site  %s in game" % (
            f"{data['accounts']:,}", green(str(data["online"])),
            cyan(str(data["in_game"])))
        stuff = "%s visits  %s items  %s unusual  %s msgs" % (
            f"{data['visits']:,}", f"{data['items']:,}",
            yellow(f"{data['unusuals']:,}"), f"{data['messages']:,}")
        rows = [self._pair("web", web, width),
                self._pair("people", people, width),
                self._pair("site", stuff, width)]
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
            out.append(self._pair("worlds" if index == 0 else "", body, width))
        return out

    def _host_line(self, data: Dict[str, Any], width: int) -> List[str]:
        hosts = data["hosts"]
        if not hosts:
            return []
        alive = sum(1 for h in hosts if h.get("alive"))
        restarts = sum(int(h.get("restarts", 0)) for h in hosts)
        text = "%d/%d alive" % (alive, len(hosts))
        text = green(text) if alive == len(hosts) else red(text)
        if restarts:
            text += yellow("  %d restart%s"
                           % (restarts, "" if restarts == 1 else "s"))
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
        lines.append("  Website     " + cyan("http://%s:%d/" % (self.address, self.port)))
        lines.append("  Local       " + cyan("http://127.0.0.1:%d/" % self.port))
        lines.append("  Admin       http://%s:%d/admin-dashboard  (%s / %s)"
                     % (self.address, self.port, admin[0], admin[1]))
        if games:
            for world in world_rows:
                lines.append("  World       http://%s:%-5d /%-16s %s"
                             % (self.address, self.port, world["id"], world["name"]))
        else:
            lines.append("  " + yellow("Game hosts disabled (--no-games)"))
        lines.append(rule(width))
        lines.append("  Status refreshes every %ds. Ctrl+C to stop."
                     % int(self.interval))
        lines.append("")
        return "\n".join(lines)
