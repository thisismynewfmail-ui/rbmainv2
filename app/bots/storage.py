"""Each bot's own folder: its account data and every conversation it has had.

    data/bots/accounts/<shard>/<id>-<username>/
        account.json                               persona, traits, profile
        logs/<USERNAME> Comment Section.jsonl      a profile's comment section
        logs/Chat Conversation With <USERNAME>.jsonl   private messages
        logs/In-Game Chat In World <World>.jsonl   what it saw and said in game
        logs/Status Posts.jsonl                    its own posts

A log is JSON lines -- ``{"at", "who", "text", ...}`` -- appended as things
happen, which is also exactly what the prompt builder reads back: the log a
bot is given for a reply is the log of *that* conversation, from *its* point
of view, and nothing else.

The folders are sharded 256 ways by account id so a population of a couple of
hundred thousand never puts more than a thousand-odd entries in one directory.
Logs are trimmed to their newest part once they pass a size cap, so a
chatty bot cannot fill the disk.
"""
from __future__ import annotations

import json
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

from .. import config as site_config

ROOT = site_config.DATA_DIR / "bots"
ACCOUNTS = ROOT / "accounts"
MAX_LOG_BYTES = 768 * 1024
KEEP_LOG_BYTES = 256 * 1024

_lock = threading.RLock()


def folder(bot_id: int, username: str) -> Path:
    return ACCOUNTS / ("%02x" % (int(bot_id) % 256)) / (
        "%d-%s" % (int(bot_id), _safe(username)))


def _safe(text: str) -> str:
    return "".join(c for c in str(text) if c.isalnum() or c in "_- ")[:60] \
        or "unknown"


# --------------------------------------------------------------- log names
def comment_log(owner: str) -> str:
    return "%s Comment Section" % _safe(owner)


def dm_log(other: str) -> str:
    return "Chat Conversation With %s" % _safe(other)


def chat_log(world_name: str) -> str:
    return "In-Game Chat In World %s" % _safe(world_name)


POSTS_LOG = "Status Posts"


# ------------------------------------------------------------------ account
def write_account(bot_id: int, username: str, data: Dict[str, Any]) -> None:
    path = folder(bot_id, username)
    try:
        (path / "logs").mkdir(parents=True, exist_ok=True)
        temp = path / "account.json.tmp"
        temp.write_text(json.dumps(data, indent=2, sort_keys=True,
                                   default=str))
        os.replace(str(temp), str(path / "account.json"))
    except OSError:
        pass


def read_account(bot_id: int, username: str) -> Dict[str, Any]:
    try:
        return json.loads((folder(bot_id, username) / "account.json")
                          .read_text())
    except (OSError, ValueError):
        return {}


def remove(bot_id: int, username: str) -> None:
    shutil.rmtree(str(folder(bot_id, username)), ignore_errors=True)


# --------------------------------------------------------------------- logs
def _log_path(bot_id: int, username: str, name: str) -> Path:
    return folder(bot_id, username) / "logs" / (_safe(name) + ".jsonl")


def append(bot_id: int, username: str, name: str,
           entries: List[Dict[str, Any]]) -> None:
    """Add lines to one of a bot's logs (creating the folder if needed)."""
    if not entries:
        return
    path = _log_path(bot_id, username, name)
    blob = "".join(json.dumps(e, separators=(",", ":"), ensure_ascii=False)
                   + "\n" for e in entries)
    with _lock:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(blob)
            if path.stat().st_size > MAX_LOG_BYTES:
                _trim(path)
        except OSError:
            pass


def _trim(path: Path) -> None:
    with open(path, "rb") as handle:
        handle.seek(-KEEP_LOG_BYTES, os.SEEK_END)
        tail = handle.read()
    cut = tail.find(b"\n")
    tail = tail[cut + 1:] if cut >= 0 else tail
    temp = path.with_suffix(".tmp")
    temp.write_bytes(tail)
    os.replace(str(temp), str(path))


def tail(bot_id: int, username: str, name: str,
         limit: int = 50) -> List[Dict[str, Any]]:
    """The newest ``limit`` entries of one log, oldest first."""
    path = _log_path(bot_id, username, name)
    try:
        size = path.stat().st_size
    except OSError:
        return []
    chunk = min(size, max(8192, limit * 600))
    try:
        with open(path, "rb") as handle:
            handle.seek(size - chunk)
            data = handle.read()
    except OSError:
        return []
    lines = data.split(b"\n")
    if chunk < size:
        lines = lines[1:]            # the first line may be cut in half
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line.decode("utf-8")))
        except ValueError:
            continue
    return out[-limit:]


def list_logs(bot_id: int, username: str) -> List[Dict[str, Any]]:
    base = folder(bot_id, username) / "logs"
    out = []
    try:
        for entry in os.scandir(str(base)):
            if not entry.name.endswith(".jsonl"):
                continue
            stat = entry.stat()
            out.append({"name": entry.name[:-6], "bytes": stat.st_size,
                        "modified": int(stat.st_mtime)})
    except OSError:
        return []
    out.sort(key=lambda row: -row["modified"])
    return out


def usage() -> Dict[str, int]:
    """Rough size of the bot folders (sampled, so it stays cheap)."""
    total = files = 0
    try:
        for shard in os.scandir(str(ACCOUNTS)):
            if not shard.is_dir():
                continue
            for bot in os.scandir(shard.path):
                files += 1
    except OSError:
        pass
    return {"folders": files, "bytes": total}


def ensure_root() -> None:
    try:
        ACCOUNTS.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def now() -> int:
    return int(time.time())
