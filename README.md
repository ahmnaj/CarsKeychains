# CarsKeychains

Multi-color car-front keychains for Bambu printers, generated from a layer spec
in the style of the original Inventor Mercedes (`reference/Mercedes1.stp`).

- Ready files for each car: `cars/<car>/out/` (`<car>.step` with one part per filament, one STL per color, `preview.png`).
- How it works, the house style and how to add a car: see [CLAUDE.md](CLAUDE.md).

```
pip install -r requirements.txt
python tools/build.py cars/mercedes_w124/spec.json
```
