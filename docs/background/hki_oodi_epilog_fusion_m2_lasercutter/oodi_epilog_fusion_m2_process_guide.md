# Helsinki Oodo Library Epiolog Fusion M2 laser cutter process guide

## 1. Oodi Epilog Laser Cutter References
Time Booking and general info: https://varaamo.hel.fi/en/reservation-unit/634

Lists of materials suitable for the laser cutter:
https://www.epiloglaser.com/how-it-works/laser-material-compatibility
https://wiki.aalto.fi/display/AF/Laser+Cutter+Materials

Model: Epilog Fusion M2 75W CO2
- Size of the cutting and engraving area: 1,016 x 711 mm, height max. 336mm.
- Supported file formats: JPG, PDF, EPS
- Resolution: 75–1200 dpi
- Material sheets from library are 60cm x 60cm and the cost varies on the material and thickness.
  Special permission from a library expert is needed to etch your own material.

Laser cutter basic user instructions, pdf: https://www.dropbox.com/scl/fi/n4ppp7l4jd3a7j0d34abi/Laserleikkuri_ENG_v5.pdf

Safety instructions and most common problems, pdf: https://www.dropbox.com/scl/fi/csdemqbu8jl8uez8zd206/Laserleikkuri_turvaohje_ENG.pdf

Manufacturer’s operating manual, pdf: https://www.epiloglaser.com/assets/downloads/manuals/fusion-manual-web.pdf

One 1hr or 2hr timeslot can typically be reserved one month in advance, unless someone cancels an earlier slot.
The laser cutter is almost always fully booked for next 30 days.

## 2. Process: Turn equipment on
Turn Laser Cutter and library's dedicated cable-attached PC on.
Turn Air Conditioning to max for 1-4 hours.
Turn Laser Cutter's air blower on during cutting to vent smoke outdoors.

## 3. Confirmed SVG routing behaviour (Epilog Fusion M2 via CorelDRAW)

Tested with `00_corel_calibration.svg` (2026-03-19):
- stroke-width 0.001–0.1mm → **vector cut** (colour irrelevant)
- stroke-width 0.5mm → **raster etch** (colour irrelevant)
- Routing is determined by stroke-width alone; colour has no effect on this machine/driver combo.

Implication for SVG authoring:
- Use stroke-width=0.1 for cut lines (confirmed hairline threshold).
- Use stroke-width=0.3 for etch lines (safely above 0.1, below 0.5 — will cut, not etch).
  **TODO**: re-test stroke-width=0.3 explicitly; current etch standard may need to move to 0.5.

## 4. Kerf calibration (finger joints, 3mm plywood)

File: `testrun_inputs/02_kerf_calibration.svg` (70×20mm)

**What it tests:** 5 slot pieces (slot widths 2.0, 2.4, 2.8, 3.2, 3.6mm) vs 1 tab piece (tab width 3.0mm, depth 3.0mm). All cuts are red, stroke-width=0.1.

**How to run:**
1. Cut `02_kerf_calibration.svg` — vector cut only, no raster.
2. Insert the tab piece into each slot. Note the tightest slot that still assembles without forcing.
3. Record the winning slot width — this is the kerf-compensated slot dimension to use in the box generator for this laser + 3mm plywood.
4. Optionally: measure actual tab and slot widths with calipers to compute actual kerf per side.

**Background:** Run01 (28 Feb 2026) produced very loose joints. Slot widths are biased well below nominal (3.0mm) to compensate for the laser kerf removing material on both sides of the cut line. Tab depth is set to 3.0mm = material thickness (run01 also had tabs that were too short).

**Results to record here after testing:**
- Winning slot width: _TBD_
- Measured tab width (actual): _TBD_
- Measured slot widths (actual): _TBD_
- Computed kerf per side: _TBD_

## 5. Known issues
The max thickness that can be cut is 6mm plywood.
The Laser Cutter is in near constant operation 10 am - 8 pm except Monday mornings (routine maintenance) and public holidays.
Over time, the smoke coats the lens making laser cutting of 6 mm plywood less effective.
It can be helpful to make 6mm drawings such that they can be flipped around axis of symmetry to cut from front and back,
when possible. Many drawings might have no symmetry, burning them twice may help (but their burnt surface is very charred afterwards).

## 6. Process

1. Follow the user guide https://www.dropbox.com/scl/fi/n4ppp7l4jd3a7j0d34abi/Laserleikkuri_ENG_v5.pdf

2. At the laser cutter:
   Put your sheet on the laser cutter bed.
   Adjust and set the laser focus for the material thickness according to instructions, using the 'focus feature'.
   Adjust and set the (0,0) origin point on the material using the 'jog' feature.

3. At the dedicated PC, do the following (happy path only described)
   3.1. Optional: Open Epilog Print Queue
   3.2. Open Corel Draw:
     - "New", use the Epilog Laser 1016x711,2 preset, it is set up for correct bed dimensions and for printing to the laser cutter
   3.3. Import your SVG. Place it on the drawing where appropriate for it to be burned/etched on the sheet
     (e.g. fresh plywood sheet vs. previous used one)
     - Visually check the drawing, especially that the overall dimensions are correct.
       How to handle anything wrong is not handled here: (RCA + correction)
   3.4. Press "Print"
        3.5.2. Print style is preset to "CorelDraw" defaults. Leave as is
        3.5.3. Press the settings "cog" icon, to the right of the "Printer" info field in the UI
   3.5. Cog settings opened popup window "Epilog Engraver Fusion Properties"
        - Choose raster-only, vector-only, combined based on your needs.
          (For some combined drawings, it is better to first do a raster-only print and after that do the vector cut print;
          this is because the printing happens in arbitrary order. Vector cut pieces 'fall' 1-2 mm based on the "bend" of the material
          the closer to the center of the sheet you get.)
        - Choose the correct Raster and Vector Settings for your material (Speed, Power, Frequency) from the table in https://www.dropbox.com/scl/fi/n4ppp7l4jd3a7j0d34abi/Laserleikkuri_ENG_v5.pdf
        - Press Print

4. Optional if any issues (loose cable between PC and laser cutter): check print job in Epilog Print Job

5. At the Laser Cutter:
- Wait for new job from PC
- Press "Go"öö
- If any errors, press "Stop" and possibly "Reset".
  Errors:
  - size is wrong compared to expectations / plans (should be checked in Corel Draw visually)
  - something to be etched is being cut, or vice-versa
- Remove and check piece

6. Done

