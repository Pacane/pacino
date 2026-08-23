#!/usr/bin/env bash
# Build every option combination into variants/<name>/ (STEP for Fusion, 3MF for slicing, two previews)
# and write variants/README.md as an index.  Takes ~15 minutes.
set -euo pipefail
cd "$(dirname "$0")"
OPENSCAD=${OPENSCAD:-$(command -v openscad || echo /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD)}
ROOT=variants
mkdir -p "$ROOT"
INDEX="$ROOT/README.md"
{
  echo "# Variants"
  echo
  echo "Every combination of the four options. Each directory has \`case_{left,right}\` and \`plate_{left,right}\`"
  echo "as **.step** (Fusion 360 / CAD) and **.3mf** (slicer), plus a bezel for the display versions, previews, and a"
  echo "\`wiring_guide.png\` showing the underside with the floor pillars and clash-free example row/column wires."
  echo "Print the plate top-side down, the case as-is; hardware and assembly notes are in the main README."
  echo
  echo "| variant | columns | keys/half | battery | nice!view | half size (mm) | preview |"
  echo "|---|---|---|---|---|---|---|"
} > "$INDEX"

measure() { # prints "W x H"
  "$OPENSCAD" --backend=Manifold -q -D 'part="case_outline_2d"' $1 -o "$ROOT/_m.svg" keyboard.scad
  python3 - "$ROOT/_m.svg" <<'PY'
import re, sys
s=open(sys.argv[1]).read(); pts=[(float(x),-float(y)) for x,y in re.findall(r'([-\d.eE+]+),([-\d.eE+]+)', s)]
xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; print("%.0f × %.0f" % (max(xs)-min(xs), max(ys)-min(ys)))
PY
}

for cols in 5 6; do for extra in no yes; do for bat in 902030 103450; do for disp in no yes; do
  name="${cols}col"; args="-D grid_outer_col=$([[ $cols == 6 ]] && echo true || echo false)"
  if [[ $extra == yes ]]; then name+="_extra2"; args+=" -D grid_extra_keys=[[1,-1],[2,-1]]"; else name+="_noextra"; args+=" -D grid_extra_keys=[]"; fi
  name+="_bat$bat"; args+=" -D battery_type=\"$bat\""
  if [[ $disp == yes ]]; then name+="_display"; args+=" -D nice_view=true"; bezel=1; else name+="_nodisplay"; args+=" -D nice_view=false"; bezel=0; fi
  ek=0; [[ $extra == yes ]] && ek=2
  keys=$(( cols*3 + ek + 3 ))
  if [[ -z ${ONLY:-} || $name == *${ONLY}* ]]; then   # ONLY=substring rebuilds a subset; the index is always complete
    echo "=== $name"
    rm -rf "$ROOT/$name"; mkdir -p "$ROOT/$name"
    OUT="$ROOT/$name" SCAD_ARGS="$args" STL=0 PREVIEWS=min BEZEL=$bezel ./build.sh step mesh png 2>&1 | grep -E "STEP|ERROR|fail|Exception" | sed 's/^/  /' || true
    rm -f "$ROOT/$name"/*.csg
    python3 tools/wiring_guide.py -o "$ROOT/$name" $args | sed 's/^/  /'
  fi
  size=$(measure "$args")
  echo "| [\`$name\`]($name/) | $cols | $keys | $bat | $disp | $size | ![]($name/preview_top.png) |" >> "$INDEX"
done; done; done; done
rm -f "$ROOT/_m.svg"
echo "done: $ROOT/"
