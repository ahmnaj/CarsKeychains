"""Zoom into a reference photo with a pixel grid, for measuring outlines instead of guessing.

Usage: python tools/photo_grid.py <photo> out.png x0 y0 x1 y1 [scale] [grid] [gamma]

Crops the box (photo px), enlarges it `scale` times (default 6) and draws a labelled grid
every `grid` px (default 5). A gamma below 1 (try 0.4) brightens shadows: use it before
deciding what is black, because dark photos hide body-colored parts and grille detail.
"""

import sys

from PIL import Image, ImageDraw


def main(photo, out, x0, y0, x1, y1, scale=6, grid=5, gamma=1.0):
    x0, y0, x1, y1, scale, grid = (int(v) for v in (x0, y0, x1, y1, scale, grid))
    im = Image.open(photo).convert("RGB")
    if float(gamma) != 1.0:
        im = im.point([int(255 * (i / 255) ** float(gamma)) for i in range(256)] * 3)
    im = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.LANCZOS)
    draw = ImageDraw.Draw(im)
    for x in range(x0 - x0 % grid + grid, x1, grid):
        major = x % (grid * 5) == 0
        draw.line([((x - x0) * scale, 0), ((x - x0) * scale, im.height)],
                  fill=(255, 0, 0) if major else (255, 220, 0))
        if x % (grid * 2) == 0:
            draw.text(((x - x0) * scale + 2, 2), str(x), fill=(255, 0, 0))
    for y in range(y0 - y0 % grid + grid, y1, grid):
        major = y % (grid * 5) == 0
        draw.line([(0, (y - y0) * scale), (im.width, (y - y0) * scale)],
                  fill=(255, 0, 0) if major else (255, 220, 0))
        if y % (grid * 2) == 0:
            draw.text((2, (y - y0) * scale + 2), str(y), fill=(255, 0, 0))
    im.save(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
