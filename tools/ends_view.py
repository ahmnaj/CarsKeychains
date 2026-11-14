"""Close-ups of the built model, to check that every groove ends in another part.

Usage: python tools/ends_view.py cars/<car>/car.py out.png            # one tile per groove end
       python tools/ends_view.py cars/<car>/car.py out.png x y [r]    # one tile round a photo px

Top-down view of the STEP with the body color drawn light and black dark (both shaded by
height), so a strip of body color left between a groove end and the part it should meet
shows up at once. The car.py must expose LINES ({name: (px line, ...)}), S, CX and BOT.
"""

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_spec import read_parts  # noqa: E402


def main(car_py, png, *window):
    mod_spec = importlib.util.spec_from_file_location("car", car_py)
    car = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(car)
    name = car.spec()["name"]
    step = Path(car_py).parent / "out" / f"{name}.step"
    tris = []
    for _, rgb, solid in read_parts(str(step)):
        dark = sum(rgb or (1, 0, 1)) / 3 < 0.08          # the black base part
        verts, faces = solid.tessellate(0.01, 0.2)
        for t in faces:
            a, b, c = (verts[k] for k in t)
            if (b - a).cross(c - a).z <= 1e-9:
                continue
            z = (a.z + b.z + c.z) / 3
            g = (0.05 + 0.10 * z) if dark else (0.45 + 0.15 * z)
            col = (g, g, g) if dark or sum(rgb) / 3 < 0.2 else tuple(0.5 * g + 0.5 * v for v in rgb)
            tris.append((z, [(a.x, a.y), (b.x, b.y), (c.x, c.y)], col))
    tris.sort(key=lambda p: p[0])
    if window:
        r = float(window[2]) if len(window) > 2 else 60
        spots = [("", (float(window[0]), float(window[1])), r)]
    else:
        spots = [(f"{n} {e}", line[0][i], 35) for n, line in car.LINES.items()
                 for e, i in (("start", 0), ("end", -1))]
    cols = min(6, len(spots))
    rows = -(-len(spots) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.2 * rows), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for ax, (title, (px, py), r) in zip(axes.flat, spots):
        x, y, d = (px - car.CX) * car.S, (car.BOT - py) * car.S, r * car.S
        near = [t for t in tris if abs(t[1][0][0] - x) < 2 * d + 3 and abs(t[1][0][1] - y) < 2 * d + 3]
        ax.add_collection(PolyCollection([t[1] for t in near], facecolors=[t[2] for t in near],
                                         edgecolors=[t[2] for t in near], linewidths=0.2))
        ax.set_xlim(x - d, x + d)
        ax.set_ylim(y - d, y + d)
        ax.set_aspect("equal")
        ax.set_facecolor((0.55, 0.7, 0.85))
        ax.set_title(title, fontsize=7)
    plt.tight_layout()
    plt.savefig(png, dpi=110)


if __name__ == "__main__":
    main(*sys.argv[1:])
