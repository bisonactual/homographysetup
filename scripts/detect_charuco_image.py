#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bedmapping.charuco import CharucoConfig, create_board, detect_charuco
from bedmapping.geometry import charuco_world_points, homography_from_points, transform_points


def board_outer_corners_mm(config: CharucoConfig) -> np.ndarray:
    width_mm = config.squares_x * config.square_length_mm
    height_mm = config.squares_y * config.square_length_mm
    return np.float32(
        [
            [0.0, 0.0],
            [width_mm, 0.0],
            [width_mm, height_mm],
            [0.0, height_mm],
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect a ChArUco board in a still image.")
    parser.add_argument("image", help="Path to a photo/image containing the ChArUco board.")
    parser.add_argument("--output", default="generated/detected_charuco_image.png")
    parser.add_argument("--squares-x", type=int, default=7)
    parser.add_argument("--squares-y", type=int, default=7)
    parser.add_argument("--square-mm", type=float, default=20.0)
    parser.add_argument("--marker-mm", type=float, default=14.0)
    parser.add_argument("--min-corners", type=int, default=8)
    args = parser.parse_args()

    image_path = Path(args.image)
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        print(f"Could not read image: {image_path}")
        return 1

    config = CharucoConfig(
        squares_x=args.squares_x,
        squares_y=args.squares_y,
        square_length_mm=args.square_mm,
        marker_length_mm=args.marker_mm,
    )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, count = detect_charuco(gray, config)
    if corners is None or ids is None or count < args.min_corners:
        print(f"FAIL detected {count} ChArUco corners, need at least {args.min_corners}")
        return 1

    board = create_board(config)
    image_points = corners.reshape(-1, 2)
    world_points_mm = charuco_world_points(ids, board)
    image_to_world = homography_from_points(image_points, world_points_mm)

    predicted_mm = transform_points(image_points, image_to_world)
    errors = np.linalg.norm(predicted_mm - world_points_mm, axis=1)

    debug = image.copy()
    cv2.aruco.drawDetectedCornersCharuco(debug, corners, ids)

    world_to_image = np.linalg.inv(image_to_world)
    outer_image_points = transform_points(board_outer_corners_mm(config), world_to_image)
    cv2.polylines(debug, [np.int32(outer_image_points)], isClosed=True, color=(0, 255, 0), thickness=3)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), debug)

    print("PASS detected ChArUco board")
    print(f"Image: {image_path}")
    print(f"Detected corners: {count}")
    print(f"Mean point error: {float(errors.mean()):.4f} mm")
    print(f"Max point error: {float(errors.max()):.4f} mm")
    print("Board outer corners in image pixels:")
    for label, point in zip(("top-left", "top-right", "bottom-right", "bottom-left"), outer_image_points):
        print(f"  {label}: x={point[0]:.1f}, y={point[1]:.1f}")
    print(f"Wrote debug image: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
