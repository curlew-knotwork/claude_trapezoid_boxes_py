#!/usr/bin/env python3
"""
trapezoid_boxes.py — Top-level entry point and mode selector.

Usage:
    python trapezoid_boxes.py [--version] [--list-presets] [--extract-config PATH]
    python trapezoid_boxes.py box        [common] [box-params]
    python trapezoid_boxes.py instrument [common] [instrument-params]
"""

from __future__ import annotations
import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

import argparse
from constants import TOOL_VERSION


def main() -> None:
    from box.cli import add_box_args, run as box_run
    from instrument.cli import add_instrument_args, run as instrument_run

    parser = argparse.ArgumentParser(
        prog="trapezoid_boxes.py",
        description="Parametric laser-cut trapezoid box/instrument body generator.",
        epilog=(
            "Examples:\n"
            "  python trapezoid_boxes.py box --long 180 --short 120 --length 380 "
            "--depth 90 --thickness 3\n"
            "  python trapezoid_boxes.py instrument --long 180 --short 120 "
            "--length 380 --depth 90 --soundhole-type round\n"
            "  python trapezoid_boxes.py --extract-config my_box.svg\n"
            "  python trapezoid_boxes.py --list-presets\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version",
                        version=f"trapezoid_boxes {TOOL_VERSION}")
    parser.add_argument("--list-presets", action="store_true", default=False,
                        help="List built-in presets and exit.")
    parser.add_argument("--extract-config", type=str, default=None, metavar="PATH",
                        help="Extract embedded config JSON from an SVG file and print to stdout.")

    sub = parser.add_subparsers(dest="mode", metavar="{box,instrument}")

    box_p = sub.add_parser("box", help="Generate a plain trapezoid box.")
    add_box_args(box_p)
    box_p.set_defaults(_run=box_run)

    instr_p = sub.add_parser("instrument", help="Generate a trapezoid instrument body.")
    add_instrument_args(instr_p)
    instr_p.set_defaults(_run=instrument_run)

    args = parser.parse_args()

    # Top-level flags — no subcommand required
    if args.list_presets:
        from presets import list_presets
        list_presets()
        sys.exit(0)

    if args.extract_config is not None:
        from core.svg_writer import extract_config
        try:
            print(extract_config(Path(args.extract_config)))
        except (IOError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # No subcommand and no top-level flag: print help
    if args.mode is None:
        parser.print_help()
        sys.exit(0)

    args._run(args)


if __name__ == "__main__":
    main()
