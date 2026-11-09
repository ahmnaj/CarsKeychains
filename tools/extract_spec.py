"""Turn a multi-body keychain STEP (like Ahmad's Inventor exports) into a layer spec.

Usage: python tools/extract_spec.py input.stp output.json --name mercedes_w124

Every solid is treated as a height field: each upward-facing flat face
becomes a layer from the solid's bottom up to that face. Part colors are
read from the STEP; heights are shifted so the keychain's bottom is z=0.
"""

import argparse
import json
import re
import sys

import cadquery as cq
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.Quantity import Quantity_Color
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label, TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool


def read_parts(path):
    """Yield (part_name, rgb, cq.Solid) for every solid, with occurrence colors applied."""
    doc = TDocStd_Document(TCollection_ExtendedString("doc"))
    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True)
    reader.SetNameMode(True)
    if reader.ReadFile(path) != 1:
        sys.exit(f"cannot read {path}")
    reader.Transfer(doc)
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colors = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

    def name(label):
        attr = TDataStd_Name()
        return attr.Get().ToExtString() if label.FindAttribute(TDataStd_Name.GetID_s(), attr) else ""

    def color(label):
        c = Quantity_Color()
        for t in (XCAFDoc_ColorType.XCAFDoc_ColorSurf, XCAFDoc_ColorType.XCAFDoc_ColorGen):
            if colors.GetColor_s(label, t, c):
                return (c.Red(), c.Green(), c.Blue())
        return None

    def shape_color(shape):
        c = Quantity_Color()
        for t in (XCAFDoc_ColorType.XCAFDoc_ColorSurf, XCAFDoc_ColorType.XCAFDoc_ColorGen):
            if colors.GetColor(shape, t, c):
                return (c.Red(), c.Green(), c.Blue())
        return None

    out = []

    def walk(label, loc, part, rgb):
        if shapes.IsReference_s(label):
            ref = TDF_Label()
            shapes.GetReferredShape_s(label, ref)
            walk(ref, loc * shapes.GetLocation_s(label), part, color(label) or rgb)
            return
        nm = name(label)
        if nm and nm not in ("SOLID", "COMPOUND"):
            part = nm
        rgb = color(label) or rgb
        if shapes.IsAssembly_s(label):
            seq = TDF_LabelSequence()
            shapes.GetComponents_s(label, seq)
            for i in range(1, seq.Length() + 1):
                walk(seq.Value(i), loc, part, rgb)
            return
        shape = cq.Shape.cast(shapes.GetShape_s(label))
        for solid in shape.Solids():
            out.append((part, shape_color(solid.wrapped) or rgb, solid.moved(cq.Location(loc))))

    roots = TDF_LabelSequence()
    shapes.GetFreeShapes(roots)
    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i), TopLoc_Location(), "", None)
    return out


def inventor_part_colors(path):
    """Map part name -> sRGB from Inventor's per-occurrence color overrides.

    Inventor stores part colors as CONTEXT_DEPENDENT_OVER_RIDING_STYLED_ITEM
    entries, which OpenCascade's reader ignores, so follow them by hand:
    override -> style -> ... -> COLOUR_RGB, and override -> shape
    representation -> product name.
    """
    text = open(path, errors="replace").read().replace("\n", "")
    ents = dict(re.findall(r"#(\d+)=([^;]*);", text))
    refs = lambda k: re.findall(r"#(\d+)", ents.get(k, ""))

    def rgb(k, depth=0):
        body = ents.get(k, "")
        if body.startswith("COLOUR_RGB"):
            return [float(v) for v in re.findall(r"[-\d.]+(?:E[-+]?\d+)?", body.split(",", 1)[1])][:3]
        if depth > 12:
            return None
        for r in refs(k):
            found = rgb(r, depth + 1)
            if found:
                return found
        return None

    rep_to_product = {}
    for k, body in ents.items():
        if body.startswith("SHAPE_DEFINITION_REPRESENTATION"):
            pds, rep = refs(k)[:2]
            pd = refs(pds)[0]
            pdf = refs(pd)[0]
            prod = refs(pdf)[0]
            m = re.match(r"PRODUCT\('([^']*)'", ents.get(prod, ""))
            if m:
                rep_to_product[rep] = m.group(1)
    colors = {}
    for k, body in ents.items():
        if body.startswith("CONTEXT_DEPENDENT_OVER_RIDING_STYLED_ITEM"):
            style, rep = refs(k)[0], refs(k)[1]
            if rep in rep_to_product:
                colors[rep_to_product[rep]] = rgb(style)
    return colors


def wire_points(wire, tol=0.02):
    pts = []
    explorer = BRepTools_WireExplorer(wire.wrapped)
    while explorer.More():
        edge = cq.Edge(explorer.Current())
        n = 1 if edge.geomType() == "LINE" else max(2, int(edge.Length() / 0.25))
        params = [i / n for i in range(n + 1)]
        p = [edge.positionAt(t) for t in params]
        if explorer.Orientation() == 1:  # TopAbs_REVERSED
            p.reverse()
        for v in p[:-1]:
            pts.append([round(v.x, 3), round(v.y, 3)])
        explorer.Next()
    return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step")
    ap.add_argument("out")
    ap.add_argument("--name", required=True)
    args = ap.parse_args()

    parts = read_parts(args.step)
    overrides = inventor_part_colors(args.step)
    z_min = min(s.BoundingBox().zmin for _, _, s in parts)
    palette, color_names, layers = {}, {}, []
    for part, rgb, solid in parts:
        rgb = overrides.get(part) or rgb
        key = tuple(round(c, 3) for c in rgb) if rgb else (0.5, 0.5, 0.5)
        if key not in color_names:
            color_names[key] = f"color{len(color_names) + 1}"
            palette[color_names[key]] = list(key)
        bottom = solid.BoundingBox().zmin
        for face in solid.Faces():
            if face.geomType() != "PLANE" or face.normalAt().z < 0.999:
                continue
            top = face.Center().z
            if top - bottom < 1e-3:
                continue
            layers.append({
                "name": part,
                "color": color_names[key],
                "z": [round(bottom - z_min, 3), round(top - z_min, 3)],
                "outline": wire_points(face.outerWire()),
                "holes": [wire_points(w) for w in face.innerWires()],
            })
    spec = {"name": args.name, "colors": palette, "layers": layers}
    with open(args.out, "w") as f:
        json.dump(spec, f, separators=(",", ":"))
    print(f"{len(layers)} layers, colors: {palette}")


if __name__ == "__main__":
    main()
