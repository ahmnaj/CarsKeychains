"""Render a top-down color preview PNG of a generated keychain STEP.

Usage: python tools/preview.py cars/<car>/out/<car>.step preview.png

Upward faces are drawn in their part color, darker the lower they sit,
so pockets and raised details are visible at a glance.
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

from extract_spec import read_parts


def main(step, png):
    polys = []
    z_top = 0.0
    for _, rgb, solid in read_parts(step):
        rgb = rgb or (1, 0, 1)
        # mesh the whole solid at once; per-face meshing drops faces with many holes
        verts, tris = solid.tessellate(0.01, 0.2)
        for t in tris:
            a, b, c = (verts[k] for k in t)
            if (b - a).cross(c - a).z <= 1e-9:  # keep only upward-facing triangles
                continue
            z = (a.z + b.z + c.z) / 3
            z_top = max(z_top, z)
            polys.append((z, [(a.x, a.y), (b.x, b.y), (c.x, c.y)], rgb))
    polys.sort(key=lambda p: p[0])
    shade = lambda rgb, z: tuple(c * (0.55 + 0.45 * z / z_top) for c in rgb)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.add_collection(PolyCollection([p[1] for p in polys],
                                     facecolors=[shade(p[2], p[0]) for p in polys],
                                     edgecolors=[shade(p[2], p[0]) for p in polys], linewidths=0.2))
    ax.autoscale()
    ax.set_aspect("equal")
    ax.set_facecolor((0.55, 0.7, 0.85))
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("mm")
    plt.savefig(png, dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main(*sys.argv[1:3])
