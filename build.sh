#!/usr/bin/env bash
# Build every exportable part of keyboard.scad into out/:
#   out/<part>_<side>.step        real B-rep for Fusion 360      (needs FreeCAD)
#   out/<part>_<side>.3mf / .stl  meshes for slicers
#   out/<profile>_<side>.dxf      2D profiles for Fusion sketches
#   out/preview_*.png             renders
# Parts: case + plate.  WITH_DISPLAY=1 adds the nice!view version (case_display, plate_display, bezel).
#
# Usage:  ./build.sh                    build everything
#         ./build.sh step [mesh] [dxf] [png]   only those
# Env:    OPENSCAD=... FREECADCMD=... to override binaries; SCAD_ARGS='-D switch_type="choc"' for overrides;
#         OUT=dir output directory; SUFFIX=_x file-name suffix; STL=0 to skip .stl; PREVIEWS=min for two previews only;
#         CARRY=1 adds the carry case tray (carry_tray, both sides, its previews and its clash check), CARRY=only builds just that.
set -euo pipefail
cd "$(dirname "$0")"

OPENSCAD=${OPENSCAD:-$(command -v openscad || echo /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD)}
FREECADCMD=${FREECADCMD:-$(command -v freecadcmd || echo /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd)}
SCAD_ARGS=${SCAD_ARGS:-}
SUFFIX=${SUFFIX:-}          # e.g. SUFFIX=_2000mah SCAD_ARGS='-D battery_type="103450"' ./build.sh
SRC=keyboard.scad
OUT=${OUT:-out}
SIDES=(left right)
# "<output name>:<part>:<extra -D args>"
VARIANTS=(
  "case:case:"
  "plate:plate:"
)
PROFILES=(
  "plate_2d:plate_2d:"
  "case_outline_2d:case_outline_2d:"
  "cavity_2d:cavity_2d:"
)
# WITH_DISPLAY=1 ./build.sh also builds the nice!view version (case_display, plate_display, bezel);
# BEZEL=1 adds just the bezel part (for builds where SCAD_ARGS already turns nice_view on)
if [[ ${WITH_DISPLAY:-0} == 1 ]]; then
  VARIANTS+=("case_display:case:-D nice_view=true" "plate_display:plate:-D nice_view=true" "bezel:bezel:-D nice_view=true")
  PROFILES+=("plate_display_2d:plate_2d:-D nice_view=true" "bezel_2d:bezel_2d:-D nice_view=true" "case_outline_display_2d:case_outline_2d:-D nice_view=true")
fi
[[ ${BEZEL:-0} == 1 ]] && VARIANTS+=("bezel:bezel:")
# CARRY=1 adds the carry case tray; CARRY=only builds nothing but the tray (and its previews)
if [[ ${CARRY:-0} == only ]]; then VARIANTS=("carry_tray:carry_tray:"); PROFILES=(); elif [[ ${CARRY:-0} == 1 ]]; then VARIANTS+=("carry_tray:carry_tray:"); fi
what=" ${*:-all} "
want() { [[ $what == *" all "* || $what == *" $1 "* ]]; }

mkdir -p "$OUT"
scad() { # scad <output> <part> <side> [extra args]
  local o=$1 p=$2 s=$3; shift 3
  "$OPENSCAD" --backend=Manifold -q -D "part=\"$p\"" -D "side=\"$s\"" $SCAD_ARGS "$@" -o "$o" "$SRC"
  echo "  $o"
}

if want mesh; then
  echo "== meshes"
  for s in "${SIDES[@]}"; do for v in "${VARIANTS[@]}"; do
    IFS=: read -r name part extra <<<"$v"
    scad "$OUT/${name}${SUFFIX}_${s}.3mf" "$part" "$s" $extra
    [[ ${STL:-1} == 0 ]] || scad "$OUT/${name}${SUFFIX}_${s}.stl" "$part" "$s" $extra --export-format binstl
  done; done
  if [[ ${CARRY:-0} != 0 ]]; then   # the tray's own fit check: every magnet has tray round it, the two trays shut without touching
    rm -f "$OUT/_carry_clash.stl"
    "$OPENSCAD" --backend=Manifold -q -D 'part="carry_clash"' $SCAD_ARGS -o "$OUT/_carry_clash.stl" --export-format binstl "$SRC" 2>/dev/null || true
    if [[ -s $OUT/_carry_clash.stl ]]; then echo "  WARNING: carry_clash is not empty -- a magnet breaks into the pocket, or the trays foul each other (part = \"carry_clash\")" >&2
    else echo "  carry_clash: empty"; fi
    rm -f "$OUT/_carry_clash.stl"
  fi
fi

if want dxf; then
  echo "== dxf profiles"
  for s in "${SIDES[@]}"; do for v in "${PROFILES[@]}"; do
    IFS=: read -r name part extra <<<"$v"
    scad "$OUT/${name}${SUFFIX}_${s}.dxf" "$part" "$s" $extra
  done; done
fi

if want step; then
  echo "== step (via FreeCAD)"
  if [[ ! -x $FREECADCMD ]]; then echo "  freecadcmd not found, skipping STEP" >&2; else
  # OCC's 2D offsetting chokes on the fused key outline, so bake the cavity polygon with OpenSCAD
  # (Clipper) first and feed it back in; FreeCAD then only sees a polygon plus small offsets.
  for s in "${SIDES[@]}"; do for v in "${VARIANTS[@]}"; do
    IFS=: read -r name part extra <<<"$v"
    # bake the outline for this variant's parameters (8 segments per quarter turn keeps the STEP face count sane)
    scad "$OUT/_cavity_bake.svg" cavity_2d left $extra -D \$fn=32 >/dev/null
    POLY=$(python3 tools/svg_polygon.py "$OUT/_cavity_bake.svg")
    if [[ $part == carry_tray ]]; then   # and the tray's pocket the same way (its 2D offsets are of the outline, the cable pocket and the finger well)
      scad "$OUT/_pocket_bake.svg" carry_pocket_2d left $extra -D \$fn=32 >/dev/null
      extra="$extra -D carry_pocket_polygon=$(python3 tools/svg_polygon.py "$OUT/_pocket_bake.svg")"
    fi
    scad "$OUT/${name}${SUFFIX}_${s}.csg" "$part" "$s" $extra -D "cavity_polygon=$POLY"
    CSG_IN="$OUT/${name}${SUFFIX}_${s}.csg" STEP_OUT="$OUT/${name}${SUFFIX}_${s}.step" "$FREECADCMD" tools/csg2step.py 2>&1 \
      | grep -E "^STEP|failed to|not valid|no shapes|usage|Exception" || true
  done; done
  rm -f "$OUT/_cavity_bake.svg" "$OUT/_pocket_bake.svg"
  fi
fi

if want png; then
  echo "== previews"
  png() { local o=$1; shift; "$OPENSCAD" --preview -q --autocenter --viewall --imgsize=1600,1100 --colorscheme=Tomorrow "$@" $SCAD_ARGS -o "$o" "$SRC"; echo "  $o"; }
  if [[ ${CARRY:-0} != 0 ]]; then   # the carry case: the pair laid out like an open book, and shut
  png "$OUT/preview_carry.png"        --camera=0,0,0,50,0,0,300 -D 'part="carry_open"' -D 'side="both"'
  png "$OUT/preview_carry_closed.png" --camera=0,0,0,55,0,25,300 -D 'part="carry_closed"'
  fi
  if [[ ${CARRY:-0} != only ]]; then
  png "$OUT/preview_assembly.png"  --camera=0,0,0,55,0,25,300 -D 'part="assembly"'
  png "$OUT/preview_top.png"       --projection=o --camera=0,0,0,0,0,0,300 -D 'part="assembly"' -D show_keycaps=false
  fi
  if [[ ${PREVIEWS:-all} != min && ${CARRY:-0} != only ]]; then
  png "$OUT/preview_exploded.png"  --camera=0,0,0,55,0,25,300 -D 'part="assembly"' -D explode=25
  png "$OUT/preview_case.png"      --camera=0,0,0,55,0,200,300 -D 'part="case"'
  png "$OUT/preview_bottom.png"    --projection=o --camera=0,0,0,180,0,0,300 -D 'part="case"'
  png "$OUT/preview_plate.png"     --camera=0,0,0,125,0,20,300 -D 'part="plate"'
  png "$OUT/preview_both.png"      --camera=0,0,0,50,0,0,300 -D 'part="assembly"' -D 'side="both"'
  "$OPENSCAD" --backend=Manifold --render -q --imgsize=2000,800 --colorscheme=Tomorrow --projection=o --camera=33,9,0,0,0,0,80 -D 'part="section"' -D show_keycaps=false $SCAD_ARGS -o "$OUT/preview_section.png" "$SRC"; echo "  $OUT/preview_section.png"
  fi
fi
echo "done."
