#!/usr/bin/env python3
"""Print the outline of an OpenSCAD-exported SVG as an OpenSCAD point list.

OpenSCAD's SVG export writes one <path> with 'M x,y L x,y ... z' subpaths and Y negated.
Used by build.sh to hand FreeCAD a plain polygon instead of a chain of 2D offsets
(OCC's 2D offsetting is unreliable on fused shapes; Clipper's in OpenSCAD is not).
"""
import re
import sys

src = open(sys.argv[1]).read()
d = " ".join(re.findall(r'<path[^>]*\bd="([^"]*)"', src, re.S))
subpaths = []
for sub in re.split(r'\bM\b', d):
    pts = [(float(x), -float(y)) for x, y in re.findall(r'([-\d.eE+]+),([-\d.eE+]+)', sub)]
    if len(pts) >= 3:
        subpaths.append(pts)
if not subpaths:
    sys.exit("no path data in %s" % sys.argv[1])
subpaths.sort(key=len, reverse=True)
if len(subpaths) > 1:
    print("warning: %d subpaths, using the longest (holes are dropped)" % len(subpaths), file=sys.stderr)
outer = subpaths[0]
if outer[0] == outer[-1]:
    outer = outer[:-1]
print("[" + ",".join("[%g,%g]" % p for p in outer) + "]")
