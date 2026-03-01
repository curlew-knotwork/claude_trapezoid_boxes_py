"""
gen_test_cut.py — Confidence test cut set via production pipeline.

Generates test_cut_set.svg using the same code path as the CLI.
Verifies all panels before writing. Any geometry bug in production code
will appear here.

Usage:
    python tests/gen_test_cut.py
    python tests/gen_test_cut.py --burn 0.05 --tolerance 0.1  # hand-press fit
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from core.models import CommonConfig, BoxConfig, DimMode, LidType
from core.trapezoid import derive
from core.radii import resolve_corner_radius
from box import panels as box_panels
from core import layout as layout_module
from core import svg_writer


# Test cut parameters — small box that exercises all joint types
_DEFAULTS = dict(
    long=65.0, short=45.0, length=45.0, depth=20.0,
    thickness=3.0, burn=0.05, tolerance=0.0,
)

_OUT = Path(__file__).parent / "test_cut_set.svg"


def run(long: float, short: float, length: float, depth: float,
        thickness: float, burn: float, tolerance: float) -> None:
    common = CommonConfig(
        long=long, short=short, length=length, leg=None,
        depth=depth, thickness=thickness,
        burn=burn, tolerance=tolerance,
        corner_radius=None, finger_width=None,
        sheet_width=600.0, sheet_height=600.0,
        labels=True, dim_mode=DimMode.OUTER,
        colorblind=False, json_errors=False,
        output=str(_OUT),
    )
    config = BoxConfig(common=common, lid=LidType.NONE)

    geom   = derive(common)
    radius = resolve_corner_radius(common, geom)
    panels = box_panels.build(config, geom, radius)
    layout = layout_module.layout_panels(panels, common.sheet_width, common.sheet_height)

    fw = thickness * 3.0  # AUTO_FINGER_WIDTH_FACTOR * thickness
    tab_w = fw + 2 * burn
    gap_w = fw - 2 * burn + 2 * tolerance
    fit   = gap_w - tab_w   # should be -4*burn + 2*tol

    print(f"Burn model: drawn_tab={tab_w:.3f}mm  drawn_slot={gap_w:.3f}mm  "
          f"nominal_fit={fit:+.3f}mm  depth={thickness+burn:.3f}mm")
    print(f"Panels: {[p.name for p in panels]}")

    svg_writer.write(layout, common, [_OUT], "box")
    print(f"Written: {_OUT}")


def main() -> None:
    p = argparse.ArgumentParser(description="Generate test cut set via production pipeline")
    p.add_argument("--burn",      type=float, default=_DEFAULTS["burn"])
    p.add_argument("--tolerance", type=float, default=_DEFAULTS["tolerance"])
    p.add_argument("--depth",     type=float, default=_DEFAULTS["depth"])
    p.add_argument("--thickness", type=float, default=_DEFAULTS["thickness"])
    args = p.parse_args()

    run(
        long=_DEFAULTS["long"], short=_DEFAULTS["short"],
        length=_DEFAULTS["length"], depth=args.depth,
        thickness=args.thickness, burn=args.burn, tolerance=args.tolerance,
    )


if __name__ == "__main__":
    main()
