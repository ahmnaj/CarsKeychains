"""Local-contrast view of a photo crop with a pixel grid, to find and measure panel lines.

Usage: python tools/seam_map.py <photo> <out.png> x0 y0 x1 y1 [scale] [gain]

Subtracts the blurred surroundings and amplifies what is left, so thin seams show as crisp
dark lines even on bright or dark paint where the plain photo hides them. Soft folds stay
soft, which tells a real seam (groove) from a fold (height step). Needs scipy.
"""

import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi


def main(photo, out, x0, y0, x1, y1, scale=4, gain=6.0):
    x0, y0, x1, y1, k = (int(v) for v in (x0, y0, x1, y1, scale))
    im = np.asarray(Image.open(photo).convert("L")).astype(float)[y0:y1, x0:x1]
    hp = im - ndi.gaussian_filter(im, 6)
    img = Image.fromarray(np.clip(128 + hp * float(gain), 0, 255).astype(np.uint8)).convert("RGB")
    img = img.resize(((x1 - x0) * k, (y1 - y0) * k), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    for x in range(x0 - x0 % 10 + 10, x1, 10):
        d.line([((x - x0) * k, 0), ((x - x0) * k, img.height)], fill=(255, 0, 0) if x % 50 == 0 else (255, 220, 0))
        if x % 20 == 0:
            d.text(((x - x0) * k + 2, 2), str(x), fill=(255, 0, 0))
    for y in range(y0 - y0 % 10 + 10, y1, 10):
        d.line([(0, (y - y0) * k), (img.width, (y - y0) * k)], fill=(255, 0, 0) if y % 50 == 0 else (255, 220, 0))
        if y % 20 == 0:
            d.text((2, (y - y0) * k + 2), str(y), fill=(255, 0, 0))
    img.save(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
