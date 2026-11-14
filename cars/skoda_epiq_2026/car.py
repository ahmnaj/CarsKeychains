"""Skoda Epiq (2026) front, body color black.

Traced from the owner's straight-on photo (reference/skoda_epiq_front.jpg, 1611x2000 px).
Coordinates below are photo pixels: the silhouette comes from a scan against the grey
background, lines from the darkest pixels of each seam, details from zoomed grids. The car
is symmetric about x=805.25 px and 1297 px wide, scaled to a 62.5 mm face. The keychain
runs from the hood (cut a little above the light strip) down to the bottom of the splitter;
wheels, mirrors and the windscreen are left off as on the other cars.

The painted body is its own part ("body_black") so it can get its own black filament; the
unpainted trim (Tech-Deck face, band between the headlights, grille, splitter) belongs to
the black base part. Panel lines (hood shut line, hood-fender lines, fender-bumper
seams, the crease across the lower bumper, the bumper-lip seams, the joints in the grille
frame and the seam between light strip and gloss panel) are 0.40 mm grooves. The SKODA lettering is left as a blank badge (0.3 below the hood).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from keychain.parts import BADGE_RECESS, BASE_TOP, SURFACE, keyring_tab_ref, layer, rounded_rect  # noqa: E402

CX, BOT = 805.25, 1378.0        # symmetry axis and lowest point of the splitter (px)
S = 62.5 / 1297.0               # mm per photo pixel
TOP = 824.0                     # where the hood is cut off (px)
GROOVE_W = 0.40 / S             # panel-line grooves are 0.40 mm wide


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
SMOOTH_STEP = 6.0        # px between points on a curve (0.29 mm)


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
    """Groove along a px polyline: (floor polygon, [end caps]).

    Where the line runs off the silhouette the floor is trimmed flush with it; the piece of
    the stroke beyond is returned as a cap, to be emptied so no body-color crumb is left
    between the trimmed floor and the edge.
    """
    poly, caps = stroke(line), []
    for pts in (line, line[::-1]):
        end = pts[0]
        if inside(end, outline_px):
            continue
        k = next((i for i, q in enumerate(pts) if inside(q, outline_px)), None)
        if k is None:
            continue
        nxt = pts[min(k + 1, len(pts) - 1)]              # a point safely inside
        for a, b in zip(outline_px, outline_px[1:] + outline_px[:1]):
            d = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
            e = lambda p: (end[0] - nxt[0]) * (p[1] - nxt[1]) - (end[1] - nxt[1]) * (p[0] - nxt[0])
            if d(end) * d(nxt) < 0 and e(a) * e(b) <= 0:
                caps.append(clip_half(stroke(line), a, b, end))
                poly = clip_half(poly, a, b, nxt)
                break
    return poly, caps


def interp(pts, x):
    """Piecewise-linear y(x) through px points sorted by x (clamped at the ends)."""
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]




def both(pts):
    """A left-side px polygon and its mirror image, in mm, not smoothed (small hard-edged parts)."""
    return [mm(pts), mm(flip(pts))]


def box(x0, y0, x1, y1, r):
    """Rounded rectangle in photo px."""
    return [(x, y) for x, y in rounded_rect(x0, y0, x1, y1, r, n=6)]


# --- traced shapes (left side, photo px) -------------------------------------

# from the bottom centre round the left side to the top centre
SIL_BOTTOM = [(CX, 1378), (470, 1378), (455, 1376), (420, 1372), (330, 1366), (240, 1362),
              (190, 1358), (180, 1356), (172, 1348)]
SIL_SIDE = [(166, 1335), (160, 1310), (157.5, 1285), (157, 1230), (157.5, 1190), (159, 1120),
            (160, 1050), (161, 1000), (162, 960), (163.5, 940), (165, 922), (167, 910),
            (170, 900), (176, 890), (183, 880), (189, 872), (197, 860), (207, 840), (214, 828),
            (216, 825.5), (219, TOP), (CX, TOP)]
SILHOUETTE = SIL_BOTTOM + SIL_SIDE

# panel lines, on the darkest pixels of each seam (measured on a dark-line map of the photo)
SHUT = [(207, 857), (209, 860), (213, 863.7), (225, 869), (240, 873), (255, 876), (270, 879),
        (300, 884), (330, 887), (360, 890), (390, 893), (420, 895), (450, 897), (510, 900),
        (570, 901.5), (630, 903), (660, 904.5), (675, 907.5), (690, 914.5), (705, 921.5),
        (720, 923), (CX, 924)]
HOOD_FENDER = [(257.5, 808), (252, 824), (249, 832), (243.5, 840), (240, 848), (234.5, 856),
               (230, 864), (228.5, 869.5)]
FENDER_BUMPER = [(211, 863), (207, 868), (200, 879), (190, 891.7), (180, 905), (171.7, 918),
                 (165.8, 928), (158, 941)]
# crease across the whole lower bumper, from side to side
CREASE = [(146, 1278.5), (160, 1283.5), (173.7, 1288.7), (190, 1295), (210, 1299), (230, 1303),
          (250, 1306), (270, 1310), (290, 1312.5), (310, 1315), (330, 1318), (370, 1323),
          (410, 1326), (450, 1327.5), (490, 1328.2), (570, 1329), (650, 1329.5), (CX, 1330)]
# seam between the bumper and its lower lip: from the air curtain to the tip of the grille
# frame; from there on it is the lower edge of the grille
LIP_SEAM = [(211, 1248), (215, 1254), (222, 1258), (228, 1260), (234, 1262), (240, 1264.5),
            (246, 1267), (252, 1268.5), (262, 1269), (270, 1270), (280, 1272), (291.5, 1274),
            (303, 1276.5)]
FRAME_JOINT = [(500, 1128), (500, 1188)]          # joint in the grille frame
LAMP_SEAM = [(451, 935), (420, 964)]                  # light strip unit to gloss panel
# (line, depth of its floor, runs across the centre)
LINES = {"hood shut line": (SHUT, 2.5, True), "hood-fender line": (HOOD_FENDER, 2.5, False),
         "fender-bumper seam": (FENDER_BUMPER, 2.5, False), "lower bumper crease": (CREASE, 2.5, True),
         "bumper-lip seam": (LIP_SEAM, 2.5, False), "grille frame joint": (FRAME_JOINT, 2.5, False),
         "light strip seam": (LAMP_SEAM, 2.0, False)}

# raised centre of the hood (a fold, 0.2 mm step)
DOME_EDGE = [(674, TOP), (680, 840), (686, 855), (692, 870), (696, 888), (700, 905), (703, 916)]

# Tech-Deck face: gloss black panel under the hood carrying the light strips
TD_END = [(208.5, 871), (207, 884), (204.5, 898), (203.5, 910), (205, 916), (208.5, 918.5)]
TD_LOWER = [(214, 916), (225, 913), (240, 915), (255, 919), (270, 922), (300, 928), (330, 934),
            (360, 941), (390, 947), (405, 956), (418, 966), (435, 981), (450, 991), (465, 997),
            (480, 1000), (510, 1003), (555, 1005), (600, 1006), (690, 1007), (CX, 1007)]
LAMP_BOTTOM = [(240, 909), (270, 912), (300, 917), (350, 925), (400, 932)]   # under the LED frame
LAMP_TIP = (449, 937)
STRIP_BOTTOM = [(475, 939), (500, 940), (550, 941), (600, 942), (650, 943), (CX, 944)]
LEDS = [[(219, 881), (232, 884), (238, 897), (222, 893)],
        [(247, 887), (277, 893), (286, 908), (255, 902)],
        [(295, 895), (338, 901), (349, 916), (307, 911)],
        [(356, 903), (414, 908), (428, 925), (369, 919)]]
# slanted slits in the strip: (x top-left, y top, x bottom-left, y bottom, width)
SLITS = [(435, 908, 450, 929, 12), (467, 910, 482, 931, 12), (499, 911, 515, 932, 12),
         (532, 913, 546, 933, 12), (564, 914, 578, 933.5, 12), (596, 915, 610, 934, 12),
         (630, 916, 643, 934.5, 10), (664, 919, 675, 935, 9)]
DIMPLES = [[(702, 931), (714, 931), (718, 938.5), (710, 938.5)],
           [(736, 931), (746, 931), (750, 938.5), (743, 938.5)],
           [(767, 931), (777, 931), (780, 938.5), (773, 938.5)]]

# main headlight (dark glass with two lens modules) and the air curtain slot under it
HEADLIGHT = [(209, 994), (240, 997.5), (300, 1004.5), (350, 1011), (400, 1018), (424, 1022.5),
             (427, 1025), (418, 1036), (408, 1048), (398, 1058), (388, 1064.5), (372, 1068),
             (330, 1068), (250, 1065), (209, 1063)]
EYES = [box(230, 1011, 272, 1045, 9), box(303, 1020, 352, 1050, 9)]
AIR_CURTAIN = [(197, 1058), (223, 1058), (222, 1200), (220, 1240), (215, 1252), (209, 1252),
               (203, 1240), (198, 1200), (196, 1100)]

# black band between the headlights; its ends run down diagonally round the grille frame
BAND_TOP = [(CX, 1059), (600, 1059.3), (500, 1059.7), (460, 1061), (436, 1061.5)]
BAND_END = [(424, 1067), (418, 1078), (409, 1090), (390, 1101), (369, 1110), (352, 1125),
            (336, 1140), (316, 1160), (296, 1180), (277, 1200), (262, 1220), (253, 1240),
            (249, 1253), (253, 1263)]
ARC1 = [(261, 1268), (267, 1256), (282, 1240), (298, 1220), (320, 1200), (342, 1180), (366, 1160),
        (385, 1148), (408, 1140), (430, 1136.5), (460, 1135), (600, 1134), (CX, 1134)]
# grille: inner edge of the body-color frame and the grille's lower edge
ARC2 = [(291.5, 1273), (308, 1256), (322, 1240), (347, 1220), (372, 1200), (390, 1190),
        (412, 1184.5), (440, 1183), (CX, 1183)]
GRILLE_BOTTOM = [(300, 1275), (330, 1280), (350, 1282.5), (370, 1286.5), (400, 1290), (425, 1292.5),
                 (434, 1295), (441, 1301), (449, 1308.5), (458, 1312.5), (472, 1315), (500, 1316),
                 (CX, 1317)]
FIN_PITCH, FIN_W = 24.44, 0.42 / S          # vertical fins, 1.18 mm apart
SIDE_FINS = [403.5, 380.5, 357, 334.5]      # fins in the closed side parts of the grille
SLOT_TOP = 1218                             # see-through part between the fins starts here
RADAR = (606, 1128, 1168)                   # sensor plate under the band: x0, y0, y1

# lower bumper: black valance with a slot, black splitter under it
SPLITTER_TOP = [(220, 1350), (260, 1345), (290, 1346.5), (300, 1347), (340, 1351), (400, 1352.5),
                (CX, 1353)]
SLOT = [(CX, 1340), (470, 1338), (420, 1336), (380, 1333), (340, 1327), (300, 1323), (302, 1329),
        (312, 1336), (340, 1343), (380, 1348), (420, 1356), (CX, 1356)]
BADGE = (722, 886, 909.5)                   # blank badge for the lettering: x0, y0, y1


def grille_top(x):
    return interp(ARC2, x)


def grille_bottom(x):
    return interp([ARC2[0]] + GRILLE_BOTTOM, x)


def spec():
    outline = sym(SILHOUETTE)
    outline_px = SILHOUETTE + flip(SILHOUETTE)[1:-1]
    half = GROOVE_W / 2

    # keyring tab as on the reference models, hole at 53% of the height
    hole_y = 0.53 * (BOT - TOP)
    side_x = interp([(y, x) for x, y in SIL_SIDE[:8]][::-1], BOT - hole_y)
    tab, tab_hole, tab_fillets = keyring_tab_ref((side_x - CX) * S, hole_y * S, mm(outline))

    # hood: stops at the hood-fender lines and at the upper edge of the shut-line groove
    shut_edge = [(x, y - half) for x, y in SHUT[4:]]
    hood = sym([(CX, TOP)] + [(x + half, y) for x, y in HOOD_FENDER[1:-1]] + shut_edge)
    dome = sym([(CX, TOP)] + DOME_EDGE + shut_edge[-2:])

    # Tech-Deck face and what stands on it
    tech_deck = sym([(CX, 924)] + SHUT[-2:1:-1] + TD_END + TD_LOWER)
    lamp_px = SHUT[2:12] + [LAMP_TIP] + LAMP_BOTTOM[::-1] + [TD_LOWER[1], TD_LOWER[0]] + TD_END[::-1]
    lamp_l, lamp_r = pair(lamp_px)
    wedge_l, wedge_r = pair([TD_LOWER[1]] + LAMP_BOTTOM + [LAMP_TIP] + TD_LOWER[10:1:-1])
    strip = sym([(CX, 924)] + SHUT[-2:10:-1] + [LAMP_TIP] + STRIP_BOTTOM)
    slits = [p for x0, y0, x1, y1, w in SLITS for p in both([(x0, y0), (x0 + w, y0), (x1 + w, y1), (x1, y1)])]
    slits += [p for d in DIMPLES for p in both(d)]
    slits.append(mm([(CX - 6.5, 931), (CX + 6.5, 931), (CX + 4, 938.5), (CX - 4, 938.5)]))
    leds = [p for led in LEDS for p in both(led)]

    hl_l, hl_r = pair(HEADLIGHT)
    eyes = [p for e in EYES for p in both(e)]
    air_l, air_r = both(AIR_CURTAIN)

    band = sym(BAND_TOP + BAND_END + ARC1)
    frame = sym([(CX, 1134)] + ARC1[-2::-1] + ARC2)
    grille = sym([(CX, 1183)] + ARC2[-2::-1] + GRILLE_BOTTOM)
    x0, y0, y1 = RADAR
    radar = mm([(x0, y0), (2 * CX - x0, y0), (2 * CX - x0, y1), (x0, y1)])

    # grille fins and the see-through slots between them
    fin_x = [CX - FIN_PITCH / 2 * (2 * k + 1) for k in range(16)]          # centre outwards
    fins, slots = [], []
    for x in fin_x + SIDE_FINS:
        a, b = x - FIN_W / 2, x + FIN_W / 2
        fins += both([(a, grille_top(a) + 2), (b, grille_top(b) + 2),
                      (b, grille_bottom(b) - 2), (a, grille_bottom(a) - 2)])
    for xr, xl in zip(fin_x, fin_x[1:]):
        a, b = xl + FIN_W / 2, xr - FIN_W / 2
        slots += both([(a, SLOT_TOP), (b, SLOT_TOP), (b, grille_bottom(b) - 9), (a, grille_bottom(a) - 9)])
    a = fin_x[0] + FIN_W / 2
    slots.append(mm([(a, SLOT_TOP), (2 * CX - a, SLOT_TOP), (2 * CX - a, 1308), (a, 1308)]))

    # lower bumper
    # (valance and body both run on under the splitter, which is laid over them afterwards)
    valance = sym(CREASE[:8:-1] + [(290, 1346.5), (293, 1358), (CX, 1361)])
    body = sym([(CX, 1364), (330, 1360), (220, 1355), (190, 1353.5), SIL_BOTTOM[-1]] + SIL_SIDE)
    slot = sym(SLOT)
    splitter = sym(SIL_BOTTOM + SPLITTER_TOP)
    # folds in the body color, 0.2 mm below the face: the sides of the bumper beside the air
    # curtains, and the lower lip under the bumper-lip seam and the grille (it runs on under
    # the valance and splitter, which are laid over it afterwards)
    side_px = [(140, 960), (150, 938), (165.8, 928), (171.7, 918), (180, 905), (190, 891.7),
               (200, 879), (201, 900), (200, 945), (199, 1000), (198, 1058), (196, 1100),
               (198, 1200), (203, 1240), (207, 1250), (140, 1250)]
    lower = sym([(CX, 1314)] + [(x, y - 3) for x, y in GRILLE_BOTTOM[-2::-1]] +
                [(291.5, 1274.3), (262, 1269.5), (240, 1265), (225, 1259.5), (213, 1253),
                 (203, 1245), (135, 1245), (135, 1357), (172, 1349.5), (220, 1352), (260, 1348),
                 (300, 1350), (CX, 1356)])
    x0, y0, y1 = BADGE
    badge = mm(box(x0, y0, 2 * CX - x0, y1, 6))

    # panel lines: a black floor plus a void above it, so the body is cut clean through and
    # splits into separate pieces along each line. Every line runs through to the silhouette
    # or into the black part it meets.
    grooves, gaps, caps = [], [], []
    for name, (line, floor, across) in LINES.items():
        if across:
            ln = smooth_line(line + flip(line)[1:])
            g, c = groove(ln, outline_px)
            grooves.append((name, floor, mm(g)))
            gaps.append((name, floor, mm(stroke(ln))))
            caps += [mm(q) for q in c]
        else:                      # trace the left one and mirror it, so both sides are identical
            ln = smooth_line(line)
            g, c = groove(ln, outline_px)
            for side, g, v in zip("LR", both(g), both(stroke(ln))):
                grooves.append((f"{name} {side}", floor, g))
                gaps.append((f"{name} {side}", floor, v))
            caps += [q for cap in c for q in both(cap)]

    def sunk(name, top, shape, color="black"):
        """A black area lower than the face: the black itself and empty space above it."""
        return [layer(name, color, 0, top, shape), layer(name + " (space)", "void", top, 4.0, shape)]

    layers = [
        layer("Backing", "black", 0, BASE_TOP, outline),
        layer("Keyring tab", "black", 0, SURFACE, tab, holes=[tab_hole]),
        *[layer("Keyring tab fillet", "black", 0, BASE_TOP, f) for f in tab_fillets],
        layer("Body", "body_black", BASE_TOP, SURFACE, body),
        layer("Hood", "body_black", BASE_TOP, 3.2, hood),
        layer("Hood centre", "body_black", BASE_TOP, 3.4, dome),
        layer("Grille frame", "body_black", BASE_TOP, 3.2, frame),
        *[layer("Bumper side fold", "void", 2.8, 4.0, p) for p in both(side_px)],
        layer("Lower lip fold", "void", 2.8, 4.0, lower),
        *sunk("Tech-Deck face", 2.4, tech_deck),
        layer("Light strip housing L", "black", 0, 2.8, lamp_l),
        layer("Light strip housing R", "black", 0, 2.8, lamp_r),
        layer("Tech-Deck wedge L", "black", 0, 2.6, wedge_l),
        layer("Tech-Deck wedge R", "black", 0, 2.6, wedge_r),
        layer("Slit strip", "black", 0, 2.8, strip),
        *[layer("Slit", "void", 2.2, 4.0, s) for s in slits],
        *sunk("Sensor plate", 2.9, radar),
        *sunk("Band between headlights", 2.6, band),
        *sunk("Grille", 2.0, grille),
        *[layer("Grille fin", "black", 0, 2.6, f) for f in fins],
        *sunk("Air curtain L", 2.0, air_l),
        *sunk("Air curtain R", 2.0, air_r),
        layer("Headlight L (space)", "void", 2.8, 4.0, hl_l),
        layer("Headlight R (space)", "void", 2.8, 4.0, hl_r),
        layer("Headlight glass L", "dark_grey", BASE_TOP, 2.8, hl_l),
        layer("Headlight glass R", "dark_grey", BASE_TOP, 2.8, hl_r),
        *sunk("Lower valance", 2.6, valance),
        layer("Valance slot", "void", 2.0, 4.0, slot),
        layer("Splitter", "black", 0, SURFACE, splitter),
        *sunk("Blank lettering badge", 3.4 - BADGE_RECESS, badge),
        *[layer("Panel line end", "void", BASE_TOP, 4.0, c) for c in caps],
        *[layer(f"Panel line {n}", "black", 0, z, g) for n, z, g in grooves],
        *[layer(f"Panel line {n} (gap)", "void", z, 4.0, g) for n, z, g in gaps],
        *[layer("Light strip LED", "white", 2.0, SURFACE, p) for p in leds],
        *[layer("Grille opening", "void", 0, 4.0, s) for s in slots],
        *[layer("Headlight lens", "void", 0, 4.0, e) for e in eyes],
    ]
    colors = {"black": [0.02, 0.02, 0.02], "body_black": [0.13, 0.14, 0.16],
              "dark_grey": [0.271, 0.271, 0.271], "white": [0.961, 0.961, 0.961]}
    return {"name": "skoda_epiq_2026", "colors": colors, "layers": finish(layers)}
