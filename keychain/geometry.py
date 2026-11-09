"""Build a multi-color keychain from a layer spec.

A spec is a list of layers. Each layer is a 2D region (outer outline plus
optional holes, in mm, front view: +X right, +Y up) extruded between two
heights and assigned a filament color. Layers are applied in order like
paint: a later layer carves its volume out of every earlier layer, so the
final per-color bodies never overlap and fit together exactly.
"""

import json
import math
from pathlib import Path

import cadquery as cq


def load_spec(path):
    with open(path) as f:
        return json.load(f)


def simplify(points, tol=0.01):
    """Douglas-Peucker: drop points that sit within tol (mm) of a straight run."""
    if len(points) < 4:
        return points

    def dp(pts):
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1e-12
        far, idx = 0.0, 0
        for i in range(1, len(pts) - 1):
            d = abs(dy * (pts[i][0] - x0) - dx * (pts[i][1] - y0)) / length
            if d > far:
                far, idx = d, i
        if far <= tol:
            return [pts[0], pts[-1]]
        return dp(pts[: idx + 1])[:-1] + dp(pts[idx:])

    # split the closed loop at its two most distant points so DP has fixed ends
    far = max(range(len(points)), key=lambda i: math.dist(points[0], points[i]))
    loop = points + [points[0]]
    return dp(loop[: far + 1])[:-1] + dp(loop[far:])[:-1]


def _region(outline, holes, z0, z1):
    def wire(points):
        return cq.Wire.makePolygon([cq.Vector(x, y, z0) for x, y in simplify(points)], close=True)

    face = cq.Face.makeFromWires(wire(outline), [wire(h) for h in holes or []])
    return cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0))


# Neighbouring parts traced separately never line up to the last micron, so
# booleans run with a small fuzzy tolerance. OpenCascade is touchy about the
# exact value, so build() tries these in turn until every body checks out.
FUZZY_TRIES = (1e-5, 1e-4, 0.0, 1e-3)


def _bool(op, a, b, fuzzy):
    """Fuzzy boolean so near-coincident walls between colors don't break OpenCascade."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
    from OCP.TopTools import TopTools_ListOfShape
    algo = {"cut": BRepAlgoAPI_Cut, "fuse": BRepAlgoAPI_Fuse}[op]()
    args, tools = TopTools_ListOfShape(), TopTools_ListOfShape()
    args.Append(a.wrapped)
    for t in b if isinstance(b, list) else [b]:
        tools.Append(t.wrapped)
    algo.SetArguments(args)
    algo.SetTools(tools)
    algo.SetFuzzyValue(fuzzy)
    algo.SetRunParallel(True)
    algo.Build()
    if not algo.IsDone():
        raise RuntimeError(f"{op} failed")
    return cq.Shape.cast(algo.Shape())


def layer_solid(layer, fuzzy=FUZZY_TRIES[0]):
    z0, z1 = layer["z"]
    regions = layer.get("regions") or [layer]
    parts = [_region(r["outline"], r.get("holes"), z0, z1) for r in regions]
    return parts[0] if len(parts) == 1 else _bool("fuse", parts[0], parts[1:], fuzzy)


def build(spec):
    """Return {color_name: cq.Shape} with non-overlapping bodies."""
    # Upper bound per color: what it would be if nothing carved into it.
    limits = {}
    for layer in spec["layers"]:
        limits[layer["color"]] = limits.get(layer["color"], 0.0) + layer_solid(layer).Volume()
    problems = []
    for fuzzy in FUZZY_TRIES:
        try:
            bodies = _build(spec, fuzzy)
        except RuntimeError as e:
            problems.append(f"fuzzy={fuzzy}: {e}")
            continue
        bad = [c for c in limits
               if c not in bodies or not bodies[c].isValid() or not 0 < bodies[c].Volume() <= limits[c] * 1.001]
        if not bad:
            return bodies
        problems.append(f"fuzzy={fuzzy}: bad bodies {bad}")
    raise RuntimeError("could not build a clean model:\n  " + "\n  ".join(problems))


def _build(spec, fuzzy):
    # Consecutive layers of the same color are fused first, so the expensive
    # cuts happen once per color change instead of once per layer.
    groups = []
    for layer in spec["layers"]:
        if groups and groups[-1][0] == layer["color"]:
            groups[-1][1].append(layer)
        else:
            groups.append((layer["color"], [layer]))

    bodies = {}
    for color, layers in groups:
        solids = [layer_solid(l, fuzzy) for l in layers]
        new = solids[0] if len(solids) == 1 else _bool("fuse", solids[0], solids[1:], fuzzy)
        for other in list(bodies):
            if other != color:
                bodies[other] = _bool("cut", bodies[other], new, fuzzy)
        bodies[color] = _bool("fuse", bodies[color], new, fuzzy) if color in bodies else new
    return {c: b.clean() for c, b in bodies.items()}


def export(spec, bodies, out_dir):
    """Write <name>.step (one colored part per filament) and one STL per color."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    name = spec["name"]
    assy = cq.Assembly(name=name)
    for color, body in bodies.items():
        rgb = spec["colors"][color]
        assy.add(body, name=color, color=cq.Color(*rgb))
        cq.exporters.export(body, str(out / f"{name}_{color}.stl"), tolerance=0.01, angularTolerance=0.1)
    assy.save(str(out / f"{name}.step"))
    return out / f"{name}.step"


def report(bodies):
    lines = []
    for color, body in bodies.items():
        bb = body.BoundingBox()
        lines.append(f"{color:10s} vol={body.Volume():8.1f} mm3  "
                     f"x[{bb.xmin:.2f},{bb.xmax:.2f}] y[{bb.ymin:.2f},{bb.ymax:.2f}] z[{bb.zmin:.2f},{bb.zmax:.2f}]")
    return "\n".join(lines)
