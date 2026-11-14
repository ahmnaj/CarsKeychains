# CarsKeychains

Multi-color 3D-printed car-front keychains, printed on a Bambu printer (AMS).
The owner models cars in Autodesk Inventor; this repo turns new car requests
into print-ready files in the same house style without manual CAD work.

## Setup

```
pip install -r requirements.txt   # CadQuery; takes ~10 min on a fresh cloud machine
```

## Layout

- `reference/Mercedes1.stp` – the owner's original Inventor export (W124 Mercedes); `reference/mercedes_w124_front.jpg` the photo it was modeled from.
- `keychain/geometry.py` – builds non-overlapping per-color bodies from a layer spec and exports STEP + STLs.
- `keychain/parts.py` – helpers and the standard heights for authoring new cars.
- `tools/build.py <spec.json|car.py>` – build a car into `cars/<car>/out/` (STEP, one STL per color, `preview.png`).
- `tools/extract_spec.py <in.stp> <out.json> --name <car>` – convert another Inventor STEP from the owner into a spec.
- `tools/preview.py <step> <png>` – top-down color render. Always look at it before handing files over.
- `tools/height_view.py <step> <png>` – same view with height as brightness and black drawn in grey; the only way to see steps inside black areas (grilles, valances).
- `tools/photo_grid.py <photo> <png> x0 y0 x1 y1 [scale] [grid] [gamma]` – zoomed crop of a photo with a pixel grid, for measuring; gamma 0.4 brightens shadows.
- `tools/overlay.py <car.py> <photo> <png> [x0 y0 x1 y1]` – draws the car's polygons over its photo to check the trace (5x enlarged; give a box for big photos). Save the full-face overlay as `out/overlay.png` for the hand-over.
- `tools/seam_map.py <photo> <png> x0 y0 x1 y1 [scale] [gain]` – local-contrast view with a pixel grid: seams show as crisp dark lines, folds stay soft. Use it to find every panel line before tracing any.
- `cars/<car>/` – one folder per car: `spec.json` or `car.py`, plus `out/`.

## Spec format

`{"name", "colors": {name: [r,g,b] 0-1}, "layers": [{"name", "color", "z": [z0, z1], "outline": [[x,y],...], "holes": [[[x,y],...]]}]}`
Units mm, front view: +X right, +Y up, Z up from the print bed. Layers are applied in
order like paint: each layer carves its volume out of every earlier layer of another
color. So: put the black backing first, then body paint, then inlays and trim.
A layer with color `"void"` is empty space: it carves every earlier layer of any color
and adds no part (use it for grooves and openings that must cut through stacked layers).
Carving is by volume only: a black layer 0 to 2.0 under a 3.0 body removes the body up to
2.0 and leaves blue above it. So everything lower than the surface around it needs either
a hole in each body-color layer over it, or a `"void"` layer above it. Prefer the void;
holes that touch the outline or each other, or cross a layer's edge, break the booleans.
A `car.py` must define `spec()` returning this dict; build it with helpers from `keychain/parts.py`.
`cars/mazda3_2012/car.py` is the authored example: it traces in photo pixels (`S`, `CX`,
`BOT` convert to mm) and has reusable helpers for smoothing (`finish`), panel-line grooves
(`groove`, `stroke`) and honeycomb mesh (`honeycomb`). Copy them for the next car.
`cars/skoda_epiq_2026/car.py` is the second one (black car, 1611x2000 photo): it adds `sunk()`
(a black area plus the void over it), vertical grille fins with see-through slots, and folds
made by a void over the body color. On a black car the painted body stays its own part
(`body_black`) so the owner can give it its own filament.

## House style

Measured from six of the owner's STEP files in `reference/` (Mercedes W124, Toyota Prius
2018, Hyundai Ioniq 2019, Hyundai Starex van, Hyundai Ioniq 6 2023, Mercedes SL), each
with its reference photo next to it. The Ioniq 6 and SL use Slovak part names (spodok =
bottom, vrch = top). The SL's STEP export is broken (its black base came out as an empty
sliver) and is an older, thinner version; use `reference/Mercedes_SL380.stl` instead, which
is complete and follows the same rules (base 1.5, parts from 1.5, bumper 3.6, Ø4 hole).

- Size: always about 70 mm wide including the keyring tab (69.5 to 70.5); height follows the
  car, 24 to 31 mm. The car face itself is about 62 to 63 mm wide.
- Thickness: 3.0 to 3.4 mm main face; the most proud features reach 3.6 to 3.9.
- Construction, the same on every car:
  - A black "Parts" body: backing plate 0 to 1.5 under the whole silhouette, plus the
    keyring tab, and black raised wherever the car is black (grilles, bumper strips,
    headlight housings, vents). Black detail tops sit at 2.0 to 3.0.
  - The body-color part sits on the backing from 1.5 and has stepped tops at 0.2 mm
    increments: 2.5, 2.8, 3.0, 3.2, 3.4 (hood lips, bumper creases, fenders).
  - Other colors are separate parts that either stand on the backing (bottom 1.5) or sit in
    pockets, 0.5 to 1.0 deep, mostly finishing flush with the surrounding surface;
    trim and logos may stand 0.2 to 0.5 proud.
  - Small dark openings are often see-through holes through the whole keychain: grille
    cells (W124), round headlight "eyes" about 3 mm (Prius, Ioniq), LED slots 2.5 x 1.2
    (Ioniq 6), lower-grille slits about 0.7 to 1.1 mm wide (Prius).
- Filaments: black is always the base. Body color is whatever the car is: white, silver,
  or grey (Inventor's default grey 0.749 means it is printed in grey filament). Accents:
  white for lamps and LED dots, silver for "chrome" trim (white 0.961 and chrome 0.957 are
  different filaments: white and silver), dark grey for grille surrounds and lower bumpers,
  orange for indicators, gold/yellow for chrome lips or fog lamps. 3 to 6 colors per car.
- The owner has one AMS (4 slots). With more than 4 colors, the extra colors are printed
  separately and glued in afterwards, so design normally: each color stays its own part
  and nothing about the construction changes. Mention in the hand-over which colors would
  be glue-ins (the least-used ones).
  Inventor RGB: black 0.02, white 0.961, chrome 0.957, dark grey 0.271, silver 0.6,
  orange (0.867, 0.486, 0.059) or (0.812, 0.31, 0), gold (0.886, 0.863, 0.165).
- Keyring tab: black, on the left, same on every car (`keyring_tab_ref` in `keychain/parts.py`):
  8 mm tall, outer end with R3.5 rounded corners (1 mm flat between them), Ø4.0 hole 4.0 mm
  in from that end, full face height (3.0; 3.4 on the Ioniq). The hole center is 3.2 to
  3.6 mm outside the body edge, at 50 to 56% of the car's height. Where the tab meets the
  car, only the 1.5 mm backing has concave R3.5 fillets. The owner rejected a tab pulled
  into the body; keep it as on the references.
- Simplification: headlights become black housings with colored inlays and see-through
  eyes; grilles become black recesses with chrome or body-color bars or a mesh; bull bars
  and bumpers are the tallest parts.
- Logos: never model them on new cars. Leave a blank badge where the logo goes, shaped like
  the real badge outline, in black, 0.3 mm below the surrounding surface so the owner can
  glue a logo into it (Prius: 6.0 x 4.3 mm oval, top at 2.7 in a 3.0 face). The older
  models with modeled logos (Ioniq 6, SL) are not the pattern to follow.
- The license plate is not modeled: the owner adds it from a Bambu Studio template.
- Smallest features: about 0.4 mm slots and 0.5 mm wide trim lines.

## What the owner expects (learned on the Mazda 3)

The owner checks every detail against the photo and sends it back until it matches. These
rules come from that review; follow them from the first version.

- Accuracy over speed. Never eyeball a shape. Measure it (see Tracing), and show the
  overlay on the photo with the hand-over. The silhouette matters most.
- Extent: from the hood, cut a little above the headlights, down to the bottom of the
  bumper. No wheels, mirrors, windscreen or roof.
- Panel lines are wanted: hood shut line, hood-fender lines, fender-bumper seams. Make
  them 0.40 mm grooves (not thicker) centered on the darkest pixels of the seam: black
  floor at 2.5 plus a void above. Run each one right through to the silhouette edge or
  into the part it meets, so the body-color part splits into separate pieces along it; a
  groove that stops short or sits under a raised layer reads as a stroke drawn on top.
  A soft fold in a surface (gradual light/dark change) is a 0.2 mm height step instead;
  sharp creases are grooves (see below). Do not add lines the car does not have.
- Grooves get their own study (the owner sent the Epiq back for this). First list every
  seam with `tools/seam_map.py` over the whole face; do not rely on the plain photo, where
  seams on bright or dark paint are invisible. Then take each line's points from the darkest
  pixel per row or column, not from an overlay by eye (two "corrections" made by eye on the
  Epiq moved lines 2 to 5 px the wrong way). A line that crosses the car (lower bumper
  crease) is one groove from edge to edge, also where it becomes the border between body
  color and black. Seams between two black parts get a groove too, floor 0.4 below the lower
  part. Trace the left line and mirror the finished polygons. Where a groove runs off the
  silhouette, empty its end cap (`groove` in the Epiq car.py returns it) or a body-color
  crumb is left at the edge. Save a picture of the grooves over the photo as
  `out/grooves.png` for the hand-over.
- Sharp creases count as grooves for the owner, not only panel gaps (second Epiq review:
  the crease between the headlight tips, the one under the light strips, the hood centre
  creases, the bumper corner edges). A crease has no dark line: find it as the row/column
  of steepest brightness change, measure it on both sides of the car and keep it only if the
  two sides agree (reflections do not mirror, real creases do); where one side is washed
  out, use the other. Each crease still has to end in the silhouette or in another part
  (headlight, grille, black trim, another groove). Only soft shading stays a 0.2 mm step
  or is left out.
- Black areas must not be flat. Give grilles and valances their real structure with
  0.4 to 1 mm steps (slot, panel, mesh, intake) and make meshes see-through: for a
  honeycomb grille, wide flat hexagon cells about 2.5 x 0.9 mm with 0.4 mm webs, rows
  following the grille's curve, trimmed by the frame like the real mesh. Do not invent a
  pattern (slits, wavy slats): if the photo is too dark to show the mesh, ask the owner
  for a close-up.
- Dark is not always black. Brighten the photo before deciding: on the Mazda the lower
  bumper looked black but was body color with small black openings. Body color should
  flow unbroken where it does on the car (lips, corners); do not let black cut it.
- The bottom edge is rarely a straight line. Trace the lower bumper like the rest.
- Curves must be smooth, not faceted: run every traced polygon through the smoothing
  (`finish` in the Mazda car.py), which keeps the traced points and real corners. Check
  that the silhouette moved less than 0.1 mm and the bounding box did not change.
- Keyring tab exactly as on the references (see House style); do not move it into the body.

## Tracing a photo

1. Save the photo in `reference/` and work in its pixel coordinates.
2. Silhouette: scan each row for the first and last non-background pixel; this also gives
   the symmetry axis and the scale (car face = 62.5 mm).
3. Details: `tools/photo_grid.py` at 4x to 8x, also with gamma 0.4 for dark areas. For a
   thin dark line, take the darkest pixel across it every few px rather than reading it
   off the grid.
4. Trace the left half and mirror it. Keep each shared edge as one named point list and
   build the neighbouring polygons from that same list, so parts meet exactly.
5. After every build run `tools/overlay.py` and compare; fix anything more than about
   1 px off. Then look at `preview.png` and `tools/height_view.py`.
6. Before hand-over check every body: valid, the expected number of separate solids, and
   no slivers (solids under about 0.1 mm3), and that no part pokes outside the silhouette
   (compare bounding boxes). A void may overrun the outline; a black floor may not.

## Making a new car

1. Get a straight-on front photo (or SVG/DXF outlines) from the owner. Do not invent
   a car's face from memory; ask for a reference.
2. Write `cars/<car>/car.py`: silhouette and keyring tab, then body, pockets, inlays and
   trim, following the house style above. Scale it so the keychain is about 70 mm wide
   including the tab. `cars/mazda3_2012/car.py` is the pattern to copy; the other five
   folders are specs extracted from the owner's own models (see Tracing a photo and
   What the owner expects).
3. Run `python tools/build.py cars/<car>/car.py`, look at `out/preview.png` and the
   overlay on the photo, and iterate until they match.
4. Leave the logo as a blank badge (see House style).
5. Commit the car folder including `out/` so the owner can download the files from GitHub.

## Printing

In Bambu Studio, import the STEP (or select all of a car's STLs together) and accept "load
as a single object with multiple parts"; then assign one filament per part.
