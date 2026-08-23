"""Convert an OpenSCAD .csg export to STEP using FreeCAD's OpenSCAD importer.

Run with FreeCAD's own interpreter (not system python).  freecadcmd tries to open every CLI
argument as a document, so the paths are passed through the environment instead:
  CSG_IN=in.csg STEP_OUT=out.step /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd tools/csg2step.py

FreeCAD rebuilds the CSG tree as real B-rep (Part workbench) features, so the STEP has true
planar faces and cylindrical holes -- directly editable in Fusion 360 (press/pull, fillets...).
"""
import os
import sys

import FreeCAD  # noqa: F401
import importCSG

src, dst = os.environ.get("CSG_IN"), os.environ.get("STEP_OUT")
if not src or not dst:
    sys.exit("usage: CSG_IN=in.csg STEP_OUT=out.step freecadcmd csg2step.py")

doc = FreeCAD.newDocument("csg")
importCSG.insert(os.path.abspath(src), doc.Name)   # prints transient "Recompute failed" noise; harmless
doc.recompute()

bad = [o.Name for o in doc.Objects if "Invalid" in o.State or "Touched" in o.State]
if bad:
    sys.exit("objects failed to recompute: %s" % ", ".join(bad))

# Top-level objects only (the importer also leaves a few stray 2D primitives at root level).
roots = [o for o in doc.Objects if hasattr(o, "Shape") and not o.InList]
shapes = [o.Shape for o in roots if not o.Shape.isNull() and o.Shape.Solids]
if not shapes:
    sys.exit("no shapes produced from %s" % src)
shape = shapes[0] if len(shapes) == 1 else shapes[0].fuse(shapes[1:])
shape = shape.removeSplitter()
if not shape.isValid():
    sys.exit("resulting shape is not valid")
shape.exportStep(os.path.abspath(dst))
print("STEP %s: %d solid(s), %d faces, volume %.1f mm^3" % (os.path.basename(dst), len(shape.Solids), len(shape.Faces), shape.Volume))
