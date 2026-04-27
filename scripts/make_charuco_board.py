#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bedmapping.charuco import CharucoConfig, render_board


PRESETS = {
    "default-140": CharucoConfig(
        squares_x=7,
        squares_y=7,
        square_length_mm=20.0,
        marker_length_mm=14.0,
        dictionary_name="DICT_4X4_50",
    ),
    "a4-balanced": CharucoConfig(
        squares_x=7,
        squares_y=5,
        square_length_mm=38.0,
        marker_length_mm=27.0,
        dictionary_name="DICT_5X5_250",
    ),
    "a4-robust": CharucoConfig(
        squares_x=6,
        squares_y=4,
        square_length_mm=45.0,
        marker_length_mm=32.0,
        dictionary_name="DICT_5X5_250",
    ),
    "full-bed-500x350": CharucoConfig(
        squares_x=10,
        squares_y=7,
        square_length_mm=50.0,
        marker_length_mm=35.0,
        dictionary_name="DICT_5X5_250",
    ),
}


def svg_wrapper(output: Path, width_mm: float, height_mm: float) -> str:
    image_name = output.name
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.3f}mm" height="{height_mm:.3f}mm" viewBox="0 0 {width_mm:.3f} {height_mm:.3f}">
  <rect x="0" y="0" width="{width_mm:.3f}" height="{height_mm:.3f}" fill="white"/>
  <image href="{image_name}" x="0" y="0" width="{width_mm:.3f}" height="{height_mm:.3f}" preserveAspectRatio="none"/>
</svg>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a printable ChArUco board image.")
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS),
        default="default-140",
        help="Known board layout to generate.",
    )
    parser.add_argument("--output", default="generated/charuco_140mm.png")
    parser.add_argument("--squares-x", type=int)
    parser.add_argument("--squares-y", type=int)
    parser.add_argument("--square-mm", type=float)
    parser.add_argument("--marker-mm", type=float)
    parser.add_argument("--dictionary", default=None)
    parser.add_argument("--pixels-per-mm", type=float, default=8.0)
    parser.add_argument("--margin-mm", type=float, default=0.0)
    parser.add_argument("--no-svg", action="store_true", help="Do not write a same-name SVG print wrapper.")
    args = parser.parse_args()

    preset = PRESETS[args.preset]
    config = CharucoConfig(
        squares_x=args.squares_x if args.squares_x is not None else preset.squares_x,
        squares_y=args.squares_y if args.squares_y is not None else preset.squares_y,
        square_length_mm=args.square_mm if args.square_mm is not None else preset.square_length_mm,
        marker_length_mm=args.marker_mm if args.marker_mm is not None else preset.marker_length_mm,
        dictionary_name=args.dictionary if args.dictionary is not None else preset.dictionary_name,
    )

    margin_px = int(round(args.margin_mm * args.pixels_per_mm))
    image = render_board(config, pixels_per_mm=args.pixels_per_mm, margin_px=margin_px)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), image)

    board_width_mm = config.squares_x * config.square_length_mm
    board_height_mm = config.squares_y * config.square_length_mm
    total_width_mm = board_width_mm + (2 * args.margin_mm)
    total_height_mm = board_height_mm + (2 * args.margin_mm)

    print(f"Wrote {output}")
    if not args.no_svg:
        svg_output = output.with_suffix(".svg")
        svg_output.write_text(svg_wrapper(output, total_width_mm, total_height_mm), encoding="utf-8")
        print(f"Wrote {svg_output}")
    print(f"Preset: {args.preset}")
    print(f"Dictionary: {config.dictionary_name}")
    print(f"Squares: {config.squares_x} x {config.squares_y}")
    print(f"Square size: {config.square_length_mm:.1f} mm")
    print(f"Marker size: {config.marker_length_mm:.1f} mm")
    print(f"Active board area: {board_width_mm:.1f} x {board_height_mm:.1f} mm")
    if args.margin_mm:
        print(f"Total print area with margin: {total_width_mm:.1f} x {total_height_mm:.1f} mm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
