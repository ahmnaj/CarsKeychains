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


def layer(name, color, z0, z1, outline, holes=None):
    return {"name": name, "color": color, "z": [z0, z1], "outline": outline, "holes": holes or []}
