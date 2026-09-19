#!/usr/bin/env python3
"""Check every Unusual effect against the shapes the renderer actually has.

An effect names its graphic by string, and the particle system falls back to
``puff`` for a name it does not know -- so a typo does not crash anything, it
just quietly ships a hat that throws smoke instead of skulls.  Nobody notices
until the effect is rolled, which may be weeks.  This reads the shape table
out of the engine and holds the catalogue against it, along with the ranges
that have to be the right way round.

    python3 tools/checkeffects.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from app.models import catalog                      # noqa: E402

ENGINE = BASE / "static" / "js" / "engine" / "particles.js"
BLENDS = ("add", "normal")
PASSED: list = []
FAILED: list = []


def check(name: str, condition: bool, detail: object = "") -> bool:
    if condition:
        PASSED.append(name)
    else:
        FAILED.append(name)
        print("  FAIL  %s  %s" % (name, str(detail)[:160]))
    return bool(condition)


def engine_shapes() -> list:
    """The shape names the atlas defines, in cell order."""
    source = ENGINE.read_text(encoding="utf-8")
    start = source.find("var SHAPE_CELLS")
    if start < 0:
        raise SystemExit("checkeffects: SHAPE_CELLS not found in %s" % ENGINE)
    body = source[start:source.find("var ATLAS_ROWS", start)]
    return re.findall(r"\['([a-z_]+)', function", body)


def main() -> int:
    shapes = engine_shapes()
    print("== %d shapes in the atlas, %d effects in the catalogue =="
          % (len(shapes), len(catalog.UNUSUAL_EFFECTS)))
    check("the atlas defines shapes", bool(shapes))
    check("shape names are unique", len(set(shapes)) == len(shapes),
          [s for s in shapes if shapes.count(s) > 1])

    for key, fx in catalog.UNUSUAL_EFFECTS.items():
        named = list(fx.get("shapes") or [])
        if fx.get("shape"):
            named.append(fx["shape"])
        check("%s: names at least one shape" % key, bool(named))
        for shape in named:
            check("%s: shape '%s' exists in the atlas" % (key, shape),
                  shape in shapes, "known: %s" % ", ".join(shapes))
        check("%s: has a name" % key, bool(fx.get("name")))
        check("%s: blend is %s" % (key, "/".join(BLENDS)),
              fx.get("blend", "normal") in BLENDS, fx.get("blend"))
        for field in ("size", "life", "rise"):
            pair = fx.get(field)
            if pair is None:
                continue
            check("%s: %s is a low/high pair" % (key, field),
                  isinstance(pair, list) and len(pair) == 2, pair)
            check("%s: %s low <= high" % (key, field), pair[0] <= pair[1], pair)
        check("%s: rate is positive" % key, (fx.get("rate") or 0) > 0,
              fx.get("rate"))
        colours = fx.get("colors") or []
        check("%s: has colours" % key, bool(colours))
        # Three digits is legal: the engine's hexToRgb expands #fff itself.
        check("%s: colours are hex" % key,
              all(re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", c)
                  for c in colours),
              colours)
        # The renderer keeps four stops per particle; more are dropped, which
        # is a ramp that silently does not do what the data says.
        check("%s: at most four colours" % key, len(colours) <= 4, len(colours))
        if fx.get("upright"):
            check("%s: wobble is a small angle" % key,
                  0 <= float(fx.get("wobble", 0.5)) <= 1.6, fx.get("wobble"))

    for dead, replacement in catalog.RETIRED_EFFECTS.items():
        check("retired '%s' points at a live effect" % dead,
              replacement in catalog.UNUSUAL_EFFECTS, replacement)
    check("every effect id is rollable",
          set(catalog.EFFECT_IDS) == set(catalog.UNUSUAL_EFFECTS))

    print("  %d passed, %d failed" % (len(PASSED), len(FAILED)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
