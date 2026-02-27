"""
instrument/cli.py — Instrument CLI: args, validation, config, run().
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
    DEFAULT_HELMHOLTZ_HZ, DEFAULT_NECK_CLEARANCE_MM,
    DEFAULT_KERF_HEIGHT_MM, DEFAULT_KERF_WIDTH_MM,
    DEFAULT_KERF_TOP_HEIGHT_MM, DEFAULT_KERF_TOP_WIDTH_MM,
    DEFAULT_NECK_BLOCK_THICK_MM, DEFAULT_TAIL_BLOCK_THICK_MM,
    RTRAP_LONG_TO_BODY_RATIO, RTRAP_ASPECT_RATIO, RTRAP_CORNER_R_MM,
    RTRAP_MAX_R_EDGE_FRACTION,
    ERR_VALIDATION_LONG_SHORT_ORDER, ERR_VALIDATION_THICKNESS_TOO_LARGE,
    ERR_VALIDATION_STRUCT_TAB_TOO_THIN, ERR_VALIDATION_TEST_STRIP_TOO_TALL,
    ERR_VALIDATION_SOUNDHOLE_TOO_TALL, ERR_VALIDATION_SOUNDHOLE_LONG_RATIO,
    ERR_VALIDATION_SOUNDHOLE_ASPECT, ERR_VALIDATION_SOUNDHOLE_RADIUS,
    ERR_VALIDATION_SOUNDHOLE_LATERAL,
)
from core.models import (
    CommonConfig, InstrumentConfig, DimMode, FingerDirection,
    SoundHoleType, SoundHoleOrientation,
)
from core import reporter
from box.cli import add_common_args, _defaults as _common_defaults, _compute_output_paths


def add_instrument_args(parser: argparse.ArgumentParser) -> None:
    """Add instrument-specific parameters."""
    add_common_args(parser)
    parser.add_argument("--top-thickness",         type=float, default=None)
    parser.add_argument("--finger-direction",       choices=["in", "out"], default=None)
    parser.add_argument("--kerfing",                action="store_true",  default=None, dest="kerfing")
    parser.add_argument("--no-kerfing",             action="store_false", default=None, dest="kerfing")
    parser.add_argument("--kerf-height",            type=float, default=None)
    parser.add_argument("--kerf-width",             type=float, default=None)
    parser.add_argument("--kerf-top-height",        type=float, default=None)
    parser.add_argument("--kerf-top-width",         type=float, default=None)
    parser.add_argument("--kerf-thickness",         type=float, default=None)
    parser.add_argument("--soundhole-type",         choices=["round", "f-hole", "rounded-trapezoid"], default=None)
    parser.add_argument("--soundhole-orientation",  choices=["same", "flipped"], default=None)
    parser.add_argument("--soundhole-long-ratio",   type=float, default=None)
    parser.add_argument("--soundhole-aspect",       type=float, default=None)
    parser.add_argument("--soundhole-r-mm",         type=float, default=None)
    parser.add_argument("--helmholtz-freq",         type=float, default=None)
    parser.add_argument("--soundhole-diameter",     type=float, default=None)
    parser.add_argument("--soundhole-size",         type=float, default=None)
    parser.add_argument("--soundhole-x",            type=float, default=None)
    parser.add_argument("--soundhole-y",            type=float, default=None)
    parser.add_argument("--neck-clearance",         type=float, default=None)
    parser.add_argument("--hardware",               action="store_true", default=None)
    parser.add_argument("--neck-block-thickness",   type=float, default=None)
    parser.add_argument("--tail-block-thickness",   type=float, default=None)
    parser.add_argument("--braces",                 action="store_true", default=None)
    parser.add_argument("--scale-length",           type=float, default=None)


def build_config(args: argparse.Namespace) -> InstrumentConfig:
    """Build InstrumentConfig from args using preset → config file → CLI precedence."""
    from presets import get_preset

    vals = _common_defaults()

    # Instrument defaults
    inst_vals = {
        "top_thickness": None,  # will default to thickness
        "kerf_thickness": None,
        "kerfing": True,
        "kerf_height": DEFAULT_KERF_HEIGHT_MM,
        "kerf_width": DEFAULT_KERF_WIDTH_MM,
        "kerf_top_height": DEFAULT_KERF_TOP_HEIGHT_MM,
        "kerf_top_width": DEFAULT_KERF_TOP_WIDTH_MM,
        "soundhole_type": None,
        "soundhole_orientation": "same",
        "soundhole_long_ratio": None,
        "soundhole_aspect": None,
        "soundhole_r_mm": None,
        "helmholtz_freq": DEFAULT_HELMHOLTZ_HZ,
        "soundhole_diameter": None,
        "soundhole_size": None,
        "soundhole_x": None,
        "soundhole_y": None,
        "neck_clearance": DEFAULT_NECK_CLEARANCE_MM,
        "hardware": False,
        "neck_block_thickness": DEFAULT_NECK_BLOCK_THICK_MM,
        "tail_block_thickness": DEFAULT_TAIL_BLOCK_THICK_MM,
        "braces": False,
        "scale_length": None,
        "finger_direction": "out",
    }

    # 1. Preset
    if args.preset:
        p = get_preset(args.preset)
        for k, v in p.get("common", {}).items():
            vals[k] = v
        for k, v in p.get("instrument", {}).items():
            inst_vals[k] = v

    # 2. Config file
    if getattr(args, "config_file", None):
        with open(args.config_file) as f:
            cfg_json = json.load(f)
        for k, v in cfg_json.get("common", {}).items():
            if v is not None:
                vals[k] = v
        for k, v in cfg_json.get("instrument", {}).items():
            if v is not None:
                inst_vals[k] = v

    # 3. CLI args
    def _apply(attr: str, key: str, d: dict) -> None:
        v = getattr(args, attr, None)
        if v is not None:
            d[key] = v

    _apply("long",           "long",           vals)
    _apply("short",          "short",          vals)
    _apply("length",         "length",         vals)
    _apply("leg",            "leg",            vals)
    _apply("depth",          "depth",          vals)
    _apply("thickness",      "thickness",      vals)
    _apply("burn",           "burn",           vals)
    _apply("tolerance",      "tolerance",      vals)
    _apply("corner_radius",  "corner_radius",  vals)
    _apply("finger_width",   "finger_width",   vals)
    _apply("sheet_width",    "sheet_width",    vals)
    _apply("sheet_height",   "sheet_height",   vals)
    _apply("output",         "output",         vals)

    if getattr(args, "inner", None):
        vals["dim_mode"] = DimMode.INNER
    if getattr(args, "colorblind", None):
        vals["colorblind"] = True
    if getattr(args, "json_errors", None):
        vals["json_errors"] = True
    if getattr(args, "labels", None) is not None:
        vals["labels"] = args.labels

    _apply("top_thickness",       "top_thickness",       inst_vals)
    _apply("kerf_thickness",      "kerf_thickness",      inst_vals)
    _apply("kerf_height",         "kerf_height",         inst_vals)
    _apply("kerf_width",          "kerf_width",          inst_vals)
    _apply("kerf_top_height",     "kerf_top_height",     inst_vals)
    _apply("kerf_top_width",      "kerf_top_width",      inst_vals)
    _apply("soundhole_type",      "soundhole_type",      inst_vals)
    _apply("soundhole_orientation","soundhole_orientation", inst_vals)
    _apply("soundhole_long_ratio","soundhole_long_ratio", inst_vals)
    _apply("soundhole_aspect",    "soundhole_aspect",    inst_vals)
    _apply("soundhole_r_mm",      "soundhole_r_mm",      inst_vals)
    _apply("helmholtz_freq",      "helmholtz_freq",      inst_vals)
    _apply("soundhole_diameter",  "soundhole_diameter",  inst_vals)
    _apply("soundhole_size",      "soundhole_size",      inst_vals)
    _apply("soundhole_x",         "soundhole_x",         inst_vals)
    _apply("soundhole_y",         "soundhole_y",         inst_vals)
    _apply("neck_clearance",      "neck_clearance",      inst_vals)
    _apply("neck_block_thickness","neck_block_thickness",inst_vals)
    _apply("tail_block_thickness","tail_block_thickness",inst_vals)
    _apply("scale_length",        "scale_length",        inst_vals)
    _apply("finger_direction",    "finger_direction",    inst_vals)

    if getattr(args, "hardware", None):
        inst_vals["hardware"] = True
    if getattr(args, "braces", None):
        inst_vals["braces"] = True
    if getattr(args, "kerfing", None) is not None:
        inst_vals["kerfing"] = args.kerfing

    thickness = vals["thickness"]
    top_t  = inst_vals["top_thickness"] or thickness
    kerf_t = inst_vals["kerf_thickness"] or thickness

    sh_type = None
    if inst_vals["soundhole_type"]:
        sh_type = SoundHoleType(inst_vals["soundhole_type"])

    sh_orient = SoundHoleOrientation(inst_vals.get("soundhole_orientation", "same"))

    fd = FingerDirection(inst_vals.get("finger_direction", "out"))

    common = CommonConfig(
        long=vals.get("long") or 0.0,
        short=vals.get("short") or 0.0,
        length=vals.get("length"),
        leg=vals.get("leg"),
        depth=vals.get("depth") or 0.0,
        thickness=thickness,
        burn=vals["burn"],
        tolerance=vals["tolerance"],
        corner_radius=vals.get("corner_radius"),
        finger_width=vals.get("finger_width"),
        sheet_width=vals["sheet_width"],
        sheet_height=vals["sheet_height"],
        labels=vals["labels"],
        dim_mode=vals["dim_mode"],
        colorblind=vals.get("colorblind", False),
        json_errors=vals.get("json_errors", False),
        output=vals.get("output", "trapezoid_box_output.svg"),
    )

    return InstrumentConfig(
        common=common,
        top_thickness=top_t,
        kerf_thickness=kerf_t,
        kerfing=inst_vals["kerfing"],
        kerf_height=inst_vals["kerf_height"],
        kerf_width=inst_vals["kerf_width"],
        kerf_top_height=inst_vals["kerf_top_height"],
        kerf_top_width=inst_vals["kerf_top_width"],
        soundhole_type=sh_type,
        soundhole_orientation=sh_orient,
        soundhole_long_ratio=inst_vals.get("soundhole_long_ratio"),
        soundhole_aspect=inst_vals.get("soundhole_aspect"),
        soundhole_r_mm=inst_vals.get("soundhole_r_mm"),
        helmholtz_freq=inst_vals["helmholtz_freq"],
        soundhole_diameter=inst_vals.get("soundhole_diameter"),
        soundhole_size=inst_vals.get("soundhole_size"),
        soundhole_x=inst_vals.get("soundhole_x"),
        soundhole_y=inst_vals.get("soundhole_y"),
        neck_clearance=inst_vals["neck_clearance"],
        hardware=inst_vals["hardware"],
        neck_block_thickness=inst_vals["neck_block_thickness"],
        tail_block_thickness=inst_vals["tail_block_thickness"],
        braces=inst_vals["braces"],
        scale_length=inst_vals.get("scale_length"),
        finger_direction=fd,
    )


def validate_config(config: InstrumentConfig) -> list[dict]:
    """Validate InstrumentConfig. Returns list of error dicts."""
    errors: list[dict] = []
    c = config.common

    def err(code, message, parameter=None, value=None):
        errors.append({"code": code, "message": message,
                        "parameter": parameter, "value": value})

    if c.long is None or c.short is None or c.depth is None:
        err("VALIDATION_MISSING_DIMS", "long, short, and depth are required.")
        return errors

    if c.long <= c.short:
        err(ERR_VALIDATION_LONG_SHORT_ORDER,
            f"long ({c.long}mm) must be greater than short ({c.short}mm).")

    if c.length is None and c.leg is None:
        err("VALIDATION_MISSING_LENGTH_OR_LEG",
            "Exactly one of --length or --leg must be provided.")
        return errors

    if c.depth <= 0:
        err("VALIDATION_DEPTH_ZERO", "depth must be > 0.")
        return errors

    if c.thickness >= c.depth / 2:
        err(ERR_VALIDATION_THICKNESS_TOO_LARGE,
            f"thickness ({c.thickness}mm) must be < depth/2 ({c.depth/2:.3f}mm).")
    if c.thickness >= c.short / 4:
        err(ERR_VALIDATION_THICKNESS_TOO_LARGE,
            f"thickness ({c.thickness}mm) must be < short/4 ({c.short/4:.3f}mm).")

    if 3 * c.depth > c.sheet_height:
        err(ERR_VALIDATION_TEST_STRIP_TOO_TALL,
            f"depth ({c.depth}mm) produces TEST_STRIP height ({3*c.depth}mm) "
            f"exceeding sheet_height ({c.sheet_height}mm). "
            "Reduce --depth or increase --sheet-height.")

    from core.trapezoid import derive
    try:
        geom = derive(c)
    except Exception as e:
        err("VALIDATION_GEOMETRY", str(e))
        return errors

    fw = c.finger_width if c.finger_width else AUTO_FINGER_WIDTH_FACTOR * c.thickness
    W_over   = c.thickness * math.tan(math.radians(geom.leg_angle_deg))
    W_struct = fw - c.tolerance - W_over
    if W_struct < c.thickness * OVERCUT_MIN_STRUCT_RATIO:
        err(ERR_VALIDATION_STRUCT_TAB_TOO_THIN,
            f"At leg_angle={geom.leg_angle_deg:.2f}°, the rotational overcut "
            f"({W_over:.3f}mm) reduces the structural tab width to {W_struct:.3f}mm, "
            f"which is less than the minimum ({c.thickness*OVERCUT_MIN_STRUCT_RATIO:.3f}mm). "
            "Reduce the angle, increase --finger-width, or reduce --thickness.")

    # Instrument-specific: scale_length > length
    if config.scale_length is not None and config.scale_length <= geom.length_outer:
        err("VALIDATION_SCALE_LENGTH",
            f"scale_length ({config.scale_length}mm) must be > length ({geom.length_outer:.1f}mm).")

    # Kerf width < thickness × 4
    if config.kerf_width >= c.thickness * 4:
        err("VALIDATION_KERF_WIDTH",
            f"kerf_width ({config.kerf_width}mm) must be < 4×thickness ({4*c.thickness}mm).")

    # Soundhole validation for rounded-trapezoid
    if config.soundhole_type == SoundHoleType.ROUNDED_TRAPEZOID:
        long_ratio = config.soundhole_long_ratio or RTRAP_LONG_TO_BODY_RATIO
        aspect     = config.soundhole_aspect
        r_mm       = config.soundhole_r_mm or RTRAP_CORNER_R_MM

        if long_ratio < 0.1 or long_ratio > 0.6:
            err(ERR_VALIDATION_SOUNDHOLE_LONG_RATIO,
                f"soundhole_long_ratio ({long_ratio}) must be in [0.1, 0.6].")

        if aspect is None:
            err(ERR_VALIDATION_SOUNDHOLE_ASPECT,
                "soundhole_aspect must be provided explicitly (None is not allowed). "
                "Use --soundhole-aspect (range 0.3–2.0).")
        elif aspect < 0.3 or aspect > 2.0:
            err(ERR_VALIDATION_SOUNDHOLE_ASPECT,
                f"soundhole_aspect ({aspect}) must be in [0.3, 2.0].")

        if aspect is not None:
            h_long   = geom.long_outer * long_ratio
            h_short  = h_long * (geom.short_outer / geom.long_outer)
            h_height = h_long * aspect
            h_inset  = (h_long - h_short) / 2
            leg_edge = math.sqrt(h_inset**2 + h_height**2)
            min_edge = min(h_short, h_long, leg_edge)

            if r_mm <= 0 or r_mm > min_edge * RTRAP_MAX_R_EDGE_FRACTION:
                err(ERR_VALIDATION_SOUNDHOLE_RADIUS,
                    f"soundhole_r_mm ({r_mm:.3f}mm) must be > 0 and "
                    f"<= min_edge×{RTRAP_MAX_R_EDGE_FRACTION} "
                    f"({min_edge * RTRAP_MAX_R_EDGE_FRACTION:.3f}mm).")

            neck_b = config.neck_block_thickness if config.hardware else 0.0
            y_near = (config.soundhole_x if config.soundhole_x is not None
                      else neck_b + config.neck_clearance)
            tail_b = config.tail_block_thickness if config.hardware else 0.0

            if y_near + h_height >= geom.length_outer - tail_b:
                err(ERR_VALIDATION_SOUNDHOLE_TOO_TALL,
                    f"neck_clearance + hole_height ({y_near + h_height:.1f}mm) "
                    f">= length - tail_block ({geom.length_outer - tail_b:.1f}mm).")

    return errors


def run(args: argparse.Namespace) -> None:
    """Instrument mode entry point."""
    import dataclasses
    from instrument import panels as instrument_panels, soundhole
    from core import layout as layout_module, svg_writer
    from core.trapezoid import derive
    from core.radii import resolve_corner_radius
    from core.models import PanelType

    config = build_config(args)

    if getattr(args, "list_presets", None):
        from presets import list_presets
        list_presets()
        sys.exit(0)

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
        panels = instrument_panels.build(config, geom, radius)

        sh_res = soundhole.compute(config, geom)
        if sh_res is not None:
            holes, sh_result = sh_res
            panels = [
                dataclasses.replace(p, holes=holes)
                if p.type == PanelType.SOUNDBOARD else p
                for p in panels
            ]
        else:
            sh_result = None

        layout = layout_module.layout_panels(
            panels, config.common.sheet_width, config.common.sheet_height)
        reporter.print_summary(geom, panels, layout, sh_result, config.common, "instrument")
        num_sheets   = max(idx for _, _, idx in layout) + 1
        output_paths = _compute_output_paths(Path(config.common.output), num_sheets)
        svg_writer.write(layout, config.common, output_paths, "instrument")
        if num_sheets > 1:
            reporter.print_warning(f"Layout required {num_sheets} sheets.")
    except (ValueError, NotImplementedError, IOError) as exc:
        reporter.print_error(str(exc), "ERR_RUNTIME", None, None,
                             config.common.json_errors)
        sys.exit(1)

    sys.exit(0)
