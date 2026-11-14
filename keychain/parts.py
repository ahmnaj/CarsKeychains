"""Helpers for authoring new car specs (outlines in mm, front view).

Heights follow the house style measured from reference/Mercedes1.stp;
see CLAUDE.md for what each level is used for.
"""

import math

# Heights above the print bed (mm)
BASE_TOP = 1.5       # black backing plate, full silhouette
POCKET_FLOOR = 2.5   # floor under lights/bezels inlays (0.5 deep pockets)
SURFACE = 3.0        # main face of the keychain; inlays finish flush here
TRIM_TOP = 3.5       # chrome trim raised 0.5 above the surface
BUMPER_TOP = 3.7     # most proud feature (bumper strip / plate bracket)
BADGE_RECESS = 0.3   # blank logo badge sits this far below the surface around it

# Keyring tab (from the Mercedes): Ø4 hole, R4 rounded end, R3.5 neck fillets
RING_HOLE_R = 2.0
RING_TAB_R = 4.0
RING_NECK_FILLET = 3.5


def circle(cx, cy, r, n=64):
    return [[cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)] for i in range(n)]


def rounded_rect(x0, y0, x1, y1, r, n=8):
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = []
    corners = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]
    for cx, cy, a0 in corners:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append([cx + r * math.cos(a), cy + r * math.sin(a)])
    return pts


def mirror(points, axis_x=0.0):
    """Mirror an outline across the vertical line x=axis_x (keeps winding valid)."""
    return [[2 * axis_x - x, y] for x, y in reversed(points)]


def keyring_tab(hole_x, hole_y, attach_x):
    """Stadium-shaped tab from the hole center to the body edge at attach_x.

    Returns (outline, hole). Put the outline in the base layer (black, 0 to
    SURFACE) and the hole as a hole of that layer.
    """
    r = RING_TAB_R
    if attach_x > hole_x:  # tab sticks out to the left
        pts, a0 = [[attach_x, hole_y - r], [attach_x, hole_y + r]], 90
    else:                  # tab sticks out to the right
        pts, a0 = [[attach_x, hole_y + r], [attach_x, hole_y - r]], -90
    for i in range(33):
        a = math.radians(a0 + 180 * i / 32)
        pts.append([hole_x + r * math.cos(a), hole_y + r * math.sin(a)])
    return pts, circle(hole_x, hole_y, RING_HOLE_R)


def keyring_tab_ref(side_x, hole_y, outline, hole_offset=3.4):
    """Keyring tab exactly as on the owner's reference models (left side).

    Measured on all five STEP files: an 8 mm tall tab whose outer end has R3.5
    rounded corners (1 mm flat between them), Ø4 hole 4.0 mm in from that end,
    full face height. Where the tab meets the car, the 1.5 mm backing plate has
    concave R3.5 fillets, tangent to the tab edge and to the car's side.

    side_x: x of the car's side at the hole height; outline: silhouette (mm).
    Returns (tab, hole, [fillet_top, fillet_bottom]): tab goes in a black layer
    0 to SURFACE with the hole, fillets in black layers 0 to BASE_TOP.
    """
    h, rc, f = 4.0, 3.5, RING_NECK_FILLET
    hx = side_x - hole_offset
    x0 = hx - 4.0                                        # outer end of the tab
    arc = lambda cx, cy, r, a0, a1, n=12: [
        [cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
         cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))] for i in range(n + 1)]
    tab = [[side_x + 1.5, hole_y + h]] + arc(x0 + rc, hole_y + h - rc, rc, 90, 180) + \
        arc(x0 + rc, hole_y - h + rc, rc, 180, 270) + [[side_x + 1.5, hole_y - h]]

    def dist(px, py):                                    # distance to the silhouette
        best = (1e9, None)
        for (ax, ay), (bx, by) in zip(outline, outline[1:] + outline[:1]):
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ((dx * dx + dy * dy) or 1e-12)))
            q = (ax + t * dx, ay + t * dy)
            best = min(best, (math.hypot(px - q[0], py - q[1]), q))
        return best

    fillets = []
    for sgn in (1, -1):
        cy = hole_y + sgn * (h + f)
        lo, hi = side_x - 2 * f, side_x                  # slide the centre until it touches the side
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if dist(mid, cy)[0] > f else (lo, mid)
        cx, q = lo, dist(lo, cy)[1]
        a_end = math.degrees(math.atan2(q[1] - cy, q[0] - cx))
        a_tab = -90 if sgn > 0 else 90
        fillets.append([[cx, hole_y + sgn * h]] + arc(cx, cy, f, a_tab, a_end)[1:] +
                       [[q[0] + 1.5, q[1]], [side_x + 1.5, hole_y + sgn * h]])
    return tab, circle(hx, hole_y, RING_HOLE_R), fillets


def layer(name, color, z0, z1, outline, holes=None):
    return {"name": name, "color": color, "z": [z0, z1], "outline": outline, "holes": holes or []}
