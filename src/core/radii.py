"""
core/radii.py — Corner arc geometry and finger termination points. No finger joint logic.
"""

from __future__ import annotations
import math

from constants import AUTO_CORNER_RADIUS_FACTOR, MIN_CORNER_RADIUS_MM
from core.models import Point, Arc, CommonConfig
from core.utils import normalise


def auto_corner_radius(thickness: float) -> float:
    """Returns 3 × thickness, rounded to nearest mm, minimum MIN_CORNER_RADIUS_MM."""
    r = round(AUTO_CORNER_RADIUS_FACTOR * thickness)
    return max(MIN_CORNER_RADIUS_MM, float(r))


def resolve_corner_radius(config: "CommonConfig", geom: "TrapezoidGeometry") -> float:  # type: ignore[name-defined]
    """Return user-specified corner_radius if provided, else auto_corner_radius(thickness).

    Validates result < short_outer / 2 and < depth_outer / 2.
    """
    from core.trapezoid import TrapezoidGeometry
    r = config.corner_radius if config.corner_radius is not None else auto_corner_radius(config.thickness)
    if r >= geom.short_outer / 2:
        raise ValueError(
            f"corner_radius ({r}mm) must be < short_outer/2 ({geom.short_outer/2:.3f}mm)."
        )
    if r >= geom.depth_outer / 2:
        raise ValueError(
            f"corner_radius ({r}mm) must be < depth_outer/2 ({geom.depth_outer/2:.3f}mm)."
        )
    return r


def corner_arc_segments(
    vertex:              Point,
    edge_a_dir:          Point,   # unit vector arriving at corner (TOWARD vertex)
    edge_b_dir:          Point,   # unit vector departing from corner (AWAY from vertex)
    corner_radius:       float,
    internal_angle_deg:  float,
) -> tuple[Point, Arc, Point]:
    """
    Returns (arc_start, arc, arc_end).

    edge_a_dir: unit vector pointing TOWARD the vertex (arriving direction).
    edge_b_dir: unit vector pointing AWAY from the vertex (departing direction).

    Bisector = normalise((-edge_a_dir) + edge_b_dir).
    WARNING: do NOT negate both — that points to exterior.

    All corner arcs in this tool subtend < 180°, so large_arc = False always.
    Clockwise = True (panel outline is clockwise in SVG Y-down).
    """
    half_angle_rad = math.radians(internal_angle_deg / 2)

    tangent_dist = corner_radius / math.tan(half_angle_rad)
    centre_dist  = corner_radius / math.sin(half_angle_rad)

    # Arc tangent points on each edge
    arc_start = Point(
        vertex.x - edge_a_dir.x * tangent_dist,
        vertex.y - edge_a_dir.y * tangent_dist,
    )
    arc_end = Point(
        vertex.x + edge_b_dir.x * tangent_dist,
        vertex.y + edge_b_dir.y * tangent_dist,
    )

    # Inward bisector: normalise((-edge_a_dir) + edge_b_dir)
    bx = -edge_a_dir.x + edge_b_dir.x
    by = -edge_a_dir.y + edge_b_dir.y
    mag = math.sqrt(bx * bx + by * by)
    bisector = Point(bx / mag, by / mag)

    # Arc centre along bisector (for reference; arc data only needs start, end, radius)
    _ = Point(
        vertex.x + bisector.x * centre_dist,
        vertex.y + bisector.y * centre_dist,
    )

    arc = Arc(
        start     = arc_start,
        end       = arc_end,
        radius    = corner_radius,
        large_arc = False,
        clockwise = True,    # panel outlines are clockwise in SVG Y-down
    )
    return arc_start, arc, arc_end


def finger_termination_point(
    corner_vertex:      Point,
    edge_direction:     Point,   # unit vector from corner toward edge interior
    corner_radius:      float,
    internal_angle_deg: float,
) -> Point:
    """The point on the edge where the corner arc ends and fingers may begin.

    Located at corner_radius / tan(internal_angle_deg / 2) from corner_vertex
    along edge_direction.
    """
    tangent_dist = corner_radius / math.tan(math.radians(internal_angle_deg / 2))
    return Point(
        corner_vertex.x + tangent_dist * edge_direction.x,
        corner_vertex.y + tangent_dist * edge_direction.y,
    )
