#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bedmapping.charuco import CharucoConfig, create_board, detect_charuco, render_board
from bedmapping.geometry import charuco_world_points, homography_from_points, transform_points


def main() -> int:
    generated = Path("generated")
    generated.mkdir(exist_ok=True)

    config = CharucoConfig()
    board_image = render_board(config, pixels_per_mm=7.0)

    h, w = board_image.shape[:2]
    source = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    target = np.float32([[140, 70], [930, 115], [875, 795], [95, 735]])

    canvas = np.full((900, 1050), 235, dtype=np.uint8)
    warp = cv2.getPerspectiveTransform(source, target)
    synthetic = cv2.warpPerspective(board_image, warp, (canvas.shape[1], canvas.shape[0]), borderValue=235)
    mask = cv2.warpPerspective(np.full_like(board_image, 255), warp, (canvas.shape[1], canvas.shape[0]))
    canvas[mask > 0] = synthetic[mask > 0]

    cv2.imwrite(str(generated / "synthetic_charuco_scene.png"), canvas)

    corners, ids, count = detect_charuco(canvas, config)
    if corners is None or ids is None or count < 8:
        print(f"FAIL detected only {count} ChArUco corners")
        return 1

    board = create_board(config)
    world_mm = charuco_world_points(ids, board)
    image_points = corners.reshape(-1, 2)
    image_to_world = homography_from_points(image_points, world_mm)

    predicted_mm = transform_points(image_points, image_to_world)
    errors = np.linalg.norm(predicted_mm - world_mm, axis=1)
    max_error = float(errors.max())
    mean_error = float(errors.mean())

    debug = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)
    cv2.aruco.drawDetectedCornersCharuco(debug, corners, ids)
    cv2.imwrite(str(generated / "synthetic_charuco_detected.png"), debug)

    if max_error > 0.25:
        print(f"FAIL reprojection error too high: mean={mean_error:.4f} mm max={max_error:.4f} mm")
        return 1

    print("PASS synthetic ChArUco homography test")
    print(f"Detected corners: {count}")
    print(f"Mean point error: {mean_error:.4f} mm")
    print(f"Max point error: {max_error:.4f} mm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

