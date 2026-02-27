#!/usr/bin/env python3
"""
trapezoid_box.py — Entry point and mode selector.

Usage:
  trapezoid_box.py [--version] [--list-presets] [--extract-config PATH] {box|instrument}
  trapezoid_box.py box        [common] [box-params]
  trapezoid_box.py instrument [common] [instrument-params]
"""

from __future__ import annotations
import argparse
import sys

from constants import TOOL_VERSION


def main() -> None:
    # ── Top-level flags (handled before subcommand parsing) ───────────────────
    # Check for --version, --list-presets, --extract-config first
    if "--version" in sys.argv:
        print(f"trapezoid_box v{TOOL_VERSION}")
        sys.exit(0)

    if "--list-presets" in sys.argv:
        from presets import list_presets
        list_presets()
        sys.exit(0)

    # --extract-config PATH: read embedded config from a trapezoidbox SVG
    if "--extract-config" in sys.argv:
        idx = sys.argv.index("--extract-config")
        if idx + 1 >= len(sys.argv):
            print("--extract-config requires a PATH argument.", file=sys.stderr)
            sys.exit(1)
        svg_path = sys.argv[idx + 1]
        from pathlib import Path
        from core.svg_writer import extract_config
        try:
            cfg = extract_config(Path(svg_path))
            print(cfg)
        except (ValueError, FileNotFoundError) as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # ── Subcommand parser ─────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        prog="trapezoid_box",
        description="Generate laser-cutter-ready SVG for trapezoidal boxes.",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    parser.add_argument("--list-presets", action="store_true", help="List presets and exit.")
    parser.add_argument("--extract-config", type=str, metavar="PATH",
                        help="Extract embedded config from a trapezoidbox SVG.")

    subparsers = parser.add_subparsers(dest="mode")

    # box subcommand
    box_parser = subparsers.add_parser("box", help="Box mode.")
    from box.cli import add_box_args
    add_box_args(box_parser)

    # instrument subcommand
    inst_parser = subparsers.add_parser("instrument", help="Instrument mode.")
    from instrument.cli import add_instrument_args
    add_instrument_args(inst_parser)

    args = parser.parse_args()

    if args.mode is None:
        parser.print_help()
        sys.exit(0)

    match args.mode:
        case "box":
            from box.cli import run
            run(args)
        case "instrument":
            from instrument.cli import run
            run(args)
        case _:
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
