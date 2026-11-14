"""Draw a car.py's polygons over its reference photo, to check the trace against the car.

Usage: python tools/overlay.py cars/<car>/car.py reference/<photo> out.png [x0 y0 x1 y1]

The car.py must expose S (mm per photo pixel), CX and BOT (photo px of x=0 and y=0), as
cars/mazda3_2012/car.py does. The optional box (photo px) crops the result to one area.
Outlines are drawn in a contrasting color per filament; voids in yellow.
"""

import importlib.util
import sys

from PIL import Image, ImageDraw

COLORS = [(0, 255, 0), (0, 160, 255), (255, 0, 255), (255, 140, 0), (0, 255, 255), (255, 60, 60)]


def main(car_py, photo, out, box=None, k=5):
    mod_spec = importlib.util.spec_from_file_location("car", car_py)
    car = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(car)
    spec = car.spec()
    im = Image.open(photo).convert("RGB")
    im = im.resize((im.width * k, im.height * k), Image.LANCZOS)
    draw = ImageDraw.Draw(im)
    color = {name: COLORS[i % len(COLORS)] for i, name in enumerate(spec["colors"])}
    color["void"] = (255, 255, 0)
    for layer in spec["layers"]:
        for poly in [layer["outline"]] + layer["holes"]:
            pts = [((x / car.S + car.CX) * k, (car.BOT - y / car.S) * k) for x, y in poly]
            draw.line(pts + [pts[0]], fill=color[layer["color"]], width=1)
    if box:
        im = im.crop(tuple(int(v) * k for v in box))
    im.save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:8] or None)
