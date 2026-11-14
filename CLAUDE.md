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
- `cars/<car>/` – one folder per car: `spec.json` or `car.py`, plus `out/`.

## Spec format

`{"name", "colors": {name: [r,g,b] 0-1}, "layers": [{"name", "color", "z": [z0, z1], "outline": [[x,y],...], "holes": [[[x,y],...]]}]}`
Units mm, front view: +X right, +Y up, Z up from the print bed. Layers are applied in
order like paint: each layer carves its volume out of every earlier layer of another
color. So: put the black backing first, then body paint, then inlays and trim.
A layer with color `"void"` is empty space: it carves every earlier layer of any color
and adds no part (use it for grooves and openings that must cut through stacked layers).
A `car.py` must define `spec()` returning this dict; build it with helpers from `keychain/parts.py`.

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

## Making a new car

1. Get a straight-on front photo (or SVG/DXF outlines) from the owner. Do not invent
   a car's face from memory; ask for a reference.
2. Write `cars/<car>/car.py`: silhouette and keyring tab, then body, pockets, inlays and
   trim, following the house style above. Scale it so the keychain is about 70 mm wide
   including the tab. `cars/` has five rebuilt examples to copy patterns from.
3. Run `python tools/build.py cars/<car>/car.py`, look at `out/preview.png`, compare it
   with the photo and iterate.
4. Leave the logo as a blank badge (see House style).
5. Commit the car folder including `out/` so the owner can download the files from GitHub.

## Printing

In Bambu Studio, import the STEP (or select all of a car's STLs together) and accept "load
as a single object with multiple parts"; then assign one filament per part.
