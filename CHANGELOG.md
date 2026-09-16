# Changelog

What changed, for people who have already printed a case or ordered a board. Newest first. Each entry says
which parts it touches and whether an existing build is affected:

- **reprint** — the printed part changed in a way that matters (fit, hardware, a feature you'd want)
- **re-order** — the PCB changed; boards from before are different
- **reflash / rewire** — the firmware pin assignment changed
- nothing marked — docs, options that default off, or changes to parts you don't have to rebuild

The project went public on 2026-09-14. Everything before that is condensed at the bottom.

## 2026-09-16

- **The MagSafe ring is now printed in, by default.** Three test prints on the slim build settled it: the ring
  goes into a pocket at a print pause before layer 5, exposed through a window in a one-layer ledge, and holds a
  mount with nothing to stick and nothing to come off. `magsafe_style = "embedded"` with `magsafe_skin = 0` is
  the default for every variant; a 0.4 mm skin over the ring is the clean-looking option, a one-layer skin held
  better but tore along its lines, hence the ledge. The stick-on groove and the glued recess stay as options.
  Case only — **reprint** if you want the ring captive (the groove cases keep working as they are). Print
  with a pause and, if you use supports, a support blocker over the ring. All variants rebuilt.

## 2026-09-15

- **MagSafe ring: three ways to fit it.** The 1 mm recess under the index column printed on support, and
  the ring's adhesive does not hold on a support-interface surface (it holds fine on the bed-side surface —
  that's how it works on other PETG cases). `magsafe_style` now defaults to `"groove"`: no recess, the ring
  sticks straight onto the underside inside a one-layer locating groove. `"embedded"` prints the steel ring
  *into* the floor at a print pause (pocket behind 0.4 mm of floor, the model prints the pause height; set
  `magsafe_ring_id` / `magsafe_ring_t` to your ring; the pocket is exactly the ring's height so the ceiling is laid
  onto the steel rather than bridged — the first test print showed a bridged annulus sagging along the ring).
  `"recess"` is the old pocket, for gluing. Case only
  — **reprint** if your ring won't stay on, otherwise the old recess is still fine with glue. All variants
  rebuilt with the groove.
- **M3 hardware option.** `screw_size = "M3"` resizes the insert holes (4.0 mm for 4.2 mm OD inserts),
  the counterbores, the plate's clearance holes (3.4 mm) and, in the slim build, the spacer bosses, wall
  channel, wall and board holes. Default stays M2, so nothing changes unless you ask for it. An existing
  M2 board can be drilled/filed to 3.4 mm at seven of its eight holes; the README says which one can't and
  how `m2_holes` keeps it M2.

## 2026-09-14

- **Insert holes get a 0.6 mm counterbore.** Heat-set inserts push a ring of plastic up around them, and
  standing proud of the boss face it kept the plate (hand-wired) or the board (slim build) from seating
  without trimming. Every insert hole now opens into a 4.2 × 0.6 mm relief; press the insert down until it
  bottoms and the flash stays below the face. Case and the `insert_test` coupon — **reprint** the case if
  your plate or board doesn't sit flat on the bosses (or trim the flash on the case you have). All variants
  rebuilt.
- Carry case removed (the two-tray design from 2026-09-08 and its files).
- README: more photos.

## Before publication (2026-08-23 → 2026-09-12)

- **2026-09-12 — slim PCB revision 2.** Three things the first batch of boards taught: the controller sits
  on top of the board (opposite the sockets), which swaps its pin rows relative to what the generator
  assumed, so per-half pin tables, silkscreen faces and the firmware lists are computed for that; the
  reset switch footprint had the 12 mm tactile's legs paired wrong (a normally fitted switch held RST at
  GND and the nano never booted); the battery/GND jumpers moved out from under the bay's corner boss.
  **re-order** — boards from before this date have the old reset footprint and jumper placement.
- **2026-08-31 — rows rewired** to pro_micro 20/19/18/16/10 (columns unchanged on 9/8/7/6/5). **rewire /
  reflash** for hand-wired halves built from the earlier wiring guide; display builds move row 3 to pin 21.
- **2026-08-27 — slim build fixes:** screw channels up the wall over the insert holes, 3 mm wall, three
  pillars pulled in from the wall; the plate's rim cut across the whole controller window at the USB end;
  floor pillars under the board. Slim case, plate and boards.
- **2026-08-25 — the slim build:** `build = "pcb"` with a generated reversible board (KiCad 9, gerbers),
  the 902030 in a plate pod or a 303040 flat under the board, 11.5 mm to the plate top; the
  `pacino_pcb` firmware shield. MagSafe recess kept clear of the battery well.
- **2026-08-24 — controller flipped** component-side-down with cradle crush ribs, the battery sunk into a
  floor well, and the nice!view stacked over the controller.
- **2026-08-23 — first commit:** the parametric hand-wired build, ZMK config with GitHub Actions builds,
  the variant gallery.
