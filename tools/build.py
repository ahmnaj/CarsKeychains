"""Build a car keychain: spec -> STEP (one part per filament) + STLs + preview.

Usage:
  python tools/build.py cars/<car>/spec.json     # extracted/plain JSON spec
  python tools/build.py cars/<car>/car.py        # authored spec, must define spec()

Output goes to cars/<car>/out/.
"""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from keychain.geometry import build, export, report  # noqa: E402
import preview  # noqa: E402


def load(path):
    path = Path(path)
    if path.suffix == ".py":
        mod_spec = importlib.util.spec_from_file_location("car", path)
        mod = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(mod)
        return mod.spec()
    return json.loads(path.read_text())


def main(path):
    spec = load(path)
    bodies = build(spec)
    print(report(bodies))
    out = Path(path).parent / "out"
    step = export(spec, bodies, out)
    preview.main(str(step), str(out / "preview.png"))
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1])
