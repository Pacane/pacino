// keyboard.scad — parametric split keyboard case + switch plate (one half; mirrored for the other)
//
// Default design: cheapino-style 3x5+3 column-stagger layout on a clean 19.05 mm MX grid (1.25u
// portrait thumbs), hand-wired, with an electronics bay beside the inner column holding a LiPo (in
// the case floor), a nice!nano in a cradle that is part of the plate (USB out through the wall),
// and a reset button + power switch below it.  Optional nice!view (nice_view = true).
//
// Tested with OpenSCAD 2025.03 (Manifold backend).  See README.md for the Fusion 360 workflow.
//
// Frame: mm, X right, Y up (away from you), Z up.  Origin = centre of the bottom pinky key of the
// LEFT half.  side="right" mirrors everything in X.
//
// Vertical stack, z=0 at the underside of the case; the wall top is flush with the plate underside:
//   build="plate":  floor_t | cavity_depth                      | plate      (no main PCB; handwire / amoeba PCBs)
//   build="pcb":    floor_t | pcb_lift | PCB | plate_to_pcb-plate_t | plate   (PCB sandwich)

include <layouts/cheapino.scad>
include <layouts/badtemper.scad>

/* [Output] */
part = "assembly"; // [assembly, section, case, plate, bezel, insert_test, plate_2d, case_outline_2d, cavity_2d, pcb_2d, pcb_outline_2d, bezel_2d, info]
// part = "section": 2D cross-section of the assembly through the plane x = section_x (Y across, Z up)
section_x = 123;
side = "left"; // [left, right, both]
// gap between the halves when side = "both"
both_gap = 30;
// lift the plate + keycaps in the assembly view
explode = 0; // [0:1:40]
show_keycaps = true;
show_switches = true;
show_electronics = true;

/* [Layout] */
// grid = parametric column stagger below (default: cheapino geometry on a 19.05 grid);
// cheapino / badtemper = exact positions from those KiCad boards (layouts/*.scad)
layout = "grid"; // [grid, cheapino, badtemper]
grid_rows = 3;
grid_cols = 5;
// per-column Y offset in mm, index 0 = pinky  (cheapino: 0, 10, 16.4, 10, 7.5)
grid_stagger = [0, 10, 16.4, 10, 7.5];
// optional 6th column outside the pinky column (Corne-style 3x6), with its own stagger
grid_outer_col = false;
grid_outer_stagger = 0;
// extra keys as [column, row] on the grid (row -1 = below the bottom row): two keys under the ring and middle
// columns, i.e. under X/C on the left half and ,/. on the right.  [] = none
grid_extra_keys = [[1, -1], [2, -1]];
// thumb keys [x, y, rotation_deg, width_u]: 1.25u caps standing "portrait" (rotation = 90 + fan) so the
// long side points up at the columns, fanned -10/-22/-34 deg around the thumb, 21.8 mm pitch along the arc
// (~1.5 mm between caps at their lower ends, 1.7 mm to the bottom row); first key where the cheapino has it
grid_thumbs = [[71.5, -15.5, 80, 1.25], [92.5, -21.5, 68, 1.25], [111.7, -31.7, 56, 1.25]];
// mounting bosses / plate screws [x, y] around the key block: on the perimeter (0.5 mm inside the inner
// wall line, so they merge into the wall) keeping the matrix clear for hand-wiring; >= 2 mm to switch bodies.
// (Two on the left edge follow the outer column, and two on the bay's right-hand corners are automatic.)
grid_holes = [[38.1, 66], [76.2, 57.1], [58.5, -4.4], [112, -48.2]];

/* [Switch] */
switch_type = "mx"; // [mx, choc]
// add the 0.8 mm side reliefs for MX switch clips
cutout_notches = false;
// 0 = default for the switch type (MX 1.5, Choc 1.3)
plate_thickness_override = 0;

/* [Build] */
// plate = switches clip into the plate, no main PCB, bosses run floor-to-plate, MCU cradle in the plate;
// pcb = PCB sandwich: bosses stop at the PCB, plate gets spacer bosses, MCU sits on the PCB
build = "plate"; // [plate, pcb]
// plate build: cavity depth below the plate underside. 0 = automatic: whatever the battery + nano cradle
// stack needs (battery + 4), but at least 10 so there is room under the MX pins for diodes and wires.
// (9-10 mm cells come out at 13.5-14.5, a 6 mm cell at 10.)
cavity_depth = 0;
// pcb build: PCB underside above the floor. 0 = automatic: hotswap sockets (2.4) or whatever makes the
// battery -- which sits on the floor, poking through a cutout in the PCB -- fit under the plate
pcb_lift = 0;
pcb_t = 1.6;
// pcb build: MCU socket height above the PCB
mcu_socket_h = 3.5;

/* [Case] */
wall = 2.4;
// floor thickness (the bumpon recesses take bumpon_depth out of it)
floor_t = 2.5;
// keys = hull the keycaps (+ bay) with key_margin / corner_r;  pcb = follow the layout's Edge.Cuts + pcb_gap
cavity_from = "keys"; // [keys, pcb]
// keycap edge -> inner wall
key_margin = 3;
// radius of the convex (outer) corners
corner_r = 4;
// notches narrower than this get filled (smooths the column stagger steps and the bay/thumb junction)
fill_r = 8;
// PCB edge -> inner wall (cavity_from = "pcb")
pcb_gap = 0.5;

/* [Electronics bay] */
// the bay is a rectangle added to the cavity beside the inner column, sized automatically from its
// contents: width = max(battery, nano [+ nice!view]) + margins, height = max(battery, nano, nice!view) + margins
use_bay = true;
// left edge and top edge of the bay (it hangs from the top edge: USB at the top, and shrinks from the bottom)
bay_left = 86.5;
bay_top_y = 61;
bay_margin = 5;
// force a bay size instead ([w, h]; 0 = auto)
bay_size_override = [0, 0];
// which cell (sets the bay size and the cavity depth): 902030 = 20x30x9 (500 mAh), 103450 = 34x50x10 (2000 mAh),
// 604060 = 40x60x6 (2000 mAh, thin), custom = battery_custom below
battery_type = "902030"; // [902030, 103450, 604060, custom]
// custom LiPo [width x, length y, thickness] -- add ~0.5 to the thickness for swelling
battery_custom = [20, 30, 9.5];
battery_clearance = 0.5;
// battery sits bay_margin from the bay's left and bottom walls; shift it with this
battery_offset = [0, 0];
// locating fence around the battery (height, width); the lead end is left open
battery_fence = [3, 1.2];
// controller board [width, length] -- measured with calipers: SuperMini nRF52840 clone = [18.1, 33]
// (nice!nano = [18, 33.5]).  The latch relies on the pocket being ~1.3 mm longer than the board, so measure.
mcu_size = [18.1, 33];
// PCB thickness (SuperMini measured 1.53; its reset button stands 1.1 mm above the board, centred on the far end)
mcu_pcb_t = 1.55;
mcu_offset = [0, 0];
// board underside above the battery top (plate build; sets the cradle height)
mcu_above_battery = 1.5;
// cradle: end clearance, side clearance (a channel for the wires running down beside the board from pads
// soldered on top), rail thickness, ledge thickness / width
mcu_clearance = 0.3;
mcu_side_clearance = 1.2;
rail_w = 1.5;
ledge_t = 1.2;
ledge_w = 2.5;
// retention: the plate overhangs the far end of the board by mcu_overhang and two tabs beside the USB slot
// hold the USB-end corners down by mcu_tab.  With the plate off the case the cradle is open at the USB end:
// slide the board in from there until it meets the far rail.  Once the plate is on, the case wall closes
// that end and the board can only move mcu_clearance + 1 mm, so both hold-downs stay engaged.
mcu_overhang = 3;
// the far-end overhang (above) and ledge (below) are corner tabs with this gap between them: SuperMini-style
// nRF52840 clones have their reset button on top and the battery pads underneath, both centred on that end
mcu_overhang_gap = 10;
// far-end ledge: a strip under the board's far edge, this deep (1.0 stays clear of the last pin pads at 1.9 mm;
// the clone's four edge-row pads get touched on their outer sliver -- leave those unsoldered or solder from the top)
mcu_far_ledge = 1.0;
// USB end: no plate ledge (the clone's B+/B- pads are right there); a post from the case floor supports the board
// under the USB connector's centre instead: [width, depth], top key_pcb_post_gap below the board. 0 = none
mcu_end_post = [4, 2.5];
mcu_tab = 1;
// vertical play above the board under the overhang / tabs. 0.9 clears a soldered wire lying on the corner pads
// (B+/B- and the last pins sit under the tabs); the board still cannot escape, as it would need to lift its
// full thickness at one end while the other is held. (0.9 is the maximum: the tabs are then the plate itself.)
mcu_lift_gap = 0.9;
// short sections at both ends of the rails (where the board has no pads) come in to mcu_clearance so the
// board is centred sideways despite the wire channels; 0 = none
mcu_locate_len = 1.5;

/* [Bumpons] */
// round recesses in the underside for self-adhesive rubber feet (0 = none)
bumpon_d = 10;
bumpon_clearance = 0.3;
bumpon_depth = 1;
// [x, y] under the key block / thumb cluster; two on the left edge follow the outer column and two more are
// placed automatically on the bay (top-right, lower-right)
bumpon_positions = [[38.1, 58], [15, 20], [71.5, -15.5], [111.7, -31.7]];
// round recess in the underside for a MagSafe magnet ring (56 mm sticker ring); 0 = none
magsafe_d = 56;
magsafe_depth = 1;
magsafe_clearance = 0.3;
// centre: under the index/middle columns, clear of the bumpons and bosses
magsafe_pos = [60, 28];

/* [Reset + power] */
// through-hole parts dropped into pockets in the plate from above: the body passes through the plate,
// the legs go through holes in a small floor hanging under the plate, wires are soldered underneath.
// They live in a "control bay" strip hung below the electronics bay (switches at its right end), off the
// battery, so they do not widen the bay.
reset_button = true;
power_switch = true;
// control bay: spans the full bay width, hung below the bay. The switch pockets sit as high as the
// battery allows (they reach up into the bay's battery-free margin) so they stay clear of the thumb keys.
// ctrl_bay_h = 0 sizes it automatically for the larger of the two switches.
ctrl_bay_h = 0;
ctrl_offset = [0, 0];
// reset: 12x12 mm THT tactile with a tall plunger (12x12x7.3): body [l, w, h without plunger], leg positions
// (5 mm apart per side, 12.5 mm across), and how far the body top sits below the plate top (2.3 leaves the
// 3.3 mm plunger ~1 mm proud).  A 6x6 switch would be [6, 6, 3.5], legs +-2.25 / +-3.25, recess 0.3.
reset_body = [12, 12, 4];
reset_legs = [[-6.25, -2.5], [-6.25, 2.5], [6.25, -2.5], [6.25, 2.5]];
reset_recess = 2.3;
// SS12D00 slide switch (3 mm actuator): body [l, w, h without actuator], leg positions (2.54 pitch)
power_body = [8.7, 3.7, 3.5];
power_legs = [[-2.54, 0], [0, 0], [2.54, 0]];
power_recess = 0;
ctrl_clearance = 0.2;
ctrl_wall = 1.5;
ctrl_floor = 1.2;
// square opening in the floor around each leg -- big enough to wrap and solder a wire to the leg from below
// (adjacent openings merge into a slot); 1.3 would be a plain pin hole
ctrl_leg_hole = 3.5;

/* [nice!view] */
// optional nice!view beside the nano, flush in the plate, clamped by a screw-down bezel (part = "bezel");
// off by default -- it widens the bay by ~8 mm
nice_view = false;
// nice!view PCB [width, length, thickness] -- 36 x 14 x 1.6 per nicekeyboards; measure yours
nv_pcb = [14, 36, 1.6];
// display glass [width, length, height above the PCB] and its centre offset along the board (+ = towards the wall)
nv_glass = [13.2, 31.5, 2.0];
nv_glass_shift = 0;
nv_clearance = 0.3;
// ledges under the long edges (width, thickness) and the ring they hang from
nv_ledge_w = 1;
nv_ledge_t = 1.2;
nv_ring_w = 1.5;
// PCB top sits this much above the plate top so the bezel clamps the PCB, not the plate
nv_preload = 0.15;
// gap between the nano cradle and the display ring
nv_gap = 2;
// bezel: thickness, overhang beyond the pocket, window clearance around the glass, corner radius
nv_bezel_t = 2.5;
nv_bezel_margin = 2.5;
nv_window_clearance = 0.2;
nv_bezel_r = 2;
// bezel screw bosses hanging under the plate: diameter, height, hole (1.7 = M2 self-tapping in PETG, 3.2 = heat-set)
nv_boss_d = 5;
nv_boss_h = 3;
nv_boss_hole_d = 1.7;
nv_bezel_hole_d = 2.3;

/* [Plate stiffening] */
// egg-crate of ribs under the plate: a wall around every switch (outside its clip zone), merging into a grid
plate_ribs = true;
rib_w = 1.5;
// rib height below the plate; 0 = automatic: down to the switch-body bottom, or 0.3 mm above the top of
// single-key hot-swap PCBs when key_pcbs is on
rib_h = 0;
// per-key hot-swap PCBs (amoeba style, ~19 mm wide) hanging on the switches under the plate
key_pcbs = true;
key_pcb_t = 1.6;
// pillars from the case floor under each board's four corners, hugging the TOP and BOTTOM edges (the row
// boundaries), so the column boundaries stay free for the row wires: [length along the edge, depth across it],
// centred key_pcb_post_x from the board centre. They stop key_pcb_post_gap below the boards so a switch being
// inserted cannot push a board off the pins. Sized for the amoeba-king (ROW pads on the left/right edges,
// COL pads + LED pad on the top/bottom edges within 4.4 mm of centre): 3.5 long at x = +-7 stays 0.9 mm
// clear of those pads. 0 length = none
key_pcb_post = [3.5, 2.5];
key_pcb_post_x = 7;
key_pcb_post_gap = 0.2;
// gap between the rib and the switch's 15.6 mm clip zone
rib_clearance = 0.3;

/* [Mounting] */
// case bosses: 6 mm leaves 1.35 mm of wall around a 3.5 mm OD heat-set insert
boss_d = 6;
// 3.3 for M2 x 4 x 3.5 brass heat-set inserts (M2 x 6 screws), 1.7 for self-tapping M2 screws
boss_hole_d = 3.3;
boss_hole_depth = 5;
// screw clearance hole through the plate
screw_d = 2.3;
// pcb build: spacer boss under the plate
plate_boss_d = 5;
// locating lip under the plate (height, width); 0 = none
lip_h = 1;
lip_w = 1.2;
lip_clearance = 0.2;

/* [Cutouts] */
// USB slot at the MCU's connector end: [width, height, z relative to the MCU board top]; open to the top
usb_cutout = [12, 7, -1.5];
// extra wall cutouts: [x, y, outward_normal_angle_deg, width, height, z_above_floor]
extra_cutouts = [];
// extra plate windows [cx, cy, w, h, rot]
plate_windows = [];

/* [Hidden] */
$fn = 64;
eps = 0.01;
// build.sh passes the Clipper-computed cavity outline back in here for the FreeCAD/STEP pass
cavity_polygon = [];

// ---------------------------------------------------------------- derived

is_choc = switch_type == "choc";
px = is_choc ? 18 : 19.05;
py = is_choc ? 17 : 19.05;
cutout = is_choc ? 13.8 : 14;
plate_t = plate_thickness_override > 0 ? plate_thickness_override : (is_choc ? 1.3 : 1.5);
plate_to_pcb = is_choc ? 2.2 : 5.0;     // plate top surface to PCB top surface
cap_w = is_choc ? 17.5 : 18;
cap_d = is_choc ? 16.5 : 18;
body = is_choc ? 13.8 : 14;             // switch body below the plate

x_left = grid_outer_col ? -px : 0;   // x of the outermost column
grid_keys = concat(
  [for (c = [0 : grid_cols - 1], r = [0 : grid_rows - 1]) [c * px, r * py + grid_stagger[c], 0, 1]],
  grid_outer_col ? [for (r = [0 : grid_rows - 1]) [-px, r * py + grid_outer_stagger, 0, 1]] : [],
  [for (e = grid_extra_keys) [e[0] * px, e[1] * py + grid_stagger[e[0]], 0, 1]],
  grid_thumbs);

keys  = layout == "cheapino" ? cheapino_keys  : layout == "badtemper" ? badtemper_keys  : grid_keys;
pcb_outline = layout == "badtemper" ? badtemper_pcb_outline : cheapino_pcb_outline;

battery = battery_type == "103450" ? [34, 50, 10.5] : battery_type == "604060" ? [40, 60, 6.5]
        : battery_type == "902030" ? [20, 30, 9.5] : battery_custom;
has_bay = layout == "grid" && use_bay;
cradle = build == "plate" && has_bay;
has_nv = nice_view && cradle;
has_ctrl = cradle && (reset_button || power_switch);

// electronics footprint across the bay: nano cradle [+ gap + nice!view ring]
nano_w = mcu_size[0] + 2 * (mcu_side_clearance + rail_w);
nv_W   = nv_pcb[0] + 2 * nv_clearance;
nv_L   = nv_pcb[1] + 2 * nv_clearance;
elec_w = nano_w + (has_nv ? nv_gap + nv_W + 2 * nv_ring_w : 0);
nano_l = mcu_size[1] + 2 * mcu_clearance + rail_w + 1;                    // pocket + far rail + gap to the wall
nv_l   = 1 + nv_boss_d + 1 + nv_L + 1 + nv_boss_d;                         // wall gap, boss, gap, pocket, gap, boss
// width: battery + margins, or the electronics row + left margin + room for a wall boss on the right
bay_w  = bay_size_override[0] > 0 ? bay_size_override[0]
       : max(battery[0] + 2 * bay_margin, elec_w + bay_margin + boss_d + 1);   // room for the corner boss beside the cradle
bay_h  = bay_size_override[1] > 0 ? bay_size_override[1]
       : max(battery[1] + 2 * bay_margin, nano_l + bay_margin, has_nv ? nv_l + bay_margin : 0);
bay    = [bay_left, bay_top_y - bay_h, bay_w, bay_h];
bay_cx = bay[0] + bay[2] / 2;
bay_cy = bay[1] + bay[3] / 2;
bay_top = bay[1] + bay[3];
bay_right = bay[0] + bay[2];
batt_c = [bay[0] + bay_margin + battery[0] / 2 + battery_offset[0], bay[1] + bay_margin + battery[1] / 2 + battery_offset[1]];

// control bay hung below the bay, full width (a narrower one leaves a pocket that the outline smoothing turns into a hole).
// Pockets are placed as high as the battery allows: their top edge 0.5 mm below the battery's bottom edge.
ctrl_half  = max(reset_body[1], power_body[1]) / 2 + ctrl_clearance + ctrl_wall;
ctrl_cy    = bay[1] + bay_margin - battery_clearance - ctrl_half + ctrl_offset[1];
ctrl_h     = ctrl_bay_h > 0 ? ctrl_bay_h : bay[1] - (ctrl_cy - ctrl_half - 0.3);
ctrl_rect  = [bay[0], bay[1] - ctrl_h, bay[2], ctrl_h];
power_c   = [bay_right - 12 + ctrl_offset[0], ctrl_cy];
reset_c   = [bay_right - 24 + ctrl_offset[0], ctrl_cy];

// MCU as [cx, cy, rot, w, l] and the point on the board end where the USB connector is.
// It sits on the left of the bay; a nice!view goes to its right.
mcu_cx0 = bay[0] + bay_margin + nano_w / 2;   // left side of the bay; the right side holds the display or a wall boss
mcu = has_bay
  ? [mcu_cx0 + mcu_offset[0], bay_top - 1 - mcu_size[1] / 2 + mcu_offset[1], 0, mcu_size[0], mcu_size[1]]
  : (layout == "badtemper" ? badtemper_mcu : cheapino_mcu);
usb = has_bay ? [mcu[0], bay_top - 1 + mcu_offset[1]] : (layout == "badtemper" ? badtemper_usb : cheapino_usb);

// nice!view pocket: centre, bezel screw boss y positions, bezel size
nv_cx = mcu[0] + mcu_size[0] / 2 + mcu_side_clearance + rail_w + nv_gap + nv_ring_w + nv_W / 2;
nv_cy = bay_top - 1 - nv_boss_d - 1 - nv_L / 2;
nv_boss_y = [nv_cy + nv_L / 2 + 1 + nv_boss_d / 2, nv_cy - nv_L / 2 - 1 - nv_boss_d / 2];
nv_bezel_size = [nv_W + 2 * nv_bezel_margin, nv_L + 2 * (1 + nv_boss_d + 1)];

// bumpons: the fixed list plus two on the bay (inset 8 mm from its top-right and bottom-right corners)
bumpons = concat([[x_left - 4, -4], [x_left - 4, 42]], bumpon_positions, has_bay
  ? [[bay_right - 8, bay_top - 8], [bay_right - 10, (has_ctrl ? ctrl_rect[1] : bay[1]) + 12]] : []);

// bosses on the bay walls: top-right corner and (control-bay) bottom-right corner
bay_holes = has_bay ? [[bay_right - 3, bay_top - 0.5], [bay_right - 2.5, (has_ctrl ? ctrl_rect[1] : bay[1]) + 0.5]] : [];
left_holes = [[x_left - 11.5, 22], [x_left, -11.5]];   // left wall mid-height, below the outermost column
holes = layout == "cheapino" ? cheapino_holes : layout == "badtemper" ? badtemper_holes : concat(left_holes, grid_holes, bay_holes);

pcb_lift_e  = pcb_lift > 0 ? pcb_lift : max(2.4, battery[2] + 0.5 - (plate_to_pcb - plate_t) - pcb_t);
z_pcb_bot   = floor_t + pcb_lift_e;
z_pcb_top   = z_pcb_bot + pcb_t;
cavity_d = cavity_depth > 0 ? cavity_depth : max(10, battery[2] + 4);
z_plate_bot = build == "pcb" ? z_pcb_top + plate_to_pcb - plate_t : floor_t + cavity_d;
z_plate_top = z_plate_bot + plate_t;
z_wall_top  = z_plate_bot;
z_batt_top  = floor_t + battery[2];
z_mcu_bot   = build == "pcb" ? z_pcb_top + mcu_socket_h : z_batt_top + mcu_above_battery;
z_mcu_top   = z_mcu_bot + mcu_pcb_t;
z_ledge_bot = z_mcu_bot - ledge_t;
z_nv_top    = z_plate_top + nv_preload;     // nice!view PCB top
z_nv_bot    = z_nv_top - nv_pcb[2];
lip_height  = build == "pcb" ? min(lip_h, z_plate_bot - z_pcb_top - 0.3) : lip_h;

if (cradle && z_ledge_bot < z_batt_top)
  echo(str("WARNING: MCU ledge (z=", z_ledge_bot, ") is below the battery top (z=", z_batt_top, ") — raise mcu_above_battery or cavity_depth"));
if (has_nv && z_nv_bot - nv_ledge_t < z_batt_top + 0.3)
  echo(str("WARNING: nice!view ledge (z=", z_nv_bot - nv_ledge_t, ") is too close to the battery top (z=", z_batt_top, ")"));
if (has_nv && nv_cx + nv_W / 2 + nv_ring_w > bay[0] + bay[2] - 1)
  echo("WARNING: nice!view does not fit beside the nano -- widen the bay");
if (cradle && z_mcu_top > z_plate_bot)
  echo(str("WARNING: MCU board top (z=", z_mcu_top, ") is above the plate underside (z=", z_plate_bot, ") — increase cavity_depth"));

x_extent = wall + (cavity_from == "pcb"
  ? max([for (p = pcb_outline) p[0]]) + pcb_gap
  : max(concat([for (k = keys) k[0] + px], has_bay ? [bay[0] + bay[2]] : [])) + key_margin);

// ---------------------------------------------------------------- 2D building blocks

module at(k) translate([k[0], k[1]]) rotate(k[2]) children();
module at_mcu() translate([mcu[0], mcu[1]]) rotate(mcu[2]) children();
module rect(w, l) square([w, l], center = true);

module keycap_2d(k) rect(k[3] * px - (px - cap_w), cap_d);

module switch_cutout_2d() {
  rect(cutout, cutout);
  if (cutout_notches && !is_choc)
    for (s = [-1, 1]) translate([0, s * 4.25]) rect(cutout + 1.6, 3.5);
}

module mcu_2d() at_mcu() rect(mcu[3], mcu[4]);
module bay_2d() if (has_bay) {
  translate([bay[0], bay[1]]) square([bay[2], bay[3]]);
  if (has_ctrl) translate([ctrl_rect[0], ctrl_rect[1]]) square([ctrl_rect[2], ctrl_rect[3]]);
}
module battery_2d(o = 0) translate(batt_c) rect(battery[0] + 2 * o, battery[1] + 2 * o);

module pcb_2d() difference() {
  polygon(pcb_outline);
  for (h = holes) translate(h) circle(d = 2.2);
}

// inner wall surface
module cavity_2d() {
  if (len(cavity_polygon) > 2)
    polygon(cavity_polygon);
  else if (cavity_from == "pcb")
    offset(r = pcb_gap) polygon(pcb_outline);
  else
    offset(r = corner_r) offset(r = -corner_r - fill_r) offset(r = fill_r)   // close (fill notches < fill_r) then open (round convex corners)
    union() {
      offset(delta = key_margin) union() { for (k = keys) at(k) keycap_2d(k); if (!has_bay) mcu_2d(); }
      bay_2d();
    }
}

// outer wall surface
module outline_2d() offset(r = wall) cavity_2d();

module plate_windows_2d() intersection() {
  offset(r = -lip_clearance - lip_w) cavity_2d();        // never cut the rim that sits on the wall
  union() {
    for (w = plate_windows) translate([w[0], w[1]]) rotate(w[4]) rect(w[2], w[3]);
    if (build == "pcb") at_mcu() rect(mcu[3] + 2, mcu[4] + 2);   // window over a PCB-mounted MCU
  }
}

module plate_2d() difference() {
  outline_2d();
  for (k = keys) at(k) switch_cutout_2d();
  for (h = holes) translate(h) circle(d = screw_d);
  if (len(plate_windows) > 0 || build == "pcb") plate_windows_2d();   // (guarded: an empty operand breaks FreeCAD)
  if (cradle) cradle_opening_2d();
}

// ---------------------------------------------------------------- 3D parts

// a box punched through the wall: local +X is outward
module wall_cut(x, y, ang, w, h, z0) {
  translate([x, y, z0]) rotate(ang)
    translate([-4, -w / 2, 0]) cube([4 + pcb_gap + key_margin + wall + 6, w, h]);
}

module wall_cutouts() {
  if (usb_cutout[0] > 0)
    wall_cut(usb[0], usb[1], mcu[2] + 90, usb_cutout[0], usb_cutout[1], z_mcu_top + usb_cutout[2]);
  if (len(extra_cutouts) > 0) for (c = extra_cutouts) wall_cut(c[0], c[1], c[2], c[3], c[4], c[5]);
}

module battery_fence() if (has_bay && battery_fence[0] > 0)
  translate([0, 0, floor_t - eps]) linear_extrude(battery_fence[0] + eps) difference() {
    battery_2d(battery_clearance + battery_fence[1]);
    battery_2d(battery_clearance);
    translate([batt_c[0], batt_c[1] + battery[1] / 2]) rect(12, 2 * battery_fence[1] + 4);   // opening for the leads
  }

// pillars under the corners of the per-key PCBs
z_key_pcb_bot = z_plate_top - (is_choc ? 2.2 : 5) - key_pcb_t;
module key_pcb_posts() if (build == "plate" && key_pcbs && key_pcb_post[0] > 0)
  for (k = keys, sx = [-1, 1], sy = [-1, 1]) at(k)
    translate([sx * key_pcb_post_x - key_pcb_post[0] / 2, sy * (py / 2 - key_pcb_post[1] / 2) - key_pcb_post[1] / 2, floor_t - eps])
      cube([key_pcb_post[0], key_pcb_post[1], z_key_pcb_bot - key_pcb_post_gap - floor_t + eps]);

// post from the floor under the controller's USB end (centre of the board, under the connector)
module mcu_end_post() if (cradle && mcu_end_post[0] > 0) at_mcu()
  translate([-mcu_end_post[0] / 2, cr_yb - 1 - mcu_end_post[1], floor_t - eps])
    cube([mcu_end_post[0], mcu_end_post[1], z_mcu_bot - key_pcb_post_gap - floor_t + eps]);

module case_bottom() difference() {
  boss_top = build == "pcb" ? z_pcb_bot : z_plate_bot;
  union() {
    key_pcb_posts();
    mcu_end_post();
    difference() {
      linear_extrude(z_wall_top) outline_2d();
      translate([0, 0, floor_t]) linear_extrude(z_wall_top) cavity_2d();
    }
    for (h = holes) translate([h[0], h[1], 0]) cylinder(d = boss_d, h = boss_top);
    battery_fence();
  }
  for (h = holes) translate([h[0], h[1], boss_top - boss_hole_depth]) cylinder(d = boss_hole_d, h = boss_hole_depth + 1);
  wall_cutouts();
  if (bumpon_d > 0) for (b = bumpons) translate([b[0], b[1], -1]) cylinder(d = bumpon_d + 2 * bumpon_clearance, h = bumpon_depth + 1);
  if (magsafe_d > 0) translate([magsafe_pos[0], magsafe_pos[1], -1]) cylinder(d = magsafe_d + 2 * magsafe_clearance, h = magsafe_depth + 1, $fn = 128);
}

// ---- nice!view: hanging ring with ledges + bezel screw bosses, the pocket cuts, and the separate bezel part
module at_nv() translate([nv_cx, nv_cy]) children();

module nv_solid() at_nv() {
  translate([-(nv_W / 2 + nv_ring_w), -(nv_L / 2 + nv_ring_w), z_nv_bot - nv_ledge_t])
    cube([nv_W + 2 * nv_ring_w, nv_L + 2 * nv_ring_w, z_plate_bot - (z_nv_bot - nv_ledge_t) + eps]);
  for (y = nv_boss_y) translate([0, y - nv_cy, z_plate_bot - nv_boss_h]) cylinder(d = nv_boss_d, h = nv_boss_h + eps);
}

module nv_cuts() at_nv() {
  translate([-nv_W / 2, -nv_L / 2, z_nv_bot]) cube([nv_W, nv_L, 20]);                           // PCB pocket
  translate([-(nv_W / 2 - nv_ledge_w), -nv_L / 2, -1]) cube([nv_W - 2 * nv_ledge_w, nv_L, 30]);  // through opening (wires, pads)
  for (y = nv_boss_y) translate([0, y - nv_cy, z_plate_bot - nv_boss_h - 1]) cylinder(d = nv_boss_hole_d, h = nv_boss_h + plate_t + 2);
}

module bezel_2d() difference() {
  offset(r = nv_bezel_r) offset(delta = -nv_bezel_r) rect(nv_bezel_size[0], nv_bezel_size[1]);
  translate([0, nv_glass_shift]) rect(nv_glass[0] + 2 * nv_window_clearance, nv_glass[1] + 2 * nv_window_clearance);
  for (y = nv_boss_y) translate([0, y - nv_cy]) circle(d = nv_bezel_hole_d);
}
module bezel() linear_extrude(nv_bezel_t) bezel_2d();

// nice!nano cradle hanging from the plate: rails on three sides (open towards the USB wall -- the board
// slides in from there with the plate off) with a wire channel along each long edge, ledges under the two
// short ends, and a cap above the board that the opening is cut from -- leaving the far-end overhang and
// the USB-end hold-down tabs.
// Local frame: board centre, +y towards the wall / USB end.
cr_W     = mcu_size[0] + 2 * mcu_side_clearance;
cr_yb    = mcu_size[1] / 2;
cr_yfar  = -cr_yb - mcu_clearance;                 // pocket far end
cr_yusb  = cr_yb + mcu_clearance;                  // pocket USB end
cr_ywall = cr_yb + 1 - lip_clearance;              // just inside the wall line
cr_tab_w = cr_W / 2 - usb_cutout[0] / 2 - 0.5;     // corner tabs beside the USB slot

module cradle_solid() at_mcu() {
  translate([0, 0, z_ledge_bot]) linear_extrude(z_plate_bot - z_ledge_bot + eps) difference() {
    translate([-(cr_W / 2 + rail_w), cr_yfar - rail_w]) square([cr_W + 2 * rail_w, cr_ywall - cr_yfar + rail_w]);
    translate([-cr_W / 2, cr_yfar]) square([cr_W, cr_ywall - cr_yfar + 1]);
  }
  translate([0, 0, z_ledge_bot]) linear_extrude(ledge_t)
    translate([-cr_W / 2, cr_yfar]) square([cr_W, mcu_clearance + mcu_far_ledge]);              // far end: strip under the edge only
  translate([-cr_W / 2, cr_yfar, z_mcu_top + mcu_lift_gap])                                          // cap
    cube([cr_W, cr_ywall - cr_yfar, z_plate_bot - (z_mcu_top + mcu_lift_gap) + eps]);
}

// opening through the cap and the plate: the board minus the far overhang, minus the two corner tabs
module cradle_opening_2d() at_mcu() difference() {
  union() {
    translate([-cr_W / 2, -cr_yb + mcu_overhang]) square([cr_W, cr_ywall - (-cr_yb + mcu_overhang) + 0.01]);
    translate([-mcu_overhang_gap / 2, -cr_yb - 0.5]) square([mcu_overhang_gap, mcu_overhang + 1]);   // gap between the far corner tabs
  }
  // (the notches overshoot the opening's edge by 1 mm: coincident edges break FreeCAD's booleans)
  for (s = [-1, 1]) translate([s > 0 ? cr_W / 2 - cr_tab_w : -cr_W / 2 - 1, cr_yb - mcu_tab]) square([cr_tab_w + 1, 5]);
}

module cradle_cuts() at_mcu() {
  difference() {   // board pocket, open at the USB end, minus the locating nubs at both ends of the wire channels
    translate([-cr_W / 2, cr_yfar, z_mcu_bot]) cube([cr_W, cr_ywall + 1 - cr_yfar, z_mcu_top + mcu_lift_gap - z_mcu_bot]);
    if (mcu_locate_len > 0) for (s = [-1, 1], e = [-1, 1])
      translate([s > 0 ? mcu_size[0] / 2 + mcu_clearance : -cr_W / 2 - 1,
                 e > 0 ? cr_yb - mcu_locate_len : -cr_yb - mcu_clearance - 1, z_mcu_bot - 1])
        cube([cr_W / 2 - mcu_size[0] / 2 - mcu_clearance + 1, mcu_locate_len + mcu_clearance + 1, 30]);
  }
  z0 = z_mcu_top + mcu_lift_gap - eps;
  difference() {   // opening through the cap and the plate, built from cubes (FreeCAD cannot extrude the notched 2D shape)
    union() {
      translate([-cr_W / 2, -cr_yb + mcu_overhang, z0]) cube([cr_W, cr_ywall - (-cr_yb + mcu_overhang) + 0.01, 20]);
      translate([-mcu_overhang_gap / 2, -cr_yb - 0.5, z0]) cube([mcu_overhang_gap, mcu_overhang + 1, 20]);
    }
    for (s = [-1, 1]) translate([s > 0 ? cr_W / 2 - cr_tab_w : -cr_W / 2 - 1, cr_yb - mcu_tab, z0 - 1]) cube([cr_tab_w + 1, 5, 22]);
  }
}

// pocket for a through-hole switch dropped in from above (body through the plate, legs through a floor below)
module ctrl_solid(p, body, recess) {
  zf = z_plate_top - recess - body[2];
  o = ctrl_clearance + ctrl_wall;
  translate([p[0] - body[0] / 2 - o, p[1] - body[1] / 2 - o, zf - ctrl_floor])
    cube([body[0] + 2 * o, body[1] + 2 * o, z_plate_bot - (zf - ctrl_floor) + eps]);
}
module ctrl_cut(p, body, legs, recess) {
  zf = z_plate_top - recess - body[2];
  translate([p[0] - body[0] / 2 - ctrl_clearance, p[1] - body[1] / 2 - ctrl_clearance, zf])
    cube([body[0] + 2 * ctrl_clearance, body[1] + 2 * ctrl_clearance, 20]);
  for (l = legs) translate([p[0] + l[0] - ctrl_leg_hole / 2, p[1] + l[1] - ctrl_leg_hole / 2, zf - ctrl_floor - 1])
    cube([ctrl_leg_hole, ctrl_leg_hole, ctrl_floor + 1.5]);
}

// ribs: ring around each switch, kept clear of the bosses and the lip
rib_height = rib_h > 0 ? rib_h : (is_choc ? 2.2 : 5) - plate_t - (key_pcbs ? 0.3 : 0);
module plate_ribs_3d() translate([0, 0, z_plate_bot - rib_height]) linear_extrude(rib_height + eps) difference() {
  intersection() {
    offset(r = -lip_clearance - lip_w) cavity_2d();
    union() for (k = keys) at(k) rect(cutout + 1.6 + 2 * rib_clearance + 2 * rib_w, cutout + 1.6 + 2 * rib_clearance + 2 * rib_w);
  }
  for (k = keys) at(k) rect(cutout + 1.6 + 2 * rib_clearance, cutout + 1.6 + 2 * rib_clearance);
  for (h = holes) translate(h) circle(d = boss_d + 1);
}

module plate() difference() {
  union() {
    translate([0, 0, z_plate_bot]) linear_extrude(plate_t) plate_2d();
    if (plate_ribs) plate_ribs_3d();
    if (lip_height > 0 && lip_w > 0)
      translate([0, 0, z_plate_bot - lip_height]) linear_extrude(lip_height + eps) difference() {
        offset(r = -lip_clearance) cavity_2d();
        offset(r = -lip_clearance - lip_w) cavity_2d();
        for (h = holes) translate(h) circle(d = boss_d + 2 * lip_clearance + 0.4);   // clear the boss tops
      }
    if (build == "pcb")
      for (h = holes) translate([h[0], h[1], z_pcb_top]) cylinder(d = plate_boss_d, h = z_plate_bot - z_pcb_top + eps);
    if (cradle) cradle_solid();
    if (has_nv) nv_solid();
    if (has_ctrl && reset_button) ctrl_solid(reset_c, reset_body, reset_recess);
    if (has_ctrl && power_switch) ctrl_solid(power_c, power_body, power_recess);
  }
  if (has_nv) nv_cuts();
  if (has_ctrl && reset_button) ctrl_cut(reset_c, reset_body, reset_legs, reset_recess);
  if (has_ctrl && power_switch) ctrl_cut(power_c, power_body, power_legs, power_recess);
  for (h = holes) translate([h[0], h[1], z_plate_bot - 5]) cylinder(d = screw_d, h = plate_t + 10);
  if (cradle) {
    cradle_cuts();
    wall_cutouts();   // the USB plug passes through the plate level too
  }
}

// ---------------------------------------------------------------- visualisation only

module keycap_3d(k) {
  w = k[3] * px - (px - cap_w);
  h = is_choc ? 3 : 8;
  lift = is_choc ? 3 : 6.5;
  at(k) translate([0, 0, z_plate_top + lift]) hull() {
    linear_extrude(eps) offset(r = 1) offset(delta = -1) rect(w, cap_d);
    translate([0, 0, h]) linear_extrude(eps) offset(r = 1) offset(delta = -1) rect(w - 4, cap_d - 4);
  }
}

module switch_3d(k) at(k) {
  below = is_choc ? 2.2 : 5;
  translate([0, 0, z_plate_top - below]) linear_extrude(below) rect(body, body);
  translate([0, 0, z_plate_top - eps]) linear_extrude(is_choc ? 3 : 6.5) rect(body + 1.6, body + 1.6);
  translate([0, 0, z_plate_top - below - 3.3]) linear_extrude(3.3) rect(4, 4);   // pins / leads
}

module mcu_3d() {
  color("darkolivegreen", 0.9) translate([0, 0, z_mcu_bot]) linear_extrude(mcu_pcb_t) mcu_2d();
  color("silver") at_mcu() translate([-4.5, mcu[4] / 2 - 7.35 + 1.3, z_mcu_top]) cube([9, 7.35, 3.2]);   // USB-C, overhangs 1.3
}

module nv_3d() at_nv() {
  color("darkolivegreen", 0.9) translate([-nv_pcb[0] / 2, -nv_pcb[1] / 2, z_nv_bot]) cube(nv_pcb);
  color("black") translate([-nv_glass[0] / 2, nv_glass_shift - nv_glass[1] / 2, z_nv_top]) cube([nv_glass[0], nv_glass[1], nv_glass[2]]);
}

module ctrl_3d(p, body, recess, actuator) {
  zf = z_plate_top - recess - body[2];
  color("dimgray") translate([p[0] - body[0] / 2, p[1] - body[1] / 2, zf]) cube(body);
  color("gainsboro") translate([p[0] - actuator[0] / 2, p[1] - actuator[1] / 2, zf + body[2]]) cube(actuator);
}

module electronics_3d() {
  if (has_bay) color("dimgray", 0.8) translate([0, 0, floor_t]) linear_extrude(battery[2]) battery_2d();
  if (!cradle) mcu_3d();
  if (build == "pcb" && cavity_from == "pcb")
    color("darkolivegreen", 0.7) translate([0, 0, z_pcb_bot]) linear_extrude(pcb_t) pcb_2d();
}

module assembly() {
  color("slategray") case_bottom();
  if (show_electronics) electronics_3d();
  translate([0, 0, explode]) {
    color("lightsteelblue") plate();
    if (show_electronics && cradle) mcu_3d();   // the nice!nano lives in the plate's cradle
    if (show_electronics && has_ctrl && reset_button) ctrl_3d(reset_c, reset_body, reset_recess, [3.5, 3.5, 3.3]);
    if (show_electronics && has_ctrl && power_switch) ctrl_3d(power_c, power_body, power_recess, [1.5, 2, 3]);
    if (has_nv) {
      if (show_electronics) nv_3d();
      color("steelblue") at_nv() translate([0, 0, z_plate_top]) bezel();
    }
    if (show_switches) color("dimgray") for (k = keys) switch_3d(k);
    if (show_keycaps) color("whitesmoke", 0.9) for (k = keys) keycap_3d(k);
  }
}

// ---------------------------------------------------------------- main

module mirrored_for_side() {
  if (side == "right") mirror([1, 0, 0]) children();
  else if (side == "both") {
    translate([-x_extent - both_gap / 2, 0]) children();
    translate([ x_extent + both_gap / 2, 0]) mirror([1, 0, 0]) children();
  }
  else children();
}

mirrored_for_side() {
  // test coupon for the hardware: a boss exactly like the case's (insert hole) on a floor slab, plus a scrap of plate
  // with its screw hole and lip relief, to try the heat-set insert and the M2 screw before printing everything
  if (part == "insert_test") {
    difference() {
      union() {
        translate([-8, -8, 0]) cube([16, 16, floor_t]);
        cylinder(d = boss_d, h = z_plate_bot);
      }
      translate([0, 0, z_plate_bot - boss_hole_depth]) cylinder(d = boss_hole_d, h = boss_hole_depth + 1);
    }
    translate([20, 0, 0]) difference() {
      translate([-8, -8, 0]) cube([16, 16, plate_t]);
      translate([0, 0, -1]) cylinder(d = screw_d, h = plate_t + 2);
    }
  }
  if (part == "info") echo(holes = holes, bay = bay, ctrl = ctrl_rect, mcu = mcu, battery_c = batt_c, reset = reset_c, power = power_c, bumpons = bumpons, keys = keys, post = key_pcb_post, post_x = [key_pcb_post_x]);
  if (part == "assembly")             assembly();
  else if (part == "section")         projection(cut = true) rotate([-90, 0, 0]) rotate([0, 0, -90]) translate([-section_x, 0, 0]) assembly();
  else if (part == "case")            case_bottom();
  else if (part == "plate")           plate();
  else if (part == "bezel")           bezel();
  else if (part == "bezel_2d")        bezel_2d();
  else if (part == "plate_2d")        plate_2d();
  else if (part == "case_outline_2d") outline_2d();
  else if (part == "cavity_2d")       cavity_2d();
  else if (part == "pcb_2d")          pcb_2d();
  else if (part == "pcb_outline_2d")  difference() {   // recommended Edge.Cuts for a Pacino PCB (build = "pcb")
    offset(r = -pcb_gap) cavity_2d();
    if (has_bay) battery_2d(1);                        // battery pokes up through the board
    for (h = holes) translate(h) circle(d = 2.2);      // M2 clearance for the case bosses' screws
  }
}
