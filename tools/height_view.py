"""Top-down render where brightness is height and black parts are drawn in grey.

Usage: python tools/height_view.py cars/<car>/out/<car>.step out.png

The normal preview shows black parts as flat black, so steps inside grilles, valances and
vents are invisible there. Use this to check black-on-black relief and see-through holes.
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

from extract_spec import read_parts


def main(step, png):
    polys = []
    for _, rgb, solid in read_parts(step):
        rgb = rgb or (1, 0, 1)
        verts, tris = solid.tessellate(0.01, 0.2)
        for t in tris:
            a, b, c = (verts[k] for k in t)
            if (b - a).cross(c - a).z <= 1e-9:
                continue
            polys.append(((a.z + b.z + c.z) / 3, [(a.x, a.y), (b.x, b.y), (c.x, c.y)], rgb))
    polys.sort(key=lambda p: p[0])

    def shade(rgb, z):
        k = (z - 1.4) / 2.0
        return tuple(min(1, max(c, 0.25) * (0.25 + 0.95 * k)) for c in rgb)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.add_collection(PolyCollection([p[1] for p in polys], facecolors=[shade(p[2], p[0]) for p in polys],
                                     edgecolors=[shade(p[2], p[0]) for p in polys], linewidths=0.2))
    ax.autoscale()
    ax.set_aspect("equal")
    ax.set_facecolor((1, 1, 1))
    ax.set_title("Height view: brighter = higher (black parts in grey so their relief shows)")
    plt.savefig(png, dpi=110, bbox_inches="tight")


if __name__ == "__main__":
    main(*sys.argv[1:3])
