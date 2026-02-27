"""
box/cli.py — Box CLI: args, validation, config, run().
"""

from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

from constants import (
    TOOL_VERSION, DEFAULT_THICKNESS_MM, DEFAULT_BURN_MM, DEFAULT_TOLERANCE_MM,
    DEFAULT_SHEET_WIDTH_MM, DEFAULT_SHEET_HEIGHT_MM,
    AUTO_FINGER_WIDTH_FACTOR, OVERCUT_MIN_STRUCT_RATIO,
    ERR_VALIDATION_LONG_SHORT_ORDER, ERR_VALIDATION_THICKNESS_TOO_LARGE,
    ERR_VALIDATION_FINGER_TOO_THIN, ERR_VALIDATION_ANGLE_TOO_STEEP,
    ERR_VALIDATION_STRUCT_TAB_TOO_THIN, ERR_VALIDATION_TEST_STRIP_TOO_TALL,
    ERR_VALIDATION_GROOVE_ANGLE_TOO_STEEP,
)
from core.models import CommonConfig, BoxConfig, DimMode, LidType
from core.trapezoid import TrapezoidGeometry
from core import reporter


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common parameters to a subcommand parser."""
    parser.add_argument("--long",          type=float, default=None)
    parser.add_argument("--short",         type=float, default=None)

    exc = parser.add_mutually_exclusive_group()
    exc.add_argument("--length",           type=float, default=None)
    exc.add_argument("--leg",              type=float, default=None)

    parser.add_argument("--depth",         type=float, default=None)
    parser.add_argument("--thickness",     type=float, default=None)
    parser.add_argument("--burn",          type=float, default=None)
    parser.add_argument("--tolerance",     type=float, default=None)
    parser.add_argument("--corner-radius", type=float, default=None)
    parser.add_argument("--finger-width",  type=float, default=None)
    parser.add_argument("--inner",         action="store_true", default=None)
    parser.add_argument("--sheet-width",   type=float, default=None)
    parser.add_argument("--sheet-height",  type=float, default=None)
    parser.add_argument("--labels",        action="store_true",  default=None, dest="labels")
    parser.add_argument("--no-labels",     action="store_false", default=None, dest="labels")
    parser.add_argument("--colorblind",    action="store_true", default=None)
    parser.add_argument("--json-errors",   action="store_true", default=None)
    parser.add_argument("--format",        choices=["svg", "dxf"], default=None)
    parser.add_argument("--per-panel",     action="store_true", default=None)
    parser.add_argument("--preset",        type=str, default=None)
    parser.add_argument("--list-presets",  action="store_true", default=None)
    parser.add_argument("--output",           type=str,   default=None)
    parser.add_argument("--config",           type=str,   default=None, dest="config_file")
    parser.add_argument("--save-config",      type=str,   default=None)
    parser.add_argument("--extract-config",   type=str,   default=None)
    parser.add_argument("--display-stroke",   type=float, default=None,
                        metavar="MM",
                        help="Stroke width for cut paths (default 0.001mm hairline). "
                             "Use e.g. 0.3 for human-viewable output.")


def add_box_args(parser: argparse.ArgumentParser) -> None:
    """Add box-specific parameters."""
    add_common_args(parser)
    parser.add_argument("--lid", choices=["none","lift-off","sliding","hinged","flap"],
                        default=None)
    parser.add_argument("--hinge-diameter", type=float, default=None)


def _defaults() -> dict:
    return {
        "long": None, "short": None, "length": None, "leg": None, "depth": None,
        "thickness": DEFAULT_THICKNESS_MM, "burn": DEFAULT_BURN_MM,
        "tolerance": DEFAULT_TOLERANCE_MM, "corner_radius": None, "finger_width": None,
        "sheet_width": DEFAULT_SHEET_WIDTH_MM, "sheet_height": DEFAULT_SHEET_HEIGHT_MM,
        "labels": True, "dim_mode": DimMode.OUTER, "colorblind": False,
        "json_errors": False, "output": "trapezoid_box_output.svg",
        "display_stroke_mm": 0.0,
    }


def build_config(args: argparse.Namespace) -> BoxConfig:
    """Build BoxConfig from args using preset → config file → CLI precedence."""
    from presets import get_preset

    vals = _defaults()

    # 1. Preset
    if args.preset:
        p = get_preset(args.preset)
        for k, v in p.get("common", {}).items():
            vals[k] = v
        box_preset = p.get("box", {})
    else:
        box_preset = {}

    lid_type   = LidType(box_preset.get("lid", "none"))
    hinge_diam = box_preset.get("hinge_diameter", 6.0)

    # 2. Config file
    if getattr(args, "config_file", None):
        with open(args.config_file) as f:
            cfg_json = json.load(f)
        for k, v in cfg_json.get("common", {}).items():
            if v is not None:
                vals[k] = v
        box_json = cfg_json.get("box", {})
        if "lid" in box_json and box_json["lid"]:
            lid_type = LidType(box_json["lid"])
        if "hinge_diameter" in box_json and box_json["hinge_diameter"] is not None:
            hinge_diam = box_json["hinge_diameter"]

    # 3. CLI args (None = not provided, does not override)
    def _apply(attr: str, key: str) -> None:
        v = getattr(args, attr, None)
        if v is not None:
            vals[key] = v

    _apply("long",          "long")
    _apply("short",         "short")
    _apply("length",        "length")
    _apply("leg",           "leg")
    _apply("depth",         "depth")
    _apply("thickness",     "thickness")
    _apply("burn",          "burn")
    _apply("tolerance",     "tolerance")
    _apply("corner_radius", "corner_radius")
    _apply("finger_width",  "finger_width")
    _apply("sheet_width",   "sheet_width")
    _apply("sheet_height",  "sheet_height")
    _apply("output",        "output")

    if getattr(args, "inner", None):
        vals["dim_mode"] = DimMode.INNER
    if getattr(args, "colorblind", None):
        vals["colorblind"] = True
    if getattr(args, "json_errors", None):
        vals["json_errors"] = True
    if getattr(args, "labels", None) is not None:
        vals["labels"] = args.labels
    if getattr(args, "display_stroke", None) is not None:
        vals["display_stroke_mm"] = args.display_stroke

    if getattr(args, "lid", None) is not None:
        lid_type = LidType(args.lid)
    if getattr(args, "hinge_diameter", None) is not None:
        hinge_diam = args.hinge_diameter

    common = CommonConfig(
        long=vals["long"] or 0.0,
        short=vals["short"] or 0.0,
        length=vals.get("length"),
        leg=vals.get("leg"),
        depth=vals["depth"] or 0.0,
        thickness=vals["thickness"],
        burn=vals["burn"],
        tolerance=vals["tolerance"],
        corner_radius=vals["corner_radius"],
        finger_width=vals["finger_width"],
        sheet_width=vals["sheet_width"],
        sheet_height=vals["sheet_height"],
        labels=vals["labels"],
        dim_mode=vals["dim_mode"],
        colorblind=vals["colorblind"],
        json_errors=vals["json_errors"],
        output=vals["output"],
        display_stroke_mm=vals.get("display_stroke_mm", 0.0),
    )
    return BoxConfig(common=common, lid=lid_type, hinge_diameter=hinge_diam)


def validate_config(config: BoxConfig) -> list[dict]:
    """Validate BoxConfig. Returns list of error dicts (empty = valid).

    Never calls sys.exit(). The CLI handles output and exit.
    """
    errors: list[dict] = []
    c = config.common

    def err(code: str, message: str, parameter: str | None = None, value: str | None = None):
        errors.append({"code": code, "message": message,
                        "parameter": parameter, "value": value})

    # Basic presence
    if c.long is None or c.short is None or c.depth is None:
        err("VALIDATION_MISSING_DIMS", "long, short, and depth are required.")
        return errors  # can't proceed

    # long > short > 0
    if c.long <= c.short:
        err(ERR_VALIDATION_LONG_SHORT_ORDER,
            f"long ({c.long}mm) must be greater than short ({c.short}mm).",
            "long", str(c.long))

    if c.short <= 0:
        err(ERR_VALIDATION_LONG_SHORT_ORDER, "short must be > 0.", "short", str(c.short))

    # Exactly one of length, leg
    if c.length is None and c.leg is None:
        err("VALIDATION_MISSING_LENGTH_OR_LEG",
            "Exactly one of --length or --leg must be provided.")
        return errors
    if c.length is not None and c.leg is not None:
        err("VALIDATION_EXCLUSIVE_LENGTH_LEG",
            "--length and --leg are mutually exclusive.")
        return errors

    # depth > 0
    if c.depth <= 0:
        err("VALIDATION_DEPTH_ZERO", "depth must be > 0.", "depth", str(c.depth))
        return errors

    # thickness constraints
    if c.thickness >= c.depth / 2:
        err(ERR_VALIDATION_THICKNESS_TOO_LARGE,
            f"thickness ({c.thickness}mm) must be < depth/2 ({c.depth/2:.3f}mm).",
            "thickness", str(c.thickness))
    if c.thickness >= c.short / 4:
        err(ERR_VALIDATION_THICKNESS_TOO_LARGE,
            f"thickness ({c.thickness}mm) must be < short/4 ({c.short/4:.3f}mm).",
            "thickness", str(c.thickness))

    # TEST_STRIP height constraint
    if 3 * c.depth > c.sheet_height:
        err(ERR_VALIDATION_TEST_STRIP_TOO_TALL,
            f"depth ({c.depth}mm) produces TEST_STRIP height ({3*c.depth}mm) "
            f"exceeding sheet_height ({c.sheet_height}mm). "
            "Reduce --depth or increase --sheet-height.",
            "depth", str(c.depth))

    # Derive geometry to check structural constraints
    from core.trapezoid import derive
    try:
        geom = derive(c)
    except Exception as e:
        err("VALIDATION_GEOMETRY", str(e))
        return errors

    # Mode B: leg > leg_inset
    if c.leg is not None:
        leg_inset = (c.long - c.short) / 2.0
        if c.leg <= leg_inset:
            err("VALIDATION_LEG_TOO_SHORT",
                f"leg ({c.leg}mm) must be > leg_inset ({leg_inset:.3f}mm).",
                "leg", str(c.leg))

    # Non-orthogonal structural safety
    fw = c.finger_width if c.finger_width else AUTO_FINGER_WIDTH_FACTOR * c.thickness
    W_over   = c.thickness * math.tan(math.radians(geom.leg_angle_deg))
    W_struct = fw - c.tolerance - W_over
    if W_struct < c.thickness * OVERCUT_MIN_STRUCT_RATIO:
        err(ERR_VALIDATION_STRUCT_TAB_TOO_THIN,
            f"At leg_angle={geom.leg_angle_deg:.2f}°, the rotational overcut "
            f"({W_over:.3f}mm) reduces the structural tab width to {W_struct:.3f}mm, "
            f"which is less than the minimum ({c.thickness*OVERCUT_MIN_STRUCT_RATIO:.3f}mm). "
            "Reduce the trapezoid angle, increase --finger-width, or reduce --thickness.")

    # Box mode additional rules
    if config.lid == LidType.SLIDING:
        if c.depth <= 3 * c.thickness:
            err(ERR_VALIDATION_GROOVE_ANGLE_TOO_STEEP,
                f"Sliding lid requires depth ({c.depth}mm) > 3×thickness ({3*c.thickness}mm).",
                "depth", str(c.depth))
        # Groove angle limit
        critical = math.degrees(math.acos(c.thickness / (c.thickness + c.tolerance)))
        if geom.leg_angle_deg >= critical:
            err(ERR_VALIDATION_GROOVE_ANGLE_TOO_STEEP,
                f"Sliding lid requires leg_angle ({geom.leg_angle_deg:.3f}°) < "
                f"groove angle limit ({critical:.3f}°). "
                "The lid cannot seat in the tilted groove without binding.")

    return errors


def _compute_output_paths(output: Path, num_sheets: int) -> list[Path]:
    """Compute output file paths for single or multi-sheet output."""
    if num_sheets == 1:
        return [output]
    stem   = output.stem
    suffix = output.suffix
    parent = output.parent
    return [parent / f"{stem}_sheet{i+1}{suffix}" for i in range(num_sheets)]


def run(args: argparse.Namespace) -> None:
    """Box mode entry point."""
    from box import panels as box_panels
    from core import layout as layout_module
    from core import svg_writer
    from core.trapezoid import derive
    from core.radii import resolve_corner_radius

    config = build_config(args)

    # Handle --list-presets (may also be handled top-level)
    if getattr(args, "list_presets", None):
        from presets import list_presets
        list_presets()
        sys.exit(0)

    # Handle --format dxf
    if getattr(args, "format", None) == "dxf":
        reporter.print_error("DXF output is not yet implemented.",
                             "ERR_FORMAT_NOT_IMPLEMENTED", "--format", "dxf",
                             config.common.json_errors)
        sys.exit(1)

    errors = validate_config(config)
    if errors:
        reporter.print_errors(errors, config.common.json_errors)
        sys.exit(1)

    try:
        geom   = derive(config.common)
        radius = resolve_corner_radius(config.common, geom)
        panels = box_panels.build(config, geom, radius)
        layout = layout_module.layout_panels(
            panels, config.common.sheet_width, config.common.sheet_height)
        reporter.print_summary(geom, panels, layout, None, config.common, "box")
        num_sheets   = max(idx for _, _, idx in layout) + 1
        output_paths = _compute_output_paths(Path(config.common.output), num_sheets)
        svg_writer.write(layout, config.common, output_paths, "box")
        if num_sheets > 1:
            reporter.print_warning(f"Layout required {num_sheets} sheets.")
    except (ValueError, NotImplementedError, IOError) as exc:
        reporter.print_error(str(exc), "ERR_RUNTIME", None, None,
                             config.common.json_errors)
        sys.exit(1)

    sys.exit(0)
