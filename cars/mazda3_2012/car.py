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

CX, BOT = 318.0, 408.0          # symmetry axis and lowest point of the valance (px)
S = 62.5 / 550.0                # mm per photo pixel


def mm(pts):
    return [[(x - CX) * S, (BOT - y) * S] for x, y in pts]


def flip(pts):
    """Mirror px points to the right side of the car (reversed to keep winding)."""
    return [(2 * CX - x, y) for x, y in reversed(pts)]


class Px(list):
    """A traced polygon still in photo pixels; spec() smooths it and converts it to mm."""


def sym(path):
    """Symmetric outline from its left half: a px path that starts and ends on x=CX."""
    right = flip(path)
    return Px(path + right[1:-1])


def pair(pts):
    return Px(pts), Px(flip(pts))


# --- smoothing ---------------------------------------------------------------
# The traced polygons have a point every few mm, which prints as visible facets. Each edge
# is replaced by a cubic curve that still passes through every traced point, so shapes and
# the silhouette stay where they were traced. A vertex stays a sharp corner when the outline
# turns more than CORNER_DEG there, or when two polygons that share it leave it in different
# directions; everywhere else all polygons sharing an edge get exactly the same curve.
CORNER_DEG = 50.0
SMOOTH_STEP = 2.5        # px between points on a curve (0.28 mm)


def _key(p):
    return (round(p[0], 2), round(p[1], 2))


def _unit(ax, ay):
    n = math.hypot(ax, ay) or 1.0
    return ax / n, ay / n


def vertex_tangents(polys, closed=True):
    """{vertex: tangent line direction} for every vertex that should be smooth."""
    seen = {}
    for poly in polys:
        n = len(poly)
        for i, v in enumerate(poly):
            if not closed and i in (0, n - 1):
                seen.setdefault(_key(v), set()).add(None)
                continue
            a, b = poly[i - 1], poly[(i + 1) % n]
            seen.setdefault(_key(v), set()).add((frozenset((_key(a), _key(b))), a, b))
    out = {}
    for k, uses in seen.items():
        if len({u[0] if u else None for u in uses}) != 1 or None in uses:
            continue                                   # polygons disagree here: keep the corner
        _, a, b = next(iter(uses))
        d1, d2 = _unit(k[0] - a[0], k[1] - a[1]), _unit(b[0] - k[0], b[1] - k[1])
        turn = math.degrees(math.acos(max(-1.0, min(1.0, d1[0] * d2[0] + d1[1] * d2[1]))))
        if turn < CORNER_DEG:
            # direction of the chord between the neighbours (follows the longer edge, so long
            # straight runs stay straight), and the shorter edge length to limit the bulge
            out[k] = _unit(b[0] - a[0], b[1] - a[1]) + (
                min(math.hypot(k[0] - a[0], k[1] - a[1]), math.hypot(b[0] - k[0], b[1] - k[1])),)
    return out


def smooth_path(poly, tangents, closed=True):
    """Replace each edge by a cubic through its end points, using the shared vertex tangents."""
    out = []
    n = len(poly)
    for i in range(n if closed else n - 1):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        length = math.hypot(ex, ey)
        ta, tb = tangents.get(_key(a)), tangents.get(_key(b))
        out.append(a)
        if length < 1e-9 or (ta is None and tb is None):
            continue                                   # straight edge between two corners
        chord = (ex / length, ey / length)
        ends = []
        for tan in (ta, tb):
            if tan is None:
                ends.append((chord[0] * length, chord[1] * length))
                continue
            sign = -1.0 if tan[0] * ex + tan[1] * ey < 0 else 1.0
            mag = min(length, 1.5 * tan[2])
            ends.append((sign * tan[0] * mag, sign * tan[1] * mag))
        (m0x, m0y), (m1x, m1y) = ends
        steps = max(2, int(math.ceil(length / SMOOTH_STEP)))
        for j in range(1, steps):
            u = j / steps
            h00, h10 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u
            h01, h11 = -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
            out.append((h00 * a[0] + h10 * m0x + h01 * b[0] + h11 * m1x,
                        h00 * a[1] + h10 * m0y + h01 * b[1] + h11 * m1y))
    if not closed:
        out.append(poly[-1])
    return out


def smooth_line(line):
    """Smooth an open polyline (a panel line) on its own."""
    return smooth_path(line, vertex_tangents([line], closed=False), closed=False)


def finish(layers):
    """Smooth every traced (Px) polygon in the layers consistently and convert it to mm."""
    polys = {}
    for l in layers:
        for poly in [l["outline"]] + l["holes"]:
            if isinstance(poly, Px):
                polys[id(poly)] = poly
    tangents = vertex_tangents(list(polys.values()))
    done = {k: mm(smooth_path(poly, tangents)) for k, poly in polys.items()}
    for l in layers:
        l["outline"] = done.get(id(l["outline"]), l["outline"])
        l["holes"] = [done.get(id(h), h) for h in l["holes"]]
    return layers


def arc(cx, cy, r, a0, a1, n=12):
    """Points on a circle in photo coordinates (y down), angles in degrees."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def circ(cx, cy, r, n=48):
    return arc(cx, cy, r, 0, 360 * (n - 1) / n, n - 1)


# --- traced shapes (left side, photo px) -------------------------------------

# bottom edge: the black valance wings hang below the bumper corners, centre lip a little higher
SILHOUETTE = [(318, 405), (166, 405), (158, 408), (80, 408), (70, 405.8), (60, 404.8), (52, 402.5),
              (47, 399.5), (44, 394), (43, 380), (42, 300), (43, 250),
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
    for pts in (line, line[::-1]):
        end = pts[0]
        if inside(end, outline_px):
            continue
        nxt = next((q for q in pts if inside(q, outline_px)), None)   # first point inside
        if nxt is None:
            continue
        # outline segment crossed between the last inside point and the end
        for a, b in zip(outline_px, outline_px[1:] + outline_px[:1]):
            d = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
            e = lambda p: (end[0] - nxt[0]) * (p[1] - nxt[1]) - (end[1] - nxt[1]) * (p[0] - nxt[0])
            if d(end) * d(nxt) < 0 and e(a) * e(b) <= 0:
                poly = clip_half(poly, a, b, nxt)
                break
    return poly


def interp(pts, x):
    """Piecewise-linear y(x) through px points sorted by x (clamped at the ends)."""
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


# lower edge of the smooth grille panel (slight V in the middle) and of the grille itself
PANEL_BOTTOM = [(148, 307.5), (160, 313.5), (175, 319.5), (200, 328), (220, 333.5), (258, 336),
                (295, 337), (318, 339)]
MESH_BOTTOM = CREASE + [(176, 358)] + GRILLE_BOTTOM


# gentle smile the mesh rows follow: the grille's lower edge, carried on out to the sides
ROW_CURVE = [(130, 349.5)] + GRILLE_BOTTOM


def edge_dist(p, poly):
    best = 1e9
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / ((dx * dx + dy * dy) or 1e-12)))
        best = min(best, math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy))
    return best


def area(poly):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))) / 2


def honeycomb(region, curve=None, x_mid=CX, a=12.0, t=5.0, h=8.0, wy=2.0, gx=3.1):
    """See-through honeycomb of wide flat hexagons, like the car's grille mesh.

    Cells are 2.5 x 0.9 mm with 0.4 mm webs, interlocked row to row, and are trimmed by
    `region` (px polygon, already inset by the frame width) the way the real mesh is cut
    off by its frame. `curve` bends the rows (px points, left half; mirrored about CX).
    Returns mm polygons.
    """
    w = a + 2 * t
    px_pitch, py_pitch = w + a + 2 * gx, h / 2 + wy
    xs = [q[0] for q in region]
    ys = [q[1] for q in region]
    bend = (lambda x: interp(curve, CX - abs(x - CX)) - curve[-1][1]) if curve else (lambda x: 0.0)
    cells = []
    for r in range(-40, 41):
        for n in range(-12, 13):
            cx = x_mid + (n + (0.5 if r % 2 else 0.0)) * px_pitch
            cy = max(ys) - h / 2 + r * py_pitch
            if not (min(xs) - w < cx < max(xs) + w):
                continue
            hexa = [(cx - w / 2, cy), (cx - a / 2, cy - h / 2), (cx + a / 2, cy - h / 2),
                    (cx + w / 2, cy), (cx + a / 2, cy + h / 2), (cx - a / 2, cy + h / 2)]
            hexa = [(x, y + bend(x)) for x, y in hexa]
            centre = (cx, cy + bend(cx))
            cell = list(region)                  # region clipped by the (convex) hexagon
            for p0, p1 in zip(hexa, hexa[1:] + hexa[:1]):
                cell = clip_half(cell, p0, p1, centre) if cell else cell
            if len(cell) < 3 or area(cell) < 0.3 * area(hexa):
                continue                          # drop slivers too small to print
            cy_s = [q[1] for q in cell]
            cx_s = [q[0] for q in cell]
            if max(cy_s) - min(cy_s) < 3.5 or max(cx_s) - min(cx_s) < 5:
                continue
            cells.append(mm(cell))
    return cells


def shrink(poly, d):
    """Rough inset of a compact polygon: pull every vertex d px towards the centroid."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        n = math.hypot(x - cx, y - cy) or 1.0
        out.append((x - (x - cx) / n * d, y - (y - cy) / n * d))
    return out


def spec():
    outline = sym(SILHOUETTE)

    # keyring tab as on the reference models, hole at 53% of the height
    top = min(y for _, y in SILHOUETTE)
    tab, tab_hole, tab_fillets = keyring_tab_ref((42.5 - CX) * S, 0.53 * (BOT - top) * S, mm(outline))

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
    # grille details: a dark slot along the top, the smooth smile-shaped panel under it,
    # and the honeycomb mesh below (owner's close-up photo of the real car)
    grille_slot = sym([(318, 278.5), (270, 277.5), (195, 276), (146, 274), (142, 276), (141.5, 282),
                       (143, 287.5), (200, 288.5), (318, 290)])
    grille_panel = sym([(318, 290), (200, 288.5), (143, 287.5), (144, 298), (148, 307.5), (160, 313.5),
                        *PANEL_BOTTOM[2:]])
    # honeycomb mesh (see-through cells) below and beside the panel, and in the fog vents
    px_sym = lambda path: path + flip(path)[1:-1]
    # open mesh area of the grille, inset 0.45 mm from the panel above and the frame below
    mesh_area = px_sym([(318, 342.8), (295, 340.8), (258, 339.8), (220, 337.3), (200, 331.8),
                        (175, 323.3), (160, 317.3), (152, 313), (156.5, 325), (165.5, 340),
                        (174.5, 352), (180, 357.5), (182, 359), (195, 362), (220, 366),
                        (245, 368.5), (270, 371), (295, 373), (318, 374)])
    mesh = honeycomb(mesh_area, curve=ROW_CURVE)
    fog_area = shrink(fog_px, 5.0)
    mesh += honeycomb(fog_area, x_mid=86) + honeycomb(flip(fog_area), x_mid=2 * CX - 86)
    lip = sym([(318, 270), (200, 267.5), (146, 266), (140, 268), (140, 272.5)] + GRILLE_TOP[::-1])
    chin = sym(GRILLE_BOTTOM[::-1] + [(177, 361.5)] + FOG_BOTTOM + [(57, 368)] + CHIN_BOTTOM[::-1])
    # lower bumper corners are body color with black slots (chrome-edged on the car)
    slot_px = [(64, 375.5), (80, 377.5), (130, 384), (137, 385), (138.5, 391), (136.5, 397),
               (130, 396.5), (100, 395.5), (80, 394.5), (74, 393), (70, 389), (66.5, 382)]
    slot_l, slot_r = pair(slot_px)
    # under the chin (straight-on photo, brightened): the blue edge swoops up from the
    # bumper corners to the chin and carries on along the bottom as a lip, so the dark
    # valance and intake between them are enclosed by blue; thin black valance wings hang
    # below the bumper corners
    swoop = [(200, 384.5), (192, 387.5), (185, 390.7), (177, 396)]
    lip_top = [(190, 397.5), (212, 397.5), (250, 398), (318, 398.5)]
    valance = sym([(318, 386.5), (290, 384.5), (250, 383)] + swoop + lip_top)
    intake = sym([(318, 386.5), (290, 384.5), (250, 383), (200, 384.5), (192, 387.5), (187.5, 391),
                  (189, 394.5), (195, 397.5), (212, 397.5), (250, 398), (318, 398.5)])
    wing_top = [(160, 404.4), (150, 404.3), (115, 404.5), (80, 405), (66, 405.3)]
    wing_l, wing_r = pair(wing_top + [(70, 405.8), (80, 408), (158, 408), (166, 405)])
    # the blue body stops at the top of the wings (its own outline, so nothing has to be cut)
    body_outline = sym(SILHOUETTE[:2] + wing_top + SILHOUETTE[5:])
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
            ln = smooth_line(ln)
            grooves.append((n, mm(groove(ln, outline_px))))
            gaps.append((n, mm(stroke(ln))))

    lit_l, lit_r = pair(LIT_PANEL)
    pockets = [lit_l, lit_r, hl_l, hl_r, fog_l, fog_r, grille, badge, slot_l, slot_r]
    layers = [
        layer("Backing", "black", 0, BASE_TOP, outline, holes=[eye_l, eye_r]),
        layer("Keyring tab", "black", 0, SURFACE, tab, holes=[tab_hole]),
        *[layer("Keyring tab fillet", "black", 0, BASE_TOP, f) for f in tab_fillets],
        layer("Body", "body_blue", BASE_TOP, SURFACE, body_outline, holes=pockets),
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
        layer("Lower valance", "black", 0, 2.6, valance),
        layer("Valance wing L", "black", 0, 2.6, wing_l),
        layer("Valance wing R", "black", 0, 2.6, wing_r),
        *[layer(f"Panel line {n}", "black", 0, 2.5, g) for n, g in grooves],
        layer("Blank logo badge", "black", 0, SURFACE - BADGE_RECESS, badge),
        layer("Projector ring L", "white", 2.5, SURFACE, ring_l, holes=[eye_l]),
        layer("Projector ring R", "white", 2.5, SURFACE, ring_r, holes=[eye_r]),
        layer("Reflector L", "white", 2.5, SURFACE, refl_l),
        layer("Reflector R", "white", 2.5, SURFACE, refl_r),
        layer("Indicator L", "orange", 2.5, SURFACE, amber_l),
        layer("Indicator R", "orange", 2.5, SURFACE, amber_r),
        *[layer(f"Panel line {n} (gap)", "void", 2.5, 4.0, g) for n, g in gaps],
        *[layer("Mesh cell", "void", 0, 4.0, m) for m in mesh],
        layer("Space over valance", "void", 2.6, 4.0, valance),
        layer("Lower intake", "void", 2.0, 4.0, intake),
    ]
    colors = {"black": [0.02, 0.02, 0.02], "body_blue": [0.2, 0.36, 0.55],
              "white": [0.961, 0.961, 0.961], "orange": [0.867, 0.486, 0.059]}
    return {"name": "mazda3_2012", "colors": colors, "layers": finish(layers)}
