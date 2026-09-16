#!/usr/bin/env python3
"""Wrap an OpenSCAD-exported case .3mf as a Bambu Studio project with a support blocker over the MagSafe ring.

The ring pocket reaches the build plate through its window, so a slicer generating support (say, for the
bumpon recesses) fills the pocket with it.  Bambu Studio / Orca read a project 3MF whose object has a second
part tagged "support_blocker"; plain 3MF readers (Cura) would print that part, so this is a separate file.

    tools/bambu_3mf.py variants/<v>/case_left.3mf [-o variants/<v>/case_left.bambu.3mf]
                       [--at X,Y] [--r 30] [--h 1.5] [--plate 128,128]

--at is the ring centre in model coordinates (default 57,28 = magsafe_pos); the right half is mirrored in X and
the script notices from the mesh.  Output is deterministic (fixed zip timestamps) so rebuilds do not churn.
"""
import argparse, math, os, re, sys, zipfile

MODEL_NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
STAMP = (2026, 1, 1, 0, 0, 0)


def read_mesh(path):
    xml = zipfile.ZipFile(path).read("3D/3dmodel.model").decode()
    V = [(float(x), float(y), float(z)) for x, y, z in re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', xml)]
    T = [(int(a), int(b), int(c)) for a, b, c in re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', xml)]
    if not V or not T:
        sys.exit("%s: no mesh found" % path)
    return V, T


def cylinder(cx, cy, r, h, n=64):
    V = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z)
         for z in (0.0, h) for i in range(n)]
    V += [(cx, cy, 0.0), (cx, cy, h)]
    cb, ct = 2 * n, 2 * n + 1
    T = []
    for i in range(n):
        j = (i + 1) % n
        T += [(i, cb, j), (n + i, n + j, ct), (i, j, n + j), (i, n + j, n + i)]
    return V, T


def mesh_xml(oid, V, T, kind, uuid):
    out = ['  <object id="%d" p:UUID="%s" type="%s">\n   <mesh>\n    <vertices>\n' % (oid, uuid, kind)]
    out += ['     <vertex x="%g" y="%g" z="%g"/>\n' % v for v in V]
    out.append('    </vertices>\n    <triangles>\n')
    out += ['     <triangle v1="%d" v2="%d" v3="%d"/>\n' % t for t in T]
    out.append('    </triangles>\n   </mesh>\n  </object>\n')
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("-o", "--out")
    ap.add_argument("--at", default="57,28", help="ring centre X,Y in model coordinates (left half)")
    ap.add_argument("--r", type=float, default=30.0, help="blocker radius")
    ap.add_argument("--h", type=float, default=1.5, help="blocker height (must cover the pocket ceiling)")
    ap.add_argument("--plate", default="128,128", help="where to put the case's centre on the plate")
    a = ap.parse_args()
    out = a.out or re.sub(r"\.3mf$", "", a.case) + ".bambu.3mf"
    cx, cy = (float(v) for v in a.at.split(","))
    V, T = read_mesh(a.case)
    xs = [v[0] for v in V]; ys = [v[1] for v in V]
    if max(xs) + min(xs) < 0:            # the right half is the left mirrored in X
        cx = -cx
    if not any(abs(v[2] - 0.0) < 1e-6 for v in V):
        sys.exit("%s: the mesh does not sit on z = 0" % a.case)
    BV, BT = cylinder(cx, cy, a.r, a.h)
    px, py = (float(v) for v in a.plate.split(","))
    tx, ty = px - (max(xs) + min(xs)) / 2, py - (max(ys) + min(ys)) / 2
    tf = "1 0 0 0 1 0 0 0 1 %g %g 0" % (tx, ty)
    name = os.path.basename(a.case).replace(".3mf", "")

    objects = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" %s>\n'
               ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n' % MODEL_NS
               + mesh_xml(1, V, T, "model", "00010000-81cb-4c03-9d28-80fed5dfa1dc")
               + mesh_xml(2, BV, BT, "other", "00010001-81cb-4c03-9d28-80fed5dfa1dc")
               + ' </resources>\n <build/>\n</model>\n')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" %s>\n' % MODEL_NS
             + ' <metadata name="Application">pacino tools/bambu_3mf.py</metadata>\n'
               ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
               ' <metadata name="Title">%s</metadata>\n <resources>\n'
               '  <object id="3" p:UUID="00000001-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n   <components>\n'
               '    <component p:path="/3D/Objects/object_1.model" objectid="1" p:UUID="00010000-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
               '    <component p:path="/3D/Objects/object_1.model" objectid="2" p:UUID="00010001-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
               '   </components>\n  </object>\n </resources>\n'
               ' <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">\n'
               '  <item objectid="3" p:UUID="00000002-b1ec-4553-aec9-835e5b724bb4" transform="%s" printable="1"/>\n'
               ' </build>\n</model>\n' % (name, tf))
    settings = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <object id="3">\n'
                '    <metadata key="name" value="%s"/>\n    <metadata key="extruder" value="1"/>\n'
                '    <part id="1" subtype="normal_part">\n      <metadata key="name" value="%s"/>\n'
                '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                '      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                '    </part>\n'
                '    <part id="2" subtype="support_blocker">\n      <metadata key="name" value="MagSafe ring: no support"/>\n'
                '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                '      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                '    </part>\n  </object>\n'
                '  <plate>\n    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value=""/>\n'
                '    <metadata key="locked" value="false"/>\n'
                '    <model_instance>\n      <metadata key="object_id" value="3"/>\n      <metadata key="instance_id" value="0"/>\n'
                '      <metadata key="identify_id" value="1"/>\n    </model_instance>\n  </plate>\n'
                '  <assemble>\n   <assemble_item object_id="3" instance_id="0" transform="%s" offset="0 0 0" />\n  </assemble>\n'
                '</config>\n' % (name, name, tf))
    files = {
        "[Content_Types].xml": ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                                ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
                                ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n</Types>\n'),
        "_rels/.rels": ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n'),
        "3D/3dmodel.model": model,
        "3D/_rels/3dmodel.model.rels": ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                                        ' <Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n'),
        "3D/Objects/object_1.model": objects,
        "Metadata/model_settings.config": settings,
    }
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n, body in files.items():
            zi = zipfile.ZipInfo(n, date_time=STAMP); zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, body)
    print("  %s  (blocker r=%g h=%g at %g,%g)" % (out, a.r, a.h, cx, cy))


if __name__ == "__main__":
    main()
