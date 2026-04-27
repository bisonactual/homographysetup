#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import cv2


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture one frame from a camera without opening a preview window.")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fourcc", default="MJPG")
    parser.add_argument("--warmup", type=int, default=5, help="Frames to discard before saving.")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

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
    print(f"Camera open: {actual_width}x{actual_height} {actual_fourcc_text}")

    frame = None
    for index in range(args.warmup + 1):
        ok, frame = capture.read()
        if not ok:
            print(f"Camera frame read failed at frame {index}")
            capture.release()
            return 1

    capture.release()

    if args.output:
        output = Path(args.output)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path("data/captures") / f"capture_{stamp}.png"

    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), frame)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
