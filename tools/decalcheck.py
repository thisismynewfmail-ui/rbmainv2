#!/usr/bin/env python3
"""Every decal and weave the holiday events name, against the painters
static/js/engine/textures.js actually has.

    python3 tools/decalcheck.py            # what is missing, and where
    python3 tools/decalcheck.py halloween_2024

A decal with no painter draws as nothing at all, so a crate stencil or a
shirt print that was never painted is simply not there.  Exit status 1 when
anything is missing.
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.models import holidays  # noqa: E402

PAINTED = set(re.findall(r"(?:painter|emblem)\('([a-z_0-9]+)'",
                         open(os.path.join(ROOT, "static/js/engine/textures.js")).read()))


def walk(node, event_id, missing):
    if isinstance(node, dict):
        for key, value in node.items():
            if (key in ("decal", "weave") and isinstance(value, str)
                    and not value.startswith("#") and value not in PAINTED):
                missing.setdefault(value, set()).add(event_id)
            walk(value, event_id, missing)
    elif isinstance(node, (list, tuple)):
        for value in node:
            walk(value, event_id, missing)


def main() -> int:
    only = set(sys.argv[1:])
    missing = {}
    for event in holidays.EVENTS:
        if only and event.id not in only:
            continue
        walk(event.items, event.id, missing)
        walk(event.crate, event.id, missing)
        walk(event.key, event.id, missing)
        if event.stencil and event.stencil not in PAINTED:
            missing.setdefault(event.stencil, set()).add(event.id + " (stencil)")
    for name, where in sorted(missing.items()):
        print("  MISSING  %-20s %s" % (name, ", ".join(sorted(where))))
    print("== %d decal%s missing ==" % (len(missing), "" if len(missing) == 1 else "s"))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
