#!/usr/bin/env python3
"""Generate the Pacino PCB -- the board for build = "pcb", the slim variant -- as a KiCad 9 project.

    tools/pcb_gen.py [-D ...openscad overrides...]

Everything comes from keyboard.scad: the board outline is the case cavity minus pcb_gap, the switch,
mounting-hole, controller and reset/power positions are the model's own.  Re-run it after changing the
model and the board follows.  There is no schematic: this script IS the schematic -- it declares every
net and every connection, and the nets are named the way the ZMK shield names them.

The board is REVERSIBLE: one design, flipped over for the right half.  What that costs, and how it is
paid for, is in three places --

  switches   every footprint carries both pin diagonals (the 0 deg pair and the 180 deg pair) and a
             hot-swap socket land on each face.  On the right half the switches and sockets go in
             rotated 180 deg; MX switches are square and their stems are symmetric, so nothing about
             the feel or the keycaps changes.
  matrix     flipping the board swaps the controller's two pin rows (row A <-> row B) but not the
             position along a row, so a hole that is pro_micro 2 on the left half is pro_micro 21 on
             the right.  Every matrix net therefore lands on a usable GPIO on both halves -- the ten
             holes were chosen so that both of their pins are free, and pins 1/14/15/16 (the nice!view
             SPI four) stay clear on BOTH halves.  The two ZMK overlays get different pin lists; the
             generator prints them.
  power      RAW and GND have no symmetric pair, so each gets a three-pad solder jumper: bridge the
             centre pad to L or R.  Reset needs no jumper -- it sits across the (rowA,3)/(rowB,3) pair,
             which is GND/RST one way round and RST/GND the other.
"""
import math, os, re, subprocess, sys, heapq

# ---------------------------------------------------------------- run under KiCad's python
try:
    import pcbnew
except ImportError:                                                    # pragma: no cover
    cand = [os.environ.get("KICAD_PYTHON", "")] + [
        "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/%s/bin/python3" % v
        for v in ("3.9", "3.11", "3.12", "Current")] + ["/usr/lib/kicad/bin/python3"]
    for py in cand:
        if py and os.path.exists(py):
            os.execv(py, [py, os.path.abspath(__file__)] + sys.argv[1:])
    sys.exit("pcbnew not importable and no KiCad python found -- set KICAD_PYTHON")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The two slim builds differ in where the cell lives, and that moves the bay, two mounting holes and
# the reset/power positions -- so they are two boards, not one board with an option.
VARIANTS = {
    "flat": dict(key="flat", name="pacino_flat", case="5col_extra2_bat303040_pcb_flat",
                 scad=["-D", "battery_pod=false", "-D", 'battery_type="custom"',
                       "-D", "battery_custom=[30,40,3]"],
                 cell="303040 (3 x 30 x 40, ~320 mAh)",
                 where="in a well in the case floor, entirely under the board -- the plate is flat",
                 leads="Battery leads to `BAT +` / `-`; the cell lies in the floor well beneath them."),
    "pod":  dict(key="pod", name="pacino_pod", case="5col_extra2_bat902030_pcb_pod",
                 scad=["-D", "battery_pod=true"],
                 cell="902030 (9.5 x 20 x 30, 500 mAh)",
                 where="in a pod moulded into the plate, directly over the controller",
                 leads="Battery leads to `BAT +` / `-`; they drop through the plate's controller "
                       "window from the pod above."),
}
OPENSCAD = os.environ.get("OPENSCAD") or "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
if not os.path.exists(OPENSCAD):
    from shutil import which; OPENSCAD = which("openscad") or OPENSCAD
ARGV = [a for a in sys.argv[1:] if not a.startswith("--variant")]
WANT = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--variant=")] or list(VARIANTS)
SCAD_ARGS = []          # set per variant in main()
LIBNAME = "pacino"      # ditto -- the footprint library this board's parts resolve to

KX0, KY0 = 60.0, 120.0            # model origin -> KiCad coordinates (KiCad y is down)
def K(p):  return (KX0 + p[0], KY0 - p[1])

# ---------------------------------------------------------------- geometry from the model
def scad(part, out, extra=()):
    return subprocess.run([OPENSCAD, "--backend=Manifold", "-q", "-D", 'part="%s"' % part,
                           "-D", 'build="pcb"', *SCAD_ARGS, *extra, "-o", out, "keyboard.scad"],
                          cwd=ROOT, capture_output=True, text=True)

def model_info():
    r = subprocess.run([OPENSCAD, "-D", 'part="info"', "-D", 'build="pcb"', *SCAD_ARGS,
                        "-o", "/tmp/_pacino_info.stl", "keyboard.scad"],
                       cwd=ROOT, capture_output=True, text=True)
    info = "".join(l[6:] for l in r.stderr.splitlines() if l.startswith("ECHO: "))
    def arr(name):
        m = re.search(name + r' = (\[.*?\])(?=, [a-z_]+ =|$)', info)
        if not m: sys.exit("could not read %s from the model:\n%s" % (name, info[:400]))
        return eval(m.group(1))
    return {k: arr(k) for k in ("keys", "holes", "mcu", "reset", "power", "stack", "bay", "ctrl")}

def dxf_polylines(path):
    L = open(path).read().split("\n"); out = []; i = 0
    while i < len(L) - 1:
        if L[i].strip() == "0" and L[i + 1].strip() == "LWPOLYLINE":
            pts = []; j = i + 2; x = None
            while j < len(L) - 1 and L[j].strip() != "0":
                c, v = L[j].strip(), L[j + 1].strip()
                if c == "10": x = float(v)
                elif c == "20": pts.append((x, float(v)))
                j += 2
            out.append(pts); i = j
        else: i += 2
    return out

def area(poly):
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly))) / 2

def rdp(pts, eps):
    if len(pts) < 3: return pts
    ax, ay = pts[0]; bx, by = pts[-1]
    dx, dy = bx - ax, by - ay; n = math.hypot(dx, dy)
    worst, wi = -1, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = abs(dx * (ay - py) - (ax - px) * dy) / n if n else math.hypot(px - ax, py - ay)
        if d > worst: worst, wi = d, i
    if worst <= eps: return [pts[0], pts[-1]]
    return rdp(pts[:wi + 1], eps)[:-1] + rdp(pts[wi:], eps)

def board_outline():
    dxf = "/tmp/_pacino_edge.dxf"
    r = scad("pcb_outline_2d", dxf)
    if r.returncode: sys.exit("openscad failed:\n" + r.stderr[-2000:])
    loops = dxf_polylines(dxf)
    loops.sort(key=lambda p: -abs(area(p)))
    outer = [K(p) for p in loops[0]]
    holes = [[K(p) for p in l] for l in loops[1:] if abs(area(l)) > 1.0]
    sys.setrecursionlimit(10000)
    outer = rdp(outer + [outer[0]], 0.008)[:-1]
    return outer, holes

# ---------------------------------------------------------------- pcbnew helpers
mm  = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def lset(*layers):
    s = pcbnew.LSET()
    for l in layers: s.addLayer(l)
    return s
CU  = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
SILK= {"F": pcbnew.F_SilkS, "B": pcbnew.B_SilkS}
MASK= {"F": pcbnew.F_Mask, "B": pcbnew.B_Mask}
PASTE={"F": pcbnew.F_Paste, "B": pcbnew.B_Paste}

OBST = []     # (layers set of "F"/"B"/"*", shape, net) -- the router's view of the copper
def obst(layers, shape, net): OBST.append((layers, shape, net))

class Gen:
    def __init__(self):
        self.b = pcbnew.CreateEmptyBoard()
        self.nets = {}
        ds = self.b.GetDesignSettings()
        ds.m_TrackMinWidth = mm(0.2); ds.m_MinClearance = mm(0.2)
        ds.m_ViasMinSize = mm(0.5); ds.m_MinThroughDrill = mm(0.3)
        ds.m_HoleToHoleMin = mm(0.25); ds.m_CopperEdgeClearance = mm(0.25)
        ds.m_SolderMaskExpansion = mm(0.05); ds.m_SolderMaskMinWidth = mm(0.2)
        self.tracks = 0; self.vias = 0
        self.pads = []          # (net, layers, x, y)
        self.parent = {}        # union-find over pad positions, per net

    def net(self, name):
        if name not in self.nets:
            n = pcbnew.NETINFO_ITEM(self.b, name); self.b.Add(n); self.nets[name] = n
        return self.nets[name]

    # -------- primitives
    def track(self, a, b, layer, net):
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(V(*a)); t.SetEnd(V(*b)); t.SetWidth(mm(0.3))
        t.SetLayer(CU[layer]); t.SetNet(self.net(net)); self.b.Add(t)
        obst(layer, ("seg", a[0], a[1], b[0], b[1], 0.15), net)
        self.tracks += 1

    def via(self, p, net):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(V(*p)); v.SetFrontWidth(mm(0.6)); v.SetDrill(mm(0.3))
        v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.net(net)); self.b.Add(v)
        obst("*", ("circ", p[0], p[1], 0.3), net); self.vias += 1

    def edge(self, a, b, layer=None, width=0.1, parent=None):
        s = pcbnew.PCB_SHAPE(parent or self.b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a)); s.SetEnd(V(*b)); s.SetLayer(layer or pcbnew.Edge_Cuts)
        s.SetWidth(mm(width))
        (parent or self.b).Add(s)

    def text(self, p, txt, layer, size=1.0, rot=0, mirror=False):
        t = pcbnew.PCB_TEXT(self.b); t.SetText(txt); t.SetPosition(V(*p)); t.SetLayer(layer)
        t.SetTextSize(V(max(size, 0.85), max(size, 0.85)))
        t.SetTextThickness(mm(max(size, 0.85) * 0.16))
        t.SetMirrored(mirror); t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); self.b.Add(t)

    # -------- footprints
    def fp(self, ref, value, at, rot, pads, courtyard=None, silk=(), fab=()):
        f = pcbnew.FOOTPRINT(self.b); self.b.Add(f)
        f.SetFPID(pcbnew.LIB_ID(LIBNAME, value))
        f.SetReference(ref); f.SetValue(value)
        f.SetPosition(V(*at))
        f.Reference().SetLayer(pcbnew.F_Fab); f.Reference().SetTextSize(V(0.8, 0.8))
        f.Value().SetLayer(pcbnew.F_Fab); f.Value().SetTextSize(V(0.8, 0.8)); f.Value().SetVisible(False)
        f.Reference().SetPosition(V(at[0], at[1] - 0.5))
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        def world(x, y): return (at[0] + ca * x - sa * -y, at[1] + (-sa) * x + ca * y)
        for p in pads:
            self._pad(f, p, world, rot)
        # graphics go on as footprint children in the unrotated frame; the orientation at the end
        # turns pads and shapes together
        def L(x, y): return (at[0] + x, at[1] + y)
        if courtyard:
            x0, y0, x1, y1 = courtyard
            pts = [L(x0, y0), L(x1, y0), L(x1, y1), L(x0, y1)]
            for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                for i in range(4):
                    self.edge(pts[i], pts[(i + 1) % 4], lay, 0.05, f)
        for (a, bb, la) in silk:
            self.edge(L(*a), L(*bb), SILK[la], 0.15, f)
        for (a, bb) in fab:
            self.edge(L(*a), L(*bb), pcbnew.F_Fab, 0.1, f)
        # orientation LAST: FOOTPRINT::SetOrientation rotates the pads it already owns, shapes and
        # offsets included.  Rotating first and adding pads after leaves every pad shape unrotated.
        f.SetOrientationDegrees(rot)
        return f

    def _pad(self, f, p, world, rot):
        num, kind, x, y, w, h, drill, shape, net = (
            p["n"], p["k"], p["x"], p["y"], p.get("w", 1.0), p.get("h", 1.0),
            p.get("d", 0), p.get("s", "circle"), p.get("net"))
        pad = pcbnew.PAD(f)
        pad.SetNumber(str(num))
        pad.SetShape({"circle": pcbnew.PAD_SHAPE_CIRCLE, "rect": pcbnew.PAD_SHAPE_RECT,
                      "oval": pcbnew.PAD_SHAPE_OVAL, "roundrect": pcbnew.PAD_SHAPE_ROUNDRECT}[shape])
        pad.SetSize(V(w, h))
        if kind in ("F", "B"):
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetLayerSet(lset(CU[kind], MASK[kind], PASTE[kind]))
            layers = kind
        elif kind == "PTH":
            pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad.SetLayerSet(lset(pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.F_Mask, pcbnew.B_Mask))
            pad.SetDrillSize(V(drill, drill)); layers = "*"
        else:
            pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
            pad.SetLayerSet(lset(pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.F_Mask, pcbnew.B_Mask))
            pad.SetDrillSize(V(drill, drill)); layers = "*"; net = None
        f.Add(pad)
        pad.SetFPRelativePosition(V(x, y))
        # NB: a pad's position is its HOLE; "off" moves the copper away from it, which is how the
        # diode lands can take an SMD part without the barrel wicking solder out of the joint.
        if "off" in p: pad.SetOffset(V(*p["off"]))
        if net: pad.SetNet(self.net(net))
        off = p.get("off", (0, 0))
        if kind != "NPTH" and net:
            self.pads.append((net, layers) + world(x + off[0], y + off[1]))
        if kind == "NPTH":
            hx, hy = world(x, y)
            obst("*", ("circ", hx, hy, drill / 2), None)
        else:
            wx, wy = world(x + off[0], y + off[1])
            if shape == "circle":
                obst(layers, ("circ", wx, wy, w / 2), net)
            else:
                obst(layers, ("rect", wx, wy, w, h, rot), net)
            if off != (0, 0):                                # the hole sits away from the copper
                hx, hy = world(x, y)
                obst("*", ("circ", hx, hy, drill / 2), net)
        return pad

# ---------------------------------------------------------------- footprints
def mx_pads(col, sw):
    """Reversible MX + Kailh hot-swap.  Both pin diagonals, a socket land on each face.

    The 0 deg pins are (-3.81,-2.54)/(2.54,-5.08); the 180 deg pins are their negatives.  Grouping
    them as "the two at |y|=2.54 are the column pin, the two at |y|=5.08 go to the diode" means a
    switch bridges column-to-diode whichever way round it goes in.  Mirroring about a diagonal (the
    naive reversible footprint) would put two 3 mm holes 2.84 mm apart and they would merge."""
    return [
        {"n": "", "k": "NPTH", "x": 0,      "y": 0,     "w": 4.0, "h": 4.0, "d": 4.0},
        {"n": "", "k": "NPTH", "x": -5.08,  "y": 0,     "w": 1.65, "h": 1.65, "d": 1.65},
        {"n": "", "k": "NPTH", "x": 5.08,   "y": 0,     "w": 1.65, "h": 1.65, "d": 1.65},
        {"n": 1, "k": "PTH", "x": -3.81, "y": -2.54, "w": 3.4, "h": 3.4, "d": 3.0, "net": col},
        {"n": 1, "k": "PTH", "x": -3.81, "y":  2.54, "w": 3.4, "h": 3.4, "d": 3.0, "net": col},
        {"n": 2, "k": "PTH", "x":  2.54, "y": -5.08, "w": 3.4, "h": 3.4, "d": 3.0, "net": sw},
        {"n": 2, "k": "PTH", "x":  2.54, "y":  5.08, "w": 3.4, "h": 3.4, "d": 3.0, "net": sw},
        {"n": 1, "k": "B", "x": -7.085, "y": -2.54, "w": 2.55, "h": 2.5, "s": "rect", "net": col},
        {"n": 2, "k": "B", "x":  5.842, "y": -5.08, "w": 2.55, "h": 2.5, "s": "rect", "net": sw},
        {"n": 1, "k": "F", "x": -7.085, "y":  2.54, "w": 2.55, "h": 2.5, "s": "rect", "net": col},
        {"n": 2, "k": "F", "x":  5.842, "y":  5.08, "w": 2.55, "h": 2.5, "s": "rect", "net": sw},
    ]
MX_CRT = (-8.8, -6.7, 7.8, 6.7)
MX_FAB = [((-7, -7), (7, -7)), ((7, -7), (7, 7)), ((7, 7), (-7, 7)), ((-7, 7), (-7, -7))]

def diode_pads(row, sw):
    """SOD-123 land on both faces at once: one plated pad per end, copper offset off the hole so an
    SMD diode solders to either face and the barrel ties them.  A THT 1N4148 on 3.3 mm pitch fits too."""
    return [
        {"n": 1, "k": "PTH", "x": -1.65, "y": 1.8, "w": 1.3, "h": 3.0, "d": 0.5, "s": "oval",
         "off": (0, -1.05), "net": row},
        {"n": 2, "k": "PTH", "x":  1.65, "y": 1.8, "w": 1.3, "h": 3.0, "d": 0.5, "s": "oval",
         "off": (0, -1.05), "net": sw},
    ]
D_CRT = (-3.0, -1.2, 2.6, 2.6)

MCU_PIN = {}      # pad number -> (x, y) in footprint coords
for i in range(1, 13):
    MCU_PIN[i] = (-7.62, -13.97 + (i - 1) * 2.54)
    MCU_PIN[25 - i] = (7.62, -13.97 + (i - 1) * 2.54)
# pro_micro pin names, row A (pads 1..12) then row B (pads 13..24), for the silk and the report
PRO_MICRO = {1: "1/TX", 2: "0/RX", 3: "GND", 4: "GND", 5: "2", 6: "3", 7: "4", 8: "5", 9: "6",
             10: "7", 11: "8", 12: "9", 13: "10", 14: "16", 15: "14", 16: "15", 17: "18", 18: "19",
             19: "20", 20: "21", 21: "VCC", 22: "RST", 23: "GND", 24: "RAW"}
# the ten matrix holes: both of each hole's two pins (left build / right build) must be a free GPIO,
# and neither may be 1/14/15/16 -- those four are the nice!view's CS/MISO/SCK/MOSI and stay free on
# BOTH halves.  That leaves exactly k = 5,6,7,8,12 on each row: ten holes for ten matrix nets.
MCU_MATRIX = {5: "COL0", 6: "COL1", 7: "COL2", 8: "COL3", 12: "COL4",
              20: "ROW0", 19: "ROW1", 18: "ROW2", 17: "ROW3", 13: "ROW4"}
MCU_POWER  = {3: "RST_A", 22: "RST_B", 24: "BAT_L", 1: "BAT_R", 4: "GND_L", 21: "GND_R"}

def mcu_pads(w, l):
    pads = []
    for n, (x, y) in sorted(MCU_PIN.items()):
        net = MCU_MATRIX.get(n) or MCU_POWER.get(n)
        pads.append({"n": n, "k": "PTH", "x": x, "y": y, "w": 1.7, "h": 1.7, "d": 1.0,
                     "s": "rect" if n == 1 else "circle", "net": net})
    return pads

def jumper_pads(l_net, common, r_net):
    return [{"n": 1, "k": "PTH", "x": -1.4, "y": 0, "w": 1.0, "h": 1.7, "d": 0.5, "s": "rect", "net": l_net},
            {"n": 2, "k": "PTH", "x":  0.0, "y": 0, "w": 1.0, "h": 1.7, "d": 0.5, "s": "rect", "net": common},
            {"n": 3, "k": "PTH", "x":  1.4, "y": 0, "w": 1.0, "h": 1.7, "d": 0.5, "s": "rect", "net": r_net}]

# ---------------------------------------------------------------- maze router
class Router:
    """Two-layer grid router.  Every net's copper is rasterised as "this cell belongs to net N";
    a cell claimed by two different nets is blocked outright.  A* then routes on the cells that are
    free or already this net's, which lets a track run right up to its own pad."""
    CELL, CLEAR, TW, EDGE = 0.25, 0.3, 0.3, 0.35

    def __init__(self, outline, obstacles):
        xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
        self.x0, self.y0 = min(xs) - 2, min(ys) - 2
        self.nx = int((max(xs) + 2 - self.x0) / self.CELL) + 1
        self.ny = int((max(ys) + 2 - self.y0) / self.CELL) + 1
        n = self.nx * self.ny
        from array import array
        self.own = [array("h", [-1]) * n, array("h", [-1]) * n]   # -1 blocked, 0 free, >0 net id
        self.netid = {}; self._inside(outline)
        for layers, shape, net in obstacles: self.claim(layers, shape, net)

    def nid(self, net):
        if net not in self.netid: self.netid[net] = len(self.netid) + 1
        return self.netid[net]

    def cell(self, x, y):
        return (int(round((x - self.x0) / self.CELL)), int(round((y - self.y0) / self.CELL)))
    def pos(self, ix, iy): return (self.x0 + ix * self.CELL, self.y0 + iy * self.CELL)

    def _inside(self, poly):
        """scanline-fill the board, then erode by the copper-to-edge clearance"""
        nx, ny, C = self.nx, self.ny, self.CELL
        rows = [bytearray(nx) for _ in range(ny)]
        edges = [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]
        for iy in range(ny):
            y = self.y0 + iy * C; xs = []
            for (ax, ay), (bx, by) in edges:
                if (ay > y) != (by > y):
                    xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
            xs.sort()
            r = rows[iy]
            for i in range(0, len(xs) - 1, 2):
                a = max(0, int(math.ceil((xs[i] - self.x0) / C)))
                b = min(nx - 1, int((xs[i + 1] - self.x0) / C))
                for ix in range(a, b + 1): r[ix] = 1
        k = int(math.ceil((self.EDGE + self.TW / 2) / C))          # separable square erosion
        for iy in range(ny):
            r = rows[iy]; out = bytearray(nx)
            for ix in range(nx):
                if all(r[j] for j in range(max(0, ix - k), min(nx, ix + k + 1))): out[ix] = 1
            rows[iy] = out
        for ix in range(nx):
            col = [rows[iy][ix] for iy in range(ny)]
            for iy in range(ny):
                if not all(col[j] for j in range(max(0, iy - k), min(ny, iy + k + 1))):
                    rows[iy][ix] = 0
        for iy in range(ny):
            base = iy * nx; r = rows[iy]
            for ix in range(nx):
                if r[ix]: self.own[0][base + ix] = self.own[1][base + ix] = 0

    def claim(self, layers, shape, net, extra=0.0):
        nid = self.nid(net) if net else -1
        infl = self.CLEAR + self.TW / 2 + extra
        kind = shape[0]
        if kind == "circ":
            _, cx, cy, r = shape; bb = (cx - r - infl, cy - r - infl, cx + r + infl, cy + r + infl)
            def d(px, py): return math.hypot(px - cx, py - cy) - r
        elif kind == "rect":
            _, cx, cy, w, h, rot = shape
            hw, hh = w / 2, h / 2; ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            rr = math.hypot(hw, hh)
            bb = (cx - rr - infl, cy - rr - infl, cx + rr + infl, cy + rr + infl)
            def d(px, py):
                dx, dy = px - cx, py - cy
                lx = dx * ca - dy * sa; ly = dx * sa + dy * ca
                ox, oy = max(abs(lx) - hw, 0), max(abs(ly) - hh, 0)
                return math.hypot(ox, oy)
        else:
            _, ax, ay, bx, by, hw = shape
            bb = (min(ax, bx) - hw - infl, min(ay, by) - hw - infl,
                  max(ax, bx) + hw + infl, max(ay, by) + hw + infl)
            ddx, ddy = bx - ax, by - ay; L = ddx * ddx + ddy * ddy
            def d(px, py):
                t = 0 if L == 0 else max(0, min(1, ((px - ax) * ddx + (py - ay) * ddy) / L))
                return math.hypot(px - ax - t * ddx, py - ay - t * ddy) - hw
        i0, j0 = self.cell(bb[0], bb[1]); i1, j1 = self.cell(bb[2], bb[3])
        planes = [0, 1] if layers == "*" else ([0] if layers == "F" else [1])
        for iy in range(max(0, j0), min(self.ny, j1 + 1)):
            base = iy * self.nx; py = self.y0 + iy * self.CELL
            for ix in range(max(0, i0), min(self.nx, i1 + 1)):
                if d(self.x0 + ix * self.CELL, py) <= infl:
                    for pl in planes:
                        o = self.own[pl][base + ix]
                        if o == 0 or o == nid: self.own[pl][base + ix] = nid
                        else: self.own[pl][base + ix] = -1

    def force(self, layers, x, y, net):
        """a pad centre always belongs to its own pad"""
        ix, iy = self.cell(x, y); nid = self.nid(net)
        planes = [0, 1] if layers == "*" else ([0] if layers == "F" else [1])
        for pl in planes:
            if 0 <= ix < self.nx and 0 <= iy < self.ny: self.own[pl][ix + iy * self.nx] = nid

    NB = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
          (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142))
    VIA = 14.0

    def route(self, net, starts, goals, limit=600000):
        """starts/goals: lists of (layer_index, x, y).  Returns a list of (layer, x, y) waypoints."""
        nid = self.nid(net); nx, ny = self.nx, self.ny
        gset = set()
        for pl, x, y in goals:
            ix, iy = self.cell(x, y); gset.add(pl * nx * ny + iy * nx + ix)
        gpts = [(self.cell(x, y), pl) for pl, x, y in goals]
        def h(ix, iy):
            best = 1e9
            for (gx, gy), _ in gpts:
                dx, dy = abs(ix - gx), abs(iy - gy)
                best = min(best, (dx + dy) + (1.4142 - 2) * min(dx, dy))
            return best * 0.999
        openh = []; g = {}; came = {}
        for pl, x, y in starts:
            ix, iy = self.cell(x, y); k = pl * nx * ny + iy * nx + ix
            if self.own[pl][iy * nx + ix] not in (0, nid): continue
            g[k] = 0.0; heapq.heappush(openh, (h(ix, iy), k))
        n = 0
        while openh:
            f, k = heapq.heappop(openh)
            if k in gset:
                path = []
                while k is not None:
                    pl, r = divmod(k, nx * ny); iy, ix = divmod(r, nx)
                    path.append((pl, ) + self.pos(ix, iy)); k = came.get(k)
                return path[::-1]
            n += 1
            if n > limit: return None
            pl, r = divmod(k, nx * ny); iy, ix = divmod(r, nx)
            gk = g[k]
            if f - h(ix, iy) > gk + 1e-9: continue
            for dx, dy, c in self.NB:
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < nx and 0 <= jy < ny): continue
                if self.own[pl][jy * nx + jx] not in (0, nid): continue
                if dx and dy:                                    # no corner cutting
                    if self.own[pl][iy * nx + jx] not in (0, nid): continue
                    if self.own[pl][jy * nx + ix] not in (0, nid): continue
                nk = pl * nx * ny + jy * nx + jx; ng = gk + c
                if ng < g.get(nk, 1e18):
                    g[nk] = ng; came[nk] = k; heapq.heappush(openh, (ng + h(jx, jy), nk))
            ol = 1 - pl                                          # layer change (via)
            ok = True
            for ddx in (-1, 0, 1):
                for ddy in (-1, 0, 1):
                    jx, jy = ix + ddx, iy + ddy
                    if not (0 <= jx < nx and 0 <= jy < ny): ok = False; break
                    if self.own[ol][jy * nx + jx] not in (0, nid): ok = False; break
                    if self.own[pl][jy * nx + jx] not in (0, nid): ok = False; break
                if not ok: break
            if ok:
                nk = ol * nx * ny + iy * nx + ix; ng = gk + self.VIA
                if ng < g.get(nk, 1e18):
                    g[nk] = ng; came[nk] = k; heapq.heappush(openh, (ng + h(ix, iy), nk))
        return None

# ---------------------------------------------------------------- placement helpers
def quad(cx, cy, rot, box):
    x0, y0, x1, y1 = box
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + ca * x + sa * y, cy - sa * x + ca * y)
            for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]

def sat_overlap(a, b, gap=0.0):
    for poly in (a, b):
        for i in range(len(poly)):
            ax, ay = poly[i]; bx, by = poly[(i + 1) % len(poly)]
            nx, ny = -(by - ay), bx - ax; L = math.hypot(nx, ny)
            if not L: continue
            nx, ny = nx / L, ny / L
            pa = [p[0] * nx + p[1] * ny for p in a]; pb = [p[0] * nx + p[1] * ny for p in b]
            if min(pa) - max(pb) > gap or min(pb) - max(pa) > gap: return False
    return True

def poly_inside(pt, poly):
    x, y = pt; c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1): c = not c
    return c

def dist_to_poly(pt, poly):
    x, y = pt; best = 1e9
    for i in range(len(poly)):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % len(poly)]
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
        best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return best

def circ_clear(q, cx, cy, r, gap):
    for i in range(len(q)):
        ax, ay = q[i]; bx, by = q[(i + 1) % len(q)]
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((cx - ax) * dx + (cy - ay) * dy) / L))
        if math.hypot(cx - ax - t * dx, cy - ay - t * dy) < r + gap: return False
    return not poly_inside((cx, cy), q)

def free_rect(outline, blocks, edge=2.0, gap=1.5, step=1.0):
    """largest empty axis-aligned rectangle on the board -- where the legend can go without
    fouling a footprint, a pad or the edge"""
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    x0, y0 = min(xs), min(ys)
    nx = int((max(xs) - x0) / step) + 1; ny = int((max(ys) - y0) / step) + 1
    grid = []
    for j in range(ny):
        row = bytearray(nx); py = y0 + j * step
        for i in range(nx):
            px = x0 + i * step
            if not poly_inside((px, py), outline) or dist_to_poly((px, py), outline) < edge: continue
            if any(sat_overlap([(px, py)] * 3 + [(px + 0.01, py)], q, gap) for q in blocks): continue
            row[i] = 1
        grid.append(row)
    best = (0, 0, 0, 0, 0); heights = [0] * nx
    for j in range(ny):
        for i in range(nx): heights[i] = heights[i] + 1 if grid[j][i] else 0
        st = []
        for i in range(nx + 1):
            h = heights[i] if i < nx else 0; start = i
            while st and st[-1][1] >= h:
                sidx, hh = st.pop(); a = hh * (i - sidx)
                if a > best[0]: best = (a, x0 + sidx * step, y0 + (j - hh + 1) * step,
                                        (i - sidx) * step, hh * step)
                start = sidx
            st.append((start, h))
    _, bx, by, bw, bh = best
    return (bx + bw / 2, by + bh / 2, bw, bh)

def fit_legend(outline, blocks, need_w, need_h):
    """place the legend in the largest clear area, turned on its side if that fits better"""
    cx, cy, cw, ch = free_rect(outline, blocks)
    flat = min(cw / need_w, ch / need_h)
    turn = min(ch / need_w, cw / need_h)
    return (cx, cy, turn, 90) if turn > flat else (cx, cy, flat, 0)

# ---------------------------------------------------------------- the board
DIODE_HOME  = (0.0, 8.8)      # the band between two key rows: 5.65 mm tall, the diode needs 4.0
# fallbacks, nearest-to-home first.  The footprint runs -1.2..+2.8 in y, so "above the switch" needs
# -10.8, not -8.8, to clear the switch courtyard.
DIODE_TRIES = sorted(
    {(lx, ly) for ly in (8.8, -10.8, 10.8, 12.8, -12.8, 4.0, -4.0, 0.0)
              for lx in (0, 3.5, -3.5, 6.5, -6.5, 9.5, -9.5)} |
    {(lx, ly) for lx in (11.6, -11.6, 13.6, -13.6) for ly in (0, 3.5, -3.5, 7, -7)},
    key=lambda p: math.hypot(p[0], p[1] - DIODE_HOME[1]))

def build():
    del OBST[:]
    info = model_info()
    outline, loops = board_outline()
    keys, holes = info["keys"], info["holes"]
    mcu, stack = info["mcu"], info["stack"]
    g = Gen()

    for i in range(len(outline)):
        g.edge(outline[i], outline[(i + 1) % len(outline)])

    # interior loops in the model outline are the mounting holes that do not touch the edge
    inner_holes = []
    for l in loops:
        cx = sum(p[0] for p in l) / len(l); cy = sum(p[1] for p in l) / len(l)
        d = 2 * max(math.hypot(p[0] - cx, p[1] - cy) for p in l)
        inner_holes.append((cx, cy, d))

    # ---- matrix from the model's key list
    thumbs = [i for i, k in enumerate(keys) if abs(k[2]) > 1e-6]
    grid   = [i for i, k in enumerate(keys) if abs(k[2]) <= 1e-6]
    colxs  = sorted(set(round(keys[i][0], 3) for i in grid))
    ncols  = len(colxs)
    rc = {}
    for c, cx in enumerate(colxs):
        ks = sorted([i for i in grid if round(keys[i][0], 3) == cx], key=lambda i: -keys[i][1])
        for r, i in enumerate(ks): rc[i] = (min(r, 3), c)
    for n, i in enumerate(thumbs): rc[i] = (4, ncols - 3 + n)

    # ---- switches + diodes
    placed = []                                   # (quad, tag) for collision checks
    for i, k in enumerate(keys):
        at = K(k); rot = k[2]
        placed.append((quad(at[0], at[1], rot, MX_CRT), "SW%d" % (i + 1)))
    boss = [(K(h)[0], K(h)[1], 3.0) for h in holes]

    def try_diode(i, lx, ly, against):
        k = keys[i]; at = K(k); rot = k[2]
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        if abs(rot) <= 1e-6 and lx < -2: return None         # the column bus runs down x = -3.81
        dx = at[0] + ca * lx + sa * ly; dy = at[1] - sa * lx + ca * ly
        q = quad(dx, dy, rot, D_CRT)
        if any(not poly_inside(p, outline) or dist_to_poly(p, outline) < 0.8 for p in q): return None
        if any(sat_overlap(q, o, 0.25) for o, _ in against): return None
        if any(not circ_clear(q, bx, by, br, 0.3) for bx, by, br in boss): return None
        return (dx, dy, rot, lx, ly, q)

    # two passes so that one diode having to move never pushes its neighbour: everybody who fits in
    # the home slot takes it first, and only the rest go looking
    diode_at = {}; late = []
    for i in range(len(keys)):
        r = try_diode(i, *DIODE_HOME, placed)
        if r: diode_at[i] = r[:5]; placed.append((r[5], "D%d" % (i + 1)))
        else: late.append(i)
    for i in late:
        at = K(keys[i]); rot = keys[i][2]
        for lx, ly in DIODE_TRIES:
            r = try_diode(i, lx, ly, placed)
            if r:
                diode_at[i] = r[:5]; placed.append((r[5], "D%d" % (i + 1))); break
        else:
            for lx, ly in DIODE_TRIES:
                ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
                dx = at[0] + ca * lx + sa * ly; dy = at[1] - sa * lx + ca * ly
                q = quad(dx, dy, rot, D_CRT); why = []
                if abs(rot) <= 1e-6 and lx < -2: why.append("colbus")
                if any(not poly_inside(pp, outline) for pp in q): why.append("outside")
                if any(dist_to_poly(pp, outline) < 0.8 for pp in q): why.append("edge")
                hit = [t for o, t in placed if sat_overlap(q, o, 0.25)]
                if hit: why.append("hits " + ",".join(hit))
                if any(not circ_clear(q, bx, by, br, 0.3) for bx, by, br in boss): why.append("boss")
                print("   D%d (%+.1f,%+.1f) at (%.1f,%.1f): %s" % (i + 1, lx, ly, dx, dy, "; ".join(why)))
            sys.exit("no room for diode D%d next to SW%d" % (i + 1, i + 1))

    for i, k in enumerate(keys):
        row, col = rc[i]; at = K(k); rot = k[2]
        sw, cn, rn = "SW%d" % (i + 1), "COL%d" % col, "ROW%d" % row
        g.fp("SW%d" % (i + 1), "MX_Hotswap_Rev", at, rot, mx_pads(cn, sw), MX_CRT, fab=MX_FAB)
        dx, dy, drot, _, _ = diode_at[i]
        g.fp("D%d" % (i + 1), "1N4148W", (dx, dy), drot, diode_pads(rn, sw), D_CRT,
             silk=[((-2.75, -0.5), (-2.75, 2.0), "F"), ((-2.75, -0.5), (-2.75, 2.0), "B")])

    # ---- controller, reset, power, jumpers, battery pads
    mat = K(mcu[:2]); mrot = mcu[2]; bay = info["bay"]
    g.fp("U1", "nice!nano", mat, mrot, mcu_pads(mcu[3], mcu[4]),
         (-mcu[3] / 2 - 0.4, -mcu[4] / 2 - 0.4, mcu[3] / 2 + 0.4, mcu[4] / 2 + 0.4),
         silk=[((-mcu[3] / 2, -mcu[4] / 2), (mcu[3] / 2, -mcu[4] / 2), "F"),
               ((mcu[3] / 2, -mcu[4] / 2), (mcu[3] / 2, mcu[4] / 2), "F"),
               ((mcu[3] / 2, mcu[4] / 2), (-mcu[3] / 2, mcu[4] / 2), "F"),
               ((-mcu[3] / 2, mcu[4] / 2), (-mcu[3] / 2, -mcu[4] / 2), "F")])
    g.fp("RSW1", "SW_Tactile_12mm", K(info["reset"]), 0,
         [{"n": 1 if x < 0 else 2, "k": "PTH", "x": x, "y": y, "w": 1.6, "h": 1.6, "d": 0.95,
           "net": "RST_A" if x < 0 else "RST_B"}
          for x in (-6.25, 6.25) for y in (-2.5, 2.5)],
         (-7.15, -6.15, 7.15, 6.15))
    g.fp("PWR1", "SS12D00", K(info["power"]), 0,
         [{"n": 1, "k": "PTH", "x": -2.54, "y": 0, "w": 1.6, "h": 1.6, "d": 0.95, "net": "BAT_P"},
          {"n": 2, "k": "PTH", "x": 0.0,  "y": 0, "w": 1.6, "h": 1.6, "d": 0.95, "net": "BAT_SW"},
          {"n": 3, "k": "PTH", "x": 2.54, "y": 0, "w": 1.6, "h": 1.6, "d": 0.95}],
         (-4.5, -1.95, 4.5, 1.95))
    # the jumpers go just right of the slide switch, at the free right-hand end of the control
    # strip -- placed off the switch, not the controller, so they follow it when the bay is wider
    pw = K(info["power"])
    jp1 = (pw[0] + 8.2, pw[1] - 1.8); jp2 = (pw[0] + 8.2, pw[1] + 2.7)
    bt1 = (mat[0], mat[1] + 18.5)   # under the plate's lead slot, clear of the controller
    g.fp("JP1", "BAT_SELECT", jp1, 0, jumper_pads("BAT_L", "BAT_SW", "BAT_R"), (-2.3, -1.3, 2.3, 1.3))
    g.fp("JP2", "GND_SELECT", jp2, 0, jumper_pads("GND_L", "GND", "GND_R"), (-2.3, -1.3, 2.3, 1.3))
    g.fp("BT1", "LiPo", bt1, 0,
         [{"n": 1, "k": "PTH", "x": -1.75, "y": 0, "w": 1.9, "h": 1.9, "d": 1.1, "net": "BAT_P"},
          {"n": 2, "k": "PTH", "x":  1.75, "y": 0, "w": 1.9, "h": 1.9, "d": 1.1, "net": "GND"}],
         (-2.9, -1.15, 2.9, 1.15))
    # ---- silkscreen.  Both faces carry it: the left half is assembled on B, the right half on F,
    # so whichever side you are looking at has to tell you what to do.
    def note(at_, txt, size=1.0, face=None, rot=0):
        if face in (None, "F"): g.text(at_, txt, pcbnew.F_SilkS, size, rot)
        if face in (None, "B"): g.text(at_, txt, pcbnew.B_SilkS, size, rot, mirror=True)
    note((jp1[0], jp1[1] - 2.2), "BAT", 1.0)
    note((jp2[0], jp2[1] + 2.4), "GND", 1.0)
    for jp in (jp1, jp2):
        note((jp[0] - 1.4, jp[1] - 1.5), "L", 0.9, face="B")     # left half solders on B
        note((jp[0] + 1.4, jp[1] - 1.5), "R", 0.9, face="F")     # right half solders on F
    note((bt1[0] - 1.75, bt1[1] + 2.1), "+", 1.2)
    note((bt1[0] + 1.75, bt1[1] + 2.1), "-", 1.2)
    note((bt1[0] + 6.8, bt1[1] + 2.1), "BAT", 1.0)
    note((K(info["reset"])[0], K(info["reset"])[1] - 7.4), "RESET", 1.2)
    note((K(info["power"])[0], K(info["power"])[1] - 2.9), "PWR", 1.0)
    note((K(info["power"])[0] - 6.6, K(info["power"])[1]), "ON", 0.9)
    note((mat[0], mat[1] - mcu[4] / 2 - 1.6), "USB", 1.2)
    note((mat[0] - mcu[3] / 2 - 2.2, mat[1] - mcu[4] / 2 + 1.0), "1", 1.0)
    note((mat[0], mat[1]), "nice!nano", 1.4)
    blocks = [q for q, _ in placed] + [
        quad(mat[0], mat[1], mrot, (-mcu[3] / 2 - 1, -mcu[4] / 2 - 1, mcu[3] / 2 + 1, mcu[4] / 2 + 1)),
        quad(*K(info["reset"]), 0, (-7.5, -6.5, 7.5, 6.5)),
        quad(*K(info["power"]), 0, (-7.5, -3.0, 5.0, 3.0)),
        quad(jp1[0], jp1[1], 0, (-3, -3, 3, 3)), quad(jp2[0], jp2[1], 0, (-3, -3, 3, 3)),
        quad(bt1[0], bt1[1], 0, (-9, -3.5, 11, 4))] + \
        [quad(bx, by, 0, (-3.4, -3.4, 3.4, 3.4)) for bx, by, _ in boss]
    lines = [("PACINO", 1.8), ("%s - PARTS THIS SIDE", 1.2)]
    need_w = max(len(t) * 0.78 * sz for t, sz in lines) + 1
    need_h = 2 * 2.9 + 1
    cx, cy, scale, trot = fit_legend(outline, blocks, need_w, need_h)
    scale = max(0.62, min(1.25, scale))
    for n, (txt, sz) in enumerate(lines):
        d = (n - 0.5) * 2.9 * scale
        at_ = (cx - d, cy) if trot else (cx, cy + d)
        g.text(at_, txt.replace("%s", "RIGHT HALF"), pcbnew.F_SilkS, sz * scale, trot)
        g.text(at_, txt.replace("%s", "LEFT HALF"), pcbnew.B_SilkS, sz * scale, trot, mirror=True)
    print("  legend at (%.1f, %.1f) rot %d scale %.2f" % (cx, cy, trot, scale))

    for n, (cx, cy, d) in enumerate(inner_holes):
        g.fp("H%d" % (n + 1), "MountingHole", (cx, cy), 0,
             [{"n": "", "k": "NPTH", "x": 0, "y": 0, "w": d, "h": d, "d": d}],
             (-d / 2 - 0.2, -d / 2 - 0.2, d / 2 + 0.2, d / 2 + 0.2))
    return g, info, outline, rc, keys, diode_at, colxs

# ---------------------------------------------------------------- connectivity
def key(net, x, y): return (net, round(x, 2), round(y, 2))

def find(par, k):
    par.setdefault(k, k)
    while par[k] != k: par[k] = par[par[k]]; k = par[k]
    return k
def union(par, a, b): par[find(par, a)] = find(par, b)

def hand_route(g, net, a, b, layer):
    g.track(a, b, layer, net)
    union(g.parent, key(net, *a), key(net, *b))

def local_routes(g, keys, rc, diode_at, colxs):
    """the routing that is the same for every key: the two column pins tied, the two diode-side pins
    tied, each socket land to its pin, the switch to its diode -- and the straight column bus"""
    for i, k in enumerate(keys):
        row, col = rc[i]; at = K(k); rot = k[2]
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        def W(x, y): return (at[0] + ca * x + sa * y, at[1] - sa * x + ca * y)
        cn, sw = "COL%d" % col, "SW%d" % (i + 1)
        hand_route(g, cn, W(-3.81, -2.54), W(-3.81, 2.54), "F")
        hand_route(g, cn, W(-7.085, -2.54), W(-3.81, -2.54), "B")
        hand_route(g, cn, W(-7.085, 2.54), W(-3.81, 2.54), "F")
        hand_route(g, sw, W(2.54, -5.08), W(2.54, 5.08), "B")
        hand_route(g, sw, W(5.842, -5.08), W(2.54, -5.08), "B")
        hand_route(g, sw, W(5.842, 5.08), W(2.54, 5.08), "F")
        _, _, _, lx, ly = diode_at[i]
        if ly >= 7.0 and -2.0 <= lx <= 7.0:      # a straight line here misses the holes and the
                                                #  diode's other pad; anything else the router does
            hand_route(g, sw, W(2.54, 5.08), W(lx + 1.65, ly + 0.75), "F")
    # column bus: grid keys in a column share an x, so it is one straight track per gap
    for c, cx in enumerate(colxs):
        ks = sorted([i for i, k in enumerate(keys)
                     if abs(k[2]) <= 1e-6 and round(k[0], 3) == cx], key=lambda i: -keys[i][1])
        for a, b in zip(ks, ks[1:]):
            pa = K(keys[a]); pb = K(keys[b])
            hand_route(g, "COL%d" % c, (pa[0] - 3.81, pa[1] + 2.54), (pb[0] - 3.81, pb[1] - 2.54), "F")

def emit_path(g, r, net, path):
    runs = []; cur = [path[0]]
    for prev, nxt in zip(path, path[1:]):
        if prev[0] != nxt[0]:
            runs.append(("seg", cur)); runs.append(("via", nxt)); cur = [nxt]
        else: cur.append(nxt)
    runs.append(("seg", cur))
    for kind, data in runs:
        if kind == "via":
            g.via((data[1], data[2]), net)
            r.claim("*", ("circ", data[1], data[2], 0.3), net, 0.05)
            continue
        pts = data
        if len(pts) < 2: continue
        simple = [pts[0]]
        for i in range(1, len(pts) - 1):
            ax, ay = pts[i - 1][1:]; bx, by = pts[i][1:]; cx, cy = pts[i + 1][1:]
            if (bx - ax, by - ay) != (cx - bx, cy - by): simple.append(pts[i])
        simple.append(pts[-1])
        lay = "F" if pts[0][0] == 0 else "B"
        for a, b in zip(simple, simple[1:]):
            g.track(a[1:], b[1:], lay, net)
            r.claim(lay, ("seg", a[1], a[2], b[1], b[2], 0.15), net, 0.05)

def connect_all(g, r):
    from collections import defaultdict
    terms = defaultdict(list)
    for net, layers, x, y in g.pads:
        t = (layers, x, y)
        if t not in terms[net]: terms[net].append(t)
    for net, ts in terms.items():
        for layers, x, y in ts: r.force(layers, x, y, net)
    failed = []
    # the handful of power/reset nets are the most constrained (fixed endpoints deep in the bay),
    # so they pick their path before the matrix fills the corridor
    rank = lambda n: 0 if n[:3] not in ("ROW", "COL", "SW1", "SW2") and not n.startswith("SW") \
        else 1 if n.startswith("ROW") else 2
    nets = sorted(terms, key=lambda n: (rank(n), n))
    for net in nets:
        ts = terms[net]
        groups = {}
        for t in ts: groups.setdefault(find(g.parent, key(net, t[1], t[2])), []).append(t)
        comps = list(groups.values())
        while len(comps) > 1:
            best = None
            for i in range(len(comps)):
                for j in range(i + 1, len(comps)):
                    for a in comps[i]:
                        for b in comps[j]:
                            d = math.hypot(a[1] - b[1], a[2] - b[2])
                            if best is None or d < best[0]: best = (d, i, j, a, b)
            _, i, j, a, b = best
            def cells(t):
                pl = [0, 1] if t[0] == "*" else ([0] if t[0] == "F" else [1])
                return [(p, t[1], t[2]) for p in pl]
            starts = [c for t in comps[i] for c in cells(t)]
            goals  = [c for t in comps[j] for c in cells(t)]
            path = r.route(net, starts, goals)
            if path is None:
                failed.append((net, a, b)); comps[i] = comps[i] + comps[j]; comps.pop(j); continue
            emit_path(g, r, net, path)
            comps[i] = comps[i] + comps[j]; comps.pop(j)
    return failed

# ---------------------------------------------------------------- ground pour + output
def export_library(g, libdir):
    """one master copy of each footprint, at the origin and without nets, so the project has a real
    library behind its footprints and they can be opened and edited in the footprint editor"""
    if os.path.isdir(libdir):
        for f in os.listdir(libdir):
            if f.endswith(".kicad_mod"): os.remove(os.path.join(libdir, f))
    os.makedirs(libdir, exist_ok=True)
    io = pcbnew.PCB_IO_MGR.PluginFind(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    done = set()
    for fp in g.b.GetFootprints():
        name = fp.GetValue()
        if name in done: continue
        done.add(name)
        m = fp.Duplicate()
        m.SetOrientationDegrees(0); m.SetPosition(V(0, 0)); m.SetReference("REF**")
        for pad in m.Pads(): pad.SetNetCode(0)
        io.FootprintSave(libdir, m)
    return sorted(done)

def add_zones(g, outline):
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(g.b); z.SetLayer(layer); z.SetNet(g.net("GND"))
        z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in outline: ch.Append(V(x, y))
        ch.SetClosed(True); z.Outline().AddOutline(ch)
        g.b.Add(z)

PRO = '''{
  "board": {"design_settings": {"defaults": {"board_outline_line_width": 0.1},
    "rules": {"min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.5,
              "min_through_hole_diameter": 0.3, "min_hole_to_hole": 0.25,
              "min_copper_edge_clearance": 0.25}}},
  "meta": {"filename": "pacino.kicad_pro", "version": 3},
  "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.3,
                                "via_diameter": 0.6, "via_drill": 0.3}]},
  "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
  "sheets": [], "text_variables": {}
}
'''

NICE_VIEW = {"1", "14", "15", "16"}     # the display's CS / MISO / SCK / MOSI

def zmk_pins():
    """A matrix hole's pin depends on which way up the board is: the flip swaps the controller's two
    pin rows (pad n <-> pad 25-n) but not the position along a row."""
    left  = {n: PRO_MICRO[n] for n in MCU_MATRIX}
    right = {n: PRO_MICRO[25 - n] for n in MCU_MATRIX}
    bad = [(n, MCU_MATRIX[n], left[n], right[n]) for n in MCU_MATRIX
           if left[n] in NICE_VIEW or right[n] in NICE_VIEW or not left[n].isdigit()
           or not right[n].isdigit()]
    if bad:
        sys.exit("matrix hole lands on an unusable pin on one of the halves: %r" % bad)
    order = [(20, 19, 18, 17, 13), (5, 6, 7, 8, 12)]        # rows 0..4, cols 0..4
    return left, right, order

BOM = [("20", "Kailh MX hot-swap socket", "CPG151101S11, one per key, on the face you assemble"),
       ("20", "1N4148W diode", "SOD-123; a through-hole 1N4148 on 3.3 mm pitch fits the same land"),
       ("20", "MX switch", "plate-mount 3-pin or PCB-mount 5-pin, 3x 1.25u for the thumbs"),
       ("1", "nice!nano v2 / nRF52840 SuperMini", "component side DOWN on 3.5 mm low-profile sockets"),
       ("2", "1x12 machined low-profile socket", "Mill-Max and similar; a normal stamped 2.54 header "
        "stands ~8.5 mm and will not fit under the plate"),
       ("2", "1x12 machined pin strip", "into the controller's castellations, pins out of its COMPONENT "
        "side. Measure board surface to controller underside with a pin seated: that is mcu_socket_h "
        "(3.5 mm by default, and it cannot go below 3.5 -- the USB shell hangs 3.2 mm under the board)"),
       ("1", "12x12 mm THT tactile switch", "reset, tall plunger, through the plate window"),
       ("1", "SS12D00 slide switch", "power, through the plate window"),
       ("1", "LiPo cell %(cell)s", "%(where)s")]

def report(g, info, keys, rc, path, v):
    left, right, order = zmk_pins()
    ds = g.b.GetDesignSettings()
    rows = ["| net | hole | left half | right half |", "|---|---|---|---|"]
    for grp, names in zip(order, (["ROW%d" % i for i in range(5)], ["COL%d" % i for i in range(5)])):
        for n, name in zip(grp, names):
            rows.append("| `%s` | U1 pad %d | `pro_micro %s` | `pro_micro %s` |"
                        % (name, n, left[n], right[n]))
    bom = ["| qty | part | notes |", "|---|---|---|"] + \
          ["| %s | %s | %s |" % tuple(x % v if "%(" in x else x for x in b) for b in BOM]
    txt = LIB_README % dict(
        keys=len(keys), nets=len(g.nets), tracks=g.tracks, vias=g.vias, name=v["name"],
        case=v["case"], cell=v["cell"], where=v["where"], leads=v["leads"], key=v["key"],
        matrix="\n".join(rows), bom="\n".join(bom))
    open(path, "w").write(txt)
    return left, right

LIB_README = """# %(name)s

The board for the slim build whose cell sits **%(where)s**.
Cell: **%(cell)s**.  Case half: [`variants/%(case)s`](../../variants/%(case)s/).

The two slim builds are two boards, not one board with an option: moving the cell moves the bay, two
of the mounting holes and the reset/power positions. The matrix, the footprints and the firmware are
identical between them.

Generated by [`tools/pcb_gen.py`](../../tools/pcb_gen.py) -- **do not hand-edit
`%(name)s.kicad_pcb`**; change the generator (or `keyboard.scad`, which the outline and every
position come from) and re-run it. There is no schematic file: the generator declares every net and
every connection, and names the nets the way the ZMK shield names them.

    tools/pcb_gen.py                 # both boards
    tools/pcb_gen.py --variant=%(key)s  # just this one

%(keys)d keys, %(nets)d nets, %(tracks)d tracks, %(vias)d vias. Two layers, 1.6 mm, 0.3 mm tracks,
0.2 mm clearance, 0.3 mm smallest drill -- inside every fab's cheapest process.

## One board, both halves

The board is **reversible**: build the left half with the parts on the back, flip the board over and
build the right half with the parts on the front. The silkscreen on each face says which half it is.
Three things make that work.

**Switches.** Every switch footprint carries *both* MX pin diagonals -- the normal pair and its 180
degree rotation -- and a hot-swap socket land on each face. On the right half the switches and the
sockets go in **rotated 180 degrees**; MX switches are square and their stems are symmetric, so
nothing about the feel, the keycaps or the plate changes. (Mirroring the pin pair instead, which is
the obvious way to do it, puts two 3 mm holes 2.84 mm apart -- they would merge into a slot.)

**Matrix.** Flipping the board swaps the controller's two pin rows but not the position along a row,
so each hole is one pin on the left half and a different one on the right. The ten matrix holes were
chosen so that *both* of their pins are usable GPIOs and neither is one of `pro_micro 1/14/15/16` --
the nice!view's CS/MISO/SCK/MOSI stay free on both halves. The two halves therefore need different
pin lists in ZMK -- which is why the slim build has its own shield, `pacino_pcb`, whose two overlays
differ from each other (the hand-wired `pacino` shield is unchanged and unrelated):

%(matrix)s

**Power.** RAW and GND have no symmetric partner, so each gets a three-pad solder jumper: bridge the
centre pad to the pad marked **L** or **R** for the half you are building (the mark is on the face
you are soldering). Reset needs no jumper -- the switch sits across the `(rowA,3)`/`(rowB,3)` pair,
which is GND/RST one way up and RST/GND the other.

| jumper | bridge to | left half | right half |
|---|---|---|---|
| `JP1` RAW | centre -> L or R | pad 24 = `RAW` | pad 1 = `RAW` |
| `JP2` GND | centre -> L or R | pad 4 = `GND` | pad 21 = `GND` |

## Assembly

1. Pick your half and work on **that face only** -- the one whose silkscreen names your half.
2. Diodes: cathode (the bar) towards the marked end. The land takes a SOD-123 on either face, or a
   through-hole 1N4148 bent to 3.3 mm.
3. Hot-swap sockets, one per key, on the same face. **Right half: rotated 180 degrees**, into the
   land that is there for it.
4. Reset and slide switch: through-hole, bodies on the *other* face -- they poke up through their
   windows in the plate.
5. Sockets for the controller on the same face as everything else; the nice!nano goes in
   **component side down**, USB towards the notch in the wall.
6. Bridge `JP1` and `JP2` to the pad marked for your half.
7. %(leads)s

## Bill of materials (per half)

%(bom)s

Plus, from the case: 8 x M2x4x3.5 heat-set inserts, 8 x M2 screws, 8 x 10 mm bumpons.

## Ordering

Two-layer, 1.6 mm, any finish, no controlled impedance. `%(name)s_gerbers.zip` is ready to upload.
Order it twice over (or ten boards, which is the usual minimum) -- the same board is both halves.
"""

def fab(path, outdir, name):
    """gerbers + drill, zipped, if kicad-cli is around"""
    from shutil import which, rmtree, make_archive
    cli = which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    if not os.path.exists(cli): return None
    tmp = os.path.join(outdir, "_gerbers")
    if os.path.isdir(tmp): rmtree(tmp)
    os.makedirs(tmp)
    for args in (["pcb", "export", "gerbers", "--no-protel-ext", "--output", tmp, path],
                 ["pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th",
                  "--output", tmp, path]):
        r = subprocess.run([cli, *args], capture_output=True, text=True)
        if r.returncode: print("  gerber export failed:", r.stderr.strip()[:200]); rmtree(tmp); return None
    z = make_archive(os.path.join(outdir, "%s_gerbers" % name), "zip", tmp)
    rmtree(tmp)
    return z

def one(key):
    """generate one of the two slim boards into pcb/<key>/"""
    global SCAD_ARGS, LIBNAME
    v = VARIANTS[key]
    SCAD_ARGS = v["scad"] + ARGV
    LIBNAME = v["name"]
    out = os.path.join(ROOT, "pcb", key)
    os.makedirs(out, exist_ok=True)
    g, info, outline, rc, keys, diode_at, colxs = build()
    local_routes(g, keys, rc, diode_at, colxs)
    r = Router(outline, OBST)
    failed = connect_all(g, r)
    add_zones(g, outline)
    libs = export_library(g, os.path.join(out, "%s.pretty" % v["name"]))
    open(os.path.join(out, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")'
        '(uri "${KIPRJMOD}/%s.pretty")(options "")(descr "Pacino, generated by tools/pcb_gen.py"))\n)\n'
        % (v["name"], v["name"]))
    path = os.path.join(out, "%s.kicad_pcb" % v["name"])
    pcbnew.SaveBoard(path, g.b)
    open(os.path.join(out, "%s.kicad_pro" % v["name"]), "w").write(PRO)
    fb = pcbnew.LoadBoard(path)                      # pour on a board that has been through the parser
    pcbnew.ZONE_FILLER(fb).Fill(fb.Zones())
    pcbnew.SaveBoard(path, fb)
    left, right = report(g, info, keys, rc, os.path.join(out, "README.md"), v)
    z = fab(path, out, v["name"])
    print("  %-5s %-28s %2d nets, %3d tracks, %2d vias, %d footprints%s"
          % (key, os.path.relpath(path, ROOT), len(g.nets), g.tracks, g.vias, len(libs),
             "  gerbers" if z else ""))
    for net, a, b in failed:
        print("      UNROUTED %-6s (%.1f,%.1f) -> (%.1f,%.1f)" % (net, a[1], a[2], b[1], b[2]))
    return failed, left, right

def main():
    bad = 0
    for key in WANT:
        if key not in VARIANTS: sys.exit("unknown variant %r (have: %s)" % (key, ", ".join(VARIANTS)))
        failed, left, right = one(key)
        bad += len(failed)
    for half, pins in (("left ", left), ("right", right)):     # identical for both boards
        print("  ZMK %s  row-gpios: %-18s col-gpios: %s"
              % (half, " ".join(pins[n] for n in (20, 19, 18, 17, 13)),
                 " ".join(pins[n] for n in (5, 6, 7, 8, 12))))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
