"""
constants.py — ALL named constants for trapezoid_box v2.0.
No other file introduces naked numbers.
"""

# ── Geometry fundamentals ─────────────────────────────────────────────────────
FLOAT_TOLERANCE             = 1e-6       # for nearly_equal()
AUTO_CORNER_RADIUS_FACTOR   = 3.0        # auto radius = this × thickness
MIN_CORNER_RADIUS_MM        = 5.0
AUTO_FINGER_WIDTH_FACTOR    = 3.0        # auto finger width = this × thickness
MIN_FINGER_COUNT            = 3
PANEL_GAP_MM                = 10.0       # gap between panels in layout

# ── Non-orthogonal joint geometry (THE GATEKEEPER) ───────────────────────────
OVERCUT_MIN_STRUCT_RATIO    = 0.5        # min remaining finger width = this × thickness
# Prevents overcut from consuming the structural tab.
# W_struct = finger_width - tolerance - T*tan(leg_angle) must be >= thickness * 0.5

# ── Laser / material defaults ─────────────────────────────────────────────────
DEFAULT_THICKNESS_MM        = 3.0
DEFAULT_BURN_MM             = 0.05       # typical CO2 kerf compensation for 3mm ply
DEFAULT_TOLERANCE_MM        = 0.1        # finger joint fit clearance

# ── Layout / sheet defaults ───────────────────────────────────────────────────
DEFAULT_SHEET_WIDTH_MM      = 600.0
DEFAULT_SHEET_HEIGHT_MM     = 600.0

# ── Acoustics ─────────────────────────────────────────────────────────────────
SPEED_OF_SOUND_MM_S         = 343000.0   # mm/s at 20°C
DEFAULT_HELMHOLTZ_HZ        = 110.0      # target A0 for dulcimer/guitar
DEFAULT_NECK_CLEARANCE_MM   = 60.0
HELMHOLTZ_L_EFF_FACTOR      = 0.85       # end-correction factor
HELMHOLTZ_MAX_ITERATIONS    = 20

# ── Instrument hardware defaults ──────────────────────────────────────────────
DEFAULT_KERF_HEIGHT_MM      = 12.0
DEFAULT_KERF_WIDTH_MM       = 6.0
DEFAULT_KERF_TOP_HEIGHT_MM  = 10.0
DEFAULT_KERF_TOP_WIDTH_MM   = 5.0
KERF_UNDERSIZE_MM           = 0.5
DEFAULT_NECK_BLOCK_THICK_MM = 25.0
DEFAULT_TAIL_BLOCK_THICK_MM = 15.0
DEFAULT_HINGE_DIAMETER_MM   = 6.0
HINGE_SPACING_MM            = 80.0       # one hinge per this many mm

# ── SVG output ────────────────────────────────────────────────────────────────
SVG_CUT_COLOUR              = (255, 0, 0)
SVG_SCORE_COLOUR            = (0, 0, 255)
SVG_LABEL_COLOUR            = (0, 0, 0)
SVG_CB_CUT_COLOUR           = (0, 0, 0)      # colorblind mode: cut = solid black
SVG_CB_SCORE_COLOUR         = (0, 0, 0)      # colorblind mode: score = dashed black
SVG_HAIRLINE_MM             = 0.001          # Epilog-compatible hairline
SVG_DISPLAY_STROKE_MM       = 0.0            # 0 = use hairline; >0 overrides for human-viewable output
SVG_LABEL_STROKE_MM         = 0.2
SVG_SCORE_DASH_MM           = 5.0
SVG_SCORE_GAP_MM            = 2.0
SVG_COORD_DECIMAL_PLACES    = 4
SVG_LABEL_FONT_MM           = 4.0
SVG_ASSEMBLY_NUM_FONT_MM    = 8.0
SVG_TRAPEZOIDBOX_NS         = "https://trapezoidbox.github.io/ns/1.0"

# ── F-hole shape proportions ──────────────────────────────────────────────────
FHOLE_UPPER_EYE_Y_RATIO     = 0.20
FHOLE_LOWER_EYE_Y_RATIO     = 0.75
FHOLE_UPPER_EYE_D_RATIO     = 0.12
FHOLE_LOWER_EYE_D_RATIO     = 0.16
FHOLE_WAIST_RATIO           = 0.60
FHOLE_WAIST_Y_RATIO         = 0.475
FHOLE_CP1_X_RATIO_UPPER     = 0.30
FHOLE_CP2_X_RATIO_UPPER     = 0.40
FHOLE_CP1_Y_RATIO_UPPER     = 0.35
FHOLE_CP2_Y_RATIO_UPPER     = 0.45
FHOLE_CP1_X_RATIO_LOWER     = 0.40
FHOLE_CP2_X_RATIO_LOWER     = 0.30
FHOLE_CP1_Y_RATIO_LOWER     = 0.55
FHOLE_CP2_Y_RATIO_LOWER     = 0.65
FHOLE_NICK_DEPTH_MM         = 1.5
FHOLE_PAIR_OFFSET_RATIO     = 0.45

# ── Rounded-trapezoid soundhole proportions ───────────────────────────────────
# Hole inherits body long/short taper ratio. Corner radius is a FIXED MM VALUE —
# a ratio-based radius fails at steep leg angles (sweep >90°, arc visually dominates).
# Aspect ratio must always be explicit (0.3–2.0); None/inherit is rejected at validation.
# Default orientation "same": long edge toward tail, matching body. "flipped": opposite.
# Default parameters chosen to give ~150Hz Helmholtz resonance on dulcimer preset.
RTRAP_LONG_TO_BODY_RATIO    = 0.28   # hole long-edge = body long_outer × this
RTRAP_ASPECT_RATIO          = 0.6    # hole height = hole_long × this (0.3–2.0, no None)
RTRAP_CORNER_R_MM           = 2.0    # corner fillet radius, fixed mm (NOT a ratio)
RTRAP_MAX_R_EDGE_FRACTION   = 0.15   # r must be <= min(all edges) × this; enforced at validation
RTRAP_ORIENTATION           = "same" # "same": long edge toward tail (matches body); "flipped": opposite

# ── Test strip ────────────────────────────────────────────────────────────────
TEST_STRIP_WIDTH_MM         = 60.0

# ── Version ───────────────────────────────────────────────────────────────────
TOOL_VERSION                = "2.0"

# ── Validation error codes (prefix ERR_) ──────────────────────────────────────
ERR_VALIDATION_LONG_SHORT_ORDER       = "VALIDATION_LONG_SHORT_ORDER"
ERR_VALIDATION_THICKNESS_TOO_LARGE    = "VALIDATION_THICKNESS_TOO_LARGE"
ERR_VALIDATION_FINGER_TOO_THIN        = "VALIDATION_FINGER_TOO_THIN"
ERR_VALIDATION_ANGLE_TOO_STEEP        = "VALIDATION_ANGLE_TOO_STEEP"
ERR_VALIDATION_STRUCT_TAB_TOO_THIN    = "VALIDATION_STRUCT_TAB_TOO_THIN"
ERR_RUNTIME                           = "ERR_RUNTIME"
ERR_FORMAT_NOT_IMPLEMENTED            = "ERR_FORMAT_NOT_IMPLEMENTED"
ERR_VALIDATION_TEST_STRIP_TOO_TALL    = "VALIDATION_TEST_STRIP_TOO_TALL"
ERR_VALIDATION_GROOVE_ANGLE_TOO_STEEP = "VALIDATION_GROOVE_ANGLE_TOO_STEEP"
ERR_VALIDATION_SOUNDHOLE_TOO_TALL     = "VALIDATION_SOUNDHOLE_TOO_TALL"
ERR_VALIDATION_SOUNDHOLE_LONG_RATIO   = "VALIDATION_SOUNDHOLE_LONG_RATIO"
ERR_VALIDATION_SOUNDHOLE_ASPECT       = "VALIDATION_SOUNDHOLE_ASPECT"
ERR_VALIDATION_SOUNDHOLE_RADIUS       = "VALIDATION_SOUNDHOLE_RADIUS"
ERR_VALIDATION_SOUNDHOLE_LATERAL      = "VALIDATION_SOUNDHOLE_LATERAL"
