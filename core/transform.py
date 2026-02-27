"""
core/transform.py — Pure coordinate transforms. No geometry creation.
"""

from __future__ import annotations
import math

from core.models import (
    Point, Line, Arc, CubicBezier, ClosedPath, PathSegment,
    _segment_start, _segment_end,
)
from core.utils import rotate_point


def flip_y(point: Point, height: float) -> Point:
    """Reflect over horizontal axis at y=height."""
    return Point(point.x, height - point.y)


def _transform_segment(seg: PathSegment, fn) -> PathSegment:
    """Apply fn (Point -> Point) to all points in a segment."""
    match seg:
        case Line(start=s, end=e):
            return Line(fn(s), fn(e))
        case Arc(start=s, end=e, radius=r, large_arc=la, clockwise=cw):
            return Arc(fn(s), fn(e), r, la, cw)
        case CubicBezier(start=s, cp1=p1, cp2=p2, end=e):
            return CubicBezier(fn(s), fn(p1), fn(p2), fn(e))


def rotate_path(path: ClosedPath, centre: Point, angle_deg: float) -> ClosedPath:
    """Rotate all points in a ClosedPath clockwise around centre."""
    fn = lambda p: rotate_point(p, centre, angle_deg)
    return ClosedPath(tuple(_transform_segment(s, fn) for s in path.segments))


def translate_path(path: ClosedPath, dx: float, dy: float) -> ClosedPath:
    """Translate all points in a ClosedPath."""
    fn = lambda p: Point(p.x + dx, p.y + dy)
    return ClosedPath(tuple(_transform_segment(s, fn) for s in path.segments))


def mirror_path_horizontal(path: ClosedPath, axis_x: float) -> ClosedPath:
    """Reflect every point: mirrored_x = 2*axis_x - x, y unchanged.

    Note: mirroring reverses path winding. Call reverse_path() after to restore CW.
    Also reverses arc clockwise sense.
    """
    def fn(p: Point) -> Point:
        return Point(2 * axis_x - p.x, p.y)

    def mirror_seg(seg: PathSegment) -> PathSegment:
        match seg:
            case Line(start=s, end=e):
                return Line(fn(s), fn(e))
            case Arc(start=s, end=e, radius=r, large_arc=la, clockwise=cw):
                # Mirror reverses sweep direction
                return Arc(fn(s), fn(e), r, la, not cw)
            case CubicBezier(start=s, cp1=p1, cp2=p2, end=e):
                return CubicBezier(fn(s), fn(p1), fn(p2), fn(e))

    return ClosedPath(tuple(mirror_seg(s) for s in path.segments))


def reverse_path(path: ClosedPath) -> ClosedPath:
    """Reverse segment order and flip each segment's start/end.

    Used after mirroring to restore clockwise winding.
    """
    def flip_seg(seg: PathSegment) -> PathSegment:
        match seg:
            case Line(start=s, end=e):
                return Line(e, s)
            case Arc(start=s, end=e, radius=r, large_arc=la, clockwise=cw):
                return Arc(e, s, r, la, not cw)
            case CubicBezier(start=s, cp1=p1, cp2=p2, end=e):
                return CubicBezier(e, p2, p1, s)

    reversed_segs = tuple(flip_seg(s) for s in reversed(path.segments))
    return ClosedPath(reversed_segs)
