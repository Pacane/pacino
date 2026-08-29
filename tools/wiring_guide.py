#!/usr/bin/env python3
"""Draw the underside wiring guide for the per-key PCB build: the inner wall, the boards with their pads,
the floor pillars and wall bosses, the row/column matrix, the nice!nano with every pin named, and each
row/column chain's wire to its pin -- every wire routed clear of the pillars, the bosses and the wall,
and checked.  The pin numbers come from the shield (row-gpios in config/boards/shields/pacino/pacino.dtsi,
col-gpios in pacino_left.overlay), so the picture cannot drift from the firmware.  Reads the layout from
keyboard.scad's `part="info"` echo and the wall from `part="cavity_2d"`.
Output: docs/wiring_guide.svg (+ .png if rsvg-convert is available).

Usage: tools/wiring_guide.py [-o outdir] [-D ...openscad overrides...]
"""
import math, re, subprocess, sys, os, shutil, tempfile, heapq

OPENSCAD = shutil.which("openscad") or "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
SHIELD = "config/boards/shields/pacino"
args = sys.argv[1:]
outdir = "docs"
if "-o" in args:
    i = args.index("-o"); outdir = args[i + 1]; del args[i:i + 2]
tmp = tempfile.mkdtemp()
def scad(part, out):
    return subprocess.run([OPENSCAD, "-D", 'part="%s"' % part, *args, "-o", out, "keyboard.scad"],
                          capture_output=True, text=True).stderr
info = "".join(l.replace("ECHO: ", "") for l in scad("info", os.path.join(tmp, "info.stl")).splitlines() if l.startswith("ECHO: "))
scad("cavity_2d", os.path.join(tmp, "cavity.svg"))
def arr(name, default=None):
    m = re.search(r'\b' + name + r' = (\[.*?\])(?=, [a-z_]+ =|$)', info)
    return eval(m.group(1)) if m else default
keys = arr("keys")                       # [x, y, rot, u]
post_l, post_d = arr("post")             # pillar [length along edge, depth]
post_x = arr("post_x")[0]
holes = arr("holes", [])                 # wall bosses (case screws)
mcu = arr("mcu"); bay = arr("bay"); ctrl = arr("ctrl"); reset = arr("reset"); power = arr("power")
m = re.search(r'flipped = (\w+)', info); flipped = m.group(1) == "true" if m else True
m = re.search(r'boss_d = ([\d.]+)', info); boss_d = float(m.group(1)) if m else 6.0
P = 19.05

# the inner wall, from the cavity_2d export (one outer contour; any inner contours are islands)
contours = []
for d in re.findall(r'<path[^>]*\bd="([^"]*)"', open(os.path.join(tmp, "cavity.svg")).read(), re.S):
    for sub in re.split(r'[Mm]', d)[1:]:
        pts = [(float(x), -float(y)) for x, y in re.findall(r'([-\d.eE+]+),([-\d.eE+]+)', sub)]
        if len(pts) > 2: contours.append(pts)
def area(poly): return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))) / 2
contours.sort(key=lambda c: -abs(area(c)))
cavity, cav_holes = (contours[0], contours[1:]) if contours else (None, [])

# amoeba-king pads in the board frame (KiCad coords with y flipped), mm from centre
ROW_R = [(7.47, y) for y in (1.775, 3.045, 4.315, 5.585)]     # right-edge ROW pads
ROW_L = [(-7.49, y) for y in (1.775, 3.045, 4.315, 5.585)]    # left-edge ROW pads
COL_T = [(x, 7.87) for x in (-0.505, 0.765, 2.035, 3.305)]    # top-edge COL pads
COL_B = [(x, -8.1) for x in (-0.505, 0.765, 2.035, 3.305)]    # bottom-edge COL pads
LED = [(-3.76, 7.87), (-3.76, -8.1)]
def tf(k, p):  # board frame -> keyboard frame
    a = math.radians(k[2]); return (k[0] + p[0]*math.cos(a) - p[1]*math.sin(a), k[1] + p[0]*math.sin(a) + p[1]*math.cos(a))
def inv(k, p):  # keyboard frame -> board frame
    a = math.radians(k[2]); dx, dy = p[0] - k[0], p[1] - k[1]
    return (dx*math.cos(a) + dy*math.sin(a), -dx*math.sin(a) + dy*math.cos(a))
def rect(k, cx, cy, w, h):  # rectangle in board frame -> polygon in keyboard frame
    return [tf(k, (cx + sx*w/2, cy + sy*h/2)) for sx, sy in ((-1,-1),(1,-1),(1,1),(-1,1))]
def circ(c, r, n=16): return [(c[0] + r*math.cos(2*math.pi*i/n), c[1] + r*math.sin(2*math.pi*i/n)) for i in range(n)]

pillars = [rect(k, sx*post_x, sy*(P/2 - post_d/2), post_l, post_d) for k in keys for sx in (-1,1) for sy in (-1,1)]
bosses = [circ(h, boss_d / 2) for h in holes]
obstacles = pillars + bosses + cav_holes

# --- the nice!nano: 2 x 12 pads on 2.54, rows 15.24 apart, USB at local +y.  Mounted component side
#     down (mcu_flipped) the pads that are on the LEFT of the usual top-view pinout (1/TX ... 9) land on
#     the local +x edge; the underside view then shows the board exactly like that pinout drawing.
PM = {1: "1/TX", 2: "0/RX", 3: "GND", 4: "GND", 5: "2", 6: "3", 7: "4", 8: "5", 9: "6", 10: "7", 11: "8", 12: "9",
      13: "10", 14: "16", 15: "14", 16: "15", 17: "18", 18: "19", 19: "20", 20: "21", 21: "VCC", 22: "RST", 23: "GND", 24: "RAW/B+"}
pad_of = {int(v.split("/")[0]): n for n, v in PM.items() if v[0].isdigit()}   # pro_micro number -> pad
def pad_local(n):
    sx = (1 if n <= 12 else -1) * (1 if flipped else -1)
    return (sx * 7.62, 13.97 - 2.54 * ((n - 1) if n <= 12 else (24 - n)))
def pin_xy(n): return tf(mcu, pad_local(n))
def gpios(path, key):
    try: txt = open(path).read()
    except OSError: return []
    m = re.search(key + r'\s*=(.*?);', txt, re.S)
    return [int(n) for n in re.findall(r'pro_micro (\d+)', m.group(1))] if m else []
row_pins = gpios(os.path.join(SHIELD, "pacino.dtsi"), "row-gpios")
col_pins = gpios(os.path.join(SHIELD, "pacino_left.overlay"), "col-gpios")

# --- geometry: distances, the wall test
def pt_seg(pt, a, b):
    ax, ay = a; bx, by = b; px, py = pt; dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
    t = max(0, min(1, ((px-ax)*dx + (py-ay)*dy) / L2)) if L2 else 0
    return math.hypot(px-ax-t*dx, py-ay-t*dy)
def cross(o, u, v): return (u[0]-o[0])*(v[1]-o[1]) - (u[1]-o[1])*(v[0]-o[0])
def seg_seg_dist(p, q, a, b):
    if (cross(p,q,a) * cross(p,q,b) < 0) and (cross(a,b,p) * cross(a,b,q) < 0): return 0
    return min(pt_seg(a, p, q), pt_seg(b, p, q), pt_seg(p, a, b), pt_seg(q, a, b))
def inside(pt, poly):
    c = False
    for i in range(len(poly)):
        (x1,y1),(x2,y2) = poly[i], poly[(i+1)%len(poly)]
        if (y1>pt[1]) != (y2>pt[1]) and pt[0] < x1 + (pt[1]-y1)*(x2-x1)/(y2-y1): c = not c
    return c
def seg_poly_dist(p, q, poly):
    if inside(p, poly) or inside(q, poly): return 0
    return min(seg_seg_dist(p, q, poly[i], poly[(i+1)%len(poly)]) for i in range(len(poly)))
def bbox(pts): xs_, ys_ = zip(*pts); return (min(xs_), min(ys_), max(xs_), max(ys_))
def bb_hit(b1, b2, m): return not (b1[2] + m < b2[0] or b2[2] + m < b1[0] or b1[3] + m < b2[1] or b2[3] + m < b1[1])
obs = [(pl, bbox(pl)) for pl in obstacles]
cav_edges = [((cavity[i], cavity[(i+1) % len(cavity)]), bbox([cavity[i], cavity[(i+1) % len(cavity)]])) for i in range(len(cavity))] if cavity else []
_in = {}
def in_cavity(p):
    if not cavity: return True
    if p not in _in: _in[p] = inside(p, cavity)
    return _in[p]
R = 0.9   # wire radius + clearance
def clear(p, q):
    sb = bbox([p, q])
    for pl, b in obs:
        if bb_hit(sb, b, R) and seg_poly_dist(p, q, pl) < R: return False
    if not in_cavity(p) or not in_cavity(q): return False
    for e, b in cav_edges:
        if bb_hit(sb, b, R) and seg_seg_dist(p, q, *e) < R: return False
    return True

# --- router: A* on a 0.5 mm grid whose cells are free only RG (> R) from every obstacle, so a step between
#     two free cells is clear; diagonal steps may not cut a corner; then line-of-sight shortcutting, with
#     any diagonal grid step that still grazes something replaced by its two straight steps.
G = 0.5; RG = 0.95
region = cavity or [p for pl in obstacles for p in pl] + [tf(k, (0, 0)) for k in keys]
X0, Y0 = math.floor(min(p[0] for p in region)) - 3, math.floor(min(p[1] for p in region)) - 3
GW, GH = int((math.ceil(max(p[0] for p in region)) + 3 - X0) / G) + 1, int((math.ceil(max(p[1] for p in region)) + 3 - Y0) / G) + 1
blk = bytearray(GW * GH)
def cell(p): return (round((p[0] - X0) / G), round((p[1] - Y0) / G))
def pt(c): return (X0 + c[0] * G, Y0 + c[1] * G)
def blocked(c): return not (0 <= c[0] < GW and 0 <= c[1] < GH) or blk[c[1] * GW + c[0]]
def cells_near(b):
    for gx in range(max(0, int((b[0]-RG-1-X0)/G)), min(GW, int((b[2]+RG+1-X0)/G) + 2)):
        for gy in range(max(0, int((b[1]-RG-1-Y0)/G)), min(GH, int((b[3]+RG+1-Y0)/G) + 2)):
            yield gx, gy
for pl, b in obs:
    for gx, gy in cells_near(b):
        p = pt((gx, gy))
        if seg_poly_dist(p, p, pl) < RG: blk[gy * GW + gx] = 1
if cavity:
    for gy in range(GH):                                       # scanline: everything outside the wall
        yv = Y0 + gy * G; xc = []
        for (a, b), _ in cav_edges:
            if (a[1] > yv) != (b[1] > yv): xc.append(a[0] + (yv - a[1]) * (b[0]-a[0]) / (b[1]-a[1]))
        xc.sort(); ins = bytearray(GW)
        for i in range(0, len(xc) - 1, 2):
            for gx in range(max(0, math.ceil((xc[i] - X0) / G)), min(GW, math.floor((xc[i+1] - X0) / G) + 1)): ins[gx] = 1
        for gx in range(GW):
            if not ins[gx]: blk[gy * GW + gx] = 1
    for (a, b), bb in cav_edges:                               # ... and the band just inside it
        for gx, gy in cells_near(bb):
            if pt_seg(pt((gx, gy)), a, b) < RG: blk[gy * GW + gx] = 1
def free_pt(p, rmax=6.0):   # the nearest free grid point to p, or None
    c = cell(p); best = None; n = int(rmax / G)
    for dx in range(-n, n + 1):
        for dy in range(-n, n + 1):
            m = (c[0]+dx, c[1]+dy)
            if not blocked(m) and (best is None or dx*dx+dy*dy < best[0]): best = (dx*dx+dy*dy, m)
    return pt(best[1]) if best else None
def route(a, b):
    if clear(a, b): return [a, b]
    sa = cell(a); fb = free_pt(b, 3); sb = cell(fb) if fb else cell(b)
    h = lambda n: math.hypot(n[0]-sb[0], n[1]-sb[1])
    pq = [(h(sa), 0, sa)]; came = {sa: None}; cost = {sa: 0}
    while pq:
        _, g, n = heapq.heappop(pq)
        if n == sb: break
        if g > cost.get(n, 1e9): continue
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if not dx and not dy: continue
                m = (n[0]+dx, n[1]+dy)
                if blocked(m) or (dx and dy and (blocked((n[0]+dx, n[1])) or blocked((n[0], n[1]+dy)))): continue
                ng = g + math.hypot(dx, dy)
                if ng < cost.get(m, 1e9):
                    cost[m] = ng; came[m] = n; heapq.heappush(pq, (ng + h(m), ng, m))
    if sb not in came: return [a, b]
    path = []; n = sb
    while n: path.append(pt(n)); n = came[n]
    path = [a] + path[::-1][1:-1] + [b]
    out = [path[0]]; i = 0                     # shortcut
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and not clear(path[i], path[j]): j -= 1
        out.append(path[j]); i = j
    fixed = [out[0]]                           # a diagonal grid step that grazes a corner -> two straight steps
    for p, q in zip(out, out[1:]):
        if not clear(p, q) and abs(abs(q[0]-p[0]) - G) < 1e-6 and abs(abs(q[1]-p[1]) - G) < 1e-6:
            fixed.append((q[0], p[1]) if not blocked(cell((q[0], p[1]))) else (p[0], q[1]))
        fixed.append(q)
    return fixed
def path_via(pts):   # route leg by leg through the waypoints
    out = [pts[0]]
    for q in pts[1:]:
        if math.hypot(q[0]-out[-1][0], q[1]-out[-1][1]) < 0.3: continue
        out += route(out[-1], q)[1:]
    return out

# --- the matrix: columns = vertical chains of grid keys; rows = same row index across columns (rows
#     counted from the top, so the extra keys under the bottom row are row 3); the thumbs are their own
#     row, hung on the inner columns.  Every wire leaves its pad perpendicular to the board edge for
#     LEAD mm (less if something is in the way) before heading off, so it never runs along an edge into a
#     pillar.
LEAD = 3.0
def lead_pt(k, pad):
    a = tf(k, pad)
    nx, ny = (math.copysign(1, pad[0]), 0) if abs(pad[0]) > abs(pad[1]) else (0, math.copysign(1, pad[1]))
    for L in (LEAD, 2.0, 1.0):
        b = tf(k, (pad[0] + nx*L, pad[1] + ny*L))
        if clear(a, b): return b
    return a
def wire(kind, ka, pa, kb, pb, lead=True):
    a, b = tf(ka, pa), tf(kb, pb)
    return (kind, [a, lead_pt(ka, pa), lead_pt(kb, pb), b] if lead else [a, b])
grid = [k for k in keys if k[2] == 0]
thumbs = sorted([k for k in keys if k[2] != 0], key=lambda k: k[0])
cols = {}
for k in grid: cols.setdefault(round(k[0], 2), []).append(k)
xs = sorted(cols)
kid = lambda k: (round(k[0], 2), round(k[1], 2))
wires = []
for x in xs:
    ks = sorted(cols[x], key=lambda k: -k[1])          # top first
    for a, b in zip(ks, ks[1:]):
        wires.append(wire("col", a, COL_B[1], b, COL_T[1]))
rowidx = {}
for x in xs:
    for i, k in enumerate(sorted(cols[x], key=lambda k: -k[1])):
        rowidx[kid(k)] = i           # 0 = top row
for x1, x2 in zip(xs, xs[1:]):
    for a in cols[x1]:
        for b in cols[x2]:
            if rowidx[kid(a)] == rowidx[kid(b)]:
                wires.append(wire("row", a, ROW_R[1], b, ROW_L[1], lead=False))   # straight across: the boards touch
# thumbs: their ROW pads on the edge that faces the main block, chained with lead-outs (out on pad 2, in on pad 1)
for a, b in zip(thumbs, thumbs[1:]):
    wires.append(wire("row", a, ROW_R[2], b, ROW_R[1]))
thumb_col = {}
for i, t in enumerate(thumbs):
    cx = xs[max(0, len(xs) - len(thumbs) + i)]; thumb_col[cx] = t
    bottom = min(cols[cx], key=lambda k: k[1])
    wires.append(wire("col", t, COL_T[1], bottom, COL_B[1]))   # thumb's COL pad (edge facing the columns) up to the column's bottom pad

# --- each chain's wire to the nano: [pad, lead, riser foot, riser top, approach, pin].  The riser runs
#     beside the nano in the pin row's direction, one lane per chain (the lowest pin takes the innermost
#     lane, so the lanes nest instead of crossing); every leg is routed if it is not clear.
nrow = max(len(c) for c in cols.values())
trow = len(row_pins) - 1 if row_pins else nrow                 # the shield's last row is the thumbs'
feeders = []                                                   # (kind, label, key, pad, pro_micro pin or None)
def best_pad(k, pads):  # the pad with the longest clear lead-out
    return max(pads, key=lambda p: math.dist(lead_pt(k, p), tf(k, p)))
for r in range(nrow):
    k = max([k for k in grid if rowidx[kid(k)] == r], key=lambda k: k[0])   # the chain's end nearest the bay
    feeders.append(("row", "row %d" % r, k, ROW_R[1], row_pins[r] if r < len(row_pins) else None))
if thumbs: feeders.append(("row", "row %d" % trow, thumbs[-1], ROW_R[2], row_pins[-1] if row_pins else None))
for j, x in enumerate(xs):
    if x in thumb_col: end, pad = thumb_col[x], COL_T[3]       # the thumb's COL pads facing the block (pad 1 holds the chain)
    else: end = min(cols[x], key=lambda k: k[1]); pad = best_pad(end, [COL_B[3], COL_B[2], COL_B[0]])
    pj = len(col_pins) - len(xs) + j                           # pins are anchored on the inner column
    feeders.append(("col", "col %d" % j, end, pad, col_pins[pj] if 0 <= pj < len(col_pins) else None))
missing = [f[1] for f in feeders if f[4] is None]
lanes = {}
for side in (1, -1):
    fs = sorted([f for f in feeders if f[4] is not None and pad_local(pad_of[f[4]])[0] * side > 0], key=lambda f: pad_local(pad_of[f[4]])[1])
    for kk, f in enumerate(fs): lanes[f[1]] = kk
net_of = {}
for kind, label, k, pad, pin in feeders:
    if pin is None or not mcu: continue
    n = pad_of[pin]; net_of[n] = label
    lx, ly = pad_local(n); sx = math.copysign(1, lx)
    a, a2 = tf(k, pad), lead_pt(k, pad)
    xr = sx * (7.62 + 3 + 1.2 * lanes[label])
    yf = ly                                                    # the lane's foot: down to the lead's level while it stays free
    while yf - G > inv(mcu, a2)[1] and not blocked(cell(tf(mcu, (xr, yf - G)))): yf -= G
    pts = [a, a2, tf(mcu, (xr, yf)), tf(mcu, (xr, ly)), tf(mcu, (sx * (7.62 + 3), ly)), pin_xy(n)]
    wires.append((kind + "_pin", path_via(pts)))
wires = [(kind, path_via(pts)) for kind, pts in wires]
aux = {22: "reset", 23: "reset", 24: "power", 4: "batt \u2212"}   # the other pins the build uses (README: reset, power, battery)
clashes = []
for kind, pts in wires:
    for p1, p2 in zip(pts, pts[1:]):
        dmin = min([seg_poly_dist(p1, p2, pl) for pl in obstacles] + [seg_seg_dist(p1, p2, *e) for e, _ in cav_edges])
        if dmin < 0.8 or not in_cavity(p1) or not in_cavity(p2): clashes.append((kind, p1, p2, dmin))
print("%d wires, %d pillars, %d bosses, %d clashes after routing" % (len(wires), len(pillars), len(bosses), len(clashes)))
for c in clashes: print("  CLASH %s (%.1f,%.1f)-(%.1f,%.1f) %.2f mm" % (c[0], *c[1], *c[2], c[3]))
if missing: print("  no pin in the shield for: " + ", ".join(missing))

# --- SVG (underside view: mirrored in x)
allx = [p[0] for p in region]; ally = [p[1] for p in region]
x0, x1, y0, y1 = min(allx)-5, max(allx)+5, min(ally)-5, max(ally)+5
S = 8  # px per mm
W, H = (x1-x0)*S, (y1-y0)*S + 120
def X(x): return (x1 - x) * S          # mirrored: underside view
def Y(y): return (y1 - y) * S
def attrs(kw): return " ".join('%s="%s"' % (k.replace("_","-"), v) for k, v in kw.items())
def poly(pts, **kw): return '<polygon points="%s" %s/>' % (" ".join("%.1f,%.1f" % (X(x), Y(y)) for x, y in pts), attrs(kw))
def text(x, y, s, **kw):
    kw.setdefault("font_family", "sans-serif"); kw.setdefault("font_size", 11)
    return '<text x="%.1f" y="%.1f" %s>%s</text>' % (X(x), Y(y), attrs(kw), s)
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
       '<rect width="100%" height="100%" fill="#f4f1ea"/>']
if cavity: svg.append(poly(cavity, fill="#fbf9f4", stroke="#8c8c8c", stroke_width=2))
for pl in cav_holes: svg.append(poly(pl, fill="#e2ded4", stroke="#8c8c8c", stroke_width=2))
for k in keys:
    svg.append(poly(rect(k, 0, 0, P, P), fill="#2f7d4e", stroke="#1c4a2e", stroke_width=1))     # board
    svg.append(poly(rect(k, 0, 0, 14, 14), fill="none", stroke="#6fbf8e", stroke_width=0.8, stroke_dasharray="3,2"))  # switch body
    svg.append(poly(rect(k, 0, 0, 10.9, 5.6), fill="#1c4a2e"))                                 # socket
    for pl in (ROW_R, ROW_L, COL_T, COL_B, LED):
        for p in pl:
            x, y = tf(k, p); svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#e8c547"/>' % (X(x), Y(y), 0.6*S))
for pl in pillars: svg.append(poly(pl, fill="#d9534f", fill_opacity="0.85"))
for h in holes:
    svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#b5b0a6" stroke="#8c8c8c" stroke-width="1"/>' % (X(h[0]), Y(h[1]), boss_d/2*S))
    svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#f4f1ea"/>' % (X(h[0]), Y(h[1]), 1.1*S))
if bay:
    for r_, name in ((bay, "bay"), (ctrl, "")):
        if r_: svg.append(poly([(r_[0], r_[1]), (r_[0]+r_[2], r_[1]), (r_[0]+r_[2], r_[1]+r_[3]), (r_[0], r_[1]+r_[3])],
                               fill="none", stroke="#9c9789", stroke_width=1, stroke_dasharray="4,3"))
for c, name, w in ((reset, "reset", 12), (power, "power", 8)):
    if c:
        svg.append(poly([(c[0]-w/2, c[1]-w/2), (c[0]+w/2, c[1]-w/2), (c[0]+w/2, c[1]+w/2), (c[0]-w/2, c[1]+w/2)],
                        fill="none", stroke="#9c9789", stroke_width=1, stroke_dasharray="2,2"))
        svg.append(text(c[0], c[1] - w/2 - 1.2, name, fill="#6b665c", font_size=10, text_anchor="middle"))
for kind, pts in wires:
    col = "#1f77d4" if kind.startswith("col") else "#ff7f0e"
    svg.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round"/>'
               % (" ".join("%.1f,%.1f" % (X(x), Y(y)) for x, y in pts), col, (0.5 if kind.endswith("_pin") else 0.8)*S))
if mcu:   # the controller, on top of the wires that pass under it
    svg.append(poly(rect(mcu, 0, 0, mcu[3], mcu[4]), fill="#2b2b2b", stroke="#111", stroke_width=1))
    svg.append(poly(rect(mcu, 0, mcu[4]/2 + 0.6, 9, 3), fill="#8a8a8a"))      # the USB-C receptacle, overhanging the end
    svg.append(text(*tf(mcu, (0, mcu[4]/2 + 3.2)), "USB", fill="#555", font_size=9, text_anchor="middle"))
    cx_ = X(tf(mcu, (0, 0))[0])
    for n in range(1, 25):
        x, y = pin_xy(n); net = net_of.get(n) or aux.get(n)
        colour = {"c": "#1f77d4", "r": "#ff7f0e"}.get(net[0], "#b48ce0") if net else None
        svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#e8c547" stroke="%s" stroke-width="2"/>' % (X(x), Y(y), 0.55*S, colour or "#2b2b2b"))
        left = X(x) < cx_
        label = PM[n] + (" \u00b7 " + net if net else "")
        svg.append(text(x, y, label, fill={"c": "#9ec9ff", "r": "#ffd28a"}.get(net[0], "#d9bff2") if net else "#c9c4b8",
                        font_size=9, text_anchor="start" if left else "end", dominant_baseline="middle",
                        dx=(1.3*S if left else -1.3*S), font_weight="bold" if net else "normal"))
for kind, label, k, pad, pin in feeders:   # name each chain where its wire to the nano leaves
    a = lead_pt(k, pad); col = "#1f77d4" if kind == "col" else "#ff7f0e"
    svg.append(text(a[0], a[1], label, fill=col, font_size=10, font_weight="bold", text_anchor="middle", dy=-0.9*S,
                    stroke="#f4f1ea", stroke_width=3, paint_order="stroke"))
ly = H - 98
def pins_txt(pins): return "/".join(str(p) for p in pins) if pins else "(no shield found)"
lines = ["Underside view (case off, plate upside down). Grey line = inner wall, grey discs = wall bosses, red = floor pillars (never run a wire over one), yellow = pads.",
         "Blue = column wires, orange = row wires: the shield's matrix. Rows count from the top (0-2 the key rows, 3 the extra keys, 4 the thumbs), columns from the pinky.",
         "Thin lines: each chain's wire to its nice!nano pin. The nano sits component side down with its USB at the wall, so its pins read as in the pinout drawing.",
         "Dashed: the bay and the reset/power pockets (those two live in the plate). Reset \u2192 RST + GND; battery + \u2192 power switch \u2192 RAW/B+; battery \u2212 \u2192 GND.",
         "Rows \u2192 pro_micro %s (pacino.dtsi), columns \u2192 %s (pacino_left.overlay).%s Left half shown; the right half is the mirror image."
         % (pins_txt(row_pins), pins_txt(col_pins), (" No pin in the shield for " + ", ".join(missing) + ": add one.") if missing else "")]
for i, l in enumerate(lines):
    svg.append('<text x="10" y="%d" font-family="sans-serif" font-size="13">%s</text>' % (ly + 20*i, l))
svg.append('</svg>')
os.makedirs(outdir, exist_ok=True)
open(os.path.join(outdir, "wiring_guide.svg"), "w").write("\n".join(svg))
if shutil.which("rsvg-convert"):
    subprocess.run(["rsvg-convert", "-o", os.path.join(outdir, "wiring_guide.png"), os.path.join(outdir, "wiring_guide.svg")])
print("wrote %s/wiring_guide.svg" % outdir + (" and .png" if shutil.which("rsvg-convert") else ""))
shutil.rmtree(tmp, ignore_errors=True)
