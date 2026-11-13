"""Mazda 3 (2012 facelift, BL2) front, body color blue.

Traced from the owner's straight-on photo (640x480 px). Coordinates below are
photo pixels, converted to mm with S so the car face is ~62.5 mm wide.
Logo is left as a blank badge (black, 0.3 below the surface).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from keychain.parts import (BASE_TOP, SURFACE, BADGE_RECESS, circle, keyring_tab, layer, mirror)  # noqa: E402

S = 62.5 / 547.0
CX, BOT = 318.0, 410.0


def P(pts):
    return [[(x - CX) * S, (BOT - y) * S] for x, y in pts]


def sym(half):
    """Left-half outline (px, going from bottom center up to top center) -> full loop."""
    left = P(half)
    right = [[-x, y] for x, y in reversed(left)]
    return left + right[1:-1] if False else left + right


def pair(half_pts):
    """Return (left, right) mm polygons from a left-side px polygon."""
    l = P(half_pts)
    return l, mirror(l)


def ell(cx, cy, rx, ry, n=48):
    return P([(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)])


def spec():
    # --- silhouette (left half bottom-center -> top-center, px) ---
    half = [(318, 410), (200, 408), (110, 403), (72, 393), (54, 372), (46, 322), (49, 272),
            (58, 222), (76, 186), (110, 160), (170, 150), (240, 146), (318, 144)]
    L = P(half)
    outline = L + [[-x, y] for x, y in reversed(L)][1:-1]
    # fix winding start: L goes bottom->top on the left, mirror returns top->bottom on right
    outline = outline[::-1] if False else outline

    # keyring tab: hole 3.3 mm outside the body edge at ~53% of the height
    hy = (BOT - 269) * S
    edge_x = (46 - CX) * S
    hole_x = edge_x - 3.3
    tab, tab_hole = keyring_tab(hole_x, hy, (62 - CX) * S)

    # --- see-through holes ---
    eyeL = ell(118, 221, 8.2, 8.2)  # ~Ø3.1 mm
    eyeR = mirror(eyeL)
    slits = []
    for y in (338, 352, 366):  # lower-grille slits ~0.9 mm tall
        x0, x1 = 232, 404
        a = P([(x0, y - 4), (x1, y - 4), (x1, y + 4), (x0, y + 4)])
        slits.append(a)
    thru = [eyeL, eyeR] + slits

    # --- housings / pockets ---
    hl, hr = pair([(74, 205), (88, 193), (125, 189), (160, 220), (172, 256), (135, 246), (95, 240), (70, 230)])
    fogL, fogR = pair([(62, 288), (98, 293), (112, 345), (82, 364), (62, 352)])
    grille = P([(150, 278), (486, 278), (492, 292), (418, 378), (390, 382), (246, 382), (218, 378), (144, 292)])
    lip = P([(135, 393), (501, 393), (494, 402), (142, 402)])
    badge = ell(318, 248, 20, 12)

    ringL, ringR = ell(118, 221, 17, 17), ell(518, 221, 17, 17)
    ringR = mirror(ringL)
    indL, indR = pair([(78, 208), (88, 200), (97, 204), (97, 230), (78, 226)])

    hood = P([(205, 228), (431, 228), (440, 200), (400, 168), (236, 168), (196, 200)])
    band = P([(150, 262), (486, 262), (486, 278), (150, 278)])

    layers = [
        layer("Backing", "black", 0, BASE_TOP, outline, holes=thru),
        layer("Keyring tab", "black", 0, SURFACE, tab, holes=[tab_hole]),
        layer("Body", "body_blue", BASE_TOP, SURFACE, outline, holes=[hl, hr, fogL, fogR, grille, lip, badge]),
        layer("Hood", "body_blue", BASE_TOP, 3.2, hood),
        layer("Bumper crease", "body_blue", BASE_TOP, 3.4, band),
        layer("Headlight housing L", "black", 0, 2.5, hl, holes=[eyeL]),
        layer("Headlight housing R", "black", 0, 2.5, hr, holes=[eyeR]),
        layer("Fog vent L", "black", 0, 2.0, fogL),
        layer("Fog vent R", "black", 0, 2.0, fogR),
        layer("Grille", "black", 0, 2.0, grille, holes=slits),
        layer("Lower lip", "black", 0, 3.4, lip),
        layer("Headlamp projector L", "white", 2.5, SURFACE, ringL, holes=[eyeL]),
        layer("Headlamp projector R", "white", 2.5, SURFACE, ringR, holes=[eyeR]),
        layer("Indicator L", "orange", 2.5, SURFACE, indL),
        layer("Indicator R", "orange", 2.5, SURFACE, indR),
        layer("Blank logo badge", "black", 0, SURFACE - BADGE_RECESS, badge),
    ]
    colors = {"black": [0.02, 0.02, 0.02], "body_blue": [0.2, 0.36, 0.55],
              "white": [0.961, 0.961, 0.961], "orange": [0.867, 0.486, 0.059]}
    return {"name": "mazda3_2012", "colors": colors, "layers": layers}
