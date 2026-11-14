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
from keychain.parts import BADGE_RECESS, BASE_TOP, SURFACE, keyring_tab_ref, layer  # noqa: E402

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
SHUT_LINE = [(151, 218), (170, 217), (200, 216), (235, 215), (270, 214), (318, 213)]

# bumper: the crease between the lit panel beside the fog vent and the grille
CREASE = [(137, 288), (141, 298), (145, 307), (152, 325), (161, 340), (170, 352)]
FOG_BOTTOM = [(172, 360), (150, 357), (112, 353), (110, 361), (80, 364), (60, 366)]
GRILLE_TOP = [(318, 276), (270, 275), (195, 273.5), (145, 271)]
GRILLE_BOTTOM = [(182, 363), (195, 366), (220, 370), (245, 372.5), (270, 375), (295, 377), (318, 378)]
CHIN_BOTTOM = [(318, 386.5), (290, 384.5), (250, 383), (200, 384), (180, 387.3), (160, 387),
               (137, 385), (130, 384), (80, 377.5), (64, 375.5), (58, 371)]

# panel lines, located on the darkest pixels of the photo's seams; 0.40 mm grooves
GROOVE_W = 3.5
LINES = {   # each runs through to the silhouette edge or into the headlight housing
    "hood shut line": [(145.5, 219.5)] + SHUT_LINE,
    "hood-fender line": [(79.5, 163), (76.5, 171), (74.5, 173.5), (73.7, 179), (73.2, 188.5)],
    "fender-bumper seam": [(41, 235), (46.5, 231.6), (51, 228.5), (56, 225.8), (60, 224),
                           (64.5, 222.8), (67.5, 222.3)],
}
# lit panel between fog vent and grille: a fold in the bumper, 0.2 mm below the surface
LIT_PANEL = [(99, 285.5), (110, 287.5), (125, 290), (137.5, 292.5)] + CREASE[1:] + \
            [(172, 360), (150, 357), (112, 353), (109, 345), (107, 320), (104, 296)]


def stroke(pts, w=GROOVE_W):
    """Polyline -> thin polygon of width w (px), ends square."""
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        nx, ny = -dy / n * w / 2, dx / n * w / 2
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    return left + right[::-1]


def inside(p, poly):
    x, y, hit = p[0], p[1], False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def clip_half(poly, a, b, keep):
    """Keep the part of poly on the same side of line a-b as point keep."""
    side = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    sk = side(keep)
    out = []
    for p, q in zip(poly, poly[1:] + poly[:1]):
        sp, sq = side(p) * sk, side(q) * sk
        if sp >= 0:
            out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def groove(line, outline_px):
    """Groove polygon along a px polyline, trimmed flush where it runs off the silhouette."""
    poly = stroke(line)
    for end, nxt in ((line[0], line[1]), (line[-1], line[-2])):
        if inside(end, outline_px):
            continue
        # outline segment crossed between the last inside point and the end
        for a, b in zip(outline_px, outline_px[1:] + outline_px[:1]):
            d = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
            e = lambda p: (end[0] - nxt[0]) * (p[1] - nxt[1]) - (end[1] - nxt[1]) * (p[0] - nxt[0])
            if d(end) * d(nxt) < 0 and e(a) * e(b) <= 0:
                poly = clip_half(poly, a, b, nxt)
                break
    return poly


def spec():
    outline = sym(SILHOUETTE)

    # keyring tab as on the reference models, hole at 53% of the height
    top = min(y for _, y in SILHOUETTE)
    tab, tab_hole, tab_fillets = keyring_tab_ref((42.5 - CX) * S, 0.53 * (BOT - top) * S, outline)

    # hood stops at the upper edge of the shut-line groove
    hood = sym(SILHOUETTE[-1:-8:-1] + [(58.5, 186)] + HL_TOP + [(x, y - GROOVE_W / 2) for x, y in SHUT_LINE])

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

    grille = sym(GRILLE_TOP + [(140, 272.5), (137, 278)] + CREASE + [(176, 358)] + GRILLE_BOTTOM)
    # grille details (from the brightened photo): a dark slot along the top, the smooth
    # smile-shaped panel under it, and the open mesh below with the radiator fins showing
    grille_slot = sym([(318, 278.5), (270, 277.5), (195, 276), (146, 274), (142, 276), (141.5, 282),
                       (143, 287.5), (200, 288.5), (318, 290)])
    grille_panel = sym([(318, 290), (200, 288.5), (143, 287.5), (144, 298), (148, 307.5), (160, 313.5),
                        (175, 319.5), (200, 328), (220, 333.5), (258, 336), (318, 337)])
    fins = []                                            # see-through slits between the fins
    for x0, x1, y0, y1 in ((234, 311, 343, 349.5), (234, 311, 354.5, 361), (270, 311, 365.5, 370.5)):
        fins += list(pair([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
    lip = sym([(318, 270), (200, 267.5), (146, 266), (140, 268), (140, 272.5)] + GRILLE_TOP[::-1])
    chin = sym(GRILLE_BOTTOM[::-1] + [(177, 361.5)] + FOG_BOTTOM + [(57, 368)] + CHIN_BOTTOM[::-1])
    # lower bumper is body color; black corner slots (chrome-edged) and a slim centre intake
    slot_px = [(64, 375.5), (80, 377.5), (130, 384), (137, 385), (138.5, 391), (136.5, 397),
               (130, 396.5), (100, 395.5), (80, 394.5), (74, 393), (70, 389), (66.5, 382)]
    slot_l, slot_r = pair(slot_px)
    intake = sym([(318, 386.5), (290, 384.5), (250, 383), (200, 384), (180, 387.3), (186, 393),
                  (200, 395.5), (250, 396.5), (318, 397.5)])
    badge = mm([(318 + 24.5 * math.cos(2 * math.pi * i / 64), 247 + 15 * math.sin(2 * math.pi * i / 64))
                for i in range(64)])                # 5.6 x 3.4 mm oval

    # panel lines: black floor at 2.5 plus a void above it, so every blue layer is cut
    # clean through and the body splits into separate pieces along each line
    outline_px = SILHOUETTE + flip(SILHOUETTE)[1:-1]
    # (the floor is trimmed flush with the silhouette; the gap may overrun it)
    grooves, gaps = [], []
    for name, line in LINES.items():
        if line[-1][0] == CX:   # runs to the centre: one line across the car
            lines = [(name, line + flip(line)[1:])]
        else:
            lines = [(name + " L", line), (name + " R", flip(line)[::-1])]
        for n, ln in lines:
            grooves.append((n, mm(groove(ln, outline_px))))
            gaps.append((n, mm(stroke(ln))))

    lit_l, lit_r = pair(LIT_PANEL)
    pockets = [lit_l, lit_r, hl_l, hl_r, fog_l, fog_r, grille, badge, slot_l, slot_r, intake]
    layers = [
        layer("Backing", "black", 0, BASE_TOP, outline, holes=[eye_l, eye_r]),
        layer("Keyring tab", "black", 0, SURFACE, tab, holes=[tab_hole]),
        *[layer("Keyring tab fillet", "black", 0, BASE_TOP, f) for f in tab_fillets],
        layer("Body", "body_blue", BASE_TOP, SURFACE, outline, holes=pockets),
        layer("Hood", "body_blue", BASE_TOP, 3.2, hood),
        layer("Bumper lip over grille", "body_blue", BASE_TOP, 3.2, lip),
        layer("Chin", "body_blue", BASE_TOP, 3.4, chin),
        layer("Lit panel L", "body_blue", BASE_TOP, 2.8, lit_l),
        layer("Lit panel R", "body_blue", BASE_TOP, 2.8, lit_r),
        layer("Headlight housing L", "black", 0, 2.5, hl_l, holes=[eye_l]),
        layer("Headlight housing R", "black", 0, 2.5, hl_r, holes=[eye_r]),
        layer("Fog vent L", "black", 0, 2.0, fog_l),
        layer("Fog vent R", "black", 0, 2.0, fog_r),
        layer("Grille mesh", "black", 0, 2.0, grille, holes=[grille_slot]),
        layer("Grille panel", "black", 0, 2.6, grille_panel),
        layer("Lower corner slot L", "black", 0, 2.0, slot_l),
        layer("Lower corner slot R", "black", 0, 2.0, slot_r),
        layer("Lower intake", "black", 0, 2.0, intake),
        *[layer(f"Panel line {n}", "black", 0, 2.5, g) for n, g in grooves],
        layer("Blank logo badge", "black", 0, SURFACE - BADGE_RECESS, badge),
        layer("Projector ring L", "white", 2.5, SURFACE, ring_l, holes=[eye_l]),
        layer("Projector ring R", "white", 2.5, SURFACE, ring_r, holes=[eye_r]),
        layer("Reflector L", "white", 2.5, SURFACE, refl_l),
        layer("Reflector R", "white", 2.5, SURFACE, refl_r),
        layer("Indicator L", "orange", 2.5, SURFACE, amber_l),
        layer("Indicator R", "orange", 2.5, SURFACE, amber_r),
        *[layer(f"Panel line {n} (gap)", "void", 2.5, 4.0, g) for n, g in gaps],
        *[layer("Radiator fin slit", "void", 0, 4.0, f) for f in fins],
    ]
    colors = {"black": [0.02, 0.02, 0.02], "body_blue": [0.2, 0.36, 0.55],
              "white": [0.961, 0.961, 0.961], "orange": [0.867, 0.486, 0.059]}
    return {"name": "mazda3_2012", "colors": colors, "layers": layers}
