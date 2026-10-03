"""RFC 6455 websocket server implementation (stdlib only) + wire helpers."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import struct
import threading
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Tuple

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_CONT = 0x0
OP_TEXT = 0x1
OP_BIN = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA

MAX_FRAME = 1 << 20  # 1 MiB is far larger than any legitimate game message

# A connection that has fallen this far behind -- this much queued for it, or
# anything queued this long -- is not going to catch up, and is let go rather
# than kept waiting on.  Snapshots never pile up (a newer one replaces one
# still waiting), so only a client that has stopped reading reaches these.
MAX_BACKLOG_BYTES = 4 << 20
MAX_BACKLOG_SECONDS = 15.0

# How long a closing connection gets to deliver what is still queued for it
# (a "kicked" note, say) and the close frame before the socket is let go.
CLOSE_GRACE_SECONDS = 2.0


class WebSocketError(Exception):
    pass


def accept_key(client_key: str) -> str:
    digest = hashlib.sha1((client_key + GUID).encode()).digest()
    return base64.b64encode(digest).decode()


def handshake_response(headers: Dict[str, str]) -> bytes:
    key = headers.get("sec-websocket-key", "")
    if not key:
        raise WebSocketError("missing Sec-WebSocket-Key")
    return ("HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Accept: %s\r\n\r\n" % accept_key(key)).encode()


class WebSocket:
    """A server-side websocket bound to an accepted socket.

    Reading is blocking, on the caller's own thread (one per connection).
    Writing never is: ``send_*`` queue the frame and return at once, and a
    writer thread per connection does the actual ``sendall``.

    That matters because the game tick sends to every player in turn while
    holding the round's lock, and the host ticks every round of a world on one
    thread.  With blocking writes, one client that stopped reading -- a laptop
    lid closed, a Wi-Fi drop, a browser frozen on something -- filled its
    socket buffer and then stopped the tick inside ``sendall``: every player
    in every round of that world lagged until it came back or the connection
    finally died.  Now that client's queue fills instead, and it alone is let
    go when it falls past MAX_BACKLOG_*.

    Snapshots (``replace`` frames) are the bulk of the traffic and each one
    supersedes the last, so a snapshot still waiting to go out is replaced
    rather than followed: a client that hiccups gets the latest state when it
    is back, not a backlog of stale ones to chew through.
    """

    def __init__(self, sock: socket.socket, rfile=None):
        self.sock = sock
        self.rfile = rfile or sock.makefile("rb", 65536)
        self.closed = False
        # when the peer last sent anything at all, pongs included (a browser
        # answers our pings itself, even from a throttled background tab)
        self.last_frame = time.monotonic()
        self._queue: Deque[List[Any]] = deque()     # [bytes, queued_at, replaceable]
        self._queued_bytes = 0
        self._pending_replace: Optional[List[Any]] = None
        self._close_entry: Optional[List[Any]] = None
        self._dropped = False
        self._cond = threading.Condition()
        self._writer = threading.Thread(target=self._write_loop, daemon=True,
                                        name="ws-writer")
        self._writer.start()

    # ----------------------------------------------------------------- read
    def _read_exact(self, count: int) -> bytes:
        chunks = []
        remaining = count
        while remaining > 0:
            chunk = self.rfile.read(remaining)
            if not chunk:
                raise WebSocketError("connection closed")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def recv(self) -> Optional[str]:
        """Return the next text message, or None when the peer closed."""
        buffer = bytearray()
        opcode = None
        while True:
            try:
                header = self._read_exact(2)
            except (WebSocketError, OSError):
                return None
            self.last_frame = time.monotonic()
            first, second = header[0], header[1]
            fin = bool(first & 0x80)
            frame_op = first & 0x0F
            masked = bool(second & 0x80)
            length = second & 0x7F
            try:
                if length == 126:
                    length = struct.unpack("!H", self._read_exact(2))[0]
                elif length == 127:
                    length = struct.unpack("!Q", self._read_exact(8))[0]
                if length > MAX_FRAME:
                    self.close(1009)
                    return None
                mask = self._read_exact(4) if masked else b""
                payload = self._read_exact(length) if length else b""
            except (WebSocketError, OSError):
                return None
            if masked and payload:
                payload = bytes(b ^ mask[i & 3] for i, b in enumerate(payload))

            if frame_op == OP_CLOSE:
                self.close(1000)
                return None
            if frame_op == OP_PING:
                self._send_frame(OP_PONG, payload)
                continue
            if frame_op == OP_PONG:
                continue
            if frame_op in (OP_TEXT, OP_BIN):
                opcode = frame_op
                buffer = bytearray(payload)
            elif frame_op == OP_CONT:
                buffer.extend(payload)
            else:
                self.close(1002)
                return None
            if fin:
                if opcode == OP_TEXT:
                    try:
                        return buffer.decode("utf-8")
                    except UnicodeDecodeError:
                        self.close(1007)
                        return None
                return ""
            if len(buffer) > MAX_FRAME:
                self.close(1009)
                return None

    # ---------------------------------------------------------------- write
    @staticmethod
    def _frame(opcode: int, payload: bytes) -> bytes:
        length = len(payload)
        if length < 126:
            header = struct.pack("!BB", 0x80 | opcode, length)
        elif length < (1 << 16):
            header = struct.pack("!BBH", 0x80 | opcode, 126, length)
        else:
            header = struct.pack("!BBQ", 0x80 | opcode, 127, length)
        return header + payload

    def _send_frame(self, opcode: int, payload: bytes, replace: bool = False) -> None:
        if self.closed:
            return
        data = self._frame(opcode, payload)
        overflow = False
        with self._cond:
            if self.closed:
                return
            pending = self._pending_replace
            if replace and pending is not None:
                # the snapshot still waiting is stale: send this one in its place
                self._queued_bytes += len(data) - len(pending[0])
                pending[0] = data
            else:
                entry = [data, time.monotonic(), replace]
                self._queue.append(entry)
                self._queued_bytes += len(data)
                if replace:
                    self._pending_replace = entry
            oldest = self._queue[0][1] if self._queue else 0.0
            if self._queued_bytes > MAX_BACKLOG_BYTES or \
                    (oldest and time.monotonic() - oldest > MAX_BACKLOG_SECONDS):
                overflow = True
            self._cond.notify()
        if overflow:
            # it has stopped reading: there is no saying goodbye, just let go
            self._drop()

    def _write_loop(self) -> None:
        while True:
            with self._cond:
                while not self._queue and not self._dropped:
                    self._cond.wait()
                if not self._queue:
                    return
                entry = self._queue.popleft()
                self._queued_bytes -= len(entry[0])
                if entry is self._pending_replace:
                    self._pending_replace = None
            try:
                self.sock.sendall(entry[0])
            except OSError:
                self._drop()
                return
            if entry is self._close_entry:
                self._drop()
                return

    def send_text(self, text: str, replace: bool = False) -> None:
        self._send_frame(OP_TEXT, text.encode("utf-8"), replace)

    def send_json(self, payload: Any) -> None:
        # state snapshots supersede each other; everything else is an event
        replace = isinstance(payload, dict) and payload.get("t") == "snap"
        self.send_text(json.dumps(payload, separators=(",", ":")), replace)

    def ping(self) -> None:
        self._send_frame(OP_PING, b"")

    @property
    def backlog(self) -> int:
        return self._queued_bytes

    def _drop(self) -> None:
        with self._cond:
            if self._dropped:
                return
            self.closed = True
            self._dropped = True
            self._queue.clear()
            self._queued_bytes = 0
            self._pending_replace = None
            self._cond.notify_all()
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass

    def close(self, code: int = 1000) -> None:
        """Stop taking frames, and let go once what is already queued (a
        "kicked" note, the last snapshot) and a close frame behind it are out
        -- or after CLOSE_GRACE_SECONDS if the peer is not reading.  Returns at
        once: nothing here waits on the peer."""
        with self._cond:
            if self.closed:
                return
            self.closed = True
            entry = [self._frame(OP_CLOSE, struct.pack("!H", code)),
                     time.monotonic(), False]
            self._close_entry = entry
            self._queue.append(entry)
            self._queued_bytes += len(entry[0])
            self._cond.notify()
        timer = threading.Timer(CLOSE_GRACE_SECONDS, self._drop)
        timer.daemon = True
        timer.start()


# The longest request line accepted.  The join ticket rides in the URL; it is
# kept small (the avatar travels by reference), and this matches the web
# server's own header limit so a line the web server forwarded is never cut
# short here -- a cut ticket fails its signature and the join is refused.
MAX_REQUEST_LINE = 32 * 1024


def read_http_request(rfile) -> Tuple[str, str, Dict[str, str]]:
    """Parse the upgrade request the web server proxied to us."""
    line = rfile.readline(MAX_REQUEST_LINE + 1)
    if not line:
        raise WebSocketError("empty request")
    if len(line) > MAX_REQUEST_LINE or not line.endswith(b"\n"):
        raise WebSocketError("request line too long")
    parts = line.decode("latin-1").strip().split()
    if len(parts) < 2:
        raise WebSocketError("bad request line")
    method, target = parts[0], parts[1]
    headers: Dict[str, str] = {}
    while True:
        header_line = rfile.readline(MAX_REQUEST_LINE)
        if not header_line or header_line in (b"\r\n", b"\n"):
            break
        raw = header_line.decode("latin-1").rstrip("\r\n")
        name, _, value = raw.partition(":")
        if name:
            headers[name.strip().lower()] = value.strip()
    return method, target, headers


def json_message(kind: str, **fields: Any) -> str:
    fields["t"] = kind
    return json.dumps(fields, separators=(",", ":"))
