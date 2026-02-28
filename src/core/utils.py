"""
core/utils.py — Pure utility functions. No geometry creation, no I/O.
"""

from __future__ import annotations
import math

from constants import FLOAT_TOLERANCE, MIN_FINGER_COUNT
from core.models import Point, Arc, Line, Arc, CubicBezier, ClosedPath, PathSegment


def nearly_equal(a: float, b: float, tol: float = FLOAT_TOLERANCE) -> bool:
    """Floating-point equality with tolerance. Use for all float comparisons in geometry."""
    return abs(a - b) <= tol


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to closed interval [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def odd_count(edge_length: float, finger_width: float) -> int:
    """Nearest odd integer to edge_length / finger_width. Minimum MIN_FINGER_COUNT."""
    n = round(edge_length / finger_width)
    if n % 2 == 0:
        n -= 1
    return max(MIN_FINGER_COUNT, n)


def actual_finger_width(edge_length: float, count: int) -> float:
    """Returns edge_length / count. count must be odd and >= 1."""
    return edge_length / count


def normalise(p: Point) -> Point:
    """Unit vector in direction of p. Raises ValueError if magnitude is zero."""
    mag = math.sqrt(p.x * p.x + p.y * p.y)
    if nearly_equal(mag, 0.0):
        raise ValueError("Cannot normalise a zero vector.")
    return Point(p.x / mag, p.y / mag)


def deg_to_rad(degrees: float) -> float:
    return math.radians(degrees)


def rad_to_deg(radians: float) -> float:
    return math.degrees(radians)


def translate_point(p: Point, dx: float, dy: float) -> Point:
    return Point(p.x + dx, p.y + dy)


def translate_path(path: ClosedPath, dx: float, dy: float) -> ClosedPath:
    """Translate an entire ClosedPath."""
    from core.transform import translate_path as _tp
    return _tp(path, dx, dy)


def rotate_point(p: Point, centre: Point, angle_deg: float) -> Point:
    """Rotate p clockwise around centre. SVG Y-down: positive = clockwise visual rotation."""
    theta = deg_to_rad(angle_deg)
    dx = p.x - centre.x
    dy = p.y - centre.y
    return Point(
        centre.x + dx * math.cos(theta) - dy * math.sin(theta),
        centre.y + dx * math.sin(theta) + dy * math.cos(theta),
    )


def arc_centre(arc: Arc) -> Point:
    """Recover arc centre from SVG arc parameters (start, end, radius, large_arc, clockwise)."""
    mx = (arc.start.x + arc.end.x) / 2
    my = (arc.start.y + arc.end.y) / 2
    dx = arc.end.x - arc.start.x
    dy = arc.end.y - arc.start.y
    half_chord = math.sqrt(dx * dx + dy * dy) / 2
    if half_chord > arc.radius + FLOAT_TOLERANCE:
        raise ValueError(f"Arc radius {arc.radius} too small for chord {2*half_chord:.4f}")
    d = math.sqrt(max(0.0, arc.radius ** 2 - half_chord ** 2))
    # Perpendicular to chord direction
    px = -dy / (2 * half_chord) if half_chord > 0 else 0.0
    py =  dx / (2 * half_chord) if half_chord > 0 else 0.0
    # Sign rule: (large_arc XOR clockwise) → centre on positive-perpendicular side
    sign = 1.0 if (arc.large_arc != arc.clockwise) else -1.0
    return Point(mx + sign * d * px, my + sign * d * py)


def approximate_as_polyline(path: ClosedPath, samples_per_curve: int = 8) -> list[Point]:
    """Convert ClosedPath to polygon for shoelace formula.

    Each segment contributes its start point and interior samples but NOT its endpoint.
    """
    pts: list[Point] = []
    for seg in path.segments:
        match seg:
            case Line(start=s):
                pts.append(s)
            case Arc() as arc:
                # Sample arc at t = 0, 1/n, ..., (n-1)/n
                centre = arc_centre(arc)
                start_angle = math.atan2(arc.start.y - centre.y, arc.start.x - centre.x)
                end_angle   = math.atan2(arc.end.y   - centre.y, arc.end.x   - centre.x)
                # Determine sweep direction
                if arc.clockwise:
                    # Clockwise in SVG Y-down: end_angle > start_angle going CW
                    if end_angle < start_angle:
                        end_angle += 2 * math.pi
                    if arc.large_arc and (end_angle - start_angle) < math.pi:
                        end_angle += 2 * math.pi
                else:
                    # Counter-clockwise
                    if end_angle > start_angle:
                        end_angle -= 2 * math.pi
                    if arc.large_arc and (start_angle - end_angle) < math.pi:
                        end_angle -= 2 * math.pi
                n = samples_per_curve
                for i in range(n):
                    t = i / n
                    angle = start_angle + t * (end_angle - start_angle)
                    pts.append(Point(
                        centre.x + arc.radius * math.cos(angle),
                        centre.y + arc.radius * math.sin(angle),
                    ))
            case CubicBezier(start=p0, cp1=p1, cp2=p2, end=p3):
                n = samples_per_curve
                for i in range(n):
                    t = i / n
                    u = 1 - t
                    x = u**3*p0.x + 3*u**2*t*p1.x + 3*u*t**2*p2.x + t**3*p3.x
                    y = u**3*p0.y + 3*u**2*t*p1.y + 3*u*t**2*p2.y + t**3*p3.y
                    pts.append(Point(x, y))
    return pts


def path_winding(path: ClosedPath) -> str:
    """Returns 'clockwise' or 'counter-clockwise' using shoelace formula.

    In SVG Y-down space, positive signed area = clockwise.
    """
    pts = approximate_as_polyline(path)
    n = len(pts)
    signed_area = sum(
        pts[i].x * pts[(i + 1) % n].y - pts[(i + 1) % n].x * pts[i].y
        for i in range(n)
    ) / 2.0
    return "clockwise" if signed_area > 0 else "counter-clockwise"
