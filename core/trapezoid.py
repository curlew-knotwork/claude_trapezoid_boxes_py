"""
core/trapezoid.py — Pure trapezoid mathematics.
No SVG, no joints, no side effects.
Assumes all inputs are already validated — no defensive checks here.
"""

from __future__ import annotations
import math
from dataclasses import dataclass

from core.models import CommonConfig, DimMode


@dataclass(frozen=True)
class TrapezoidGeometry:
    # Outer dimensions (mm)
    long_outer:          float
    short_outer:         float
    length_outer:        float
    depth_outer:         float
    thickness:           float

    # Derived geometry
    leg_inset:           float    # (long_outer - short_outer) / 2
    leg_length:          float    # sqrt(length_outer² + leg_inset²)
    leg_angle_deg:       float    # arctan(leg_inset / length_outer)
    long_end_angle_deg:  float    # 90 + leg_angle_deg  (interior angle at long/narrow end)
    short_end_angle_deg: float    # 90 - leg_angle_deg  (interior angle at short/wide end)

    # Inner dimensions (for Helmholtz)
    long_inner:          float    # long_outer - 2*thickness
    short_inner:         float    # short_outer - 2*thickness
    length_inner:        float    # length_outer - 2*thickness (simplified)
    depth_inner:         float    # depth_outer - 2*thickness
    air_volume:          float    # 0.5*(long_inner+short_inner)*length_inner*depth_inner


def derive(config: CommonConfig) -> TrapezoidGeometry:
    """Derive all trapezoid geometry from a CommonConfig.

    Mode A: config.length is not None.
    Mode B: config.leg is not None.
    DimMode.INNER: input dimensions treated as inner; 2*thickness added before computing.
    """
    t = config.thickness

    if config.dim_mode == DimMode.INNER:
        long_o  = config.long  + 2 * t
        short_o = config.short + 2 * t
        depth_o = config.depth + 2 * t
    else:
        long_o  = config.long
        short_o = config.short
        depth_o = config.depth

    leg_inset = (long_o - short_o) / 2.0

    if config.length is not None:
        length_o = config.length + (2 * t if config.dim_mode == DimMode.INNER else 0)
        leg_len  = math.sqrt(length_o ** 2 + leg_inset ** 2)
    else:
        # Mode B: leg is the diagonal
        leg_len  = config.leg  # type: ignore[assignment]
        length_o = math.sqrt(leg_len ** 2 - leg_inset ** 2)

    leg_angle = math.degrees(math.atan2(leg_inset, length_o))

    return TrapezoidGeometry(
        long_outer          = long_o,
        short_outer         = short_o,
        length_outer        = length_o,
        depth_outer         = depth_o,
        thickness           = t,
        leg_inset           = leg_inset,
        leg_length          = leg_len,
        leg_angle_deg       = leg_angle,
        long_end_angle_deg  = 90.0 + leg_angle,
        short_end_angle_deg = 90.0 - leg_angle,
        long_inner          = long_o  - 2 * t,
        short_inner         = short_o - 2 * t,
        length_inner        = length_o - 2 * t,
        depth_inner         = depth_o  - 2 * t,
        air_volume          = 0.5 * (long_o - 2*t + short_o - 2*t) * (length_o - 2*t) * (depth_o - 2*t),
    )
