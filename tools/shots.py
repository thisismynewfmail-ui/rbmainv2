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


def _scene_id(world, area):
    """The arrival scene an area plays: Last Light's are named by the area,
    the rotation's by its prefix and the area, an event world's by its
    thumbnail."""
    if world["id"] == "last_light":
        return area["id"]
    if world.get("prefix"):
        return "%s_%s" % (world["prefix"], area["id"])
    return area["thumb"]


def _scene_info(world, area):
    if world["id"] == "last_light":
        return {"name": area["name"], "round": 3, "attempt": 1, "tries": 3}
    return {"name": area["name"], "round": 3, "logo": world["name"],
            "line": "One round, then the server moves on", "kicker": "NOW ENTERING"}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("world")
    parser.add_argument("area", nargs="?")
    parser.add_argument("--cam", action="append", default=[])
    parser.add_argument("--thumbs", action="store_true")
    parser.add_argument("--intros", action="store_true")
    parser.add_argument("--times", default="1.2,3.0,4.6")
    parser.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "shots"))
    parser.add_argument("--rigtime", type=float, default=1000.0,
                        help="the clock the map's rigs are drawn at (wall seconds)")
    parser.add_argument("--rigsettle", type=float, default=4.0,
                        help="seconds of the rigs' lives run before the picture")
    parser.add_argument("--rigstate", default="",
                        help="JSON (or a file of it) for the rigs' world: {players: [{pos}], "
                             "flags: [{state, pos}], viewer: {eye, dir}, events: "
                             "[[seconds before, kind, msg]]}; positions in area coordinates")
    args = parser.parse_args(argv[1:])
    from app.models import worlds
    world = worlds.get_any(args.world)
    if world is None and (args.thumbs or args.intros):
        print("no such world")
        return 2
    job = {"width": 1280, "height": 720}
    if args.thumbs:
        job.update(kind="thumb", scripts=[world["thumb_script"]],
                   thumbs=[world["thumb"]] + [a.get("thumb") or ("ll_" + a["id"])
                                              for a in world.get("areas") or []])
    elif args.intros:
        times = [float(t) for t in args.times.split(",")]
        areas = [a for a in world.get("areas") or [] if not args.area or a["id"] == args.area]
        job.update(kind="intro", scripts=[], post=list(world.get("game_scripts") or []),
                   scenes=[[_scene_id(world, a), t, _scene_info(world, a)]
                           for a in areas for t in times])
    else:
        import importlib
        from app.game.maps.events import kit
        if args.world == "blackout_relay":
            # the map rotation is its own package, with its own payloads
            from app.game.maps import relay as package
            data = package.build()
            payload = package.area_payload(data, args.area)
        elif args.world == "last_light":
            from app.game.maps import lastlight as package
            data = package.build()
            payload = package.area_payload(data, args.area)
        else:
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
        # the map's moving scenery, drawn the way the client draws it
        scripts = [u for u in (world or {}).get("game_scripts") or [] if "_rigs" in u]
        if scripts:
            job["rigs"] = ["static/js/game/rigs.js"] + [u.lstrip("/") for u in scripts]
            job["rig_time"] = args.rigtime
            job["rig_settle"] = args.rigsettle
            state = {}
            if args.rigstate:
                text = args.rigstate
                if os.path.exists(text):
                    with open(text) as fh:
                        text = fh.read()
                state = json.loads(text)

            def place(p):
                return [p[0] + ox, p[1], p[2] + oz]
            for who in (state.get("players") or []) + (state.get("zombies") or []):
                who["pos"] = place(who["pos"])
            for flag in state.get("flags") or []:
                if flag.get("pos"):
                    flag["pos"] = place(flag["pos"])
            if state.get("viewer"):
                state["viewer"]["eye"] = place(state["viewer"]["eye"])
            for event in state.get("events") or []:
                if len(event) > 2 and isinstance(event[2], dict) and event[2].get("from"):
                    event[2]["from"] = place(event[2]["from"])
            job["rig_state"] = state
    handle, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(handle, "w") as f:
        json.dump(job, f)
    return subprocess.call(["node", os.path.join(ROOT, "tools", "shots.js"), "--job", path,
                            "--out", args.out])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
