#!/usr/bin/env python3
"""Bootstrap files for designing the Pacino PCB (the build = "pcb" thin variant) in KiCad:

  docs/pcb/pacino_edge_cuts.dxf   the board outline (cavity - 0.5 mm, battery cutout, M2 boss holes)
  docs/pcb/pacino_placement.csv   switch / hole / MCU / battery positions, in model and KiCad coords

Model frame: X right, Y up, origin = centre of the bottom pinky key (left half).
KiCad frame: Y down; the CSV's kicad columns place the origin key at (KX0, KY0).
Import the DXF onto Edge.Cuts; place footprints at the CSV coordinates (kbplacer takes CSVs too).
The right half is the mirror image; with a reversible design one board serves both.

Usage: tools/kicad_placement.py [-D ...openscad overrides...]
"""
import csv, os, re, shutil, subprocess, sys

OPENSCAD = shutil.which("openscad") or "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
KX0, KY0 = 60.0, 120.0
args = sys.argv[1:] + ["-D", 'build="pcb"']
os.makedirs("docs/pcb", exist_ok=True)
out = subprocess.run([OPENSCAD, "-D", 'part="info"', *args, "-o", "/tmp/_kp.stl", "keyboard.scad"],
                     capture_output=True, text=True).stderr
info = "".join(l.replace("ECHO: ", "") for l in out.splitlines() if l.startswith("ECHO: "))
def arr(name):
    m = re.search(name + r' = (\[.*?\])(?=, [a-z_]+ =|$)', info); return eval(m.group(1))
keys, holes, mcu, batt = arr("keys"), arr("holes"), arr("mcu"), arr("battery_c")
subprocess.run([OPENSCAD, "--backend=Manifold", "-q", "-D", 'part="pcb_outline_2d"', *args,
                "-o", "docs/pcb/pacino_edge_cuts.dxf", "keyboard.scad"], check=True)
with open("docs/pcb/pacino_placement.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["type", "ref", "x_model", "y_model", "rot_deg", "x_kicad", "y_kicad", "note"])
    for i, k in enumerate(keys):
        w.writerow(["switch", "SW%d" % (i + 1), k[0], k[1], k[2], round(KX0 + k[0], 3), round(KY0 - k[1], 3),
                    "%gu MX hotswap" % k[3]])
    for i, h in enumerate(holes):
        w.writerow(["hole", "H%d" % (i + 1), h[0], h[1], 0, round(KX0 + h[0], 3), round(KY0 - h[1], 3),
                    "M2 clearance 2.2, screw passes into the case boss below"])
    w.writerow(["mcu", "U1", mcu[0], mcu[1], mcu[2], round(KX0 + mcu[0], 3), round(KY0 - mcu[1], 3),
                "nice!nano footprint, USB towards +Y (model) / -Y (KiCad)"])
    w.writerow(["keepout", "BAT", batt[0], batt[1], 0, round(KX0 + batt[0], 3), round(KY0 - batt[1], 3),
                "battery pokes through the board cutout here (already in the Edge.Cuts DXF)"])
print("wrote docs/pcb/pacino_edge_cuts.dxf and docs/pcb/pacino_placement.csv (%d switches, %d holes)"
      % (len(keys), len(holes)))
