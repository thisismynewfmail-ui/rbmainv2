#!/usr/bin/env python3
"""Pictures of an event world's areas, thumbnails and arrival sequences.

    python3 tools/shots.py rail_rivals dustbowl            # the area's views
    python3 tools/shots.py rail_rivals dustbowl --cam "x,y,z,tx,ty,tz[,fov]"
    python3 tools/shots.py rail_rivals --thumbs            # card + area thumbnails
    python3 tools/shots.py rail_rivals --intros            # arrival stills
    python3 tools/shots.py ... --out /tmp/shots

Views are given in the area's own coordinates (its centre is 0, 0); with no
--cam the area's spectator cameras and a few overviews are shot.  Renders
through tools/shots.js (headless Chromium, the engine's own renderer).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("world")
    parser.add_argument("area", nargs="?")
    parser.add_argument("--cam", action="append", default=[])
    parser.add_argument("--thumbs", action="store_true")
    parser.add_argument("--intros", action="store_true")
    parser.add_argument("--times", default="1.2,3.0,4.6")
    parser.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "shots"))
    args = parser.parse_args(argv[1:])
    from app.models import worlds
    world = worlds.get_any(args.world)
    if world is None and (args.thumbs or args.intros):
        print("no such world")
        return 2
    job = {"width": 1280, "height": 720}
    if args.thumbs:
        job.update(kind="thumb", scripts=[world["thumb_script"]],
                   thumbs=[world["thumb"]] + [a["thumb"] for a in world.get("areas") or []])
    elif args.intros:
        times = [float(t) for t in args.times.split(",")]
        areas = [a for a in world.get("areas") or [] if not args.area or a["id"] == args.area]
        job.update(kind="intro", scripts=[], post=list(world.get("game_scripts") or []),
                   scenes=[[a["thumb"], t, {"name": a["name"], "round": 3, "logo": world["name"],
                                            "line": "One round, then the server moves on",
                                            "kicker": "NOW ENTERING"}]
                           for a in areas for t in times])
    else:
        import importlib
        from app.game.maps.events import kit
        package = importlib.import_module("app.game.maps.events.%s" % args.world)
        data = package.build()
        payload = kit.area_payload(data, args.area)
        ox, _, oz = payload["markers"]["centre"]
        views, names = [], []
        for i, text in enumerate(args.cam):
            v = [float(t) for t in text.split(",")]
            views.append([[v[0] + ox, v[1], v[2] + oz], [v[3] + ox, v[4], v[5] + oz],
                          v[6] if len(v) > 6 else 60])
            names.append("%s_cam%d" % (args.area, i))
        if not views:
            for i, cam in enumerate(payload["markers"].get("cameras") or []):
                views.append([cam["p"], cam["t"], 60])
                names.append("%s_spec%d" % (args.area, i))
            hx = (payload["markers"]["area_rect"][1] - payload["markers"]["area_rect"][0]) / 2
            for i, (ex, ey, ez, tx, tz) in enumerate(((0, hx * 1.1, 1, 0, 0),
                                                      (-hx * 0.9, 90, hx * 0.5, 0, 0),
                                                      (hx * 0.9, 90, -hx * 0.5, 0, 0))):
                views.append([[ox + ex, ey, oz + ez], [ox + tx, 0, oz + tz], 60])
                names.append("%s_over%d" % (args.area, i))
        job.update(kind="map", map=payload, views=views, names=names)
    handle, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(handle, "w") as f:
        json.dump(job, f)
    return subprocess.call(["node", os.path.join(ROOT, "tools", "shots.js"), "--job", path,
                            "--out", args.out])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
