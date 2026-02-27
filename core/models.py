"""
core/models.py — All dataclasses and enums for trapezoid_box v2.0.
No logic lives here — only data definitions.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Union

from constants import FLOAT_TOLERANCE


# ── Enums ────────────────────────────────────────────────────────────────────

class DimMode(Enum):
    OUTER = "outer"
    INNER = "inner"


class LidType(Enum):
    NONE      = "none"
    LIFT_OFF  = "lift-off"
    SLIDING   = "sliding"
    HINGED    = "hinged"
    FLAP      = "flap"


class FingerDirection(Enum):
    INWARD  = "in"
    OUTWARD = "out"


class SoundHoleType(Enum):
    ROUND              = "round"
    FHOLE              = "f-hole"
    ROUNDED_TRAPEZOID  = "rounded-trapezoid"


class SoundHoleOrientation(Enum):
    SAME    = "same"
    FLIPPED = "flipped"


class MarkType(Enum):
    LABEL        = auto()
    GRAIN_ARROW  = auto()
    ASSEMBLY_NUM = auto()


class PanelType(Enum):
    BASE            = "BASE"
    WALL_LONG       = "WALL_LONG"
    WALL_SHORT      = "WALL_SHORT"
    WALL_LEG_LEFT   = "WALL_LEG_LEFT"
    WALL_LEG_RIGHT  = "WALL_LEG_RIGHT"
    SOUNDBOARD      = "SOUNDBOARD"
    LID             = "LID"
    NECK_BLOCK      = "NECK_BLOCK"
    TAIL_BLOCK      = "TAIL_BLOCK"
    KERF_STRIP      = "KERF_STRIP"
    KERF_FILLET     = "KERF_FILLET"
    TEST_STRIP      = "TEST_STRIP"


# ── Primitive geometry ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Line:
    start: Point
    end: Point


@dataclass(frozen=True)
class Arc:
    start:      Point
    end:        Point
    radius:     float
    large_arc:  bool
    clockwise:  bool


@dataclass(frozen=True)
class CubicBezier:
    start: Point
    cp1:   Point
    cp2:   Point
    end:   Point


PathSegment = Union[Line, Arc, CubicBezier]


def _segment_start(seg: PathSegment) -> Point:
    match seg:
        case Line(start=s):        return s
        case Arc(start=s):         return s
        case CubicBezier(start=s): return s


def _segment_end(seg: PathSegment) -> Point:
    match seg:
        case Line(end=e):        return e
        case Arc(end=e):         return e
        case CubicBezier(end=e): return e


@dataclass(frozen=True)
class ClosedPath:
    segments: tuple[PathSegment, ...]

    def __post_init__(self) -> None:
        if len(self.segments) == 0:
            raise ValueError("ClosedPath must have at least one segment.")
        last_end    = _segment_end(self.segments[-1])
        first_start = _segment_start(self.segments[0])
        if not (abs(last_end.x - first_start.x) <= FLOAT_TOLERANCE and
                abs(last_end.y - first_start.y) <= FLOAT_TOLERANCE):
            raise ValueError(
                f"ClosedPath not closed: last ends at ({last_end.x:.4f}, {last_end.y:.4f})"
                f" but first starts at ({first_start.x:.4f}, {first_start.y:.4f})."
            )


# ── Finger joints ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FingerEdge:
    start:            Point
    end:              Point
    term_start:       Point    # finger start (after left corner arc tangent)
    term_end:         Point    # finger end (before right corner arc tangent)
    finger_width:     float    # actual width after odd-count adjustment; 0.0 if count=0
    count:            int      # number of fingers; 0 = plain edge
    depth:            float    # mating panel thickness
    protrude_outward: bool     # True = fingers extend beyond nominal edge
    is_slotted:       bool     # True = this edge carries slots, not protruding fingers
    burn:             float
    tolerance:        float


# ── Marks and score lines ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Mark:
    type:      MarkType
    position:  Point
    content:   str
    angle_deg: float = 0.0


# ── Holes ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CircleHole:
    centre:   Point
    diameter: float


@dataclass(frozen=True)
class ClosedHole:
    path: ClosedPath


Hole = Union[CircleHole, ClosedHole]


# ── Sound hole result ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SoundHoleResult:
    type:                SoundHoleType
    diameter_or_size_mm: float
    open_area_mm2:       float
    target_freq_hz:      float
    achieved_freq_hz:    float
    iterations:          int


# ── Panel ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Panel:
    type:           PanelType
    name:           str
    outline:        ClosedPath
    finger_edges:   list[FingerEdge]
    holes:          list[Hole]
    score_lines:    list[Line]
    marks:          list[Mark]
    grain_angle_deg: float
    width:          float      # nominal outer width (for layout packing)
    height:         float      # nominal outer height (for layout packing)

    def bounding_box(self) -> tuple[float, float]:
        """Returns (width, height) nominal outer dimensions."""
        return (self.width, self.height)


# ── Configuration dataclasses ─────────────────────────────────────────────────

@dataclass
class CommonConfig:
    long:          float
    short:         float
    length:        float | None   # None if mode B (leg provided instead)
    leg:           float | None   # None if mode A (length provided instead)
    depth:         float
    thickness:     float = 3.0
    burn:          float = 0.05
    tolerance:     float = 0.1
    corner_radius: float | None = None    # None = auto (3 × thickness)
    finger_width:  float | None = None    # None = auto (3 × thickness)
    sheet_width:   float = 600.0
    sheet_height:  float = 600.0
    labels:        bool  = True
    dim_mode:      DimMode = DimMode.OUTER
    colorblind:    bool  = False
    json_errors:   bool  = False
    output:        str   = "trapezoid_box_output.svg"


@dataclass
class BoxConfig:
    common:         CommonConfig
    lid:            LidType = LidType.NONE
    hinge_diameter: float   = 6.0


@dataclass
class InstrumentConfig:
    common:                  CommonConfig
    top_thickness:           float = 3.0
    kerf_thickness:          float = 3.0
    kerfing:                 bool  = True
    kerf_height:             float = 12.0
    kerf_width:              float = 6.0
    kerf_top_height:         float = 10.0
    kerf_top_width:          float = 5.0
    soundhole_type:          SoundHoleType | None = None
    soundhole_orientation:   SoundHoleOrientation = SoundHoleOrientation.SAME
    soundhole_long_ratio:    float | None = None
    soundhole_aspect:        float | None = None
    soundhole_r_mm:          float | None = None
    helmholtz_freq:          float = 110.0
    soundhole_diameter:      float | None = None
    soundhole_size:          float | None = None
    soundhole_x:             float | None = None
    soundhole_y:             float | None = None
    neck_clearance:          float = 60.0
    hardware:                bool  = False
    neck_block_thickness:    float = 25.0
    tail_block_thickness:    float = 15.0
    braces:                  bool  = False
    scale_length:            float | None = None
    finger_direction:        FingerDirection = FingerDirection.OUTWARD
