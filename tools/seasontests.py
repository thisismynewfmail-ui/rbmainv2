#!/usr/bin/env python3
"""The seasonal site skin (app/models/season.py): when it is on, what it says.

    python3 tools/seasontests.py

No server needed: it asks the model directly with fixed clocks.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import crates, season  # noqa: E402

PASSED = FAILED = 0


def check(name: str, ok: bool, detail: object = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print("  PASS  " + name)
    else:
        FAILED += 1
        print("  FAIL  %s  %r" % (name, detail))


def main() -> int:
    os.environ.pop("BLOCKHAVEN_SEASON", None)
    ev = crates.EVENTS["halloween"]
    starts, ends = ev["starts"], ev["ends"]
    print("== when the skin is on ==")
    check("on at the first second", (season.current(starts) or {}).get("holiday") == "halloween")
    check("on at the last second", (season.current(ends - 1) or {}).get("holiday") == "halloween")
    check("off the second it ends", season.current(ends) is None)
    check("off the second before it starts", season.current(starts - 1) is None,
          season.current(starts - 1))
    old = [e for e in crates.EVENTS.values() if e.get("holiday") == "halloween" and e["id"] != "halloween"]
    if old:
        past = min(old, key=lambda e: e["starts"])
        got = season.current(past["starts"] + 3600) or {}
        check("an earlier Halloween wears the same skin", got.get("event_id") == past["id"], got.get("event_id"))
    xmas = crates.EVENTS.get("christmas_2026")
    if xmas:
        check("a holiday without a skin leaves the site alone",
              season.current(xmas["starts"] + 9 * 86400) is None)
    os.environ["BLOCKHAVEN_EVENTS"] = "all"
    try:
        check("forcing every event on does not paint the site",
              season.current(xmas["starts"] + 9 * 86400) is None if xmas else True)
    finally:
        os.environ.pop("BLOCKHAVEN_EVENTS", None)

    print("\n== the switch ==")
    os.environ["BLOCKHAVEN_SEASON"] = "off"
    check("BLOCKHAVEN_SEASON=off turns it off", season.current(starts + 60) is None)
    os.environ["BLOCKHAVEN_SEASON"] = "halloween"
    pre = season.current(ends + 30 * 86400) or {}
    check("a preview out of season is forced and never ends",
          pre.get("forced") is True and pre.get("ends") == 0 and pre.get("left_long") == "PREVIEW", pre)
    os.environ.pop("BLOCKHAVEN_SEASON", None)

    print("\n== the countdown ==")
    check("days and hours", season.left_labels(28 * 86400 + 4 * 3600)[0] == "28d 4h")
    check("the last three days", season.left_labels(2 * 86400 + 5 * 3600)[0] == "LAST 3 DAYS · 2d 5h")
    check("the last day", season.left_labels(86400)[0] == "ENDS IN 24h 0m")
    check("the last hours", season.left_labels(5 * 3600 + 12 * 60)[0] == "ENDS IN 5h 12m")

    print("\n== which pages calm down ==")
    now = starts + 3600
    check("the market is calm", (season.current(now, "/market") or {}).get("calm") is True)
    check("a world page is quiet", (season.current(now, "/worlds/blackout_relay") or {}).get("lite") is True)
    check("the worlds list is not", (season.current(now, "/worlds") or {}).get("lite") is False)
    check("the sign-in page is quiet", (season.current(now, "/login") or {}).get("lite") is True)
    blob = json.dumps((season.current(now, "/") or {}).get("client"))
    check("the client blob is plain JSON with no markup", "<" not in blob and "event_id" in blob, blob)

    print("\n" + "=" * 20 + " %d passed, %d failed " % (PASSED, FAILED) + "=" * 20)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
