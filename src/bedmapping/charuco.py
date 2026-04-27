from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class CharucoConfig:
    squares_x: int = 7
    squares_y: int = 7
    square_length_mm: float = 20.0
    marker_length_mm: float = 14.0
    dictionary_name: str = "DICT_4X4_50"


def aruco_dictionary(name: str) -> cv2.aruco.Dictionary:
    dictionary_id = getattr(cv2.aruco, name)
    return cv2.aruco.getPredefinedDictionary(dictionary_id)


def create_board(config: CharucoConfig) -> cv2.aruco.CharucoBoard:
    return cv2.aruco.CharucoBoard(
        (config.squares_x, config.squares_y),
        config.square_length_mm,
        config.marker_length_mm,
        aruco_dictionary(config.dictionary_name),
    )


def render_board(config: CharucoConfig, pixels_per_mm: float = 8.0, margin_px: int = 0) -> np.ndarray:
    board = create_board(config)
    width_px = int(round(config.squares_x * config.square_length_mm * pixels_per_mm)) + (2 * margin_px)
    height_px = int(round(config.squares_y * config.square_length_mm * pixels_per_mm)) + (2 * margin_px)
    image = board.generateImage((width_px, height_px), marginSize=margin_px)
    return image


def detect_charuco(image: np.ndarray, config: CharucoConfig) -> tuple[np.ndarray | None, np.ndarray | None, int]:
    board = create_board(config)
    dictionary = aruco_dictionary(config.dictionary_name)
    detector = cv2.aruco.CharucoDetector(board, cv2.aruco.CharucoParameters(), cv2.aruco.DetectorParameters())
    corners, ids, marker_corners, marker_ids = detector.detectBoard(image)
    count = 0 if ids is None else len(ids)
    return corners, ids, count
