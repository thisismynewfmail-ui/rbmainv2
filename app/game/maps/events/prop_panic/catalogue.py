"""Prop Panic's props: every thing a hider can turn into, in one place.

Each kind is drawn once, here, in its own local frame -- standing on the
floor at the origin, front to +z -- and that one drawing is used three ways:

* the areas furnish themselves with it (:func:`place`), so the teapot on
  Grandma's sideboard is these parts;
* the client draws a hider wearing it from the same parts (they travel to
  it in the area's ``extra["props"]``), so a disguise is the real thing and
  not a lookalike;
* the rules take its ``size`` as the hider's hull -- what a hunter's shot
  has to hit, and what the hider's own movement collides with.

A kind's parts all fit inside its ``size`` box, and every part is solid and
axis aligned (quarter turns only), so a placed prop collides exactly as it
looks and a disguised one never pokes through a wall it is pressed against.
Details that sit on a face stand a few hundredths proud of it, so no two
faces of one prop ever share a plane.

``hp`` is how much a hider in it can take: small things go down fast, big
things soak a magazine.  ``speed`` is how a hider in it moves (a footstool
scuttles, a suit of armour clanks).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

from ..kit import sign_decal

Part = Dict[str, Any]

# ---------------------------------------------------------------- palette
WOOD = "#7a5335"
WOOD_LIGHT = "#a07a52"
WOOD_DARK = "#543923"
WOOD_RED = "#7a3a24"
IRON = "#3a3e44"
BRASS = "#c89a3a"
GOLD = "#d8b040"
SILVER = "#b8bcc2"
WHITE = "#f2f0ea"
CREAM = "#efe3c8"
BLACK = "#22242a"
ROSE = "#b0606e"
SAGE = "#7f9a72"
PLUM = "#6e4a6a"
MUSTARD = "#d0a040"
TERRACOTTA = "#c0663a"
LEAF = "#4a8a3a"
LEAF_DARK = "#356a2c"
SOIL = "#4a3424"
STONE = "#a89a88"
MARBLE = "#e8e4dc"
BRONZE = "#a8743a"
SAND = "#c8a878"
LAPIS = "#2a4a9a"
RED = "#d8402a"
BLUE = "#2f6ad0"
YELLOW = "#f2c230"
GREEN = "#3aa04a"
PURPLE = "#8a4ad0"
ORANGE = "#f08a2a"
PINK = "#f07aa8"
TEAL = "#2ab0a0"
SKIN = "#f5cd30"


# ------------------------------------------------------------ the drawing
def _part(t: str, x: float, y0: float, z: float, w: float, h: float, d: float,
          c: str, **o: Any) -> Part:
    """A part standing on ``y0`` (its bottom), centred on (x, z)."""
    part: Part = {"t": t, "p": [round(x, 3), round(y0 + h / 2.0, 3), round(z, 3)],
                  "s": [round(w, 3), round(h, 3), round(d, 3)], "c": c}
    if o.get("m"):
        part["m"] = o["m"]
    if o.get("dec"):
        part["dec"] = o["dec"]
    if o.get("turn"):
        part["turn"] = int(o["turn"]) % 4      # a quarter turn of its own
    if o.get("wrap"):
        part["dw"] = 1                         # the decal all the way round
    if o.get("ghost"):
        part["ghost"] = 1                      # no collision (light, glass, paint)
    if o.get("a") is not None and o["a"] < 1.0:
        part["a"] = float(o["a"])
    return part


def B(x, y0, z, w, h, d, c, **o):     # a box
    return _part("box", x, y0, z, w, h, d, c, **o)


def R(x, y0, z, w, h, d, c, **o):     # a rounded box: cushions, plush
    return _part("rbox", x, y0, z, w, h, d, c, **o)


def C(x, y0, z, w, h, d, c, **o):     # an upright cylinder
    return _part("cyl", x, y0, z, w, h, d, c, **o)


def S(x, y0, z, w, h, d, c, **o):     # a sphere (its box)
    return _part("sph", x, y0, z, w, h, d, c, **o)


def K(x, y0, z, w, h, d, c, **o):     # a cone, point up
    return _part("cone", x, y0, z, w, h, d, c, **o)


def M(mesh, x, y0, z, w, h, d, c, **o):   # one of the engine's own meshes
    return _part(mesh, x, y0, z, w, h, d, c, **o)


def _kind(name: str, size: Sequence[float], hp: int, parts: List[Part],
          speed: float = 1.0, tags: Sequence[str] = ()) -> Dict[str, Any]:
    return {"name": name, "size": [float(v) for v in size], "hp": int(hp),
            "speed": float(speed), "parts": parts, "tags": list(tags)}


KINDS: Dict[str, Dict[str, Any]] = {}


def kind(key: str, *args, **kw) -> None:
    KINDS[key] = _kind(*args, **kw)


# ================================================================ cottage
kind("armchair", "Armchair", (2.8, 3.4, 2.6), 100, [
    C(-1.0, 0.0, -0.9, 0.3, 0.32, 0.3, WOOD_DARK), C(1.0, 0.0, -0.9, 0.3, 0.32, 0.3, WOOD_DARK),
    C(-1.0, 0.0, 0.9, 0.3, 0.32, 0.3, WOOD_DARK), C(1.0, 0.0, 0.9, 0.3, 0.32, 0.3, WOOD_DARK),
    B(0.0, 0.32, 0.1, 2.0, 0.88, 2.2, ROSE, dec="rosebuds"),
    R(0.0, 1.2, 0.25, 1.9, 0.5, 1.9, CREAM),
    B(-1.2, 0.32, 0.05, 0.4, 1.9, 2.3, ROSE, dec="rosebuds"),
    B(1.2, 0.32, 0.05, 0.4, 1.9, 2.3, ROSE, dec="rosebuds"),
    R(0.0, 1.2, -0.95, 2.0, 2.2, 0.5, ROSE),
], speed=0.88, tags=["sit"])

kind("dining_chair", "Dining chair", (1.9, 4.0, 1.9), 60, [
    B(-0.75, 0.0, 0.75, 0.24, 1.7, 0.24, WOOD), B(0.75, 0.0, 0.75, 0.24, 1.7, 0.24, WOOD),
    B(-0.75, 0.0, -0.75, 0.24, 1.7, 0.24, WOOD), B(0.75, 0.0, -0.75, 0.24, 1.7, 0.24, WOOD),
    B(0.0, 1.7, 0.0, 1.8, 0.24, 1.8, WOOD_LIGHT),
    R(0.0, 1.94, 0.1, 1.5, 0.22, 1.4, ROSE),
    B(-0.75, 1.94, -0.78, 0.24, 2.06, 0.24, WOOD), B(0.75, 1.94, -0.78, 0.24, 2.06, 0.24, WOOD),
    B(0.0, 3.3, -0.78, 1.8, 0.5, 0.2, WOOD_LIGHT),
    B(0.0, 2.6, -0.78, 1.26, 0.3, 0.16, WOOD),
], tags=["sit"])

kind("rocking_chair", "Rocking chair", (2.0, 3.6, 2.6), 80, [
    B(-0.85, 0.0, 0.0, 0.25, 0.25, 2.5, WOOD_DARK), B(0.85, 0.0, 0.0, 0.25, 0.25, 2.5, WOOD_DARK),
    B(-0.8, 0.25, 0.6, 0.2, 1.05, 0.2, WOOD), B(0.8, 0.25, 0.6, 0.2, 1.05, 0.2, WOOD),
    B(-0.8, 0.25, -0.6, 0.2, 1.05, 0.2, WOOD), B(0.8, 0.25, -0.6, 0.2, 1.05, 0.2, WOOD),
    B(0.0, 1.3, 0.0, 1.8, 0.2, 1.6, WOOD_LIGHT),
    R(0.0, 1.5, 0.05, 1.5, 0.3, 1.3, SAGE),
    B(-0.8, 1.5, -0.7, 0.18, 2.0, 0.18, WOOD), B(0.8, 1.5, -0.7, 0.18, 2.0, 0.18, WOOD),
    B(0.0, 2.1, -0.7, 1.42, 0.15, 0.12, WOOD_LIGHT), B(0.0, 2.7, -0.7, 1.42, 0.15, 0.12, WOOD_LIGHT),
    B(0.0, 3.3, -0.7, 1.84, 0.3, 0.32, WOOD),
], tags=["sit"])

kind("grandfather_clock", "Grandfather clock", (1.8, 6.4, 1.2), 90, [
    B(0.0, 0.0, 0.0, 1.8, 0.5, 1.2, WOOD_DARK),
    B(0.0, 0.5, 0.0, 1.4, 3.6, 0.9, WOOD_RED),
    B(0.0, 1.2, 0.47, 0.8, 2.4, 0.04, "#2a1a10"),
    C(0.0, 1.5, 0.52, 0.5, 0.5, 0.06, BRASS),
    B(0.0, 1.9, 0.53, 0.08, 1.4, 0.04, BRASS),
    B(0.0, 4.1, 0.0, 1.7, 1.7, 1.1, WOOD_RED),
    B(0.0, 4.25, 0.56, 1.3, 1.3, 0.04, CREAM, dec="clockface"),
    B(0.0, 5.8, 0.0, 1.8, 0.3, 1.2, WOOD_DARK),
    B(0.0, 6.1, 0.0, 1.2, 0.3, 0.8, WOOD_DARK),
], speed=0.85, tags=["tall"])

kind("floor_lamp", "Floor lamp", (1.6, 5.2, 1.6), 50, [
    C(0.0, 0.0, 0.0, 1.2, 0.2, 1.2, BRASS),
    C(0.0, 0.2, 0.0, 0.2, 3.6, 0.2, BRASS),
    K(0.0, 3.8, 0.0, 1.6, 1.4, 1.6, CREAM),
    C(0.0, 3.62, 0.0, 0.5, 0.18, 0.5, "#ffe2a8", m="neon"),
], tags=["tall"])

kind("potted_plant", "Potted plant", (1.8, 3.0, 1.8), 50, [
    C(0.0, 0.0, 0.0, 1.3, 1.1, 1.3, TERRACOTTA),
    C(0.0, 1.1, 0.0, 1.4, 0.2, 1.4, "#a8542e"),
    C(0.0, 1.2, 0.0, 1.1, 0.06, 1.1, SOIL),
    S(0.0, 1.25, 0.0, 1.8, 1.75, 1.8, LEAF),
], tags=["plant"])

kind("teapot", "Teapot", (1.6, 1.4, 1.1), 40, [
    S(0.0, 0.0, 0.0, 1.1, 1.0, 1.1, "#f2f0ea"),
    B(0.0, 0.0, 0.0, 0.7, 0.1, 0.7, "#d0c8b8"),
    C(0.0, 0.95, 0.0, 0.42, 0.2, 0.42, ROSE),
    S(0.0, 1.12, 0.0, 0.22, 0.22, 0.22, ROSE),
    B(0.62, 0.35, 0.0, 0.36, 0.18, 0.2, "#f2f0ea"),
    B(-0.62, 0.3, 0.0, 0.14, 0.5, 0.18, "#f2f0ea"),
], speed=1.12, tags=["small", "table"])

kind("cookie_jar", "Cookie jar", (1.1, 1.4, 1.1), 30, [
    C(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, "#c8b0e0"),
    C(0.0, 1.0, 0.0, 1.06, 0.18, 1.06, PLUM),
    S(0.0, 1.18, 0.0, 0.3, 0.22, 0.3, PLUM),
    B(0.0, 0.35, 0.47, 0.5, 0.3, 0.06, CREAM, dec=sign_decal("COOKIES", CREAM, PLUM, 1.7)),
], speed=1.12, tags=["small", "table"])

kind("yarn_basket", "Basket of yarn", (1.8, 1.6, 1.8), 40, [
    C(0.0, 0.0, 0.0, 1.7, 0.9, 1.7, "#b08a5a"),
    S(-0.35, 0.6, -0.2, 0.8, 0.8, 0.8, ROSE),
    S(0.35, 0.62, 0.15, 0.75, 0.75, 0.75, "#7aa0c8"),
    S(0.0, 0.75, -0.45, 0.62, 0.62, 0.62, MUSTARD),
    C(0.35, 1.1, 0.4, 0.06, 0.5, 0.06, "#c8c8c8"),
], speed=1.06, tags=["small"])

kind("footstool", "Footstool", (1.9, 1.3, 1.5), 50, [
    C(-0.7, 0.0, -0.5, 0.22, 0.4, 0.22, WOOD_DARK), C(0.7, 0.0, -0.5, 0.22, 0.4, 0.22, WOOD_DARK),
    C(-0.7, 0.0, 0.5, 0.22, 0.4, 0.22, WOOD_DARK), C(0.7, 0.0, 0.5, 0.22, 0.4, 0.22, WOOD_DARK),
    B(0.0, 0.4, 0.0, 1.8, 0.4, 1.4, WOOD),
    R(0.0, 0.8, 0.0, 1.7, 0.5, 1.3, PLUM),
], speed=1.1, tags=["small"])

kind("side_table", "Side table", (2.0, 2.6, 2.0), 70, [
    B(-0.8, 0.0, -0.8, 0.22, 2.0, 0.22, WOOD_DARK), B(0.8, 0.0, -0.8, 0.22, 2.0, 0.22, WOOD_DARK),
    B(-0.8, 0.0, 0.8, 0.22, 2.0, 0.22, WOOD_DARK), B(0.8, 0.0, 0.8, 0.22, 2.0, 0.22, WOOD_DARK),
    B(0.0, 0.6, 0.0, 1.38, 0.12, 1.38, WOOD),
    B(0.0, 2.0, 0.0, 2.0, 0.2, 2.0, WOOD),
    B(0.0, 2.2, 0.0, 1.5, 0.04, 1.5, "#f4ece0", dec="lace"),
    C(0.35, 2.24, 0.2, 0.4, 0.36, 0.4, "#5a8ac0"),
], tags=["table"])

kind("book_stack", "Stack of books", (1.5, 1.5, 1.1), 30, [
    B(0.0, 0.0, 0.0, 1.4, 0.36, 1.0, "#7a2a2a"),
    B(0.04, 0.36, 0.02, 1.3, 0.34, 0.94, "#2a4a6a"),
    B(-0.05, 0.7, -0.02, 1.2, 0.3, 0.9, "#2a6a3a"),
    B(0.06, 1.0, 0.03, 1.1, 0.28, 0.84, MUSTARD),
    B(0.0, 1.28, 0.0, 1.0, 0.2, 0.8, PLUM),
], speed=1.12, tags=["small", "table"])

kind("radio", "Old radio", (1.7, 1.6, 1.1), 40, [
    R(0.0, 0.0, 0.0, 1.6, 1.4, 0.9, WOOD_RED),
    B(-0.3, 0.3, 0.47, 0.8, 0.8, 0.04, "#c8b090", dec="canvas"),
    C(0.5, 0.75, 0.48, 0.32, 0.32, 0.06, BRASS),
    C(0.5, 0.3, 0.48, 0.22, 0.22, 0.06, BRASS),
    B(0.0, 1.4, 0.0, 0.5, 0.12, 0.3, WOOD_DARK),
], speed=1.1, tags=["small", "table"])

kind("birdcage", "Birdcage", (1.5, 3.0, 1.5), 50, [
    C(0.0, 0.0, 0.0, 1.4, 0.2, 1.4, BRASS),
    C(0.0, 0.2, 0.0, 1.3, 1.8, 1.3, GOLD, m="metal"),
    S(0.0, 1.6, 0.0, 1.32, 1.0, 1.32, GOLD, m="metal"),
    C(0.0, 2.5, 0.0, 0.1, 0.3, 0.1, BRASS),
    S(0.0, 2.75, 0.0, 0.3, 0.25, 0.3, BRASS),
    S(0.0, 0.85, 0.66, 0.36, 0.36, 0.08, YELLOW),
], tags=["tall"])

kind("umbrella_stand", "Umbrella stand", (1.1, 3.0, 1.1), 40, [
    C(0.0, 0.0, 0.0, 1.0, 1.8, 1.0, "#4a6a5a"),
    C(0.0, 1.8, 0.0, 1.06, 0.1, 1.06, BRASS),
    C(-0.2, 1.9, 0.1, 0.16, 0.9, 0.16, BLACK),
    C(0.22, 1.9, -0.12, 0.16, 0.7, 0.16, "#8a2a3a"),
    B(-0.2, 2.8, 0.1, 0.4, 0.14, 0.14, WOOD_DARK),
], speed=1.05, tags=["tall"])

kind("laundry_basket", "Laundry basket", (2.2, 1.8, 1.5), 50, [
    B(0.0, 0.0, 0.0, 2.1, 1.2, 1.4, "#c8a870", dec="wicker"),
    R(-0.4, 1.0, 0.0, 1.1, 0.6, 1.1, "#a8c8e0"),
    R(0.45, 1.05, -0.05, 0.9, 0.7, 0.9, "#f0d0d8"),
], tags=["small"])

kind("garden_gnome", "Garden gnome", (1.2, 2.2, 1.2), 40, [
    C(0.0, 0.0, 0.0, 1.0, 0.2, 1.0, "#8a8a80"),
    C(0.0, 0.2, 0.0, 0.8, 0.7, 0.8, BLUE),
    S(0.0, 0.8, 0.0, 0.8, 0.5, 0.7, RED),
    S(0.0, 1.0, 0.18, 0.5, 0.48, 0.42, "#f2c8a0"),
    S(0.0, 0.85, 0.22, 0.44, 0.42, 0.3, WHITE),
    K(0.0, 1.38, 0.0, 0.66, 0.8, 0.66, RED),
], speed=1.1, tags=["small", "garden"])

kind("watering_can", "Watering can", (1.8, 1.3, 0.9), 30, [
    C(0.0, 0.0, 0.0, 0.9, 0.9, 0.8, "#4a8a6a", m="metal"),
    B(0.68, 0.35, 0.0, 0.44, 0.16, 0.16, "#4a8a6a", m="metal"),
    C(0.82, 0.5, 0.0, 0.16, 0.28, 0.16, "#3a7a5a", m="metal"),
    B(-0.2, 0.9, 0.0, 0.14, 0.38, 0.14, "#3a7a5a", m="metal"),
    B(0.0, 1.16, 0.0, 0.58, 0.14, 0.12, "#3a7a5a", m="metal"),
], speed=1.12, tags=["small", "garden"])

kind("flower_pot", "Flower pot", (1.4, 1.6, 1.4), 30, [
    C(0.0, 0.0, 0.0, 1.0, 0.8, 1.0, TERRACOTTA),
    C(0.0, 0.8, 0.0, 1.1, 0.16, 1.1, "#a8542e"),
    S(-0.2, 0.85, 0.1, 0.62, 0.55, 0.62, "#e85a8a"),
    S(0.24, 0.9, -0.12, 0.55, 0.6, 0.55, YELLOW),
    S(0.0, 1.0, -0.2, 0.5, 0.55, 0.5, "#c86ad8"),
], speed=1.12, tags=["small", "garden", "plant"])

kind("wheelbarrow", "Wheelbarrow", (1.9, 1.9, 3.6), 80, [
    S(0.0, 0.0, 1.35, 0.22, 0.9, 0.9, BLACK),
    B(0.0, 0.32, 1.35, 0.3, 0.26, 0.3, IRON),
    B(-0.5, 0.0, -0.9, 0.16, 0.7, 0.16, IRON), B(0.5, 0.0, -0.9, 0.16, 0.7, 0.16, IRON),
    B(0.0, 0.7, 0.0, 1.8, 0.9, 2.2, "#3a7ac0", m="metal"),
    B(0.0, 1.6, 0.0, 1.5, 0.08, 1.9, SOIL),
    B(-0.6, 0.85, -1.45, 0.14, 0.14, 0.7, WOOD), B(0.6, 0.85, -1.45, 0.14, 0.14, 0.7, WOOD),
], speed=0.95, tags=["garden"])

kind("birdbath", "Birdbath", (1.9, 2.6, 1.9), 70, [
    C(0.0, 0.0, 0.0, 1.2, 0.3, 1.2, STONE),
    C(0.0, 0.3, 0.0, 0.5, 1.5, 0.5, STONE),
    C(0.0, 1.8, 0.0, 1.9, 0.5, 1.9, STONE),
    C(0.0, 2.3, 0.0, 1.5, 0.06, 1.5, "#7ab8d8"),
    S(0.4, 2.3, 0.2, 0.3, 0.3, 0.4, "#8a6a4a"),
], tags=["garden"])

kind("toaster", "Toaster", (1.5, 1.2, 1.0), 30, [
    R(0.0, 0.0, 0.0, 1.4, 1.0, 0.9, SILVER),
    B(-0.3, 1.0, 0.0, 0.25, 0.04, 0.6, BLACK), B(0.3, 1.0, 0.0, 0.25, 0.04, 0.6, BLACK),
    B(-0.3, 0.92, 0.0, 0.2, 0.22, 0.5, "#d8a868"),
    B(0.71, 0.5, 0.0, 0.06, 0.16, 0.3, BLACK),
], speed=1.12, tags=["small", "table"])

kind("pedal_bin", "Pedal bin", (1.3, 2.2, 1.3), 50, [
    C(0.0, 0.0, 0.0, 1.2, 1.9, 1.2, "#c8ccd0", m="metal"),
    C(0.0, 1.9, 0.0, 1.24, 0.2, 1.24, "#a8acb0", m="metal"),
    B(0.0, 0.0, 0.58, 0.5, 0.12, 0.12, BLACK),
], tags=["small"])

kind("television", "Old television", (2.6, 3.4, 2.2), 80, [
    B(-1.1, 0.0, -0.9, 0.2, 1.2, 0.2, WOOD_DARK), B(1.1, 0.0, -0.9, 0.2, 1.2, 0.2, WOOD_DARK),
    B(-1.1, 0.0, 0.9, 0.2, 1.2, 0.2, WOOD_DARK), B(1.1, 0.0, 0.9, 0.2, 1.2, 0.2, WOOD_DARK),
    B(0.0, 1.2, 0.0, 2.6, 0.2, 2.2, WOOD),
    B(0.0, 1.4, -0.1, 2.4, 1.8, 1.8, WOOD_RED),
    B(-0.25, 1.65, 0.81, 1.6, 1.3, 0.04, "#2a3a3a", m="glass"),
    C(0.8, 2.4, 0.82, 0.28, 0.28, 0.06, BRASS), C(0.8, 1.85, 0.82, 0.28, 0.28, 0.06, BRASS),
    C(-0.4, 3.2, -0.2, 0.1, 0.2, 0.1, SILVER), C(0.4, 3.2, -0.2, 0.1, 0.2, 0.1, SILVER),
], speed=0.88, tags=["table"])

kind("hatbox", "Hatbox", (1.6, 1.3, 1.6), 30, [
    C(0.0, 0.0, 0.0, 1.5, 1.0, 1.5, "#f0c0c8"),
    C(0.0, 1.0, 0.0, 1.58, 0.24, 1.58, "#e090a0"),
    B(0.0, 1.24, 0.0, 0.7, 0.06, 0.16, "#c03a5a"),
], speed=1.12, tags=["small"])


# ================================================================== toys
kind("teddy_bear", "Teddy bear", (2.4, 3.0, 1.9), 70, [
    R(-0.5, 0.0, 0.45, 0.7, 0.6, 0.9, "#a87a4a"), R(0.5, 0.0, 0.45, 0.7, 0.6, 0.9, "#a87a4a"),
    S(0.0, 0.0, -0.15, 1.7, 1.7, 1.4, "#a87a4a"),
    S(0.0, 0.5, 0.5, 0.9, 0.9, 0.3, "#d8b088"),
    S(-0.95, 0.75, 0.05, 0.5, 0.9, 0.5, "#a87a4a"), S(0.95, 0.75, 0.05, 0.5, 0.9, 0.5, "#a87a4a"),
    S(0.0, 1.55, 0.0, 1.2, 1.15, 1.1, "#a87a4a"),
    S(0.0, 1.8, 0.48, 0.5, 0.4, 0.3, "#d8b088"),
    S(0.0, 1.95, 0.65, 0.16, 0.12, 0.1, BLACK),
    S(-0.5, 2.5, 0.0, 0.42, 0.42, 0.3, "#a87a4a"), S(0.5, 2.5, 0.0, 0.42, 0.42, 0.3, "#a87a4a"),
    B(0.0, 1.38, 0.32, 0.8, 0.18, 0.5, RED),
], speed=0.95, tags=["plush"])

kind("toy_block", "Toy block", (1.8, 1.8, 1.8), 50, [
    B(0.0, 0.0, 0.0, 1.8, 1.8, 1.8, RED, dec=sign_decal("A", RED, WHITE)),
], speed=1.05, tags=["block"])

kind("toy_block_b", "Toy block", (1.8, 1.8, 1.8), 50, [
    B(0.0, 0.0, 0.0, 1.8, 1.8, 1.8, BLUE, dec=sign_decal("B", BLUE, YELLOW)),
], speed=1.05, tags=["block"])

kind("toy_block_c", "Toy block", (1.8, 1.8, 1.8), 50, [
    B(0.0, 0.0, 0.0, 1.8, 1.8, 1.8, GREEN, dec=sign_decal("C", GREEN, WHITE)),
], speed=1.05, tags=["block"])

kind("jack_in_box", "Jack-in-the-box", (2.0, 2.2, 1.8), 50, [
    B(0.0, 0.0, 0.0, 1.6, 1.6, 1.6, PURPLE, dec="party"),
    B(0.0, 1.6, 0.0, 1.7, 0.12, 1.7, YELLOW),
    S(0.85, 0.6, 0.0, 0.1, 0.4, 0.4, SILVER, m="metal"),
    B(0.95, 0.75, 0.0, 0.08, 0.5, 0.08, SILVER),
    S(0.0, 1.72, 0.0, 0.5, 0.45, 0.5, RED),
], speed=1.05, tags=["box"])

kind("rubber_duck", "Rubber duck", (1.6, 1.7, 2.0), 40, [
    S(0.0, 0.0, -0.15, 1.5, 1.0, 1.6, YELLOW),
    S(0.0, 0.75, 0.45, 0.9, 0.85, 0.85, YELLOW),
    B(0.0, 1.0, 0.85, 0.5, 0.18, 0.3, ORANGE),
    S(-0.25, 1.25, 0.8, 0.14, 0.14, 0.06, BLACK), S(0.25, 1.25, 0.8, 0.14, 0.14, 0.06, BLACK),
    B(0.0, 0.6, -0.95, 0.4, 0.3, 0.1, YELLOW),
], speed=1.08, tags=["plush"])

kind("toy_robot", "Wind-up robot", (1.9, 3.2, 1.4), 60, [
    B(-0.35, 0.0, 0.0, 0.45, 1.0, 0.6, SILVER, m="metal"),
    B(0.35, 0.0, 0.0, 0.45, 1.0, 0.6, SILVER, m="metal"),
    B(0.0, 1.0, 0.0, 1.3, 1.2, 0.9, "#7a8aa8", m="metal"),
    B(0.0, 1.35, 0.46, 0.7, 0.5, 0.04, "#2a3a4a", dec="neongrid"),
    B(-0.78, 1.2, 0.0, 0.26, 0.9, 0.3, SILVER, m="metal"),
    B(0.78, 1.2, 0.0, 0.26, 0.9, 0.3, SILVER, m="metal"),
    B(0.0, 2.2, 0.0, 0.9, 0.7, 0.8, "#7a8aa8", m="metal"),
    B(-0.2, 2.45, 0.41, 0.2, 0.16, 0.04, "#7affd8", m="neon"),
    B(0.2, 2.45, 0.41, 0.2, 0.16, 0.04, "#7affd8", m="neon"),
    C(0.0, 2.9, 0.0, 0.08, 0.2, 0.08, SILVER),
    S(0.0, 3.0, 0.0, 0.2, 0.2, 0.2, RED, m="neon"),
    B(0.0, 1.4, -0.55, 0.12, 0.12, 0.2, BRASS),
    B(0.0, 1.32, -0.63, 0.5, 0.28, 0.06, BRASS),
], tags=["robot"])

kind("toy_drum", "Toy drum", (1.9, 1.5, 1.9), 50, [
    C(0.0, 0.0, 0.0, 1.8, 0.14, 1.8, YELLOW),
    C(0.0, 0.14, 0.0, 1.7, 0.9, 1.7, RED, dec="harlequin", wrap=True),
    C(0.0, 1.04, 0.0, 1.8, 0.14, 1.8, YELLOW),
    C(0.0, 1.18, 0.0, 1.66, 0.04, 1.66, WHITE),
    B(-0.3, 1.22, 0.1, 0.12, 0.12, 0.9, WOOD_LIGHT),
    B(0.3, 1.22, -0.1, 0.12, 0.12, 0.9, WOOD_LIGHT),
], speed=1.05, tags=["box"])

kind("rocking_horse", "Rocking horse", (1.2, 3.4, 3.6), 80, [
    B(-0.45, 0.0, 0.0, 0.2, 0.25, 3.5, WOOD_DARK), B(0.45, 0.0, 0.0, 0.2, 0.25, 3.5, WOOD_DARK),
    B(-0.4, 0.25, 0.9, 0.18, 1.1, 0.18, WOOD), B(0.4, 0.25, 0.9, 0.18, 1.1, 0.18, WOOD),
    B(-0.4, 0.25, -0.9, 0.18, 1.1, 0.18, WOOD), B(0.4, 0.25, -0.9, 0.18, 1.1, 0.18, WOOD),
    R(0.0, 1.35, 0.0, 0.9, 0.9, 2.3, WHITE),
    B(0.0, 2.25, 0.05, 0.94, 0.12, 0.7, RED),
    R(0.0, 2.0, 1.05, 0.7, 1.2, 0.6, WHITE),
    R(0.0, 2.7, 1.35, 0.6, 0.55, 0.9, WHITE),
    B(0.0, 2.25, 0.82, 0.16, 0.9, 0.2, "#5a3a2a"),
    B(0.0, 1.5, -1.25, 0.2, 0.9, 0.2, "#5a3a2a"),
    B(-0.32, 2.85, 1.55, 0.04, 0.12, 0.12, BLACK), B(0.32, 2.85, 1.55, 0.04, 0.12, 0.12, BLACK),
], speed=0.92, tags=["plush"])

kind("beach_ball", "Beach ball", (1.8, 1.8, 1.8), 40, [
    S(0.0, 0.0, 0.0, 1.8, 1.8, 1.8, WHITE, dec="sp_rainbow_gores", wrap=True),
], speed=1.1, tags=["ball"])

kind("toy_rocket", "Toy rocket", (1.6, 3.8, 1.6), 60, [
    B(-0.65, 0.0, 0.0, 0.3, 0.9, 0.12, RED), B(0.65, 0.0, 0.0, 0.3, 0.9, 0.12, RED),
    B(0.0, 0.0, -0.65, 0.12, 0.9, 0.3, RED), B(0.0, 0.0, 0.65, 0.12, 0.9, 0.3, RED),
    C(0.0, 0.0, 0.0, 1.0, 2.6, 1.0, WHITE, m="metal"),
    C(0.0, 1.5, 0.0, 1.04, 0.3, 1.04, BLUE),
    S(0.0, 1.9, 0.48, 0.4, 0.4, 0.1, "#8ad8ff", m="glass"),
    K(0.0, 2.6, 0.0, 1.0, 1.2, 1.0, RED),
], tags=["tall"])

kind("spinning_top", "Spinning top", (1.7, 1.9, 1.7), 40, [
    K(0.0, 0.0, 0.0, 0.5, 0.4, 0.5, SILVER),
    C(0.0, 0.4, 0.0, 1.6, 0.5, 1.6, ORANGE, dec="sp26_gores", wrap=True),
    K(0.0, 0.9, 0.0, 1.5, 0.7, 1.5, TEAL),
    C(0.0, 1.5, 0.0, 0.16, 0.4, 0.16, WOOD_LIGHT),
], speed=1.1, tags=["ball"])

kind("gift_box", "Gift box", (1.9, 1.8, 1.9), 50, [
    B(0.0, 0.0, 0.0, 1.8, 1.3, 1.8, "#3aa07a"),
    B(0.0, 1.3, 0.0, 1.9, 0.3, 1.9, "#2a8a6a"),
    B(0.0, 0.02, 0.0, 0.3, 1.3, 1.84, RED),
    B(0.0, 0.03, 0.0, 1.84, 1.28, 0.3, RED),
    B(0.0, 1.6, 0.0, 0.32, 0.04, 1.9, RED),
    S(-0.25, 1.6, 0.0, 0.5, 0.2, 0.36, RED), S(0.25, 1.6, 0.0, 0.5, 0.2, 0.36, RED),
], speed=1.05, tags=["box"])

kind("toy_soldier", "Toy soldier", (1.3, 3.6, 1.1), 60, [
    C(0.0, 0.0, 0.0, 1.2, 0.2, 1.0, GREEN),
    B(-0.22, 0.2, 0.0, 0.36, 1.1, 0.4, "#1a2a5a"), B(0.22, 0.2, 0.0, 0.36, 1.1, 0.4, "#1a2a5a"),
    B(0.0, 1.3, 0.0, 0.9, 1.0, 0.55, RED),
    B(0.0, 1.85, 0.29, 0.1, 0.4, 0.04, GOLD),
    B(-0.54, 1.35, 0.0, 0.2, 0.85, 0.24, RED), B(0.54, 1.35, 0.0, 0.2, 0.85, 0.24, RED),
    S(0.0, 2.3, 0.0, 0.6, 0.6, 0.55, "#f2c8a0"),
    C(0.0, 2.7, 0.0, 0.62, 0.9, 0.55, BLACK),
], speed=1.0, tags=["tall"])

kind("plush_dino", "Plush dinosaur", (2.0, 2.8, 3.4), 80, [
    R(-0.45, 0.0, 0.2, 0.6, 0.7, 0.6, GREEN), R(0.45, 0.0, 0.2, 0.6, 0.7, 0.6, GREEN),
    S(0.0, 0.3, -0.1, 1.6, 1.5, 1.9, GREEN),
    S(0.0, 0.5, -1.1, 0.8, 0.7, 1.0, GREEN),
    S(0.0, 1.4, 0.8, 0.8, 1.1, 0.8, GREEN),
    S(0.0, 2.0, 1.1, 0.95, 0.75, 1.1, GREEN),
    S(-0.3, 2.35, 1.55, 0.18, 0.18, 0.08, BLACK), S(0.3, 2.35, 1.55, 0.18, 0.18, 0.08, BLACK),
    K(0.0, 1.7, -0.1, 0.36, 0.5, 0.36, YELLOW), K(0.0, 1.55, -0.6, 0.3, 0.42, 0.3, YELLOW),
    S(0.0, 0.7, 0.4, 0.95, 0.9, 0.7, "#a8e070"),
], speed=0.95, tags=["plush"])

kind("board_games", "Stack of board games", (2.2, 1.4, 1.6), 50, [
    B(0.0, 0.0, 0.0, 2.1, 0.42, 1.5, BLUE, dec=sign_decal("SNAKES", BLUE, YELLOW, 2.5)),
    B(0.05, 0.42, -0.02, 2.0, 0.4, 1.44, RED, dec=sign_decal("CASTLES", RED, WHITE, 2.5)),
    B(-0.06, 0.82, 0.03, 1.9, 0.38, 1.38, GREEN, dec=sign_decal("BLOCKOPOLY", GREEN, WHITE, 2.5)),
], speed=1.08, tags=["box"])

kind("toy_car", "Pedal car", (1.7, 1.7, 2.8), 70, [
    S(-0.7, 0.0, 0.85, 0.26, 0.6, 0.6, BLACK), S(0.7, 0.0, 0.85, 0.26, 0.6, 0.6, BLACK),
    S(-0.7, 0.0, -0.85, 0.26, 0.6, 0.6, BLACK), S(0.7, 0.0, -0.85, 0.26, 0.6, 0.6, BLACK),
    R(0.0, 0.3, 0.0, 1.3, 0.7, 2.7, RED),
    B(0.0, 1.0, -0.5, 1.0, 0.1, 0.9, BLACK),
    B(0.0, 1.0, 0.65, 1.2, 0.5, 0.9, RED),
    B(0.0, 1.5, 0.3, 1.1, 0.12, 0.08, "#8ad8ff", m="glass"),
    C(0.0, 1.0, 0.1, 0.5, 0.06, 0.5, BLACK),
    B(-0.4, 0.7, 1.36, 0.3, 0.2, 0.04, YELLOW, m="neon"),
    B(0.4, 0.7, 1.36, 0.3, 0.2, 0.04, YELLOW, m="neon"),
], tags=["box"])

kind("ball_pit_ball", "Big ball", (1.6, 1.6, 1.6), 40, [
    S(0.0, 0.0, 0.0, 1.6, 1.6, 1.6, PINK),
], speed=1.12, tags=["ball"])

kind("xylophone", "Xylophone", (2.4, 1.4, 1.4), 50, [
    B(-0.9, 0.0, 0.0, 0.2, 0.7, 1.3, WOOD), B(0.9, 0.0, 0.0, 0.2, 0.7, 1.3, WOOD),
    B(0.0, 0.7, 0.0, 2.3, 0.12, 1.3, WOOD_LIGHT),
    B(-0.84, 0.82, 0.0, 0.26, 0.16, 1.2, RED), B(-0.5, 0.82, 0.0, 0.26, 0.16, 1.1, ORANGE),
    B(-0.17, 0.82, 0.0, 0.26, 0.16, 1.0, YELLOW), B(0.17, 0.82, 0.0, 0.26, 0.16, 0.9, GREEN),
    B(0.5, 0.82, 0.0, 0.26, 0.16, 0.8, BLUE), B(0.84, 0.82, 0.0, 0.26, 0.16, 0.7, PURPLE),
    S(0.3, 1.0, 0.3, 0.3, 0.3, 0.3, RED),
], speed=1.06, tags=["box"])


# ============================================================== megamart
kind("cereal_box", "Cereal box", (1.4, 2.1, 0.7), 30, [
    B(0.0, 0.0, 0.0, 1.4, 2.0, 0.6, ORANGE, dec=sign_decal("CRUNCH O's", ORANGE, "#5a2a0a", 0.7)),
    B(0.0, 2.0, 0.0, 1.3, 0.08, 0.5, "#d8701a"),
], speed=1.12, tags=["shelf", "food"])

kind("watermelon", "Watermelon", (1.7, 1.3, 2.1), 40, [
    S(0.0, 0.0, 0.0, 1.6, 1.3, 2.1, "#2a7a2a", dec="jl_melon", wrap=True),
], speed=1.08, tags=["food", "produce"])

kind("pumpkin", "Pumpkin", (1.9, 1.8, 1.9), 50, [
    M("pumpkin", 0.0, 0.0, 0.0, 1.9, 1.5, 1.9, ORANGE),
    C(0.0, 1.45, 0.0, 0.2, 0.35, 0.2, "#4a6a2a"),
], speed=1.05, tags=["food", "produce"])

kind("trolley", "Shopping trolley", (2.0, 3.2, 3.4), 80, [
    S(-0.7, 0.0, 1.2, 0.12, 0.36, 0.36, BLACK), S(0.7, 0.0, 1.2, 0.12, 0.36, 0.36, BLACK),
    S(-0.7, 0.0, -1.2, 0.12, 0.36, 0.36, BLACK), S(0.7, 0.0, -1.2, 0.12, 0.36, 0.36, BLACK),
    B(0.0, 0.36, 0.0, 1.6, 0.12, 2.6, SILVER, m="metal"),
    B(-0.7, 0.48, 1.2, 0.1, 1.1, 0.1, SILVER, m="metal"), B(0.7, 0.48, 1.2, 0.1, 1.1, 0.1, SILVER, m="metal"),
    B(-0.7, 0.48, -1.2, 0.1, 1.1, 0.1, SILVER, m="metal"), B(0.7, 0.48, -1.2, 0.1, 1.1, 0.1, SILVER, m="metal"),
    B(0.0, 1.58, 0.15, 1.9, 1.3, 2.9, "#c8ccd0", m="metal", dec="netting"),
    B(0.0, 2.88, -1.35, 1.9, 0.12, 0.12, RED),
    B(-0.85, 2.9, -1.0, 0.1, 0.08, 0.6, SILVER, m="metal"), B(0.85, 2.9, -1.0, 0.1, 0.08, 0.6, SILVER, m="metal"),
], speed=0.92, tags=["floor"])

kind("soda_bottle", "Giant soda", (0.9, 2.6, 0.9), 30, [
    C(0.0, 0.0, 0.0, 0.85, 1.6, 0.85, "#c82a2a", dec="cola", wrap=True),
    K(0.0, 1.6, 0.0, 0.84, 0.6, 0.84, "#c82a2a"),
    C(0.0, 2.2, 0.0, 0.3, 0.26, 0.3, "#c82a2a"),
    C(0.0, 2.46, 0.0, 0.34, 0.14, 0.34, WHITE),
], speed=1.12, tags=["shelf", "food"])

kind("flour_sack", "Sack of flour", (1.6, 2.0, 1.1), 40, [
    R(0.0, 0.0, 0.0, 1.5, 1.6, 1.0, "#e8dcc0", dec=sign_decal("FLOUR", "#e8dcc0", "#6a4a2a", 1.5)),
    R(0.0, 1.6, 0.0, 0.9, 0.4, 0.6, "#d8ccb0"),
], speed=1.06, tags=["food"])

kind("paint_can", "Paint can", (1.3, 1.6, 1.3), 30, [
    C(0.0, 0.0, 0.0, 1.2, 1.3, 1.2, SILVER, m="metal"),
    C(0.0, 0.3, 0.0, 1.24, 0.7, 1.24, "#3a8ad8", dec=sign_decal("SKY BLUE", "#3a8ad8", WHITE, 1.4)),
    C(0.0, 1.3, 0.0, 1.0, 0.1, 1.0, "#3a8ad8"),
    B(0.0, 1.4, 0.0, 1.0, 0.08, 0.08, IRON),
], speed=1.1, tags=["shelf"])

kind("traffic_cone", "Traffic cone", (1.5, 2.3, 1.5), 40, [
    B(0.0, 0.0, 0.0, 1.5, 0.2, 1.5, ORANGE),
    K(0.0, 0.2, 0.0, 1.2, 2.1, 1.2, ORANGE),
    C(0.0, 0.9, 0.0, 0.84, 0.3, 0.84, WHITE),
], speed=1.1, tags=["floor"])

kind("bin", "Bin", (1.7, 2.8, 1.7), 60, [
    C(0.0, 0.0, 0.0, 1.6, 2.4, 1.6, "#2a6a4a"),
    C(0.0, 2.4, 0.0, 1.7, 0.3, 1.7, "#1a5a3a"),
    B(0.0, 1.0, 0.72, 0.6, 0.6, 0.06, WHITE, dec=sign_decal("RECYCLE", WHITE, "#2a6a4a", 1.0)),
], tags=["floor"])

kind("toilet_rolls", "Pack of toilet rolls", (1.9, 1.9, 1.9), 40, [
    B(0.0, 0.0, 0.0, 1.8, 1.8, 1.8, "#e8f0f8", dec=sign_decal("SOFT 24", "#e8f0f8", "#3a6ab0", 1.0)),
    C(-0.45, 1.8, -0.45, 0.8, 0.06, 0.8, WHITE), C(0.45, 1.8, -0.45, 0.8, 0.06, 0.8, WHITE),
    C(-0.45, 1.8, 0.45, 0.8, 0.06, 0.8, WHITE), C(0.45, 1.8, 0.45, 0.8, 0.06, 0.8, WHITE),
], speed=1.05, tags=["shelf"])

kind("fire_extinguisher", "Fire extinguisher", (0.9, 2.3, 0.9), 40, [
    C(0.0, 0.0, 0.0, 0.8, 1.7, 0.8, RED, m="metal"),
    S(0.0, 1.5, 0.0, 0.8, 0.45, 0.8, RED, m="metal"),
    C(0.0, 1.85, 0.0, 0.24, 0.2, 0.24, BLACK),
    B(0.0, 2.05, 0.0, 0.5, 0.1, 0.16, BLACK),
    B(0.0, 0.7, 0.4, 0.5, 0.5, 0.06, WHITE, dec=sign_decal("FIRE", WHITE, RED, 1.0)),
], speed=1.12, tags=["floor"])

kind("wet_floor", "Wet floor sign", (1.5, 2.5, 1.2), 40, [
    B(0.0, 0.0, 0.2, 1.4, 2.3, 0.14, YELLOW, dec=sign_decal("CAUTION WET FLOOR", YELLOW, BLACK, 0.6)),
    B(0.0, 0.0, -0.3, 1.4, 2.3, 0.14, YELLOW),
    B(0.0, 2.3, -0.05, 1.0, 0.18, 0.36, YELLOW),
], speed=1.08, tags=["floor"])

kind("basket", "Shopping basket", (1.8, 1.8, 1.3), 30, [
    B(0.0, 0.0, 0.0, 1.7, 1.0, 1.2, RED, dec="netting"),
    B(-0.5, 1.0, 0.0, 0.1, 0.7, 0.1, BLACK), B(0.5, 1.0, 0.0, 0.1, 0.7, 0.1, BLACK),
    B(0.0, 1.62, 0.0, 1.14, 0.1, 0.08, BLACK),
    S(-0.3, 0.75, 0.0, 0.6, 0.55, 0.6, "#e04040"),
    S(0.32, 0.8, 0.1, 0.5, 0.45, 0.5, YELLOW),
], speed=1.1, tags=["floor"])

kind("water_cooler", "Water cooler", (1.5, 4.4, 1.5), 60, [
    B(0.0, 0.0, 0.0, 1.4, 2.8, 1.4, WHITE),
    B(0.0, 1.8, 0.72, 0.5, 0.2, 0.06, "#3a8ad8"),
    B(0.0, 1.4, 0.71, 0.8, 0.12, 0.08, "#a8acb0"),
    C(0.0, 2.8, 0.0, 1.2, 1.4, 1.2, "#8ac8f0", m="glass"),
    C(0.0, 4.2, 0.0, 0.5, 0.2, 0.5, "#6aa8d8", m="glass"),
], tags=["tall"])

kind("box_pallet", "Pallet of boxes", (3.0, 2.9, 3.0), 100, [
    B(-1.2, 0.0, 0.0, 0.5, 0.4, 3.0, WOOD_LIGHT), B(1.2, 0.0, 0.0, 0.5, 0.4, 3.0, WOOD_LIGHT),
    B(0.0, 0.0, 0.0, 0.5, 0.4, 3.0, WOOD_LIGHT),
    B(0.0, 0.4, 0.0, 3.0, 0.1, 3.0, WOOD),
    B(-0.72, 0.5, -0.72, 1.4, 1.2, 1.4, "#c8a070", dec="crate_logo"),
    B(0.72, 0.5, -0.72, 1.4, 1.2, 1.4, "#c8a070"),
    B(-0.72, 0.5, 0.72, 1.4, 1.2, 1.4, "#c8a070"),
    B(0.72, 0.5, 0.72, 1.4, 1.2, 1.4, "#c8a070", dec="crate_logo"),
    B(-0.35, 1.7, 0.0, 1.4, 1.2, 2.1, "#b89060"),
], speed=0.86, tags=["floor"])

kind("cash_register", "Till", (1.7, 1.5, 1.4), 50, [
    B(0.0, 0.0, 0.0, 1.6, 0.6, 1.3, "#5a5e66", m="metal"),
    B(0.0, 0.6, -0.15, 1.4, 0.5, 0.9, "#3a3e44", m="metal"),
    B(0.0, 0.62, 0.45, 1.2, 0.08, 0.4, "#a8acb0", dec="keys"),
    B(0.0, 1.1, -0.3, 0.9, 0.36, 0.1, "#2a3a2a", dec=sign_decal("$9.99", "#1a2a1a", "#7aff8a", 2.5)),
], speed=1.08, tags=["table"])

kind("cheese_wheel", "Cheese wheel", (1.8, 1.1, 1.8), 40, [
    C(0.0, 0.0, 0.0, 1.8, 1.0, 1.8, "#f0c840"),
    C(0.0, 1.0, 0.0, 1.5, 0.06, 1.5, "#e8b830"),
], speed=1.1, tags=["food"])


# ================================================================ museum
kind("marble_bust", "Marble bust", (1.5, 3.6, 1.5), 60, [
    B(0.0, 0.0, 0.0, 1.4, 0.3, 1.4, STONE),
    B(0.0, 0.3, 0.0, 1.0, 1.8, 1.0, MARBLE),
    B(0.0, 2.1, 0.0, 1.3, 0.2, 1.3, STONE),
    S(0.0, 2.3, 0.0, 1.2, 0.6, 0.8, MARBLE),
    S(0.0, 2.7, 0.0, 0.7, 0.85, 0.75, MARBLE),
    B(0.0, 2.95, 0.36, 0.12, 0.26, 0.12, MARBLE),
    B(0.0, 0.9, 0.51, 0.7, 0.3, 0.04, GOLD, dec=sign_decal("AUGUSTUS", GOLD, BLACK, 2.3)),
], tags=["statue"])

kind("urn", "Urn", (1.5, 2.6, 1.5), 50, [
    C(0.0, 0.0, 0.0, 0.8, 0.3, 0.8, BRONZE, m="metal"),
    S(0.0, 0.2, 0.0, 1.5, 1.6, 1.5, BRONZE, m="metal"),
    C(0.0, 1.7, 0.0, 0.6, 0.5, 0.6, BRONZE, m="metal"),
    C(0.0, 2.2, 0.0, 0.9, 0.2, 0.9, GOLD, m="metal"),
], tags=["vase"])

kind("amphora", "Amphora", (1.4, 3.0, 1.4), 50, [
    K(0.0, 0.0, 0.0, 0.5, 0.6, 0.5, TERRACOTTA),
    S(0.0, 0.3, 0.0, 1.3, 1.8, 1.3, TERRACOTTA, dec="sp_knotband", wrap=True),
    C(0.0, 2.0, 0.0, 0.5, 0.7, 0.5, TERRACOTTA),
    C(0.0, 2.7, 0.0, 0.7, 0.2, 0.7, "#a8542e"),
    B(-0.5, 1.8, 0.0, 0.14, 0.8, 0.14, TERRACOTTA), B(0.5, 1.8, 0.0, 0.14, 0.8, 0.14, TERRACOTTA),
    B(0.0, 2.5, 0.0, 1.18, 0.14, 0.12, TERRACOTTA),
], tags=["vase"])

kind("armour", "Suit of armour", (2.0, 6.0, 1.6), 100, [
    B(0.0, 0.0, 0.0, 1.8, 0.3, 1.4, STONE),
    B(-0.32, 0.3, 0.0, 0.5, 2.1, 0.6, SILVER, m="metal"),
    B(0.32, 0.3, 0.0, 0.5, 2.1, 0.6, SILVER, m="metal"),
    B(0.0, 2.4, 0.0, 1.3, 1.7, 0.85, SILVER, m="metal"),
    B(0.0, 2.6, 0.43, 0.8, 1.1, 0.04, "#c8ccd0", m="metal"),
    S(-0.7, 3.6, 0.0, 0.6, 0.5, 0.6, SILVER, m="metal"), S(0.7, 3.6, 0.0, 0.6, 0.5, 0.6, SILVER, m="metal"),
    B(-0.82, 2.3, 0.0, 0.32, 1.3, 0.36, SILVER, m="metal"),
    B(0.82, 2.3, 0.0, 0.32, 1.3, 0.36, SILVER, m="metal"),
    B(0.0, 4.1, 0.0, 0.8, 0.9, 0.8, SILVER, m="metal"),
    B(0.0, 4.45, 0.41, 0.6, 0.12, 0.04, BLACK),
    K(0.0, 5.0, 0.0, 0.5, 0.6, 0.5, SILVER, m="metal"),
    B(0.0, 5.6, 0.0, 0.1, 0.4, 0.5, RED),
    B(0.86, 0.3, 0.38, 0.1, 3.4, 0.1, IRON),
], speed=0.84, tags=["statue", "tall"])

kind("globe", "Globe", (1.9, 3.4, 1.9), 60, [
    C(0.0, 0.0, 0.0, 1.4, 0.2, 1.4, WOOD_DARK),
    C(0.0, 0.2, 0.0, 0.26, 1.3, 0.26, WOOD),
    C(0.0, 1.5, 0.0, 1.0, 0.14, 1.0, BRASS),
    S(0.0, 1.62, 0.0, 1.6, 1.6, 1.6, "#3a6ab0", dec="xm_compass", wrap=True),
    B(0.0, 1.5, -0.85, 0.12, 1.9, 0.12, BRASS),
], tags=["tall"])

kind("stanchion", "Rope post", (0.9, 3.3, 0.9), 40, [
    C(0.0, 0.0, 0.0, 0.9, 0.2, 0.9, GOLD, m="metal"),
    C(0.0, 0.2, 0.0, 0.26, 2.6, 0.26, GOLD, m="metal"),
    S(0.0, 2.8, 0.0, 0.42, 0.42, 0.42, GOLD, m="metal"),
], speed=1.1, tags=["post"])

kind("fern", "Potted fern", (1.9, 3.2, 1.9), 50, [
    C(0.0, 0.0, 0.0, 1.3, 1.3, 1.3, "#e8e4dc"),
    C(0.0, 1.3, 0.0, 1.4, 0.16, 1.4, STONE),
    K(0.0, 1.3, 0.0, 1.9, 1.9, 1.9, LEAF),
    K(0.0, 2.0, 0.0, 1.3, 1.2, 1.3, LEAF_DARK),
], tags=["plant"])

kind("statuette", "Statuette", (1.3, 3.2, 1.3), 50, [
    B(0.0, 0.0, 0.0, 1.2, 1.0, 1.2, "#3a3a40"),
    B(0.0, 1.0, 0.0, 0.8, 0.2, 0.8, GOLD, m="metal"),
    C(0.0, 1.2, 0.0, 0.5, 1.0, 0.4, BRONZE, m="metal"),
    S(0.0, 2.1, 0.0, 0.7, 0.4, 0.5, BRONZE, m="metal"),
    S(0.0, 2.45, 0.0, 0.4, 0.45, 0.4, BRONZE, m="metal"),
    B(0.36, 2.2, 0.0, 0.14, 0.9, 0.14, BRONZE, m="metal"),
], tags=["statue"])

kind("mummy_case", "Mummy case", (2.0, 5.8, 1.5), 100, [
    B(0.0, 0.0, 0.0, 2.0, 0.3, 1.4, SAND),
    R(0.0, 0.3, 0.0, 1.5, 4.6, 1.2, GOLD),
    R(0.0, 0.5, 0.06, 1.3, 3.2, 1.2, LAPIS, dec="sp_scales"),
    R(0.0, 3.7, 0.08, 1.2, 1.4, 1.2, GOLD),
    B(0.0, 4.2, 0.69, 0.7, 0.7, 0.04, "#d8a868"),
    B(0.0, 4.9, 0.0, 1.6, 0.9, 1.0, LAPIS),
    B(0.0, 3.3, 0.66, 0.9, 0.2, 0.04, RED),
], speed=0.84, tags=["tall"])

kind("meteorite", "Meteorite", (2.2, 1.8, 2.0), 80, [
    B(0.0, 0.0, 0.0, 2.1, 0.3, 1.9, "#3a3a40"),
    S(0.0, 0.3, 0.0, 1.9, 1.5, 1.7, "#4a4048", m="metal"),
    S(0.3, 0.9, 0.3, 0.6, 0.5, 0.6, "#ff8a3a", m="neon"),
], speed=0.95, tags=["rock"])

kind("treasure_chest", "Treasure chest", (2.5, 2.2, 1.7), 80, [
    B(0.0, 0.0, 0.0, 2.4, 1.2, 1.6, WOOD_RED, dec="planks"),
    B(0.0, 1.2, 0.0, 2.4, 0.6, 1.6, WOOD_RED),
    B(0.0, 1.8, 0.0, 2.2, 0.3, 1.4, WOOD_RED),
    B(-1.0, 0.02, 0.0, 0.16, 1.8, 1.64, GOLD, m="metal"), B(1.0, 0.02, 0.0, 0.16, 1.8, 1.64, GOLD, m="metal"),
    B(0.0, 0.9, 0.82, 0.4, 0.5, 0.04, GOLD, m="metal"),
    S(-0.3, 1.82, 0.0, 0.5, 0.36, 0.5, GOLD, m="metal"), S(0.35, 1.82, 0.1, 0.42, 0.3, 0.42, GOLD, m="metal"),
], speed=0.92, tags=["box"])

kind("canopic_jar", "Canopic jar", (1.0, 1.9, 1.0), 30, [
    C(0.0, 0.0, 0.0, 0.9, 1.2, 0.9, "#e8dcc0"),
    C(0.0, 0.3, 0.0, 0.94, 0.5, 0.94, LAPIS, dec="sp_ogham"),
    S(0.0, 1.15, 0.0, 0.8, 0.75, 0.8, GOLD),
], speed=1.12, tags=["vase", "small"])

kind("dino_egg", "Dinosaur egg", (1.5, 2.2, 1.5), 50, [
    C(0.0, 0.0, 0.0, 1.4, 0.3, 1.4, "#3a3a40"),
    M("egg", 0.0, 0.3, 0.0, 1.3, 1.85, 1.3, "#d8c8a0", dec="ea24_speckle"),
], speed=1.05, tags=["rock"])

kind("totem", "Totem pole", (1.7, 5.6, 1.6), 100, [
    B(0.0, 0.0, 0.0, 1.4, 1.6, 1.4, WOOD_RED),
    B(0.0, 0.7, 0.72, 1.0, 0.5, 0.04, "#2a8a7a"),
    B(0.0, 1.6, 0.0, 1.4, 1.6, 1.4, WOOD),
    B(0.0, 2.2, 0.72, 0.8, 0.6, 0.04, YELLOW),
    B(0.0, 3.2, 0.0, 1.4, 1.6, 1.4, WOOD_RED),
    B(0.0, 3.8, 0.72, 0.9, 0.5, 0.04, "#2a8a7a"),
    B(0.0, 4.8, 0.0, 1.7, 0.4, 1.0, "#2a8a7a"),
    B(0.0, 5.2, 0.0, 1.0, 0.4, 0.9, WOOD),
], speed=0.86, tags=["tall", "statue"])

kind("ammonite", "Fossil", (1.9, 2.4, 1.0), 50, [
    B(0.0, 0.0, 0.0, 1.6, 0.4, 0.9, "#3a3a40"),
    S(0.0, 0.4, 0.0, 1.8, 1.9, 0.5, "#c8b090", dec="sp_snail"),
], speed=1.0, tags=["rock"])

kind("museum_bench", "Bench", (3.6, 1.6, 1.4), 80, [
    B(-1.5, 0.0, 0.0, 0.3, 1.0, 1.2, IRON), B(1.5, 0.0, 0.0, 0.3, 1.0, 1.2, IRON),
    B(0.0, 1.0, 0.0, 3.6, 0.3, 1.4, "#5a3a22"),
    R(0.0, 1.3, 0.0, 3.3, 0.3, 1.2, "#7a2a2a"),
], speed=0.9, tags=["sit"])

kind("vase", "Ming vase", (1.3, 2.4, 1.3), 40, [
    C(0.0, 0.0, 0.0, 0.7, 0.2, 0.7, WHITE),
    S(0.0, 0.1, 0.0, 1.3, 1.5, 1.3, WHITE, dec="sp26_quarters", wrap=True),
    C(0.0, 1.5, 0.0, 0.5, 0.7, 0.5, "#2a5ab0"),
    C(0.0, 2.2, 0.0, 0.7, 0.2, 0.7, WHITE),
], speed=1.08, tags=["vase", "small"])


# ======================================================== using the kinds
def hull(key: str, quarter: int = 0) -> List[float]:
    """A kind's size, turned by ``quarter`` quarter turns."""
    w, h, d = KINDS[key]["size"]
    return [d, h, w] if quarter % 2 else [w, h, d]


def turned(part: Part, x: float, y: float, z: float, quarter: int) -> Part:
    """One of a kind's parts placed at (x, y, z) and turned ``quarter``
    quarter turns about the vertical."""
    q = quarter % 4
    yaw = q * math.pi / 2.0
    lx, ly, lz = part["p"]
    c, s = round(math.cos(yaw)), round(math.sin(yaw))
    out = dict(part)
    out["p"] = [round(x + lx * c + lz * s, 3), round(y + ly, 3), round(z - lx * s + lz * c, 3)]
    total = (q + int(part.get("turn", 0))) % 4
    out.pop("turn", None)
    if total:
        out["r"] = [0.0, round(total * math.pi / 2.0, 4), 0.0]
    else:
        out.pop("r", None)
    return out


def stamp(b, parts: Sequence[Part], x: float, z: float, y: float = 0.0,
          quarter: int = 0) -> None:
    """Build ``parts`` (drawn in a local frame like a kind's) into area
    ``b`` at (x, y, z), turned ``quarter`` quarter turns."""
    for part in parts:
        placed = turned(part, x, y, z, quarter)
        made = b.add(placed["t"], placed["p"], placed["s"], placed["c"], r=placed.get("r"),
                     material=placed.get("m", ""), decal=placed.get("dec", ""),
                     collide=not placed.get("ghost"), alpha=placed.get("a", 1.0))
        if placed.get("dw"):
            made["dw"] = 1


def place(b, key: str, x: float, z: float, y: float = 0.0, quarter: int = 0,
          hide: bool = True) -> None:
    """Stand a ``key`` at (x, y, z) in area ``b``, facing quarter turn
    ``quarter`` (0 faces +z).  It is solid; ``hide`` puts it on the list of
    things a hider may turn into (and a hunter may mistake for one)."""
    entry = KINDS[key]
    for part in entry["parts"]:
        placed = turned(part, x, y, z, quarter)
        made = b.add(placed["t"], placed["p"], placed["s"], placed["c"], r=placed.get("r"),
                     material=placed.get("m", ""), decal=placed.get("dec", ""), collide=True)
        if placed.get("dw"):
            made["dw"] = 1
    if hide:
        b.extra.setdefault("decor", []).append(
            {"k": key, "p": b.at(x, y, z), "q": quarter % 4})


def payload(keys: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """The kinds an area uses, as the client needs them to draw disguises."""
    return {k: {"name": KINDS[k]["name"], "size": KINDS[k]["size"], "hp": KINDS[k]["hp"],
                "speed": KINDS[k]["speed"], "parts": KINDS[k]["parts"]}
            for k in sorted(set(keys))}


def finish(b, starter: Optional[str] = None) -> None:
    """Close an area's prop list: the kinds it uses (every disguise in it)
    and the one a hider starts as if they never pick (``starter``)."""
    decor = b.extra.get("decor") or []
    keys = [d["k"] for d in decor]
    b.extra["props"] = payload(keys)
    b.extra["starter"] = starter or (keys[0] if keys else "")
