#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import cv2


def main() -> int:
    parser = argparse.ArgumentParser(description="Open a camera preview and save frames.")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fourcc", default="MJPG", help="Requested camera format, e.g. MJPG or YUYV.")
    parser.add_argument("--output-dir", default="data/captures")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(args.camera, cv2.CAP_V4L2)
    if args.fourcc:
        if len(args.fourcc) != 4:
            print("--fourcc must be exactly four characters, for example MJPG or YUYV")
            return 1
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*args.fourcc))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not capture.isOpened():
        print(f"Could not open camera {args.camera}")
        return 1

    actual_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fourcc = int(capture.get(cv2.CAP_PROP_FOURCC))
    actual_fourcc_text = "".join(chr((actual_fourcc >> 8 * i) & 0xFF) for i in range(4))
    print(f"Preview open: {actual_width}x{actual_height} {actual_fourcc_text}")
    print("Press 's' to save a frame, 'q' or Escape to quit.")
    while True:
        ok, frame = capture.read()
        if not ok:
            print("Camera frame read failed")
            return 1

        cv2.imshow("grblHAL bedmapping camera preview", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("s"):
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = output_dir / f"capture_{stamp}.png"
            cv2.imwrite(str(output), frame)
            print(f"Saved {output}")

    capture.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
