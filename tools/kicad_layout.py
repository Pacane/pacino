#!/usr/bin/env python3
"""Extract a keyboard layout from a KiCad 7/8 .kicad_pcb and emit an OpenSCAD layout file.

Usage:  kicad_layout.py board.kicad_pcb [--prefix NAME] > layouts/NAME.scad

Emits (all in mm, X right, Y up, origin = centre of the bottom-left switch):
  NAME_keys        = [[x, y, rot_deg, width_u], ...]   one entry per SW* footprint
  NAME_holes       = [[x, y], ...]                     mounting holes (2.0-3.5 mm drills, refs h*/H*/MH*)
  NAME_mcu         = [x, y, rot_deg, w, l]             U1 footprint centre + outline size
  NAME_pcb_outline = [[x, y], ...]                     closed Edge.Cuts polygon (arcs discretised)
"""
import math
import re
import sys

TOL = 0.05  # mm, for chaining outline segments


def footprints(src):
    """Yield (lib, ref, at(x,y,rot), body) for each top-level footprint."""
    for lib, body in re.findall(r'\n\t\(footprint "([^"]+)"\n(.*?)\n\t\)(?=\n)', src, re.S):
        ref = re.search(r'\(property "Reference" "([^"]+)"', body)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', body)
        x, y, rot = at.groups()
        yield lib, (ref.group(1) if ref else "?"), (float(x), float(y), float(rot or 0)), body


def gfx_bbox(body):
    pts = re.findall(r'\((?:start|end) ([-\d.]+) ([-\d.]+)\)', body)
    if not pts:
        return None
    xs = [float(a) for a, _ in pts]
    ys = [float(b) for _, b in pts]
    return min(xs), max(xs), min(ys), max(ys)


def arc_points(p0, pm, p1, n=None):
    """Discretise a 3-point arc (start, mid, end)."""
    (x0, y0), (xm, ym), (x1, y1) = p0, pm, p1
    d = 2 * (x0 * (ym - y1) + xm * (y1 - y0) + x1 * (y0 - ym))
    if abs(d) < 1e-9:
        return [p0, p1]
    ux = ((x0**2 + y0**2) * (ym - y1) + (xm**2 + ym**2) * (y1 - y0) + (x1**2 + y1**2) * (y0 - ym)) / d
    uy = ((x0**2 + y0**2) * (x1 - xm) + (xm**2 + ym**2) * (x0 - x1) + (x1**2 + y1**2) * (xm - x0)) / d
    r = math.hypot(x0 - ux, y0 - uy)
    a0 = math.atan2(y0 - uy, x0 - ux)
    am = math.atan2(ym - uy, xm - ux)
    a1 = math.atan2(y1 - uy, x1 - ux)
    # choose sweep direction that passes through the mid point
    def norm(a):
        return a % (2 * math.pi)
    ccw = norm(am - a0) < norm(a1 - a0)
    sweep = norm(a1 - a0) if ccw else -norm(a0 - a1)
    if n is None:
        n = max(4, int(abs(sweep) * r / 0.5))  # ~0.5 mm segments
    return [(ux + r * math.cos(a0 + sweep * i / n), uy + r * math.sin(a0 + sweep * i / n)) for i in range(n + 1)]


def edge_segments(src):
    """Return list of polylines (lists of points) for every Edge.Cuts graphic."""
    segs = []
    for kind, body in re.findall(r'\n\t\((gr_line|gr_arc|gr_rect|gr_circle|gr_poly)\n(.*?)\n\t\)', src, re.S):
        if '(layer "Edge.Cuts")' not in body:
            continue
        g = lambda k: tuple(map(float, re.search(r'\(%s ([-\d.]+) ([-\d.]+)\)' % k, body).groups()))
        if kind == "gr_line":
            segs.append([g("start"), g("end")])
        elif kind == "gr_arc":
            segs.append(arc_points(g("start"), g("mid"), g("end")))
        elif kind == "gr_rect":
            (x0, y0), (x1, y1) = g("start"), g("end")
            segs.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
        elif kind == "gr_circle":
            c, e = g("center"), g("end")
            r = math.hypot(e[0] - c[0], e[1] - c[1])
            n = max(16, int(2 * math.pi * r / 0.5))
            segs.append([(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)])
        elif kind == "gr_poly":
            pts = re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', body)
            segs.append([tuple(map(float, p)) for p in pts] + [tuple(map(float, pts[0]))])
    return segs


def chain(segs):
    """Chain segments end-to-end into closed loops; return the longest loop."""
    segs = [list(s) for s in segs]
    loops = []
    while segs:
        loop = segs.pop(0)
        progress = True
        while progress:
            progress = False
            for i, s in enumerate(segs):
                if math.dist(loop[-1], s[0]) < TOL:
                    loop += s[1:]
                elif math.dist(loop[-1], s[-1]) < TOL:
                    loop += s[-2::-1]
                elif math.dist(loop[0], s[-1]) < TOL:
                    loop = s[:-1] + loop
                elif math.dist(loop[0], s[0]) < TOL:
                    loop = s[::-1][:-1] + loop
                else:
                    continue
                segs.pop(i)
                progress = True
                break
        loops.append(loop)
    loops.sort(key=len, reverse=True)
    best = loops[0]
    if math.dist(best[0], best[-1]) < TOL:
        best = best[:-1]
    # drop consecutive duplicates
    out = [best[0]]
    for p in best[1:]:
        if math.dist(p, out[-1]) > 1e-3:
            out.append(p)
    return out, len(loops)


def fmt(v):
    return ("%.3f" % v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def main():
    args = sys.argv[1:]
    prefix = "pcb"
    if "--prefix" in args:
        i = args.index("--prefix")
        prefix = args[i + 1]
        del args[i:i + 2]
    src = open(args[0]).read()

    keys, holes, mcu = [], [], None
    for lib, ref, (x, y, rot), body in footprints(src):
        if re.fullmatch(r"(SW|K|MX|S)\d+", ref):
            width = 1.5 if "1.5u" in lib.lower() else 1.0
            keys.append((ref, x, y, rot, width))
        elif re.fullmatch(r"(h|H|MH|H_)\d+", ref) or "MountingHole" in lib:
            drill = re.search(r'\(drill ([\d.]+)\)', body)
            if drill and 1.9 <= float(drill.group(1)) <= 3.6:
                holes.append((x, y, float(drill.group(1))))
        elif ref == "U1":
            bb = gfx_bbox(body)
            mcu = (x, y, rot, bb)

    if not keys:
        sys.exit("no SW* footprints found")

    # origin: bottom-left switch (min x, then max KiCad-y i.e. lowest on screen)
    ox = min(k[1] for k in keys)
    oy = max(k[2] for k in keys if abs(k[1] - ox) < 1.0)

    def tx(x, y):  # KiCad (y down) -> OpenSCAD (y up)
        return (x - ox, oy - y)

    keys.sort(key=lambda k: int(re.sub(r"\D", "", k[0]) or 0))
    outline, nloops = chain(edge_segments(src))

    print("// Generated by tools/kicad_layout.py from %s -- do not edit, re-run instead." % args[0])
    print("// Units: mm. X right, Y up. Origin = centre of %s (bottom-left switch)." % keys[0][0])
    print("// KiCad origin of this frame: (%s, %s)\n" % (fmt(ox), fmt(oy)))
    print("%s_keys = [  // [x, y, rot_deg, width_u]" % prefix)
    for ref, x, y, rot, w in keys:
        sx, sy = tx(x, y)
        # KiCad rotation is CCW on screen; 180 == 0 for a symmetric cutout
        srot = ((rot + 90) % 180) - 90
        print("  [%s, %s, %s, %s],  // %s" % (fmt(sx), fmt(sy), fmt(srot), fmt(w), ref))
    print("];\n")
    print("%s_holes = [  // [x, y]  (M2-ish mounting holes)" % prefix)
    for x, y, d in holes:
        sx, sy = tx(x, y)
        print("  [%s, %s],  // drill %s" % (fmt(sx), fmt(sy), fmt(d)))
    print("];\n")
    if mcu:
        x, y, rot, bb = mcu
        cx, cy = tx(x + (bb[0] + bb[1]) / 2, y + (bb[2] + bb[3]) / 2)
        print("%s_mcu = [%s, %s, %s, %s, %s];  // [cx, cy, rot, width, length]  USB end = +Y before rotation"
              % (prefix, fmt(cx), fmt(cy), fmt(rot), fmt(bb[1] - bb[0]), fmt(bb[3] - bb[2])))
        # USB end is the -y (top-of-screen) end of the footprint graphics
        ux, uy = tx(x + (bb[0] + bb[1]) / 2, y + bb[2])
        print("%s_usb = [%s, %s];  // board end where the USB connector sits\n" % (prefix, fmt(ux), fmt(uy)))
    print("%s_pcb_outline = [  // %d points, from Edge.Cuts (%d loop%s found, longest used)"
          % (prefix, len(outline), nloops, "" if nloops == 1 else "s"))
    for x, y in outline:
        sx, sy = tx(x, y)
        print("  [%s, %s]," % (fmt(sx), fmt(sy)))
    print("];")


if __name__ == "__main__":
    main()
