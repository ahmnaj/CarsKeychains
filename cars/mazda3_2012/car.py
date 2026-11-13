"""Mazda 3 (2012 facelift, BL) front, body color blue.

Traced from the owner's straight-on photo (640x480 px, izmocars). Coordinates
below are photo pixels: the silhouette comes from a scan of the white
background, details from zoomed grids. The car is symmetric about x=318 px and
550 px wide, scaled to a 62.5 mm face. Keychain runs from the hood (cut above
the headlights) down to the bottom of the bumper; wheels, mirrors and the
windscreen are left off as on the other cars.

Logo is left as a blank badge (black, 0.3 below the surface).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from keychain.parts import (BADGE_RECESS, BASE_TOP, RING_HOLE_R, RING_NECK_FILLET, RING_TAB_R,
                            SURFACE, circle, layer)  # noqa: E402

CX, BOT = 318.0, 403.0          # symmetry axis and bumper bottom (px)
S = 62.5 / 550.0                # mm per photo pixel


def mm(pts):
    return [[(x - CX) * S, (BOT - y) * S] for x, y in pts]


def flip(pts):
    """Mirror px points to the right side of the car (reversed to keep winding)."""
    return [(2 * CX - x, y) for x, y in reversed(pts)]


def sym(path):
    """Symmetric outline from its left half: a px path that starts and ends on x=CX."""
    right = flip(path)
    return mm(path + right[1:-1])


def pair(pts):
    return mm(pts), mm(flip(pts))


def arc(cx, cy, r, a0, a1, n=12):
    """Points on a circle in photo coordinates (y down), angles in degrees."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def circ(cx, cy, r, n=48):
    return arc(cx, cy, r, 0, 360 * (n - 1) / n, n - 1)


# --- traced shapes (left side, photo px) -------------------------------------

SILHOUETTE = [(318, 403), (54, 403), (47, 400), (44, 394), (43, 380), (42, 300), (43, 250),
              (44, 232), (46, 220), (49, 208), (52, 198), (56, 190), (60, 183), (65, 176),
              (71, 170), (80, 166), (100, 164.5), (200, 166), (318, 167)]

# headlight: upper edge is also the lower edge of the hood
HL_TOP = [(61, 187.5), (65, 186.7), (80, 186), (90, 187.5), (100, 190), (110, 192.5),
          (120, 197.5), (130, 204), (140, 211), (148, 218)]
HL_REST = [(157, 228), (167, 240), (173, 250), (178, 260), (172, 260), (163, 255),
           (148, 252.5), (132, 250), (115, 247.5), (98, 245), (85, 241.7), (73, 235),
           (67, 227), (63, 215), (62, 202)]
EYE = (107.5, 221.0)

# hood shut line from the headlight to the middle
SHUT_LINE = [(160, 215.5), (190, 213), (230, 212), (318, 211)]

# bumper: the crease between fog vent and grille, offset to leave a 0.57 mm body strip
CREASE = [(137, 288), (141, 298), (145, 307), (152, 325), (161, 340), (170, 352)]
FOG_BOTTOM = [(172, 360), (150, 357), (112, 353), (110, 361), (80, 364), (60, 366)]
GRILLE_TOP = [(318, 276), (270, 275), (195, 273.5), (145, 271)]
GRILLE_BOTTOM = [(182, 363), (195, 366), (220, 370), (245, 372.5), (270, 375), (295, 377), (318, 378)]
CHIN_BOTTOM = [(318, 386), (250, 384.5), (200, 383), (130, 380), (80, 377), (62, 375), (57, 371)]


def ring_tab(side_x, hy, offset=3.6):
    """Keyring tab on the left with R4 end and R3.5 fillets into the body side."""
    r, f, hx = RING_TAB_R, RING_NECK_FILLET, side_x - offset
    pts = [[side_x + 1.5, hy + r + f]]
    pts += [[side_x - f + f * math.cos(math.radians(-a)), hy + r + f + f * math.sin(math.radians(-a))]
            for a in range(0, 91, 10)]
    pts += [[hx + r * math.cos(math.radians(a)), hy + r * math.sin(math.radians(a))] for a in range(90, 271, 6)]
    pts += [[side_x - f + f * math.cos(math.radians(a)), hy - r - f + f * math.sin(math.radians(a))]
            for a in range(90, -1, -10)]
    pts += [[side_x + 1.5, hy - r - f]]
    return pts, circle(hx, hy, RING_HOLE_R)


def spec():
    outline = sym(SILHOUETTE)

    # keyring tab: hole 3.6 mm outside the straight side, at 53% of the height
    top = min(y for _, y in SILHOUETTE)
    tab, tab_hole = ring_tab((42.5 - CX) * S, 0.53 * (BOT - top) * S)

    hood = sym(SILHOUETTE[-1:-8:-1] + [(58.5, 186)] + HL_TOP + SHUT_LINE)

    hl_px = HL_TOP + HL_REST
    hl_l, hl_r = pair(hl_px)
    eye_l, eye_r = pair(circ(*EYE, 11.5))           # see-through, ~2.6 mm
    ring_l, ring_r = pair(circ(*EYE, 17))           # projector chrome ring
    amber_px = [(66, 192), (80, 190), (93, 192)] + arc(*EYE, 19.5, 240, 125) + \
               [(88, 240), (76, 233.5), (70, 225.5), (66.5, 214), (65.5, 200)]
    amber_l, amber_r = pair(amber_px)
    refl_px = arc(*EYE, 19.5, -70, 70) + [(128, 246.5), (148, 249), (163, 251.5), (170, 254.5),
                                          (167, 247), (160, 236), (152, 226), (144, 218),
                                          (136, 211.5), (127, 206), (118, 201)]
    refl_l, refl_r = pair(refl_px)

    # honeycomb fog vent; the lit panel between it and the grille crease is body color
    fog_px = [(62, 283), (65, 279), (70, 277), (77, 276), (90, 280), (99, 286), (104, 296),
              (107, 320), (109, 345), (110, 361), (80, 364), (60, 366), (61, 356)]
    fog_l, fog_r = pair(fog_px)

    grille = sym(GRILLE_TOP + [(140, 272.5), (139.5, 278)] +
                 [(x + 2.5, y) for x, y in CREASE] + [(176, 358)] + GRILLE_BOTTOM)
    lip = sym([(318, 270), (200, 267.5), (146, 266), (140, 268), (140, 272.5)] + GRILLE_TOP[::-1])
    chin = sym(GRILLE_BOTTOM[::-1] + [(177, 361.5)] + FOG_BOTTOM + [(57, 368)] + CHIN_BOTTOM[::-1])
    valance = sym(CHIN_BOTTOM + [(56, 378), (56, 403), (318, 403)])
    badge = mm([(318 + 24.5 * math.cos(2 * math.pi * i / 64), 247 + 15 * math.sin(2 * math.pi * i / 64))
                for i in range(64)])                # 5.6 x 3.4 mm oval

    pockets = [hl_l, hl_r, fog_l, fog_r, grille, badge]
    layers = [
        layer("Backing", "black", 0, BASE_TOP, outline, holes=[eye_l, eye_r]),
        layer("Keyring tab", "black", 0, SURFACE, tab, holes=[tab_hole]),
        layer("Body", "body_blue", BASE_TOP, SURFACE, outline, holes=pockets),
        layer("Hood", "body_blue", BASE_TOP, 3.2, hood),
        layer("Bumper lip over grille", "body_blue", BASE_TOP, 3.2, lip),
        layer("Chin", "body_blue", BASE_TOP, 3.4, chin),
        layer("Headlight housing L", "black", 0, 2.5, hl_l, holes=[eye_l]),
        layer("Headlight housing R", "black", 0, 2.5, hl_r, holes=[eye_r]),
        layer("Fog vent L", "black", 0, 2.0, fog_l),
        layer("Fog vent R", "black", 0, 2.0, fog_r),
        layer("Grille", "black", 0, 2.0, grille),
        layer("Lower valance", "black", 0, SURFACE, valance),
        layer("Blank logo badge", "black", 0, SURFACE - BADGE_RECESS, badge),
        layer("Projector ring L", "white", 2.5, SURFACE, ring_l, holes=[eye_l]),
        layer("Projector ring R", "white", 2.5, SURFACE, ring_r, holes=[eye_r]),
        layer("Reflector L", "white", 2.5, SURFACE, refl_l),
        layer("Reflector R", "white", 2.5, SURFACE, refl_r),
        layer("Indicator L", "orange", 2.5, SURFACE, amber_l),
        layer("Indicator R", "orange", 2.5, SURFACE, amber_r),
    ]
    colors = {"black": [0.02, 0.02, 0.02], "body_blue": [0.2, 0.36, 0.55],
              "white": [0.961, 0.961, 0.961], "orange": [0.867, 0.486, 0.059]}
    return {"name": "mazda3_2012", "colors": colors, "layers": layers}
