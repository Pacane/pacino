#!/usr/bin/env python3
"""Draw the underside wiring guide for the per-key PCB build: boards, pads, floor pillars and example
row/column wires, and check that no wire crosses a pillar. Reads the layout from keyboard.scad's
`part="info"` echo. Output: docs/wiring_guide.svg (+ .png if rsvg-convert is available).

Usage: tools/wiring_guide.py [-o outdir] [-D ...openscad overrides...]
"""
import math, re, subprocess, sys, os, shutil

OPENSCAD = shutil.which("openscad") or "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
args = sys.argv[1:]
outdir = "docs"
if "-o" in args:
    i = args.index("-o"); outdir = args[i + 1]; del args[i:i + 2]
out = subprocess.run([OPENSCAD, "-D", 'part="info"', *args, "-o", "/tmp/_wg.stl", "keyboard.scad"],
                     capture_output=True, text=True).stderr
info = "".join(l.replace("ECHO: ", "") for l in out.splitlines() if l.startswith("ECHO: "))
def arr(name):
    m = re.search(name + r' = (\[.*?\])(?=, [a-z_]+ =|$)', info); return eval(m.group(1))
keys = arr("keys")                       # [x, y, rot, u]
post_l, post_d = arr("post")             # pillar [length along edge, depth]
post_x = arr("post_x")[0] if isinstance(arr("post_x"), list) else float(re.search(r'post_x = ([-\d.]+)', info).group(1))
P = 19.05

# amoeba-king pads in the board frame (KiCad coords with y flipped), mm from centre
ROW_R = [(7.47, y) for y in (1.775, 3.045, 4.315, 5.585)]     # right-edge ROW pads
ROW_L = [(-7.49, y) for y in (1.775, 3.045, 4.315, 5.585)]    # left-edge ROW pads
COL_T = [(x, 7.87) for x in (-0.505, 0.765, 2.035, 3.305)]    # top-edge COL pads
COL_B = [(x, -8.1) for x in (-0.505, 0.765, 2.035, 3.305)]    # bottom-edge COL pads
LED = [(-3.76, 7.87), (-3.76, -8.1)]
def tf(k, p):  # board frame -> keyboard frame
    a = math.radians(k[2]); return (k[0] + p[0]*math.cos(a) - p[1]*math.sin(a), k[1] + p[0]*math.sin(a) + p[1]*math.cos(a))
def rect(k, cx, cy, w, h):  # rectangle in board frame -> polygon in keyboard frame
    return [tf(k, (cx + sx*w/2, cy + sy*h/2)) for sx, sy in ((-1,-1),(1,-1),(1,1),(-1,1))]

pillars = [rect(k, sx*post_x, sy*(P/2 - post_d/2), post_l, post_d) for k in keys for sx in (-1,1) for sy in (-1,1)]

# --- example matrix: columns = vertical chains of grid keys; rows = same row index across columns
#     (rows counted from the top, so extra keys below the bottom row are row -1); thumbs chained as
#     their own row and hung on the inner columns.  Every wire leaves its pad perpendicular to the
#     board edge for LEAD mm before heading off, so it never runs along an edge into a pillar.
LEAD = 3.0
def pad_out(k, pad):  # pad point and a point LEAD mm outward from the board edge
    nx, ny = (math.copysign(1, pad[0]), 0) if abs(pad[0]) > abs(pad[1]) else (0, math.copysign(1, pad[1]))
    return tf(k, pad), tf(k, (pad[0] + nx*LEAD, pad[1] + ny*LEAD))
def wire(kind, ka, pa, kb, pb, lead=True):
    a, a2 = pad_out(ka, pa); b, b2 = pad_out(kb, pb)
    return (kind, [a, a2, b2, b] if lead else [a, b])
grid = [k for k in keys if k[2] == 0]
thumbs = sorted([k for k in keys if k[2] != 0], key=lambda k: k[0])
cols = {}
for k in grid: cols.setdefault(round(k[0], 2), []).append(k)
xs = sorted(cols)
wires = []
for x in xs:
    ks = sorted(cols[x], key=lambda k: -k[1])          # top first
    for a, b in zip(ks, ks[1:]):
        wires.append(wire("col", a, COL_B[1], b, COL_T[1]))
rowidx = {}
for x in xs:
    for i, k in enumerate(sorted(cols[x], key=lambda k: -k[1])):
        rowidx[(round(k[0],2), round(k[1],2))] = i           # 0 = top row
for x1, x2 in zip(xs, xs[1:]):
    for a in cols[x1]:
        for b in cols[x2]:
            if rowidx[(round(a[0],2), round(a[1],2))] == rowidx[(round(b[0],2), round(b[1],2))]:
                wires.append(wire("row", a, ROW_R[1], b, ROW_L[1], lead=False))   # straight across: the boards touch
# thumbs: their ROW pads on the edge that faces the main block, chained with lead-outs
for a, b in zip(thumbs, thumbs[1:]):
    wires.append(wire("row", a, ROW_R[1], b, ROW_R[1]))
for i, t in enumerate(thumbs):
    cx = xs[max(0, len(xs) - len(thumbs) + i)]
    bottom = min(cols[cx], key=lambda k: k[1])
    wires.append(wire("col", t, COL_T[1], bottom, COL_B[1]))   # thumb's COL pad (edge facing the columns) up to the column's bottom pad

# --- router: A* on a 1 mm grid, obstacles = pillars dilated by the wire radius, then line-of-sight shortcutting
import heapq
R = 0.9
def seg_poly_dist(p, q, poly):
    def pt_seg(pt, a, b):
        ax, ay = a; bx, by = b; px, py = pt; dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
        t = max(0, min(1, ((px-ax)*dx + (py-ay)*dy) / L2)) if L2 else 0
        return math.hypot(px-ax-t*dx, py-ay-t*dy)
    def inside(pt):
        c = False
        for i in range(len(poly)):
            (x1,y1),(x2,y2) = poly[i], poly[(i+1)%len(poly)]
            if (y1>pt[1]) != (y2>pt[1]) and pt[0] < x1 + (pt[1]-y1)*(x2-x1)/(y2-y1): c = not c
        return c
    if inside(p) or inside(q): return 0
    def cross(o, u, v): return (u[0]-o[0])*(v[1]-o[1]) - (u[1]-o[1])*(v[0]-o[0])
    d = 1e9
    for i in range(len(poly)):
        a, b = poly[i], poly[(i+1)%len(poly)]
        if (cross(p,q,a) * cross(p,q,b) < 0) and (cross(a,b,p) * cross(a,b,q) < 0): return 0
        d = min(d, pt_seg(a, p, q), pt_seg(b, p, q), pt_seg(p, a, b), pt_seg(q, a, b))
    return d
def clear(p, q): return all(seg_poly_dist(p, q, pl) >= R for pl in pillars)
GX0, GY0 = math.floor(min(p[0] for pl in pillars for p in pl)) - 15, math.floor(min(p[1] for pl in pillars for p in pl)) - 15
GW, GH = math.ceil(max(p[0] for pl in pillars for p in pl)) + 15 - GX0, math.ceil(max(p[1] for pl in pillars for p in pl)) + 15 - GY0
blocked = set()
for pl in pillars:
    xs_, ys_ = [p[0] for p in pl], [p[1] for p in pl]
    for gx in range(math.floor(min(xs_)-R-1)-GX0, math.ceil(max(xs_)+R+1)-GX0+1):
        for gy in range(math.floor(min(ys_)-R-1)-GY0, math.ceil(max(ys_)+R+1)-GY0+1):
            pt = (GX0+gx, GY0+gy)
            if seg_poly_dist(pt, pt, pl) < R: blocked.add((gx, gy))
def route(a, b):
    if clear(a, b): return [a, b]
    sa, sb = (round(a[0])-GX0, round(a[1])-GY0), (round(b[0])-GX0, round(b[1])-GY0)
    h = lambda n: math.hypot(n[0]-sb[0], n[1]-sb[1])
    pq = [(h(sa), 0, sa)]; came = {sa: None}; cost = {sa: 0}
    while pq:
        _, g, n = heapq.heappop(pq)
        if n == sb: break
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if not dx and not dy: continue
                m = (n[0]+dx, n[1]+dy)
                if m in blocked or not (0 <= m[0] <= GW and 0 <= m[1] <= GH): continue
                ng = g + math.hypot(dx, dy)
                if ng < cost.get(m, 1e9):
                    cost[m] = ng; came[m] = n; heapq.heappush(pq, (ng + h(m), ng, m))
    if sb not in came: return [a, b]
    path = []; n = sb
    while n: path.append((n[0]+GX0, n[1]+GY0)); n = came[n]
    path = [a] + path[::-1][1:-1] + [b]
    out = [path[0]]; i = 0                     # shortcut
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and not clear(path[i], path[j]): j -= 1
        out.append(path[j]); i = j
    return out
wires = [(kind, route(pts[0], pts[-1]) if len(pts) == 2 else [pts[0]] + route(pts[1], pts[-2]) + [pts[-1]]) for kind, pts in wires]
clashes = []
for kind, pts in wires:
    for p1, p2 in zip(pts, pts[1:]):
        dmin = min(seg_poly_dist(p1, p2, pl) for pl in pillars)
        if dmin < 0.8: clashes.append((kind, p1, p2, dmin))
print("%d wires, %d pillars, %d clashes after routing" % (len(wires), len(pillars), len(clashes)))
for c in clashes: print("  CLASH %s (%.1f,%.1f)-(%.1f,%.1f) %.2f mm" % (c[0], *c[1], *c[2], c[3]))

# --- SVG (underside view: mirrored in x)
allx = [p[0] for k in keys for p in rect(k, 0, 0, P, P)]; ally = [p[1] for k in keys for p in rect(k, 0, 0, P, P)]
x0, x1, y0, y1 = min(allx)-6, max(allx)+6, min(ally)-6, max(ally)+6
S = 8  # px per mm
W, H = (x1-x0)*S, (y1-y0)*S + 60
def X(x): return (x1 - x) * S          # mirrored: underside view
def Y(y): return (y1 - y) * S
def poly(pts, **kw):
    return '<polygon points="%s" %s/>' % (" ".join("%.1f,%.1f" % (X(x), Y(y)) for x, y in pts), " ".join('%s="%s"' % (k.replace("_","-"), v) for k, v in kw.items()))
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
       '<rect width="100%" height="100%" fill="#f4f1ea"/>']
for k in keys:
    svg.append(poly(rect(k, 0, 0, P, P), fill="#2f7d4e", stroke="#1c4a2e", stroke_width=1))     # board
    svg.append(poly(rect(k, 0, 0, 14, 14), fill="none", stroke="#6fbf8e", stroke_width=0.8, stroke_dasharray="3,2"))  # switch body
    svg.append(poly(rect(k, 0, 0, 10.9, 5.6), fill="#1c4a2e"))                                 # socket
    for pl in (ROW_R, ROW_L, COL_T, COL_B, LED):
        for p in pl:
            x, y = tf(k, p); svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#e8c547"/>' % (X(x), Y(y), 0.6*S))
for pl in pillars: svg.append(poly(pl, fill="#d9534f", fill_opacity="0.85"))
for kind, pts in wires:
    col = "#1f77d4" if kind == "col" else "#ff7f0e"
    svg.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round"/>' % (" ".join("%.1f,%.1f" % (X(x), Y(y)) for x, y in pts), col, 0.8*S))
ly = H - 40
svg.append('<text x="10" y="%d" font-family="sans-serif" font-size="14">Underside view (case off, plate upside down). Red = floor pillars (never run a wire over one). Yellow = pads. Blue = column wires, orange = row wires (example matrix).</text>' % (ly))
svg.append('<text x="10" y="%d" font-family="sans-serif" font-size="14">Leave the pads straight out: column wires along the board centre line, row wires straight across the column gap. Left half shown; the right half is the mirror image.</text>' % (ly+20))
svg.append('</svg>')
os.makedirs(outdir, exist_ok=True)
open(os.path.join(outdir, "wiring_guide.svg"), "w").write("\n".join(svg))
if shutil.which("rsvg-convert"):
    subprocess.run(["rsvg-convert", "-o", os.path.join(outdir, "wiring_guide.png"), os.path.join(outdir, "wiring_guide.svg")])
print("wrote %s/wiring_guide.svg" % outdir + (" and .png" if shutil.which("rsvg-convert") else ""))
