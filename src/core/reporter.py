"""
core/reporter.py — All stdout/stderr output. No other module prints.
"""

from __future__ import annotations
import json
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.models import Panel, CommonConfig
    from core.trapezoid import TrapezoidGeometry


def print_errors(errors: list[dict], json_mode: bool = False) -> None:
    """Print validation errors. In json_mode: single JSON array to stderr."""
    if json_mode:
        print(json.dumps(errors), file=sys.stderr)
    else:
        for e in errors:
            code    = e.get("code", "ERROR")
            message = e.get("message", "")
            param   = e.get("parameter")
            val     = e.get("value")
            parts   = [f"[{code}] {message}"]
            if param:
                parts.append(f"  parameter: {param}")
            if val:
                parts.append(f"  value: {val}")
            print("\n".join(parts), file=sys.stderr)


def print_error(message: str, code: str, parameter: str | None, value: str | None,
                json_mode: bool = False) -> None:
    """Print a single runtime error."""
    err = {"code": code, "message": message, "parameter": parameter, "value": value}
    if json_mode:
        print(json.dumps(err), file=sys.stderr)
    else:
        parts = [f"[{code}] {message}"]
        if parameter:
            parts.append(f"  parameter: {parameter}")
        if value:
            parts.append(f"  value: {value}")
        print("\n".join(parts), file=sys.stderr)


def print_warning(message: str) -> None:
    """Print a warning to stderr."""
    print(f"WARNING: {message}", file=sys.stderr)


def print_summary(
    geom:      "TrapezoidGeometry",
    panels:    list["Panel"],
    layout:    list[tuple],
    sh_result: object | None,
    config:    "CommonConfig",
    mode:      str,
) -> None:
    """Print a human-readable summary of the generated output."""
    print(f"trapezoid_boxes v2.0 — {mode} mode")
    print(f"  Geometry: long={geom.long_outer:.1f} short={geom.short_outer:.1f} "
          f"length={geom.length_outer:.1f} depth={geom.depth_outer:.1f} "
          f"T={geom.thickness:.1f}mm")
    print(f"  Leg angle: {geom.leg_angle_deg:.3f}°  "
          f"Air volume: {geom.air_volume/1000:.1f}cm³")
    print(f"  Panels: {len(panels)}")
    if sh_result is not None:
        print(f"  Soundhole: {sh_result.type.value}  "       # type: ignore[union-attr]
              f"target={sh_result.target_freq_hz:.1f}Hz  "   # type: ignore[union-attr]
              f"achieved={sh_result.achieved_freq_hz:.1f}Hz") # type: ignore[union-attr]
    num_sheets = max(idx for _, _, idx in layout) + 1
    print(f"  Sheets: {num_sheets}")
    print(f"  Output: {config.output}")
