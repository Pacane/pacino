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
part = "assembly"; // [assembly, section, case, plate, bezel, insert_test, pcb_test, plate_2d, case_outline_2d, cavity_2d, pcb_2d, pcb_outline_2d, bezel_2d, info]
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
// pcb build: part = "pcb_test" prints a stand-in for the board at pcb_t thick -- the real outline and
// every hole a switch, the controller or the two switches passes through -- so the whole stack can be
// test-fitted before a board is ordered. The stand-ins for the hot-swap sockets are bumps on the
// underside at the socket's real height, which is what makes the 2.4 mm under the board a real test.
pcb_test_sockets = true;
// holes come out undersize when printed; these are the drilled sizes plus a little
pcb_test_slop = 0.2;
// pcb build: carry the cell in a pod that is part of the plate, directly over the socketed controller
// (whose bare back finishes flush with the plate top), instead of in a well in the case floor. Below the
// board every millimetre of cell is a millimetre of case; the 3.5 mm above it is fixed by the MX
// plate-to-PCB geometry and otherwise wasted, so this costs no case height at all -- 11.5 mm to the plate
// top, the MX minimum, with the 902030 still in the build. The pod stands battery + pod_wall proud of the
// plate, under the keycaps (14.5). The cell goes in through the MCU window from below and rests on the
// controller; its leads drop into the bay past the window's far end. The board is then solid (no cutout).
battery_pod = true;
pod_wall = 1.2;
pod_clearance = 0.4;

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
// sink the battery into the floor, leaving this much plastic under it (0 = off, battery sits on the full
// floor inside the fence). The well's walls replace the fence, and the case gets ~1.3 mm thinner.  With a
// well the cell sits against the bay's LEFT wall (which then doubles as the well's side) instead of
// bay_margin from it, so the bay's right-hand corners stay clear for the two bumpons there: a bumpon
// recess over the well would leave 0.2 mm of floor.  Required by mcu_flipped (component clearance).
battery_well_floor = 1.2;
// the well is the cell's outline plus this all round
well_clearance = 0.75;
// controller board [width, length]: SuperMini / "Pro Micro nRF52840" nice!nano clone, measured 18 x 33
// (vendors quote 17.8 wide -- the 0.3 mm nub clearance covers both).  nice!nano = [18, 33.5].
// Sideways the board is located by the nubs at the pocket ends, NOT by the 1.2 mm wire channels along
// its sides -- the channel span is ~20.4 mm by design.
mcu_size = [18, 33];
mcu_pins = 12;          // per side (nice!nano / Pro Micro: 2 x 12 on 2.54, rows 15.24 apart)
// PCB thickness (SuperMini measured 1.53; its reset button stands 1.1 mm above the board, centred on the far end)
mcu_pcb_t = 1.55;
mcu_offset = [0, 0];
// board underside above the battery top (plate build; sets the cradle height)
mcu_above_battery = 1.5;
// mount the controller upside down: components and USB face INTO the case (protected, solid plate above,
// closed USB window lower in the wall). Wires poke through the pads from the bare top side and exit
// downward into the case -- no wire channels, pocket = board + 0.6 mm. The onboard reset/LED face down
// (the external reset button covers reset + bootloader). Needs the battery well (module clearance).
mcu_flipped = true;
// cradle: end clearance; side clearance (flipped: rails sit right at the board; unflipped: a 1.2 mm wire
// channel along each edge for wires soldered on top); rail thickness, ledge thickness / width
mcu_clearance = 0.3;
mcu_side_clearance = 0.3;
crush_rib = 0.6;       // how far the crush ribs stand proud of each cradle rail face (flipped only)
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
// placed automatically on the bay: 8 mm in from its top-right corner, and 12 mm up from the bottom of the
// control strip on the right.  With a battery well they move outward by only what the well forces (the
// bay is sized so a full-size foot always fits there); the model warns if a foot has nowhere to go.
bumpon_positions = [[38.1, 58], [15, 20], [71.5, -15.5], [111.7, -31.7]];
// floor left between the bay's top-right recess and the outside of the wall. 1.0 is the minimum (a 1 x 1 mm
// lip at the case's bottom edge); with a wide cell every extra millimetre here is a millimetre of case width
bumpon_skin = 1.0;
// round recess in the underside for a MagSafe magnet ring (56 mm sticker ring); 0 = none
magsafe_d = 56;
magsafe_depth = 1;
magsafe_clearance = 0.3;
// centre: under the index column, clear of the bumpons and bosses -- and of the battery well, whose key-side
// edge is on the bay line (x = 86.5): the recess is 1 mm into the underside and the well 1.3 mm into the top of the
// floor, so where they overlap only 0.2 mm is left (the model warns).  [60, 28] ran 1.8 mm under the well.
magsafe_pos = [57, 28];

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
// optional nice!view, flush in the plate, clamped by a screw-down bezel (part = "bezel"); off by default.
// With a flipped nano the plate above it is solid, so the display can sit DIRECTLY OVER the board instead
// of beside it -- the bay then stays as narrow as the no-display version (~11.6 mm narrower overall).
// Stacked, the bezel's screw bosses move from the display's ends to its sides: an end boss would hang
// straight through the board below.
nice_view = false;
nv_stacked = true;      // display over the nano (requires mcu_flipped); false = the old side-by-side bay
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
// single-key hot-swap PCBs when key_pcbs is on (a hand-wired idea: build = "pcb" ignores all of this)
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
has_pod = build == "pcb" && has_bay && battery_pod;   // cell above the plate, not in the floor
has_nv = nice_view && cradle;
nv_over = has_nv && nv_stacked && mcu_flipped;   // the display sits on top of the board, not beside it
has_ctrl = has_bay && (reset_button || power_switch);   // the control strip exists in both builds;
                                                        // plate pockets only when hand-wired, windows when on a PCB

// electronics footprint across the bay: nano cradle [+ gap + nice!view ring]
nano_w = mcu_size[0] + 2 * (mcu_side_clearance + rail_w);
nv_W   = nv_pcb[0] + 2 * nv_clearance;
nv_L   = nv_pcb[1] + 2 * nv_clearance;
elec_w = nano_w + (has_nv && !(nv_stacked && mcu_flipped) ? nv_gap + nv_W + 2 * nv_ring_w : 0);
nano_l = mcu_size[1] + 2 * mcu_clearance + rail_w + 1;                    // pocket + far rail + gap to the wall
nv_l   = 1 + nv_boss_d + 1 + nv_L + 1 + nv_boss_d;                         // wall gap, boss, gap, pocket, gap, boss
// width: battery + margins, or the electronics row + left margin + room for a wall boss on the right
well_on  = has_bay && !has_pod && battery_well_floor > 0;   // the cell is in a well in the floor
bumpon_r = bumpon_d / 2 + bumpon_clearance;                 // recess radius
// the cell needs room *in the bay* only when it sits in the case floor (in the plate pod it is not in
// the bay at all).  In a well it sits against the bay's left wall, and the bay must then be wide
// enough for the top-right foot to fit beside it: cell + well + foot + 1 mm of skin outside the recess
batt_bay_margin = has_pod ? 0 : bay_margin;
batt_mx    = well_on ? well_clearance : bay_margin;           // cell -> bay left wall
foot_bay_w = well_on ? batt_mx + battery[0] + well_clearance + 0.3 + 2 * bumpon_r + bumpon_skin - wall : 0;

bay_w  = bay_size_override[0] > 0 ? bay_size_override[0]
       : max(battery[0] + 2 * batt_bay_margin, foot_bay_w, elec_w + bay_margin + boss_d + 1);   // room for the corner boss beside the cradle
bay_h  = bay_size_override[1] > 0 ? bay_size_override[1]
       : max(battery[1] + 2 * batt_bay_margin, nano_l + bay_margin, has_nv ? nv_l + bay_margin : 0);
bay    = [bay_left, bay_top_y - bay_h, bay_w, bay_h];
bay_cx = bay[0] + bay[2] / 2;
bay_cy = bay[1] + bay[3] / 2;
bay_top = bay[1] + bay[3];
bay_right = bay[0] + bay[2];
batt_c = [bay[0] + batt_mx + battery[0] / 2 + battery_offset[0], bay[1] + bay_margin + battery[1] / 2 + battery_offset[1]];

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

// battery pod (build = "pcb"): a box moulded into the plate over the controller. The interior clears
// both the cell and the MCU window it drops through, so its walls always land on plate, never over the
// window. pod_ih is measured from the plate top -- the controller's bare back is flush with it.
batt_cc = has_pod ? [mcu[0], mcu[1]] : batt_c;   // the cell is centred over the controller in the pod
pod_iw  = max(battery[0] + 2 * pod_clearance, mcu[3] + 2.4);
pod_il  = max(battery[1] + 2 * pod_clearance, mcu[4] + 2.4);
// interior height is measured from the plate top, but the cell actually lands on whatever is
// highest: with the stock 3.5 mm sockets the controller's back finishes 0.05 mm proud of the plate,
// and taller sockets lift it (and the cell) further, so add whatever it stands proud by
pod_ih  = battery[2] + pod_clearance + max(0, mcu_socket_h + mcu_pcb_t - plate_to_pcb);
usb = has_bay ? [mcu[0], bay_top - 1 + mcu_offset[1]] : (layout == "badtemper" ? badtemper_usb : cheapino_usb);

// nice!view pocket: centre, bezel screw boss y positions, bezel size
nv_cx = nv_over ? mcu[0]
      : mcu[0] + mcu_size[0] / 2 + mcu_side_clearance + rail_w + nv_gap + nv_ring_w + nv_W / 2;
nv_cy = bay_top - 1 - nv_boss_d - 1 - nv_L / 2;
nv_boss_r  = nv_over ? nv_W / 2 + nv_ring_w + 1 + nv_boss_d / 2 : nv_L / 2 + 1 + nv_boss_d / 2;
nv_boss_off = nv_over ? [[nv_boss_r, 0], [-nv_boss_r, 0]] : [[0, nv_boss_r], [0, -nv_boss_r]];
nv_bezel_size = nv_over ? [nv_W + 2 * (1 + nv_boss_d + 1), nv_L + 2 * nv_bezel_margin]
                        : [nv_W + 2 * nv_bezel_margin, nv_L + 2 * (1 + nv_boss_d + 1)];

// bumpons: the fixed list plus two on the bay -- 8 mm in from its top-right corner, and 12 mm up from the
// bottom of the control strip on the right.  A recess (1 mm) over the battery well (1.3 mm into the 2.5 mm
// floor) would leave 0.2 mm of plastic, so with a well each foot is pushed outward by exactly what it
// takes to clear the well: the top one to the right (the bay was sized so it never needs more than
// leaves 1 mm of skin outside the recess), the bottom one down into the control strip.
bay_y0      = has_ctrl ? ctrl_rect[1] : bay[1];
well_right  = batt_c[0] + battery[0] / 2 + well_clearance;
well_top    = batt_c[1] + battery[1] / 2 + well_clearance;
well_bottom = batt_c[1] - battery[1] / 2 - well_clearance;
foot_keep   = bumpon_r + 0.3;                                  // recess edge -> well edge
top_dy = max(0, (bay_top - 8) - well_top);
top_x  = !well_on ? bay_right - 8
       : max(bay_right - 8, well_right + sqrt(max(0, foot_keep * foot_keep - top_dy * top_dy)));
bot_x  = bay_right - 10;
bot_dx = max(0, bot_x - well_right);
bot_y  = !well_on ? bay_y0 + 12
       : min(bay_y0 + 12, well_bottom - sqrt(max(0, foot_keep * foot_keep - bot_dx * bot_dx)));
bay_foot_top = [top_x, bay_top - 8];
bay_foot_bot = bot_y - bumpon_r >= bay_y0 - wall + 1.0 ? [[bot_x, bot_y]] : [];   // still on the floor?
if (has_bay && len(bay_foot_bot) == 0)
  echo("WARNING: no room for the bay's lower bumpon between the battery well and the wall -- add a control strip or a taller bay");
if (has_bay && top_x + bumpon_r > bay_right + wall - bumpon_skin + 0.01)
  echo("WARNING: the bay's top-right bumpon would break through the wall -- widen the bay (bay_size_override)");
// the MagSafe recess (magsafe_depth into the underside) must stay clear of the well (floor_t - battery_well_floor into
// the top of the floor): where the two overlap only battery_well_floor - magsafe_depth of plastic is left
well_left = batt_c[0] - battery[0] / 2 - well_clearance;
magsafe_r = magsafe_d / 2 + magsafe_clearance;
magsafe_well_gap = norm([magsafe_pos[0] - max(well_left, min(well_right, magsafe_pos[0])),
                         magsafe_pos[1] - max(well_bottom, min(well_top, magsafe_pos[1]))]) - magsafe_r;
if (well_on && magsafe_d > 0 && magsafe_well_gap < 0)
  echo(str("WARNING: the MagSafe recess runs ", -magsafe_well_gap, " mm under the battery well, leaving ",
           battery_well_floor - magsafe_depth, " mm of floor there -- move magsafe_pos"));
bumpons = concat([[x_left - 4, -4], [x_left - 4, 42]], bumpon_positions,
                 has_bay ? concat([bay_foot_top], bay_foot_bot) : []);

// bosses on the bay walls: top-right corner and (control-bay) bottom-right corner
bay_holes = has_bay ? [[bay_right - 3, bay_top - 0.5], [bay_right - 2.5, (has_ctrl ? ctrl_rect[1] : bay[1]) + 0.5]] : [];
left_holes = [[x_left - 11.5, 22], [x_left, -11.5]];   // left wall mid-height, below the outermost column
holes = layout == "cheapino" ? cheapino_holes : layout == "badtemper" ? badtemper_holes : concat(left_holes, grid_holes, bay_holes);

batt_z0     = battery_well_floor > 0 ? battery_well_floor : floor_t;
// board height above the battery: flat back needs 1.5 (ledge + air); flipped, the components hang
// down and need ~2.8 (nRF module + margin)
mcu_ab_e    = mcu_flipped ? max(mcu_above_battery, 2.8) : mcu_above_battery;
pcb_lift_min = 2.4;   // what a Kailh hot-swap socket needs under the board
pcb_lift_e  = pcb_lift > 0 ? pcb_lift : has_pod ? pcb_lift_min   // pod: only the sockets are under the board
            : max(pcb_lift_min, batt_z0 + battery[2] + 0.5 - floor_t - (plate_to_pcb - plate_t) - pcb_t);
z_pcb_bot   = floor_t + pcb_lift_e;
z_pcb_top   = z_pcb_bot + pcb_t;
cavity_d = cavity_depth > 0 ? cavity_depth : max(10, batt_z0 + battery[2] + mcu_ab_e + mcu_pcb_t + 0.95 - floor_t);
z_plate_bot = build == "pcb" ? z_pcb_top + plate_to_pcb - plate_t : floor_t + cavity_d;
z_plate_top = z_plate_bot + plate_t;
z_wall_top  = z_plate_bot;
z_batt_bot  = has_pod ? z_plate_top : batt_z0;
// does the cell stand higher than the board's underside?  If so the board needs a cutout for it; if
// not (a thin cell in the floor well, or the plate pod) the board stays solid.
batt_thru   = has_bay && !has_pod && batt_z0 + battery[2] > floor_t + pcb_lift_e;
// thickest cell that fits *under* the board -- measured at the minimum lift, since a cell that fits
// there does not push the board up in the first place
batt_max_t  = floor_t + pcb_lift_min - batt_z0 - 0.3;
z_batt_top  = z_batt_bot + battery[2];
z_mcu_bot   = build == "pcb" ? z_pcb_top + mcu_socket_h : z_batt_top + mcu_ab_e;
z_mcu_top   = z_mcu_bot + mcu_pcb_t;
z_ledge_bot = z_mcu_bot - ledge_t;
z_nv_top    = z_plate_top + nv_preload;     // nice!view PCB top
z_nv_bot    = z_nv_top - nv_pcb[2];
// stacked, the display's support ledges hang over the board's back, so they are thinned to clear it
// (they then double as the board's hold-down, replacing the cradle roof pad the display cuts through)
nv_ledge_te = nv_over ? min(nv_ledge_t, z_nv_bot - z_mcu_top - 0.4) : nv_ledge_t;
lip_height  = build == "pcb" ? min(lip_h, z_plate_bot - z_pcb_top - 0.3) : lip_h;

// the controller hangs its USB connector 3.2 mm below its own board, so the sockets cannot be
// shorter than that plus clearance -- this is what fixes mcu_socket_h at 3.5, not a guess
// The one geometry that fails silently: a cell too thick to fit under the board has to poke through
// it, and in the bay that cutout runs straight under the controller -- whose pin rows are then left
// with no board to solder to.  (This is exactly what the first pass at this design did.)
if (build == "pcb" && batt_thru
    && abs(batt_cc[0] - mcu[0]) < (battery[0] + 2 + mcu[3]) / 2
    && abs(batt_cc[1] - mcu[1]) < (battery[1] + 2 + mcu[4]) / 2)
  echo(str("WARNING: the cell pokes through the board and its cutout runs under the controller -- ",
           "the pin rows would have no board under them. Use battery_pod = true, or a cell at most ",
           batt_max_t, " mm thick, which fits under the board and leaves it solid."));

if (build == "pcb" && mcu_flipped && mcu_socket_h < 3.2 + 0.3)
  echo(str("WARNING: mcu_socket_h = ", mcu_socket_h, " is shorter than the USB connector needs; ",
           "the connector would sit ", 3.2 + 0.3 - mcu_socket_h, " mm inside the PCB -- use 3.5 mm sockets"));

if (has_pod && (mcu[1] + pod_il / 2 + pod_wall > bay_top + wall
             || mcu[0] - pod_iw / 2 - pod_wall < bay[0] - wall
             || mcu[0] + pod_iw / 2 + pod_wall > bay_right + wall))
  echo(str("WARNING: the battery pod (", pod_iw + 2 * pod_wall, " x ", pod_il + 2 * pod_wall,
           ") overhangs the plate around the bay -- use a smaller cell or widen the bay"));

if (cradle && z_ledge_bot < z_batt_top)
  echo(str("WARNING: MCU ledge (z=", z_ledge_bot, ") is below the battery top (z=", z_batt_top, ") — raise mcu_above_battery or cavity_depth"));
if (has_nv && z_nv_bot - nv_ledge_te < z_batt_top + 0.3)
  echo(str("WARNING: nice!view ledge (z=", z_nv_bot - nv_ledge_te, ") is too close to the battery top (z=", z_batt_top, ")"));
if (has_nv && !nv_over && nv_cx + nv_W / 2 + nv_ring_w > bay[0] + bay[2] - 1)
  echo("WARNING: nice!view does not fit beside the nano -- widen the bay");
if (has_nv && nv_stacked && !mcu_flipped)
  echo("WARNING: nv_stacked needs mcu_flipped (the plate must be solid over the board) -- falling back to side by side");
if (nv_over && nv_ledge_te < 0.4)
  echo(str("WARNING: stacked nice!view leaves only ", nv_ledge_te, " mm of ledge over the board -- raise nv_preload"));
// stacked, the bezel's screw bosses hang beside the board; an end boss would pass straight through it
if (nv_over && nv_boss_r - nv_boss_d / 2 < mcu_size[0] / 2 + mcu_side_clearance)
  echo("WARNING: stacked nice!view bezel bosses overlap the nano below -- widen nv_ring_w or shrink nv_boss_d");
if (nv_over && (nv_cx + nv_boss_r + nv_boss_d / 2 > bay[0] + bay[2] - 0.5 || nv_cx - nv_boss_r - nv_boss_d / 2 < bay[0] + 0.5))
  echo("WARNING: stacked nice!view bezel bosses fall outside the bay -- widen the bay");
if (cradle && mcu_flipped && z_batt_top > z_mcu_bot - 2.5)
  echo(str("WARNING: flipped MCU components (down to z=", z_mcu_bot - 2.5, ") hit the battery top (z=", z_batt_top, ") — set battery_well_floor"));
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
module battery_2d(o = 0) translate(batt_cc) rect(battery[0] + 2 * o, battery[1] + 2 * o);

module pcb_2d() difference() {
  polygon(pcb_outline);
  for (h = holes) translate(h) circle(d = 2.2);
}

// the board for build = "pcb": the cavity less pcb_gap, the M2 clearances (the bosses' screws pass
// through them; seven of the eight fall on the edge and come out as notches), and -- only when the
// cell is in the floor rather than the plate pod -- the cutout it pokes through.  This is exactly
// what tools/pcb_gen.py turns into Edge.Cuts.
module pcb_board_2d() difference() {
  offset(r = -pcb_gap) cavity_2d();
  // the board only needs a cutout if the cell actually pokes up through it: true for a thick cell in
  // the floor, false for the plate pod and false for a thin one that fits under the board
  if (batt_thru) battery_2d(1);
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
    if (build == "pcb") at_mcu() rect(has_pod ? pod_iw : mcu[3] + 2, mcu[4] + 2);   // window over a PCB-mounted MCU (the cell drops through it into the pod)
    // PCB-mounted switches poke up through these; 0.3 mm clearance each side, not 0.5, because the
    // two windows are only 1.65 mm apart and the rib between them is plate
    if (build == "pcb" && has_ctrl && reset_button) translate(reset_c) rect(reset_body[0] + 0.6, reset_body[1] + 0.6);
    if (build == "pcb" && has_ctrl && power_switch) translate(power_c) rect(power_body[0] + 0.6, power_body[1] + 0.6);
  }
}

module plate_2d() difference() {
  outline_2d();
  for (k = keys) at(k) switch_cutout_2d();
  for (h = holes) translate(h) circle(d = screw_d);
  if (len(plate_windows) > 0 || build == "pcb") plate_windows_2d();   // (guarded: an empty operand breaks FreeCAD)
  if (cradle && !mcu_flipped) cradle_opening_2d();
}

// ---------------------------------------------------------------- 3D parts

// a box punched through the wall: local +X is outward
module wall_cut(x, y, ang, w, h, z0) {
  translate([x, y, z0]) rotate(ang)
    translate([-4, -w / 2, 0]) cube([4 + pcb_gap + key_margin + wall + 6, w, h]);
}

module wall_cutouts() {
  // flipped: an open-top notch (the solid plate bridges it) — a closed window would leave a
  // sub-mm sliver under the wall top, which prints badly
  usb_z0 = mcu_flipped ? z_mcu_bot - 3.2 - 1.9 : z_mcu_top + usb_cutout[2];
  if (usb_cutout[0] > 0)
    wall_cut(usb[0], usb[1], mcu[2] + 90, usb_cutout[0],
             mcu_flipped ? z_wall_top - usb_z0 + 1 : usb_cutout[1], usb_z0);
  if (len(extra_cutouts) > 0) for (c = extra_cutouts) wall_cut(c[0], c[1], c[2], c[3], c[4], c[5]);
}

module battery_fence() if (has_bay && !has_pod && battery_fence[0] > 0 && battery_well_floor == 0)
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

// floor support at the controller's USB end (the far end stands on the plate's corner tabs / ledge):
// unflipped, one post under the connector's centre; flipped, two posts under the component side's outer
// corners at |x| 5.5-8.5 (beside the hanging USB connector and its shell lugs)
module mcu_end_post() if (cradle && mcu_end_post[0] > 0) at_mcu() {
  if (mcu_flipped) {
    for (s = [-1, 1]) translate([s > 0 ? 5.5 : -8.5, cr_yb - 1.6, floor_t - eps])
      cube([3, 1.4, z_mcu_bot - key_pcb_post_gap - floor_t + eps]);
  } else
  translate([-mcu_end_post[0] / 2, cr_yb - 1 - mcu_end_post[1], floor_t - eps])
    cube([mcu_end_post[0], mcu_end_post[1], z_mcu_bot - key_pcb_post_gap - floor_t + eps]);
}

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
  if (has_bay && !has_pod && battery_well_floor > 0)   // battery well sunk into the floor (its walls locate the cell)
    translate([0, 0, battery_well_floor]) linear_extrude(floor_t - battery_well_floor + eps) battery_2d(well_clearance);
}

// ---- nice!view: hanging ring with ledges + bezel screw bosses, the pocket cuts, and the separate bezel part
module at_nv() translate([nv_cx, nv_cy]) children();

module nv_solid() at_nv() {
  translate([-(nv_W / 2 + nv_ring_w), -(nv_L / 2 + nv_ring_w), z_nv_bot - nv_ledge_te])
    cube([nv_W + 2 * nv_ring_w, nv_L + 2 * nv_ring_w, z_plate_bot - (z_nv_bot - nv_ledge_te) + eps]);
  for (b = nv_boss_off) translate([b[0], b[1], z_plate_bot - nv_boss_h]) cylinder(d = nv_boss_d, h = nv_boss_h + eps);
}

module nv_cuts() at_nv() {
  translate([-nv_W / 2, -nv_L / 2, z_nv_bot]) cube([nv_W, nv_L, 20]);                           // PCB pocket
  translate([-(nv_W / 2 - nv_ledge_w), -nv_L / 2, -1]) cube([nv_W - 2 * nv_ledge_w, nv_L, 30]);  // through opening (wires, pads)
  for (b = nv_boss_off) translate([b[0], b[1], z_plate_bot - nv_boss_h - 1]) cylinder(d = nv_boss_hole_d, h = nv_boss_h + plate_t + 2);
}

module bezel_2d() difference() {
  offset(r = nv_bezel_r) offset(delta = -nv_bezel_r) rect(nv_bezel_size[0], nv_bezel_size[1]);
  translate([0, nv_glass_shift]) rect(nv_glass[0] + 2 * nv_window_clearance, nv_glass[1] + 2 * nv_window_clearance);
  for (b = nv_boss_off) translate(b) circle(d = nv_bezel_hole_d);
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
  rail_z0 = mcu_flipped ? z_mcu_bot - 0.5 : z_ledge_bot;   // flipped: rails stop just below the board so
  translate([0, 0, rail_z0]) linear_extrude(z_plate_bot - rail_z0 + eps) difference() {         // wire tails exit underneath them
    translate([-(cr_W / 2 + rail_w), cr_yfar - rail_w]) square([cr_W + 2 * rail_w, cr_ywall - cr_yfar + rail_w]);
    translate([-cr_W / 2, cr_yfar]) square([cr_W, cr_ywall - cr_yfar + 1]);
  }
  if (mcu_flipped) {
    // far end: two corner tabs under the component side's outer 0.5 mm (clear of the edge-centred reset
    // and inboard of nothing else; eyeball your board's far corners before printing)
    for (s = [-1, 1]) translate([s > 0 ? 5 : -8.8, cr_yfar - 1, z_mcu_bot - ledge_t]) cube([3.8, mcu_clearance + 1.5, ledge_t + eps]);
    // roof pad: centre strip over the bare back, limiting lift to 0.2
    translate([-3, cr_yfar, z_mcu_top + 0.2]) cube([6, cr_ywall - cr_yfar, z_plate_bot - (z_mcu_top + 0.2) + eps]);
  } else
  translate([0, 0, z_ledge_bot]) linear_extrude(ledge_t)
    translate([-cr_W / 2, cr_yfar]) square([cr_W, mcu_clearance + mcu_far_ledge]);              // far end: strip under the edge only
  if (!mcu_flipped)
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
  if (mcu_flipped)
    difference() {   // board tunnel under the solid plate, open at the USB end; the roof pad stays
      translate([-cr_W / 2, cr_yfar, z_mcu_bot]) cube([cr_W, cr_ywall + 1 - cr_yfar, z_plate_bot - z_mcu_bot - eps]);
      translate([-3 - 0.01, cr_yfar - 1, z_mcu_top + 0.2 - 0.01]) cube([6.02, cr_ywall - cr_yfar + 2, 20]);
      // poke hole through the far rail to push the board out (plate off)
    }
  else
  difference() {   // board pocket, open at the USB end, minus the locating nubs at both ends of the wire channels
    translate([-cr_W / 2, cr_yfar, z_mcu_bot]) cube([cr_W, cr_ywall + 1 - cr_yfar, z_mcu_top + mcu_lift_gap - z_mcu_bot]);
    if (mcu_locate_len > 0) for (s = [-1, 1], e = [-1, 1])
      translate([s > 0 ? mcu_size[0] / 2 + mcu_clearance : -cr_W / 2 - 1,
                 e > 0 ? cr_yb - mcu_locate_len : -cr_yb - mcu_clearance - 1, z_mcu_bot - 1])
        cube([cr_W / 2 - mcu_size[0] / 2 - mcu_clearance + 1, mcu_locate_len + mcu_clearance + 1, 30]);
  }
  if (mcu_flipped) translate([0, cr_yfar - rail_w / 2, z_mcu_bot + 0.8]) rotate([90, 0, 0]) cylinder(d = 4, h = rail_w + 3, center = true);
  z0 = z_mcu_top + mcu_lift_gap - eps;
  if (!mcu_flipped)
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
// the ribs hang from the plate's underside to just short of whatever is beneath them: the main board
// on a PCB build, the per-key boards on a hand-wired one, or the switch body's bottom if neither.
// (Deriving the PCB build's from key_pcbs -- a hand-wired idea -- happened to give the same 3.2 mm,
// but turning key_pcbs off then stood the ribs straight on the board.)
rib_height = rib_h > 0 ? rib_h
           : build == "pcb" ? plate_to_pcb - plate_t - 0.3
           : (is_choc ? 2.2 : 5) - plate_t - (key_pcbs ? 0.3 : 0);
module plate_ribs_3d() translate([0, 0, z_plate_bot - rib_height]) linear_extrude(rib_height + eps) difference() {
  intersection() {
    offset(r = -lip_clearance - lip_w) cavity_2d();
    union() for (k = keys) at(k) rect(cutout + 1.6 + 2 * rib_clearance + 2 * rib_w, cutout + 1.6 + 2 * rib_clearance + 2 * rib_w);
  }
  for (k = keys) at(k) rect(cutout + 1.6 + 2 * rib_clearance, cutout + 1.6 + 2 * rib_clearance);
  for (h = holes) translate(h) circle(d = boss_d + 1);
}

// crush ribs: five half-round ribs per rail face, each centred ON the pocket wall so its outer
// half is buried in the rail (nothing bulges outward) and exactly crush_rib protrudes into the
// slot. Full rail height, so each is a clean perimeter deviation the slicer reproduces; the round
// profile is its own lead-in and concentrates the crush. Slot at the ribs = cr_W - 2*crush_rib.
// (No hull() here: FreeCAD implements hull by shelling out to the openscad binary and fails.)
module cradle_ribs() at_mcu()
  for (s = [-1, 1], yy = [4, 10, 16, 22, 28])
    translate([s * cr_W / 2, cr_yfar + yy, z_mcu_bot - 0.5])
      cylinder(r = crush_rib, h = z_plate_bot - (z_mcu_bot - 0.5) + eps, $fn = 24);

// plain rectangle on purpose: the STEP pass (OCC) cannot do the offset-in-offset rounding trick,
// and hull() is worse -- FreeCAD shells out to OpenSCAD for it and fails
module pod_2d(o = 0) at_mcu() rect(pod_iw + 2 * o, pod_il + 2 * o);

module pod_solid() translate([0, 0, z_plate_top - eps])
  linear_extrude(pod_ih + pod_wall + eps) pod_2d(pod_wall);
module pod_cut() translate([0, 0, z_plate_top]) linear_extrude(pod_ih) pod_2d(0);

module plate() {
  plate_hull();
  if (cradle && mcu_flipped && crush_rib > 0) cradle_ribs();   // after the cuts: they live inside the board tunnel
}

module plate_hull() difference() {
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
    if (build == "plate" && has_ctrl && reset_button) ctrl_solid(reset_c, reset_body, reset_recess);
    if (build == "plate" && has_ctrl && power_switch) ctrl_solid(power_c, power_body, power_recess);
    if (has_pod) pod_solid();
  }
  if (has_pod) pod_cut();
  if (has_nv) nv_cuts();
  if (build == "plate" && has_ctrl && reset_button) ctrl_cut(reset_c, reset_body, reset_legs, reset_recess);
  if (build == "plate" && has_ctrl && power_switch) ctrl_cut(power_c, power_body, power_legs, power_recess);
  for (h = holes) translate([h[0], h[1], z_plate_bot - 5]) cylinder(d = screw_d, h = plate_t + 10);
  if (cradle) {
    cradle_cuts();
    if (!mcu_flipped) wall_cutouts();   // unflipped only: the USB plug crosses the plate level
  }
}

// A printable stand-in for the PCB.  Print it flat, bumps up, then turn it over into the case: it
// checks the outline against the walls and bosses, that every switch's pins land in a hole, the
// plate-to-board spacing, where the controller and the two switches sit, and the cell's room --
// everything except the copper.  It is not as stiff as a real 1.6 mm board, so do not judge flex by it.
socket_bump = [[-8.71, 4.59], [0.49, 4.59], [0.49, 7.13], [7.47, 7.13],
               [7.47, 3.03], [-1.76, 3.03], [-1.76, 0.49], [-8.71, 0.49]];
module pcb_test() difference() {
  union() {
    linear_extrude(pcb_t) pcb_board_2d();
    if (pcb_test_sockets)
      for (k = keys) at(k) translate([0, 0, -1.85]) linear_extrude(1.85 + eps) polygon(socket_bump);
  }
  d = pcb_test_slop;
  for (k = keys) at(k) {
    translate([0, 0, -3]) cylinder(d = 4 + d, h = pcb_t + 6);                       // centre post
    for (sx = [-1, 1]) translate([sx * 5.08, 0, -3]) cylinder(d = 1.65 + d, h = pcb_t + 6);   // pegs
    for (p = [[-3.81, 2.54], [-3.81, -2.54], [2.54, 5.08], [2.54, -5.08]])          // switch pins
      translate([p[0], p[1], -3]) cylinder(d = 3 + d, h = pcb_t + 6);
  }
  if (build == "pcb") {
    at_mcu() for (sx = [-1, 1], i = [0 : mcu_pins - 1])                             // controller sockets
      translate([sx * 7.62, (mcu_pins - 1) * 1.27 - i * 2.54, -1]) cylinder(d = 1 + d, h = pcb_t + 2);
    if (has_ctrl && reset_button) for (l = reset_legs)
      translate([reset_c[0] + l[0], reset_c[1] + l[1], -1]) cylinder(d = 0.95 + d, h = pcb_t + 2);
    if (has_ctrl && power_switch) for (l = power_legs)
      translate([power_c[0] + l[0], power_c[1] + l[1], -1]) cylinder(d = 0.95 + d, h = pcb_t + 2);
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
  color("gray12") translate([0, 0, z_mcu_bot]) linear_extrude(mcu_pcb_t) mcu_2d();
  color("silver") at_mcu() translate([-4.5, mcu[4] / 2 - 7.35 + 1.3, mcu_flipped ? z_mcu_bot - 3.2 : z_mcu_top])
    cube([9, 7.35, 3.2]);   // USB-C (below the board when flipped)
}

module nv_3d() at_nv() {
  color("darkolivegreen", 0.9) translate([-nv_pcb[0] / 2, -nv_pcb[1] / 2, z_nv_bot]) cube(nv_pcb);
  color("black") translate([-nv_glass[0] / 2, nv_glass_shift - nv_glass[1] / 2, z_nv_top]) cube([nv_glass[0], nv_glass[1], nv_glass[2]]);
}

module ctrl_3d(p, body, recess, actuator, on_board = false) {
  zf = on_board ? z_pcb_top : z_plate_top - recess - body[2];
  color("dimgray") translate([p[0] - body[0] / 2, p[1] - body[1] / 2, zf]) cube(body);
  color("gainsboro") translate([p[0] - actuator[0] / 2, p[1] - actuator[1] / 2, zf + body[2]]) cube(actuator);
}

// Kailh MX hot-swap socket, roughly: it hangs under the board on the pin side of the switch and is
// what sets pcb_lift.  Drawn from the pad extents the PCB uses (model frame, y up).
module socket_3d(k) at(k) translate([-8.0, 1.4, z_pcb_bot - 1.85]) cube([14.8, 4.9, 1.85]);

// SOD-123 diode, drawn at the nominal slot in the band below each key.  tools/pcb_gen.py moves the
// handful that do not fit there (near a mounting boss, or the board edge); the board file is the
// authority on where each one actually is.
module diode_3d(k) at(k) translate([-1.35, -9.6, z_pcb_bot - 1.1]) cube([2.7, 1.6, 1.1]);

// Exploded view: every layer lifts by its own multiple of `explode`, so explode = 0 is exactly the
// assembled model and anything above it separates the stack in the order you put it together.
// the order is the order you build it in, so the gaps read as steps
ex_board = 1;   // the PCB, with its sockets, diodes and the two switches soldered on
ex_mcu   = 2;   // the controller, into its sockets
ex_batt  = 3;   // the cell into the pod above; in the floor well it comes out below the board, at 0.5
ex_plate = 4;   // the plate, carrying the pod, the windows and the ribs
ex_sw    = 5;   // switches, clipped into the plate
ex_cap   = 6;   // keycaps onto the switches

module assembly() {
  color("slategray") case_bottom();

  // the board and everything soldered to it
  if (build == "pcb") translate([0, 0, explode * ex_board]) {
    color("darkolivegreen", 0.7) translate([0, 0, z_pcb_bot]) linear_extrude(pcb_t) {
      if (cavity_from == "pcb") pcb_2d(); else pcb_board_2d();
    }
    if (show_electronics) {
      color("gray20") for (k = keys) socket_3d(k);
      color("gray35") for (k = keys) diode_3d(k);
      if (has_ctrl && reset_button) ctrl_3d(reset_c, reset_body, reset_recess, [3.5, 3.5, 3.3], true);
      if (has_ctrl && power_switch) ctrl_3d(power_c, power_body, power_recess, [1.5, 2, 3], true);
    }
  }
  // the cell, where it lives: a well in the floor, or the pod in the plate
  if (show_electronics && has_bay)
    translate([0, 0, explode * (has_pod ? ex_batt : 0.5)])
      color("firebrick", 0.85) translate([0, 0, z_batt_bot]) linear_extrude(battery[2]) battery_2d();
  // the controller: on sockets on the board, or held in the plate's cradle
  if (show_electronics && !cradle) translate([0, 0, explode * ex_mcu]) mcu_3d();


  translate([0, 0, explode * ex_plate]) {
    color("lightsteelblue") plate();
    if (show_electronics && cradle) translate([0, 0, -explode]) mcu_3d();   // in the plate's cradle
    if (show_electronics && build == "plate" && has_ctrl && reset_button) ctrl_3d(reset_c, reset_body, reset_recess, [3.5, 3.5, 3.3]);
    if (show_electronics && build == "plate" && has_ctrl && power_switch) ctrl_3d(power_c, power_body, power_recess, [1.5, 2, 3]);
    if (has_nv) {
      if (show_electronics) nv_3d();
      color("steelblue") at_nv() translate([0, 0, z_plate_top]) bezel();
    }
  }
  if (show_switches) translate([0, 0, explode * ex_sw]) color("dimgray") for (k = keys) switch_3d(k);
  if (show_keycaps) translate([0, 0, explode * ex_cap]) color("whitesmoke", 0.9) for (k = keys) keycap_3d(k);
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
  if (part == "info") echo(stack = [z_pcb_bot, z_pcb_top, z_plate_bot, z_plate_top, z_mcu_bot], pod = [pod_iw, pod_il, pod_ih],
                           holes = holes, bay = bay, ctrl = ctrl_rect, mcu = mcu, battery_c = batt_cc, reset = reset_c, power = power_c, bumpons = bumpons, keys = keys, post = key_pcb_post, post_x = [key_pcb_post_x]);
  if (part == "assembly")             assembly();
  else if (part == "section")         projection(cut = true) rotate([-90, 0, 0]) rotate([0, 0, -90]) translate([-section_x, 0, 0]) assembly();
  else if (part == "case")            case_bottom();
  else if (part == "plate")           plate();
  else if (part == "bezel")           bezel();
  else if (part == "bezel_2d")        bezel_2d();
  else if (part == "plate_2d")        plate_2d();
  else if (part == "case_outline_2d") outline_2d();
  else if (part == "cavity_2d")       cavity_2d();
  else if (part == "pcb_test")        pcb_test();
  else if (part == "pcb_2d")          pcb_2d();
  else if (part == "pcb_outline_2d")  pcb_board_2d();   // Edge.Cuts for the Pacino PCB (build = "pcb")
}
