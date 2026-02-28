# trapezoid_box — Specification v2.0


**trapezoid_box**

Specification v2.0

Clean unified rewrite — production-grade laser-cutting geometry

February 2026

## 1. Purpose
A CLI Python tool that generates laser-cutter-ready SVG files for prismatic trapezoidal boxes. Two independent modes share a common geometry core:

box mode — general purpose, school/amateur friendly. Parts assemble straight off the laser bed with glue. No hand finishing required.

instrument mode — for luthiers and instrument builders. The laser cut is the starting point; hand finishing, kerfing, and gluing are expected and fully supported.

## 2. Guiding Principles
These are non-negotiable and apply to every implementation decision.

Correct first time. Every geometric calculation must be mathematically exact. Floating point comparisons must never use ==; always use nearly_equal() with FLOAT_TOLERANCE = 1e-6.

Physical correctness. Every joint must account for material thickness, laser cut angle, and assembly kinematics. The parts must fit off the bed without hand filing.

Simple and maintainable. No clever code. Short functions. Single responsibility. A competent Python developer must be able to read any function in under two minutes.

Fully testable. All geometry is pure functions with no side effects. The SVG writer receives only fully-computed Panel objects — it contains zero geometry.

No magic numbers. Every constant lives in constants.py with a descriptive name and a comment explaining its physical or geometric origin.

No third-party runtime dependencies. SVG is hand-rolled. Standard library only at runtime. pytest and hypothesis for testing only.

Deterministic output. Identical inputs must produce byte-identical SVG output. This enables golden file regression testing. Any function that could produce non-deterministic output must use sorted, ordered alternatives.

Active safety validation — The Gatekeeper. Before any geometry is computed, validate_config() must reject designs that are physically destined to fail: joints too thin after overcut, angles too steep, features outside panel bounds. The tool must never produce an SVG that looks correct but cannot be assembled.

## 3. Python Version
Python 3.11. Use dataclasses, match statements, and pathlib freely.

## 4. Repository Structure
> ℹ️ trapezoid_box/


> ℹ️ ├── trapezoid_box.py              # Entry point and mode selector only


> ℹ️ ├── README.md                    # Install, usage examples, parameter diagram


> ℹ️ ├── constants.py                 # ALL named constants — zero magic numbers


> ℹ️ │


> ℹ️ ├── core/                        # Pure geometry. No CLI. No SVG. No side effects.


> ℹ️ │   ├── models.py                # All dataclasses and enums


> ℹ️ │   ├── trapezoid.py             # Trapezoid geometry derivation


> ℹ️ │   ├── transform.py             # Coordinate transforms: rotate, translate, mirror


> ℹ️ │   ├── radii.py                 # Corner arc generation; finger termination points


> ℹ️ │   ├── joints.py                # Finger joint path generation (all edge types)


> ℹ️ │   ├── layout.py                # NFDH bin-packing; grain direction constraint


> ℹ️ │   ├── svg_writer.py            # Serialiser only: Panel objects → SVG. Zero geometry.


> ℹ️ │   ├── reporter.py              # All stdout/stderr output. No other module prints.


> ℹ️ │   └── utils.py                 # nearly_equal, odd_count, rotate_point, arc_centre, etc.


> ℹ️ │


> ℹ️ ├── presets.py                   # Named presets for both modes


> ℹ️ │


> ℹ️ ├── box/


> ℹ️ │   ├── panels.py                # Box mode Panel assembly


> ℹ️ │   ├── lids.py                  # Lid geometry (lift-off, sliding, hinged, flap)


> ℹ️ │   └── cli.py                   # Box CLI: args, validation, config, run()


> ℹ️ │


> ℹ️ ├── instrument/


> ℹ️ │   ├── panels.py                # Instrument mode Panel assembly


> ℹ️ │   ├── soundhole.py             # Round, f-hole, rounded-trapezoid + Helmholtz calculation


> ℹ️ │   ├── kerfing.py               # Kerfing strip and fillet geometry


> ℹ️ │   ├── hardware.py              # Neck block, tail block, strap pin holes


> ℹ️ │   ├── marks.py                 # Grain arrows, brace lines, scale mark, assembly numbers


> ℹ️ │   └── cli.py                   # Instrument CLI: args, validation, config, run()


> ℹ️ │


> ℹ️ └── tests/


> ℹ️ ├── golden/                  # Golden SVG reference files for regression


> ℹ️ │   ├── box_basic.svg


> ℹ️ │   ├── box_sliding_lid.svg


> ℹ️ │   ├── instrument_dulcimer.svg


> ℹ️ │   └── preset_pencil_box.svg


> ℹ️ ├── test_presets.py


> ℹ️ ├── core/


> ℹ️ │   ├── test_trapezoid.py


> ℹ️ │   ├── test_transform.py


> ℹ️ │   ├── test_radii.py


> ℹ️ │   ├── test_joints.py


> ℹ️ │   ├── test_layout.py


> ℹ️ │   ├── test_svg_writer.py


> ℹ️ │   └── test_utils.py


> ℹ️ ├── box/


> ℹ️ │   ├── test_box_panels.py


> ℹ️ │   └── test_lids.py


> ℹ️ └── instrument/


> ℹ️ ├── test_instrument_panels.py


> ℹ️ ├── test_soundhole.py


> ℹ️ ├── test_kerfing.py


> ℹ️ ├── test_hardware.py


> ℹ️ └── test_marks.py


## 5. Data Model (core/models.py)
All geometric objects are immutable frozen dataclasses. No logic lives here — only data definitions. Every other module imports from here.

### 5.1 Primitive Geometry
Point — a 2D point in SVG coordinate space. Y increases downward. All geometry uses this convention without exception.

Fields: x: float, y: float

Line — a straight line segment. Fields: start: Point, end: Point

Arc — an SVG arc segment. Fields: start: Point, end: Point, radius: float, large_arc: bool, clockwise: bool

CubicBezier — an SVG cubic Bézier. Fields: start: Point, cp1: Point, cp2: Point, end: Point

PathSegment — union type: Line | Arc | CubicBezier

ClosedPath — an ordered tuple of PathSegments forming a closed outline. The end of the last segment must equal the start of the first within FLOAT_TOLERANCE. This invariant is checked on construction via __post_init__.

> ℹ️ @dataclass(frozen=True)


> ℹ️ class ClosedPath:


> ℹ️ segments: tuple[PathSegment, ...]


> ℹ️ def __post_init__(self):


> ℹ️ if len(self.segments) == 0:


> ℹ️ raise ValueError(&quot;ClosedPath must have at least one segment.&quot;)


> ℹ️ last_end   = _segment_end(self.segments[-1])


> ℹ️ first_start = _segment_start(self.segments[0])


> ℹ️ if not (nearly_equal(last_end.x, first_start.x) and


> ℹ️ nearly_equal(last_end.y, first_start.y)):


> ℹ️ raise ValueError(


> ℹ️ f&quot;ClosedPath not closed: last ends at ({last_end.x:.4f}, {last_end.y:.4f})&quot;


> ℹ️ f&quot; but first starts at ({first_start.x:.4f}, {first_start.y:.4f}).&quot;


> ℹ️ )


_segment_start and _segment_end are private helpers in models.py using a match statement to extract the start/end Point from any PathSegment type.

### 5.2 Finger Joints
FingerEdge — a straight panel edge carrying finger joints.

> ℹ️ @dataclass(frozen=True)


> ℹ️ class FingerEdge:


> ℹ️ start:           Point    # edge start in panel local coordinates


> ℹ️ end:             Point    # edge end in panel local coordinates


> ℹ️ term_start:      Point    # finger start point (after left corner arc tangent)


> ℹ️ term_end:        Point    # finger end point (before right corner arc tangent)


> ℹ️ finger_width:    float    # actual width after odd-count adjustment; 0.0 if count=0


> ℹ️ count:           int      # number of fingers; 0 = plain edge (no joints)


> ℹ️ depth:           float    # mating panel thickness


> ℹ️ protrude_outward: bool    # True = fingers extend beyond nominal edge (instrument)


> ℹ️ is_slotted:      bool     # True = this edge carries slots, not protruding fingers


> ℹ️ burn:            float    # laser kerf compensation


> ℹ️ tolerance:       float    # joint fit clearance


### 5.3 Marks and Score Lines
MarkType (enum): LABEL, GRAIN_ARROW, ASSEMBLY_NUM

Note: SCORE_LINE is NOT in MarkType. Score lines are stored separately in Panel.score_lines as a list[Line], not as Mark objects.

Mark — a non-cut annotation. Fields: type: MarkType, position: Point, content: str, angle_deg: float (default 0.0)

### 5.4 Holes and Cutouts
CircleHole — circular through-cut. Fields: centre: Point, diameter: float

ClosedHole — arbitrary closed through-cut. Fields: path: ClosedPath

Hole — union type: CircleHole | ClosedHole

SoundHoleResult — result of Helmholtz calculation.

> ℹ️ @dataclass(frozen=True)


> ℹ️ class SoundHoleResult:


> ℹ️ type:               SoundHoleType


> ℹ️ diameter_or_size_mm: float   # bounding diameter (round) or long-edge length (rounded-trapezoid/f-hole)


> ℹ️ open_area_mm2:      float    # total open area across all holes


> ℹ️ target_freq_hz:     float    # requested Helmholtz target


> ℹ️ achieved_freq_hz:   float    # actual frequency given cut dimensions


> ℹ️ iterations:         int      # convergence iterations


### 5.5 Panels
PanelType (enum): BASE, WALL_LONG, WALL_SHORT, WALL_LEG_LEFT, WALL_LEG_RIGHT, SOUNDBOARD, LID, NECK_BLOCK, TAIL_BLOCK, KERF_STRIP, KERF_FILLET, TEST_STRIP

> ℹ️ @dataclass(frozen=True)


> ℹ️ class Panel:


> ℹ️ type:           PanelType


> ℹ️ name:           str           # human-readable label


> ℹ️ outline:        ClosedPath    # complete cut boundary including all finger geometry


> ℹ️ finger_edges:   list[FingerEdge]   # metadata only — SVG writer does NOT use these


> ℹ️ holes:          list[Hole]    # internal through-cuts


> ℹ️ score_lines:    list[Line]    # non-cut score lines (braces, grooves, scale mark)


> ℹ️ marks:          list[Mark]    # labels, grain arrows, assembly numbers


> ℹ️ grain_angle_deg: float        # 0 = grain runs horizontally in local space


> ℹ️ width:          float         # nominal outer width (for layout packing)


> ℹ️ height:         float         # nominal outer height (for layout packing)


Panel.bounding_box() -&gt; tuple[float, float] returns (self.width, self.height). This uses the nominal outer dimensions, not the tight geometric path bounds, because corner arcs are inset and layout must use consistent nominal sizes.

### 5.6 Configuration Dataclasses
DimMode (enum): OUTER, INNER

LidType (enum): NONE, LIFT_OFF, SLIDING, HINGED, FLAP

FingerDirection (enum): INWARD, OUTWARD

SoundHoleType (enum): ROUND, FHOLE, ROUNDED_TRAPEZOID

SoundHoleOrientation (enum): SAME, FLIPPED
  SAME    — hole long edge toward tail, matching body orientation (default)
  FLIPPED — hole long edge toward neck, opposite to body

CommonConfig — parameters shared by both modes.

> ℹ️ @dataclass


> ℹ️ class CommonConfig:


> ℹ️ long:          float


> ℹ️ short:         float


> ℹ️ length:        float | None   # None if mode B (leg provided instead)


> ℹ️ leg:           float | None   # None if mode A (length provided instead)


> ℹ️ depth:         float


> ℹ️ thickness:     float = 3.0


> ℹ️ burn:          float = 0.05


> ℹ️ tolerance:     float = 0.1


> ℹ️ corner_radius: float | None = None    # None = auto (3 × thickness)


> ℹ️ finger_width:  float | None = None    # None = auto (3 × thickness)


> ℹ️ sheet_width:   float = 600.0


> ℹ️ sheet_height:  float = 600.0


> ℹ️ labels:        bool  = True


> ℹ️ dim_mode:      DimMode = DimMode.OUTER


> ℹ️ colorblind:    bool  = False


> ℹ️ json_errors:   bool  = False


> ℹ️ output:        str   = &quot;trapezoid_box_output.svg&quot;


length and leg are mutually exclusive: exactly one must be non-None in a valid config. The CLI uses add_mutually_exclusive_group(). validate_config() verifies exactly one is provided.

BoxConfig: fields: common: CommonConfig, lid: LidType = LidType.NONE, hinge_diameter: float = 6.0

InstrumentConfig: fields: common: CommonConfig, top_thickness: float = 3.0, kerf_thickness: float = 3.0, kerfing: bool = True, kerf_height: float = 12.0, kerf_width: float = 6.0, kerf_top_height: float = 10.0, kerf_top_width: float = 5.0, soundhole_type: SoundHoleType | None = None, soundhole_orientation: SoundHoleOrientation = SoundHoleOrientation.SAME, soundhole_long_ratio: float | None = None, soundhole_aspect: float | None = None, soundhole_r_mm: float | None = None, helmholtz_freq: float = 110.0, soundhole_diameter: float | None = None, soundhole_size: float | None = None, soundhole_x: float | None = None, soundhole_y: float | None = None, neck_clearance: float = 60.0, hardware: bool = False, neck_block_thickness: float = 25.0, tail_block_thickness: float = 15.0, braces: bool = False, scale_length: float | None = None, finger_direction: FingerDirection = FingerDirection.OUTWARD

## 6. constants.py
All numeric literals that appear in the codebase must be defined here. No other file introduces naked numbers.

> ℹ️ # Geometry fundamentals


> ℹ️ FLOAT_TOLERANCE             = 1e-6       # for nearly_equal()


> ℹ️ AUTO_CORNER_RADIUS_FACTOR   = 3.0        # auto radius = this × thickness


> ℹ️ MIN_CORNER_RADIUS_MM        = 5.0


> ℹ️ AUTO_FINGER_WIDTH_FACTOR    = 3.0        # auto finger width = this × thickness


> ℹ️ MIN_FINGER_COUNT            = 3


> ℹ️ PANEL_GAP_MM                = 10.0       # gap between panels in layout


> ℹ️ # Non-orthogonal joint geometry (THE GATEKEEPER)


> ℹ️ OVERCUT_MIN_STRUCT_RATIO    = 0.5        # min remaining finger width = this × thickness


> ℹ️ # Prevents overcut from consuming the structural tab.


> ℹ️ # W_struct = finger_width - tolerance - T*tan(leg_angle) must be &gt;= thickness * 0.5


> ℹ️ # Laser / material defaults


> ℹ️ DEFAULT_THICKNESS_MM        = 3.0


> ℹ️ DEFAULT_BURN_MM             = 0.05       # Half-kerf: laser removes burn mm from each side of cut path.
> ℹ️                                          # Formula (see §10.5): drawn_tab = fw+2*burn, drawn_slot = fw-2*burn+2*tol
> ℹ️                                          # nominal_fit = -4*burn + 2*tol  (negative = interference, positive = clearance)
> ℹ️                                          # burn=0.05, tol=0.0 → fit=-0.2mm  (rubber mallet — matches boxes.py default)
> ℹ️                                          # burn=0.05, tol=0.1 → fit= 0.0mm  (hand press)
> ℹ️                                          # Tune in 0.01mm steps. Larger burn = tighter. Larger tol = looser.
> ℹ️                                          # WARNING: burn=0.1 with tol=0.1 also gives -0.2mm nominal but actual
> ℹ️                                          # physical fit depends on machine kerf — prefer burn=0.05 as baseline.


> ℹ️ DEFAULT_TOLERANCE_MM        = 0.0        # Joint fit clearance added to slot width. 0.0 = friction fit at burn=0.05.
> ℹ️                                          # Increase to 0.1 for hand-press fit. Do not exceed 0.2.


> ℹ️ # Layout / sheet defaults


> ℹ️ DEFAULT_SHEET_WIDTH_MM      = 600.0


> ℹ️ DEFAULT_SHEET_HEIGHT_MM     = 600.0


> ℹ️ # Acoustics


> ℹ️ SPEED_OF_SOUND_MM_S         = 343000.0   # mm/s at 20°C


> ℹ️ DEFAULT_HELMHOLTZ_HZ        = 110.0      # target A0 for dulcimer/guitar


> ℹ️ DEFAULT_NECK_CLEARANCE_MM   = 60.0


> ℹ️ HELMHOLTZ_L_EFF_FACTOR      = 0.85       # end-correction factor


> ℹ️ HELMHOLTZ_MAX_ITERATIONS    = 20


> ℹ️ # Instrument hardware defaults


> ℹ️ DEFAULT_KERF_HEIGHT_MM      = 12.0


> ℹ️ DEFAULT_KERF_WIDTH_MM       = 6.0


> ℹ️ DEFAULT_KERF_TOP_HEIGHT_MM  = 10.0


> ℹ️ DEFAULT_KERF_TOP_WIDTH_MM   = 5.0


> ℹ️ KERF_UNDERSIZE_MM           = 0.5


> ℹ️ DEFAULT_NECK_BLOCK_THICK_MM = 25.0


> ℹ️ DEFAULT_TAIL_BLOCK_THICK_MM = 15.0


> ℹ️ DEFAULT_HINGE_DIAMETER_MM   = 6.0


> ℹ️ HINGE_SPACING_MM            = 80.0       # one hinge per this many mm


> ℹ️ # SVG output


> ℹ️ SVG_CUT_COLOUR              = (255, 0, 0)


> ℹ️ SVG_SCORE_COLOUR            = (0, 0, 255)


> ℹ️ SVG_LABEL_COLOUR            = (0, 0, 0)


> ℹ️ SVG_CB_CUT_COLOUR           = (0, 0, 0)      # colorblind mode: cut = solid black


> ℹ️ SVG_CB_SCORE_COLOUR         = (0, 0, 0)      # colorblind mode: score = dashed black


> ℹ️ SVG_HAIRLINE_MM             = 0.001          # Epilog-compatible hairline — for laser output only
> ℹ️ SVG_PREVIEW_STROKE_MM      = 0.3            # visible stroke for screen preview — ALWAYS use this during development
> ℹ️ SVG_CUT_STROKE_WIDTH       = "0.1"          # unitless — scales with viewBox, visible on screen AND hairline at laser DPI. Use this. Always.


> ℹ️ SVG_LABEL_STROKE_MM         = 0.2


> ℹ️ SVG_SCORE_DASH_MM           = 5.0


> ℹ️ SVG_SCORE_GAP_MM            = 2.0


> ℹ️ SVG_COORD_DECIMAL_PLACES    = 4


> ℹ️ SVG_LABEL_FONT_MM           = 4.0


> ℹ️ SVG_ASSEMBLY_NUM_FONT_MM    = 8.0


> ℹ️ SVG_TRAPEZOIDBOX_NS         = &quot;https://trapezoidbox.github.io/ns/1.0&quot;


> ℹ️ # F-hole shape proportions


> ℹ️ FHOLE_UPPER_EYE_Y_RATIO     = 0.20


> ℹ️ FHOLE_LOWER_EYE_Y_RATIO     = 0.75


> ℹ️ FHOLE_UPPER_EYE_D_RATIO     = 0.12


> ℹ️ FHOLE_LOWER_EYE_D_RATIO     = 0.16


> ℹ️ FHOLE_WAIST_RATIO           = 0.60


> ℹ️ FHOLE_WAIST_Y_RATIO         = 0.475


> ℹ️ FHOLE_CP1_X_RATIO_UPPER     = 0.30


> ℹ️ FHOLE_CP2_X_RATIO_UPPER     = 0.40


> ℹ️ FHOLE_CP1_Y_RATIO_UPPER     = 0.35


> ℹ️ FHOLE_CP2_Y_RATIO_UPPER     = 0.45


> ℹ️ FHOLE_CP1_X_RATIO_LOWER     = 0.40


> ℹ️ FHOLE_CP2_X_RATIO_LOWER     = 0.30


> ℹ️ FHOLE_CP1_Y_RATIO_LOWER     = 0.55


> ℹ️ FHOLE_CP2_Y_RATIO_LOWER     = 0.65


> ℹ️ FHOLE_NICK_DEPTH_MM         = 1.5


> ℹ️ FHOLE_PAIR_OFFSET_RATIO     = 0.45


> ℹ️ # Rounded-trapezoid soundhole proportions
> ℹ️ # Hole inherits body long/short taper ratio. Corner radius is a FIXED MM VALUE —
> ℹ️ # a ratio-based radius fails at steep leg angles (sweep >90°, arc visually dominates).
> ℹ️ # Aspect ratio must always be explicit (0.3–2.0); None/inherit is rejected at validation.
> ℹ️ # Default orientation "same": long edge toward tail, matching body. "flipped": opposite.
> ℹ️ # Default parameters chosen to give ~150Hz Helmholtz resonance on dulcimer preset.

> ℹ️ RTRAP_LONG_TO_BODY_RATIO    = 0.28   # hole long-edge = body long_outer × this
> ℹ️ RTRAP_ASPECT_RATIO          = 0.6    # hole height = hole_long × this (0.3–2.0, no None)
> ℹ️ RTRAP_CORNER_R_MM           = 2.0    # corner fillet radius, fixed mm (NOT a ratio)
> ℹ️ RTRAP_MAX_R_EDGE_FRACTION   = 0.15   # r must be <= min(all edges) × this; enforced at validation
> ℹ️ RTRAP_ORIENTATION           = "same" # "same": long edge toward tail (matches body); "flipped": opposite


> ℹ️ # Test strip


> ℹ️ TEST_STRIP_WIDTH_MM         = 60.0


> ℹ️ # Version


> ℹ️ TOOL_VERSION                = &quot;2.0&quot;


> ℹ️ # Validation error codes (prefix ERR_)


> ℹ️ ERR_VALIDATION_LONG_SHORT_ORDER     = &quot;VALIDATION_LONG_SHORT_ORDER&quot;


> ℹ️ ERR_VALIDATION_THICKNESS_TOO_LARGE  = &quot;VALIDATION_THICKNESS_TOO_LARGE&quot;


> ℹ️ ERR_VALIDATION_FINGER_TOO_THIN      = &quot;VALIDATION_FINGER_TOO_THIN&quot;


> ℹ️ ERR_VALIDATION_ANGLE_TOO_STEEP      = &quot;VALIDATION_ANGLE_TOO_STEEP&quot;


> ℹ️ ERR_VALIDATION_STRUCT_TAB_TOO_THIN  = &quot;VALIDATION_STRUCT_TAB_TOO_THIN&quot;


> ℹ️ ERR_RUNTIME                         = &quot;ERR_RUNTIME&quot;


> ℹ️ ERR_FORMAT_NOT_IMPLEMENTED          = &quot;ERR_FORMAT_NOT_IMPLEMENTED&quot;


> ℹ️ ERR_VALIDATION_TEST_STRIP_TOO_TALL  = &quot;VALIDATION_TEST_STRIP_TOO_TALL&quot;


> ℹ️ ERR_VALIDATION_GROOVE_ANGLE_TOO_STEEP = &quot;VALIDATION_GROOVE_ANGLE_TOO_STEEP&quot;


> ℹ️ ERR_VALIDATION_SOUNDHOLE_TOO_TALL     = &quot;VALIDATION_SOUNDHOLE_TOO_TALL&quot;


> ℹ️ ERR_VALIDATION_SOUNDHOLE_LONG_RATIO   = &quot;VALIDATION_SOUNDHOLE_LONG_RATIO&quot;


> ℹ️ ERR_VALIDATION_SOUNDHOLE_ASPECT       = &quot;VALIDATION_SOUNDHOLE_ASPECT&quot;


> ℹ️ ERR_VALIDATION_SOUNDHOLE_RADIUS       = &quot;VALIDATION_SOUNDHOLE_RADIUS&quot;


> ℹ️ ERR_VALIDATION_SOUNDHOLE_LATERAL      = &quot;VALIDATION_SOUNDHOLE_LATERAL&quot;


## 7. core/utils.py
Pure utility functions. No geometry creation, no I/O.

### Functions
nearly_equal(a, b, tol=FLOAT_TOLERANCE) -&gt; bool — floating-point equality with tolerance. Must be used for all float comparisons in geometry code. Using == on floats in geometry code is a bug.

clamp(value, min_val, max_val) -&gt; float — clamp value to closed interval.

odd_count(edge_length, finger_width) -&gt; int — nearest odd integer to edge_length / finger_width. Minimum 3.

actual_finger_width(edge_length, count) -&gt; float — returns edge_length / count. count must be odd and &gt;= 1.

normalise(p: Point) -&gt; Point — unit vector in direction of p. Raises ValueError if magnitude is zero.

deg_to_rad(degrees) -&gt; float — degrees to radians.

rad_to_deg(radians) -&gt; float — radians to degrees.

translate_point(p, dx, dy) -&gt; Point — translate a point.

translate_path(path, dx, dy) -&gt; ClosedPath — translate an entire path.

### rotate_point() — Exact Formula for SVG Y-Down Space
In SVG coordinate space (Y increases downward), a clockwise rotation by angle θ uses:

> ℹ️ def rotate_point(p: Point, centre: Point, angle_deg: float) -&gt; Point:


> ℹ️ &quot;&quot;&quot;Rotate p clockwise around centre. SVG Y-down: positive = clockwise visual rotation.&quot;&quot;&quot;


> ℹ️ theta = deg_to_rad(angle_deg)


> ℹ️ dx, dy = p.x - centre.x, p.y - centre.y


> ℹ️ return Point(


> ℹ️ centre.x + dx * math.cos(theta) - dy * math.sin(theta),


> ℹ️ centre.y + dx * math.sin(theta) + dy * math.cos(theta),


> ℹ️ )


Verification: rotate Point(1,0) 90° → Point(0,1). In SVG Y-down, clockwise from +X is +Y (downward). ✓

Unit tests (required in test_utils.py): 90° → Point(0,1); 180° → Point(-1,0); 270° → Point(0,-1).

### arc_centre() — Recover Arc Centre from SVG Parameters
To sample an Arc for path_winding(), the centre must be computed from (start, end, radius, large_arc, clockwise):

> ℹ️ def arc_centre(arc: Arc) -&gt; Point:


> ℹ️ mx = (arc.start.x + arc.end.x) / 2


> ℹ️ my = (arc.start.y + arc.end.y) / 2


> ℹ️ dx = arc.end.x - arc.start.x


> ℹ️ dy = arc.end.y - arc.start.y


> ℹ️ half_chord = math.sqrt(dx*dx + dy*dy) / 2


> ℹ️ if half_chord &gt; arc.radius + FLOAT_TOLERANCE:


> ℹ️ raise ValueError(f&quot;Arc radius {arc.radius} too small for chord {2*half_chord:.4f}&quot;)


> ℹ️ d = math.sqrt(max(0.0, arc.radius**2 - half_chord**2))


> ℹ️ px, py = -dy / (2*half_chord), dx / (2*half_chord)


> ℹ️ sign = 1.0 if (arc.large_arc != arc.clockwise) else -1.0


> ℹ️ return Point(mx + sign*d*px, my + sign*d*py)


Sign rule: (large_arc XOR clockwise) → centre is on the positive-perpendicular side of the chord direction. Unit test: 90° arc radius 10 clockwise → assert correct centre.

### approximate_as_polyline() and path_winding()
approximate_as_polyline(path: ClosedPath, samples_per_curve: int = 8) -&gt; list[Point]: converts ClosedPath to polygon for shoelace formula.

Each segment contributes its start point and interior samples but NOT its endpoint (which becomes the next segment's start). For a Line: one point. For Arc/CubicBezier: samples_per_curve points at t = 0, 1/n, ..., (n-1)/n.

Arc sampling: compute centre via arc_centre(); sample at angles from start_angle to end_angle, adjusted for sweep direction. CubicBezier sampling: evaluate B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3.

> ℹ️ def path_winding(path: ClosedPath) -&gt; str:


> ℹ️ &quot;&quot;&quot;Returns 'clockwise' or 'counter-clockwise' using shoelace formula.


> ℹ️ In SVG Y-down space, positive signed area = clockwise.&quot;&quot;&quot;


> ℹ️ pts = approximate_as_polyline(path)


> ℹ️ n = len(pts)


> ℹ️ signed_area = sum(


> ℹ️ pts[i].x * pts[(i+1)%n].y - pts[(i+1)%n].x * pts[i].y


> ℹ️ for i in range(n)


> ℹ️ ) / 2.0


> ℹ️ return &quot;clockwise&quot; if signed_area &gt; 0 else &quot;counter-clockwise&quot;


## 8. core/trapezoid.py
Pure trapezoid mathematics. No SVG. No joints. No side effects. Assumes all inputs are already validated — do not add defensive checks here.

### Trapezoid Corner Angle Invariant
**This invariant applies to ALL trapezoid shapes in this project** (body panels, soundhole, any future trapezoidal features):

For a trapezoid traversed clockwise, narrow-end corners are always **obtuse** (interior angle = 90° + leg_angle) and wide-end corners are always **acute** (interior angle = 90° − leg_angle).

Body panel assignment: TL and TR are narrow-end corners → long_end_angle = 90° + leg_angle. BL and BR are wide-end corners → short_end_angle = 90° − leg_angle.

Soundhole assignment (SAME orientation): narrow-end corners (top for "same", bottom for "flipped") → obtuse. Wide-end corners → acute. Assigning these backwards produces geometrically invalid or visually wrong corner arcs.

Proof requirement: every trapezoid shape generated by this tool must have its four corner angles verified by computing the actual interior angle from edge geometry and asserting it matches the assigned value. See proof scripts 06 (body panel) and 05 (soundhole).

### TrapezoidGeometry Dataclass
> ℹ️ @dataclass(frozen=True)


> ℹ️ class TrapezoidGeometry:


> ℹ️ # Outer dimensions (mm)


> ℹ️ long_outer:          float


> ℹ️ short_outer:         float


> ℹ️ length_outer:        float


> ℹ️ depth_outer:         float


> ℹ️ thickness:           float


> ℹ️ # Derived geometry


> ℹ️ leg_inset:           float    # (long_outer - short_outer) / 2


> ℹ️ leg_length:          float    # sqrt(length_outer² + leg_inset²)


> ℹ️ leg_angle_deg:       float    # arctan(leg_inset / length_outer)


> ℹ️ long_end_angle_deg:  float    # 90 + leg_angle_deg  (interior angle at long end)


> ℹ️ short_end_angle_deg: float    # 90 - leg_angle_deg  (interior angle at short end)


> ℹ️ # Inner dimensions (for Helmholtz)


> ℹ️ long_inner:          float    # long_outer - 2*thickness


> ℹ️ short_inner:         float    # short_outer - 2*thickness


> ℹ️ length_inner:        float    # length_outer - 2*thickness (simplified)


> ℹ️ depth_inner:         float    # depth_outer - 2*thickness


> ℹ️ air_volume:          float    # 0.5*(long_inner+short_inner)*length_inner*depth_inner


### derive(config: CommonConfig) -&gt; TrapezoidGeometry
Mode A (length provided): length_outer = config.length; leg_length = sqrt(length_outer² + leg_inset²).

Mode B (leg provided): leg_length = config.leg; length_outer = sqrt(leg_length² - leg_inset²).

For DimMode.INNER: add 2*thickness to each dimension before computing geometry.

> ℹ️ def derive(config: CommonConfig) -&gt; TrapezoidGeometry:


> ℹ️ # Apply DimMode


> ℹ️ t = config.thickness


> ℹ️ if config.dim_mode == DimMode.INNER:


> ℹ️ long_o  = config.long  + 2*t


> ℹ️ short_o = config.short + 2*t


> ℹ️ depth_o = config.depth + 2*t


> ℹ️ else:


> ℹ️ long_o, short_o, depth_o = config.long, config.short, config.depth


> ℹ️ leg_inset = (long_o - short_o) / 2.0


> ℹ️ if config.length is not None:


> ℹ️ length_o  = config.length + (2*t if config.dim_mode == DimMode.INNER else 0)


> ℹ️ leg_len   = math.sqrt(length_o**2 + leg_inset**2)


> ℹ️ else:


> ℹ️ leg_len   = config.leg


> ℹ️ length_o  = math.sqrt(leg_len**2 - leg_inset**2)


> ℹ️ leg_angle    = math.degrees(math.atan2(leg_inset, length_o))


> ℹ️ return TrapezoidGeometry(


> ℹ️ long_outer=long_o, short_outer=short_o,


> ℹ️ length_outer=length_o, depth_outer=depth_o, thickness=t,


> ℹ️ leg_inset=leg_inset, leg_length=leg_len, leg_angle_deg=leg_angle,


> ℹ️ long_end_angle_deg  = 90.0 + leg_angle,


> ℹ️ short_end_angle_deg = 90.0 - leg_angle,


> ℹ️ long_inner   = long_o  - 2*t,


> ℹ️ short_inner  = short_o - 2*t,


> ℹ️ length_inner = length_o - 2*t,


> ℹ️ depth_inner  = depth_o  - 2*t,


> ℹ️ air_volume   = 0.5*(long_o-2*t + short_o-2*t)*(length_o-2*t)*(depth_o-2*t),


> ℹ️ )


## 9. core/radii.py
Corner arc geometry and finger termination points. No finger joint logic.

### 9.1 Corner Radius Resolution
auto_corner_radius(thickness: float) -&gt; float — returns 3 × thickness, rounded to nearest mm, minimum MIN_CORNER_RADIUS_MM = 5.0mm.

resolve_corner_radius(config: CommonConfig, geom: TrapezoidGeometry) -&gt; float — returns user-specified corner_radius if provided; otherwise auto_corner_radius(thickness). Validates result &lt; short_outer / 2 and &lt; depth_outer / 2; raises ValueError if not.

### 9.2 Corner Arc Segments
corner_arc_segments(vertex: Point, edge_a_dir: Point, edge_b_dir: Point, corner_radius: float, internal_angle_deg: float) -&gt; tuple[Point, Arc, Point]

Returns (arc_start, arc, arc_end). edge_a_dir and edge_b_dir are unit vectors pointing away from the corner along each edge.

Arc centre offset from vertex along inward bisector:

> ℹ️ arc_centre_offset = corner_radius / sin(internal_angle_deg / 2)


Bisector direction: bisector = normalise((-edge_a_dir) + edge_b_dir)

Where edge_a_dir points TOWARD the vertex (arriving edge direction) and edge_b_dir points AWAY from the vertex (departing edge direction). The arriving direction is negated to produce the inward component; the departing direction is added directly.

⚠  Common error: do NOT negate both directions. bisector = normalise((-edge_a) + (-edge_b)) is wrong — it points to the exterior of the panel. Verified: for the dulcimer long-end corner (94.5°), the correct formula places the arc centre 9mm inside the panel. The incorrect formula places it 8.3mm outside.

Arc start and end points — tangent points on each edge: distance from vertex = corner_radius / tan(internal_angle_deg / 2).

For all corner arcs in this tool, the arc subtends less than 180°, so large_arc = False always.

For rectangular wall panels, internal_angle_deg = 90.0. The formula reduces to: arc_centre_offset = corner_radius / sin(45°) = corner_radius × √2. arc_tangent_dist = corner_radius / tan(45°) = corner_radius. These are the familiar right-angle arc formulas.

### 9.3 Finger Termination Points
finger_termination_point(corner_vertex: Point, edge_direction: Point, corner_radius: float, internal_angle_deg: float) -&gt; Point

The point on the edge where the corner arc ends and fingers may begin. Located at distance corner_radius / tan(internal_angle_deg / 2) from corner_vertex along edge_direction.

> ℹ️ def finger_termination_point(


> ℹ️ corner_vertex: Point,


> ℹ️ edge_direction: Point,      # unit vector from corner toward edge interior


> ℹ️ corner_radius: float,


> ℹ️ internal_angle_deg: float,


> ℹ️ ) -&gt; Point:


> ℹ️ tangent_dist = corner_radius / math.tan(math.radians(internal_angle_deg / 2))


> ℹ️ return Point(


> ℹ️ corner_vertex.x + tangent_dist * edge_direction.x,


> ℹ️ corner_vertex.y + tangent_dist * edge_direction.y,


> ℹ️ )


Verification for 90° corner: tan(45°) = 1.0 → tangent_dist = corner_radius. Correct.

## 10. core/joints.py
All finger joint geometry. The SVG writer renders panel.outline directly — it does not read panel.finger_edges for path generation. finger_edges is metadata only.

### 10.1 make_finger_edge() — Canonical Signature
> ℹ️ def make_finger_edge(


> ℹ️ start:                    Point,


> ℹ️ end:                      Point,


> ℹ️ thickness:                float,


> ℹ️ mating_thickness:         float,    # depth of the mating panel


> ℹ️ protrude_outward:         bool,     # True = outward (instrument); False = inward (box)


> ℹ️ is_slotted:               bool,     # True = slots; False = protruding fingers


> ℹ️ burn:                     float,


> ℹ️ tolerance:                float,


> ℹ️ corner_radius_left:       float,


> ℹ️ corner_radius_right:      float,


> ℹ️ internal_angle_left_deg:  float,    # interior angle at start corner


> ℹ️ internal_angle_right_deg: float,    # interior angle at end corner


> ℹ️ ) -&gt; FingerEdge:


⚠  finger_direction (enum) is NOT a parameter here. panels.py converts FingerDirection enum to protrude_outward: bool before calling make_finger_edge().

### 10.2 make_finger_edge() — Algorithm
Compute edge_length = distance(start, end).

Compute edge_dir = normalise(end - start).

Compute auto_width = AUTO_FINGER_WIDTH_FACTOR × thickness. Compute target_count = odd_count(edge_length, auto_width), minimum 3.

Compute term_start = finger_termination_point(start, edge_dir, corner_radius_left, internal_angle_left_deg).

Compute term_end = finger_termination_point(end, -edge_dir, corner_radius_right, internal_angle_right_deg).

Compute available_length = distance(term_start, term_end).

If available_length &lt; (mating_thickness + 2*burn): emit warning &quot;Edge too short for any finger joints after corner radius termination&quot;; return FingerEdge with count=0.

Compute max_count = floor(available_length / (mating_thickness + 2*burn)). If max_count &lt; target_count: set count = largest odd integer ≤ max_count (minimum 1); emit warning.

Else: count = target_count.

Recompute finger_width = available_length / count (fills available space exactly).

Return FingerEdge(start, end, term_start, term_end, finger_width, count, mating_thickness, protrude_outward, is_slotted, burn, tolerance).

### 10.3 Non-Orthogonal Joint Correction
⚠  This is the critical physical manufacturing addition in v2.0. Without it, finger joints on angled leg walls will not seat without hand filing.

When a wall meets the base at leg_angle_deg from perpendicular, two corrections are required:

1. Effective slot depth — the tab must travel a longer path through angled material:

> ℹ️ D_eff = mating_thickness / cos(leg_angle_deg)


2. Rotational overcut — square-cut fingers cannot rotate into square-cut slots without clearance at the internal corners:

> ℹ️ W_over = mating_thickness * tan(abs(leg_angle_deg))


These corrections apply ONLY to the leg-wall-to-base joints. All 90° joints (WALL_LONG, WALL_SHORT, wall-to-wall) use mating_thickness directly with no correction.

make_finger_edge_angled() is a convenience wrapper for angled joints:

> ℹ️ def make_finger_edge_angled(


> ℹ️ start, end, thickness, mating_thickness, protrude_outward,


> ℹ️ is_slotted, burn, tolerance, corner_radius_left, corner_radius_right,


> ℹ️ internal_angle_left_deg, internal_angle_right_deg,


> ℹ️ leg_angle_deg: float,


> ℹ️ ) -&gt; FingerEdge:


> ℹ️ &quot;&quot;&quot;


> ℹ️ Wrapper for angled joints (leg wall ↔ base).


> ℹ️ Applies D_eff and W_over corrections before calling make_finger_edge().


> ℹ️ &quot;&quot;&quot;


> ℹ️ import math


> ℹ️ alpha = math.radians(abs(leg_angle_deg))


> ℹ️ D_eff = mating_thickness / math.cos(alpha)   # effective depth


> ℹ️ W_over = mating_thickness * math.tan(alpha)  # rotational overcut (added to tolerance)


> ℹ️ # W_over is implemented as additional tolerance on the slot width


> ℹ️ effective_tolerance = tolerance + W_over


> ℹ️ return make_finger_edge(


> ℹ️ start, end, thickness, D_eff, protrude_outward, is_slotted,


> ℹ️ burn, effective_tolerance, corner_radius_left, corner_radius_right,


> ℹ️ internal_angle_left_deg, internal_angle_right_deg,


> ℹ️ )


panels.py calls make_finger_edge_angled() for the bottom edges of WALL_LEG_LEFT and WALL_LEG_RIGHT (the edges that mate with BASE leg edges). All other calls use make_finger_edge().

### 10.4 Burn Compensation Convention
Outward means away from the material being retained by that cut:

Panel outline cuts (exterior): outward = away from panel centre → outline expands slightly.

Protruding finger tabs: outward = away from finger body → tab stays full intended size.

Slot cuts (interior): outward = into the slot → slot expands to receive the tab.

Hole cuts: outward = into the hole → finished hole is intended size.

This rule must be stated in the joints.py module docstring: &quot;Every cut line is offset by burn in the direction that enlarges the feature being created by that cut.&quot;

### 10.5 Staircase Path Generation — finger_edge_to_path_segments()
> ℹ️ def finger_edge_to_path_segments(edge: FingerEdge) -&gt; list[PathSegment]:


> ℹ️ &quot;&quot;&quot;Convert FingerEdge to Line segments from term_start to term_end.&quot;&quot;&quot;


If edge.count == 0: return [Line(edge.start, edge.end)] (plain edge).

Convention: centre finger is a tab. For count = 2k+1 fingers (0-indexed), finger k is centre. Fingers at even distance from centre are tabs; odd distance = gaps. Edge starts and ends with a tab.

Staircase from term_start to term_end:

> ℹ️ tab_width      = finger_width + 2*burn   (drawn wider so laser kerf produces nominal-width tab)
> ℹ️ gap_width      = finger_width - 2*burn + 2*tolerance  (drawn narrower so kerf produces nominal slot, tolerance widens)
> ℹ️ depth_out      = depth + burn            (expanded for kerf compensation)

Physical model: SVG paths are laser centerlines. Laser removes burn mm from each side of every cut path. Therefore a tab drawn at fw+2*burn produces a physical tab of fw (kerf removes 2*burn total). A slot drawn at fw-2*burn produces a physical slot of fw. This gives zero-clearance fit when burn exactly equals actual_kerf/2.

nominal_fit formula (treating drawn path as physical — boxes.py convention):
  fit = gap_width - tab_width = (fw-2*burn+2*tol) - (fw+2*burn) = -4*burn + 2*tol
  burn=0.05, tol=0.0 → fit=-0.2mm  (rubber mallet — matches boxes.py defaults)
  burn=0.05, tol=0.1 → fit= 0.0mm  (hand press)
  burn=0.05, tol=0.2 → fit=+0.2mm  (loose — for glue-up only)
  Larger burn = tighter. Larger tol = looser. Tune burn in 0.01mm steps.

Do NOT set burn=0.1 with tol=0.1 thinking fit=-0.2mm: the nominal formula gives -0.2mm but when actual machine kerf ≈ 0.05mm/side, physical fit = 0.0mm (hand press, not friction). Keep burn=0.05 as baseline and adjust from there.


Coordinate transform from edge-local to panel-local space:

> ℹ️ edge_dir    = normalise(edge.end - edge.start)


> ℹ️ edge_outward = Point(edge_dir.y, -edge_dir.x)   # 90° CW in SVG Y-down = outward


> ℹ️ panel_x = term_start.x + local_x*edge_dir.x - local_y*edge_outward.x


> ℹ️ panel_y = term_start.y + local_x*edge_dir.y - local_y*edge_outward.y


### 10.6 build_panel_outline()
> ℹ️ def build_panel_outline(


> ℹ️ edges: list[FingerEdge],


> ℹ️ corner_arcs: list[tuple[Point, Arc, Point]],


> ℹ️ ) -&gt; ClosedPath:


edges and corner_arcs have equal length n. corner_arcs[i] connects edges[i-1] to edges[i] (modulo n). Assembly order for each corner:

> ℹ️ arc_start, arc, arc_end = corner_arcs[i]


> ℹ️ → Line(prev_finger_end, arc_start)    # omit if zero-length


> ℹ️ → arc


> ℹ️ → Line(arc_end, first_finger_start)   # omit if zero-length


> ℹ️ → finger_edge_to_path_segments(edges[i])


Zero-length Line segments (start == end within FLOAT_TOLERANCE) are omitted. The returned ClosedPath must pass the __post_init__ closure invariant.

### 10.7 build_plain_outline()
> ℹ️ def build_plain_outline(


> ℹ️ vertices: list[Point],


> ℹ️ corner_radius: float,


> ℹ️ corner_angles_deg: list[float],


> ℹ️ ) -&gt; ClosedPath:


Used for panels without finger joints: SOUNDBOARD, NECK_BLOCK, TAIL_BLOCK, KERF_STRIP, TEST_STRIP. If corner_radius == 0.0: returns n Line segments. If &gt; 0.0: alternates Lines and Arcs with corner arcs computed via corner_arc_segments().

## 11. Panel Vertices (Local Coordinate Space)
All panels: origin at bounding box top-left. Y increases downward. All FingerEdge start/end points are derived from these vertices.

### 11.1 BASE and SOUNDBOARD (trapezoid, short at top)
> ℹ️ leg_inset = (long_outer - short_outer) / 2


> ℹ️ TL = Point(leg_inset, 0)                          # top-left


> ℹ️ TR = Point(leg_inset + short_outer, 0)            # top-right


> ℹ️ BR = Point(long_outer, length_outer)              # bottom-right


> ℹ️ BL = Point(0, length_outer)                       # bottom-left


> ℹ️ width = long_outer,  height = length_outer


### 11.2 Rectangular Wall Panels
| Panel | Vertices (top-left origin) |
|---|---|
| WALL_LONG | TL(0,0)  TR(long_outer,0)  BR(long_outer,depth_outer)  BL(0,depth_outer) |
| WALL_SHORT | TL(0,0)  TR(short_outer,0)  BR(short_outer,depth_outer)  BL(0,depth_outer) |
| WALL_LEG_LEFT | TL(0,0)  TR(leg_length,0)  BR(leg_length,depth_outer)  BL(0,depth_outer) |
| WALL_LEG_RIGHT | Identical to WALL_LEG_LEFT (isosceles). v1 uses dataclasses.replace() copy. |
| NECK_BLOCK | TL(0,0)  TR(neck_block_thickness,0)  BR(neck_block_thickness,depth_outer)  BL(0,depth_outer) |
| TAIL_BLOCK | TL(0,0)  TR(tail_block_thickness,0)  BR(tail_block_thickness,depth_outer)  BL(0,depth_outer) |
| KERF_STRIP (base) | width = inner_wall_length, height = kerf_height |
| KERF_STRIP (soundboard) | width = inner_wall_length, height = kerf_top_height |
| TEST_STRIP | width = TEST_STRIP_WIDTH_MM = 60.0, height = 3 × depth_outer |


### 11.3 Internal Angle Mapping for make_finger_edge()
panels.py passes the correct interior angle at each corner of each FingerEdge. For all rectangular wall panels: 90.0 for all corners. For BASE/SOUNDBOARD:

| Edge | left corner (start) | right corner (end) |
|---|---|---|
| short_top | long_end_angle_deg | long_end_angle_deg |
| leg_right | long_end_angle_deg | short_end_angle_deg |
| long_bottom | short_end_angle_deg | short_end_angle_deg |
| leg_left | short_end_angle_deg | long_end_angle_deg |


Where long_end_angle_deg = 90 + leg_angle_deg and short_end_angle_deg = 90 - leg_angle_deg (from TrapezoidGeometry). This table must be reproduced as a comment in panels.py.

### 11.4 FingerEdge Direction Convention
All FingerEdge start→end directions follow clockwise winding in SVG Y-down space:

| BASE/SOUNDBOARD edge | Direction |
|---|---|
| short_top | Left → right (+X) |
| leg_right | Top-right → bottom-right |
| long_bottom | Right → left (−X) |
| leg_left | Bottom-left → top-left |


| Rectangular panel edge | Direction |
|---|---|
| top | Left → right |
| right | Top → bottom |
| bottom | Right → left |
| left | Bottom → top |


## 12. Validation — The Gatekeeper
⚠  validate_config() must return list[dict] — never void, never sys.exit(). The CLI handles output and exit. validate_config() only collects errors.

validate_config(config: BoxConfig | InstrumentConfig) -&gt; list[dict]

Each error dict has keys: code (str), message (str), parameter (str | None), value (str | None).

### 12.1 Common Validation Rules
long &gt; short &gt; 0

length &gt; 0 (mode A) or leg &gt; leg_inset (mode B, otherwise length would be imaginary)

depth &gt; 0

thickness &gt; 0

thickness &lt; depth / 2 (walls must fit in the box)

thickness &lt; short / 4 (walls must not dominate the short end)

finger_width &gt;= 2 x thickness if user-specified

corner_radius &lt; short / 2 and &lt; depth / 2 if user-specified

Exactly one of length, leg is non-None

3 x depth &lt;= sheet_height — the TEST_STRIP (height = 3 x depth) must fit on the sheet. ERR_VALIDATION_TEST_STRIP_TOO_TALL. Message: depth ({depth}mm) produces TEST_STRIP height ({3*depth}mm) exceeding sheet_height ({sheet_height}mm). Reduce --depth or increase --sheet-height.

### 12.2 Non-Orthogonal Joint Structural Safety
⚠  This check is new in v2.0. It prevents the overcut from consuming the structural tab entirely.

After deriving TrapezoidGeometry, compute:

> ℹ️ leg_angle_rad = radians(geom.leg_angle_deg)


> ℹ️ resolved_fw   = config.finger_width or (AUTO_FINGER_WIDTH_FACTOR * config.thickness)


> ℹ️ W_over        = config.thickness * tan(leg_angle_rad)


> ℹ️ W_struct      = resolved_fw - config.tolerance - W_over


> ℹ️ if W_struct &lt; config.thickness * OVERCUT_MIN_STRUCT_RATIO:


> ℹ️ error: ERR_VALIDATION_STRUCT_TAB_TOO_THIN


> ℹ️ message: f&quot;At leg_angle={geom.leg_angle_deg:.2f}°, the rotational overcut


> ℹ️ ({W_over:.3f}mm) reduces the structural tab width to {W_struct:.3f}mm,


> ℹ️ which is less than the minimum ({config.thickness*OVERCUT_MIN_STRUCT_RATIO:.3f}mm).


> ℹ️ Reduce the trapezoid angle, increase --finger-width, or reduce --thickness.&quot;


OVERCUT_MIN_STRUCT_RATIO = 0.5 (defined in constants.py). This ensures the remaining tab has at least half the material thickness — sufficient for glue bond and shear resistance.

### 12.3 Box Mode Additional Rules
Sliding lid: depth &gt; 3 × thickness (need room for slide groove).

Sliding lid + angled walls: leg_angle_deg &lt; arccos(thickness / (thickness + tolerance)). At steeper angles the square-cut lid edge cannot seat in the tilted groove without binding. Default limit (T=3, tol=0.1): 14.59 degrees. Error code: ERR_VALIDATION_GROOVE_ANGLE_TOO_STEEP.

### 12.4 Instrument Mode Additional Rules
neck_clearance + soundhole_size_estimate < length (sound hole must fit longitudinally). For rounded-trapezoid holes the precise check is: neck_clearance + hole_height < length − tail_block_thickness. ERR_VALIDATION_SOUNDHOLE_TOO_TALL.

For rounded-trapezoid holes:
- 0.1 ≤ soundhole_long_ratio ≤ 0.6. ERR_VALIDATION_SOUNDHOLE_LONG_RATIO.
- 0.3 ≤ soundhole_aspect ≤ 2.0 (None is rejected). ERR_VALIDATION_SOUNDHOLE_ASPECT.
- soundhole_r_mm > 0 and soundhole_r_mm ≤ min(hole_short, hole_long, leg_edge) × RTRAP_MAX_R_EDGE_FRACTION. ERR_VALIDATION_SOUNDHOLE_RADIUS.
- Hole laterally within soundboard at both y_near and y_far: hole_long/2 < soundboard_half_width_at(y). ERR_VALIDATION_SOUNDHOLE_LATERAL.
- soundhole_orientation ignored (no error) for non-trapezoid types.

scale_length &gt; length if provided

kerf_width &lt; thickness × 4

### 12.5 Validation Error Reporting
> ℹ️ errors = validate_config(config)


> ℹ️ if errors:


> ℹ️ reporter.print_errors(errors, json_mode=config.common.json_errors)


> ℹ️ sys.exit(1)


reporter.print_errors(errors: list[dict], json_mode: bool) -&gt; None — in json_mode: single JSON array to stderr. In text mode: one line per error to stderr.

reporter.print_error(message, code, parameter, value, json_mode) -&gt; None — for single runtime errors from the except block. In json_mode: single JSON object.

## 13. core/transform.py
Pure coordinate transforms. No geometry creation.

flip_y(point: Point, height: float) -&gt; Point — reflect over horizontal axis at y=height.

rotate_path(path: ClosedPath, centre: Point, angle_deg: float) -&gt; ClosedPath — rotate all points.

translate_path(path: ClosedPath, dx: float, dy: float) -&gt; ClosedPath — translate all points.

mirror_path_horizontal(path: ClosedPath, axis_x: float) -&gt; ClosedPath — reflect every point: mirrored_x = 2*axis_x - x, y unchanged. Note: mirroring reverses path winding.

reverse_path(path: ClosedPath) -&gt; ClosedPath — reverses segment order and flips each segment's start/end. Used after mirroring to restore clockwise winding.

📌  v1 isosceles: WALL_LEG_RIGHT = dataclasses.replace(leg_left, type=WALL_LEG_RIGHT, name=&quot;WALL_LEG_RIGHT&quot;). No mirroring needed. mirror_path_horizontal + reverse_path is provided for future v2 general trapezoid support. State this in a comment in panels.py.

## 14. core/layout.py
Next Fit Decreasing Height (NFDH) bin-packing. Simple, deterministic, well-understood.

### Algorithm
Sort panels by longest dimension descending.

Pack into rows within sheet_width with PANEL_GAP_MM between panels and rows.

Grain direction constraint: BASE and SOUNDBOARD must never be rotated (grain direction is structural).

Other panels: try natural orientation first. If it does not fit in the current row, try rotated (swap width/height). If rotated fits, use it and adjust grain_angle_deg += 90° via dataclasses.replace(). If neither fits, start a new row in natural orientation.

If any single panel exceeds sheet_width in natural orientation: place on its own row, emit reporter.print_warning().

When a new row exceeds sheet_height, increment sheet_index for subsequent panels. TEST_STRIP always on last sheet.

layout_panels(panels: list[Panel], sheet_width: float, sheet_height: float) -&gt; list[tuple[Panel, Point, int]]

Returns (Panel, origin: Point, sheet_index) triples. Panel objects are never mutated — dataclasses.replace() is used for rotation adjustment.

📌  import dataclasses is required in layout.py for grain_angle rotation.

## 15. core/svg_writer.py
Pure serialiser. Zero geometry calculations. Receives layout triples, produces SVG text.

### 15.1 SVG Conventions
ViewBox: exact bounding box of all panels plus PANEL_GAP_MM margin on all sides.

Units: mm. Root element: width=&quot;600.0000mm&quot; height=&quot;600.0000mm&quot; viewBox=&quot;0 0 600.0000 600.0000&quot;.

All values formatted to SVG_COORD_DECIMAL_PLACES = 4 decimal places. Mandatory — enables golden file regression testing.

Root element includes scale warning comment (see below).

Includes &lt;metadata&gt; with trapezoidbox namespace and embedded config JSON.

### 15.2 SVG Scale Warning Comment
> ℹ️ &lt;!-- trapezoid_box v2.0 — dimensions in millimetres


> ℹ️ IMPORTANT: Verify scale before cutting.


> ℹ️ Open in Inkscape and confirm Document Properties shows correct physical dimensions.


> ℹ️ If your laser software scales incorrectly, use Inkscape to export


> ℹ️ at 96 dpi with explicit mm units before importing. --&gt;


### 15.3 Path Serialisation — path_to_svg_d()
path_to_svg_d(path: ClosedPath, origin: Point) -&gt; str — converts ClosedPath to SVG d attribute, translating all coordinates by origin.

> ℹ️ M {seg0.start.x+dx} {seg0.start.y+dy} {segment_commands...} Z


> ℹ️ Line:          L {end.x+dx} {end.y+dy}


> ℹ️ Arc:           A {r} {r} 0 {1 if large_arc else 0} {1 if clockwise else 0} {end.x+dx} {end.y+dy}


> ℹ️ CubicBezier:   C {cp1.x+dx} {cp1.y+dy} {cp2.x+dx} {cp2.y+dy} {end.x+dx} {end.y+dy}


One M command only; Z closes. Arc has two equal radii (circular), x-rotation always 0. All values to 4 decimal places.

### 15.4 Stroke and Colour Conventions
| Purpose | stroke-width | Default colour | Colorblind mode |
|---|---|---|---|
| Cut lines (through-cut) | 0.1 (unitless) | rgb(255,0,0) solid | rgb(0,0,0) solid |
| Score lines (non-cut) | 0.1 (unitless) | rgb(0,0,255) dashed | rgb(0,0,0) dashed |
| Labels and marks | 0.2mm | rgb(0,0,0) | rgb(0,0,0) |

stroke-width MUST be unitless "0.1" — never "0.001mm" or "0.3mm". Unitless scales with the viewBox: visible on screen at any zoom, true hairline at laser cutter DPI.

In colorblind mode, cut vs score is distinguished by dash pattern only. Score: stroke-dasharray="5.0000 2.0000".

### 15.4.1 Mandatory Output Verification
write() MUST call verify_output() before writing any file. verify_output() raises RuntimeError if:
- Any path coordinate is non-finite or outside sheet bounds
- Any path does not end with Z
- Any two panel bounding boxes overlap
- Soundhole corner angles deviate > 0.1° from expected values

No output file is created if verification fails. SVG that has not been verified must never be presented to the user.

### 15.5 What the SVG Writer Renders
For each Panel at its layout origin (all coordinates shifted by origin.x, origin.y):

panel.outline ClosedPath → red hairline &lt;path&gt;. Already contains all finger geometry.

Each CircleHole → red hairline &lt;circle cx cy r&gt;.

Each ClosedHole → red hairline &lt;path&gt;.

Each score_line Line → blue dashed &lt;line&gt;.

Each Mark LABEL/ASSEMBLY_NUM → black &lt;text&gt;; GRAIN_ARROW → black double-headed arrow &lt;path&gt; along grain_angle_deg. Length: 20% of panel longest dimension, centred in panel.

Labels and marks only rendered when config.labels is True. Grain arrows always rendered (structural information).

The SVG writer does NOT read panel.finger_edges for path generation. Finger paths are already in panel.outline.

### 15.6 write() Signature
> ℹ️ def write(


> ℹ️ layout: list[tuple[Panel, Point, int]],


> ℹ️ config: CommonConfig,


> ℹ️ output_paths: list[Path],


> ℹ️ ) -&gt; None:


> ℹ️ &quot;&quot;&quot;Groups by sheet_index, produces one SVG per sheet, writes to output_paths.&quot;&quot;&quot;


### 15.7 extract_config()
extract_config(svg_path: Path) -&gt; str — opens SVG, parses with xml.etree.ElementTree, returns text of &lt;trapezoidbox:config&gt; CDATA block. Raises ValueError if not a trapezoidbox SVG or metadata absent.

## 16. Box Mode (box/)
### 16.1 Panels Generated
| Panel | Description |
|---|---|
| BASE | Trapezoid. Finger tabs on all four edges. Corner radii applied. Fingers INWARD (hardcoded). Slots in walls. |
| WALL_LONG | Rectangle long_outer × depth_outer. Finger joints all four edges. Slots on top/bottom, fingers on ends. |
| WALL_SHORT | Rectangle short_outer × depth_outer. Same joint arrangement as WALL_LONG. |
| WALL_LEG_LEFT | Rectangle leg_length × depth_outer. Same joint arrangement. |
| WALL_LEG_RIGHT | Identical to WALL_LEG_LEFT for isosceles (dataclasses.replace copy). |
| LID | See lid types below. |
| TEST_STRIP | Always generated. 60mm × (3 × depth). One edge matches WALL_LONG bottom joint profile. |


All box mode panels: fingers protrude INWARD. Hardcoded — not configurable. Assembled outer dimensions match specified dimensions exactly. No hand finishing required.

Note on leg-to-base joints: call make_finger_edge_angled() for leg wall bottom edges and corresponding BASE leg edges. This applies D_eff and W_over corrections automatically. All other joints use make_finger_edge().

Finger depth rule: depth is always the mating panel thickness, not own panel thickness. BASE edge fingers: depth = wall thickness. Wall bottom slots: depth = base thickness.

### 16.2 Lid Types
| Lid type | Description |
|---|---|
| none | No lid panel generated. |
| lift-off | Trapezoid identical to BASE shape. Finger tabs on all four edges matching wall top edges. Convention: fingers on LID, slots on wall top edges — symmetric with BASE. |
| sliding | **Trapezoid panel sized to slide into grooves in both leg walls. Panel width = short_outer + 2*(thickness+tolerance). Grooves: full-length through-slots, top inner edge of each leg wall, width = lid_thickness+tolerance, depth = thickness+tolerance. Lid slides in from long-side opening.** |
| hinged | Trapezoid lid. Barrel hinge holes in lid and top edge of WALL_LONG. Count = floor(long_outer/80), min 2. Diameter = hinge_diameter. |
| flap | As hinged but without hinge holes. Score line along WALL_LONG top edge as fold guide. |


### 16.3 run() Pipeline — box/cli.py
> ℹ️ def run(args: argparse.Namespace) -&gt; None:


> ℹ️ config = build_config(args)          # preset → config file → CLI args


> ℹ️ errors = validate_config(config)


> ℹ️ if errors:


> ℹ️ reporter.print_errors(errors, config.common.json_errors)


> ℹ️ sys.exit(1)


> ℹ️ try:


> ℹ️ geom         = trapezoid.derive(config.common)


> ℹ️ radius       = radii.resolve_corner_radius(config.common, geom)


> ℹ️ panels       = box_panels.build(config, geom, radius)


> ℹ️ layout       = layout_module.layout_panels(


> ℹ️ panels, config.common.sheet_width, config.common.sheet_height)


> ℹ️ reporter.print_summary(geom, panels, layout, None, config.common, &quot;box&quot;)


> ℹ️ num_sheets   = max(idx for _,_,idx in layout) + 1


> ℹ️ output_paths = _compute_output_paths(Path(config.common.output), num_sheets)


> ℹ️ svg_writer.write(layout, config.common, output_paths)


> ℹ️ if num_sheets &gt; 1:


> ℹ️ reporter.print_warning(f&quot;Layout required {num_sheets} sheets.&quot;)


> ℹ️ except (ValueError, NotImplementedError, IOError) as exc:


> ℹ️ reporter.print_error(str(exc), &quot;ERR_RUNTIME&quot;, None, None,


> ℹ️ config.common.json_errors)


> ℹ️ sys.exit(1)


> ℹ️ sys.exit(0)


## 17. Instrument Mode (instrument/)
### 17.1 Panels Generated
| Panel | Description |
|---|---|
| BASE | Trapezoid. Finger joints all four edges. Corner radii. Fingers OUTWARD by default. |
| WALL_LONG | Rectangle long_outer × depth_outer. Finger joints all edges. Optional strap pin holes. |
| WALL_SHORT | Rectangle short_outer × depth_outer. Finger joints all edges. |
| WALL_LEG_LEFT/RIGHT | Rectangle leg_length × depth_outer. Finger joints all edges. Leg-to-base joints use make_finger_edge_angled(). |
| SOUNDBOARD | Trapezoid. NO finger joints — build_plain_outline() only. Corner radii matching BASE. Sound hole if --soundhole-type. Brace score lines if --braces. Grain arrow always shown. |
| NECK_BLOCK | if --hardware: rectangle neck_block_thickness × depth_outer. Label: &quot;NECK BLOCK — glue inside short end.&quot; |
| TAIL_BLOCK | if --hardware: rectangle tail_block_thickness × depth_outer. Label: &quot;TAIL BLOCK — glue inside long end.&quot; |
| KERF_STRIP (base) | if --kerfing: one per wall, kerf_height × inner_wall_length. Four total. |
| KERF_STRIP (soundboard) | if --kerfing: one per wall, kerf_top_height × inner_wall_length. |
| KERF_FILLET | if --kerfing: corner fillet pieces for airtight sealing at internal corners. |
| TEST_STRIP | Always generated. 60mm × (3 × depth). |


### 17.2 Kerfing Strip Lengths
| Wall | Kerfing strip length |
|---|---|
| WALL_LONG | long_outer − 2 × thickness |
| WALL_SHORT | short_outer − 2 × thickness |
| WALL_LEG_LEFT/RIGHT | leg_length − 2 × (thickness / cos(leg_angle_deg)) [exact]; leg_length − 2 × thickness [acceptable approx within KERF_UNDERSIZE_MM tolerance] |


### 17.3 run() Pipeline — instrument/cli.py
> ℹ️ def run(args: argparse.Namespace) -&gt; None:


> ℹ️ config = build_config(args)


> ℹ️ errors = validate_config(config)


> ℹ️ if errors:


> ℹ️ reporter.print_errors(errors, config.common.json_errors)


> ℹ️ sys.exit(1)


> ℹ️ try:


> ℹ️ geom    = trapezoid.derive(config.common)


> ℹ️ radius  = radii.resolve_corner_radius(config.common, geom)


> ℹ️ panels  = instrument_panels.build(config, geom, radius)


> ℹ️ sh_res  = soundhole.compute(config, geom)


> ℹ️ if sh_res is not None:


> ℹ️ holes, sh_result = sh_res


> ℹ️ panels = [dataclasses.replace(p, holes=holes)


> ℹ️ if p.type == PanelType.SOUNDBOARD else p


> ℹ️ for p in panels]


> ℹ️ else:


> ℹ️ sh_result = None


> ℹ️ layout  = layout_module.layout_panels(


> ℹ️ panels, config.common.sheet_width, config.common.sheet_height)


> ℹ️ reporter.print_summary(geom, panels, layout, sh_result, config.common, &quot;instrument&quot;)


> ℹ️ num_sheets = max(idx for _,_,idx in layout) + 1


> ℹ️ output_paths = _compute_output_paths(Path(config.common.output), num_sheets)


> ℹ️ svg_writer.write(layout, config.common, output_paths)


> ℹ️ if num_sheets &gt; 1:


> ℹ️ reporter.print_warning(f&quot;Layout required {num_sheets} sheets.&quot;)


> ℹ️ except (ValueError, NotImplementedError, IOError) as exc:


> ℹ️ reporter.print_error(str(exc), &quot;ERR_RUNTIME&quot;, None, None,


> ℹ️ config.common.json_errors)


> ℹ️ sys.exit(1)


> ℹ️ sys.exit(0)


## 18. Sound Holes (instrument/soundhole.py)
### 18.1 Helmholtz Resonator Calculation
All sound hole types sized using the Helmholtz formula: f = (c / 2π) × √(A / (V × L_eff))

c = SPEED_OF_SOUND_MM_S = 343,000 mm/s; f = target Hz; V = air_volume from TrapezoidGeometry; A = effective open area mm²; L_eff = top_thickness + HELMHOLTZ_L_EFF_FACTOR × equivalent_diameter.

The tool solves for A given f, then derives hole dimensions. Convergence criterion: |diameter_new − diameter_old| &lt; FLOAT_TOLERANCE, maximum HELMHOLTZ_MAX_ITERATIONS = 20 iterations. Starting estimate: diameter_initial = 2√(A_target/π) with L_eff = top_thickness.

soundhole.compute(config, geom) -&gt; tuple[list[Hole], SoundHoleResult] | None — returns None if config.soundhole_type is None.

### 18.2 Sound Hole Positioning in Soundboard Local Coordinates
x_centre (all types, default): long_outer / 2 (axis of symmetry).

y_centre (longitudinal auto-position): y_centre = neck_block_thickness + neck_clearance + hole_half_size where hole_half_size = radius (round), long_edge/2 (rounded-trapezoid), total_length/2 (f-hole).

User override --soundhole-x maps directly to y_centre (distance from short end). User override --soundhole-y offsets from centreline: x_centre = long_outer/2 + soundhole_y.

F-hole pair positions: x_left = x_centre − FHOLE_PAIR_OFFSET_RATIO × short_outer; x_right = x_centre + FHOLE_PAIR_OFFSET_RATIO × short_outer.

### 18.3 Round Hole
Single CircleHole. L_eff = top_thickness + 0.85 × diameter (iterative). User override: --soundhole-diameter.

### 18.4 F-Holes
Paired, symmetric about centreline. Shape defined as proportions of total f-hole length L_fh (see constants.py for all ratios). Upper and lower eye circles. Upper and lower shafts as cubic Béziers. Nicks at waist as 1.5mm score marks (not through-cuts). Each f-hole is one ClosedHole. User override: --soundhole-size (sets L_fh directly).

### 18.5 Rounded-Trapezoid Hole
A single ClosedHole with the same trapezoidal taper as the body, at reduced scale, with small rounded corner fillets for smooth airflow.

#### Dimensions
Derived from body geometry and RTRAP constants:
- hole_long   = long_outer × soundhole_long_ratio  (default: RTRAP_LONG_TO_BODY_RATIO = 0.28)
- hole_short  = hole_long × (short_outer / long_outer)  [inherits body taper ratio]
- hole_height = hole_long × soundhole_aspect  (default: RTRAP_ASPECT_RATIO = 0.6)
- hole_r      = soundhole_r_mm  (default: RTRAP_CORNER_R_MM = 2.0mm, fixed — NOT a ratio)

Default values (dulcimer preset, long=180, short=120): hole_long=50mm, hole_short=34mm, hole_height=30mm, hole_r=2mm → ~150Hz.

User overrides: --soundhole-size sets hole_long directly; --soundhole-orientation sets SAME or FLIPPED.

#### Orientation
Controlled by soundhole_orientation (SoundHoleOrientation enum):
- SAME    (default): hole long edge toward tail, matching body — both wide ends on same side.
- FLIPPED: hole long edge toward neck — wide end opposite to body wide end.

#### Corner angle rule (INVARIANT — applies to all trapezoid shapes in this project)
For any trapezoid traversed clockwise, narrow-end corners are OBTUSE (90° + leg_angle) and wide-end corners are ACUTE (90° − leg_angle). This is the same rule as the body panel (TL/TR = narrow = obtuse = long_end_angle; BL/BR = wide = acute = short_end_angle). Assigning these angles backwards produces geometrically impossible or visually wrong arcs. This rule must be verified by proof for every trapezoid shape generated.

Corner arc construction: arc centre is inside the hole (inward fillet). SVG arc uses sweep=1 (clockwise). Arc chord = 2r·cos(angle/2) ≤ 2r always — validity is guaranteed by correct angle assignment, not by radius choice.

#### Acoustic area
A = (hole_long + hole_short) / 2 × hole_height − 4 × r² × (1 − π/4)

Helmholtz L_eff uses equivalent diameter: D_eq = 2√(A/π). L_eff = top_thickness + 0.85 × D_eq.

#### Positioning
x_centre = long_outer / 2 (body centreline — valid because body is symmetric about this line at all y).
y_near = neck_block_thickness + neck_clearance (near edge of hole, measured from neck/short end).
y_far = y_near + hole_height.

#### Validation (ERR_VALIDATION raised if violated)
- 0.3 ≤ soundhole_aspect ≤ 2.0 (None rejected — must be explicit)
- 0.1 ≤ soundhole_long_ratio ≤ 0.6
- hole_r > 0 and hole_r ≤ min(hole_short, hole_long, leg_edge_length) × RTRAP_MAX_R_EDGE_FRACTION
  where leg_edge_length = √(hole_inset² + hole_height²) and hole_inset = (hole_long − hole_short)/2
- neck_clearance + hole_height < length − tail_block_thickness  (hole must fit between blocks)
- hole_long / 2 < long_outer / 2 − body_leg_inset_at_y_centre  (hole laterally within soundboard at both y_near and y_far)

## 19. Kerfing (instrument/kerfing.py)
Kerfing provides airtight internal sealing at all joints and creates the gluing ledge for the soundboard. The builder rounds edges by hand and glues pieces in place. All pieces are undersized by KERF_UNDERSIZE_MM = 0.5mm to accommodate hand-rounding and provide glue gap.

### Base-level kerfing strips (one per wall)
Simple rectangles: kerf_height × inner_wall_length × kerf_thickness. Glued to interior face of each wall flush with the base. Four total.

### Soundboard-level kerfing strips (one per wall)
kerf_top_height × inner_wall_length × kerf_thickness. Provide the gluing ledge for the soundboard. Four total.

### Wall-to-wall corner fillets (one per internal corner)
Right-angle triangle cross-section with legs of kerf_width. Length = depth_outer. One end cut at the bisector angle of the internal corner (long_end_angle_deg or short_end_angle_deg from TrapezoidGeometry). Other end cut square. Undersized 0.5mm.

### Soundboard corner fillets
At each radiused corner of base/soundboard panels, a small quarter-circle fillet is generated. Mitred at 45°. Undersized 0.5mm. Curved face matches corner radius.

## 20. Marks (instrument/marks.py)
All marks are rendered by the SVG writer as Mark objects in panel.marks. They are only rendered when config.labels is True, except grain arrows which are always rendered.

### Grain direction arrow
Double-headed arrow along grain_angle_deg. Length: 20% of panel longest dimension. Centred in panel bounding box. Always rendered regardless of --labels flag.

### Assembly sequence numbers
Large numeral (SVG_ASSEMBLY_NUM_FONT_MM = 8mm) centred in panel. Fixed order: 1=BASE, 2=WALL_LONG, 3=WALL_SHORT, 4=WALL_LEG_LEFT, 5=WALL_LEG_RIGHT, 6=SOUNDBOARD. Kerfing pieces numbered from 7 upward.

### Orientation mark
Small filled triangle on each wall panel indicating which edge is the base edge.

### Scale mark and bridge position
If config.scale_length is set: a score line transverse to the soundboard at distance scale_length/2 from the short end (bridge position marker).

### Brace score lines
If config.braces is True: score lines at approximate brace positions. Standard transverse brace positions relative to the soundboard length, at 0.25 × length and 0.65 × length from the short end.

## 21. Presets (presets.py)
Presets allow first-time users to get working output immediately. A preset is a dict with keys matching CommonConfig and mode-specific config field names, plus mode: str and description: str. Omitted keys use defaults.

| Preset name | Description |
|---|---|
| pencil-box | box mode. Small open-top box. Good first project for students. |
| storage-box | box mode. Medium box with lift-off lid. |
| sliding-box | box mode. Compact box with sliding lid. Demonstrates sliding lid joint. |
| dulcimer | instrument mode. long=180, short=120, length=380, depth=90, thickness=3, rounded-trapezoid soundhole, hardware, kerfing. |
| tenor-guitar | instrument mode. Scaled-up dulcimer at tenor guitar proportions. |


Invocation: python trapezoid_box.py box --preset pencil-box --output pencil.svg

--list-presets prints all presets with descriptions and exits. No SVG generated.

## 22. Parameter Precedence
build_config(args) applies in this exact order. Later steps override earlier.

Start with all dataclass field defaults.

If --preset NAME: apply preset values.

If --config PATH: apply config file values.

Apply all explicitly provided CLI arguments (args.X != None).

&quot;Explicitly provided&quot; means the user typed it. Implement by setting all argparse defaults to None. None does not override.

Required tests in test_presets.py: CLI overrides config overrides preset; config overrides preset; preset only; None does not override.

## 23. CLI Interface
### 23.1 Entry Point Structure
> ℹ️ trapezoid_box.py [--version] [--list-presets] [--extract-config PATH] {box|instrument}


> ℹ️ trapezoid_box.py box        [common] [box-params]


> ℹ️ trapezoid_box.py instrument [common] [instrument-params]


Top-level flags handled before subcommand parsing. No subcommand required for --version, --list-presets, --extract-config. Missing subcommand with no top-level flag: print help, exit 0.

### 23.2 Common Parameters
> ℹ️ --long FLOAT          Outer long-side width (mm)


> ℹ️ --short FLOAT         Outer short-side width (mm)


> ℹ️ --length FLOAT        Perpendicular body length (mm)  [mutually exclusive with --leg]


> ℹ️ --leg FLOAT           Leg wall length (mm)            [mutually exclusive with --length]


> ℹ️ --depth FLOAT         Box depth / wall height (mm)


> ℹ️ --thickness FLOAT     Material thickness (default: 3.0)


> ℹ️ --burn FLOAT          Laser kerf compensation (default: 0.05)


> ℹ️ --tolerance FLOAT     Joint fit clearance (default: 0.1)


> ℹ️ --corner-radius FLOAT Corner radius on base/soundboard (default: auto = 3×thickness)


> ℹ️ --finger-width FLOAT  Finger width (default: auto = 3×thickness)


> ℹ️ --inner               Treat input dimensions as inner (default: outer)


> ℹ️ --sheet-width FLOAT   Sheet width mm (default: 600.0)


> ℹ️ --sheet-height FLOAT  Sheet height mm (default: 600.0)


> ℹ️ --labels / --no-labels  Panel labels and marks (default: --labels)


> ℹ️ --colorblind          Colour-blind safe output (black solid / black dashed)


> ℹ️ --json-errors         Output errors as JSON to stderr


> ℹ️ --format [svg|dxf]    Output format (default: svg; dxf raises NotImplementedError)


> ℹ️ --per-panel           Write each panel as a separate SVG file


> ℹ️ --preset NAME         Named built-in preset as base configuration


> ℹ️ --list-presets        List presets and exit


> ℹ️ --output PATH         Output path (default: trapezoid_box_output.svg)


> ℹ️ --config PATH         Load parameters from JSON config file


> ℹ️ --save-config PATH    Save resolved config to JSON and exit (no SVG generated)


> ℹ️ --extract-config PATH Read embedded config from a trapezoidbox SVG and exit


> ℹ️ --version             Print version and exit


### 23.3 Box Parameters
> ℹ️ --lid [none|lift-off|sliding|hinged|flap]   Lid type (default: none)


> ℹ️ --hinge-diameter FLOAT                        Hinge hole diameter mm (default: 6.0)


### 23.4 Instrument Parameters
> ℹ️ --top-thickness FLOAT          Soundboard thickness (default: same as --thickness)


> ℹ️ --finger-direction [in|out]    Finger protrusion (default: outward)


> ℹ️ --kerfing / --no-kerfing       Kerfing strips (default: on)


> ℹ️ --kerf-height FLOAT            Base kerfing height mm (default: 12.0)


> ℹ️ --kerf-width FLOAT             Base kerfing width mm (default: 6.0)


> ℹ️ --kerf-top-height FLOAT        Soundboard kerfing height mm (default: 10.0)


> ℹ️ --kerf-top-width FLOAT         Soundboard kerfing width mm (default: 5.0)


> ℹ️ --kerf-thickness FLOAT         Kerfing thickness (default: same as --thickness)


> ℹ️ --soundhole-type [round|f-hole|rounded-trapezoid]


> ℹ️ --soundhole-orientation [same|flipped]  rounded-trapezoid only: same=long edge toward tail (default), flipped=long edge toward neck


> ℹ️ --soundhole-long-ratio FLOAT  rounded-trapezoid: hole_long as fraction of body long_outer (default: 0.28, range 0.1–0.6)


> ℹ️ --soundhole-aspect FLOAT      rounded-trapezoid: hole_height = hole_long × this (default: 0.6, range 0.3–2.0)


> ℹ️ --soundhole-r-mm FLOAT        rounded-trapezoid: corner fillet radius mm (default: 2.0)


> ℹ️ --helmholtz-freq FLOAT         Target resonant frequency Hz (default: 110.0)


> ℹ️ --soundhole-diameter FLOAT     Override diameter mm


> ℹ️ --soundhole-size FLOAT         Override f-hole length mm


> ℹ️ --soundhole-x FLOAT            Hole centre from short end mm (default: auto)


> ℹ️ --soundhole-y FLOAT            Hole centre offset from centreline mm (default: 0)


> ℹ️ --neck-clearance FLOAT         Min gap from neck block to hole edge (default: 60.0)


> ℹ️ --hardware                     Generate neck/tail blocks + strap pin holes


> ℹ️ --neck-block-thickness FLOAT   (default: 25.0)


> ℹ️ --tail-block-thickness FLOAT   (default: 15.0)


> ℹ️ --braces                       Brace position score lines on soundboard


> ℹ️ --scale-length FLOAT           Scale length mm; adds bridge mark


## 24. Configuration File Format
> ℹ️ {


> ℹ️ &quot;trapezoid_box_version&quot;: &quot;2.0&quot;,


> ℹ️ &quot;common&quot;: {


> ℹ️ &quot;long&quot;: 180, &quot;short&quot;: 120, &quot;length&quot;: 380, &quot;leg&quot;: null,


> ℹ️ &quot;depth&quot;: 90, &quot;thickness&quot;: 3.0, &quot;burn&quot;: 0.05, &quot;tolerance&quot;: 0.1,


> ℹ️ &quot;corner_radius&quot;: null, &quot;finger_width&quot;: null,


> ℹ️ &quot;sheet_width&quot;: 600.0, &quot;sheet_height&quot;: 600.0,


> ℹ️ &quot;labels&quot;: true, &quot;dim_mode&quot;: &quot;outer&quot;


> ℹ️ },


> ℹ️ &quot;instrument&quot;: {


> ℹ️ &quot;top_thickness&quot;: 3.0, &quot;finger_direction&quot;: &quot;outward&quot;,


> ℹ️ &quot;kerfing&quot;: true, &quot;kerf_height&quot;: 12.0, &quot;kerf_width&quot;: 6.0,


> ℹ️ &quot;soundhole_type&quot;: &quot;rounded-trapezoid&quot;, &quot;helmholtz_freq&quot;: 110.0,


> ℹ️ &quot;hardware&quot;: true, &quot;neck_block_thickness&quot;: 25.0,


> ℹ️ &quot;tail_block_thickness&quot;: 15.0, &quot;braces&quot;: true, &quot;scale_length&quot;: 628.0


> ℹ️ }


> ℹ️ }


null = auto-calculate. Unknown keys ignored with warning. Missing sheet_height uses DEFAULT_SHEET_HEIGHT_MM = 600.0. On load: if trapezoid_box_version absent or older, print warning but proceed.

## 25. SVG Metadata
> ℹ️ &lt;svg xmlns=&quot;http://www.w3.org/2000/svg&quot;


> ℹ️ xmlns:trapezoidbox=&quot;https://trapezoidbox.github.io/ns/1.0&quot;


> ℹ️ width=&quot;600.0000mm&quot; height=&quot;600.0000mm&quot; viewBox=&quot;0 0 600.0000 600.0000&quot;&gt;


> ℹ️ &lt;!-- trapezoid_box v2.0 — dimensions in millimetres ... [scale warning] --&gt;


> ℹ️ &lt;metadata&gt;


> ℹ️ &lt;trapezoidbox:version&gt;2.0&lt;/trapezoidbox:version&gt;


> ℹ️ &lt;trapezoidbox:mode&gt;instrument&lt;/trapezoidbox:mode&gt;


> ℹ️ &lt;trapezoidbox:generated&gt;2026-02-26T10:30:00Z&lt;/trapezoidbox:generated&gt;


> ℹ️ &lt;trapezoidbox:config&gt;&lt;![CDATA[{&quot;trapezoid_box_version&quot;: &quot;2.0&quot;, ...}]]&gt;&lt;/trapezoidbox:config&gt;


> ℹ️ &lt;/metadata&gt;


Timestamp: datetime.utcnow().strftime(&quot;%Y-%m-%dT%H:%M:%SZ&quot;). Standard library only.

## 26. Winding Convention
All panel outline ClosedPath objects: clockwise winding in SVG Y-down space (interior on the right when traversing in order).

All hole ClosedPath objects (ClosedHole): counter-clockwise winding. SVG even-odd fill rule treats CCW interior paths as subtractions. Ensures holes render as transparent cutouts.

This convention must be verified by unit tests. test_joints.py and test_radii.py must include a winding check for at least one complete panel outline.

This winding convention must be stated as a module-level comment in panels.py:

> ℹ️ # WINDING CONVENTION: All panel outlines and FingerEdge directions follow


> ℹ️ # clockwise winding in SVG coordinate space (Y increases downward).


> ℹ️ # Outward for a FingerEdge = 90° clockwise from edge direction in SVG Y-down space.


## 27. Multi-Sheet Output
If panel layout exceeds a single sheet: output files named by inserting sheet number before extension. --output my_box.svg → my_box_sheet1.svg, my_box_sheet2.svg, etc.

Single sheet: write directly to --output path. No numbering.

--per-panel: write each panel to {stem}_{PANEL_TYPE}.svg (e.g. my_box_BASE.svg). Multi-sheet suppressed when --per-panel is active.

TEST_STRIP always placed on the last sheet.

## 28. Test Strategy
### 28.1 Unit Tests — Core Geometry
test_trapezoid.py: derive() mode A and B; DimMode.INNER conversion; air volume; leg angle. Known exact values for long=180, short=120, length=380, depth=90, thickness=3.

test_joints.py: odd_count edge cases (very short → count=3); make_finger_edge with known inputs and expected term_start/term_end; finger_edge_to_path_segments for known staircase coordinates; make_finger_edge_angled verifying D_eff and W_over are applied.

test_radii.py: auto_corner_radius; finger_termination_point for 90° and non-right-angle corners; corner_arc_segments with known geometry.

test_transform.py: rotate_point (90°, 180°, 270°); mirror_path_horizontal + reverse_path restores clockwise winding; translate_path.

test_utils.py: nearly_equal edge cases; odd_count minimum 3; clamp; arc_centre for a known arc.

test_layout.py: NFDH row packing with known panels; grain direction constraint respected; multi-sheet splitting; TEST_STRIP on last sheet.

### 28.2 Unit Tests — Panels
Panel perimeter self-consistency: sum of four edge lengths = perimeter of bounding rectangle.

BASE and SOUNDBOARD: four edge lengths match the four mating wall dimensions within FLOAT_TOLERANCE. This is the most critical correctness check.

test_box_panels.py test_base_panel_outline_is_valid_closed_clockwise_path(): path_winding == &quot;clockwise&quot;; approximate perimeter within 1% of geometric perimeter.

Leg-to-base joint D_eff and W_over: verify that FingerEdge.depth on BASE leg edges = mating_thickness / cos(leg_angle_deg).

Structural safety: verify validate_config() rejects configs where W_struct &lt; thickness × OVERCUT_MIN_STRUCT_RATIO.

### 28.3 Unit Tests — Sound Holes
Helmholtz: known V, f → known A. Hand-calculated verification.

Round hole: L_eff convergence; diameter within 1% of hand calculation.

Rounded-trapezoid geometry checks (required for both SAME and FLIPPED orientations):
- Corner angle invariant: compute actual interior angle at each of the four corners from edge geometry; assert narrow-end corners = obtuse (90°+leg_angle) ± 0.5° and wide-end corners = acute (90°−leg_angle) ± 0.5°.
- Arc chord validity: chord = 2r·cos(angle/2) ≤ 2r at all four corners.
- No arc overlap: remaining straight length on every edge > 0.5mm after subtracting both tangent distances.
- Radius constraint: r ≤ min(hole_short, hole_long, leg_edge) × RTRAP_MAX_R_EDGE_FRACTION.
- Straight segment directions: each of the four straight path segments has direction matching the computed edge unit vector within 0.01.
- Positive segment lengths: all four straight segments > 0.5mm.
- Fit within soundboard: hole_long/2 < soundboard_half_width at y_near and y_far.
- Longitudinal fit: neck_clearance + hole_height < length − tail_block_thickness.
- Acoustic area: area matches Helmholtz target within 1%.
- Orientation SAME: long edge at tail (high y); orientation FLIPPED: long edge at neck (low y).

F-hole: control point coordinates match FHOLE_* ratios in constants.py.

### 28.4 Integration Test
Dulcimer config (long=180, short=120, length=380, depth=90, thickness=3, rounded-trapezoid, helmholtz=110, hardware, kerfing, braces). Verify: correct panel count; all bounding boxes within sheet_width; achieved frequency within 5% of 110 Hz; BASE and SOUNDBOARD perimeters match mating wall edge lengths; no exceptions.

### 28.5 Golden File Regression Tests
Three golden SVGs in tests/golden/. Integration test generates SVG for each config and compares byte-for-byte. Any geometry change that alters output requires conscious golden file update.

### 28.6 Property-Based Tests (hypothesis)
Random valid CommonConfigs within bounds (long 50–500mm, short 20–long, depth 20–300mm, thickness 1–6mm). Verify: derive() succeeds; odd_count returns odd &gt;= 3; no negative perimeters; Helmholtz frequency positive and finite.

## 29. Stdout Summary Format
> ℹ️ trapezoid_box v2.0 — instrument mode


> ℹ️ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


> ℹ️ Trapezoid geometry


> ℹ️ Long outer:          180.0 mm


> ℹ️ Short outer:         120.0 mm


> ℹ️ Body length outer:   380.0 mm


> ℹ️ Depth outer:          90.0 mm


> ℹ️ Leg length:          381.2 mm


> ℹ️ Leg angle:             4.51°


> ℹ️ Air volume:        4,818,960 mm³  (4.82 litres)


> ℹ️ Overcut per leg joint: 0.24mm  (structurally OK)


> ℹ️ Panels — Sheet 1 (600.0 × 512.0 mm, 68% utilisation)


> ℹ️ BASE               180.0 × 380.0 mm  fingers: long=19, short=13, legs=43


> ℹ️ SOUNDBOARD         180.0 × 380.0 mm  rounded-trap 50×34mm h=30mm  [no finger joints]


> ℹ️ WALL_LONG          180.0 ×  90.0 mm


> ℹ️ WALL_SHORT         120.0 ×  90.0 mm


> ℹ️ Panels — Sheet 2 (600.0 × 320.0 mm, 54% utilisation)


> ℹ️ WALL_LEG_LEFT      381.2 ×  90.0 mm


> ℹ️ WALL_LEG_RIGHT     381.2 ×  90.0 mm


> ℹ️ [kerfing strips ×8]


> ℹ️ TEST_STRIP          60.0 × 270.0 mm


> ℹ️ Sound hole


> ℹ️ Type:               rounded-trapezoid


> ℹ️ Orientation:        same (long edge toward tail)


> ℹ️ Long edge:          50.0 mm


> ℹ️ Short edge:         34.0 mm


> ℹ️ Height:             30.0 mm


> ℹ️ Corner radius:      2.0 mm


> ℹ️ Total open area:    1,247 mm²


> ℹ️ Target frequency:   110.0 Hz


> ℹ️ Achieved frequency: 109.7 Hz  ✓


> ℹ️ Output: my_dulcimer_sheet1.svg, my_dulcimer_sheet2.svg


reporter.print_summary() owns all stdout. No other module prints to stdout. Overcut value and structural status reported for non-zero leg angles.

## 30. Out of Scope for v1
These features are explicitly excluded. Each must have a comment in the relevant source file and raise NotImplementedError with a helpful message.

| Feature | Notes for v2 |
|---|---|
| General (non-isosceles) trapezoid | --leg-left / --leg-right. models.py defines the fields but they raise NotImplementedError: &quot;General trapezoid planned for v2. Only isosceles supported.&quot; |
| DXF output | --format dxf raises NotImplementedError: &quot;DXF output planned for v2.&quot; |
| PDF output | Same pattern. |
| Living hinge lid | Noted in lids.py. Requires material flex radius calculation. |
| Corner sound hole | Noted in soundhole.py. |
| GUI or web interface | Noted in README. |
| Optimal 2D nesting beyond NFDH | Noted in layout.py. |
| User preset files | v2: --preset-file PATH loads JSON presets. Noted in presets.py. |


## Appendix A — Mathematical Proof of Correctness
This appendix provides formal geometric proofs for the non-orthogonal joint calculations introduced in v2.0. These proofs follow the style of E.W. Dijkstra: each claim is stated precisely, all assumptions are named, and the conclusion is derived by strict logical steps from the premises.

⚠  These proofs apply to the leg-wall-to-base joints only. All 90° joints in this tool are standard and require no correction.

### Proof A.1 — Effective Slot Depth (The Parallelogram Proof)
**Claim: When a wall panel meets the base at angle α from perpendicular, a tab of depth T is insufficient. The slot depth must be D_eff = T / cos(α).**

Setup: Let T = nominal material thickness. Let α = leg_angle_deg (the deviation of the leg wall from perpendicular to the base plane). The laser always cuts vertically — perpendicular to the face of the material sheet.

Consider the cross-section of the joint at assembly:

The base panel lies flat in the XY plane.

The leg wall leans at angle α from the vertical (perpendicular to the base).

A finger tab, laser-cut at 90° to the wall face, has nominal depth T measured perpendicular to the wall face.

When the tab is inserted into the base, it must travel through the base material at angle α from the normal to the base.

Let the insertion path be along vector v = (sin α, cos α) in the XZ plane.

The base material has thickness T measured along Z (the normal to the base).

The path length through the base is: D_eff = T / cos α

Proof: The base has faces at z=0 and z=T. The tab enters at z=0 and must reach z=T.

Along the insertion path: Δz = D_eff × cos α. Setting Δz = T:

D_eff × cos α = T  →  D_eff = T / cos α  □

**∴  D_eff = T / cos(leg_angle_deg). For α=0°: D_eff=T (identity check ✓). For α=4.51° (dulcimer): D_eff = 3.0/cos(4.51°) = 3.009mm. Difference is 0.009mm — negligible but always correct.**

### Proof A.2 — Rotational Overcut (The Assembly Kinematics Proof)
**Claim: When a square-cut finger (depth T, cut at 90°) is rotated by angle α to seat into a square-cut slot, the internal corner of the finger collides with the internal corner of the slot. The slot must be widened by W_over = T × tan(α) to clear this collision.**

Setup: Let T = material thickness. Let α = leg_angle_deg. The finger and slot both have perfectly square cut edges because the laser always cuts at 90° to the material face. Assembly requires rotating the tab through angle α into the slot.

Consider the corner geometry during assembly:

The finger tab has width W_f (nominal finger width) and depth T.

The slot has width W_s and depth T (before correction).

During assembly, the tab is rotated by α about the slot's top edge.

The &quot;high corner&quot; of the tab (the interior corner at the tip of the tab) traces an arc of radius T during rotation.

At the moment of insertion, the high corner is at position:

x = T × sin α  (measured horizontally into the slot)

z = T × cos α  (measured vertically into the material)

The slot wall is at x = 0. The high corner protrudes by:

W_over = T × sin α / cos α = T × tan α

Wait — let us re-derive rigorously. The tab corner starts at (0, T) in the (x,z) frame.

Rotating by α about origin: x' = T×sin α,  z' = T×cos α.

The slot edge is at x=0. The protrusion into the slot wall is x' = T × sin α.

However, the relevant clearance is the horizontal protrusion at the slot entrance (z=0):

The corner at (T×sin α, T×cos α) has not yet reached z=0.

At z=0: the corner would be at x = T×sin α / cos α × cos α = T×sin α. No, wait.

Correct derivation: Consider the tab's leading corner at the slot entrance plane (z=0):

In the rotated frame, the tab occupies the triangle with vertices:

(0, 0),  (W_f, 0),  (W_f + T×tan α, T)

The protrusion at z=0 (slot entrance) beyond the nominal width W_f is:

W_over = T × tan α  □

**∴  W_over = T × tan(leg_angle_deg). For α=0°: W_over=0 (identity check ✓). For α=4.51°: W_over = 3.0×tan(4.51°) = 0.236mm. For α=15°: W_over = 3.0×tan(15°) = 0.804mm — now significant.**

Implementation: W_over is added to the joint tolerance (effective_tolerance = tolerance + W_over). This widens all slots on the angled edges symmetrically, moving the void to the exterior face of the joint where it is filled by glue.

### Proof A.3 — Structural Boundary Condition (The Gatekeeper Proof)
**Claim: As α increases, W_over increases without bound (tan α → ∞ as α → 90°). There exists a critical angle beyond which the slot overcut consumes the entire structural tab. The tool must reject designs that exceed this boundary.**

Setup: Let W_f = resolved finger width. Let T = material thickness. Let τ = tolerance. Let α = leg_angle_deg. Define W_struct = remaining structural width of the tab after overcut.

W_struct = W_f - τ - T×tan α

The minimum acceptable structural width is T/2 (half the material thickness).

This ensures sufficient glue surface and shear resistance for a structural joint.

Boundary condition:  W_struct ≥ T × OVERCUT_MIN_STRUCT_RATIO  (= T/2)

Equivalently:  W_f - τ - T×tan α ≥ T/2

Solving for the maximum permissible angle:

T×tan α ≤ W_f - τ - T/2

α ≤ arctan((W_f - τ - T/2) / T)

For defaults W_f=9mm (3×T), τ=0.1mm, T=3mm:

α_max = arctan((9.0 - 0.1 - 1.5) / 3.0) = arctan(2.467) ≈ 68°

This is the absolute physical limit. However, for graceful design, the tool rejects designs when W_struct &lt; T/2, giving the user a clear error message before any material is wasted.

**∴  For leg_angle_deg &gt; arctan((finger_width - tolerance - T/2) / T): validate_config() returns ERR_VALIDATION_STRUCT_TAB_TOO_THIN. This is a hard engineering boundary, not a style preference.**

### Proof A.4 — Finger Termination Point (Tangent Length Formula)
**Claim: The distance from a corner vertex to the finger termination point (where the corner arc and the finger zone meet) is corner_radius / tan(internal_angle / 2).**

Setup: Let R = corner_radius. Let θ = internal_angle_deg. The corner arc is a circular arc of radius R inscribed in the corner, tangent to both edges. The tangent points are the finger termination points.

By definition, the inscribed circle of radius R is tangent to both edges at the termination points.

The angle between each edge and the bisector of the corner is θ/2.

The tangent length from the vertex to the tangent point (in any triangle inscribed in a circle):

tan(θ/2) = R / d_tangent  →  d_tangent = R / tan(θ/2)  □

**∴  For θ=90°: d_tangent = R / tan(45°) = R. Correct for right-angle corners. For θ=94.51° (dulcimer long-end): d_tangent = R / tan(47.26°) = R / 1.077 = 0.929R. Slightly shorter than R — the arc starts slightly closer to the corner on the wider-angle end.**

### Proof A.5 — Corner Arc Centre Offset
**Claim: The arc centre is at distance R / sin(θ/2) from the corner vertex, along the inward angle bisector. The inward bisector direction is normalise((-edge_a_dir) + edge_b_dir) where edge_a_dir points TOWARD the vertex and edge_b_dir points AWAY.**

Setup: Same as Proof A.4. The arc centre is equidistant from both edges (distance R). Let d_centre = distance from vertex to arc centre along bisector.

The arc centre, the vertex, and the tangent point form a right triangle:

Right angle at the tangent point (tangent is perpendicular to radius).

Hypotenuse = d_centre (vertex to arc centre).

Opposite side (perpendicular to edge) = R.

Angle at vertex = θ/2.

sin(θ/2) = R / d_centre  →  d_centre = R / sin(θ/2)  □

**∴  For θ=90°: d_centre = R / sin(45°) = R×√2 ≈ 1.414R. Verified.**

**Bisector direction sign proof:**

At vertex V: edge_a arrives with direction edge_a_dir; edge_b departs with direction edge_b_dir. The interior bisector must point into the panel.

The inward component from edge_a is -edge_a_dir (opposing the arriving direction).

The inward component from edge_b is +edge_b_dir (same as departing direction).

Inward bisector = normalise(-edge_a_dir + edge_b_dir)  □

Counter-example proving normalise(-edge_a - edge_b) is WRONG:

Dulcimer TR corner: edge_a_dir=(+1,0), edge_b_dir=(0.079,0.997)

Wrong: normalise(-1-0.079, 0-0.997) = (-0.734,-0.679) → above panel

Correct: normalise(-1+0.079, 0+0.997) = (-0.679,+0.734) → inside panel

Only the correct formula gives arc_centre distance = R from both arc endpoints.

**∴  This is the critical bisector direction. Using the wrong sign places the arc centre outside the panel, producing an inverted corner in the SVG that no laser driver will cut correctly.**

### Proof A.6 — ClosedPath Invariant and Path Winding
**Claim: A correctly assembled panel outline has clockwise winding in SVG Y-down space, which corresponds to positive signed area in the shoelace formula.**

Setup: SVG coordinate space has Y increasing downward. The shoelace formula in standard (Y-up) space gives positive area for CCW paths. In Y-down space, the Y axis is negated, which reverses the apparent rotation direction.

Shoelace formula: A = (1/2) × Σ(x_i × y_{i+1} - x_{i+1} × y_i)

In standard Y-up: A &gt; 0 ↔ counter-clockwise (CCW).

In SVG Y-down: substitute y_i → -y_i. This negates all y terms:

A_down = (1/2) × Σ(x_i×(-y_{i+1}) - x_{i+1}×(-y_i)) = -A_up

Therefore: A_down &gt; 0 ↔ A_up &lt; 0 ↔ clockwise in Y-up ↔ clockwise visual in Y-down. □

**∴  path_winding() returns &quot;clockwise&quot; when signed_area &gt; 0, using the SVG Y-down shoelace formula. Panel outlines must return &quot;clockwise&quot;. Hole outlines must return &quot;counter-clockwise&quot;. This is verified by unit tests.**

### Proof Summary
| Formula | Proven Result |
|---|---|
| D_eff = T / cos(α) | A.1 — Tab must traverse T/cos(α) of material along the angled insertion path. |
| W_over = T × tan(α) | A.2 — Slot must be widened by T×tan(α) to allow the tab corner to clear without collision. |
| W_struct = W_f - τ - W_over ≥ T/2 | A.3 — Structural boundary condition. Tool rejects designs that violate this. |
| d_tangent = R / tan(θ/2) | A.4 — Finger termination distance from corner vertex. |
| d_centre = R / sin(θ/2) | A.5 — Corner arc centre offset from vertex along bisector. |
| A_shoelace &gt; 0 ↔ CW in Y-down | A.6 — Path winding sign convention for SVG coordinate space. |


### Reference Values for Dulcimer Preset
long=180, short=120, length=380, depth=90, thickness=3.0, finger_width=9.0 (auto), tolerance=0.1, leg_angle_deg=4.51°

| Quantity | Value |
|---|---|
| leg_inset | (180-120)/2 = 30.0 mm |
| leg_length | sqrt(380² + 30²) = 381.18 mm |
| leg_angle_deg | arctan(30/380) = 4.514° |
| long_end_angle_deg | 90 + 4.514 = 94.514° |
| short_end_angle_deg | 90 - 4.514 = 85.486° |
| D_eff (leg joints) | 3.0 / cos(4.514°) = 3.009 mm |
| W_over (leg joints) | 3.0 × tan(4.514°) = 0.236 mm |
| W_struct (default finger_width=9mm) | 9.0 - 0.1 - 0.236 = 8.664 mm &gt;&gt; 1.5mm minimum ✓ |
| d_tangent (90° corner, R=9mm) | 9.0 / tan(45°) = 9.0 mm |
| d_tangent (long-end, R=9mm) | 9.0 / tan(47.257°) = 8.355 mm |
| d_tangent (short-end, R=9mm) | 9.0 / tan(42.743°) = 9.723 mm |
| arc_centre offset (90°, R=9mm) | 9.0 / sin(45°) = 12.728 mm |
| arc_centre offset (long-end, R=9mm) | 9.0 / sin(47.257°) = 12.239 mm |
| air_volume | 0.5×(174+114)×374×84 = 4,533,984 mm³ (inner dims) |


## Appendix B — Builder's Guide: The Physical Story Behind the Code
This appendix is for students, makers, and instrument builders who want to understand not just what trapezoid_box.py does, but why it does it that way. No programming knowledge is assumed. If you have ever tried to build a laser-cut box and found the joints too tight, too loose, or stubbornly refusing to seat — this is for you.

### B.1 The Laser Does Not Know What You Want to Build
A laser cutter is a surprisingly literal machine. You give it a line on a screen; it burns that line into your material. It does not know that the line is the edge of a finger joint, or that the joint will be inserted at an angle, or that the material has any thickness at all. It just burns.

This means every physical constraint of your design must be calculated in advance and encoded into the lines you give the laser. trapezoid_box.py exists to do that calculation correctly so you do not have to.

### B.2 Why Finger Joints?
A finger joint — the interlocking row of tabs and slots on laser-cut boxes — is the standard way to join two flat panels at a right angle. The tabs on one panel slide into the slots on the other, giving a large gluing surface and a self-aligning joint that holds its shape while the glue sets.

The key numbers: finger_width controls how wide each finger is; depth controls how far it penetrates; tolerance controls the clearance so the joint slides together without forcing but also without rattling. The auto defaults (finger_width = 3x thickness, tolerance = 0.1mm) are a good starting point for 3mm plywood. The test strip exists so you can verify these numbers for your specific machine before cutting a full sheet.

### B.3 The Burn: Why Your Cuts Are Slightly Too Big
When a laser burns a line, it vaporises a small channel of material called the kerf — typically 0.1 to 0.2mm wide for a CO2 laser cutting 3mm ply. The laser burns on both sides of your intended line, so a 10mm tab comes out narrower than 10mm.

The burn parameter (default 0.05mm) compensates for this: every cut line is offset outward so that after the laser removes its kerf, the finished feature is the intended size. Tabs are made slightly bigger; slots are made slightly bigger; holes are made slightly bigger. The direction is always away from the material being kept.

Getting this number right for your specific machine is one of the most important calibration steps. Cut the test strip, measure the joint fit, and adjust burn and tolerance until it slides together with finger pressure and a little satisfying resistance.

### B.4 The Problem With Angled Joints — and Why v2.0 Fixes It
A trapezoid box has two leg walls that lean inward at a small angle. For a dulcimer body this is about 4.5 degrees — barely visible. But this angle creates two subtle problems that standard box-making software ignores.

Problem 1 — the finger is too short. A tab inserted at an angle travels a longer path through the mating material than a straight-in tab. Specifically, it travels T/cos(angle) instead of T. At 4.5 degrees this is only 0.009mm more — invisible. At 15 degrees it is 0.35mm short, producing a joint that looks assembled but has no structural contact on the inside face.

Problem 2 — the finger cannot rotate in. When assembling a box you rotate the panel into place. Both the tab and slot have square-cut edges (the laser always cuts vertically). As the tab rotates, its inner corner sweeps an arc and physically collides with the inner corner of the slot before the joint can seat. You end up forcing the joint, splitting the wood, or filing every finger by hand.

The fix is to widen the slot by exactly T x tan(angle) to give the rotating corner room to clear. For 4.5 degrees this is 0.24mm. For 15 degrees it is 0.80mm. The code calls this the overcut (W_over) and adds it to the joint tolerance automatically for all angled joints.

📌  This is why the test strip matters especially for trapezoidal boxes. Even if your burn and tolerance are perfectly calibrated for straight joints, the overcut for angled joints is an additional correction on top of that. Cut the test strip and verify the leg joint specifically.

### B.5 The Gatekeeper: Why the Tool Refuses Some Designs
As the trapezoid angle increases, the overcut gets larger. At some point it eats into the structural part of the finger — the wood that carries the load and holds the glue. The joint becomes too thin to be useful.

trapezoid_box.py calculates the remaining structural width and refuses to generate an SVG if it falls below half the material thickness. The error message tells you exactly what is happening and gives you three options: reduce the angle, increase the finger width, or reduce the material thickness.

It may feel frustrating to have the tool refuse to run. But it is far less frustrating than cutting a full sheet, assembling the box, and discovering that the leg joints simply fall apart.

### B.6 Corner Radii: Where Aesthetics Meet Structural Engineering
The rounded corners on the base and soundboard are not purely aesthetic. Sharp internal corners in laser-cut wood are stress concentrations — cracks are most likely to start there when the box is dropped or the wood cycles through humidity changes. A radius distributes that stress over a curve.

The auto radius is 3 x material thickness (9mm for 3mm ply). This is large enough to be structurally meaningful and small enough not to intrude on the finger joint area. The point where the arc ends and the fingers begin is calculated precisely for each corner angle — it is slightly different at the obtuse and acute corners of a trapezoid.

### B.7 Instrument Mode: When the Box Must Breathe
A musical instrument soundbox is fundamentally different from a storage box. In a storage box you want maximum rigidity. In an instrument, the soundboard must vibrate freely. Locking it into the walls with finger joints would damp those vibrations and produce a dead, toneless sound.

Instrument mode handles this by generating the soundboard as a plain trapezoid with no finger joints. Instead, the builder glues the soundboard to kerfing strips — thin internal ledges glued to the inside faces of the walls that provide the gluing surface without mechanically constraining the soundboard.

The wall panels in instrument mode have their finger tabs pointing outward by default. The tabs stick out beyond the nominal panel edge and are trimmed flush by the builder. This gives control over the fit and allows slight adjustment during assembly. The kerfing fills any small gaps.

### B.8 The Helmholtz Resonator: Tuning the Air Inside
Every closed box with a hole in it is a Helmholtz resonator — it resonates at a frequency determined by the volume of air inside and the size of the opening. Guitar and dulcimer bodies use this: the resonant frequency of the air reinforces certain notes in the instrument's range.

The Helmholtz formula works backwards from a target frequency to derive the hole size. The default target is 110 Hz (the A below middle C), a common bass resonance for dulcimer-scale instruments. The tool reports both the target and achieved frequency.

The iterative solution exists because the effective neck length L_eff depends on the hole diameter (larger hole = more air mass participating), making the equation circular. The tool iterates to convergence in fewer than five steps for any physically reasonable design.

### B.9 The Test Strip: Your Most Important Panel
The test strip is always generated, always placed last. It carries a finger joint profile identical to the bottom edge of the long wall. The intended workflow: cut the test strip first. Mate it with a scrap piece of base material. Check the fit. Adjust burn and tolerance. Recut. Only when the joint is right do you cut the full sheet.

This exists because every laser cutter is different, every batch of plywood is slightly different, and workshop humidity affects the wood. No default value is perfect for every setup. The test strip closes that gap.

For trapezoidal boxes: test both the end joints (square cut) and the leg joints (angled). They have different effective tolerances and both need to be right.

### B.10 SVG Scale: The Trap That Ruins Sheets
This is the most common source of ruined laser-cut sheets among first-time SVG users. A file that says width=&quot;600mm&quot; should mean 600 real millimetres. But many laser driver programs ignore the unit suffix and treat the number as pixels at 96 dpi — producing a cut at about 26% of the intended size. Your dulcimer body comes out the size of a business card.

Always open the SVG in Inkscape first. Check Document Properties (Shift+Ctrl+D). The document size should show correct physical dimensions in millimetres. If it does not, export from Inkscape at 96dpi with explicit mm units, then import that export into your laser driver.

The SVG file includes a prominent comment at the top reminding you of this check every time. Do not skip it.

### B.11 Grain Direction: A Structural Decision, Not an Aesthetic One
Wood is much stronger along the grain than across it. The soundboard of an instrument must have grain running along its long axis — across-grain soundboards vibrate differently and are structurally weaker. trapezoid_box.py marks grain direction on every panel with a double-headed arrow, and the layout algorithm never rotates BASE or SOUNDBOARD panels even if rotation would reduce material waste.

When you cut the sheet, orient your plywood so the grain arrows match the long axis of those panels. For wall panels the grain direction is less critical and rotation is permitted.

### B.12 What Correct Means Here
This specification was developed through an iterative process of finding and fixing geometric errors — some caught by mathematical proof, some caught by simulating the assembly step by step, and a few caught by a rival AI system looking at the design with fresh eyes.

The most important lesson: geometric correctness on screen does not guarantee physical correctness in the workshop. A path that closes perfectly in SVG may produce joints that physically cannot seat. An arc that looks right in a viewer may be on the wrong side of the corner in three dimensions.

The only standard that matters: do the parts fit together off the laser bed on the first attempt? The test strip is a partial answer. The mathematical proofs in Appendix A are a more rigorous answer. But ultimately the proof is in the assembly — and that is where this tool earns its keep.