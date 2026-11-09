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
A `car.py` must define `spec()` returning this dict; build it with helpers from `keychain/parts.py`.

## House style (measured from the Mercedes)

- Size: about 70 x 25 mm including the keyring tab; the car face itself about 63 x 25.
- Filaments: black, white (body and headlight lenses), silver "chrome", orange (indicators,
  lit lamps). Inventor colors: black 0.02, white 0.961, chrome 0.957, orange (0.867, 0.486, 0.059).
- Heights from the bed (z):
  - 0 to 1.5: black backing plate under the whole silhouette.
  - 1.5 to 3.0: white body sits on the backing; 3.0 is the main face of the keychain
    (hood lip up to 3.2, lower-apron vent strips 2.8).
  - Pockets 0.5 deep (floor 2.5) hold lights and headlight bezels, finishing flush at 3.0.
  - Chrome trim stands 0.5 proud: grille surround 3.0 to 3.5; grille bars 2.7 to 3.2.
  - Bumper strip (black) is the highest part at 3.7; the plate bracket (chrome) reaches 3.7.
  - Black shows through slots cut in the white body for vents.
  - Grille openings are through-holes (see-through).
- Keyring tab: black, on the left, full 3.0 thick, Ø4 hole, R4 rounded end, R3.5 fillets
  where it meets the body; hole center about 4 mm outside the body edge, at mid height of the bumper line.
- The license plate is not modeled: the owner adds it from a Bambu Studio template.
- Smallest features in the original: about 0.4 mm slots and 0.5 mm wide trim lines.

## Making a new car

1. Get a straight-on front photo (or SVG/DXF outlines) from the owner. Do not invent
   a car's face from memory; ask for a reference.
2. Write `cars/<car>/car.py`: silhouette and keyring tab, then body, pockets, inlays and
   trim, following the heights above. Scale the car to about 63 mm wide.
3. Run `python tools/build.py cars/<car>/car.py`, look at `out/preview.png`, compare it
   with the photo and iterate.
4. Leave real brand logos as a plain badge area unless the owner asks otherwise.
5. Commit the car folder including `out/` so the owner can download the files from GitHub.

## Printing

In Bambu Studio, import the STEP (or select all of a car's STLs together) and accept "load
as a single object with multiple parts"; then assign one filament per part.
