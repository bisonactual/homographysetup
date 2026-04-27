from __future__ import annotations

import cv2
import numpy as np


def homography_from_points(image_points: np.ndarray, world_points_mm: np.ndarray) -> np.ndarray:
    if len(image_points) < 4:
        raise ValueError("At least four point pairs are required for a homography")

    matrix, mask = cv2.findHomography(
        np.asarray(image_points, dtype=np.float32),
        np.asarray(world_points_mm, dtype=np.float32),
        method=0,
    )
    if matrix is None:
        raise ValueError("Could not compute homography")
    return matrix


def transform_points(points: np.ndarray, homography: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(points, homography)
    return transformed.reshape(-1, 2)


def charuco_world_points(ids: np.ndarray, board: cv2.aruco.CharucoBoard) -> np.ndarray:
    chessboard_corners = board.getChessboardCorners()
    flat_ids = ids.reshape(-1)
    return np.asarray([chessboard_corners[int(corner_id)][:2] for corner_id in flat_ids], dtype=np.float32)

